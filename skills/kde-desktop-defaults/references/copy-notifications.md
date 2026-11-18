# Running copy popups dismiss while the job stays available

Plasma's native schema defaults Jobs/PermanentPopups to true.
The edition supplies false in `/etc/xdg/plasmanotifyrc`.
Find the installed file's owner before changing it: it belongs to plasma-workspace, so its successor carries the value, not the look package.
The source file is `libnotificationmanager/plasmanotifyrc`; leave the schema and every other setting alone.
KConfig reads the person's ~/.config/plasmanotifyrc above this system default, and a saved true remains true across upgrades.

## Recipe

1. Build the successor from the pinned published plasma-workspace source, preserving its existing patches and provenance manifest.
   Append the one configuration patch; retain the predecessor's Lean Code plan.
2. Install the built binaries and companions in the isolated rig through apt, checking the simulated and actual plan for removals.
3. Read org.kde.notificationmanager Settings in the real login, then start a genuine long KIO copy with KUiServerV2JobTracker.
   A throttled local HTTP source keeps the copy running without an external network.
4. Capture the early popup and the later desktop beyond popupTimeout.
   Read the private KWin window lifecycle, active JobViewServer path and growing destination bytes.
   Open the tray and capture the still-running job after the popup leaves.
5. Repeat on the predecessor, where the popup stays, and with a saved user true, where it also stays.
   A short finished job does not prove running-job behavior.

## Traps

- **Symptom:** a copy advances and has a JobView path but no notification window appears in a minimal rig.
  **Cause:** the notifications applet cannot instantiate PulseAudio.qml because plasma-pa is absent.
  **Fix:** install that real runtime dependency in the fixture and rerun the same control.
  **Found by:** the session log's missing org.kde.plasma.private.volume module.
- **Symptom:** the screenshot visibly has a popup but the checker reports none.
  **Cause:** its window class is org.kde.plasmashell, while the regular desktop is plasmashell.
  **Fix:** recognize both classes and track actual window IDs; do not infer popup existence solely from a screenshot filename.
  **Found by:** matching the screenshot to private KWin lifecycle logging.
- **Symptom:** a new patch loses credit for the older carried patches.
  **Cause:** provenance-files.py writes a new manifest rather than appending.
  **Fix:** preserve previous noncomment entries and add the new patch's entry.
  **Found by:** inspection of the first source-preparation attempt before accepting a build.
