# test-bench: lessons from the lanes of 25 October to 6 November 2026

Harvested by ORDER 429 from the accepted lane reports; each line names the lane it came from.
A trap gives its symptom, its cause, its fix and how the cause was found; a recipe gives the commands and the result to expect.

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: testQuickStereo fails since effects limits (30/12) make a stereo output paint twice; CI without a render node skipped it. Fix: switch the effects' depth off where a test needs no depth. Negative control: linear curve fails (sinking -2 for -6 at 103 ms). kde-ci-local cannot take a partial clone (--filter=blob:none) (lane kwin-stereo-effects)
- Symptom: random init() failure in testX11Window (6 of 14 runs, also on the stock image), then the Wayland connected() signal never arrives (5 s, 30 s no help). Cause found for the other test flake: QSignalSpy::wait() counts only signals after the call, so a signal of a thread that starts at once is lost; use a flag with qWaitFor. For the connection flake: failing at connection 80 of 150 on old code, passes with the fix; ruled out the socket accept, event loop, Xwayland and load. Retry (3 connections) kept as a workaround, root cause open (lane kwin-x11-child-243)
- Symptom: kwin-testVirtualStereoProtocol fails in kde-ci-local. Cause: it compared the output-device registry version with 25 while it is 27 after swap eyes (26) and iZ3D options (27). Also a missing libkpipewire-dev meant testScreencasting was never generated, and `quilt top` includes its directory prefix so a naive pop popped the whole stack (lane kwin-wiz3d-outputs)
- Symptom: tests of a script in a bare container drift when the script gains steps; EACCES tests pass as root. Fix: judge by the record key, use an unprivileged uid after the root setup (setpriv), and note that mktemp -d folders hide fixtures from that uid. Also: a runner Depends on its meta makes a cycle of three, and a plain apt-get upgrade left the integration map absent until a catalogue package took the file (lane no-fallbacks-system-346f3)
- Symptom: test of package remove/purge fails 8 checks. Cause: dpkg-deb -x does not install the postrm. Fix: dpkg --unpack so the real postrm runs. Also a Korean particle audit found 15 particles where the earlier count said 8 (repeats on one line, `%s 에서`, `%s 가`) (lane no-fallbacks-followups-346f6)
- Symptom: proot hides a child's exit status. Fix: tests write explicit inner status files and an absent file or non-zero status fails the harness (lane time-shortcuts-359)
- A Claude lane's `sh -c 'rm -rf $VAR ...'` is refused by the safety check even in a container script; use fresh unique directories instead of removing variable paths (lane graphics-page-227)
- Symptom: a test's EXIT trap fails. Cause: the trap referenced a BUS variable though no bus was started. Fix: the trap removes only its scratch. Found by: the old test erroring on exit. (lane no-fallbacks-drivers-346f2)

## Perks of the part

- A KWin build gate needs only a read-copy of the repository (dists/ plus amd64/all .deb files without -dbgsym or lc-hr): 892 files, 3.7 GB, 16 seconds, safe while a publication round swaps the live tree (lane kwin-screenshot2-0ea31ae7-330)
- Bench model: the person is in the room with hands and expert recovery, the partner has remote access only; announce before any load or reboot. The skill's NUT paragraph exists ("A UPS tells the machine to shut down, if you let it"). (lane test-bench-skill-395)

## Measured facts

- KWin CI image with render node: 183 tests, 182 pass including all 11 stereo tests; the one failure is testLockScreen (lock never reported) (lane kwin-stereo-effects)
- Audit method: classify a code path as U (unwanted silent fallback) or R (retry of the same artifact with a visible final failure); a retry that never ends in a visible failure is U (cushion calibration). Examples: ISO recipe excludes ZFS with pin -1 and ignores the purge failure; HEVC decoder error logs "H.264 fallback" to logcat only; build-from-dsc ignores apt update failure; a purge simulation returning 100 with no stdout still reaches the real purge because awk and sort return 0 (lane no-silent-fallbacks-audit-343)
- Add the pull-the-plug test and NUT's SHUTDOWNCMD to the bench sheet. Observed `allow_killpower 0` after a clean halt on a station UPS (nutdrv_qx, 2000 VA sine): decide per site whether the UPS should cut its output after the halt. Licences of bench-software references: Copilot MIT, NanoKVM GPL-3.0, Snipe-IT AGPL-3.0, LAVA GPL-2.0+, labgrid LGPL-2.1, Labrack unstated. (lane test-bench-skill-395)

