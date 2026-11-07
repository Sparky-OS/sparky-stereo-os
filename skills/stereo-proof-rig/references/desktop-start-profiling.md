# Desktop startup profiling on another machine

Symptom: a desktop program starts slower after an edition upgrade, although its own package did not change.
Compare the compositor and shared userspace before assigning the cost to the program or kernel.
Performance is information, never a release gate.

## Establish the measuring state

1. Read the upgrade's exact before and after versions, raw repetitions and definition of its timing mark.
   A first mapped window and Plasma's desktop-ready stage are different observations.
   Separate fresh configuration, cold page cache and warm starts.
2. Check the disk floor, running kernel and installed package cohort on the target.
   Take its shared bench lock, record the holder PID and set core limits to zero.
   Every cooling or readiness wait has a timeout.
3. Use a fresh nested headless KWin, private D-Bus and private HOME for each launch.
   A machine at its display-manager greeter is sufficient for this method.
   Do not add physical-screen power or activity calls: those belong to a separately authorized real-display bench.
   Keep application caches according to the chosen cold or warm mode.
   Check the temperature immediately before each measured launch, using the same gate on every variant.

## Collect and interpret the profile

Keep ordinary timing repetitions separate from profiling runs, because profiling adds overhead.
Profile only the private compositor, application and its descendants.
Record monotonic start and window timestamps, so startup samples can be separated from post-window activity.
Include loader work when choosing how to start or attach the profiler.
An on-CPU hot path alone does not explain time spent blocked on I/O or another process.
Retain enough call-stack and symbol information to name the measured function, rather than guessing from a patch title.

Only after the profile gives a suspect should the package A/B remove that change.
Build with the edition recipe and the same dependencies, then extract each variant into its own private prefix.
Use its explicit KWin executable, library path and plugin paths in the private session.
Verify the running executable and mapped libkwin paths before accepting a row.
A local rebuild of the published source is a useful control for changed build dependencies.
Test a staged next-round build separately from the causal A/B.
Keep the installed package cohort unchanged, stop every nested session, stop the holder by its recorded PID and confirm a nonblocking lock acquisition.
Report unsuccessful starts as failures, never as timing samples.

## Traps found during preflight

- Symptom: the ScreenSaver activity call fails while the machine is at its greeter.
  Cause: a real-display bench prerequisite was mistakenly copied into a nested headless startup probe.
  Fix: remove all physical-session and output operations from the headless probe; a greeter does not block private D-Bus/KWin sessions.
  Found by: checking the method against the task's isolation rules and the earlier benchmark's actual launch command.
- Symptom: Python raises `AttributeError` for `SessionBus.get_unix_process_id`.
  Fix: call the session bus's `org.freedesktop.DBus.GetConnectionUnixProcessID` method with the private KWin's bus name.
  Found by: the instrumented probe's traceback before the application launch; exclude that failed row.
- Symptom: a borrowed container image runs bash as a script and reports that the binary cannot be executed.
  Cause: the image already had bash as its ENTRYPOINT.
  Fix: inspect the image metadata and override the entrypoint explicitly when supplying a new script.
- Symptom: apt cannot find `/repo/./Packages` despite a valid distribution tree being mounted there.
  Cause: an inherited flat-repository source in the borrowed image.
  Fix: replace that container-local source with the mounted tree's actual suite/component source before updating indexes.

## Profile reading seen in practice

- Symptom: a new compositor package is suspected, but startup samples are mainly in the application.
  Keep the measured compositor/application CPU share and the elapsed time separate.
  Loader symbol lookup below Qt Wayland EGL initialization is an application startup path; PNG inflation below WallpaperItem/QImageReader is a wallpaper load path.
  A small compositor share is a reason to test the compositor A/B, not proof that the remaining elapsed time belongs to another package.
- Symptom: a cooler probe no longer reproduces the older median.
  Retain both observations and compare package variants under the same new gate.
  Do not relabel historical state as a package cause, and record whether the earlier gate was per batch or per launch.
- Symptom: a profile contains setup or post-window activity.
  Record with the monotonic clock and restrict reports to the application's exec/start mark through its first-window mark.
  Keep unprofiled controls because sampling, call-stack collection and profiler startup can change timing.

- Symptom: an exported recipe is refused as a broken Git checkout inside a container.
  Cause: a broader workspace mount exposes an ancestor `.git` that is not usable from the container.
  Fix: mount the exported recipe directly at a dedicated container path with no Git ancestor, rather than pretending that the broken checkout is an export.
- Symptom: an installed compositor's `/proc/PID/maps` is unreadable by the test child, while an extracted variant can be inspected.
  Record file capabilities and the metadata refusal; extracted packages may differ from the installed executable's privilege metadata.
  Keep prefix verification strict, and compare all causal variants through the same prefix method.
- Symptom: a long build's caller disappears and the last captured log predates a surviving package.
  Check archive completeness and the saved source/configuration metadata before reusing that package.
  A missing container and incomplete log do not establish an OOM, compiler failure or disk failure.
  Copy the driver script into the disposable build layer before executing it; do not edit a running shell script in place.

- Symptom: a private perf output file is used, but build-ID caching was never scoped.
  Use `perf record --no-buildid-cache` when the recording itself retains the required build IDs, and give report tools a private HOME and explicit debug-download policy.
  The record option prevents cache updates; a private output filename alone does not.
  Never purge a shared cache when its prior ownership was not recorded.
- Symptom: a second paired batch changes the difference between the two groups' medians.
  Report that difference and the median of the per-pair differences separately; they are different statistics.
  Retain outliers and reverse the initial variant order in the confirming batch.
  A small remaining difference without a changed hot function is an unresolved attribution, not a reason to disable a feature or invent a fix.
