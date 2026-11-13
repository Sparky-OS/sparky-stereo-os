# A long unattended measurement on a laptop

Prepare on the station; the person owns the bench and decides when to start it.
Never connect to a reserved machine merely to prepare its experiment.

1. Pin the complete input tree, seed compiler, container image and offline workload; carry checksums in one folder. Build the image from a named signed HTTPS snapshot and export it. No image pulls or compiler/crate downloads during measurement.
2. Measure a small representative sample on the preparation machine under its CPU limit. Name the scale factor, its uncertainty and the largest repeated subject that fits the time budget. Keep whole builds when final binaries are part of the question. Do not report forecasts as laptop measurements.
3. Use a fixed plan and fresh targets. Write each result under a partial directory. Only after every command and output check succeeds, write its atomic receipt, rename the directory and advance state. Bind version, input checksum, configuration, raw metrics and machine state. Save results before deleting a build tree.
4. Keep a lock, state and detached worker (`nohup` or a user service). Supply start/resume, status and after-step pause commands. After a person reboots, relaunch resumes at the first unfinished whole step. An immediate stop discards only that unfinished step; verify finished receipts before skipping them.
5. Sample free space every five seconds throughout loading, extraction and execution; stop five GiB above the chosen floor. Record CPU temperature, frequency, governor, load and kernel throughout measured commands. Missing sensors or counters stop explicitly. State start/pause temperatures and a cool-down timeout. Record pauses separately because they add to elapsed time.
6. Set `LC_ALL=C` in every tool and accept either decimal mark in numeric reports. Reject incomplete or ambiguous data. Compare every observed difference with the sample's spread; one whole build per form gives size and real compilers, not repeatable whole-build timing.
7. Dry-run every step in a container on a tiny subject. Kill a step after it has written partial metrics, resume, and prove the partial result was not counted and completed steps were not repeated. Inject low-space and high-temperature readings, show rejection/pause before green recovery, and exercise comma-decimal summaries. Keep the red and green evidence.
8. Give the person a page: running time and uncertainty, cores/memory/disk/heat, exact commands, what pause means, where state and results live, and recovery after a stopped step. Keep their desktop, display, power settings and boot state outside the kit.

The Rust compiler experiment's machinery is in the build repository's `tools/rust-lean-experiment`.
Its temperature defaults (62 °C before starting, pause above 90 °C, two hours to cool) are explicit choices for its hot A10 bench, not universal laptop limits.
Rootful Podman and perf capabilities apply only inside that kit's isolated store and containers; they do not justify changing host perf policy or the person's compiler.

- Symptom: a resumed job counts a metrics file from a killed process as a finished round.
  Cause: file existence was used as a completion marker.
  Fix: require the committed whole-step receipt and validate its output hashes; partial directories never enter the summary.
  Found by: receipt fault-injection controls distinguish a metrics-only directory from a complete result and reject later corruption.
- Symptom: a short thermal test intermittently says pause/resume did not happen.
  Cause: the fake engine's run marker and pause-control marker can be written in either order during process launch; an adjacency assertion tested scheduling.
  Fix: assert that pause precedes unpause while allowing the independent launch marker between them, then test real container controls in the full dry run.
  Found by: the retained failing action log `pause, run, unpause`; the corrected control checks the intended order.

- Symptom: a direct version probe names the intended compiler, but perf measures the seed.
  Cause: file-capability perf crosses secure exec; its executable search and stripped library environment differ from the direct call.
  Fix: resolve the intended executable before perf, explicitly re-establish the selected PATH/library path afterwards, and check the measured version output. Reject the earlier samples.
  Found by: comparing the raw measured --version output with the direct probe, then a corrected full compiler/workload sample.
- Symptom: a large stopped target prevents resume at the next-build free-space requirement.
  Cause: checking capacity before reclaiming the disposable unfinished target counts space that resume will immediately retire.
  Fix: after validating the payload under the exclusive worker lock, retire only runtime/work before checking next-build capacity; leave durable results alone and keep the continuous floor guard.
  Found by: the resume-path audit and a control that checks target retirement precedes the space query while accepted results survive.
- Symptom: killing the guard leaves its container running.
  Cause: a detached client can outlive the process supervising it.
  Fix: arrange parent-death termination for the client and a signal-aware container PID 1, forwarding signals so the owned container's descendants end too.
  Found by: an actual SIGKILL guard control and inspection of only the named container; no half-step result was accepted.

The laptop kit's complete small container run exercised every step and kill/pause/resume path; its unit and actual-container fault controls are separate evidence. No laptop performance claim follows from that dry run.

- Symptom: Podman refuses resume after a person reboots, although kit receipts remain.
  Cause: a persistent custom runroot/tmpdir retains an alive file with the prior host boot ID.
  Fix: record the host boot ID and, after a changed boot, retire only the kit’s runroot and engine temporary directory before engine initialization; keep its graph/image store and accepted results. Reject symlinked volatile roots.
  Found by: Podman’s own checkBootID diagnostic and runtime refresh code, then simulated changed-boot and symlink controls. This is not an actual hardware reboot test.
