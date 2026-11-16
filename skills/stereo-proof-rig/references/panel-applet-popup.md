# A panel applet's pop-up in the rig (the volume applet over the panel)

Written on 2026-11-16 (ORDER 464b).
It measures, in both eyes, where a pop-up opened from a panel icon stands against the panel and against a window under it.

## Recipe

1. **The image.** The rig image with the edition's `plasma-workspace`, `plasma-desktop` and `plasma-pa`, plus `pipewire-pulse`, `python3-jeepney`, `wayland-utils`, `dbus-x11` and `kactivitymanagerd`.
   Check `dpkg-query -W kwin-wayland plasma-workspace plasma-desktop` for the set under test; an apt log's `Inst` lines are not printed by a real install, so do not count them.
2. **PipeWire with a null sink, inside the container, before plasmashell** (nothing of the host's sound is touched):
   ```
   export PIPEWIRE_RUNTIME_DIR=$XDG_RUNTIME_DIR PULSE_RUNTIME_PATH=$XDG_RUNTIME_DIR/pulse
   pipewire & sleep 1.5; wireplumber & pipewire-pulse & sleep 1.5
   pw-cli create-node adapter '{ factory.name=support.null-audio-sink node.name=rig-null media.class=Audio/Sink object.linger=true audio.position=[FL FR] }'
   wpctl status    # the sink is listed and starred as the default
   ```
   The applet then shows the device and its slider instead of "No output or input devices found".
   The `rtkit` errors in `pipewire`'s log (no system bus) are harmless.
3. **One panel with known widgets**, through the shell's scripting: `panels().forEach(p => p.remove())`, then a `Panel` with `location`, `height = 44`, `kickoff`, `volume`, `digitalclock`.
   The widgets pack from the start of the panel, so the volume icon is at start + 1.5 x height (along the panel), half the height across it.
   For the person's own task bar put `icontasks`, `systemtray` and the clock instead and read the tray icon's place from one capture.
4. **The click:** KWin's fake input, `m:X,Y`, `s:300`, `b:272`, `s:1800` (logical pixels).
5. **Pinning:** click the pin button, the last icon of the pop-up's header (frame right edge minus 16, frame top plus 30 logical px).
   Then open another window (a Qt widgets test window), place it with a KWin script and click on it: the pinned pop-up must keep its level and its place.
6. **Numbers from KWin, not from the picture:** a KWin script that prints `workspace.stackingOrder` with `frameGeometry`, `appletPopup`, `dock`, `layer`, `opacity` and the screens' geometry.
   The pop-up's border from the output edges is its frame against the screen geometry.
7. **Disparity:** the shift that makes the right eye's rows inside the pop-up's frame equal the left eye's (device pixels, left minus right); also search rows -4 to 4 at that shift: the vertical offset must be 0.
   The prediction is `lround(PoppedLimit * deviceWidth / 1920)` for a pop-up (a dock gets 0): 4 at the default on a 1920-wide output, at any scale, because the width is the output's device width.
8. **The pop-up-only reference by opacity:** a KWin script sets `w.opacity = 0` on every window that is not an applet pop-up or the desktop, then a capture; set it back to 1.
   With BASE (the scene before the pop-up opened) and REF (the pop-up alone), the overlap rectangle is classified per pixel: where BASE and REF differ, is the capture like REF (pop-up in front) or like BASE (the other window in front).
   Check the classifier itself with the same images: BASE as the capture must give all "other window", REF all "pop-up".
9. **No natural overlap with a floating panel:** the pop-up's frame ends where the panel's frame starts (the panel window is the bar plus its floating margin).
   To test the stacking anyway, move the pop-up into the panel with a KWin script (`w.frameGeometry = {...}` on the pop-up) and name the capture "forced overlap"; say in the report that the overlap was forced.

## Traps

- Symptom: `E: Conflicting values set for option Trusted regarding source file:/repo/ mashtabba`.
  Cause: the rig image already carries a `sparky-stereo.sources` for `file:/repo`, and a second source file for the same path disagrees with it.
  Fix: mount the repository at `/repo` and add no source file.
  Found by: `cat /etc/apt/sources.list.d/*` in the image.
- Symptom: an install step "installed 0" packages (`grep -c '^Inst'` prints 0) while `dpkg-query` shows them installed.
  Cause: apt prints `Inst` lines only in a simulation.
  Fix: read `dpkg-query -W` after the install.
- Symptom: `sed: -e expression #1, char 4: missing command` in the container script.
  Cause: `sed -n 1,25` without the `p` command.
  Fix: `sed -n 1,25p`.
- Symptom: `cp: cannot stat '.../cfg/out-1.json'` in a case that worked by hand.
  Cause: the run script mounted only the work folder and the lane folder, and the config was written beside them.
  Fix: write inputs under a mounted folder.
- Symptom: no overlap to measure although the pop-up "opens over the panel".
  Cause: the pop-up's frame and the floating panel's frame only touch (pop-up bottom 1020, panel window top 1020).
  Fix: step 9, and say that the natural placement has no overlap.
- Symptom: a pinned pop-up is gone when another window takes the focus although the capture after the pin click looked right.
  Cause: the pin point was computed from the pop-up's frame before the pop-up had been moved (a forced overlap), so the click missed the pin button and the pop-up closed on focus change.
  Fix: read the pop-up's frame from KWin again just before the pin click; check that the pop-up is still in the window list after the other window is focused.
  Found by: the window list after the focus change had no applet pop-up, and a crop of the capture showed the pin icon at 24 px below the click.
- Check of the instrument: classify the same images with BASE as the capture (every discriminating pixel must read "other window") and with REF as the capture (every one "pop-up"); a run gave 6045 of 6045 both ways.
- Two outputs: write a second entry in `outputs` (new uuid, connector `Virtual-1`) and in `setups` (position at the first output's width), start KWin with `--output-count 2`, take the capture of the panel's screen by name (`CaptureScreen`), and subtract that screen's origin from every logical rectangle.
