# USB-C side by side glasses, recognised by their EDID

Written by queue row 132 (2026-11-26) against Stereo KWin 6.7.4-2+stereo3d68 and the edition kernel 7.3.4-stereo3d18.

USB-C glasses (XREAL, VITURE, Rokid, RayNeo and others) are DisplayPort monitors over DP Alt Mode, driven by the GPU's own DisplayPort driver: no driver of their own is needed for the picture.
In their 3D mode most of them announce one mode two eyes wide (3840x1080) and show its left half to the left eye and its right half to the right eye.
Stereo KWin offers a side by side (full) twin of such a mode under Other stereo formats, and chooses it by itself for glasses it knows by their EDID identity, so the desktop (one eye, 1920x1080) is copied into each half and a 3D program's eyes reach each eye at their own resolution.
The person's choice per output (Display Settings, "USB-C 3D glasses") stays theirs.

## Recipe: adding a pair of glasses

1. **Find a real EDID in a public record.** Never an entry without one.
   - [linuxhw/EDID](https://github.com/linuxhw/EDID): a shallow clone without blobs lists every path in seconds (`git clone --depth 1 --filter=blob:none --no-checkout`, then `git ls-tree -r --name-only HEAD`), and `git cat-file -p HEAD:PATH` fetches one record. Search the paths by PnP ID (`/LBT4753/`, `/TCL03D4/`) and `DigitalDisplay.md` by name; glasses hide under unexpected vendor folders (XREAL's MRG is "Nreal Air", a VITURE is under "Others").
   - An owner's own captures: `xrandr --props` and `edid-decode` in both modes (the xrdome project's `docs/hardware/` has a VITURE Pro XR and an XREAL Air 2 Pro, 2D and SBS).
   - Kernel and forum reports: freedesktop's drm/misc issue 53 (XREAL Air, Air 2 Pro), an NVIDIA forum attachment (VITURE Beast).
2. **Keep only what the kernel reads.** The base block's byte 126 names the extension blocks (VESA E-EDID A2, 3.11); some probe dumps carry more blocks after them. Check every kept block's checksum. The bench's [`edid/edid-extract.py`](../../../tools/vkms-stereo-bench/edid/edid-extract.py) does both and prints the identity and every detailed timing.
3. **Read the identity, never the name:** the PnP ID with the product code. Names repeat ("Air", "SmartGlasses", "VITURE") and product codes repeat across makers (MRG 0x3132 is the XREAL Air, CVT 0x3132 a VITURE).
4. **Each mode is its own EDID.** The glasses re-announce themselves when their mode changes. Record every state a record shows (2D, Full SBS, Half SBS, the glasses' own 2D-to-3D mode) and list each state no record shows under `not_public`, with the reason. Every pair measured in both modes so far keeps its identity in Full SBS (XREAL One Pro, XREAL Air 2 Pro, VITURE Pro XR), though other fields change (the VITURE's made year).
5. **Add it in three places, one commit each side:** the identity table `sparky-os/data/stereo-glasses.json` (build tree), KWin's `s_stereoGlasses[]` (`src/outputconfigurationstore.cpp`), and the EDID file in KWin's `autotests/integration/data` with a row in `mockGlassesTest`'s `publishedEdidsComeUpByIdentity` and its source in `usb-c-glasses-edids.txt`.
   New EDIDs travel as rows of hex (`.hex`, `QByteArray::fromHex`): a quilt patch carries text only, and binary files need `debian/source/include-binaries` (the One Pro's `.bin` files do).
6. **Check:** `python3 sparky-os/tests/check-stereo-glasses-table.py --kwin UNPACKED_KWIN_SOURCE` fails when the table and KWin carry different identities, a state has neither an EDID nor a reason, an EDID's identity, version, serial, date or timings differ from the table, a control or an identity marked not entered reaches KWin, or KWin's test does not read an EDID the table names.

Run the checker red too: on KWin's source with the test data but without the new identities, it fails on the identities alone.

## Recipe: the proof per pair of glasses, in a VKMS guest

The skill [`vkms-stereo`](../../vkms-stereo/SKILL.md) holds the bench; for glasses it is simpler, because no HDMI 3D mode is involved (the twin is KWin's).

1. **The edition's own kernel**, from its package: the published `linux-image` already has VKMS with the configfs `connectors`, `edid`, `edid_enabled` and `status` attributes. Take the closure of `vkms`, `9p`, `9pnet_virtio`, `overlay` and `configfs` from the package's `modules.dep`, decompress them (BusyBox `insmod` reads plain `.ko`), and give `vkms` `create_default_dev=0` on the `insmod` line.
2. **One DisplayPort connector** (`type` 10: the glasses are DisplayPort), the EDID written in one write before `enabled`.
3. **The root as a container image** with the edition's packages pinned at 1001, exported with `docker export` into a folder (owners not kept, `/dev` left out) and shared read only over 9p; tmpfs on `/tmp`, `/run`, `/root`, `/var/tmp` and `/home`, so every case starts with no saved state.
4. **One guest per case:** KWin with `--drm` in a D-Bus session, `kscreen-doctor -o` polled until an output has a current mode (it prints the mode's tag, `(3D-SBS-full)`, and "Side by side 3D glasses: enabled"; a fresh session's KWin logs only `Generating new config for 1 outputs`, while `Chose new mode for output ... side by side (full), for glasses` comes from the path that finds a saved setup, as when the glasses switch modes with the cable in), then the output set to scale 1 and three frames read with `drm-grab` (the bench's), each kept once two grabs a second apart are equal.
5. **Two clients:** the bench's `fullscreen-2d` (a gradient: the halves of a twin frame must be equal) and the bench's [`src/glasses-sbs.c`](../../../tools/vkms-stereo-bench/src/glasses-sbs.c), an address-coded full-screen window declared full side by side (`R = x & 0xff`, `G = y & 0xff`, `B = eye << 7 | (y >> 8 & 7) << 4 | (x >> 8 & 15)`), so every scanned-out sample says which eye and which place it shows. On the twin each half must hold its whole eye, 1920x1080 samples each; on a 2D mode the left view is the whole picture and no sample carries the right eye's bit.
6. **Red and green:** every EDID on the published KWin and on the candidate, the controls on both (a 32:9 monitor of the same size, an ordinary monitor with a glasses maker's PnP ID), and the One Pro as the regression row.

One guest case took about a minute with KVM and four virtual processors, the matrix of 30 cases about half an hour.

## Traps

- **Symptom:** KWin's package build stops with status 2 a few minutes in, `build.log` holds only dpkg-source's warning. **Cause:** `build_user=$(getent passwd 1000 | cut -d: -f1)` under `set -o pipefail`: `getent` exits 2 when no user has uid 1000. **Fix:** the build image carries a user with uid 1000 (`useradd --create-home --uid 1000 builder`), as the recipe's README says. **Found by:** `build-versions.txt` written and nothing after it, then reading the script from that line.
- **Symptom:** a client's `stereo_declare_wayland()` returns non-zero; the window shows as plain 2D. **Cause:** the declaration global is bound on a roundtrip after `stereo_declare_wayland_init()`. **Fix:** `wl_display_roundtrip()` after the init, then check `stereo_supported_wayland()`, as the library's API.md example does.
- **Symptom:** a full-screen client on the glasses is configured at 2844x800, and no sample of a frame is where it should be. **Cause:** KWin's first scale from the EDID's screen size: glasses announce 12 x 7 cm, so KWin starts them at 1.35. **Fix for a proof:** set the output to scale 1 before the clients (`kscreen-doctor output.DP-1.scale.1`, then poll until `Scale: 1`), and record the scale KWin chose. The default itself has no recorded design yet.
- **Symptom:** a linuxhw record decodes four blocks, two of them unknown or repeated. **Cause:** the probe dumped more than the base block declares. **Fix:** keep `128 * (1 + byte 126)` bytes, as the kernel reads.
- **Symptom:** `DigitalDisplay.md` lists a monitor as 3840x1080 whose first timing is another size. **Fix:** choose a control by its first detailed timing, read from the record itself.
- **Symptom:** every glasses EDID fails `edid-decode --check`. **Cause:** they give a detailed timing's image size as its pixels in millimetres (3840 x 1080 mm on a 12 x 7 cm screen), among other findings. They are the devices' own bytes: load them as they are, and say so beside them.
- **Symptom:** freedesktop's GitLab answers an issue page with an Anubis check. **Fix:** its API returns the issue as JSON without a login (`/api/v4/projects/drm%2Fmisc%2Fkernel/issues/53`); comments need a token.
- **Symptom:** a frame of the scanout, not of a writeback connector. **Cause:** a writeback job needs the DRM master, which KWin holds. `drm-grab` reads the framebuffer the CRTC scans out through `GETFB2` (root in the guest), which is what the panel would show.

- **Symptom:** the red run of `testMockDrmGlasses` (the recipe's patch reversed in the package's built tree) passes every row. **Cause:** that tree is the Lean Code projection, without comments, so `patch -R` fails on the hunk's comment lines (`Hunk #1 FAILED`) and `ninja` finds nothing to rebuild. **Fix:** change the code itself with a script that fails unless it finds what it changes (put the previous `s_stereoGlasses` back), and check that the file was compiled and the library linked again. **Found by:** a red run that could not fail, then `patch-reverse.log` and `ninja: no work to do`. Measured on +stereo3d68: green 26 of 26, red 13 of 26 failing (the eleven glasses rows and the two mode-following rows).
- **Symptom:** `sha256sum -c` reports no `OK` line and `readelf -n` no `Build ID`, on files that are fine. **Cause:** the host's `LANGUAGE` list names another language after English, which has no catalogue of its own, so gettext prints that language's words (`SUCESSO`, `ID da compilação`). **Fix:** `LC_ALL=C` before any tool whose output a script parses.
- **Symptom:** the candidate's root holds many more packages than the published one. **Cause:** installing every package of the build brings `kwin-dev` and its development dependencies. **Fix:** leave the `-dev` package out of a rig root, or say that the roots differ there (the runtime libraries are the same versions).

## The glasses known on 2026-11-26

| Glasses | PnP, product | EDID name | Records | In KWin |
|---|---|---|---|---|
| XREAL One Pro | MRG 0x4100 | XREAL One Pro | 2D, Half, Full, Real 3D (an owner's) | since +stereo3d34 |
| XREAL Air 2 Pro | MRG 0x3135 | Air 2 Pro | 2D, Full SBS | +stereo3d68 |
| VITURE Pro XR | CVT 0x3132 | VITURE | 2D, Full SBS | +stereo3d68 |
| XREAL Air | MRG 0x3132 | Air | 2D | +stereo3d68 |
| Nreal Light | MRG 0x3131 | Light | 2D | +stereo3d68 |
| VITURE Beast | VIT 0x0120 | VITURE Beast | 2D | +stereo3d68 |
| Rokid Air | LBT 0x4752 | Rokid Air | 2D | +stereo3d68 |
| Rokid Max | LBT 0x4753 | Rokid Max | 2D | +stereo3d68 |
| TCL SmartGlasses (RayNeo Air series by obs-nyan-real-3dof's table) | TCL 0x03D4 | SmartGlasses | 2D | +stereo3d68 |
| TCL SmartGlasses, 120 Hz | TCL 0x03D5 | SmartGlasses | 2D | +stereo3d68 |
| XREAL 1S | MRG 0x4102 | XREAL 1S | identity described, no EDID published | not entered |

A pair known by its 2D EDID only comes up in full side by side when its Full SBS EDID keeps the identity, as every measured pair does; until a record shows it, that is not claimed.
