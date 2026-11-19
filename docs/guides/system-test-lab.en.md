# The system test lab: one command, one report

**For contributors who want to know whether a change still works on the whole system, not only in its own package.**

The lab runs checks that no 3D television, sound card, controller or desktop of yours is needed for.
Everything happens in throwaway containers and small virtual machines, and each check is run twice: once on the edition's components (it must hold) and once on the stock ones, Debian's or upstream's (it must not hold).
A check that holds on both proves nothing, so the lab turns the run red when it sees one.

## Run it

You need Docker, a solid-state disk with 8 GiB free for the scratch folder (the images take about 6 GiB more in Docker), `/dev/kvm` for the rows that run a small virtual machine, and a clone of the edition's build tree and of this repository.
The lab never uses your default Docker: set `DOCKER_HOST` to the Docker you want it to use, or it skips every row and says why.
Run it from the build tree's root; the paths below start there.

1. Prepare the images, the two kernels and the two compositor roots once: `sparky-os/tests/lab/rig/prepare.sh WORK SKILLS_CLONE STAGE_AUDIO REPO_TREE [PLASMA_PA_DEB]`.
   `WORK` is an empty scratch folder, `SKILLS_CLONE` your clone of this repository, `REPO_TREE` the published tree to test (a folder with `pool` and `dists`).
   `STAGE_AUDIO` is a folder with the `sparky-stereo-audio` package and a `Packages` file (`dpkg-scanpackages` makes one), until a published tree carries the package; `PLASMA_PA_DEB` is the edition's `plasma-pa` package with the Sound Quality page, and without it that one row is skipped and says so.
   It runs apt only inside containers, over HTTPS, loads no module on your machine, and takes about eight minutes the first time; run again, it skips what exists.
2. See the rows and what each needs: `python3 -I sparky-os/tests/lab/lab.py --list --var work=WORK --var skills=SKILLS_CLONE`.
3. Run them: `python3 -I sparky-os/tests/lab/lab.py --var work=WORK --var skills=SKILLS_CLONE --tree REPO_TREE --evidence DIR`.
   `--only ROW` runs one row, `--kind screens|audio|input|weak` one kind.
   `--tree` names the published tree the report says it ran against; give it the tree you gave `prepare.sh`, and for a newer round make a new `WORK` as the `README.md` next to `lab.py` says (the report tells you when the two trees differ).

A full run takes about half an hour; one row takes one to four minutes.
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

## The rows today

- **Screens** (a small virtual machine with a virtual HDMI output and the EDID of a 3D television, of a plain HDMI sink, or of a television that also takes 1920x1080 at 120 Hz): the 3D modes the EDID declares and the pair shown in each; one view on a plain monitor, also by an EDID with no 3D at all; an anaglyph output set from the command line; 16 bit deep colour counted level by level in each eye; the eye order of every mode, with the output's swap eyes setting off and on.
- **Audio** (a private sound system with fake sound cards): the graph following 44.1 and 96 kHz, a 16 bit only device, what the engine reads from a card, a display's audio blocks and a headphone jack, and the Sound Quality page (devices, a chosen rate reaching the running graph, a refused one said).
- **Input** (a virtual game controller with 128 buttons): seen whole by the kernel and by SDL.
- **Weak** (the same rows under 2 processors and 2 GiB): they still work.

Some rows are named skips, for work that belongs to someone else or that cannot be made red on stock; the report names whose.

## Add a row

A row is a few lines of data in `matrix.json`: an id, a kind, the image and mounts, and two commands, one for `ours` and one for `stock`.
A command's exit status is its answer: 0 means the check holds, 1 means it does not, 77 means it cannot run (print `SKIP: the reason` first).
Write the check so that it can fail on stock for the reason you are proving:

1. Say what the stock component does instead, in plain words.
2. Compute the expectation from the standard or the fixture (an EDID read by `edid-decode`, a report descriptor, a table of rates), never from the program under test.
3. Compare decoded RGB arrays for pictures and state the shift in pixels with its sign; never call a pair flat unless the count of differing RGB pixels is 0.
4. Run both sides and read both outputs before you trust the row.

A screen row proves the output the EDID asks for, never a program's own output mode.
The screens rows share one small guest; a row picks what it does there with two lines of data (`env.LAB_PHASE` and `env.LAB_EDID`) and the layouts or modes it names, so a new output feature usually needs a line in `matrix.json` and, at most, a new judge in `rows/` with a test in `tests/test_judges.py` that plants the loss it looks for.
Nothing in a row may touch a real display, television, sound device, input device, Bluetooth adapter or session of your machine, and anything that discovers or pairs devices runs with `--network none`.

## What the lab does not prove

The lab proves what the compositor, the kernel, the sound system and SDL do with virtual devices.
It does not prove a real television, a real sound card, a real controller or a real colourimeter, and it reports no timing as a result.
The 16 bit levels it counts are those of the compositor's output buffer, and the eye order rows compare the frame the compositor scans out with a model made from the same two pictures; neither says what a particular display shows.
The rows that are skipped, and what each would need, are in the report.
