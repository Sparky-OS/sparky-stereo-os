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

These controls have unit-test evidence. A completed container dry run and any actual bench results must be stated separately in the hand-back.
