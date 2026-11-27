# Measuring kernel flavours on a real machine

**For contributors comparing the edition's v3 and PREEMPT_RT kernels.** Check package and boot identity first, then measure each workload with its own counters.
The package, baseline and workload instrumentation were exercised on build 18 on 2026-11-27.

## Verify what will boot

1. Verify the archive's signed `InRelease` with the installed distribution keyring, check the `Packages` and `Sources` indexes against its SHA-256 section, and check the selected image, headers and source archives against those indexes.
2. For each release, read `boot/config-RELEASE` from the image and `usr/src/linux-headers-RELEASE/.config` from the headers.
   List members with `dpkg-deb --fsys-tarfile DEB | tar -tf -`, then extract the named members with `dpkg-deb --fsys-tarfile DEB | tar -xOf - MEMBER`.
   The two config copies must agree.
   Diff the configs and compare normalized in-tree module paths.
   Compare the retained `SOURCE.edition.json` ordered patch paths and digests and the file bytes and symlink targets below each orig tarball's top-level directory.
3. At the bench, record the time, boot ID and `uname -r`, hash the installed config and compare it with the matching published payload.
   Read `dkms status` per kernel, and keep the installed instances, the package's eligibility rules, and any separate build qualification in the record.
4. Read `GRUB_DEFAULT`, the kernel in the selected entry in the generated menu, and `grub-editenv /boot/grub/grubenv list`.
   Record the existing fallback entry and simulate installation of the exact image and headers with `apt-get -s --no-install-recommends install IMAGE=VERSION HEADERS=VERSION`.
   Read `/etc/grub.d/10_linux` and its version sorter before relying on an index such as `GRUB_DEFAULT=0`.
   Verify the generated default still selects the original kernel after installation before setting `grub-reboot` to the exact submenu entry for a single boot.
   Recheck the boot ID, kernel and one-time entry after every reboot, and compare the final package, DKMS, boot and output baseline after removal.

## Workload protocol

Use the same machine, firmware, application and driver builds, input hashes, sample durations, output, sink and buffering across kernels.
Record the current hardware mode, temperature, clock policy, power state and background load.
Interleave boot batches where possible and preserve run order so shifts with heat or boot can be seen.
Use at least five accepted runs per kernel per workload and keep each observation, the median and a stated spread.

| Workload | Counter and control |
|---|---|
| PipeWire playback | Keep the audio fixture, sink, rate, quantum and load identical and read back the active graph settings. Record beginning and end values for the same driver and stream identities. Report graph xruns and playback underruns separately when PipeWire exposes distinct counters. `pw-top`'s `ERR` combines xruns and errors. With only that column, report the aggregate and mark standalone underruns unavailable. |
| Video playback | Play a marked full side-by-side fixture with audio and verify the decode route, declaration and `display-sync-active`. Take deltas of mpv's `frame-drop-count`, `decoder-frame-drop-count` and `vo-delayed-frame-count`, with the framedrop policy recorded. Sample signed `avsync` over the clip before EOF. Give its trend or start-to-end change and the largest absolute observation. mpv estimates the delayed count and measures A/V sync within the player. |
| Stereo presentation | Draw a declared full side-by-side surface with a distinct marker in each eye on the selected output at its current mode. Request `wp_presentation.feedback` before each measured commit and keep the commit ID, predetermined deadline in the advertised `clock_id`, outcome, output, presentation timestamp, sequence and flags. Report `discarded` and late `presented` counts separately. Show slow submissions and pending or missing feedback separately. Tie cadence to the measured refresh and the workload's submission schedule. Compositor feedback measures presentation of the surface update. Physical panel timing needs separate instrumentation. |
| Scheduler | Match cyclictest's policy, priorities, affinities, timer interval and duration under the same background load. Record per-thread histograms, overflows and observed maxima. `--default-system` keeps the existing power-management behaviour. Wake-up latency covers the timed CPU thread. |
| CPU inference | Pin the model, input, runtime, thread count and warm-up. Time individual warmed calls with a monotonic clock and record percentiles. Count completed inferences per elapsed second separately at a stated batch size and concurrency. Report first-call latency separately if measured. |
| Sensor or control loop | Define the sensor timestamp, the end of the decision or actuator response, the deadline and its denominator. Record the real sensor and actuator chain. If that equipment is absent, mark the workload unmeasured. |

### Reading the counters

On PipeWire 1.6.9, collect `pw-profiler -J` across a steady window and stop it with SIGINT to close the JSON array.
Match each cycle to the playback driver and stream, and require the active driver clock's rate and duration to match the test.
The driver's and follower's `xrun_count` give separate graph counters.
For an ALSA playback driver, the clock record's `xrun` is the cumulative missing frame count from underrun recovery.
Report its delta and the number of observed positive changes separately. Several recoveries between samples can make the latter a lower bound.
Keep the rate and quantum overrides scoped to the process group and restore the values read at entry, including zero.
[PipeWire 1.6.9 profiler output](https://github.com/PipeWire/pipewire/blob/1.6.9/src/tools/pw-profiler.c), [PipeWire's ALSA recovery](https://github.com/PipeWire/pipewire/blob/1.6.9/spa/plugins/alsa/alsa-pcm.c).

With a single fixed-refresh output, set a presentation schedule before starting the measured commits.
Anchor it to a warm-up `presented` timestamp, use the output's advertised period, and submit one update every two refreshes at a fixed lead time.
During a pilot, choose a lead that lets the compositor reach the intended refresh, then keep it fixed for both flavours.
Count a presentation as late when its reported timestamp falls more than half a refresh past the intended tick. Keep the timestamps so the tolerance can be reviewed.

[PipeWire `pw-top` manual](https://manpages.debian.org/testing/pipewire-bin/pw-top.1.en.html), [mpv command interface](https://mpv.io/manual/stable/#properties), [Wayland presentation protocol](https://gitlab.freedesktop.org/wayland/wayland-protocols/-/blob/main/stable/presentation-time/presentation-time.xml), [cyclictest manual](https://manpages.debian.org/testing/rt-tests/cyclictest.8.en.html).

A finite run gives an observed maximum.
A hard real-time bound requires evidence that covers the whole pipeline and all conditions in the claim.
Keep every flavour's config because RT versus v3 changes the ISA target and other options along with preemption.
The result informs the edition's optional kernel choice and leaves its boot default alone.
[Kernel PREEMPT_RT theory](https://docs.kernel.org/core-api/real-time/theory.html), [ROS 2 real-time design](https://design.ros2.org/articles/realtime_background.html), [GStreamer latency design](https://gstreamer.freedesktop.org/documentation/additional/design/latency.html), [Wang et al. on scheduling real-time GPU tasks](https://arxiv.org/abs/2401.16529).

## Traps seen in build 18

- **Symptom.** The base and RT orig tarballs have different SHA-256 digests.
  **Cause.** The top-level directory and `SOURCE.edition.json` carry flavour-specific names.
  **Fix.** Verify each original digest, then compare normalized member contents and ordered patch hashes.
  **How found.** Only `SOURCE.edition.json` differed across 96,147 regular files or symlinks, and both records carried the same 241 ordered patches.
- **Symptom.** The published RT image contains no `i915.ko`.
  **Cause.** The retained i915 Kconfig requires `!PREEMPT_RT`.
  **Fix.** Keep a working boot entry for machines that require i915. Verify hardware support before treating the presence of `xe.ko` as a fallback.
  **How found.** The signed package's module list and final config agreed with the shipped i915 Kconfig.
- **Symptom.** An NVIDIA DKMS package contains `IGNORE_PREEMPT_RT_PRESENCE=1`.
  **Cause.** This argument bypasses NVIDIA's RT build check. The build and runtime checks have separate evidence.
  **Fix.** Read the matching build proof, check signed outputs and vermagic, and qualify on the affected hardware before claiming runtime support.
  **How found.** The round's two NVIDIA DKMS archives carried the argument. The kernel build's six-module qualification covered the open package, and the AMD bench had neither NVIDIA package installed.
- **Symptom.** `GRUB_DEFAULT=0` looks unchanged when comparing different sets of images.
  **Cause.** Zero selects the first generated entry. The image list controls what it boots.
  **Fix.** Read the kernel from the entry and check the ordering with the candidate release. Verify again after installation, before a one-time reboot.
  **How found.** The installed GRUB generator used `version_sort -r`, backed by `sort -V`. That sort kept `7.3.4-stereo3d18-v3` first with the build 18 RT release added to the input list.
- **Symptom.** The profiler reader fails on `{ } ]`, or reports a combined count as underruns.
  **Cause.** `pw-profiler -J` writes a JSON array with an empty final object. Its ALSA clock and graph driver report different quantities.
  **Fix.** Read the closed array, skip the empty object and keep the driver and follower counters separate from the driver's cumulative missing frames.
  **How found.** A pilot's raw first and last lines showed the array framing. The tagged profiler and ALSA recovery sources identified the fields.
- **Symptom.** The declared video subsurface gets `presented` events with sequence zero and without `sync_output`.
  **Cause.** The measured KWin subsurface path omitted the output and sequence identifiers while still supplying timestamps and a refresh period.
  **Fix.** Use the presentation clock and a scheduled timestamp deadline. Make the output association only when the compositor has exactly one advertised output and its mode matches the baseline, or when feedback explicitly identifies the output.
  **How found.** The v3 pilot returned sequence zero, flags 7 and a 16,665,277 ns refresh on a compositor with one active panel. A 12 ms lead put all 90 updates at least one refresh late. A 26 ms lead put all 90 inside the timestamp tolerance under the pilot load.
- **Symptom.** mpv reports `sbs2l` in its input property even though the fixture is two full-width eyes.
  **Cause.** The application's input mode label and the renderer's declared layout describe different points in the pipeline.
  **Fix.** Check the independent source dimensions and mark, the actual rendered frame dimensions and the compositor declaration. Record the renderer and display-sync state with each sample.
  **How found.** The marked 960×270 fixture had square samples in FFprobe. The mpv renderer logged the same coded size and `stereo=sbsl`, and the Wayland trace showed `set_content(3)` on the video surface.
- **Symptom.** A run passes a cool-start gate, but its first workload sample is much hotter.
  **Cause.** Querying the compositor after the gate starts helper processes and wakes the CPU.
  **Fix.** Check the output first, then collect the cooled start record. Keep subsequent temperature samples and the maximum for the row.
  **How found.** The 62 °C gate passed in a rehearsal, then post-query readings reached 71.75 °C. The rehearsal was excluded.
- **Symptom.** A stopped workload appears to have succeeded through `kde-inhibit`.
  **Cause.** The inhibitor's exit value did not propagate the child runner's failure.
  **Fix.** In the inhibited process, record the worker's actual status. Require it and the completed workload receipts before a boot transition.
  **How found.** A terminated worker left the wrapper with status zero. A wrong-kernel trial proved the explicit child-status check rejects the mismatch.
