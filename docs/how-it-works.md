<a id="why-one-format-full-side-by-side-at-any-resolution"></a>

# One presentation contract for stereo and HDR

**For program and driver developers, and anyone following the design:** why stereo uses both eyes side by side, each at its own resolution, and how preserving each picture's description could extend the same division of work to HDR. The stereo choice has device-test evidence; the HDR extension is a design awaiting implementation and equivalent testing.

**The stereo contract in three lines.**
- **Stereo KWin** (KDE Plasma's compositor, with our stereo changes) speaks full side by side, at any resolution.
- **Programs** decode or generate stereo in any standard, and deliver full side by side, at any resolution, to Stereo KWin.
- **Outputs** (Stereo KWin's filters at the end, one per kind of screen) convert from that to whatever each screen needs.

That is what makes stereo work across GPUs, across monitors (2D ones included) and across every 3D output format.

**One picture, any screens, any GPUs.**
One mirrored desktop on two 3D televisions at once, frame packing at 30 Hz from an AMD integrated GPU and top and bottom at 60 Hz from an NVIDIA RTX 3060, both in 3D.
The program drew one full side-by-side picture; each output converted it for its own screen.
It takes both halves: our driver changes, which give amdgpu and NVIDIA's open kernel modules the HDMI 3D modes, and this one-format contract.

**Two places, two rules.**
Inside a program, anything goes: a player reads every packing a file can carry, an engine renders its eyes however it likes.
Inside Stereo KWin, only full side by side exists: the two eyes as separate pictures side by side, left eye first, at any resolution, declared once.
"Full" names that layout, not a size: half-width and half-height eyes stay as they are, so a half top-and-bottom frame of 1920x1080 arrives as one 3840x540 buffer.
No program resizes an eye; in a window or full screen, Stereo KWin does the one resize.
The output filters then turn that into whatever the screen needs: a 3D television's own HDMI 3D modes, anaglyph on any monitor, interleaved and frame-sequential displays, a headset through OpenXR.

**A window's 2D part and its 3D area are separate surfaces.**
The 2D part (menus, toolbars, panels, the document around a picture) is the window's own surface, at its normal size, one eye's size, and declares nothing.
The 3D area (a stereo video, a 3D viewport, a stereo painting canvas) is a surface of its own that hands Stereo KWin full side by side.
Stereo KWin shows the 2D part identical in both eyes and gives the 3D area each eye's view, in place inside the window.
Only a program that is stereo and full screen only, whose whole window is the 3D area, makes its whole window stereo.
The separation is also what gives the 2D part its depth: its elements declare their planes (sunk, screen, popped), and Stereo KWin draws those for each screen, while the 3D areas carry their own eyes.

**It is how sound already works on Linux.**
A program hands PipeWire PCM samples with their sample rate and channel layout.
PipeWire resamples, mixes and sends it to HDMI, Bluetooth or a USB DAC, and the program never learns which.
Nobody calls that a limitation: it is why every Linux program plays sound on every device.
Decoded picture samples, with their stereo layout and colour description, are the visual equivalent. Full side by side keeps both views associated with the same presentation frame; preserving HDR precision, luminance information and any gain map would let the compositor adapt that picture to each display.
The same principle serves stereo and HDR: **describe each content layer once, preserve its information through the stack, and convert for the screen at the output.**
A new kind of 3D screen needs one new output filter, and every stereo program already written works on it the day the filter lands.

**Why only one format.**
With several formats, the work is every input format times every output format times every program that wants stereo.
The formats and the displays are short lists; the programs are an open list, and that is the term that never ends.
Every earlier attempt put the format question on each program: quad-buffer needed a workstation card, NVIDIA's 3D Vision needed one vendor's driver, and every player grew its own menu of packings.
Each program had to know the display, and almost none did.
Here a program learns stereo once: it renders two eyes, declares them to Stereo KWin, and never needs to know what a television or a headset is.

**Why full side by side.**
- **Programs already produce it.** Games and VR engines render two viewports side by side, most 3D files carry side by side, and our Mesa packs quad-buffer OpenGL and two-layer Vulkan into it at swap.
- **It loses nothing.** Each eye keeps the resolution it came with, and nothing is stretched inside to be squeezed again at the screen; Stereo KWin resizes once, into the window or the screen, and half formats exist only in the output filters, where a display asks for them.
- **It survives the path.** One ordinary buffer passes through X11, Xwayland, screenshots, screencasts and remote desktop unchanged.
- **The eyes stay in sync.** Both views travel in one buffer and are committed together, keeping them associated with the same presentation frame. Each output, frame sequential included, can be built from that pair.

The converting costs copying rows and columns, work Stereo KWin does every frame anyway; every test runs in software rendering (llvmpipe) as well as on a GPU.
The design in one page: [STEREO3D.md](https://invent.kde.org/danielcamposramos/kwin/-/blob/stereo3d/STEREO3D.md).

## HDR: the same principle, an engineering choice still to test

Stereo layout and colour are independent properties: a picture can be mono or stereo, SDR or HDR. Full side by side specifies where the two views go; it does not select an HDR encoding, working colour space or precision. The [combined declaration](stereo-hdr-content.md) proposes keeping the colour description and any reconstruction data with each content layer, so an HDR picture can sit inside an SDR window and each output can adapt it separately.

**Engineering limit, clarified 19 October 2026:** Daniel has tested the stereo choice on devices, but has not yet performed equivalent cross-format HDR tests. PQ, HLG and gain-map images have different decoding and reconstruction requirements. The HDR interchange representation, working colour space, precision and metadata handling remain choices to evaluate; floating-point composition is a candidate, not a validated decision.

Reference images and measurements must cover HDR, deep-colour SDR and 8-bit outputs, mixed SDR/HDR content, mirrored screens and consistency between the two eyes. Deep colour alone is not HDR, and the existing stereo and deep-colour results do not establish that the proposed HDR path works.
