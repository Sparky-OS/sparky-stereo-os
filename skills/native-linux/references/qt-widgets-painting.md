# How Qt Widgets reach the screen, and painting them on the GPU

Written on 2026-11-11 from Qt 6.11.2 (the edition's qt6-base 6.11.2+dfsg-5+stereo3d15) and two prototypes measured on an AMD Renoir iGPU and an NVIDIA RTX 3060.
Read it before changing how a QWidget window is painted, flushed or measured.
Neither prototype is shipped: both live behind one environment variable in a lane's build, and the numbers below are what they measured.

- `QT_WIDGETS_GPU_PAINT=1` (or `opengl`): the widgets painted by Qt's OpenGL paint engine. Slower than CPU painting for a terminal: one draw call for each thing painted.
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
6. **What is not a rectangle, a glyph or a picture is drawn by the raster engine.** The engine repeats the same call, with the same state, transformation and clip, on a raster `QPainter` that draws into a transparent part of a scratch image; the part is uploaded with the frame and laid over the target at its place in the paint order. The result is the raster engine's by construction. `QT_WIDGETS_PAINT_STATS=1` prints how many of each kind a flush had, `QT_LOGGING_RULES=qt.gui.batchpaint.info=true` names each kind once, and `QT_WIDGETS_GPU_PAINT_DUMP=FOLDER` saves each frame's scratch image.

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
| A dashed outline | Draw it whole: under a narrower clip the raster engine's dashes start elsewhere |
| A picture scaled without smoothing | The place and the size are rounded (`x`, `y`, `width`, `height`, each by itself), and the source is stepped through by the rounded size; a sample that falls between two texels takes the one before (`qt_scale_image_*`: `qCeil(...) - 1`) |
| A picture scaled with smoothing | Each edge is rounded, the mapping of the unrounded rectangle is kept |
| A picture at its own size | Its place is rounded to a whole pixel |
| The text cursor | `QTextLayout::drawCursor()` uses `RasterOp_NotDestination` when the engine says it has raster operations: invert through blending (`OneMinusDstColor`, `OneMinusSrcColor`). At a fractional scale the cursor is a line in that mode: have the raster engine draw the line as coverage, and invert through the coverage |
| `CompositionMode_Source` with a colour that is not opaque | It takes the place of what is there: a batch of its own without blending |

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
- **Symptom:** on NVIDIA's own driver a window painted once per eye on the GPU shows the left eye, flat, while the same window painted on the CPU has depth. **Cause:** the pair needs a surface with two views (`EGL_EXT_multiview_window`), which the edition's Mesa has and NVIDIA's EGL has not; the shared memory pair needs no EGL. **Fix (work to do):** hand the pair over as one surface holding its views side by side, as the edition's Qt already does for 3D content, marked as the desktop's depth. **Found by:** the same warning, and a capture with identical eyes.
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
- **Symptom:** every cell of the paint check differs at scale 1.25, by a column at each vertical edge. **Cause:** not the painting: the same window with an EGL surface lies one pixel left of the window with a shared memory buffer at that scale (both GPU paths, cause not found). **Fix:** compare each capture from its own corner mark. **Found by:** the mark's column, 74 in one capture and 73 in the others.
- **Symptom:** with LCD antialiasing, text the raster engine draws for the batched path (rotated, under a round clip) is grey where CPU painting has coloured fringes. **Cause:** two: on a transparent ground the raster engine blends an LCD mask as grey, and for a painter on an image it asks the font for 8-bit masks. **Fix:** draw such text white on black, on a device that says it is a widget, and blend the pen's colour through the coverage. **Found by:** saving the scratch image (`QT_WIDGETS_GPU_PAINT_DUMP`): the text there was grey.
- **Symptom:** LCD text at 70 per cent opacity differs from CPU painting over every glyph. **Cause:** `s->flags.fast_text` needs an opacity of 1; otherwise `alphaPenBlt()` makes spans whose coverage is the mask's green channel. **Fix:** the same choice in the shader. **Found by:** reading `alphaPenBlt()` after the cell of opacity failed only with LCD text.
- **Symptom:** the fragment shader with two outputs does not compile on OpenGL ES. **Cause:** `qsb` writes `layout(location = 0, index = 1)` into the `300 es` source without `#extension GL_EXT_blend_func_extended : require`. **Fix:** insert the line after `#version` when the shader is loaded (`QShader::shader()`, `setShader()`), and use that shader only where the context has the extension. **Found by:** `qsb --dump`. NVIDIA's EGL gives Qt an OpenGL ES 3.2 context by default.
- **Symptom:** the right eye of a Stereo Union window painted on the batched path misses its rounded boxes, and the log says the scratch image is full. **Cause:** a window painted once per eye gets a store twice as wide while records already point into the scratch image, which was made for the narrower window and refused to be remade. **Fix:** the image grows wider or taller and keeps every texel where it is. **Found by:** the warning, and 41,191 pixels of the right eye off by more than 32 levels.
- **Symptom:** a frame with one thin vertical line uploads 7 MB. **Cause:** the raster-drawn parts are packed in rows across an image as wide as the window, and the whole rows were uploaded. **Fix:** upload the columns in use. **Found by:** `uploaded_kB` in the statistics of a terminal with a scroll bar.
- **Symptom:** Konsole's "frames per second" in the DOOM fire benchmark follow the painting path only a little. **Cause:** Konsole repaints about 20 times a second whatever arrives, and the fire is 13,400 rectangles and no glyph (block characters are drawn as rectangles); the count measures how fast the terminal reads. Of an 8 ms paint pass the engine's own calls take about 1 ms and the draw 0.15 ms; the rest is the program's paint code and `QPainter`'s front end. **Found by:** the statistics' `rectangles`, `glyphs` and `engine_ms` (`QT_WIDGETS_PAINT_STATS=2`).
- **Symptom:** a measuring matrix started with a shell tool's ten-minute limit is still wanted an hour later. **Fix:** start it detached, write a last line when it ends, and wait for that line in short waits; never replace the libraries a running matrix mounts.
