# Why one format: full side by side, at any resolution

**For anyone who wants to know why 3D works on every screen here, and for program and driver developers:** the one picture every program hands the desktop, both eyes side by side at full size, and why.

**The standard in three lines.**
- **Stereo KWin** (KDE Plasma's compositor, with our stereo changes) speaks full side by side, at any resolution.
- **Programs** decode or generate stereo in any standard, and deliver full side by side, at any resolution, to Stereo KWin.
- **Outputs** (Stereo KWin's filters at the end, one per kind of screen) convert from that to whatever each screen needs.

That is what makes stereo work across GPUs, across monitors (2D ones included) and across every 3D output format.

**One picture, any screens, any GPUs.** One mirrored desktop on two 3D televisions at once, frame packing at 30 Hz from an AMD integrated GPU and top and bottom at 60 Hz from an NVIDIA RTX 3060, both in 3D. The program drew one full side-by-side picture; each output converted it for its own screen. It takes both halves: our driver changes, which give amdgpu and NVIDIA's open kernel modules the HDMI 3D modes, and this one-format contract.

**Two places, two rules.**
Inside a program, anything goes: a player reads every packing a file can carry, an engine renders its eyes however it likes.
Inside Stereo KWin, only full side by side exists: both eyes at full size, left eye first, at any resolution, declared once.
The output filters then turn that into whatever the screen needs: a 3D television's own HDMI 3D modes, anaglyph on any monitor, interleaved and frame-sequential displays, a headset through OpenXR.

**A window's 2D part and its 3D area are separate surfaces.**
The 2D part (menus, toolbars, panels, the document around a picture) is the window's own surface, at its normal size, one eye's size, and declares nothing.
The 3D area (a stereo video, a 3D viewport, a stereo painting canvas) is a surface of its own that hands Stereo KWin full side by side.
Stereo KWin shows the 2D part identical in both eyes and gives the 3D area each eye's view, in place inside the window.
Only a program that is stereo and full screen only, whose whole window is the 3D area, makes its whole window stereo.
The separation is also what gives the 2D part its depth: its elements declare their planes (sunk, screen, popped), and Stereo KWin draws those for each screen, while the 3D areas carry their own eyes.

**It is how sound already works on Linux.**
A program hands PipeWire plain PCM, at whatever rate it likes.
PipeWire resamples, mixes and sends it to HDMI, Bluetooth or a USB DAC, and the program never learns which.
Nobody calls that a limitation: it is why every Linux program plays sound on every device.
Full side by side is the stereo picture's PCM, and Stereo KWin is its PipeWire.
A new kind of 3D screen needs one new output filter, and every stereo program already written works on it the day the filter lands.

**Why only one format.**
With several formats, the work is every input format times every output format times every program that wants stereo.
The formats and the displays are short lists; the programs are an open list, and that is the term that never ends.
Every earlier attempt put the format question on each program: quad-buffer needed a workstation card, NVIDIA's 3D Vision needed one vendor's driver, and every player grew its own menu of packings.
Each program had to know the display, and almost none did.
Here a program learns stereo once: it renders two eyes, declares them to Stereo KWin, and never needs to know what a television or a headset is.

**Why full side by side.**
- **Programs already produce it.** Games and VR engines render two viewports side by side, most 3D files carry side by side, and our Mesa packs quad-buffer OpenGL and two-layer Vulkan into it at swap.
- **It loses nothing.** Each eye keeps its full resolution; half formats exist only in the output filters, where a display asks for them.
- **It survives the path.** One ordinary buffer passes through X11, Xwayland, screenshots, screencasts and remote desktop unchanged.
- **The eyes stay in sync.** Both eyes travel in one buffer, committed once, so they always show the same instant; that is what lets every output, frame sequential included, be built from the same frame.

The converting costs copying rows and columns, work Stereo KWin does every frame anyway; every test runs in software rendering (llvmpipe) as well as on a GPU.
The design in one page: [STEREO3D.md](https://invent.kde.org/danielcamposramos/kwin/-/blob/stereo3d/STEREO3D.md).
