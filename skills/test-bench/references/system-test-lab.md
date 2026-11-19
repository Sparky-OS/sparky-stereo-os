# The system test lab: the matrix, a row that is red on stock, the traps

**Check freshness first.**
Written on 2026-11-19 (ORDER 22, milestone 1) against the published tree r1117a (kernel 7.3.4-stereo3d18, Stereo KWin 6.7.4-2+stereo3d58) and the staged sparky-stereo-audio 0.1.0.
The build tree's `sparky-os/tests/lab/` holds the runner; the contributor page is [the system test lab](../../../docs/guides/system-test-lab.en.md).

## Working recipe

1. `rig/prepare.sh WORK SKILLS STAGE TREE` once: the guest image, the two kernels (the edition's from the tree, Debian's unsigned binary and modules), the SDL under test, the audio images (stock and ours), the compositor images and their roots.
2. `lab.py --list --var work=WORK --var skills=SKILLS` shows each row and what it still needs.
3. `lab.py --var ... --evidence DIR [--only ROW] [--kind K]` runs the rows and writes `report.md` and `report.json`. Exit 1 when a row fails, 2 for a bad matrix, 3 with `--strict` for an unnamed skip.
4. `python3 -I tests/test_lab.py` is the runner's own test (a planted failing row, a row green on stock, a row that cannot run, the Docker flags against a fake docker).

## The matrix

`matrix.json` has `{"prefix": "lab22", "rows": [...]}`. A row: `id` (a-z, 0-9, dash), `kind` (screens, audio, input, weak), `title`, `needs` (`docker`, `image:NAME`, `path:P`, `kvm`), `image`, `mounts` (`[src, dst, "rw"]`, read only by default), `limits` (`cpus`, `memory`), `devices`, `user` (`host` is the caller's uid), `sides.ours` and `sides.stock` (each `cmd`, optionally its own `image`, `mounts`, `env`, `versions`), `expect` (default ours pass, stock fail), `proves`, `not_proven`. `{work}`, `{skills}`, `{lab}` and `{tree}` in any string come from `--var` or the runner. A `weak` row names a `base` row and its own `limits`. A row with `skip` is a named skip (`tracks` says whose it is).
A command's exit status is its answer: 0 holds, 1 does not, 77 cannot run (`SKIP: reason` on stdout). Green runs first; the red side runs only after a green one. The container is `lab22-ROW-SIDE`, `--pull=never --ulimit core=0 --network none`, removed by its literal name; `/evidence` is the side's own folder.

## Writing a row so that it is red on stock

- Put the one difference in the component, never in the harness: the screens rows boot the same edition kernel and change only the compositor's root; the input row changes the kernel and SDL together because both carry the feature; the audio rows change only the package.
- Compute the expectation outside the program under test (edid-decode, the HID report descriptor, the fixture's own rate table).
- When the stock side cannot even start (Debian's kernel has no VKMS), say so as a skipped side, never as a red.
- A check that cannot fail is not a row: the runner fails a row that is green on stock.

## Traps met (symptom, cause, fix, how found)

- **A guest lists no 3D mode and `Virtual-1` is its only connector.** Cause: BusyBox `insmod` ignores the kernel command line's module parameters, so `vkms.create_default_dev=0` was not applied and the default device became card0. Fix: pass the parameter to `insmod` (`mkguest.py --modarg vkms=create_default_dev=0`). Found by: `ls /sys/class/drm` printed by the guest and the connector name.
- **The stock row's guest says "could not create the device".** Cause: the stock side was given Debian's kernel, which has no vkms module. Fix: the screens rows use the edition's kernel on both sides. Found by: the module list printed by the assembler.
- **Debian's kernel image package is a 1.9 KB stub.** The kernel is in `linux-binary-unsigned-VERSION` and the modules in `linux-modules-VERSION`.
- **`docker run ... sh /lab/x.sh` exits 1 with no output.** Cause: `set -e` and `grep -c` printing 0 (exit 1). Fix: `|| true`. Found by: the evidence folder had only the first file.
- **The audio rig's session exits at once.** Cause: `/run/user/1001` does not exist in a fresh container. Fix: `rows/as-rig.sh` makes it as root before `setpriv`. Found by: the PipeWire log in `/tmp`.
- **A hat count of 1 for a 4-hat HID device.** Cause: hid-input maps every hat switch onto ABS_HAT0X/Y, on Debian's kernel and on ours. Not a lab fault: the row prints hats and does not judge them.
- **`kscreen-doctor` cannot switch anaglyph on.** `kwinoutputconfig.json` with `"anaglyph": true` is kept and not applied at start; needs a libkscreen client calling `KScreen::Output::setAnaglyph`. The row is a named gap.
- **Frames of 3D modes are not single pictures.** A frame-packing scanout is 1920x2205; judge each eye from its region (analyze-kwin.py does).
