# One separation, one place

The spec in three lines (stereo-layer docs/display-depth.md, "The depth of a display: one source"):
1. The person's depth limits are set in one place, the desktop's 3D Depth settings, built on the display; they are pixels of a view 1920 wide of the screen.
2. Stereo KWin applies them per output, `lround(limit x output width / 1920)`; a program hands KWin full side by side at any resolution and KWin scales once.
3. A program never scales a limit by its own window, picture, thumbnail, icon or render buffer; the only arithmetic a place may do is the unit conversion of the screen's value into the pixels of a buffer KWin will scale.

Exceptions, and only these: a program with its own internal 3D settings, and content that carries its own authored pair (a stereo photograph, a film, an icon pair rendered by a tool).
Established programs have no formula tying separation to a window or screen size: Bino's source has no separation or parallax code, sView's separation is the person's own offset, mpv and VLC have none.

## Proof, large and small
Run the same content large and small on one screen in a Stereo KWin rig (a real plasmashell, a 3D twin mode), capture both eyes as arrays, and read the separation as left minus right in output pixels (positive in front of the screen); the swapped reading must flip the sign.
On a 1920 wide output at the defaults the desktop elements stand at wallpaper -10, inactive windows -2, -4 and so on, active window and panel 0, menu +4, sub-menu +8.

## Traps
- Symptom: stereo icons flat up to 64 px. Cause: the icon tool set the camera separation as a share of the picture's width (`DEPTH_RANGE = 0.03`), so the same fraction gave less than a pixel at small sizes. Found by measuring the pair files (block matching, sub-pixel). Fix: `tools/icons3d/scene.py` takes the range in pixels of a 1920 wide screen and chooses the separation and the convergence plane per size.
- Symptom: a protocol sentence told programs to "scale them to its own view's width". Cause: kde_stereo_depth_v1 `depth_limits` description (KWin s43-0001). Fix: the limits are the screen's; programs get them in buffer pixels from libstereo-declare's `stereo_depth_limits_for_buffer`.
