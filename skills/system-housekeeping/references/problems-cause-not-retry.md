# A problem that says its cause, and offers a repair only where one can work

The engine's default for a failed system service is "Repair starts it again".
That is right for a service that failed for a moment and wrong for one whose cause stays (no swap area, a device that cannot freeze, a missing file): the retry fails the same way, or does something the person did not ask for (it hibernates the computer).
Daniel's rule (memory no-silent-fallbacks, 2026-11-01): when a step cannot do what it is for it says what failed, why and what to do; ORDER 462 applied it to "Try again".

## Recipe

1. Read the cause from the failed attempt itself: the unit's invocation in the journal (`INVOCATION_ID` / `_SYSTEMD_INVOCATION_ID`), then the kernel's lines between its first and last line.
   `MONITOR_INVOCATION_ID`, `MONITOR_UNIT`, `MONITOR_EXIT_STATUS` and `MONITOR_SERVICE_RESULT` reach the engine's handler from systemd (systemd.service(5)).
2. Give the problem its own message (LOCALnn in the package's lang/, ten languages) built from nested messages: `args` are `[["LOCALphrase"], ["LOCALreason", device, error]]`, and `more` holds the what-to-do sentence as `["LOCALfix", args]`.
3. Classify each cause as one that stays or one that can pass.
   Stays: the record has an empty `repair`, the text says "Repair is not offered", and the problem ends when the unit is no longer `failed` (the next attempt that works).
   Can pass or unknown: keep `["systemctl","restart",UNIT]` and say what Repair does ("starts the operation again, which puts the computer to sleep again").
4. Where the failure leaves the unit successful, the handler never runs: add an `ExecStopPost=-/usr/bin/sparky-stereo-problems VERB %n` drop-in, key the record without a `unit` field (so no unit state ends it), and end it from the same verb when a later run worked.
5. Test the engine with journals built from exports (`systemd-journal-remote`, `SPARKY_STEREO_PROBLEMS_JOURNAL`), red on the engine before the change.
   The worked example is `sparky-os/packages/sparky-stereo-problems` 0.2.1 and [power-idle's failed-hibernation.md](../../power-idle/references/failed-hibernation.md).

## Traps met

- Symptom: a problem written for a successful unit disappears at the next `list`.
  Cause: a record with `unit` is finished by the collector as soon as the unit's `ActiveState` is not `failed`.
  Fix: omit `unit`, and clear the key yourself when the next run worked.
- Symptom: a check "the text does not say Repair starts it again" fails although the new text is right.
  Cause: `list` prints every kept problem, and other failed services in the same store say it.
  Fix: read the one record with `text --boot sparky-stereo-problems KEY`.
- Symptom: a German `journalctl -x` shows an English operation name inside a German sentence.
  Cause: nested messages are journal fields in English (see failed-hibernation.md).
  Fix: none in the catalog; say it in the test's name so nobody "fixes" it.
