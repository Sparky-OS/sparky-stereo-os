# More than 80 buttons: EV_BTN, SDL and Wine

Written on 2026-11-06 (ORDER 15, milestone 1). Symptom first, then the recipe, then the traps.

## Why a joystick stops at 80 buttons

Symptom: a throttle, wheel or button box with 128 buttons shows 80 in `evtest`, SDL and Wine, and the last 48 do nothing.
Cause: `hid-input` gives every Button-page usage a key code (`BTN_JOYSTICK` up to `BTN_DEAD`, then `BTN_TRIGGER_HAPPY`) and the codes stop at `KEY_MAX` (0x2ff in Linux 7.3), which is 80 buttons.
Raising `KEY_MAX` moves the wall and grows every bitmap that userspace reads.
Tomasz Pakuła's "Input: New EV_BTN event for generic buttons" (RFC, linux-input and LKML, 2026-01-04) adds event type 6, `EV_BTN`, whose code is the HID button number starting at 1 and whose value is the state.
It has no ceiling at `KEY_MAX` (the series caps a device at `INPUT_MAX_BUTTONS`, 2048), joysticks keep their `EV_KEY` codes beside it, and `EVIOCGBTNCNT` returns the button count.
Others addressed the same wall differently and are not carried: Ivan Gorinov (2025-12-20, 112 codes) and Ricardo Esteves (2026-02-09, `KEY_MAX` to 0x31d).

## Find the newest version of a kernel series

1. The author's own archive is the first stop: `ratatoskr.run/linux-input/author/<Name>` lists every message of a person, newest first, and a thread page carries the whole thread as JSON-LD (replies included).
2. For the raw text of a patch use `lkml.iu.edu/<yymm>.<n>/<number>.html`: lines end in `<br>`, tabs are kept, addresses are masked as `xxxxxxxxx` (put the real domain back).
3. Compare with mainline by reading `include/uapi/linux/input-event-codes.h` from `raw.githubusercontent.com/torvalds/linux/master`.
4. The author's fork branch is not the posted series: Pakuła's `ev-btn` branch was an earlier draft (field `num_buttons` where the posted patches say `button_count`, and no `EVIOCGBTNCNT` commit).

## Carry an input series in the edition's kernel and check it builds, without a full build

1. Make the group `kernel/series/NN-name/` in the build repository: one file per posted patch, headers `From:` (the author), `Date:`, `Subject:`, his message and Signed-off-by untouched, then a bracketed note (link, review state, "drop this group when ..."), our `Assisted-by:` trailer, then `---` and the diff.
2. List it once, with a status comment, at the end of `series.txt`: every flavour applies that list, and the v3 and rt lists only add flavour patches (a second entry in a flavour list would apply the group twice and fail).
3. The published source package's `.orig.tar.xz` already holds the series applied (it is the retained, patched tree), so extract it and apply only the new group: `SKIP='^(0[0-9]|[123][0-9]|4[0-3]|90)-' sh apply-series.sh TREE FLAVOUR` (adjust the numbers) ends with "6 patch files applied"; `git apply` has no fuzz, so this is strict. Do it for base, v3 and rt, each from its own tarball, and compare the sha256 of the touched files.
4. Reverse the group (`git apply -R`, last patch first), check the file hashes are back to the original, apply again: proves the committed files, not only the first run.
5. Configure with the recipe, out of tree, with the tree mounted read-only: `sh kernel/configure.sh FLAVOUR /obj` (ends "102 of 102 requested values hold"), `make O=/obj -j4 modules_prepare` (about 50 s), then `make O=/obj -j4 W=1 drivers/input/ drivers/hid/` (about 80 s, 347 objects, writes the `.o` files and no `.ko`). Expect no warning in the touched files. The image needs the build tools and, because the configuration has `CONFIG_RUST=y`, rustc, rust-src, bindgen and libclang.
6. Prove the objects carry the change: `objdump -d drivers/input/evdev.o | grep 0x8004451c` finds the `EVIOCGBTNCNT` compare.
7. Prove the headers with a negative control: a C file with `_Static_assert(EV_BTN == 0x06)` and `EVIOCGBTNCNT` fails to compile against the container's stock `linux-libc-dev` headers and passes against `make O=/obj headers_install INSTALL_HDR_PATH=...`.

## SDL and Wine

- SDL: pull request 14758 (Pakuła, open draft, two commits, 2026-01-04) touches `src/core/linux/SDL_evdev_capabilities.c`, `src/joystick/linux/SDL_sysjoystick.c` and `SDL_sysjoystick_c.h`; the diff applies strictly to SDL 3.4.18. Debian's `libsdl2-2.0-0` is `sdl2-compat` on top of SDL3, so one SDL3 patch serves SDL2 programs too.
- Wine: merge request 9853 (draft, two patches to `dlls/winebus.sys/bus_udev.c`, `has_conflicts`) is written against Wine master. It does not apply to Wine 10.0 (the `lnxev_info` structure and the button loop it edits are not there; 5 of 6 hunks are rejected), so a Wine 10.0 package needs a port of the idea to the older `lnxev` code, credited to him.
- The kernel part is the one that decides: both consumers fall back to `EV_KEY` on a kernel without `EV_BTN`, so they can ship first.

## Traps

- Symptom: a fetch returns HTTP 200 and a page titled "Making sure you're not a bot!". Cause: Anubis, a bot check, on lore.kernel.org, git.kernel.org, patchwork.kernel.org and, for browser-like user agents, gitlab.winehq.org. Fix: do not solve it; use the mirrors above, and for gitlab.winehq.org a plain `curl` (default user agent) to `/-/merge_requests/N.patch` and `/api/v4/projects/wine%2Fwine/merge_requests/N`. Found by: `head -c 300` of the body.
- Symptom: the ratatoskr month pages answer 429 after a few requests. Cause: rate limit. Fix: query the author page once and the thread JSON once; do not loop over months.
- Symptom: `git apply --check` of patch 5 alone fails ("patch failed: drivers/hid/hid-input.c:770") while patches 1 to 4 pass alone. Cause: patch 5 re-indents the switch that patch 4 rewrites, so its context exists only after patch 4. Fix: check a series in order on a copy (apply, then reverse), never patch by patch on the pristine tree. Found by: the checks of the six files in a loop.

## Prove it at runtime without a full kernel build (milestone 2)

Recipe, all in containers and one QEMU guest, nothing on the host's input devices:
1. Reduced kernel from the same tree: `make tinyconfig`, merge a fragment (64BIT, SMP, TTY, SERIAL_8250_CONSOLE, PCI, VIRTIO_PCI, NET, INET, NET_9P_VIRTIO, 9P_FS, DEVTMPFS, TMPFS, PROC_FS, SYSFS, BINFMT_ELF, BINFMT_SCRIPT, UNIX, INOTIFY_USER, EPOLL, EVENTFD, TIMERFD, SIGNALFD, INPUT, INPUT_EVDEV, HID, HID_GENERIC, HIDRAW, UHID, MAGIC_SYSRQ), `olddefconfig`, check the options are `=y`, `make bzImage`: about 3 minutes on four CPUs, a 1.9 MB image. Build it twice from the same tree, once without the new group (the control) and once with it.
2. Guest userland without a disk image: `docker export` of a Debian container that has python3, libsdl3-0 and libsdl2-2.0-0 (sdl2-compat), extracted to a directory and served to the guest as its root over virtio-9p (`-virtfs local,path=ROOT,mount_tag=r,security_model=none,readonly=on` and `root=r rootfstype=9p rootflags=trans=virtio,version=9p2000.L`). Create empty `/out` `/run` `/tmp` in it first. A second 9p share, `out`, is the only writable place and carries the plan script and the results.
3. QEMU runs in a container with the host's `/usr` mounted read-only, `--device /dev/kvm --group-add <kvm gid>`, `-machine pc,accel=kvm -nographic -no-reboot -nic none -serial file:...`; the guest's `/init` mounts proc, sys, devtmpfs and the 9p shares, runs the plan and exits, and `panic=1` ends QEMU. Boot to result: about 10 seconds.
4. Libraries under test sit in `/opt/NAME/libSDL3.so.0` and a run picks one with `LD_LIBRARY_PATH`; sdl2-compat finds the same libSDL3, so SDL2 programs are tested by the same switch.
5. Matrix, each cell one boot: control kernel and new kernel, each with the unpatched and the patched SDL. Expect: control kernel `EVIOCGBTNCNT` errno 22 and no EV_BTN in the event types; new kernel 128 and `I: BTN=128`, 128 EV_BTN events one button at a time and 80 EV_KEY events; SDL3 and SDL2 report 128 buttons only with the new kernel and the patched SDL (79 in every other cell, the 80th is lost by SDL's `i < KEY_MAX` loop).
6. Build SDL for the test with cmake only (`-DSDL_UNIX_CONSOLE_BUILD=ON -DSDL_TESTS=OFF`, the two Debian patches applied by `patch -p1 -F0` first): two minutes, and a control build without the new patches from the same tree.

Traps met in the runtime proof:
- Symptom: SDL with the pull request reports 79 buttons on a kernel that offers 128, and the new log line says the kernel has no EV_BTN. Cause: the pull request falls back to `#define EVIOCGBTNCNT 0` when the build headers lack EV_BTN, and `ioctl(fd, 0, ...)` always fails, so every library built before the kernel headers carry EV_BTN never uses it. Fix: define the ioctl as `_IOR('E', 0x1c, unsigned int)` when the fallback is 0 (debian patch 0003 of libsdl3). Found by: the matrix, patched SDL on the new kernel.
- Symptom: pressing all 128 buttons at once gives 44 EV_BTN events and one SYN_DROPPED, and SDL then shows 24 buttons held. Cause: `input_estimate_events_per_packet()` counts 7 events for all keys and evdev sizes the client buffer from it (8 packets, rounded to a power of two), so one report that changes 128 buttons (EV_BTN + EV_KEY + MSC_SCAN) overflows it; SDL's EV_BTN path cannot resync because it skips `EVIOCGKEY` for EV_BTN devices. Fix: add `button_count` to the estimate (group 44, 0007). Found by: a held-together case, all buttons down in one report, in the same guest run.
- Symptom: a client that opens the device while buttons are held sees none above 80. Cause: `EVIOCGKEY` only knows EV_KEY and there is no way to read EV_BTN state (Ivan Gorinov, 2026-01-07). Found by: opening a second client with buttons 1, 5, 100 and 128 held.
- Symptom: QEMU container cannot reach Docker half way through a session (`Cannot connect to the Docker daemon`). Cause: the lane's proxy process ended while the socket file stayed. Fix: the main session restarts the proxy; keep the evidence and the scripts on disk so a run can resume.
