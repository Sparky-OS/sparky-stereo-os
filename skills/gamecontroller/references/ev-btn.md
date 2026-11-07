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
