# GTK pieces still to build: GIMP's canvas (GTK 3), and what is left

Written on 2026-11-08 (ORDER 137, milestone 2) from the sources of GIMP 3.2.6, and cut on 2026-11-26 (milestone 4) to what is left.
The built parts are in [GTK 4 and GTK 3 and GtkGLArea](gtk-glarea.md): GTK 4's stereo area with its X11 route, its depth and colour state and Celluloid (milestones 1 to 3), and the same area in GTK 3 (milestone 4).

## GIMP 3.2: the canvas is cairo, not GL

- `grep` for `GtkGLArea`, `gtk_gl_area`, `GdkGLContext` and `epoxy` in GIMP 3.2.6's `app/` and `libgimp*` finds nothing; the build needs `gtk+-3.0 >= 3.24` only.
- The canvas: `GimpDisplayShell` connects `draw` handlers (gimpdisplayshell.c) and `gimp_display_shell_draw_image()` (app/display/gimpdisplayshell-draw.c) renders the image through GEGL into `shell->render_cache`, a cairo image surface in device pixels (chunked, `gimp_display_shell_render()`), and paints it with `cairo_set_source_surface()` and `cairo_paint()`. The tools and guides are `GimpCanvasItem`s drawn with cairo over it. The projection format, the colour management filter (`gimpdisplayshell-profile.c`, `-filter.c`) and the display transform all end in that 8 bit cairo surface.
- The stereo content of GIMP is a document with depth, not a rendered scene. Two ways, which differ for the person and so both are options (memory every-path-a-user-option): (1) the depth layers design (picture plus depth assembled into full side by side by libstereo-dibr, memory depth-content-options-shared-library), shown as an area of the canvas; (2) the image drawn twice with its layers shifted by their own depth, as the desktop does for its UI (memory stereo-plasma-depth-rules: "faked 3D becomes stereo by doubling, not by cameras"). The design of the depth layers is queue row 148.
- Where it goes in GIMP: `gimp_display_shell_draw_image()` draws the render cache once; for stereo it draws it into a picture twice as wide (the render cache and the paint of each chunk once per eye, with the shift of each layer applied in `gimp_display_shell_render()` through the GEGL pipeline), and that picture becomes the picture of a stereo area.

### What milestone 4 built that GIMP's canvas takes

- **A surface of its own under a GTK 3 window, with a hole over it**, on Wayland and X11 (gtk/gtkglareastereo.c in the edition's gtk+3.0): the subsurface below the window or the declared X11 child, its declaration, and the window's opaque region with the hole. GIMP's tools, guides and selection outlines (`GimpCanvasItem`s) stay in the window, drawn over the hole: the case `--overlay` proves exactly that for a label.
- **The pair as a dma-buf in the canvas's depth** (XB30, XB48 where the driver exports one, XB4H) and **its colour state described** with `wp_color_management_v1` (ITU-T H.273 code points, `GdkColorState`). GIMP's display transform knows the image's profile; the canvas would hand the compositor the image's own primaries and transfer function instead of converting to 8 bit sRGB in the render cache.
- **The views' own size** (`stereo-view-width`): the canvas can render each eye at the zoom's resolution and let the compositor resize once.

### What the canvas still needs, each with where it goes

- **A GL picture to hand over.** The stereo area takes OpenGL views; GIMP renders with GEGL into cairo image surfaces in memory. Either the canvas becomes a GtkGLArea that uploads the two render caches as textures (the area then needs no change), or the area learns a memory route: `wl_shm` takes `ABGR16161616` and `ABGR16161616F` too, which would also give a software renderer its stereo area (the case where it says "cannot export its picture as a dma-buf" today). That choice is the canvas milestone's first measurement.
- **A deep render cache.** `render_cache` is `CAIRO_FORMAT_ARGB32`/`RGB24`; cairo 1.17.2 and later has `CAIRO_FORMAT_RGBA128F` and `RGB96F`, and GEGL renders in float already.
- **A deep picture without stereo.** GTK 3 draws a plain area into its 8 bit sRGB window (and logs that its format and colour state reach the compositor only in stereo): the same surface without the stereo declaration would carry a deep 2D canvas. It is the same code with one view and no declaration.

## What earlier milestones left, still open

- **A 16 bit integer stereo area on a driver that exports no 16 bit dma-buf** (NVIDIA's EGL and zink on NVIDIA, in GTK 4 and GTK 3 alike: the area says "cannot export its picture as a dma-buf"). The memory route above is the way that keeps every bit.
- **Luminances and mastering data.** A colour state carries primaries, transfer function, matrix and range, nothing else, in GDK 4 and in GDK 3's, so a PQ picture reaches KWin without its peak and KWin makes room for 10000 cd/m²: the reference white is shown at about half (measured in GTK 4: 110 cd/m² on a 1000 cd/m² output). It needs an API for the protocol's `set_luminances` and the mastering display and content light levels.
- **Hybrid log-gamma on a stereo area.** KWin lists no HLG transfer function, so the pair cannot be described: owed by KWin. GDK 4 converts it itself for a plain area; GDK 3 converts nothing, so its left view alone shows the values as written and the area says why.
- **A colour state on X11.** An X window has no description; a stereo area with a state other than sRGB, or deeper than the window's visual, says so (GTK 4 and GTK 3).
- **A 2D widget over an X11 stereo area in GTK 4** (`glarea-stereo-test --stereo --overlay` on X11: the label is hidden). GTK 3 shows it when the window has an alpha channel, by placing the child below the window without a frame and keeping a hole; GDK 4 needs the same, as a `GdkSubsurface` over the child window so that GSK cuts the hole in the toplevel.
- **GTK 3's X11 window on zink** shows only its GL area under Xwayland (Debian's GTK 3 too): GTK 3's own fault, recorded with the lane's failures; the edition's NVIDIA sessions run GLX programs on zink, so a GTK 3 program with a GL area on X11 is affected there.
