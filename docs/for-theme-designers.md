# For theme designers and customizers: depth is a design material

On Sparky Stereo OS the desktop has real depth, and a theme decides how it looks.
Shadows, bevels and raised or sunken frames have drawn depth in 2D for decades; here the same meanings become a distance your eyes can see.
This page says what you can design with, the rules every theme keeps, and what is designed and coming.
Each part is marked **built** or **designed (coming)**.

## What you can design with (built)

**Status:** built in Stereo KWin on our KWin branch [`stereo3d-depth`](https://invent.kde.org/danielcamposramos/kwin/-/tree/stereo3d-depth), coming with the next KWin package.

- **Three planes: sunk, screen and popped.** The active window sits at the screen; its menus, dialogs and tooltips pop; the wallpaper and the windows behind sink. All subtle, a few pixels of parallax.
- **Everything in between is Stereo KWin's, by stacking order.** Background windows share the depth behind the active window in the same order as in 2D, so a pile of windows reads as a pile of papers. Any depth between the limits is valid; nothing goes beyond them.
- **The limits are the user's.** System Settings, "3D Depth", sets how far popped comes out and how far sunk goes back, in pixels at a view 1920 wide, scaled to each screen; zero switches depth off. A theme's depth lives inside the range each user chose.
- **The screen's edge.** A popped thing that touches the edge of its screen stays at the screen's depth, because depth in front of the screen that the screen's frame cuts through looks broken. Panels touch the edges, so they sit at the screen. Leave a small gap when something near an edge should pop.
- **Shadows lie on what they fall on.** A window's shadow takes the depth of whatever it lands on, not the depth of the window that casts it.
- **The pointer takes the depth of what it is over.**
- **Stereo content stays 3D everywhere.** A 3D movie or game keeps both eyes wherever its window sits in the pile.

## Pop: a little scale and a little depth, together (designed, coming)

- **One value per element gives both cues:** bigger and nearer when popped, smaller and further when sunk.
- **Everything follows its element's plane:** its text scales and moves with it, and so does its click area.
- **Text shares its element's depth.** What tires the eyes is 2D text lying over a picture at another depth, not depth as such.
- **On a 2D screen, the pop is the same scale plus a move up and to the left,** so depth reads on every screen, with or without glasses.
- **Elements declare their planes, and Stereo KWin draws them for each screen.** A theme says where a part sits; it never draws a second eye for the desktop's own parts. Pictures that carry their own eyes, such as stereo icons and 3D backgrounds, are full side by side, like any stereo picture.

The edition's own look, Stereo Oxygen, made from KDE's Oxygen, is the first theme being made this way.

## The rules every theme keeps

- **A window is never behind anything it covers.** Depth always agrees with what covers what. Stacking and focus keep this today (built); dragging, dropping, dialogs and effects keep it as they arrive (designed). Changes between depths are eased, never a jump.
- **Comfort.** Depth stays within the user's limits. Your eyes turn to the depth they see while they focus on the screen; the further those two disagree, the sooner people tire, which is the "zone of comfort" measured by Shibata, Kim, Hoffman and Banks ([Journal of Vision, 2011](https://doi.org/10.1167/11.8.11)). The desktop's limits are kept to a few pixels for that reason; the default values are our own rule, and each user can change them. Effects with large depth honour KDE's animation speed and the desktop's reduced-motion setting (the `reduced-motion` key of the [freedesktop Settings portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Settings.html)) (designed).
- **Every theme works on every output.** 3D televisions, anaglyph on any monitor, headsets, and 2D screens. On a 2D screen only one view is drawn, and an effect's depth leaves it exactly as it looks today.
- **One place for depth, one rule for everyone.** The user's limits and the theme's depth settings live in one place, and every effect, theme and program reads the same values; none brings a depth rule of its own. Effects get a depth range of their own there, with room for creative motion beyond the desktop's subtle limits, editable by users and developers alike (designed).

## Effects with their own depth (designed, coming)

Today KWin's effects are flat: Glide and Sheet draw a perspective picture once for both eyes, and Fall Apart moves its pieces in the plane of the screen.
Their stereo versions describe their motion once, in three dimensions, and the renderer's two cameras make each eye; no effect needs to know which eye is being drawn.
On 2D screens they look exactly as they do today.

- **Fall Apart, Fly and Dive.** With Fly, a closing window's pieces come toward you as they fade. With Dive, they fall into the depth behind the screen, land on a floor and bounce while they fade. A background window being closed makes a short opposite move first, as an anticipation.
- **The floor belongs to the theme.** Where Dive's pieces land, the floor's size and its depth, is part of the theme, so a theme fits it to its own background: the bottom of a well, a table top, the last layer of a 3D wallpaper.
- **Glide.** An opening window swings in from behind to the screen; a closing one swings away behind it.
- **Sheet.** A dialog comes down from its parent window at the popped depth. A dialog over a dialog may go one step further, and that is the end: a third stays at the second's depth.
- **The drag lift.** A window you pick up rises a step, with a setting from flat up to popped, and never sinks. While it passes over a popped window it rises to that window's depth and comes back down when it leaves; dropped there, it keeps that depth, so no window is left behind what it covers.

## 3D backgrounds (coming)

**The engine is a video wallpaper.** [org.kde.video](https://github.com/Sparky-OS/org.kde.video), the video wallpaper and lock screen plugin by **Jeromy Streets**, has been in Sparky's repository since 2018 and is offered in APTus, Sparky's app installer.
It now lives in the Sparky-OS organization, with Jeromy Streets as its maintainer, and its Plasma 6 port is the next step, done with him.

**Then stereo, behind the desktop.** Stereo video and stereo stills play on the sunk side, behind every window, with the windows always in front.
The plugin is QML, so it shows them through the QML item of the shared stereo layer (`libstereo-layer1`), the same layer the edition's picture viewers use: file marks first, full side by side inside, every output converting for its own screen.
Scenes whose depth seems to go on forever, like facing mirrors, become possible.

## An example theme, in words: the well

This is a design example of what the pieces above allow together, not a theme that exists yet; every part of it is designed and coming.

- **The background is a well.** You look down into it, and the water at the bottom reflects a sun that moves.
- **Closing a window with Dive,** its pieces fall into the well and bounce on its bottom, never outside it, because the theme put the floor there.
- **The water mirrors your desktop.** The compositor holds a live picture of every window, so the background can reflect the windows above it, rippling.
- **The light follows the real sun.** Night Light already knows your location and the times of sunrise and sunset, so the well's light can follow your day.
- **The well calms while you work.** When a window is active, the background's depth eases toward the screen and its motion slows; when you come back to the desktop, it opens up again. Your eyes are never pulled between text at the screen and a deep, moving background. How much it calms is the theme's setting.

## How to get involved

- **The themes issue:** ISSUE_LINK. Ideas, sketches, side-by-side mockups and wallpapers in MPO, JPS or side by side are all welcome there.
- **The beta tester calls:** [#26](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) in English, [#25](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) in Portuguese, [#27](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) in Polish. You don't need a 3D TV: red and cyan glasses on any monitor are enough to see depth.
- **Read more:** [Depth on the desktop](depth-on-the-desktop.md), the [house formats](house-formats.md), and the design in one page, [STEREO3D.md](https://invent.kde.org/danielcamposramos/kwin/-/blob/stereo3d/STEREO3D.md).

## References

- **Comfort:** T. Shibata, J. Kim, D. M. Hoffman and M. S. Banks, "The zone of comfort: Predicting visual discomfort with stereo displays", Journal of Vision 11(8):11, 2011, [doi:10.1167/11.8.11](https://doi.org/10.1167/11.8.11).
- **Reduced motion:** the [Settings portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Settings.html), `org.freedesktop.appearance` `reduced-motion` (added in xdg-desktop-portal 1.21).
- **Stereo pictures:** CIPA DC-007 (Multi-Picture Format, MPO); JPS; full side by side, left eye first, as in the [house formats](house-formats.md).
