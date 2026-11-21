# A program that rotates its scene for the second eye (Jmol), and a plotting module of ours fitted to the limits (Matplotlib)

Learned in ORDER 50 step 4 (November 2026) on Jmol 16.3.55 and Matplotlib 3.10.9, Stereo KWin +stereo3d59, libstereo-declare 1.12.1.
Which case a program is decides everything: a program that draws its own pair keeps its own separation (Daniel, 2026-11-18, "I agree"); a scene where we add the cameras is fitted to the person's limits ("the camera offset is the largest for which every pixel of the 3D area stays inside the person's limits").
Read it in the program's own source before anything else.

## Jmol: its own pair, made by turning the model

**What its source does** (`org/jmol/viewer`): `stereo on`, `stereo N` choose the mode DOUBLE; `TransformManager.getStereoRotationMatrix` turns the right eye's picture by minus the stereo angle about the vertical axis through the centre of rotation (`setAsYRotation(-stereoRadians)`), the left eye's picture is the unturned view; `Viewer.getScreenImageBuffer` draws the turned picture in the right half and the unturned one in the left half; `setScreenDimension` halves the width it is given.
A negative angle (the default of `stereo on`, -5) is cross-eyed: the left eye's picture is in the right half (Bob Hanson's answer in Jmol-SwingJS issue 58, quoting Jmol's documentation).
`set perspectiveDepth false` makes the projection orthographic, and then turning the model is the skill's orbit for an orthographic view with one eye at 0: no vertical disparity.

**The closed form** (orthographic): an atom at `(x, z)` Angstrom from the centre, `s` pixels per Angstrom, angle `a`: `disparity = s (x (cos a - 1) - z sin a)`, right eye minus left eye. The `x (cos a - 1)` term is the horizontal shrink of the turned eye (0.38 % at 5 degrees): the one-sided turn is not a symmetric orbit, and it shows as plus and minus a few tenths of a pixel at the model's sides.
**Measured** (the edition's jmol, a 500 px panel, 36.9 px per Angstrom, `stereo 5`): oxygen at z = 3, -10.0 px against -9.65; sodium at (3, 3, 3), -10.0 against -10.07; sulfur and chlorine at x = +3 and -3, -0.39 and +0.39 against -0.42 and +0.42; vertical 0.0 for every atom.
The depth is Jmol's own: 10 px in front of the screen, past a popped limit of 4. It is a program with its own internal 3D setting (Daniel, 2026-11-19), so it is reported, not fitted.

**The rig's fixture:** six atoms at known places and flat colours (`set ambientPercent 100; set diffusePercent 0; set specular off`), so each atom is one exact colour in each eye and its centroid is read per eye; sulfur and chlorine 6 Angstrom apart give the scale in the unturned eye. An atom straight behind another is hidden in the left eye (nitrogen behind oxygen): read it only where it shows.

## Matplotlib: our cameras, fitted

**The cameras** (python3-stereo-matplotlib, `stereo_matplotlib.cameras`): Matplotlib 3.10 builds `projection @ view @ world` in `Axes3D.get_proj`; the module puts one shear between view and projection, `x' = x + s c (d - z0)` with `d` a point's distance in front of the camera, `z0` the axes' centre (`dist * focal_length` in perspective, `dist` in orthographic), `c = 1 / z0` in perspective (a camera moved by `s` with its frustum shifted back: parallel, off-axis) and `c = 1` in orthographic (the shear about the camera target). Left eye `s = -b`, right `s = +b`. Closed form, in Matplotlib's projected units: perspective `2 b e (1 / z0 - 1 / d)`, orthographic `2 b (d - z0) / z0`; times the x scale of the axes' `transData` for pixels.
**The fit:** draw the figure once with Matplotlib's own camera while recording every point it projects with an Axes3D's own matrix (wrap `proj3d._proj_transform_vec` and `_proj_transform_vec_clip`, match the matrix by identity): data, panes, grid, ticks and labels. Disparity is linear in `b`, so each point's disparity per unit offset gives the largest `b` for which every point inside the 3D area stays within `[-popped, +sunk]`. A planar polygon's depth between its corners is bounded by its corners', so no drawn pixel passes a limit.
**The limits:** `stereo_declare.x11_buffer_limits(display, window, buffer_width, shown_width)` on the declared window (libstereo-declare 1.11 or later), never an arithmetic of the module's own.

## Traps

- **Symptom:** an interactive figure redraws without end once the pair is drawn. **Cause:** marking an axes stale (`ax.stale = True`) when the eye cameras are put on or taken off makes a figure in interactive mode schedule a redraw, whose draw event draws the pair again. **Fix:** never mark stale around `Figure.draw`; a draw computes every projection anew.
- **Symptom:** a test that counts projected points fails with exactly three. **Cause:** with the axes switched off only the markers are projected. Count what the scene draws; test the axes box separately (panes, grid and labels give more than fifty points).
- **Symptom:** Tk or Qt dies on an X error after the canvas is destroyed. **Cause:** Xlib's error handler is one for the whole process and the toolkit's Xlib shares it. **Fix:** set a quiet handler only around the module's own calls, `XSync`, and put the previous one back.
- **Symptom:** the old module raised NotImplementedError for orthographic plots ("parallel orthographic rays discard depth"). **Cause:** it moved the camera, which an orthographic projection cannot see. **Fix:** the shear about the target, as GNU Octave's orthographic plots in the edition.
