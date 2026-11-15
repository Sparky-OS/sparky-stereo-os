# A service that must not retry for ever

**For service maintainers:** stop a persistent startup failure while retaining the vendor's module repair and later USB activation.
Written 2026-11-14 from ORDER 569's real-systemd and umockdev fixture proof.

## Working recipe

1.
   Read the unit and activation rules from the actual package; record its version and ownership.
   Keep a hand-installed vendor service: no removal, masking or in-place rewriting.
2.
   Read the failed invocation and kernel reason.
   A missing module or rejected signing key cannot be repaired by five-second retries.
   Preserve existing startup steps, including a vendor's DKMS repair path.
3.
   Use an edition-owned drop-in.
   DisplayLink's `Restart=on-abnormal` stops on a failed startup or reported exit error while retaining restart on abnormal signals, timeouts or watchdogs.
   Keep the vendor's USB activation.
4.
   Store the actual failed invocation in the one problems engine, with clear cause and next step in every required language.
   Clear its key after a successful start.
   Do not offer automatic restart as a repair for a key or module that must first be repaired.
5.
   Prove the old retry, the new stop and later activation under real systemd in a throwaway container.
   A unit parser does not prove restart behaviour.

## DisplayLink example

Synaptics' Ubuntu `displaylink-driver` 6.4.0-22 owns the service, with `Restart=always` and `RestartSec=5`.
Its pre-step tries `modprobe evdi`, then DKMS installation and another load.
USB rules invoke `udev.sh`; its USB-add path starts the service when vendor `17e9` is present.
Keep these files byte for byte, and inspect newer vendor releases before assuming the same layout.

The hardware package's drop-in selects `Restart=on-abnormal` and adds a status helper.
`ExecStopPost` receives `SERVICE_RESULT`, `EXIT_CODE`, `EXIT_STATUS` and `INVOCATION_ID`.
The helper syncs the journal, reads that invocation and passes its output to the shared engine.
`ExecStartPost` clears the same key.
See [a problem that says its cause](problems-cause-not-retry.md).

Avoid a duplicate generic failed-service record.
Its hook is a named drop-in; a same-named `/dev/null` link for this unit suppresses that hook.
It does not mask the vendor service.
An empty `OnFailure=` in a different drop-in does not reliably remove the dependency the hook added.

## Proof without a physical DisplayLink device

Run the hardware recipe's `tests/displaylink-systemd.py` only as root in a disposable container with systemd as PID 1, journald, the system bus, umockdev and the published problems engine.
Arguments are the extracted vendor package, hardware recipe and evidence directory.
Disable core dumps and pass no host devices or session.
A fixture daemon occupies the vendor binary's path; fixture module and DKMS commands select failure or success.
No proprietary daemon or physical module is executed.

The old unit retries at least three times in twelve seconds.
With the drop-in, one pre-step attempt fails and the unit stays failed with `NRestarts=0` for twelve seconds.
One problem contains the actual module error.
After the fixture module becomes available, umockdev supplies a later USB add to the unchanged vendor script; the service starts and the problem clears.
The test checks that the vendor unit bytes stayed equal.
This proves activation plumbing, not a physical display or Secure Boot load.

## Traps: symptom, cause, fix and how found

* **A failed pre-step retries forever.** `Restart=always` includes startup failure.
  A rejected evdi signing key needs repair/enrolment.
  The restart counter and `ExecStartPre` journal identify why retries cannot help.
* **A guard prevents the vendor's module repair.** Placing `ExecCondition=modprobe evdi` before its current pre-step skips the DKMS path.
  Read the real unit first; preserve that path and change the restart policy instead.
  Comparing the package versions exposes the difference.
* **`reset-failed` fails on a stopped, unloaded fixture.** systemd may have garbage-collected it.
  Stop and start already reset this test's retry state; do not require a reset of a nonexistent failed unit.
  Read stderr and state to distinguish a fixture problem from restart behaviour.
* **A kept error disappears before the next successful start.** A record's `unit` field ties its lifetime to failed state.
  Omit it when the helper owns clear-on-success; clear the key explicitly.
  The engine collector's output and record fields identify the premature clear.
* **Language checks pass without a language review.** Catalogue and placeholder parity establish structure only.
  Report the missing independent/native review instead of calling it translation-quality proof.
