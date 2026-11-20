# The system test lab: the matrix, a row that is red on stock, the traps

A core limit of exactly 1 suppresses the piped core helper; a zero limit does not, as the [crash trap](../../stereo-proof-rig/SKILL.md#traps-that-fooled-us) explains.

**Check freshness first.**
Written on 2026-11-19 (ORDER 22, milestone 1) and extended on 2026-11-19 (continuation 1, the next rows), against the published tree r1117a (kernel 7.3.4-stereo3d18, Stereo KWin 6.7.4-2+stereo3d58, libkscreen 6.7.4-1+stereo3d12), the staged sparky-stereo-audio 0.1.0 and the staged plasma-pa 6.7.4-1+stereo3d3 (the Sound Quality page).
The build tree's `sparky-os/tests/lab/` holds the runner; the contributor page is [the system test lab](../../../docs/guides/system-test-lab.en.md).

## Working recipe

1. `rig/prepare.sh WORK SKILLS STAGE_AUDIO TREE [PLASMA_PA_DEB]` once, from nothing: the guest image, the two kernels (the edition's from the tree, Debian's unsigned binary and modules), the SDL under test, the audio images (stock and ours), the compositor images and their roots, and with the plasma-pa package the page images. About 8 minutes, 4 GiB in WORK and about 6 GiB of images in Docker. It refuses a WORK made from another round of the tree and says what to remove.
2. `lab.py --list --var work=WORK --var skills=SKILLS` shows each row and what it still needs.
3. `lab.py --var ... --evidence DIR [--tree TREE] [--only ROW] [--kind K]` runs the rows and writes `report.md` and `report.json`. Exit 1 when a row fails, 2 for a bad matrix, 3 with `--strict` for an unnamed skip. A full run is about 30 minutes. Run one guest at a time: each takes 4 processors.
4. `python3 -I tests/test_lab.py` is the runner's own test (a planted failing row, a row green on stock, a row that cannot run, the Docker flags against a fake docker, the shipped matrix) and `python3 -I tests/test_judges.py` the judges' (a planted loss for each).

## The matrix

`matrix.json` has `{"prefix": "lab22", "rows": [...]}`. A row: `id` (a-z, 0-9, dash), `kind` (screens, audio, input, weak), `title`, `needs` (`docker`, `image:NAME`, `path:P`, `kvm`), `image`, `mounts` (`[src, dst, "rw"]`, read only by default), `limits` (`cpus`, `memory`), `devices`, `user` (`host` is the caller's uid), `env`, `sides.ours` and `sides.stock` (each `cmd`, optionally its own `image`, `mounts`, `env`, `versions`), `expect` (default ours pass, stock fail), `proves`, `not_proven`. `{work}`, `{skills}`, `{lab}` and `{tree}` in any string come from `--var` or the runner. A `weak` row names a `base` row and its own `limits`. A row with `skip` is a named skip (`tracks` says whose it is).
A command's exit status is its answer: 0 holds, 1 does not, 77 cannot run (`SKIP: reason` on stdout). Green runs first; the red side runs only after a green one. The container is `lab22-ROW-SIDE`, `--pull=never --ulimit core=1 --network none`, removed by its literal name; `/evidence` is the side's own folder.

The screens guest (`rows/screens_guest.sh`) has four phases, picked by `env.LAB_PHASE`, and three EDIDs, picked by `env.LAB_EDID`; the arguments of the command are the layouts or tags the phase shoots:

| Phase | Steps in the guest | Judge | Arguments |
|---|---|---|---|
| `kwin` (default) | the bench's `kwin-steps.sh`, filtered | `screens_judge.py` with `analyze-kwin.py` | `fp tab sbs-half sbs-full 2d`, and `edid-no-3d`, `no-3d-modes` |
| `deep` | `rig/guest/deep-steps.sh`: the ramp client in 16, 10 and 8 bit shm and the 16 bit EGL pair, grabbed at 16 bit | `deep_judge.py` | `2d sbs-half` |
| `eyeorder` | `rig/guest/eyeorder-steps.sh`: the bench's eye order matrix | `eyeorder_judge.py` with `analyze-eyeorder.py` | the bench's tags: `hdmi-sbs-half hdmi-tab hdmi-sbs-full hdmi-fp twin-sbs-half twin-tab anaglyph-modern anaglyph-crt rows-left rows-right columns-left columns-right checkerboard-left checkerboard-right fs-left fs-right` |
| `anaglyph` | `rig/guest/anaglyph-steps.sh`: four ways to ask for anaglyph | `anaglyph_judge.py` | `doctor` (the other three are printed for the diagnosis) |

EDIDs: `stereo-test` (the bench's 3D television), `stereo-test-2d` (the same with the HDMI 3D fields removed by `edid/make-2d-edid.py`), `stereo-eyeorder` (the 3D television plus 1920x1080 at 120 Hz, `rig/guest/make-eyeorder-edid.py`). `edid-decode --check` of the one in use is in each side's evidence (`edid-decode.txt`).

The Sound Quality page row runs the page's own QML type in the page rig's harness (`rows/page_row.sh`, images `lab22-page-*:1` made by `rig/build-page.sh` from the audio images plus plasma-pa and `qml-qt6`), and `rows/page_judge.py` judges it against the fake devices' table.

## Writing a row so that it is red on stock

- Put the one difference in the component, never in the harness: the screens rows boot the same edition kernel and change only the compositor's root; the input row changes the kernel and SDL together because both carry the feature; the audio rows change only the package.
- Compute the expectation outside the program under test (edid-decode, the HID report descriptor, the fixture's own rate table, the Dubois matrices, the ramp the client drew).
- When the stock side cannot even start (Debian's kernel has no VKMS), say so as a skipped side, never as a red.
- A check that cannot fail is not a row: the runner fails a row that is green on stock. Before a row goes in, run the stock side by hand and read why it fails: the deep colour row is red because stock scans out 8 bits (a measured difference); the eye order rows are red because stock Mesa has no `EGL_EXT_multiview_window`, so the declared client cannot run (the same reason as the first milestone's screens rows).
- A row whose first measurement shows stock equal to ours is not a row. Say what was measured and leave it out, or keep it as a named skip with the numbers.
- Judge on decoded values (RGB arrays, 16 bit samples), count the differing pixels, state shifts with their sign, and print what the judge saw beside its verdict: the evidence folder is what a reviewer reads.
- Give every judge a test that plants the loss it looks for (`tests/test_judges.py`): an 8 bit scanout, a leaking eye, a missing swap, the left view alone where the mix is due.

## What the rows measured (r1117a)

| Row | Ours | Stock |
|---|---|---|
| `screens-deep-colour` | scans out AB48; a 16 bit shm ramp of 256 values keeps 256 levels in the plain mode and in each eye of side by side half; the 16 bit EGL pair keeps 256 levels in each eye and none of the other eye's; a 10 bit client shows 4 and an 8 bit client 1 | scans out AB24; the same 16 bit client shows 1 level (both compositors advertise AB48 and XB48 shm formats, so the difference is in the output buffer, not in the format list) |
| `screens-plain-monitor-2d-edid` | the EDID has no `3D present`; 0 3D modes listed; one view of the declared client | no client |
| `screens-anaglyph` | `kscreen-doctor output.NAME.anaglyph.enable`, then `output.NAME.mode.ID` of the `virtual-3D:5` mode: the 3D area is (164, 215, 0), the Dubois mix of red and green | "Unable to parse arguments", exit 0 |
| `screens-eyeorder-*` | every mode, swap off and on, equals the model (all pixels exact, the other swap's model matching none of the differing pixels); the mode list has no right eye first twin | the declared client cannot run |
| `audio-sound-quality-page` | the page's `SoundFormats` lists the fixture's devices, a chosen 96 kHz reaches PipeWire's `clock.rate`, 96 kHz on the 48 kHz only device is refused and said | `SoundFormats is not a type` |

## Traps met (symptom, cause, fix, how found)

- **A guest lists no 3D mode and `Virtual-1` is its only connector.** Cause: BusyBox `insmod` ignores the kernel command line's module parameters, so `vkms.create_default_dev=0` was not applied and the default device became card0. Fix: pass the parameter to `insmod` (`mkguest.py --modarg vkms=create_default_dev=0`). Found by: `ls /sys/class/drm` printed by the guest and the connector name.
- **The stock row's guest says "could not create the device".** Cause: the stock side was given Debian's kernel, which has no vkms module. Fix: the screens rows use the edition's kernel on both sides. Found by: the module list printed by the assembler.
- **Debian's kernel image package is a 1.9 KB stub.** The kernel is in `linux-binary-unsigned-VERSION` and the modules in `linux-modules-VERSION`.
- **`docker run ... sh /lab/x.sh` exits 1 with no output.** Cause: `set -e` and `grep -c` printing 0 (exit 1). Fix: `|| true`. Found by: the evidence folder had only the first file.
- **The audio rig's session exits at once.** Cause: `/run/user/1001` does not exist in a fresh container. Fix: `rows/as-rig.sh` makes it as root before `setpriv`. Found by: the PipeWire log in `/tmp`.
- **A hat count of 1 for a 4-hat HID device.** Cause: hid-input maps every hat switch onto ABS_HAT0X/Y, on Debian's kernel and on ours. Not a lab fault: the row prints hats and does not judge them.
- **Frames of 3D modes are not single pictures.** A frame-packing scanout is 1920x2205; judge each eye from its region (analyze-kwin.py does).
- **A 16 bit ramp counts as 1 level in the grab.** Symptom: the deep readback shows 1 distinct value in a ramp that the client drew with 256, on a compositor that scans out AB48. Cause: `drm-grab` writes an 8 bit PPM (the high bits of each channel). Fix: `DRM_GRAB_DEEP=1` writes a 16 bit PPM (maxval 65535) and `deep_judge.py` reads it with `array('H')`; Pillow would turn it back into 8 bits. Found by: counting the same frame both ways.
- **Both compositors list AB48 and XB48 as shm formats, yet only one keeps the bits.** Symptom: the 16 bit client "draws" on stock and the frame has 1 level. Cause: stock KWin composes into an AB24 scanout buffer. Fix: none to make, it is the difference the row is for; judge the output, not the list of formats. Found by: the `fb ... format AB24` line of `drm-grab`.
- **`drm-grab CARD OUT HDMI-A-1` prints its usage.** Symptom: every grab of the eye order steps fails, the frames never become equal, each grab waits its 20 tries, a run takes 5 minutes and the analysis says "no reference". Cause: the bench's `eyeorder/steps.sh` passes a connector name; `src/drm-grab.c` takes two arguments. Fix: the lab's steps pass two. Found by: the `grab-ref.txt` file holding the usage line.
- **`analyze-eyeorder.py` needs NumPy.** Symptom: "the analysis wrote no summary". Cause: the guest image had Pillow only. Fix: `python3-numpy` in the guest image (`prepare.sh`). Found by: `analyze.err`.
- **The matrix's `-right` tags are gone.** Symptom: "never set or never grabbed" for `rows-right`, `columns-right`, `checkerboard-right`, `fs-right`. Cause: Stereo KWin since +stereo3d48 lists every packing left eye first; the swap flips the order. Fix: `eyeorder_judge.py` holds a `-right` tag when the mode list has no such twin (the analysis prints "is not listed"). Found by: `doctor-second.txt`, which has no `virtual-3D:8`.
- **A stored `"anaglyph": true` changes nothing.** Symptom: after KWin starts with it, the 3D area is still red (the left view alone). Cause: `anaglyph` and `otherStereoFormats` on an output are toggles that make the output offer the anaglyph (and other) modes; the picture is the output's current mode, and only a mode with the anaglyph layout (`virtual-3D:5` modern, `6` CRT) is an anaglyph. Fix: choose the mode, from the command line `kscreen-doctor output.NAME.anaglyph.enable` then `output.NAME.mode.ID`, or store both the toggle and the mode (flags 0x20000 + 0x200 = 131584). Found by: the four variants of `anaglyph-steps.sh`.
- **`kscreen-doctor --help` does not list `anaglyph`, `otherStereoFormats`, `swapEyes` and the other stereo verbs.** They are in `doctor.cpp` (libkscreen +stereo3d12) and work. The first milestone read the help and wrote that the verb did not exist. Read `doctor.cpp` of the version, or run the verb and read the result.
- **Stock `kscreen-doctor` exits 0 on a line it cannot parse.** It prints "Unable to parse arguments" and returns 0, so an exit status alone proves nothing there. Judge what the compositor then shows.
- **qml6 prints "X is not a type" without the word "error".** The page rig's `qml-steps.sh` filters on `rror|Warning` and would show nothing for stock plasma-pa. The page row keeps the raw output and tells "the page is not there" from "the rig did not start".
- **A stock KWin session cannot run the declared client; do not wait for it.** Symptom: the stock side of a guest row takes minutes. Cause: each grab waits for a non-black frame that never comes. Fix: the steps end early when the client process has ended (`kill -0`) and say why.
- **Half float EGL configs do not hold a narrow ramp.** A half float has 2048 values in an octave; 256 values of a 16 bit channel in the band 0x8000 to 0x80ff are 8 of them. The ramp client asks for a fixed point 16 bit config and prints that none exists when only half float does. Mesa 26.1.6 on Wayland has 30 configs with 16 bits, all fixed point.
- **Two guests at once slow both.** Each guest takes 4 processors and the machine is shared: the lab runs rows one after the other, and so should a by-hand run next to it.
