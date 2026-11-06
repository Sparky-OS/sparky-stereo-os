# Declaring an X11 child window: a player's video window

Learned on VLC Stereo's Qt interface (ORDER 265, November 2026).
The recipe first, then the traps with their symptoms.

## Recipe

1. The 3D area is a native child window of the interface's top-level window (Qt's `WA_NativeWindow` widget, a toolkit's GL area). Find the top-level: walk `XQueryTree` upwards from the child to the nearest ancestor that carries `WM_STATE` (ICCCM 4.1.3.1; the window manager manages it), else the last ancestor below the root.
2. Declare the child, and let the library list it in that top-level window:
   `stereo_declare_x11_child(display, toplevel, child, STEREO_SBS_FULL, STEREO_CLASS_VIDEO, STEREO_VIDEO_CURRENT, 0, 0)`.
   It needs `stereo_supported_x11(display) >= 5` and libstereo-declare 1.7.0, so the package says `libstereo-declare1 (>= 1.7.0)` in its Depends and `libstereo-declare-dev (>= 1.7.0)` in its Build-Depends (the symbol's version is not in the library's `shlibs`).
3. Draw one view in each half of the child's own buffer. Stereo KWin shows the left half to the left eye and the right half to the right eye, each at the place of the child's rectangle, and the interface around it the same in both eyes.
4. When the video closes, or a 2D video takes its place in the same window, call `stereo_remove_x11_child(display, toplevel, child)`: it takes the child out of the top-level's `_KDE_NET_WM_STEREO_CONTENT_CHILDREN` and deletes its format and class.
5. Wrap the two calls in an Xlib error handler that ignores errors (set and restore it around `XSync`): the windows can be gone already, and Xlib's default handler ends the process.
6. When the declaration cannot be made (support below 5, no managed ancestor, an X error), say so: a message in the program's log with the reason and a dialog for the person. Showing the 3D video with one view as if it worked is a silent failure.

## Traps

- **Declaring only the child.** Symptom: the capture is one picture (`stereo` false, 1920 wide), the video area shows one colour, both eyes the same. Cause: Stereo KWin reads the children a top-level lists, and the library's `stereo_declare_x11()` on a child lists nothing. How it was found: walk the window tree with the properties in `stereo-proof-rig/scripts/x11_props.py`: the child had `_KDE_NET_WM_STEREO_CONTENT` and its top-level had no `_CHILDREN`.
- **Both eyes show the left view (red and red).** The child is declared and listed, but the program drew the second view beyond the window's right edge (offset by the window's width, as for a top-level that the compositor makes twice as wide). Stereo KWin does not make a child twice as wide: the child's buffer is its own, and the two views go in its two halves.
- **Why the program cannot double its child.** Qt's video widget reads the real size of the X window on every `ConfigureNotify` (`VideoWidget::physicalSize()` in VLC), so a child resized to twice its width reports twice the width back and the program cannot tell its own doubling from the person's resize. Until a toolkit gives the program a window of its own to size (the CHILD_PLACE route of `stereo_declare_x11_child_place()`, support version 8), each view is drawn at half the child's width and the compositor expands it once: lossless for a half side by side source in a window as wide as the frame, a halving of the horizontal resolution for the other packings.
- **The version of the library.** The plugin that calls `stereo_declare_x11_child()` loads against 1.0 and fails at run time with an undefined symbol: write the minimum version into Depends yourself.
- **A desktop that announces 4 or less.** Test the path with a preload that returns 4 from `stereo_supported_x11()` (`stereo-proof-rig/references/x11-session-rig.md`); the program must say so and the capture shows one view.
