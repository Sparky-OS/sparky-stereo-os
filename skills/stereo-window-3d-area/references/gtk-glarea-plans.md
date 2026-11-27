# GTK pieces still to build: what is left (GIMP's canvas per eye, depth layers and deep canvas built)

Written on 2026-11-08 (ORDER 137, milestone 2) from the sources of GIMP 3.2.6, cut on 2026-11-26 (milestone 4) to what is left, and rewritten the same day after GIMP's milestones 1 (the canvas per eye, GIMP 3.2.8), 2 (depth layers) and 3 (the deep and HDR canvas).
The built parts are in [GTK 4 and GTK 3 and GtkGLArea](gtk-glarea.md); GIMP's canvas per eye, its route, proof and traps are in [an editor's canvas per eye](../../stereo-pictures/references/an-editors-canvas-per-eye.md).

## GIMP, milestone 1 (built): the canvas per eye

Each eye is rendered by GIMP's own render code into a render cache of its own, from that eye's sources (an eye layer, or the eye's view of a packed picture in both halves), and the two pictures go up as textures into one stereo GtkGLArea that lies under the canvas items (GimpCanvas's underlay). The eye's sources are a list (`GimpDisplayShellEyeSource`: a buffer in image coordinates, its abyss, the part of the image it fills), which is where the depth layers plug in.

**Upstream to watch:** GIMP's master merged its own MPO loader on 2026-06-13 (merge request 2852, "plug-ins: Add initial MPO loading support"); GIMP 3.2.8 has none. When the edition moves to GIMP 3.4, read how that loader opens a pair (one image, layers and their names) against the canvas's model (top-level "Left eye" and "Right eye" layers) and the stereo pictures plug-in's own MPO procedure, which then both claim the type.

## GIMP, milestone 2 (built): the depth layers (queue row 148)

Built in gimp 3.2.8-1+stereo3d2 on stereo-layer 1.24.0 (2026-11-26); the person's view, the route, the proof and the traps are in [an editor's canvas per eye, Depth layers](../../stereo-pictures/references/an-editors-canvas-per-eye.md#depth-layers-milestone-2-queue-row-148).
Daniel's design (2026-10-15): a layer type that groups other layers at one depth the artist sets, three decimals; one key held with the tool's normal movement pops, another sinks; no nesting that adds up; the model in a library GIMP and Krita share; a tool has no limits; each eye sees the layer moved by half the value (doubling, never cameras); modes 1 and 2 stay.

What was built, against the plan of milestone 1:
1. **The model:** libstereo-policy `stereo-depth.h` (`stereo_depth_parse`, `stereo_depth_format`, `stereo_depth_round`, `stereo_depth_eye_shift`, `stereo_depth_shift_is_whole`, `stereo_depth_shift_rgba`), with `autotests/depthlayertest.c`. The fractional move is a Lanczos window of three lobes on premultiplied samples (the edition's choice, said as such).
2. **The layer type:** `GimpDepthLayer` (a `GimpGroupLayer` with a `depth` property and its own undo); its value is also its persistent parasite `gimp-depth-layer`. Layer > New Depth Layer (the selected layers go into it), the Layers dock's Depth row, the PDB group `depth_layer` (`gimp-depth-layer-new`, `-get-depth`, `-set-depth`, `-new-from-eye`; core only).
3. **Each eye's picture:** not a second state of the image's graph, which composites each layer over the layers below and reads a normal group from its projection, but a chain of its own per eye (`GimpEyeProjectable`): copies of the mode nodes over the eye's own picture, the layers' content and masks fanned out of the image's graph and moved by `gimp:depth-shift`, which calls the library. The display's third kind of image takes each eye's projection as its one source.
4. **XCF:** the parasite is saved with the group by XCF as it is; `xcf-load.c` turns a group carrying it into a depth layer (`gimp_depth_layer_xcf_load_hack`, the text layer's precedent). The plug-in exports MPO, JPS and PNS from each eye's picture.
5. **The keys:** 8 pops, 7 sinks (actions `layers-depth-pop` and `layers-depth-sink`, rebindable); held over the canvas, the pointer's movement moves the depth (0.1 px a pixel) and the tool does not see it. On an AZERTY keyboard the digits need Shift; whether GTK 3 still matches the accelerator then is not measured (a person can bind other keys). Krita's tool factories' own shortcuts are still to be read for Krita's part.
6. **The decision no design covered,** taken by the lane and said so: an image with eye layers and depth layers shows each eye its own eye layer under the depth layers; a packed picture in an editing mode keeps its depth layers at the screen and tells.

**Krita's part (later, in the edition's fork):** the same model through the stereo layer's Qt side, a depth layer as a `KisGroupLayer` subclass with the same parasite-like property in .kra, each eye's projection built like GIMP's, the two keys as Krita input actions (the V of the ruler is the model) bound in `kritadefault.profile`.

## GIMP, milestone 3 (built): the deep and HDR canvas

Built in gimp 3.2.8-1+stereo3d3 on gtk+3.0 3.24.52-3+stereo3d2 (2026-11-26); the person's view, the route, the proof and the traps are in [an editor's deep and HDR canvas](../../deep-colour/references/an-editors-deep-canvas.md), GTK's part in [GTK 3](gtk-glarea.md#gtk-3).
Daniel's design (2026-10-15 ~23:10): "gimp ramp up on the working canvas is included, deep sdr/hdr color + hdr - passing to the compositor just like 3D information ... our job is make sure to code it to the specs - inside our contract only!"

What was built, against the plan's six items:
1. **The deep render cache:** each eye's (and a 2D deep image's) render cache and picture in `CAIRO_FORMAT_RGBA128F`, rendered through GEGL in floats; the textures `GL_RGBA32F` with `GL_FLOAT`. Cairo clamps floats above 1.0, so the image's samples are copied and composited by GIMP itself wherever the view is unrotated.
2. **The area's depth and colour state** by the image's precision and profile: ITU-T H.273 code points from the profile's `cicp` tag, 1/13 and 1/8 for GIMP's own sRGB and linear sRGB, otherwise linear Rec. 2020 (9/8), to which GIMP's display transform converts after soft-proofing and the display filters.
3. **A deep picture without stereo:** GTK 3's plain area with a deeper format, another colour state or luminances goes on a surface of its own with nothing declared (`surface-shown`, `surface-error`); GIMP uses it for every image deeper than 8 bits, with code points or wider than sRGB.
4. **What GTK owed:** the memory way (`wl_shm` XBGR16161616, XBGR2101010, XBGR16161616F, XBGR8888 or XRGB8888) where no dma-buf carries the picture (so a 16 bit stereo area on NVIDIA's EGL or zink on NVIDIA, and any area on a software renderer, reaches the compositor, at one copy a frame), and `gtk_gl_area_set_luminances()`, `gtk_gl_area_set_mastering_display()`, `gtk_gl_area_set_content_light_levels()`.
5. **Upstream:** GIMP's merge request !2755 has not landed in GIMP's master (its GitHub mirror at 42f75a1f, 2026-11-26, has no Wayland colour-management commit; GNOME's GitLab answers non-browser clients with 406 and has no Wayback capture). GTK's main (42cf1237, gdk/wayland's colour code) lists the compositor's `set_luminances` feature but sends only a transfer function and primaries (named or by chromaticities) for a surface: no luminances, no mastering data, and no API for them. Nothing goes to GIMP (its README refuses AI-generated contents).
6. **The proof:** the ramp counted where rendered and in each eye's buffer at a virtual HDR output for 8, 10, 12, 16 bit, half float and float images, what KWin received, and the red rows (see the deep canvas page).

Beside the plan: the old path stays a choice ("every path a user option"), Preferences > Color Management, "Show deep images in their own depth and colors", on by default; off gives GIMP's own 8 bit canvas converted to its monitor profile, as before.

## What is left, still open

- **A half float picture through memory.** KWin 6.7.4 lists no `wl_shm` half float format (`src/wayland/shmclientbuffer.cpp`, `s_formats`: 2101010 and 16161616 integer only), so a half float or float picture on a software renderer has no way: the area says so (`GDK_GL_ERROR_UNSUPPORTED_FORMAT`) and GIMP steps down to 16 bit integer. KWin's to add (the format in `s_formats` and its upload as a half float texture).
- **Hybrid log-gamma.** KWin lists no HLG transfer function, so an HLG picture cannot be described, stereo or not: owed by KWin. GIMP steps down to 8 bit sRGB (a stereo image) or its 8 bit canvas (2D) and says so.
- **Mastering data from files.** GIMP 3.2's loaders keep no mastering display or content light levels (HEIF's `mdcv` and `clli`, PNG's mDCV and cLLI), so a PQ canvas is described with PQ's defaults and KWin, making room for 10000 cd/m², shows its reference white at about half on a 1000 cd/m² output. GTK 3 has the API now; GIMP needs the metadata in its image model first.
- **A float picture reaches the compositor as half float.** GIMP renders a float image's views in 32 bit floats (256 values in the ramp's band), and the area hands them over as XBGR16161616F: DRM's format list (drm_fourcc.h) has no 32 bit float RGBA format, so no buffer can carry more; the same as GTK 3's stereo area since milestone 4.
- **GTK 4's luminance API.** The same three functions for GTK 4's `GtkGLArea` and textures (GDK 4 has none either).
- **A rotated or unevenly scaled deep view** goes through cairo, which clips values above 1.0.
- **Translucent pixels in a linear state** are blended over the checkerboard in linear light, the 2D canvas in its monitor's encoding: the same opaque picture, a slightly different translucent one.
- **GIMP's monitor profile and the compositor's.** An 8 bit sRGB canvas (2D, or a stereo image's 8 bit area) is still converted to GIMP's monitor profile, which on Wayland is GIMP's configured one (sRGB by default); a person who sets a display profile in GIMP and has the compositor manage the screen too gets two conversions. The other half of the same protocol is GIMP's !2755.
- **A colour state on X11.** An X window has no description; a stereo area with a state other than sRGB, or deeper than the window's visual, says so (GTK 4 and GTK 3), and GIMP takes the 8 bit sRGB step.

- **A 2D widget over an X11 stereo area in GTK 4** (`glarea-stereo-test --stereo --overlay` on X11: the label is hidden). GTK 3 shows it when the window has an alpha channel, by placing the child below the window without a frame and keeping a hole; GDK 4 needs the same, as a `GdkSubsurface` over the child window so that GSK cuts the hole in the toplevel.
- **GTK 3's X11 window on zink** shows only its GL area under Xwayland (Debian's GTK 3 too): GTK 3's own fault, recorded with the lane's failures; the edition's NVIDIA sessions run GLX programs on zink, so a GTK 3 program with a GL area on X11 is affected there.
