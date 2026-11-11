---
metadata:
  requires-packages: qt6-base-dev
name: stereo-window-3d-area
description: >-
  Stereo content in an ordinary Qt, KDE or GTK 4 window, and depth of the desktop's own elements: a declared
  subsurface under a hole in the window, Stereo Union's depth values, the levels sunk, screen and popped within the person's
  limits, menus, popups, tooltips, select lists, notifications and dialogs at depth (xdg_popup), the 10 px popup
  border, KWin's effects with their own depth (Fall Apart, Sheet, Glide, Zoom, drag), and the boot splash at the
  person's limits (popped= and sunk= on the kernel line, a Plymouth guest). Load it when a popup menu at the screen
  edge looks cut or flat in 3D, a sub-menu sits behind its parent, a tooltip or select list is not popped, a dialog
  collapses to its title bar, a hidden top level kills the native child, a whole window is declared instead of its 3D
  area, two windows draw each other's depth, an element's parallax must stay in its rectangle, or the boot splash
  ignores a lowered popped limit.
---

# A 3D area inside an ordinary window

## Working recipe

1. Classify the task: stereo media/scene surface, whole-window depth, or control-level depth (built for Stereo Union-styled Qt Quick and Qt Widgets windows on Wayland). Choose the appropriate pattern below.
2. Trace content, declaration, compositing, clipping and logical input separately; test resize, overlap, close/reopen and mode changes.
3. Return both-eye captures, declaration count, geometry and 2D baseline. Shared styling does not imply shared rendering or an implemented stereo consumer.

**Check freshness first.**
Written on 2026-10-07 from the forks linked below; KWin's effects with depth of their own added on 2026-11-02.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; this one assumes its contract.

## The shape

This section describes a stereo content area with depth-neutral surrounding UI.
For whole-window depth and control-level depth, read [Qt, KDE and depth](references/qt-kde-depth.md) and [Depth inside every window](../../docs/depth-inside-windows.md).
Run eye-equality checks below with desktop plane depth disabled; when enabled, validate the intended transform and logical input instead of identical screen coordinates.

A program window has two parts that must not be mixed:

- **the 2D part:** menus, toolbars, panels, the on-screen display, the document around a picture. It stays the window's own surface, at its normal size (one eye's size), declares nothing, and Stereo KWin shows it identical in both eyes;
- **the 3D area:** a video, a 3D viewport, a canvas. It is a **surface of its own**, handed to Stereo KWin as full side by side (the two eyes side by side, left eye first, each at its own resolution), declared once.

Stereo KWin composes the two in place: the 3D area gets each eye's view inside the window, the 2D part sits over it at screen depth.

## The pattern that works on Wayland

1. **A subsurface below the window.** Create a `wl_subsurface` for the 3D area, placed *below* the window's own surface, positioned and sized with `wp_viewporter` to the area's rectangle in the window. Put both eyes side by side into it, each at its own resolution (a video's views as the stream carries them, a picture's as the file has them, a scene's at its render resolution), and declare it once as full side by side (`kde-stereo-content-v1` from our [plasma-wayland-protocols](https://invent.kde.org/danielcamposramos/plasma-wayland-protocols/-/tree/stereo3d-6.7), through the shared declaration library `libstereo-declare` in the edition).
2. **A hole in the window.** The window surface must be transparent exactly over the 3D area, so the subsurface shows through. In Qt Widgets: make the top level translucent and paint its background yourself everywhere *except* the 3D area's rectangle, because Qt skips `autoFillBackground` and `PE_Widget` on translucent windows. A small event filter on the top level does it.
3. **Follow the rectangle.** Move and resize the subsurface when the area moves (Kdenlive uses a 100 ms timer), and only while the area is visible and not covered: a document in another tab must not leave its layer on screen.
4. **2D on top stays 2D.** Overlays drawn over the 3D area (a popup palette, a compass, subtitles) are drawn by the window, once, so they come out identical in both eyes.
5. **A popup is an xdg_popup, never a subsurface.** Menus, tooltips, select lists and dialogs get their depth from KWin as popup surfaces of their own; a popup made as a subsurface stays at its parent window's level (the browser's case: [lessons-2026-11.md](references/lessons-2026-11.md)).

Worked examples:
- **Kdenlive's monitor**, the first one: [danielcamposramos/kdenlive `stereo3d-26.08`](https://invent.kde.org/danielcamposramos/kdenlive/-/tree/stereo3d-26.08).
- **Marble's globe**, a `StereoLayer` class any `QWidget` program can copy: [1df996420832](https://invent.kde.org/danielcamposramos/marble/-/commit/1df996420832) on [`stereo3d`](https://invent.kde.org/danielcamposramos/marble/-/tree/stereo3d).
- **Krita's canvas**, a child `QWindow` sharing textures with the canvas, also used to keep 16-bit documents deep in a stereo session: [`sparky/stereo-canvas-wayland`](https://invent.kde.org/danielcamposramos/krita/-/tree/sparky/stereo-canvas-wayland).
- **Video through MpvQt**, shared by Haruna and PlasmaTube, at 10 bits or half float: [danielcamposramos/mpvqt `stereo3d`](https://invent.kde.org/danielcamposramos/mpvqt/-/tree/stereo3d), used by [Haruna `stereo3d`](https://invent.kde.org/danielcamposramos/haruna/-/tree/stereo3d).
- **Video through Qt Multimedia** (Dragon Player, Plank Player): in the edition's Qt Multimedia the video output takes every packing apart itself and draws the video in a declared layer below the window, so a Qt Quick player keeps only its QML and its 3D menu. The public branch carries the `StereoMode` type so far ([Sparky-OS/qtmultimedia `stereo3d-6.11`](https://github.com/Sparky-OS/qtmultimedia/tree/stereo3d-6.11)); the rest follows.
- **A hole in a Qt Quick window:** an opaque flat-colour node that writes (0,0,0,0) over the area, with an alpha buffer asked for when the window is created; no colour or background of the program changes.
- **The declaration library's state is per thread:** declare on the thread that initialised it, and let the thread that presents the frames own the layer.
- **A build option must not change a class layout** that other translation units see: keep the new members always, and hold an optional type through a `shared_ptr` to an incomplete type.

## Which Qt routes work, measured

- A stereo `QWindow` inside `QWidget::createWindowContainer` works on Wayland with our Qt and Mesa.
- A native stereo `QOpenGLWidget` (`WA_NativeWindow`) does **not**: it comes out with `stereo=false`.
- On X11 (xcb), a plain stereo `QOpenGLWidget` in a 2D window works with our Qt, Mesa, Xwayland and KWin: Qt gives it a native child window, Mesa lists it, and KWin shows it per eye with the rest of the window the same in both eyes (measured on the GPU and in software). The window is flushed with a stereo context, because GLX gives a window the configuration of the context made current on it.
- A plain `QOpenGLWidget` program with the stereo default format does come out stereo on Wayland today (Kubrick, KAlgebra, Kalzium, measured): but the whole top-level window is declared, menus included. A fix in Qt is being written so that a stereo `QOpenGLWidget` inside a 2D window becomes its own stereo surface, with no change in the program.
- **Size a stereo top level before its window is created** (`adjustSize()` or a resize when a dialog is built): otherwise its first frame is committed at Qt's default 100x30 and the compositor keeps that size, so the dialog collapses to its title bar (Kalzium's molecule editor; the engine fix is queued).
- **Never empty or hide the top level of a native 3D area on Wayland.** Qt 5's Wayland platform destroys a hidden window's `wl_surface` and does not make the native children's subsurfaces again when the window gets a new one: Qt keeps moving the orphaned `wl_subsurface`, and KWin ends the connection with "wl_subsurface: error 0: no parent". Qt hides a native window that a resize makes empty. VLC Stereo died at the start of every video in its minimal view because the interface restored an invalid -1x-1 size for the video widget it showed for the first time, and in minimal view that is the whole window. Guard every path that resizes the top level to nothing, hides it or recreates it while the 3D area's native child lives, and test the program's view modes (minimal view, full screen, always on top, a second file) with `WAYLAND_DEBUG=client` and the window's surfaces in view.
- **A GL widget in a dialog turns the parent stereo:** Qt recreates the dialog's parent top level as a GL window when a `QOpenGLWidget` appears, and under the stereo default format the parent is declared too.
- Setting a stereo *default* surface format makes the whole top level stereo, against the separation rule: set the format on the 3D area's own window only.
- Qt's client-side decorations once flattened stereo windows; our Qt gives the decorations' content framebuffer a slot per eye ([Sparky-OS/qtbase `stereo3d-csd`](https://github.com/Sparky-OS/qtbase/tree/stereo3d-csd)), or KWin decorates the stereo window with server-side decorations.
- Qt Widgets forced an 8-bit alpha on every translucent window, so a 2D part over a deeper 3D area was 8 bits; our Qt keeps the alpha and depth the window asks for (10/10/10/2 or 16/16/16/16), and a window that asks for nothing stays 8/8/8/8 ([Sparky-OS/qtbase `stereo3d-alpha`](https://github.com/Sparky-OS/qtbase/tree/stereo3d-alpha)). Deep content in its own layer, as Krita does, is still the pattern ([`deep-colour`](../deep-colour/SKILL.md)).

## GTK 4 (GtkGLArea, Wayland)

GtkGLArea draws into a framebuffer of its own and appends one texture to the scene graph, so a stereo GtkGLArea is the same pattern with GTK's own subsurface: each eye is rendered by the program's unchanged render handler (the signal is emitted once per eye, `gtk_gl_area_get_current_eye()` says which), the two views are copied side by side into one opaque texture, and that texture goes on a `GdkSubsurface` (the path `GtkGraphicsOffload` takes) declared with `kde_stereo_content_v1` version 2, so the area keeps its size.
GTK composites an offloaded picture itself whenever the subsurface cannot be used; for a stereo area that would show both eyes flat, so the area draws a clip of the left view as its fallback and tells the program (`stereo-shown`, `stereo-error`) and the log, once.
The recipe, the proof cases and the traps (no dma-buf from llvmpipe, a blit that obeys the scissor, the decision that comes a frame late, a dma-buf export that writes no descriptor with zink on NVIDIA) are in [GTK 4 and GtkGLArea](references/gtk-glarea.md).
X11 is the same area as a child window declared with libstereo-declare (milestone 2). GIMP 3.2's canvas is cairo, not GL; a GL player (Celluloid) and deep colour are plans in [GTK pieces still to build](references/gtk-glarea-plans.md).

## X11 programs

Under Xwayland, a 3D area is a child X window.
The window lists the child in `_KDE_NET_WM_STEREO_CONTENT_CHILDREN` (WINDOW/32) and the child declares itself with its own `_KDE_NET_WM_STEREO_CONTENT`; Mesa's GLX does both for a stereo GLX child (Togl in Netgen, FLTK's GL window in gmsh, ParaView's render view), and keeps the child listed while the window lives.
KWin, announcing version 5 of `_KDE_NET_WM_STEREO_CONTENT_SUPPORTED`, redirects each listed child; our Xwayland gives it a surface of its own, and KWin shows that surface one view per eye at the child's place, the rest of the window the same in both eyes.
The child keeps its own size and its buffer is twice as wide, one eye at the child's size on each side (declaration version 4); input still goes to the window, and the X server finds the child.
A program that declares its own child window, with no GLX, writes the same two properties.
In our Qt on xcb, a stereo `QOpenGLWidget` gets a native child window of its own and is shown the same way, with no change in the program.
A window that shows a splash screen first could lose its one-eye size afterwards; our KWin sends it a synthetic ConfigureNotify, so it gets the size back (found on Krita).
Native Wayland is the route to prefer when the toolkit has it.

## KWin's effects with depth of their own

Daniel's design calls of 2026-10-11, for the effects KWin draws over windows.
How a theme designer meets them is on [For theme designers](../../docs/for-theme-designers.md#effects-with-their-own-depth-designed-coming).

- **Effects get depth options of their own,** beyond the desktop's gentle limits, kept in the one place where the desktop's depth settings live and editable by users and developers: "One place, one rule, but for everyone".
  His reason: "without this freedom the creativity will be stuck".
  A headset output allows more still.
- **A window's depth is never behind anything it covers.** The depth solver keeps this in stacking, focus, dragging, dropping, dialogs and effects: the highest overlapped level wins, with hysteresis at overlap edges, and every change of level is eased (one easing for the pointer and the windows: fast up, gentle down, at Plasma's animation speed).
- **An effect describes its motion once, in three dimensions,** on the shared per-eye layer; the renderer's two cameras make each eye, so no effect knows which eye is drawn.
  Large depths honour KDE's animation speed and the reduced-motion setting, and a 2D output stays pixel-identical to today's.
- **The calls:**
  - Fall Apart: "Fly" brings the pieces toward the viewer; "Dive" drops them to the sunk limit, where they hit a floor and bounce while they fade.
    Built first, on the edition's KWin branch ([b0af6ca](https://github.com/Sparky-OS/kwin/commit/b0af6ca82f46)).
  - A closing background window first moves the other way, as an anticipation (Dive: pop, then sink; Fly: sink, then pop).
  - Dive's floor belongs to the theme: its size and depth are set in the theme editor, and effects read the theme's depth geometry.
  - Sheet: the dialog starts from its parent's plane at the popped value; a dialog over a dialog is the limit, and a third stays bound to the second.
  - Glide: sunk to the screen on opening, the reverse on closing.
  - Zoom: a magnifier mode whose area comes toward the viewer; plain zoom keeps a constant parallax.
  - Dragging: one step up by default, with an option from flat to popped, and only ever up.
    Over a popped window the dragged window rises to its level and comes back down after leaving it; dropped there, it keeps that plane.
  - Flip Switch made stereo.
  - A shaded window's title bar reads as a cylinder: its own plane at the edges, popped 1 or 2 px at the crest, an option on the depth settings page (0, 1 or 2 px).
- **Study KWin's removed effects before designing a new one** (Snap Helper, Resize, the C++ Flip Switch, the old Cube): "the solution might be there and being ditched".
  Resize's scaled drawing while resizing serves XR, the old Cube's cylinder and sphere mappings serve the 3D cube and a VR home, and Present Windows' layouts a headset overview, credited to Kompose.

## Proof for this kind of work

As in the general skill, plus:
- **0 differing pixels between the eyes outside the 3D area** (the menus, the toolbars, the window background);
- **exactly one declaration**, on the 3D area's surface, and none on the top level;
- **no squeeze:** with stereo off the window has its normal size, and with stereo on the 3D area holds both eyes, neither squeezed nor stretched;
- **overlays:** an overlay over the 3D area changes the same pixels in both eyes and none in one eye only;
- **the 2D control:** stereo off against the distribution's build, 0 differing pixels.

## A declared layer's state follows its declaration

Never commit a buffer of two views to a surface the compositor has not taken as stereo content, and never report a layer active before its declaration was taken: a refused declaration is logged once, shown by a property the player reads, and the video is drawn the ordinary way.
[The rule, the recipe to force and capture a refusal, and the traps](references/declared-layer-state.md) (ORDER 448, after ORDER 49's packed frame in both eyes).

## The boot splash at the person's depth

The splash takes the main screen's limits, never numbers of its own: sparky-stereo-boot puts `popped=` and `sunk=` on each stereo output of `plymouth.stereo=` (the person's `kwinrc` `[StereoDepth]` limits times the display's factor, as KWin resolves them), Plymouth hands them to the theme (`Window.GetStereoPoppedLimit ()`, `Window.GetStereoSunkLimit ()`), the theme places its levels inside them, and what the person did not save is the display's default, said.
[The chain, the guest rig that proves it (`scripts/plymouth-rig/`), the predicted and measured parallax, and the traps](references/boot-splash-depth.md) (ORDER 481).

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (13 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
