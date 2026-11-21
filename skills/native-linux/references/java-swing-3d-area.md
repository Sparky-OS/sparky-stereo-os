# A Java Swing window's 3D area (Jmol)

Learned on Jmol 16.3.55 (ORDER 50 step 4, November 2026), Debian's OpenJDK 25 on the edition's session, Stereo KWin +stereo3d59, libstereo-declare 1.12.1.
The recipe first, then the traps with their symptoms.

## Where a Swing program draws on the edition

OpenJDK has no Wayland toolkit in Debian testing: a Swing program is an X11 client of Xwayland (its window is in `xwininfo -root -tree`, its class in `WM_CLASS`, e.g. `org-openscience-jmol-app-jmolpanel-JmolPanel`).
Swing's components are lightweight: a `JPanel` has no X window, Swing paints it into its frame's X window.
So a 3D area needs an X window of the program's own, made with Xlib through JNA (which Debian's Java programs often carry already: Jmol has `jna.jar` on its class path), and declared with libstereo-declare through JNA as well.

## Recipe

1. **The frame's X window:** `Native.getWindowID(frame)` (JNA, through JAWT) once the frame is showing.
2. **Two windows of your own** on your own Xlib connection (`XOpenDisplay(null)`): a place window of the panel's size, child of the frame's window, at the panel's position (`panel.getLocationOnScreen()` minus the frame window's root origin from `XTranslateCoordinates`), and inside it the views window, two views wide. `XCreateSimpleWindow` selects no events, so clicks, the wheel and keys go on to the frame and Swing dispatches them to the panel as before.
3. **Declare the views window** on the managed top-level (the nearest ancestor with `WM_STATE`, ICCCM 4.1.3.1): `stereo_declare_x11_child(display, toplevel, views, 3, 4, 0, width, height)` with the size one view is shown at, when `stereo_supported_x11()` is 8 or more; `stereo_declare_x11_one_view_size()` when the panel's size changes; `stereo_remove_x11_child()` when the area goes.
4. **Let the program draw each eye at the panel's size.** Jmol's side-by-side mode (`stereo 5`) halves the width it is given (`Viewer.setScreenDimension`: `width = (width + 1) / 2`), so the panel tells it twice its width and paints into an image two views wide.
5. **Put the image into the views window:** `XCreateImage` (ZPixmap, the window's depth from `XGetGeometry`, 32 bits per pixel) over a JNA `Memory` filled from the image's `int[]` (TYPE_INT_RGB is the X server's 0x00RRGGBB on little-endian), `XPutImage`, `XFree` of the XImage only (the memory is yours). Paint the left eye's picture into the panel too, so a screenshot of the window or a desktop that drops the area still shows the right view.
6. **Popups get windows of their own:** `JPopupMenu.setDefaultLightWeightPopupEnabled(false)` and `ToolTipManager.sharedInstance().setLightWeightPopupEnabled(false)`, or a menu that drops over the area is drawn under the child window.
7. **The person's switch:** "Enable 3D" in the program's menu, stored in the program's own preferences only when the person changes it; the default in the program's own default table. Where the desktop announces no stereo at all, the window stays flat and nothing is said; where it is a stereo desktop that cannot (support under 8), or the person ticked the box, say it once in a dialog, in the person's language (Jmol: a `ResourceBundle` of its own, `Stereo3D.properties` and `Stereo3D_pt_BR.properties`).

## Proof (Jmol, the installed package, a virtual Stereo KWin 1920x1080, AMD)

Fixture: six atoms at known places drawn with flat colours (`set ambientPercent 100; set diffusePercent 0; set specular off`), so each atom's centroid can be read in each eye; `stereo 5` with `set perspectiveDepth false` (the preset).
Jmol turns the right eye's picture by minus the angle about the vertical axis through the centre of rotation (`TransformManager.getStereoRotationMatrix`), so `disparity = s (x (cos a - 1) - z sin a)` pixels for an atom at `(x, z)` Angstrom, `s` the pixels per Angstrom read in the left eye.

| Row | Expected | Got |
|---|---|---|
| ours, Enable 3D on (default) | a pair; one declared child, two views wide, listed; nothing differs outside the area; atoms on the prediction; vertical 0 | capture 3840x1080; child 1000x500, one view 500x500, listed, limits [10, 4]; 0 pixels differ outside; oxygen (z = 3) -10.0 px against -9.65, sodium (3, 3, 3) -10.0 against -10.07, sulfur and chlorine -0.39 and +0.39 against -0.42 and +0.42; vertical 0.0 for every atom |

## Traps

- **Symptom:** the patch is a whole-file rewrite of `DisplayPanel.java` and `Jmol-resources.properties` (930 changed lines for a 116-line change). **Cause:** those files have CRLF line ends and the editing tool wrote LF. **Fix:** write the edited file back with the original's line ends. **Found by:** `diffstat` on the patch before committing it.
- **Symptom:** the program's state cannot be read from the application's package (`stereoDoubleFull`, `stereoDegrees` are package-private in `org.jmol.viewer`). **Fix:** two public getters in `TransformManager`, nothing else in the viewer.
- **Symptom:** a cross-eyed setting (`stereo on`, a negative angle) gives inverted depth. **Cause:** Jmol puts the left eye's picture on the right for a negative angle. **Fix:** hand the halves over exchanged, left eye first; the angle stays the program's.
- **Symptom:** in the rig the window does not follow KWin's maximize (KWin's frame is 1920x1080, the content stays at the start size). Not chased: the area follows the panel's own size; measure at the program's own size.
- **Symptom:** a KWin script that matches the window by "Jmol" in its caption finds nothing. **Cause:** Jmol titles its window after the file. **Fix:** match `resourceClass`.
- The class sets no X error handler: Xlib's handler is one for the whole process and AWT installs its own; swapping it would hide AWT's errors.
