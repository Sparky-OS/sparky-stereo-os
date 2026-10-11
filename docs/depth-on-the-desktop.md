# Depth on the desktop

**Three places, declared: sunk, screen and popped.** All subtle, a few pixels, with the limits your own settings (System Settings, "3D Depth"). The active window sits at the screen; its menus, tooltips and notifications pop; the wallpaper and the windows behind sink.

**Everything in between is Stereo KWin's job, by stacking order.** Stacked background windows fan out from sunk towards popped, always behind the active window, in the same order as in 2D. A window caught in the middle of a pile, its edges out of the stack, reads as a sheet floating within it, the way a pile of papers looks in real life. No program declares this; it falls out of the order.

**In the background, each window is 2D.** A window in the pile is a flat sheet at its place in the stack: the desktop's pop effects inside it come to one plane. Its stereo content stays 3D: a movie or a game is full side by side wherever its window is, so a 3D movie plays on one screen while you work on another.

**Pop is real, not faked: a little scale and a little depth, together.** One value per element gives both cues: bigger and nearer when popped, smaller and further when sunk.
- **Everything follows its element's plane:** its text scales and moves with it, and so does its click area, so a popped element has no dead margin and a sunk one no click area beyond its picture. The plane's geometry lives inside the window itself, the one geometry that drawing and input both read.
- **Text shares its element's depth.** What tires the eyes is 2D text lying over a picture at another depth, not depth as such.
- **On a 2D screen, the pop is the same scale plus a move up and to the left,** so depth reads on every screen, with or without glasses.

## The Desktop Cube: what one format makes possible

Plasma's Desktop Cube, rebuilt on the standard, shows what follows from one format without inventing anything new.
- **It is a 3D application, treated like a game:** its scene has its own depth and hands Stereo KWin full side by side, two views of one scene, one camera per eye.
- **Its faces are your real desktops, each a stereo surface.** The windows on a face sit on the desktop's three planes (sunk, screen and popped, with the pop your own setting), so each face is a relief, and the cube's cameras see the windows standing off its faces from any angle.
- **When it closes on one desktop, it is the desktop:** the front face lands on the screen plane, identical to the flat desktop.
- **It is the seed of the VR home:** the same scene, seen through a headset's cameras, is a floating 3D desktop.

**On a 2D screen, too.** A straight 2D screen shows only the left eye, as always, and never renders the second one. But during the cube's animation that one view is still the real 3D scene: live desktops on a turning cube, windows in relief, depth shown by perspective and motion alone. Desktop interfaces have seen little new in years; the cube that is real depth on a 3D screen is something new on a 2D one, before anyone puts on glasses.
