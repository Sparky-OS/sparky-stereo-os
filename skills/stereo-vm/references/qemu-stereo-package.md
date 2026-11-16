# The next qemu-stereo package from fork commits

Written on 2026-11-16 by Claude Opus 5.5 with Daniel Ramos (ORDER 156b), when the depth work of Sparky-OS/qemu branch `order156-depth` became `qemu 1:11.1.2+ds-3+stereo3d8+lc1`, the successor of the published `+stereo3d7+lc1`.
The general packaging rules are in [edition-packaging](../../edition-packaging/SKILL.md) and the Lean Code ones in [lean-code](../../lean-code/SKILL.md); this page is the QEMU route and its traps.

## Recipe

1. **Reconcile the fork branch with the published source, by tree and by patch-id.**
   The fork's branches start from a snapshot commit ("Record authored source from authenticated shipped source package") that records only the files the stereo work touches (64 files), so `git log` alone does not say which package a commit equals.
   - Unpack the published source with its patches applied: `dpkg-source -x qemu_VERSION.dsc src7`.
   - For each fork commit, compare every file it records with that tree: `git ls-tree -r --name-only C` and `git show C:FILE | cmp - src7/FILE`. The commit with no difference is the published package; here the root equalled `+stereo3d6` but for `ui/spice-display.c` and its header, which the three patches of `+stereo3d7` change.
   - Compare patch-ids: `git patch-id --stable < PATCH` for each published patch, `git show C | git patch-id --stable` for each fork commit. Equal ids mean the commit is already carried.
   - Write the result as a table: commit, subject, in the published package or not, the evidence.
2. **Make one DEP-3 patch per missing commit**, numbered after the published series (`stereo3d/0012-...`): `Description:` with the commit's subject and body, `Author:`, `Origin:` the fork commit's URL, `Forwarded: no` (QEMU declines AI-assisted contributions, so the work is carried), `Last-Update:` the commit's date, and the commit's own `Assisted-by:`. The generator used is below.
3. **Prove the patches are the branch:** copy the patched published tree (`cp -a`, no `git init`), apply the new patches with `patch -p1 -F0`, and compare every file the fork's tip records with `cmp`. Expected: 0 of 66 differ.
4. **The successor source** is made the way every other edition successor is: `packages/qemu-stereo/next-source.sh PUBLISHED.dsc OUT` runs `repo/lc-successor.py --in-place --overlay`, the overlay holding the whole new `debian/patches/series`, the new patches, and `debian/control` plus `debian/control-in` (QEMU regenerates `control` from `control-in` at clean, so a build dependency goes into both). The changelog text lives in `changelog-stereo3dN.txt`; its bullets become `--item`s.
   - Commit the recipe first: the source's date is the recipe folder's last commit.
   - Make the source twice into two folders; the `.dsc` and `.debian.tar.xz` must hash the same.
   - The published changelog must stay a byte-identical suffix: `tail -c $(stat -c %s OLD.changelog) NEW.changelog | cmp - OLD.changelog`.
   - Put the orig tarball beside the new `.dsc` (the successor writes only the `.dsc` and the Debian tarball).
5. **Build** with `release/build-from-lc-dsc.sh DSC amd64 sparky-lc-migration:20261020 REPO OUT`:
   - `SPARKY_LC_ARCHIVE_DIR`: a folder with the recipe's `gate-sources.json` as `sources.json` and the three keyrings it names under `keyrings/` (Debian's archive keyring, deb-multimedia's, the edition repository's public key);
   - `SPARKY_LC_PREVIOUS_DIR`: the published package's binaries, so the gate compares against them;
   - `SPARKY_CONTAINER_PREFIX` set to the lane's prefix, `CPUS=4`;
   - the script has no `--ulimit core=0`: wrap `docker` in an exported shell function that adds it to `docker run` and nothing else;
   - read the gates in the build's own log: `lc1: verified N packages`, `archive-qualified link check passed`, `build record`.
6. **Install by apt from the published set** in the proof image: a flat repository of the new `.deb` files (`dpkg-scanpackages -m . > Packages`, `deb [trusted=yes] file:/local ./`, pinned at 1001 with `Pin: origin ""`), then `apt-get -s install` of exactly the installed binary packages of source `qemu` (`dpkg-query -W -f '${source:Package} ${Package}\n'`); keep the `Inst` and `Remv` lines, every `Inst` naming the new version and no `Remv`.
7. **Red and green** on the installed packages, below.

The DEP-3 generator (Python, the fork clone and the output folder, then `NAME=COMMIT` pairs):

```python
import subprocess, sys
from pathlib import Path
repo, out = Path(sys.argv[1]), Path(sys.argv[2])
git = lambda *a: subprocess.check_output(['git', '-C', str(repo), *a], text=True)
for name, commit in (a.split('=', 1) for a in sys.argv[3:]):
    full = git('rev-parse', commit + '^{commit}').strip()
    body = [l for l in git('log', '-1', '--format=%b', full).rstrip('\n').splitlines()]
    assisted = [l.split(':', 1)[1].strip() for l in body if l.startswith('Assisted-by:')]
    body = [l for l in body if not l.startswith('Assisted-by:')]
    while body and not body[-1].strip():
        body.pop()
    head = ['Description: ' + git('log', '-1', '--format=%s', full).strip()]
    head += ([' .'] + [' ' + l if l.strip() else ' .' for l in body]) if body else []
    head += ['Author: ' + git('log', '-1', '--format=%an <%ae>', full).strip(),
             'Origin: https://github.com/Sparky-OS/qemu/commit/' + full, 'Forwarded: no',
             'Last-Update: ' + git('log', '-1', '--date=short', '--format=%ad', full).strip()]
    head += ['Assisted-by: ' + a for a in assisted]
    (out / name).write_text('\n'.join(head) + '\n---\n' + git('show', '--format=', '--stat=72', full) + '\n'
                            + git('show', '--format=', '--full-index', '--no-renames', full))
```

## Red and green for a guest with depth

The guest of [the depth section](../SKILL.md#picture-plus-depth-through-the-vm-chain-order-156) with three additions in its `init`: `layout=4` draws a 3840-wide side by side (full) frame (the right view's red block 30 columns to the left, so the expected disparity is exactly -30), `force=1` sets the layout on the plain 1920x1080@60 mode when the connector lists no such mode, and the connector's EDID is printed as one `EDID <hex>` line.
One fresh container per case (Stereo KWin `--virtual` 3840x2400, the installed QEMU's GTK display on Wayland, KVM, three ScreenShot2 captures); the expectation is the guest's own drawing and the depth library's documented parallax, never a picture the viewer drew.

| Case | Published +stereo3d7 | +stereo3d8 |
| --- | --- | --- |
| L + depth, from the EDID | the guest lists 51 modes and no `l-depth`: `FAIL no 1920x1080@60 mode of layout 5` | the guest lists 55 modes, `l-depth` among them; a pair at KWin, declared once (`set_content(3)`, `set_destination(1920, 1080)`): left eye the picture (0 of 2,073,600 differ), red block -58.0 px against -57.55 predicted, vertical 0.0, 0 of 270,000 screen-plane samples differ |
| L + depth, forced | a pair at KWin: the left eye is the picture (0 of 2,073,600 differ), the right eye is the depth map (every sample grey, 0 red samples), 270,000 of 270,000 screen-plane samples differ | not needed: the mode is listed |
| L + depth + graphics + graphics-depth, forced | the same, and the left eye lacks the graphics (22,500 samples, the 150x150 box) | red block -58.0 px, graphics box -57.5 px, vertical 0.0, screen plane 0 differ; the left eye differs from picture plus graphics in 1,200 samples, the red block's three edge columns on each side (the library's overlay path blends the picture at its own depth edges; layout 5's path keeps the picture exact) |
| 2D guest | one 3840x2400 picture, the block's 40,000 samples | 0 pixels differ from +stereo3d7's capture; nothing declared |
| side by side (full) guest | left and right views exact, disparity -30.0, vertical 0.0 | 0 pixels differ from +stereo3d7's capture; declared once |

## Traps

- **Symptom:** `git apply --check` of the depth commits on the published tree: `error: patch failed: include/ui/console.h:124` and `ui/wayland-stereo.c:237`. **Cause:** the depth work was written on five fork commits that no package carried (line-alternative metadata and native line samples, the rutabaga disable, the GL readback bound). **Fix:** carry them too, before the depth patches, so the package equals the branch. **How found:** the per-commit tree comparison of step 1 (the published tree differed from the fork's base in the files those five commits touch).
- **Symptom:** after 57 minutes the build stops at `debian/rules:771: binary-helper] Error 1`; far above it: `qemu-system-gui_...deb: link check failed: /usr/lib/x86_64-linux-gnu/qemu/ui-gtk.so: 3 new undefined: error_free, error_reportf_err, warn_report_once_cond (the previous build resolved them)`. **Cause:** the depth code in the GTK module calls three more QEMU functions; `qemu-system-x86_64` exports them (`nm -D --defined-only`). The published module already leaves 139 symbols to the loader, 113 from the program and 26 from `ui-opengl.so` in the same directory, but the gate traced the module alone and required every undefined symbol to be in the previous build. **Fix:** the gate's plugin rule of ORDER 156b ([lean-code lessons](../../lean-code/references/lessons-2026-11.md)), then the source made again (the toolkit travels inside it) and built again; a first version of the rule that counted the program alone failed the second build the same way, because of the 26 symbols from `ui-opengl.so`. **How found:** `grep -n 'link check failed' -A2` in the build log; the script stops before its cleanup, so the build tree and `link-scratch` stay in OUT for reading.
- **Symptom:** `git patch-id` prints nothing for a published patch (`0006`). **Cause:** a plain unified diff without `diff --git` headers. **Fix:** read the commit from its `From` line or compare trees instead.
- **Symptom:** the branch-keeper hook refuses `rm -rf` of a scratch copy: "branch master: 2 commit(s) on no remote". **Cause:** `git init` and a commit in the scratch copy, to use `git apply`, made it a clone with local work. **Fix:** bundle it into the lane folder before removing it, or never `git init` a scratch tree: `patch -p1 -F0` on a `cp -a` copy does the same check. A hook judges a whole command line before it runs, so the bundle and the removal go in two calls.
- **Symptom:** the build container's name has a double dash (`...-lc1--amd64`). **Cause:** `build-from-lc-dsc.sh` passes `basename` output, newline included, through `tr -c`. **Fix:** find it with `docker ps --filter name=PREFIX`, never type it.
- **Symptom:** `docker run IMAGE sh -c ...` on the rig base `rp-580-rig:published` prints `/usr/bin/sh: cannot execute binary file`. **Cause:** its entrypoint is `bash` with a script as command. **Fix:** `--entrypoint ""`, and `docker commit --change 'ENTRYPOINT []'` for an image made from it.
- **Symptom:** apt in that rig base warns `Missing key A401FF99368FA1F98152DE755C808C2B65558117` for deb-multimedia. **Cause:** the image's own copy of the keyring. **Consequence:** harmless for QEMU (its dependencies come from Debian and the edition); the gate's folder takes a keyring that has the key (check with `gpg --show-keys --with-colons`).
- **Symptom:** a recipe change after the source was made gives another source. **Cause:** the date is the recipe folder's last commit. **Fix:** freeze the recipe folder once the source is built; skills and notes go elsewhere.

## Measured

- The build (`release/build-from-lc-dsc.sh`, 4 CPUs, 8 GB memory): 3,286 s on 2026-11-16 (two earlier builds of the same version took 3,410 s and 2,912 s to their gate failure). Watched on the first one: about 15 minutes of build dependencies and the Lean Code projection (4,359 of 21,537 build-input files), 31 minutes compiling (5,282 steps for the system emulators, then the x86 and user-mode builds), 11 minutes of packaging, Lean Code assembly and the gate. A failed gate costs the whole build.
- Disk: the build tree in OUT peaked at 10.4 GB (the container's apt layer comes on top, not measured apart). The stage is 800 MB for 39 packages (dbgsym included) and the source.
- The package's own tests in the build: the block suite, 129 OK, 0 failed, 4 skipped.
- Every one of the 39 packages has the same file list as `+stereo3d7` (version replaced, dbgsym build ids left out); `qemu-system-gui` gains `Depends: libstereo-dibr1 (>= 1.18.0)` from the library's shlibs file.
- Upgrade from the published set: 5 `Inst` lines (`qemu-system-common`, `-data`, `-gui`, `-modules-opengl`, `-x86`), each `+stereo3d7` to `+stereo3d8`, no `Remv`.
- A guest started with KVM reads the EDID before the GTK window reports its size: with `+stereo3d8` its first mode was 1280x800 (QEMU's default) where `+stereo3d7` gave the window's 640x506; under TCG both give 640x506. A race of the one-second test guest, not a change of the patches; say which accelerator a mode list came from.

## Debian has moved

On 2026-11-16 Debian testing and unstable carry `qemu 1:11.1.3+ds-1` (experimental `1:11.2.0~rc0+ds-1`); `+stereo3d8` stays on `1:11.1.2+ds-3`, as `+stereo3d7` is.
A rebase onto 11.1.3 needs: the new orig tarball and Debian's `-1` `debian/` (signature checked with `gpgv --keyring /usr/share/keyrings/debian-keyring.gpg`), our 21 stereo patches (all apply at fuzz 0, `0004` and `0007` with line offsets), Debian's three patches that 11.1.3 carries upstream no longer in the series, `prepare-lean.py` run again (its five rules targets and both hooks are still found once each), and a new rebase script, since `rebase-debian.py` asserts `1:11.1.2+ds-3`.
