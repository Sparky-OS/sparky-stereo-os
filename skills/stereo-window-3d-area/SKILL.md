---
name: stereo-window-3d-area
description: How to give an ordinary desktop program a stereo 3D area (a video, a 3D viewport, a painting canvas) inside its normal window on Sparky Stereo OS, with the menus and toolbars staying 2D. Patterns solved in Kdenlive, Marble, Krita, Haruna and PlasmaTube, with links to their code. Load the general sparky-stereo skill first.
---

# A 3D area inside an ordinary window

**Check freshness first.** Written on 2026-10-07 from the forks linked below. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; this one assumes its contract.

## The shape

A program window has two parts that must not be mixed:

- **the 2D part:** menus, toolbars, panels, the on-screen display, the document around a picture. It stays the window's own surface, at its normal size (one eye's size), declares nothing, and Stereo KWin shows it identical in both eyes;
- **the 3D area:** a video, a 3D viewport, a canvas. It is a **surface of its own**, handed to Stereo KWin as full side by side (both eyes at full size, left first), declared once.

Stereo KWin composes the two in place: the 3D area gets each eye's view inside the window, the 2D part sits over it at screen depth.

## The pattern that works on Wayland

1. **A subsurface below the window.** Create a `wl_subsurface` for the 3D area, placed *below* the window's own surface, positioned and sized with `wp_viewporter` to the area's rectangle in the window. Render both eyes side by side into it and declare it once as full side by side (`kde-stereo-content-v1` from our [plasma-wayland-protocols](https://invent.kde.org/danielcamposramos/plasma-wayland-protocols/-/tree/stereo3d-6.7), through the shared declaration library `libstereo-declare` in the edition).
2. **A hole in the window.** The window surface must be transparent exactly over the 3D area, so the subsurface shows through. In Qt Widgets: make the top level translucent and paint its background yourself everywhere *except* the 3D area's rectangle, because Qt skips `autoFillBackground` and `PE_Widget` on translucent windows. A small event filter on the top level does it.
3. **Follow the rectangle.** Move and resize the subsurface when the area moves (Kdenlive uses a 100 ms timer), and only while the area is visible and not covered: a document in another tab must not leave its layer on screen.
4. **2D on top stays 2D.** Overlays drawn over the 3D area (a popup palette, a compass, subtitles) are drawn by the window, once, so they come out identical in both eyes.

Worked examples:
- **Kdenlive's monitor**, the first one: [danielcamposramos/kdenlive `stereo3d-26.08`](https://invent.kde.org/danielcamposramos/kdenlive/-/tree/stereo3d-26.08).
- **Marble's globe**, a `StereoLayer` class any `QWidget` program can copy: [1df996420832](https://invent.kde.org/danielcamposramos/marble/-/commit/1df996420832) on [`stereo3d`](https://invent.kde.org/danielcamposramos/marble/-/tree/stereo3d).
- **Krita's canvas**, a child `QWindow` sharing textures with the canvas, also used to keep 16-bit documents deep in a stereo session: [`sparky/stereo-canvas-wayland`](https://invent.kde.org/danielcamposramos/krita/-/tree/sparky/stereo-canvas-wayland).
- **Video through MpvQt**, shared by Haruna and PlasmaTube, at 10 bits or half float: [danielcamposramos/mpvqt `stereo3d`](https://invent.kde.org/danielcamposramos/mpvqt/-/tree/stereo3d), used by [Haruna `stereo3d`](https://invent.kde.org/danielcamposramos/haruna/-/tree/stereo3d).
- **Video through Qt Multimedia** (Dragon Player, Plank Player): moving into Qt Multimedia's video output in October 2026, so a Qt Quick player needs no code of its own for declared video.

## Which Qt routes work, measured

- A stereo `QWindow` inside `QWidget::createWindowContainer` works on Wayland with our Qt and Mesa.
- A native stereo `QOpenGLWidget` (`WA_NativeWindow`) does **not**: it comes out with `stereo=false`.
- Setting a stereo *default* surface format makes the whole top level stereo, against the separation rule: set the format on the 3D area's own window only.
- Qt's client-side decorations once flattened stereo windows; our Qt gives the decorations' content framebuffer a slot per eye ([danielcamposramos/qtbase `stereo3d-csd`](https://github.com/danielcamposramos/qtbase/tree/stereo3d-csd)).
- A translucent Qt window is forced to an 8-bit alpha, so its 2D part is 8 bits even when the 3D area is deeper; a fix in Qt is being written. Until then, put any deep content in its own layer, as Krita does.

## X11 programs

Under Xwayland, a 3D area is a child X window. Our Xwayland gives a redirected child window a surface of its own and keeps alpha on 32-bit surfaces, so the same separation works for X11 programs; the declaration goes through the X11 side of the same library. Native Wayland is the route to prefer when the toolkit has it.

## Proof for this kind of work

As in the general skill, plus:
- **0 differing pixels between the eyes outside the 3D area** (the menus, the toolbars, the window background);
- **exactly one declaration**, on the 3D area's surface, and none on the top level;
- **no squeeze:** with stereo off the window has its normal size, and with stereo on the 3D area holds both eyes at full size;
- **overlays:** an overlay over the 3D area changes the same pixels in both eyes and none in one eye only;
- **the 2D control:** stereo off against the distribution's build, 0 differing pixels.
