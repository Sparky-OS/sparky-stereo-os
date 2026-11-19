# The system test lab: one command, one report

**For contributors who want to know whether a change still works on the whole system, not only in its own package.**

The lab runs checks that no 3D television, sound card, controller or desktop of yours is needed for.
Everything happens in throwaway containers and small virtual machines, and each check is run twice: once on the edition's components (it must hold) and once on the stock ones, Debian's or upstream's (it must not hold).
A check that holds on both proves nothing, so the lab turns the run red when it sees one.

## Run it

You need Docker, a solid-state disk with 15 GiB free for the scratch folder, and a clone of the edition's build tree and of this repository.
The lab never uses your default Docker: set `DOCKER_HOST` to the Docker you want it to use, or it skips every row and says why.

1. Prepare the images, the two kernels and the two compositor roots once: `sparky-os/tests/lab/rig/prepare.sh WORK SKILLS_CLONE STAGE_AUDIO REPO_TREE`. It runs apt only inside containers, over HTTPS, and loads no module on your machine.
2. See the rows and what each needs: `python3 -I sparky-os/tests/lab/lab.py --list --var work=WORK --var skills=SKILLS_CLONE`.
3. Run them: `python3 -I sparky-os/tests/lab/lab.py --var work=WORK --var skills=SKILLS_CLONE --evidence DIR`.
   `--only ROW` runs one row, `--kind screens|audio|input|weak` one kind, `--tree DIR` names the published tree the run is against.

A full run takes a few minutes.
The exit status is 0 when no row failed, 1 when a row failed, 2 for a bad matrix or option, and 3 (only with `--strict`) for a row that could not run and is not a named skip.

## Read the report

`report.md` and `report.json` are in the evidence folder, with one folder per row and side holding what that run printed and wrote.
The table says, for every row:

- **PASS**: the check held on ours and did not hold on stock.
- **FAIL**: it did not hold on ours (a fault, named with its row), or it held on stock where it must be red, or the check itself broke.
- **SKIPPED**: the row could not run, and the reason is in the last column. A skipped row is never counted as a pass. Some are named skips: checks that belong to another piece of work and are listed so they are not forgotten.

The first lines name the published tree the run was against, and each side's `versions.txt` lists the package versions it ran with.
A time is reported, never a condition: a slow row that holds is a pass.
Rows under a limit of 2 processors and 2 GiB (kind `weak`) say that the check still works under the limit and how long it took.

## Add a row

A row is a few lines of data in `matrix.json`: an id, a kind, the image and mounts, and two commands, one for `ours` and one for `stock`.
A command's exit status is its answer: 0 means the check holds, 1 means it does not, 77 means it cannot run (print `SKIP: the reason` first).
Write the check so that it can fail on stock for the reason you are proving:

1. Say what the stock component does instead, in plain words.
2. Compute the expectation from the standard or the fixture (an EDID read by `edid-decode`, a report descriptor, a table of rates), never from the program under test.
3. Compare decoded RGB arrays for pictures and state the shift in pixels with its sign; never call a pair flat unless the count of differing RGB pixels is 0.
4. Run both sides and read both outputs before you trust the row.

A screen row proves the output the EDID asks for, never a program's own output mode.
Nothing in a row may touch a real display, television, sound device, input device, Bluetooth adapter or session of your machine, and anything that discovers or pairs devices runs with `--network none`.

## What the lab does not prove

The lab proves what the compositor, the kernel, the sound system and SDL do with virtual devices.
It does not prove a real television, a real sound card, a real controller or a real colourimeter, and it reports no timing as a result.
The rows that are skipped, and what each would need, are in the report.
