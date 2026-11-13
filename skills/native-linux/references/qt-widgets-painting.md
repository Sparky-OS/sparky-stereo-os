# How Qt Widgets reach the screen, and painting them on the GPU

Written on 2026-11-11 from Qt 6.11.2 (the edition's qt6-base 6.11.2+dfsg-5+stereo3d15) and two prototypes measured on an AMD Renoir iGPU and an NVIDIA RTX 3060.
Read it before changing how a QWidget window is painted, flushed or measured.
Neither prototype is shipped: both live behind one environment variable in a lane's build, and the numbers below are what they measured.
Added on 2026-11-13: the fixed-work measure, the person's choice on the Graphics page, the pair where the EGL has one view, and the cause of the 125 % offset.

- `QT_WIDGETS_GPU_PAINT=1` (or `opengl`): the widgets painted by Qt's OpenGL paint engine. It takes more processor than CPU painting for a terminal (one draw call for each thing painted) and stays available as the person's choice.
- `QT_WIDGETS_GPU_PAINT=batch`: the widgets' painting recorded and drawn in a few draw calls through the window's RHI. The picture is the CPU path's to a level or two of rounding, text included, at scales 1, 1.25 and 2.

## The three ways a widget window is drawn

| Way | Who paints the widgets | How the frame reaches the compositor | When |
|---|---|---|---|
| Raster backing store | `QRasterPaintEngine`, on the CPU, into a `QImage` | The image is a `wl_shm` buffer: `QWaylandShmBackingStore::flush()` attaches and commits it, and the compositor uploads it | Every plain widget window (Konsole, Dolphin, Kate) |
| RHI composition | The same raster engine, on the CPU | `QPlatformBackingStore::rhiFlush()`: `QBackingStoreDefaultCompositor` uploads the image's dirty region as a texture and draws it, with the textures of `QOpenGLWidget`, `QQuickWidget` and `QRhiWidget` children, into a `QRhiSwapChain` on the window's own EGL or Vulkan surface | A window that holds such a child, or every window with `QT_WIDGETS_RHI=1` (`QT_WIDGETS_RHI_BACKEND=opengl\|vulkan`) |
| OpenGL paint engine | `QOpenGL2PaintEngineEx` (Qt OpenGL), on the GPU | Only into a `QOpenGLPaintDevice`: a `QOpenGLWidget`, a `QOpenGLWindow`, a framebuffer object | Never for a plain widget in stock Qt |

Where to read it in qtbase:

- `src/widgets/kernel/qwidgetrepaintmanager.cpp`: `paintAndFlush()` (begin paint, `QWidgetPrivate::drawWidget()` on `store->paintDevice()`, end paint), `flush(QWidget *, ...)` (RHI or not, by `usesRhiFlush`).
- `src/widgets/kernel/qwidget.cpp`: `q_evaluateRhiConfig()` decides the window's surface type before its `QWidgetWindow` is made; `QWidgetPrivate::drawWidget()` sets the paint engine's system clip and sends the paint event.
- `src/gui/painting/qbackingstore.cpp`: `QBackingStore::handle()` asks the platform for its store (`QWaylandIntegration::createPlatformBackingStore()` returns the shared memory one).
- `src/gui/painting/qplatformbackingstore.cpp`, `qbackingstorerhisupport.cpp`, `qbackingstoredefaultcompositor.cpp`: one `QRhi` and one compositor per backing store and surface type; `checkForceRhi()` reads the environment.
- `src/opengl/qopenglpaintengine.cpp`: the OpenGL engine; every `fillRect`, every text run and every pixmap is its own draw call with its own uniforms.

Qt has no `QPainter` on the RHI: [QTBUG-74407](https://bugreports.qt.io/browse/QTBUG-74407) ("Qt RHI Painter", Lars Knoll, 2019, open; Paul Tvete, 2019-11-26: "A proof of concept paint engine has been made ... It still requires substantial work to get to feature parity with the OpenGL paint engine") and [QTBUG-78634](https://bugreports.qt.io/browse/QTBUG-78634) ("QRhi-based QPainter integration for widgets", Laszlo Agocs, 2019, "Not for Qt 6.0").
Qt Canvas Painter (6.11) is an imperative painter on the RHI with an API of its own; it is not a `QPaintEngine`, so no existing `paintEvent()` draws through it.
Qt 4 had the OpenGL engine as a graphics system for whole widget windows (`-graphicssystem opengl`); Gunnar Sletta's 2009 overview names its limits ("Aliased drawing is a pain", "font sharing", native theming), and qtbase removed the last such path in 2012 (e973d0965c, Girish Ramakrishnan: "Rendering quality using the opengl paint engine is pretty poor so remove it").
Qt's own documentation still says it: "Antialiasing in the OpenGL paint engine is done using multisampling ... the resulting quality is not on par with the quality of the software paint engine" ([QOpenGLPaintDevice](https://doc.qt.io/qt-6/qopenglpaintdevice.html)).

## Painting the widgets through the OpenGL paint engine (the first prototype)

1. A `QPlatformBackingStore` whose `paintDevice()` is a `QOpenGLPaintDevice` over a framebuffer object, multisampled (the engine antialiases by samples only) with a stencil attachment (the engine writes a region clip into the stencil), resolved into a texture at `endPaint()`.
2. The store paints on a context of its own, current on a `QOffscreenSurface`, that shares with `QOpenGLContext::globalShareContext()`: every window's RHI context shares with that one (`QBackingStoreRhiSupport::create()`), so each window's compositor can sample the texture. Make the global share context before the first RHI is made.
3. The window is flushed through the RHI composition, which draws the store's own texture instead of uploading an image. `QBackingStoreDefaultCompositor::flush()` calls its own `toTexture()`, never the store's virtual one, so the compositor needs a hook for a texture handed over.
4. Qt Gui and Qt Widgets do not link Qt OpenGL. The store lives in Qt OpenGL; a shipped form needs a decided place for it (a platform plugin interface, or Qt Widgets linking Qt OpenGL), not a library opened by name.
5. The process draws on the GPU its environment names, like any OpenGL program, so the Graphics page's choice (`DRI_PRIME=pci-...`, Mesa's or NVIDIA's EGL vendor file, NVIDIA's offload variables) reaches the painting with no code of its own. Print `GL_RENDERER` from the paint context as the proof.
6. Element depth: the repaint manager already paints a window once per eye into a store twice as wide. On this path the pair goes to the two views of the window's own EGL surface (`_q_stereo_views` = 2, `EGL_EXT_multiview_window`), each view taking its half of the texture, and an element's shift of less than a pixel is added to the engine's projection after its snap to the pixel grid, with linear filtering for glyphs and pixmaps while it is not zero.

## The batched path (the second prototype)

One file in Qt Gui, `src/gui/painting/qbatchedpaintengine.cpp`, and three shaders in `src/gui/painting/shaders/` (`batchpaint.vert`, `batchpaint.frag`, `batchpaint_dual.frag`).
It uses only `QRhi`, so it needs neither Qt OpenGL nor a context of its own.

1. **A paint engine that records.** A `QPaintEngineEx` whose calls draw nothing: each fill of a rectangle, each glyph and each picture becomes one record of 40 bytes (a rectangle on the target, a rectangle in a texture, a colour, a kind).
2. **Cut on the CPU, kept in order.** A widget's clip is a region of rectangles, so every record is cut against it when it is made. There is no scissor, no stencil, no depth buffer and no sorting; paint order is draw order.
3. **One quad, drawn as instances.** At the flush the records are one vertex buffer (`QRhiVertexInputBinding::PerInstance`), drawn by one shader with three textures bound: glyph masks, small pictures, and the frame's raster-drawn parts. A paint pass is one draw call; another call happens only where the blending changes (`CompositionMode_Source`, the inverting text cursor).
4. **Inside the compositor's frame.** `QBackingStoreDefaultCompositor::flush()` has a frame open on the window's swapchain; the store draws its records in a pass of that frame, into a texture that keeps the window's contents (`QRhiTextureRenderTarget::PreserveColorContents`), and hands the texture over. A scroll is two `copyTexture()` calls recorded in order with the painting.
5. **Edges by coverage.** The fragment shader weighs each pixel by the part of it the rectangle covers (`gl_FragCoord` against the rectangle's corners). A rectangle on whole pixels is drawn exactly as the raster engine fills it; a rectangle moved by a part of a pixel has exact edges with no multisampling.
6. **What is not a rectangle, a glyph or a picture is drawn by the raster engine.** The engine repeats the same call, with the same state, transformation and clip, on a raster `QPainter` that draws into a transparent part of a scratch image; the part is uploaded with the frame and laid over the target at its place in the paint order. The result is the raster engine's by construction. `QT_WIDGETS_PAINT_STATS=1` prints how many of each kind a flush had, `QT_LOGGING_RULES=qt.gui.batchpaint.info=true` names each kind once, and `QT_WIDGETS_GPU_PAINT_DUMP=FOLDER` saves each frame's scratch image and lists its records, and `QT_WIDGETS_GPU_PAINT_GROUND=RRGGBB` gives a new texture a colour, to tell a pixel nothing painted from one painted black.

### What Qt already had, and what was taken

| Piece | Where | Taken? |
|---|---|---|
| The scene graph's batch renderer | qtdeclarative `src/quick/scenegraph/coreapi/qsgbatchrenderer.cpp` (`prepareOpaqueBatches()`, `prepareAlphaBatches()`, `uploadBatch()`, `renderMergedBatch()`) | The lesson (one buffer, few calls). Not the code: it belongs to Qt Quick's retained tree and merges by material, which ends a batch at every change from rectangle to text |
| The scene graph's native text | `qsgrhitextureglyphcache.cpp`, `qsgdefaultglyphnode_p.cpp` (`QSGTextMaskMaterial`) | The method: the font engine's own masks in a texture, a quad for each glyph |
| `QTextureGlyphCache` | qtbase `src/gui/painting/qtextureglyphcache.cpp` | Not as it is: one cache, so one texture, for each font; bold inside a line would end the batch. One texture for all fonts instead |
| Distance-field and curve text | `qsgadaptationlayer.cpp`, `qsgcurveglyphatlas.cpp` | No: both draw text differently from the raster engine |
| The scene graph's picture atlas | `util/qsgrhiatlastexture.cpp` | The method: small pictures in one texture, each with its edge repeated around it |
| `QRhi`, the RHI compositor | qtbase `src/gui/rhi`, `src/gui/painting/qbackingstoredefaultcompositor.cpp` | Used as they are; the compositor got one hook that hands a texture over |
| Qt Canvas Painter (6.11) | its own module | No: an API of its own, not a `QPaintEngine`; commercial or GPL 3 only |
| A painter on the RHI | [QTBUG-74407](https://bugreports.qt.io/browse/QTBUG-74407), [QTBUG-78634](https://bugreports.qt.io/browse/QTBUG-78634) | Open since 2019; Paul Tvete's proof of concept was never merged, and qtbase's dev branch had none on 2026-11-11 |

### How text stays the CPU path's text

- The raster engine draws a glyph by blending the font engine's mask for the part of a pixel the glyph's position has, on a whole pixel (`QRasterPaintEngine::drawCachedGlyphs()`, `QFontEngine::glyphData()`, `subPixelPositionFor()`). The batched engine keeps those same masks in one texture and places each on the same whole pixel, taken unfiltered. Nothing is scaled or filtered, so the scale of the screen does not matter.
- Ask the font for the mask a widget gets: the raster engine passes `Format_None` when the painter's device is a widget and `Format_A8` otherwise. A raster painter begun on a `QImage` therefore draws grey text on a desktop with LCD antialiasing. Begin it on a small `QPaintDevice` whose `devType()` is `QInternal::Widget` and whose `redirected()` returns the image.
- **LCD antialiasing** (a coverage for each colour channel; the font's default on many desktops) needs a weight for each channel when blending: dual-source blending (`OneMinusSrc1Color`), in OpenGL 3.3 or OpenGL ES with `GL_EXT_blend_func_extended`. Qt's OpenGL RHI backend answered "Unsupported blend factor" for the `Src1` factors; the prototype maps them. All records go through the one shader with two outputs, so LCD text needs no batch of its own.
- Where the text is not opaque (`QPainter::setOpacity()`), the raster engine leaves its fast path and takes the green channel of an LCD mask as the one coverage (`alphaPenBlt()`, `qGreen(rgbCoverage)`). Follow it.
- Text the raster engine must draw (rotated, under a path clip) is drawn white on black into the scratch image, where the raster engine blends by channel because the ground is opaque; what is left is the coverage, and the pen's colour is blended through it like a glyph. Drawn in its own colour onto a transparent part, the raster engine gives up the channels (`alphargbblend_argb32()`: "Give up and do a naive gray alphablend").
- **An element's eye shift of less than a pixel** is added to each glyph's position before the part of a pixel is taken, so the glyph gets its own mask for the new place: text at half a pixel is as sharp as text on whole pixels (measured: the mean difference between neighbours 19.4 against 18.2, where the first prototype's filtered text had 13.6). A font with full hinting has one mask for each glyph, so its text moves by whole pixels.

### What makes the picture differ from the raster engine's, and how to follow it

Found with a window of 24 kinds of painter call, captured on both paths and compared cell by cell.

| Kind | The raster engine's rule | 
|---|---|
| A rectangle with a pen | The inside is a rectangle and the pen's line is four narrow raster-drawn parts; they must tile exactly, or a line of pixels stays unpainted |
| A rounded rectangle | The same four parts, wider by the corner's radius: the inside of a rounded rectangle is a rectangle of one colour, and a frame around a large view then costs its outline, not its area |
| A dashed outline | Draw it whole: under a narrower clip the raster engine's dashes start elsewhere |
| A pattern brush (`Dense4Pattern`, `CrossPattern`) | It is tiled over the device's pixels, not scaled, from the transformation's translation divided by its scale (`QSpanData::setupMatrix()`, `BlendTiled`). Drawn into another place the pattern starts elsewhere unless the scale is 1: move the brush origin by the place's offset times (1 - 1/scale) |
| A picture scaled without smoothing | The place and the size are rounded (`x`, `y`, `width`, `height`, each by itself), and the source is stepped through by the rounded size; a sample that falls between two texels takes the one before (`qt_scale_image_*`: `qCeil(...) - 1`) |
| A picture scaled with smoothing | Each edge is rounded, the mapping of the unrounded rectangle is kept |
| A picture at its own size | Its place is rounded to a whole pixel |
| The text cursor | `QTextLayout::drawCursor()` uses `RasterOp_NotDestination` when the engine says it has raster operations: invert through blending (`OneMinusDstColor`, `OneMinusSrcColor`). At a fractional scale the cursor is a line in that mode: have the raster engine draw the line as coverage, and invert through the coverage |
| `CompositionMode_Source` with a colour that is not opaque | It takes the place of what is there: a batch of its own without blending |
| A clip | `QRasterPaintEngine::clip()` takes a path that is a rectangle as one whether or not it says so (`QVectorPath::isRect()`; QGraphicsView clips each item to a rectangle built as a path), and rounds a clip rectangle by its corners (`qt_mapFillRect()`) |
| A translucent window's start of painting | A raster store empties each dirty rectangle with its own `QPainter` (`CompositionMode_Source`, transparent), so the rectangle is rounded like every fill. Empty the same pixels: one more column at a fractional scale stays empty, a line through the window |

What remained after that, at every scale, on both GPUs, with grey and LCD text: differences of one or two levels (the GPU rounds a blend differently), and at scale 1.25 a few dozen pixels by up to 6 levels in a picture scaled with smoothing (the filter's precision).

## Measuring CPU against GPU painting fairly

- **One build, one switch.** Use the same libraries for both paths and switch by environment; add a run with the published packages to show that the unswitched build paints as stock does.
- **Alternate.** CPU, GPU, CPU, GPU, each case several times, one fresh compositor session per run, so both paths meet the same machine.
- **Record the machine with every run:** `/proc/loadavg` before and after, each GPU's use before the run, the other processes on the GPU. A run taken above the core count or beside another GPU job is tagged, never averaged in.
- **Drive the program from inside.** A preloaded library with `Q_COREAPP_STARTUP_FUNCTION` and a `QTimer` that moves the window's longest vertical `QScrollBar` gives every run the same scroll, without input events; end the program with `_exit(0)` so no dialog holds a run.
- **Measure in the repaint manager:** paints per second, the time from `beginPaint()` to the end of painting, and the flush, printed once a second. The paint time of an OpenGL path is the time to submit, not to draw: read the GPU's use and the program's own result (frames a terminal took, megabytes it read) beside it.
- **CPU per cent of the program and of the compositor separately:** shared memory windows cost the compositor an upload, GPU windows do not.
- **GPU use:** `gpu_busy_percent` for amdgpu, `nvidia-smi --query-gpu=utilization.gpu,power.draw` for NVIDIA (inside a container that got the card through CDI); power from the amdgpu hwmon `power1_input` and `nvidia-smi`. Package power (RAPL) is readable by root only.
- **Text by pixels, then by eye:** capture both paths with ScreenShot2 at scale 1 and at a fractional scale, count differing pixels, and put the same crop of each side by side, enlarged without smoothing.
- **A picture check that can fail:** one widget that makes each kind of painter call in its own cell (fills on whole and on parts of pixels, text at several sizes, coloured and translucent text, static text, pictures at their size, scaled, in part and with opacity, a large picture, lines, rectangles with a pen, rounded rectangles, paths, gradients and patterns, a clip of two rectangles, a clip that is a path, the text cursor, Source composition, opacity, a scaled and a rotated painter, tiled and one-bit pictures, points and dashes, terminal cells), with a mark of an unusual colour at its corner. Capture it on both paths and count the differing pixels cell by cell from each capture's own mark. Run it with grey and with LCD text (a `fonts.conf` in the test's own configuration folder: `rgba` `rgb`, `hintstyle` `hintfull` and `hintslight`), at scales 1, 1.25 and 2, on every GPU.
- **Stop animations and the blinking cursor for captures** (`kdeglobals`: `[KDE]` `CursorBlinkRate=0`, `AnimationDurationFactor=0`), and capture the CPU path twice first: what differs between two captures of the same path (a button that fades after a message arrived) is the program's, not the painting's.
- **Typing latency:** a preloaded library sends key events to the widget with the focus (`QCoreApplication::sendEvent()`), printing the time of each; the repaint manager prints the time each frame is handed to the compositor; pair each key with the first frame after it. This is the time to the commit, not to the light on the screen. A terminal adds its own wait before it repaints (Konsole: about 10 ms), which dominates.
- **Memory:** `Rss` and `Pss` from `/proc/PID/smaps_rollup` at the end of the run, the kernel driver's count from `/proc/PID/fdinfo` (`drm-total-memory`, amdgpu), and `nvidia-smi --query-gpu=memory.used`. A process with an OpenGL context carries the driver: about 25 to 50 MB more with Mesa, about 100 MB more with NVIDIA's.

## What the measurement is for

Widgets move to the GPU to free the processor for other work, first of all on small machines.
A few milliseconds of paint time are not something a person sees at this scale, so they do not decide anything.
- **The headline of every report is the processor load a program takes for the same work** (per frame, or at a fixed frame rate), on the smallest machine available first. Paint time in milliseconds is supporting detail.
- **The three ways stay the person's choice:** the processor, Qt's OpenGL paint engine, and batched painting. A path that measures worse on one machine is not removed.
- **Compare like with like:** a program that draws real content sends many items in few draw calls, as a game does. One draw call for each rectangle is the first prototype's limit, not a fair picture of GPU painting.

Measured on a small laptop on 2026-11-12 (AMD A10, a Carrizo iGPU and a Hainan discrete GPU, the names taken from each run's `GL_RENDERER` line):

| Program | Processor painting | OpenGL paint engine | Batched |
|---|---|---|---|
| Konsole, share of one core | 88 to 92 % | 114 to 116 % | the same or a little less, with 18 to 24 % more frames on the Hainan (about 22 % less processor for each frame) |
| Kate, share of one core | 48 to 50 % | 64 to 68 % | the same or a little less |
| Dolphin, share of one core | 61 to 71 % | 100 to 108 % | the same or a little less |

Batched painting also halved the paint time there (Konsole 11.6 to 5.0 ms, Kate 2.7 to 1.5, Dolphin 4.2 to 2.4) and cost about 40 MB more for each program and 0.4 to about 1 % of a core at idle.
Still owed: the load at a fixed amount of work, so that a path that draws more frames is not charged for them.

Two traps from that run:
- **Symptom:** the results' "igpu" and "dgpu" labels are the wrong way round. **Cause:** the kit named the cards by their order, not by what drew. **Fix:** name the card from the `GL_RENDERER` line of each run. **Found by:** reading the renderer line in each log beside its label.
- **Symptom:** the summary script fails on the laptop and works on the station. **Cause:** the laptop's locale writes a decimal comma, and the script parsed a point. **Fix:** run the measuring tools under `LC_ALL=C` and accept both in the parser. **Found by:** the traceback's `could not convert string to float: '11,6'`.

## The same work on every path: the fixed-work measure

A path that draws more frames must not be charged for them, so the work is fixed by script and the cost is counted over one window of wall time.
"The same work" is this page's reading of the aim (free the processor): a fixed script of frames at a fixed rate.

**The work, 20 seconds each, the same bytes and the same steps on every path:**

| Case | What is fixed |
|---|---|
| Terminal, colour animation | 300 recorded frames of a 160x48 fire animation, one every 1/15 s, each written whole to the terminal |
| Terminal, text | 300 frames of 12 new lines each, 15 a second, so the terminal scrolls |
| File manager | 1,200 scroll steps through 5,000 files, 60 a second, the place a function of the step number |
| Editor, scrolling | 1,200 scroll steps through 60,000 lines, 60 a second |
| Editor, typing | 200 key presses, 10 a second, a Return after every 60 |
| Idle | one minute of each program, the terminal's cursor blinking |

**The recipe** (the scripts are a lane's, described here so they can be written again):

1. A feeder (C, about 60 lines) plays a file of frames to the terminal: frame `k` is due at `T0 + k / rate` on `CLOCK_MONOTONIC` (`clock_nanosleep(..., TIMER_ABSTIME, ...)`), a late frame is written at once and the next keeps its own time. The recording is made by a generator with its own arithmetic (no library's random numbers), and its SHA-256 is checked on every machine, so two machines get the same bytes.
2. A preloaded driver (`Q_COREAPP_STARTUP_FUNCTION`) does the scroll steps and the keys on the same absolute schedule: each step through the event loop (`QTimer::singleShot(0, ...)`), so the paint it asked for happens before the next step. It prints how late the steps were and the program's own processor time (`getrusage`) at the first and the last step.
3. One clock for everything: the session script takes `T0 = now + warm-up` once and hands it to the feeder, the driver and the counter.
4. The counter reads, at `T0` and at `T0 + 20 s`: `/proc/PID/stat` user and system ticks of the program and of the compositor (all threads), `/proc/stat` for the whole machine, `/proc/PID/fdinfo/*` `drm-engine-*` (the GPU time the kernel counts for the program, by card), and between them every card's `gpu_busy_percent`, every hwmon `power*_input` by its name, `nvidia-smi`; memory from `smaps_rollup` at the end.
5. The repaint manager prints one line for each frame handed to the compositor (`QT_WIDGETS_PAINT_STATS=3`); the frames inside the window are counted, so a path that paints fewer or more frames for the same work shows.
6. Result for a run: processor milliseconds per frame asked for, the program and the compositor together, then each. For idle: per cent of one core.
7. Rounds: every case on the three ways one after another, the order of the ways turned with the round (so none always runs first), one fresh compositor session per run, at least three rounds; the table shows the median with the smallest and the largest.

**What a quiet run is.** Record with every run the load average before and after and the processors busy with other work over the window itself (`/proc/stat` minus the program, the compositor and the feeder).
A run is marked CONTENDED when the load average is above the processor count, other work takes more than a quarter of the processors, or another program computes on the same GPU; it is repeated on a quieter machine and never averaged with quiet runs.
On a shared machine wait before each run until fewer than about three processors are busy, for a bounded time, and take the run marked if the wait ends.
Processor time for the same work rises under contention (shared caches, two threads of one core), so a contended table shows the order of the ways, not their sizes.

**Naming the card.** Pin a card by its PCI ID (`DRI_PRIME=VENDOR:DEVICE!`) and name it from the run's own `GL_RENDERER` line.
A pin that names no card Mesa has a driver for is not an error to Mesa: the program draws on its default card. So also check where the kernel counted the program's GPU time (`drm-pdev` in fdinfo) and refuse the run when it is another card.
Painting on the processor does not use the pin: run it once a round and show its row with every card.

**What it measured on the first machine (2026-11-13).**
A Ryzen with a Renoir iGPU and an RTX 3060, the nested compositor on the same card as the program, 1920x1080; 172 runs over four hours on a machine other work kept loading (load average 1.8 to 33): 171 valid, 35 quiet, 137 CONTENDED.
Processor milliseconds per frame asked for, the program and the compositor together; quiet runs where there were any (the median, their count), otherwise the median of the contended ones, marked.
Contended runs cost about 1.4 to 1.7 times the quiet ones on every way, in the same order.

| Case | The processor | Qt's OpenGL engine | Batched |
|---|---|---|---|
| Terminal, colour animation, Mesa | 14.8 (1 quiet) | 35.9 (1) | 8.6 (2) |
| The same, NVIDIA | 14.3 (2) | 25.5 (2) | 9.5 (2) |
| Terminal, text, Mesa | 6.9 (2) | 11.3 (2) | 5.3 (2) |
| The same, NVIDIA | 7.6 (1) | 10.1 (2) | 6.0 (2) |
| File manager scrolling, Mesa | 4.2 (1) | 5.2 (1) | 4.3 (2) |
| The same, NVIDIA | 4.5 (1) | 5.2 (1) | 4.4 (1) |
| Editor scrolling, Mesa, contended (4 each) | 4.6 | 5.5 | 4.9 |
| The same, NVIDIA, contended | 4.5 | 6.2 | 4.2 |
| Editor typing, Mesa, contended (4 each) | 11.7 | 17.1 | 13.7 |
| The same, NVIDIA, contended (3 or 4) | 12.4 | 17.9 | 15.5 |
| Terminal idle, cursor blinking, % of a core, Mesa, contended (3 each) | 0.43 | 0.62 | 0.60 |
| File manager idle, % of a core, Mesa (1 quiet each) | 0.27 | 0.27 | 0.27 |
| Editor "idle" (it repaints a small area 27 times a second), % of a core, Mesa, contended | 5.4 | 9.0 | 7.6 |

What the numbers say:

- A program that paints much each frame (a terminal) takes 20 to 40 % less processor for the same frames when batched, on both cards. Qt's OpenGL engine takes one and a half to two and a half times the processor's, and under load it could not finish 300 frames of the animation in their 20 seconds (one run invalid for that).
- A program that paints little each frame (a file manager or an editor scrolling) takes the same on the processor and batched, within the spread of the runs. Typing into an editor and an editor that keeps repainting a small area took more when batched (about a sixth and about two fifths, both from contended runs only): a frame through the GPU has a fixed cost, and small frames pay it each time.
- So the gain is the program's, not the kind's: a default by kind ("other programs") would move a terminal, a file manager and an editor together.
- Idle costs the same within a quarter of a per cent of a core on every way.
- Memory: 25 to 30 MB more a program with Mesa and 85 to 95 MB with NVIDIA's driver, on both GPU ways.
- An editor that looks idle may not be: the frames inside the window are counted for that reason.

## The choice a desktop gives the person, and how it reaches a program

The three ways are one switch a program reads at its start, `QT_WIDGETS_GPU_PAINT` (nothing: the processor; `batch`; `opengl`), so a desktop can offer them without touching any program.
The edition's Graphics page (`sparky-stereo-graphics`) has "Paint windows": Automatic, On the processor, On the graphics card (batched), On the graphics card, Qt's OpenGL engine, for each kind of program and for each program.

- **Automatic is a measurement, not a guess:** the way measured for that kind of program on that machine or its model, kept in the machine's record beside the GPU measured best (`[MeasuredPaint]` in the system's `sparky-stereo-graphicsrc`, written by `sparky-stereo-gpu-record --set-paint KIND WAY` or shipped with a known model's record). Where nothing was measured it is the processor, which is how every Qt paints.
- **The launcher hands it over.** The page's resolver (`sparky-stereo-gpu-env --app ID`) prints `QT_WIDGETS_GPU_PAINT=...` after the GPU's own variables, and Plasma's launcher (KIO) starts the program with every line it prints; `sparky-stereo-gpu-run` does the same for a program started by hand. Nothing is printed for the processor.
- **A value set by hand in the session wins,** as a GPU variable set by hand does, and the page says so.
- **A way chosen for a program is that program's alone.** A terminal or a file manager hands its environment to everything it starts, so a way chosen for it would paint its children too, against their own choices. The edition's Qt reads the variables when the application starts and, when they came with someone to tell (`QT_WIDGETS_GPU_PAINT_TELL`: the page's mark), takes them out of its environment. A value set by hand comes without that mark and is inherited as any variable is. Read it at application start, not at the first window: a terminal starts its shell before it paints. Proof: start a terminal both ways with a shell that writes `env` to a file.
- **What cannot be had is told and kept, and the program still starts.** Before the start the resolver knows two cases: no graphics processor that can draw, and a Qt without the painting (it looks the switch's reader up in the installed Qt Gui: a Qt without it would ignore the variable without a word). After the start only the program knows (no OpenGL in the session, an OpenGL the processor draws, Qt OpenGL not loadable, a surface that cannot be made): the resolver also prints `QT_WIDGETS_GPU_PAINT_TELL=COMMAND`, and the edition's Qt runs `COMMAND --paint-failed PROGRAM CODE WORDS` once. The problem is kept by the desktop's one problems engine with "Paint on the processor" as the person's explicit choice. While a failure is kept the resolver adds `QT_WIDGETS_GPU_PAINT_TELL_OK=1`, and the first window that does paint on the GPU runs `COMMAND --paint-ok PROGRAM`, which ends it.
- **Proof on installed packages:** install the page's package in a throwaway container, write the choice as the page writes it, start a program the way the menu does (`kioclient exec /usr/share/applications/ID.desktop`), then read `/proc/PID/environ` of the program, its `painting on "RENDERER"` line and its DRM client in `/proc/PID/fdinfo`; start it once with `LIBGL_ALWAYS_SOFTWARE=1` and read the kept problem; start it again and see the problem gone.

Traps of this part:

- **Symptom:** a program whose desktop entry sets `PrefersNonDefaultGPU` itself never gets the painting variable. **Cause:** KIO asks the page's resolver only for entries without that key. **Fix (work to do):** KIO asks for the painting's variables alone (`--print paint-env`) for those entries. **Found by:** reading the launcher's patch before choosing where the variable is printed.
- **Symptom:** the kept problem names the renderer as `LLVM 21.1.8, 256 bits)`. **Cause:** the renderer's name has parentheses of its own, and the text after the last opening one was taken. **Fix:** take what follows the fixed words. **Found by:** the installed-package proof's one failing line.
- **Symptom:** a message that should be in the person's language is English in a test container. **Cause:** `LANGUAGE=pt_BR` does nothing under the `C` locale, and the image had no `pt_BR.UTF-8`. **Fix:** `localedef -i pt_BR -f UTF-8 pt_BR.UTF-8` in the image and `LANG=pt_BR.UTF-8` in the test. **Found by:** the same message came out right through the problems engine's own catalogue.
- **Symptom:** a D-Bus activatable program is now started by the launcher itself. **Cause:** the launcher starts such a program itself whenever the resolver's answer is not empty, and the painting variable makes it so. That is what carries the variable to the program; say it in the hand-back.

## Qt's own frame at a fractional scale (the 125 % offset)

**Symptom:** at 125 % a window flushed through the RHI (every GPU path, and stock Qt's `QT_WIDGETS_RHI=1`) lies one pixel left of the same window as a shared memory buffer, and one row is displaced part of the way down (291,114 of 2,250,000 pixels in a terminal).
**Cause:** not the painting and not the RHI: Qt's own frame around the window. With a frame the client draws, the Wayland EGL context renders the content into a framebuffer and blits it with the frame (`DecorationsBlitter::blit()` in `qwaylandglcontext.cpp`); it passed products of logical sizes and the scale to `glViewport()`, which truncates them, while the surface's buffer and the content framebuffer are sized with `QSize * qreal` (rounded) and the shared memory store rounds the frame's margins. So the content was placed one pixel left and drawn one pixel smaller than its framebuffer.
**Fix:** place the content from the buffer's top by the rounded margins and draw it at its framebuffer's size.
Measured on a terminal at 125 %, nothing moved before comparing: 291,114 differing pixels before, 1,840 after, and 0 at scales 1 and 2 between the published plugin and the fixed one.
What is left is one row at the content's lower edge: the shared memory store gives the content the buffer's rounded height less the rounded margins, the EGL window a framebuffer of the content's own rounded height, and the two differ by a row at some sizes. That is a disagreement between the two stores, which the open report below describes, not the blitter's offset.
**Found by:** the same comparison with a window without a frame: 0 differing pixels between the shared memory window and the RHI one; then reading the three places that turn a logical size into pixels. A first fix that placed the content by the rounded bottom margin left it one row off everywhere: the store counts from the top.
**Upstream:** Qt's dev branch no longer has this code (94f96210518d, David Edmundson, "wayland: move decoration into subsurfaces"); 6.11 and 6.12 do. [QTBUG-149635](https://bugreports.qt.io/browse/QTBUG-149635) (a one-pixel seam with client-side decorations at a fractional scale) is open and related.
**Where it shows:** only where Qt draws its own frame (a compositor without server-side decorations, a test rig without a decoration plugin). Under KWin's own decoration there is no blitter and no offset.

## The pair where the EGL has no surface with two views

A window painted once per eye on the GPU needs somewhere to put the second eye.
With `EGL_EXT_multiview_window` (the edition's Mesa) the window's surface has two views and each takes its half of the pair texture.
NVIDIA's own EGL has no such surface, and the window was shown flat, which was said.
The shared memory pair never needed EGL: its buffer is twice as wide, declared full side by side and as the desktop's own depth.
The GPU pair now does the same:

1. **Who decides:** the Wayland EGL window, when the wish changes (`_q_stereo_views` set by the widgets' repaint manager, with `_q_stereo_pair` saying that the engine composes the pair itself). Qt Quick's renderer draws into two views and never sets `_q_stereo_pair`, so it is not touched. The change is made on the GUI thread, in the property's own event, which the repaint manager sends before it flushes: the first pair frame already has the new width.
2. **The buffer:** `ensureSize()` doubles the width; the `wl_egl_window` is resized; the surface's `wp_viewport` destination stays one view's size, which is what a compositor takes as the size of one view of a declared surface.
3. **The declaration:** the same call the shared memory store makes (`QWaylandStereoDepth::setPair()`: `kde_stereo_content_v1.set_content(side_by_side_full)` and `kde_stereo_depth_v1.set_desktop_depth(1)`, with the next commit), made again for a new surface.
4. **The swapchain:** the window says `_q_stereo_side_by_side_buffer`, and the OpenGL RHI swapchain's `surfacePixelSize()` doubles its width for it, so the compositor's size check before the frame resizes it.
5. **The frame:** `QBackingStoreDefaultCompositor::flush()` draws the pair texture whole over the whole target (source rectangle twice as wide, one quad), and each render-to-texture child twice, by setting the viewport to each half: a child's quad is placed for one view, so its uniforms need no change.

Proof on the NVIDIA card (the gallery window, frameless, a 3D mode of a nested Stereo KWin, both eyes captured), 2026-11-13:

| Case | Shared memory pair (CPU) | Batched | OpenGL engine | The same window before (flat) |
|---|---|---|---|---|
| Parallaxes 2, -2, 1, -1, 4, -4 | as given | as given; each eye differs from the CPU pair in 613 of 1,310,720 pixels, none by more than 32 levels | as given | 0, 0, 0, 0, 0, 0 |
| Parallaxes 0.5, -0.5, 1.5, -1.5, 0.25, 1 | 1, -1, 2, -2, 0, 1 (rounded) | 0.5, -0.5, 1.5, -1.5, 0.25, 1.0 | 0.5, -0.5, 1.5, -1.5, 0.263, 1.0 | |
| The eyes exchanged (the control that must fail) | fails | fails | fails | |
| A window with a render-to-texture widget | | per eye, as given | | |
| No depth | eyes identical | eyes identical | | |
| Stereo Union, ElementLimit 12 | | every box the CPU pair's disparity | | |
| Text of a button at half a pixel (mean difference between neighbours; higher is sharper) | 18.2 in both eyes (whole pixels) | 19.4 in the eye with the half pixel, 18.2 in the other | 13.0 and 18.2 | |
| A 2D output | | 0 pixels differ from the build before | | |
| On the wire | | one `set_content(3)`, one `set_desktop_depth(1)`, no warning | | |

A window with a frame the client draws stays flat on every path (work to do: the frame blitter drawing content and frame once into each half, or into each view).

Traps of this part:

- **Symptom:** after a rebuilt Wayland EGL plugin is put over the installed one, every window is black or painted on the processor, and the log says `Failed to load client buffer integration: "wayland-egl"`. **Cause:** the plugin calls a function the build newly exports from the Wayland client library, and the installed library has no such symbol. **Fix:** put the client library of the same build beside the plugin. **Found by:** a comparison in which the GPU path equalled CPU painting exactly, pixel for pixel, which a GPU path never does.
- **Symptom:** on a 2D session of the test rig the client dies with `interface 'kde_stereo_depth_v1' has no event 1` as soon as a pair is forced. **Cause:** the rig's older compositor sends an event the client's protocol version does not have ([stereo-proof-rig](../../stereo-proof-rig/SKILL.md), versioned events), and the rig's stand-in for it was loaded only in 3D sessions. **Fix:** the 2D control is the window without depth, which is what a 2D output gets (no style shows depth there). **Found by:** a black capture and the client's last line.
- **Symptom:** a helper written as a shell function does not run under `env VAR=value helper ...`, and every case that used it leaves no capture. **Cause:** `env` starts programs, not shell functions. **Fix:** export the variables in a subshell and call the function there. **Found by:** only the cases without the helper had results.
- **Symptom:** a test commit of a source tree that tracks only the touched files suddenly holds 7,000 files. **Cause:** `git add -A DIR` adds every untracked file under it. **Fix:** add the changed files by name, or `git add -u`. **Found by:** `git diff --stat` of the series.

## What the first prototype measured (2026-11-11)

One machine, a Ryzen with a Renoir iGPU (Mesa radeonsi) and an RTX 3060 (NVIDIA 615), nested Stereo KWin on the same GPU as the program, Qt's own window frame, 1920x1080, three rounds, CPU and GPU painting alternating.
Read the numbers as one machine's, and measure again on a slower CPU before deciding anything.

| Case | CPU painting | OpenGL paint engine |
|---|---|---|
| Konsole, a full-screen colour animation (160x48 cells) | 9 ms per paint, the terminal takes 297 frames a second | 18 to 20 ms per paint, 221 to 242 frames a second |
| Konsole, `cat` of a 20 MB file | 27 MB/s | 27 MB/s (Mesa), 24 MB/s (NVIDIA) |
| Konsole idle, cursor blinking | 0.1 % of a core | 0.3 % |
| Dolphin scrolling 5,000 files | 19 to 22 % of a core, KWin 6 to 9 % | 26 to 35 %, KWin 5 to 6 % |
| Kate scrolling 60,000 lines | 10 to 12 %, KWin 5 to 7 % | 16 to 17 %, KWin 4.5 % |
| Every widget of a 900x760 window repainted | 4.0 to 4.5 ms | 1.5 ms (Mesa), 2.3 ms (NVIDIA) |
| The same, once per eye (element depth) | 8.8 to 9.3 ms | 3.2 ms (Mesa), 4.1 ms (NVIDIA, shown flat) |
| `QT_WIDGETS_RHI=1` (stock: CPU painting, RHI composition) | | Kate: 13 ms per flush and 58 paints a second instead of 82 |

What the numbers say:

- The OpenGL engine's cost follows the number of things drawn, not the pixels: one draw call with its own uniforms for each rectangle, text run and pixmap. A terminal draws thousands of small things a frame and loses; a window of large fills and few items wins.
- The compositor saves a little (no upload of a shared memory buffer); the program pays more than that back.
- Painting once per eye is where the GPU path pays: the pair costs about a third of the CPU's time on Mesa.
- Text at scale 1 uses the same glyphs; some labels sit one pixel higher. At a fractional scale (1.25) the engine places every glyph on a whole pixel, so letters are spaced unevenly where the raster engine places them by parts of a pixel.
- An element moved by half a pixel is drawn with linear filtering, so its text is soft in the eye that carries the half pixel and sharp in the other.
- With whole-pixel parallaxes both paths gave the same disparities to the thousandth of a pixel; with fractions the GPU path gave 0.5, -0.5, 1.5, -1.5 and 0.263 (for 0.25, the four samples' grid) where the CPU path rounds to 1, -1, 2, -2 and 0.

## What the batched path measured (2026-11-11)

The same machine and rig; Qt's frame around the window; 1920x1080; the three paths alternating.
One round only, on a station other work was loading (the load before a run: median 9.7 on 12 threads, 10 of 42 runs above 12), so read each number as one run's and the differences between paths as the finding.
The times are the repaint manager's: the paint pass (the program's paint code and the engine), then the flush.

| Case | CPU painting | OpenGL paint engine | Batched |
|---|---|---|---|
| Konsole, the colour animation (13,400 rectangles a paint), Mesa | 16.4 + 0.06 ms | 25.6 + 0.7 ms | 5.0 + 1.1 ms |
| The same, NVIDIA | 13.4 + 0.05 ms | 39.2 + 0.5 ms | 8.3 + 1.7 ms |
| Konsole, `cat` of 20 MB (2,570 glyphs a paint), Mesa | 15.0 + 0.06 ms, 11.6 MB/s | 16.8 + 0.8 ms | 8.6 + 0.9 ms, 16.8 MB/s |
| The same, NVIDIA | 12.2 + 0.05 ms, 15.7 MB/s | 25.4 + 0.4 ms, 11.8 MB/s | 9.2 + 1.0 ms, 16.3 MB/s |
| Kate scrolling, Mesa | 1.2 + 0.1 ms, 19 % of a core | 1.6 + 0.6 ms, 30 % | 0.6 + 1.2 ms, 22 % |
| Kate scrolling, NVIDIA, a quiet station | 0.8 + 0.1 ms, 15.5 % | | 0.8 + 1.5 ms, 24 % |
| Dolphin scrolling, NVIDIA, a quiet station | 1.3 + 0.03 ms, 23.6 %, KWin 10.9 % | | 1.0 + 0.6 ms, 25.5 %, KWin 6.5 % |
| Konsole typing (a character every 50 ms), Mesa | 3.2 % of a core | 6.4 % | 5.8 % |
| Konsole idle, cursor blinking | 0.2 % | 0.5 % | 0.4 % |
| A key to its frame in Konsole (median of 120 keys) | 11.6 to 12.7 ms | 12.9 to 14.4 ms | 12.0 to 12.2 ms |
| Memory of Konsole (RSS), Mesa | 156 MB | 180 MB | 187 MB |
| Memory of Konsole (RSS), NVIDIA | 234 MB | 319 MB | 334 MB |
| Draw calls for a paint pass | | one for each thing painted | 1 or 2 |

What the numbers say:

- Batching removes the first prototype's loss: a terminal's paint pass costs a third to three quarters of CPU painting's, where the OpenGL engine cost one and a half to three times as much.
- What is left of a paint pass is the program's own paint code and `QPainter`'s front end (text layout): of 8 ms, the engine's calls took about 1 ms and the draw 0.15 ms. A painting path cannot remove that.
- A frame through the GPU has a fixed cost of about a millisecond (the frame, a pass, the swap). A window that paints little (an editor scrolling by three lines, a blinking cursor) pays more for that than it saves on this CPU; the compositor saves its upload.
- The key-to-frame time does not depend on the path: a terminal's own wait before it repaints is ten times the difference.
- A process that paints on the GPU carries an OpenGL driver: about 30 MB with Mesa, about 100 MB with NVIDIA's, for every program.
- On a slower CPU or a larger screen the raster engine's share grows and the fixed cost does not; measure there before choosing a default.

## Traps

- **Symptom:** a terminal painted on the GPU takes a third of the output it took before, and the flush time is 12 ms. **Cause:** `QWaylandGLContext::swapBuffers()` emulates a blocking swap (`waitForFrameSync(100)`) when the context's format has a swap interval above 0, and widgets are painted and flushed on the GUI thread, which also reads the terminal's program. **Fix:** swap interval 0 in the format the window's RHI is made with. **Found by:** `flush_ms` in the repaint manager's statistics, 12.8 ms at 60 paints per second against 0.07 ms on the raster path.
- **Symptom:** text moved by half a pixel does not move at all. **Cause:** the OpenGL engine snaps a translation to whole pixels for glyphs (`snapToPixelGrid` in `updateMatrix()`), and samples its glyph cache with `GL_NEAREST`. **Fix:** add the part of a pixel after the snap, and filter linearly while it is not zero. **Found by:** reading `updateMatrix()` before the first capture.
- **Symptom:** an image build copies the whole package repository (15 GB) into Docker's build cache. **Cause:** `docker build --build-context repo=DIR` sends the folder even for a `RUN --mount=type=bind,from=repo`. **Fix:** fill the image in a container that bind-mounts the repository read-only, then `docker commit`. **Found by:** the build log's "transferring repo: 9.98GB".
- **Symptom:** `apt-get install konsole dolphin` on the edition's repository alone stops with `libavcodec63 ... Depends libaom3 (>= 1:3.15.3) but none of the choices are installable`. **Cause:** Konsole's part and Dolphin need Qt Multimedia, the edition's is built on its FFmpeg, and that FFmpeg needs deb-multimedia's libraries. **Fix:** install `deb-multimedia-keyring` from the edition's repository and add deb-multimedia's source before the install. **Found by:** apt's own explanation of the two conflicting assignments.
- **Symptom:** `kwin_wayland: Operation not permitted` in a container. **Cause:** its file capability needs `--cap-add SYS_NICE`.
- **Symptom:** the first line of a Dockerfile, `# syntax=docker/dockerfile:1`, hangs the build. **Cause:** it pulls the frontend from Docker Hub, and the CLI's credential helper is locked on a station without a desktop prompt. **Fix:** leave the line out; BuildKit's built-in frontend knows `RUN --mount`.
- **Symptom:** Qt's Gerrit REST answers 403 to an anonymous query, and bugreports.qt.io redirects. **Fix:** read issues through Jira's REST on the new host (`https://qt-project.atlassian.net/rest/api/2/issue/QTBUG-N?fields=...`), and search qtbase's history through the GitHub mirror's commit search.
- **Symptom:** a stereo capture of a widget window with element depth shows both eyes the same, on the CPU path too. **Cause:** the rig's KWin has no decoration plugin installed, so Qt draws its own frame around every window, and a window with a client-drawn frame is painted once. **Fix:** install a KWin decoration, or test with a frameless window (`Qt::FramelessWindowHint`). **Found by:** the capture showed Qt's own title bar, and `QWindow::frameMargins()` was not null.
- **Symptom:** the Union widget style draws, but no element has depth, and the log says `union.general: Could not find a supported platform plugin for platform "wayland" and session names QList("")`. **Cause:** Union picks its platform plugin by the session's desktop name. **Fix:** start the program with `XDG_CURRENT_DESKTOP=KDE XDG_SESSION_DESKTOP=KDE KDE_FULL_SESSION=true KDE_SESSION_VERSION=6`. **Found by:** the log line; with the variables the eyes differ.
- **Symptom:** a preload meant for the rig's KWin does nothing. **Cause:** `kwin_wayland` carries a file capability, and the loader ignores `LD_PRELOAD` for such a program. **Fix:** run a copy of the binary (a copy has no capability) with the preload. **Found by:** the client still died with the event the preload should have dropped.
- **Symptom:** the first frame of a window painted once per eye on the GPU shows one eye, and a window that paints only once stays that way. **Cause:** the Wayland EGL window takes its second view at the start of the next frame, never inside one (`QWaylandEglWindow::beginFrameViews()`), so the frame that sets `_q_stereo_views` is flushed to a surface with one view. **Fix:** ask for another paint when the pair starts or ends. **Found by:** a warning placed where the compositor draws a pair into a swapchain without stereo fired once in every run and the capture was still right, because the gallery repainted.
- **Symptom:** on NVIDIA's own driver a window painted once per eye on the GPU shows the left eye, flat, while the same window painted on the CPU has depth. **Cause:** the pair needs a surface with two views (`EGL_EXT_multiview_window`), which the edition's Mesa has and NVIDIA's EGL has not; the shared memory pair needs no EGL. **Fix:** one buffer twice as wide holding the eyes side by side, declared as the shared memory pair is ([above](#the-pair-where-the-egl-has-no-surface-with-two-views)). **Found by:** the same warning, and a capture with identical eyes.
- **Symptom:** a window with Qt's own frame, painted once per eye on the GPU, shows the left eye only. **Cause:** not found; the decorated EGL window's content framebuffer has a slot per eye only for a window that asked for stereo when it was made. **Fix in the prototype:** such a window is painted once, as on the CPU. **Found by:** captures with identical eyes.
- **Symptom:** an idle terminal reports about five paints per second on one path and none on the other. **Cause:** the only statistics line of the run was the start-up second, and the cursor never blinked: Konsole reads `BlinkingCursorEnabled` from the profile's `[Terminal Features]` group. **Fix:** the right group, and a summary that reports "no paints" when the run printed nothing after the warm-up. **Found by:** reading the run's log instead of its summary.
- **Symptom:** numbers measured before a cut-off cannot be tied to the source tree found afterwards. **Cause:** the library was older than the last edits (`ninja -n` only says CMake must run again; `git stash` and `git stash pop` also give every changed file a new time). **Fix:** commit before every measuring round, and write the commit into the round's folder. **Found by:** rebuilding changed the library's size.
- **Symptom:** "GPU painting" is slower than CPU painting and `GL_RENDERER` says `llvmpipe`. **Cause:** Mesa's EGL follows the compositor's main device; with the compositor on a GPU Mesa has no driver for (NVIDIA's own driver) and Mesa's vendor file named, the context comes up in software unless `DRI_PRIME=pci-...` names a Mesa GPU. **Fix:** name the GPU as well as the vendor, and refuse a software renderer by its name, saying so. **Found by:** printing `GL_RENDERER` in a container that had both GPUs.
- **Symptom:** captures at `kwin_wayland --virtual --scale 1.25` are identical, pixel for pixel, to the captures at scale 1. **Cause:** the virtual backend's option enlarges the output; the windows stay at 1. **Fix:** set the scale as the display settings do, `kscreen-doctor output.NAME.scale.1.25`, and read it back. **Found by:** the same count of differing pixels in both pairs of captures.
- **Symptom:** a run on a rig image without a GPU cannot be captured (`Screenshot got cancelled`). **Cause:** Stereo KWin's virtual output needs a render node. **Fix:** give the container a GPU for KWin and switch only the program to software with its own environment.
- **Symptom:** the shaders of a new Qt Gui file cannot be baked: the build image has `libQt6ShaderTools` but no `qsb`. **Cause:** `qsb` is in `qt6-shader-baker`, which nothing in a qt6-base build depends on (qtbase keeps its `.qsb` files baked in the source). **Fix:** `apt-get download qt6-shader-baker`, `dpkg-deb -x` it into the work folder and run `usr/lib/qt6/bin/qsb --glsl "300 es,330,150,130" --hlsl 50 --msl 12 -o X.qsb X`; record the package's version and hash. **Found by:** `ls /usr/lib/qt6/bin`.
- **Symptom:** `QT_WIDGETS_GPU_PAINT=batch` does nothing. **Cause:** the switch was read with `qEnvironmentVariableIntValue()`, which gives 0 for a word. **Fix:** read the value as text and name the accepted words in the warning for any other. **Found by:** reading the switch's three readers before building.
- **Symptom:** a tool bar has a line of the window's background colour around it, one pixel wide; 1,580 pixels differ in each of three programs. **Cause:** a rectangle drawn with a pen was split into a native inside and four raster-drawn sides that left one row and one column between them. **Fix:** whole-number corners for the inside, and sides that end exactly there. **Found by:** the same count of differing pixels in three different programs, then the crop.
- **Symptom:** a dashed rectangle has its dashes elsewhere on one side. **Cause:** drawn under a narrower clip, the raster engine's dash stroker starts its pattern at the clip. **Fix:** dashed outlines are drawn in one part. **Found by:** the paint check's cell of dashes.
- **Symptom:** a picture scaled down without smoothing differs in whole rows and columns (1,100 pixels, by up to 255 levels). **Cause:** where a sample falls exactly between two texels the raster engine takes the one before, the GPU the one after. **Fix:** take the sample a little before its place (`floor(texel - 0.002)`). **Found by:** the paint check's large picture, a checkerboard, where a wrong row shows.
- **Symptom:** a warning names composition mode 37, and Kate's text cursor is black on a dark ground. **Cause:** `QTextLayout::drawCursor()` sets `RasterOp_NotDestination` when the engine's features include `RasterOpModes`. **Fix:** an inverting blend for rectangles, and raster-drawn coverage for anything else in that mode (the cursor is a line at a fractional scale). **Found by:** the warning, then `grep NotDestination` in Qt Gui.
- **Symptom:** every cell of the paint check differs at scale 1.25, by a column at each vertical edge. **Cause:** not the painting: the same window with an EGL surface lies one pixel left of the window with a shared memory buffer at that scale (every path that flushes through the RHI; see the trap on programs at 1.25 below). **Fix:** compare each capture from its own corner mark. **Found by:** the mark's column, 74 in one capture and 73 in the others.
- **Symptom:** with LCD antialiasing, text the raster engine draws for the batched path (rotated, under a round clip) is grey where CPU painting has coloured fringes. **Cause:** two: on a transparent ground the raster engine blends an LCD mask as grey, and for a painter on an image it asks the font for 8-bit masks. **Fix:** draw such text white on black, on a device that says it is a widget, and blend the pen's colour through the coverage. **Found by:** saving the scratch image (`QT_WIDGETS_GPU_PAINT_DUMP`): the text there was grey.
- **Symptom:** LCD text at 70 per cent opacity differs from CPU painting over every glyph. **Cause:** `s->flags.fast_text` needs an opacity of 1; otherwise `alphaPenBlt()` makes spans whose coverage is the mask's green channel. **Fix:** the same choice in the shader. **Found by:** reading `alphaPenBlt()` after the cell of opacity failed only with LCD text.
- **Symptom:** the fragment shader with two outputs does not compile on OpenGL ES. **Cause:** `qsb` writes `layout(location = 0, index = 1)` into the `300 es` source without `#extension GL_EXT_blend_func_extended : require`. **Fix:** insert the line after `#version` when the shader is loaded (`QShader::shader()`, `setShader()`), and use that shader only where the context has the extension. **Found by:** `qsb --dump`. NVIDIA's EGL gives Qt an OpenGL ES 3.2 context by default.
- **Symptom:** the right eye of a Stereo Union window painted on the batched path misses its rounded boxes, and the log says the scratch image is full. **Cause:** a window painted once per eye gets a store twice as wide while records already point into the scratch image, which was made for the narrower window and refused to be remade. **Fix:** the image grows wider or taller and keeps every texel where it is. **Found by:** the warning, and 41,191 pixels of the right eye off by more than 32 levels.
- **Symptom:** a dialog repainted whole uploads 6 MB a frame and its flush takes 5 ms, where the first prototype's took 1 ms. **Cause:** two. Every rounded rectangle of the style (buttons, the frame around a text view with all its inside) went to the raster engine whole. And the raster-drawn parts are packed in rows as wide as the window, where one tall side strip makes a tall row, and whole rows were uploaded and emptied. **Fix:** the inside of a rounded rectangle as a rectangle of the brush with four raster-drawn sides, and each part its own entry of the upload (`QRhiTextureUploadDescription::setEntries()`, a copy of the part). **Found by:** `uploaded_kB` and the kinds in the statistics of a window whose every widget repaints; the first fix alone changed the count of parts and not the kilobytes.
- **Symptom:** at scale 1.25 Konsole and Dolphin painted on the GPU differ from CPU painting all over (99,356 pixels of Konsole's window), while the paint check's window of 1280 by 700 passes. **Cause:** not the painting. The same raster picture flushed through the RHI (`QT_WIDGETS_RHI=1`, stock Qt) differs from the shared memory window in the same 96,589 pixels: on an EGL surface the window lies a pixel left, and where its size is not whole at that scale one row is displaced part of the way down. Against that RHI capture the batched picture differs in 4,421 pixels, each by one level. **Fix:** at a fractional scale, compare a GPU path with CPU painting flushed through the RHI, not with the shared memory window. **Found by:** measuring the displacement region by region (1, -1 at the top, 1, 0 at the bottom), then the control.
- **Symptom:** at scale 1.25 Dolphin painted on the GPU has black lines one pixel wide between its items and beside its side bar; other programs have none. **Cause:** Dolphin's window is translucent, and the store emptied each dirty rectangle to every pixel it touches (rounded outward) where the painting that follows covers the rounded rectangle; the column between stayed empty. **Fix:** round the emptied rectangle as a fill is rounded. **Found by:** a colour for new textures (`QT_WIDGETS_GPU_PAINT_GROUND`) showed the lines were painted, not left; the list of the frame's records (`QT_WIDGETS_GPU_PAINT_DUMP`) showed a transparent rectangle 180 to 182 followed by fills 180 to 181.
- **Symptom:** a check that passed at scale 2 fails there after an unrelated change, in the one cell with a pattern brush (25,200 pixels). **Cause:** the pattern's start depends on where the raster-drawn part lies in the scratch image, and the change moved the parts; before, the place happened to be a multiple of the pattern's period. **Fix:** the brush origin, as in the table above. **Found by:** the failing cell's size, exactly the pattern rectangle's, and `getBlendType()` in `qdrawhelper.cpp`. A check that passes may pass by the luck of a placement: vary the placement.
- **Symptom:** a frame with one thin vertical line uploads 7 MB. **Cause:** the raster-drawn parts are packed in rows across an image as wide as the window, and the whole rows were uploaded. **Fix:** upload the columns in use. **Found by:** `uploaded_kB` in the statistics of a terminal with a scroll bar.
- **Symptom:** Konsole's "frames per second" in the DOOM fire benchmark follow the painting path only a little. **Cause:** Konsole repaints about 20 times a second whatever arrives, and the fire is 13,400 rectangles and no glyph (block characters are drawn as rectangles); the count measures how fast the terminal reads. Of an 8 ms paint pass the engine's own calls take about 1 ms and the draw 0.15 ms; the rest is the program's paint code and `QPainter`'s front end. **Found by:** the statistics' `rectangles`, `glyphs` and `engine_ms` (`QT_WIDGETS_PAINT_STATS=2`).
- **Symptom:** a measuring matrix started with a shell tool's ten-minute limit is still wanted an hour later. **Fix:** start it detached, write a last line when it ends, and wait for that line in short waits; never replace the libraries a running matrix mounts.

## Find where the processor time goes before choosing a default

Added 2026-11-13 after the small-machine fixed-work run.
A shorter paint pass is not evidence that the process uses less processor.
The GUI-thread paint timer measures a wall-time interval; process accounting includes every thread, parsing, layout, driver work, flushes and work outside that interval.
Waiting for a frame can lengthen a timer without consuming the same amount of processor.
Only matched profiles can show which work replaced a saving.

1. Keep the fixed workload, requested frames, actual paints, rate, geometry, source commit and loaded-library hashes identical.
2. Inside the isolated rig, check `perf stat -e cpu-clock:u -- true` before a long run.
   Missing perf and refused events are explicit unavailable results, not empty successful profiles.
   [Kernel perf security](https://docs.kernel.org/admin-guide/perf-security.html) describes CAP_PERFMON; grant only a container-scoped capability when authorized, never change the person's host perf policy for a probe.
3. Build the same Qt with matching debug information or frame pointers; preserve build IDs and the unstripped libraries used by the measured process.
   A Release ELF's symbol table can name functions but is not line-level debug information.
   Use `readelf -S` to check for `.debug_info` and `readelf -n` for the build ID.
4. Record only the owned client and nested compositor, across the same work window:
   `perf record -e cpu-clock:u -F 99 --call-graph dwarf,8192 -p CLIENT_PID,KWIN_PID -o perf.data -- sleep 20`.
   Attach before the work begins or align the start to its absolute monotonic time; save the actual profile interval and reject a missed window.
   Keep profiler overhead separate from the unprofiled load table.
5. Read `perf report --stdio --no-children --sort comm,dso,symbol -i perf.data` and unresolved-symbol counts.
   Separate the program, Qt text/layout, the paint engine, region/copy work, RHI flush and the GL driver, including its worker threads.
   Do not add inclusive call-tree percentages: the caller and its descendants overlap.
   Scale exclusive user samples by measured user CPU time, and leave system CPU time and unresolved samples as separate buckets.
6. Limit only the experiment when comparing a small machine: record the container's CPU count/quota, cpuset, throttling, frequency and temperature alongside each row.
   A quota changes available execution time; it does not make a newer processor the older architecture.
   Accept a claimed calibration only after both processor-painting control rows and their spread match the reference closely enough, with the actual mismatch stated.
   No small-machine calibration or function attribution was established in the first milestone 4 rig because perf access was refused.
7. Measure each proposed engine change again at the same work, on both paths and cards, with a red control and a quiet three-round table.
   Keep the three choices; a profile is a reason to test a change, not a reason to silently change Automatic.

### The small machine changed the conclusion

Processor milliseconds per requested frame, program and nested compositor together, median of three quiet runs on an AMD A10 with Carrizo and Hainan (118 valid runs in the complete matrix).
The card names came from the run's renderer, not the order of the device nodes.

| Work | Processor painting | Batched, Hainan | Batched, Carrizo |
|---|---|---|---|
| Terminal animation | 34.6 | 32.3 | 33.7 |
| Terminal text | 30.7 | 28.8 | 30.8 |
| File manager scrolling | 11.7 | 12.6 | 11.3 |
| Editor scrolling | 9.9 | 9.9 | 10.7 |
| Editor typing | 25.6 | 30.6 | 31.7 |

Compare with the Ryzen/RTX station table above: its quiet terminal rows saved 20 to 40 percent, while this machine's terminal gain is 0 to 7 percent inside the spread.
Editor typing costs 20 to 24 percent more batched on the small machine.
The small machine's animation paint interval fell from 16.2 ms to 8.4 ms plus a 4.6 ms flush, while the program's processor time stayed about 30 ms per requested frame.
That establishes the discrepancy, not its per-function cause.
Permission-free station profiles below identify shared work and added driver costs; they do not allocate the small machine’s remaining milliseconds by function.
Automatic stays processor painting; a measured rule per program is a proposal requiring a design decision, not a shipped default.

### A decorated pair candidate on the GPU

This candidate is excluded from the package after the fractional edge failures below; the existing client-frame exception stays.
In its scoped successful rows, the client-side frame is identical in the two eyes, with the content in its own half of one double-width FBO.
The Wayland EGL platform advertises this capability to Widgets; other platforms keep their existing frame exception.
The blitter draws the decoration with its full texture coordinates and then samples the left or right half of the content texture into that eye's content rectangle.
This route also avoids changing a previously mono decoration context into a native two-view context.

Measured in the rig on AMD and NVIDIA, scales 1 and 1.25, through an application-driven resize to logical width 940 and hide/show:

| Check | Batched | Qt OpenGL engine |
|---|---|---|
| Requested disparities 0.5, -0.5, 1.5, -1.5, 0.25, 1 | exact | known multisample grid error; 0.226 for 0.25 at scale 1.25 |
| Vertical disparity | 0 | centroid residual at most 0.024 px |
| Frame pixels differing between eyes | 0 | 0 |
| A render-to-texture child inside the decorated window, scale 1.25 after resize/hide/show | exact element disparities; the child's 22,500 pixels identical between eyes, on both cards | |
| Earlier build / flat-exception control | all disparities 0 | |
| 2D new against earlier build | 0 differing pixels | |

This still paints a window once per eye.
It does not implement both eyes from one recorded paint callback and does not establish that pair's processor cost.
The fractional-scale blitter fix and the one-row extent remainder remain separate: QTBUG-149635's attachment shows the same visible right/bottom seam class, not a proof that its dimensions reproduce our exact rounding disagreement.

An additional logical-width-941 case at scale 1.25 fails on both cards: content splits across the eyes after either an application-driven or compositor-driven resize. The fixture logs depth/pair/SBS true and logical backing-store width 1882. The batched texture rounds `1882 * 1.25` to 2353, but the default compositor recognises a pair only when its texture width equals `2 * round(941 * 1.25)`, which is 2352. Its mono branch then maps the wrong content into the decorated pair. This remains open; the even-width lifecycle table does not qualify arbitrary fractional sizes. A fix needs a shared physical eye extent and eye origin across painting, texture selection and the EGL FBO; merely weakening the pair-width check does not prove alignment.

### Traps found while packaging and profiling

- **Symptom:** installed client processes and their hardware-renderer logs pass, but the screenshots are black.
  **Cause found in the rig:** the vendor pin was applied to clients after the nested compositor had already chosen its EGL path.
  **Fix:** pin the compositor before starting it too, reject blank pictures in the capture gate, and inspect a representative picture.
  **Found by:** viewing the supposedly successful installed-page capture; moving the pin before KWin restored visible window content. The precise driver-side reason for the unpinned failure was not profiled.
- **Symptom:** an AMD-pinned run says it rendered on NVIDIA but its summary says valid.
  **Cause:** glvnd tried NVIDIA first, while the placement check ran only if engine counters were present.
  **Fix:** name Mesa's EGL vendor for AMD pins and reject GPU placement as unverified when the kernel exposes no engine-time evidence.
  **Found by:** a two-GPU dry run's renderer line, empty fdinfo counters and an old parser accepting the same input the corrected parser rejects.
  A vendor string alone does not prove a physical GPU when two cards share that renderer family.
- **Symptom:** the lane build works but the exported patch series cannot build the engine or embed its shaders.
  **Cause:** a partial Git snapshot omitted the edited Gui CMake file; its build still read the untracked file.
  **Fix:** compare every build input against the published source, capture the CMake diff and qualify the source package independently.
  **Found by:** `git ls-files src/gui/CMakeLists.txt` returned nothing while the file contained the new source and resource entries.
- **Symptom:** a Git patch containing baked shader binaries cannot be applied by quilt.
  **Cause:** quilt applies text patches, not Git binary patch payloads.
  **Fix:** carry the checked baked resources through source format 3.0's explicit `debian/source/include-binaries`, with text-only quilt patches.
  **Found by:** auditing the `.qsb` entries before source preparation, then checking the repacked and re-extracted source.

### When perf is refused: fixed-work Callgrind and native thread time

Symptom: even `perf record -e cpu-clock:u` fails with permission denied in the isolated container, including with `CAP_PERFMON`.
Cause found by the actual event-open failure and the kernel policy readout; container capabilities did not make this event available.
Keep the host security policy unchanged.
Use Debian's `valgrind` package, fetched through HTTPS apt in a separate tools image, and matching program/library debug packages.
`valgrind-dbg` did not exist in the measured Debian archive; verify package candidates rather than inventing a debug package.
The Qt build's own dbgsym packages resolve its inline and LTO functions; Konsole also needs its KPart debug package, and Kate needs KTextEditor debug symbols.
Record exact versions and build IDs.

1. Reuse the fixed-work kit's feed and typing driver, with a short fixed input count, after startup settles.
   The measured continuation used the first 12 terminal animation/text records and 20 typing events, identical files, rates and sequence on both paths.
2. Launch the client with `valgrind --tool=callgrind --instr-atstart=no --separate-threads=yes --trace-children=no --callgrind-out-file=callgrind.out.%p`.
   Enable with `callgrind_control --instr=on PID`, zero before work, then dump the measured part after input completion and drain.
   Keep all client thread files for that part, including driver workers; exclude the terminal feed child and later shutdown dumps.
3. Read `callgrind_annotate --inclusive=yes --auto=no --threshold=100 FILE` for call roots, and group disjoint self costs for totals.
   Inclusive callers and descendants overlap and must not be summed.
   Keep generic memcpy/memset separate unless caller edges establish its purpose; not every copy is an atlas upload.
4. Beside it, repeat natively and snapshot `/proc/PID/task/TID/{comm,stat,schedstat}` over the same input/completion window.
   The first schedstat field is nanoseconds spent on the processor; retain user/system ticks too.
   Sum every program thread, record the compositor separately, and name each driver thread.
   A native driver worker has kernel and scheduling costs that user-space instruction counts cannot turn into milliseconds.
5. Record actual paint callbacks as well as requested inputs.
   Callgrind often slows execution about fifty times; these samples had about 25 to 146 times the native program CPU accounting.
   That ratio includes changed repaint work as well as instrumentation; it is not application speed.
   Instrumentation changed coalescing: 12 animation inputs produced 65/71 paints, 12 text inputs produced one paint on either path, and 20 keys produced 25/21 paints.
   Instructions per input are not instructions for an identical paint count.
   Neither GPU instructions nor kernel work inside driver ioctls is counted by Callgrind.
6. Do not emulate a small CPU by relabelling the station.
   Here a four-CPU cgroup quota left native animation/text processor controls at 14.64/8.50 ms per requested input, far from the A10's 34.6/30.7 ms rows, with different windows and contention.
   No architecture/frequency calibration was established and the small machine's exact attribution stays open.

Measured on the AMD station path, M user-space instructions per requested input, with matching debug symbols:

| Work | Processor painting | Batched | Observation |
|---|---:|---:|---|
| Terminal animation | 171.698 | 90.069 | raster/blending and memory fills fall; parser/model stays almost unchanged |
| Terminal text | 8.088 | 7.508 | text shaping stays on the processor; text coalesced to one paint |
| Editor typing | 22.064 | 21.652 | completion and shaping remain; copies, submission and driver costs are added |

For typing, `QTextEngine::shapeText` has 53.22/53.28 M inclusive instructions for the complete fixed work, while `paintAndFlush` falls from 131.93 to 104.67 M.
Self raster/blending falls from 3.284 to 1.310 M instructions per key, but generic copies rise from 2.978 to 3.527 M and driver work appears at 0.334 M on the GUI thread plus 0.202 M on workers.
Native typing totals were 279/334 ms in the first pair and 230/416 ms in bounded-shutdown repeats, all contended; these are diagnostic samples, not a quiet penalty percentage.
The first batched run has 28.4 ms in the driver's `cs0` thread, absent on the processor path.
This explains why a shorter paint alone cannot establish total offload: parsing, shaping and completion remain, with new copy/submission/driver work.
It does not prove which group dominates the A10's remaining 30 ms.
Candidates in Qt are fewer scratch clears/copies, dirty upload regions and a point/underline fast path; none has a measured saving or changes Automatic.

Primary references: [Callgrind manual](https://valgrind.org/docs/manual/cl-manual.html), [cost and call-edge format](https://valgrind.org/docs/manual/cl-format.html), [kernel schedstat](https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html).

Additional traps found by the raw runs:

- Symptom: a self-cost parser differs from Callgrind's header by a few instructions.
  Cause: the optional header summary differs from the file's final totals in these measured files.
  Fix: require the parsed disjoint self sum to equal the totals footer exactly, and retain both counters; skip call-arc costs when summing self instructions.
  The format specification and footer comparison identified the right consistency check.
- Symptom: a native terminal run times out although every input and resulting paint completed.
  Cause: the final paint preceded the controller reading the feed completion file, and a nonblinking terminal has no later paint.
  Fix: wait for a bounded quiet processor drain after feed completion; preserve the failed run.
  The feed, paint timestamps and idle process identified this ordering error.
- Symptom: a typing measurement finishes but the container waits indefinitely at shutdown.
  Cause: the editor's unsaved-document shutdown did not end after TERM.
  Fix: bound termination and kill only the owned PID before waiting; retain the completed measurement and label forced shutdown.
- Symptom: a new compiler reports the vector-path conversion used but never defined.
  Cause: the batched engine relied on an inline definition available through a previous compiler's PCH.
  Fix: include `private/qpainterpath_p.h` explicitly; the nonmatching-PCH compilation exposed the missing direct include.

### Equal eye extents are necessary but not sufficient

The rejected CSD candidate rounded the complete double width, while the compositor recognized twice the rounded single-eye width.
At width 941 and scale 1.25 these are 2353 and 2352 pixels, so its pair guard selected the mono mapping.
A trial equalized extents and added the right-eye residual; width 941 then passed on AMD.
But width 942 at 1.25 failed with 1926 unequal content-rim pixels, despite identical frame pixels.
The residual was added after primitive pixel rounding, leaving different coverage at the two content edges.
The next change must keep the depth shift separate from a local physical eye origin, apply origin/clip transforms consistently before rounding, and then place each eye at its equal integer boundary.
Keep both red cases.
Qualify odd and even widths at 100, 125, 150 and 175 percent on both cards, both GPU engines, lifecycle and controls before removing the client-frame exception.
The partial trial is not that qualification; its CSD patches stay out of the recipe.
Both eyes from one recorded paint callback also remains unimplemented: shifted/clipped left-eye records cannot reconstruct right-eye-only coverage or style parts with their own depth.
