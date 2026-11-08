# Requalifying the gl-stereo savers

Read on 2026-11-08 (gl-stereo 0.4.3, ORDER 146d), from a requalification of the published 0.4.2 layer and of the 0.4.3 layer on an NVIDIA card, with the AMD render node out of reach.
gl-stereo's own recipe is `savers/audit/README.md`, section "Requalifying after a layer change"; this page adds what it leaves out: the audit image when its base is gone, a device other than the AMD render node, the run times and every trap met.

## When it is needed

The 130 saver receipts in `savers/qualification-6.09.json` bind two things: the SHA-256 of the stripped `libgl-stereo.so` (`library_sha256`) and the SHA-256 of each saver's executable (`executable_sha256`).
`install-qualified.py`, run by `packaging/qualify-package.sh` in the package build, stops the build with "untested layer binary" or "untested saver binary" when either differs.
So all 130 are needed again after any change to the layer, even a message on stderr, and after a rebuild of XScreenSaver's savers (a Lean Code rebuild gives other bytes).

Check first which savers the installed package can offer at all:

```sh
python3 - <<'PY'
import sys; sys.path.insert(0, '/usr/lib/gl-stereo/savers')
import catalogue
print(len(catalogue.load('/usr/share/gl-stereo/catalogue.json')), 'eligible of 132')
PY
```

`catalogue.load` drops every entry whose executable no longer has the receipt's hash, so a catalogue made for older savers silently offers almost none.
With gl-stereo 0.4.2-1+lc1 and xscreensaver 6.09+dfsg1-2+stereo3d4+lc1 it printed 1 of 132: the receipts named the +stereo3d3 savers.

## Recipe

1. **The audit image.** The README's base (`gl-stereo-package-proof:3`) no longer exists.
   Make one from the pinned amd64 testing base: the edition's repository (`Signed-By` its public key, pin 1001), deb-multimedia, and `apitrace build-essential cmake dbus-x11 gpgv kscreen kwin-wayland libcap2-bin libegl-dev libgl-dev libstereo-declare-dev libstereoshow-dev libwayland-dev libx11-dev lintian mesa-utils ninja-build pkgconf plasma-wayland-protocols procps python3-dbus python3-gi python3-numpy python3-pil python3-tk qt6-base-private-dev qt6-declarative-dev sparky-stereo-power-profiles systemsettings wayland-protocols x11-utils x11-xserver-utils xauth xscreensaver xscreensaver-data xscreensaver-data-extra xscreensaver-gl xscreensaver-gl-extra xvfb libwayland-egl-backend-dev paraview python3-paraview`.
   The base needs the edition repository mounted, so make it with `docker run` and `docker commit` (6 minutes), then build `savers/audit/Dockerfile` over it with its `FROM` line changed (apt over HTTPS only, `tools/https-only-build.sh`).
   Install the saver packages from the repository that the package build will use: the receipts name their executables.
2. **The seccomp profile.** `savers/audit/seccomp-setarch.py` over Docker's own default profile of the daemon's commit (for Docker 29.9.2: `vendor/github.com/moby/profiles/seccomp/default.json` at tag `docker-v29.9.2`, SHA-256 `785b2429…`, giving a profile with SHA-256 `084fe00d…`, the same as 29.9.1's).
3. **Prove the device with the layer the committed receipts name.** Install the published layer's five packages as the bootstrap and run the whole requalification; it must give the committed receipts' outcomes: 130 of 130, the group counts, 92 depth savers with the same residuals (mean and histogram, `depth_residual_mean_px`), exact 2D pairs.
   Compare per saver with a script, not by eye (group, state, oracle, passed, `stock_2d_exact`, `kwin_composition`, `camera_or_flat`, each `residual_px`).
   On the RTX 3060, with `XWAYLAND_NO_GLAMOR=1` (below), it reproduced all of it: 0 outcome differences, 118 of 130 stock 2D pictures byte-identical to the committed hashes, the rest differing only where the savers' executables were rebuilt.
4. **The bootstrap build is the build that ships.** The packages that ship are the Lean Code ones (`+lc1`), and lean 0.1.28 drops the lines of removed comments, so the layer it builds has another build ID than the plain build's, with the same machine code: 0.4.3 gave `cab2fc79…` (Lean Code) against `f21ac090…` (plain), and `install-qualified.py` stopped the Lean Code build with "untested layer binary" for antinspect on receipts made with the plain layer.
   So make the bootstrap with `sparky-os/release/build-dh-lean.sh` on the authored tree with `savers/qualification-6.09.json` removed, and an orig tarball made from `git ls-files` minus `debian/` and minus that file (the package keeps the five accepted receipts and prints the layer's hash; 5 minutes with the gate).
   The same layer came from `/work/lean-source` (build-dh-lean.sh) and `/work/build/tree` (build-from-lc-dsc.sh), so the build path does not matter, only the source does.
   A plain `dpkg-buildpackage` bootstrap (75 seconds) is fine for a first look, but its receipts will not fit the Lean Code build.
5. **The requalification.** Container with `--network none --cpus 4 --cap-add SYS_NICE --security-opt seccomp=PROFILE`, the device, the checkout at `/workspace/gl-stereo`, scratch at `/build`, the bootstrap debs at `/debs`, the XScreenSaver original tarball at `/orig`, `xscreensaver-gl-extra 6.09+dfsg1-2+stereo3d1` at `/old`, the repository at `/var/local/sparky-stereo-repo`, then `requalify-root.sh` as root.
   About 50 to 65 minutes at four CPUs, depending on what else the machine runs: setup and late-compositor 1 minute, glsnake lights 2, the 130 KWin sessions 19 to 22, old Flurry, warmups, Star Wars and Flurry 4, the 28 references 6, FlipText 2, the 129 mono controls 17, the other mono controls 4, collector and compiler 1; the functional suite 2.5.
   Steps can be run again by name (`STEPS="candidate install-candidate functional compile"`), and the scratch keeps the earlier results.
6. **Commit the receipts, build the final package** with `build-dh-lean.sh` on the authored tree with the new manifest (5 minutes), then the published form from its `.dsc` with `build-from-lc-dsc.sh` (5 minutes; the gate, `lean.release check-debs`, the previous +lc1 build as the comparison, `SPARKY_LC_ARCHIVE_DIR` and `SPARKY_LC_PREVIOUS_DIR` set as the scripts say); the build's own gate prints "132 receipts bind the tested stripped binaries" and the layer's hash must equal the receipts'.
7. **Install the final debs in the audit image** and run the installed functional suite, the sizing rig and `tests/run-late-doubling.py` held and unheld.
   The new message ("the compositor did not double window N") must appear only in the held session.

## Other device than the AMD render node

KWin's virtual backend needs a DRM render node.
With none it logs "Failed to open drm node /dev/dri/renderD128", falls back to software compositing and the window capture is cancelled (`org.kde.KWin.ScreenShot2.Error.Cancelled`, no `kwin.png`): llvmpipe alone does not do.
The NVIDIA card through CDI (`--device nvidia.com/gpu=0`, no group 125) gives KWin `/dev/dri/renderD129`; the savers still draw with llvmpipe (the client sets `LIBGL_ALWAYS_SOFTWARE=1`).
Mesa's EGL cannot take KWin's place on that node (`__EGL_VENDOR_LIBRARY_FILENAMES` Mesa's file, with or without `MESA_LOADER_DRIVER_OVERRIDE=zink`: `eglInitialize failed`).
Set `-e XWAYLAND_NO_GLAMOR=1` (see the first trap).

## Traps

- **Symptom:** the exact producer-against-KWin composition check fails for 41 of 130 savers ("composited interior differs from producer", up to 12 % of the pixels, max error 179) and 11 independent-camera references fail after it (mean error 26, "reference mismatch"), with the layer the committed receipts name.
  **Cause:** on NVIDIA's render node Xwayland's glamor path gives other pixels for translucent window content than the AMD path did: in every differing pixel KWin's value is at least the producer's in all three channels (lit scenes look brighter).
  **Not** the compositor version (the figures were identical to 15 digits under KWin +stereo3d24 and +stereo3d46) and not the layer.
  **Fix:** `XWAYLAND_NO_GLAMOR=1` in the container; Xwayland logs "Disabling glamor and dri3 support, XWAYLAND_NO_GLAMOR is set" and the compositions are exact (0 changed pixels).
  **Found by:** reading the dump (`frame-*.ppm`) against `kwin.png` for one saver with numpy (sign of the difference per pixel), then a single-saver rerun with the variable; the first run's failures were deterministic, so a race was ruled out.
- **Symptom:** the variable set on the container has no effect.
  **Cause:** `requalify-root.sh` runs the steps through `env -i`.
  **Fix:** `user()` passes `XWAYLAND_NO_GLAMOR` through when it is set (committed with 0.4.3's receipts).
- **Symptom:** `installed-functional status 127` after "quad-gears: ... measured residual" in the log.
  **Cause:** `run-native-tests.sh` runs `pvpython` and the image had no ParaView.
  **Fix:** `paraview` and `python3-paraview` in the audit image.
- **Symptom:** `rotation.py` stops at `assert {'starfield','rocks'} <= ...` in the functional suite of the published 0.4.2 packages.
  **Cause:** the published catalogue's Rocks receipt (made by the package build) names the executable of the earlier XScreenSaver; `catalogue.load` drops it.
  **Fix:** none needed for the requalification itself, whose bootstrap build regenerates the five accepted receipts against the installed savers; do not use the published packages' catalogue for the functional suite of a proof run, compile the candidate manifest without that gate and compare it.
- **Symptom:** `tests/starfield.py` ends with `EOFError: producer closed` once, in a run with the machine at a load average of 15 to 22.
  **Cause:** not determined; the same steps with the same inputs passed at load 7.
  **Fix:** run the failed steps again and keep the first log (`installed-functional.attempt1.log`); never edit the test.
- **Symptom:** a depth saver (atunnel) fails the depth oracle ("analytic reprojection has too little depth-consistent coverage") in the run with glamor on and passes in the run with it off.
  **Cause:** not determined (the oracle reads the layer's own dump); noted so the next run knows it is not the layer.
- **The Lean Code layer is not the plain layer.** See step 4: requalify the bootstrap that is built the way the package ships, or the final build stops at the gate.
- **The repository changed under the receipts.** Receipts made against +stereo3d3 savers do not hold for +stereo3d4+lc1: every executable hash differs.
  Requalify against the savers of the repository the final build uses, and say so in the changelog; `gl-stereo-savers` depends on `xscreensaver-gl (>= …+stereo3d3)`, which does not pin the build the receipts name.
- **Disk.** The scratch of one run is 0.8 GB, the image 4.4 GB; delete the case directories after copying the logs, statuses, `qualification-6.09.json` and the comparison output.

## What a good run looks like (0.4.3, Lean Code layer `cab2fc79…`)

`requalify.log` shows every step with status 0; `installed-mono-summary.log`: "exact nonempty 2D controls 130 of 130"; `installed-qualification.log`: "depth residual mean -0.043 px over 92 savers; histogram {-0.5: 13, 0.0: 75, 0.5: 3, 1.0: 1}" and "PASS: 130 complete installed qualifications {'layer': 118, 'flat': 10, 'owning-fix': 2}"; the mutations log: 13 PASS lines (valid accepted, missing, duplicate, unknown, stale-layer, stale-saver, settings, false-proof, false-2d, false-composition, excess-depth, excess-residual, shifted-residuals rejected); `installed-late-compositor.log`: "held equals plain: True".
The candidate manifest (compiled without the functional gate) and the final one are the same file (`cmp`).
