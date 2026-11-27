# The AAC Bluetooth codec: our plugin beside Debian's PipeWire, its exact pin, and its rebuild when Debian moves

**Check freshness first.**
Written on 2026-11-26 (queue row 944) on Debian's PipeWire 1.6.11-2 and the edition's `pipewire-bluez5-codec-aac 1.6.11-2+aac2+lc1`.
Read `spa/plugins/bluez5/media-codecs.h` of the PipeWire you build against before trusting a version number here.

Daniel, 2026-10-02: "Debian PipeWire lacks AAC (fdk non-free)"; his JBL TUNE510BT offers SBC and AAC.
Debian builds PipeWire without Fraunhofer's library (it is in non-free), so the edition builds the one plugin that needs it, `libspa-codec-bluez5-aac.so`, from PipeWire's own source, and `sparky-stereo-hardware-support` Depends on it.
The recipe is `sparky-os/packages/pipewire-bluez5-codec-aac` in the build repository.

## Why the pin is exact, and what it costs

- The codec plugin speaks a private interface: `SPA_TYPE_INTERFACE_Bluez5CodecMedia` ("Spa:Pointer:Interface:Bluez5:Codec:Media:Private"), whose header says "The version should be incremented when any of the structs or semantics change" (`SPA_VERSION_BLUEZ5_CODEC_MEDIA`, 16 in 1.6.9 and 1.6.11).
  `codec-loader.c` refuses a plugin of another version at load ("codec plugin ... has incompatible ABI version").
- So the package Depends on `libspa-0.2-bluetooth (= DEBIAN_VERSION)`, the version whose source it was built from.
- The cost: the day Debian testing moves PipeWire, apt keeps PipeWire back on every installed edition rather than remove the codec (apt-get(8): new versions "that cannot be upgraded without changing the install status of another package will be left at their current version"), and the edition cannot be installed fresh with both.
  On 2026-11-26 testing's index of 20:15 UTC moved to 1.6.11-2: eight packages kept back (`libpipewire-0.3-0t64 libpipewire-0.3-modules libspa-0.2-bluetooth libspa-0.2-modules pipewire pipewire-bin pipewire-jack pipewire-pulse`), 0 removed.
- Loosening the pin is not the answer: it would let a plugin load into a PipeWire it was not built for, and it would keep the plugin's own fixes away (below).

## Recipe: when Debian moves PipeWire

1. **See it the same day.** `sparky-os/repo/watch-exact-pins.sh OUT PUBLISHED_PACKAGES...` (build repository) reads Debian testing's and unstable's signed indexes through apt in a container and runs `check-exact-pins.py` on every exact pin of the edition: a `FAIL testing` line names the package to rebuild, a `WARN unstable` line names the next move before it reaches testing.
   Run it inside an image of an installed edition (`BASE=`) so that the edition's other repositories (deb-multimedia, SparkyLinux) count, and give NVIDIA's source with `EXTRA_ROOT=` (from the published `sparky-stereo-cuda-repo`): otherwise the NVIDIA driver's pins on NVIDIA's own packages read as failures.
2. **Read what moved.** Debian's changelog since the old version, upstream's `NEWS` for every release between, and `diff -r` of `spa/plugins/bluez5` between the two upstream tarballs: `media-codecs.h` (the interface version), `codec-loader.c`, `meson.build`, `a2dp-codec-aac.c`.
3. **Build.** In a checkout with nothing uncommitted under `sparky-os` (the record then says `recipeDirty: false`; `SPARKY_PROVENANCE_REQUIRED=1` refuses a missing fact, not a dirty tree):
   `OUT=DIR SPARKY_LC_ARCHIVE_DIR=GATE SPARKY_BUILD_CONTAINER=NAME SPARKY_PROVENANCE_REQUIRED=1 build.sh NEW_UPSTREAM NEW_DEBIAN` (for example `1.6.11 1.6.11-2`), with `GATE/sources.json` naming Debian forky `main` and `non-free` and deb-multimedia's forky `main` and `non-free`, and beside it the two public keyrings (`debian-archive-keyring.pgp`, `deb-multimedia-keyring.pgp`).
   The plugin links the edition's FDK AAC, deb-multimedia's `libfdk-aac2` (the recipe takes only `fdk-aac` from deb-multimedia), so its Depends says `libfdk-aac2 (>= 1:3.0.0)` as the published one did.
   The recipe verifies Debian's `.dsc` with `dscverify`, builds only the AAC plugin with upstream's tests (51 of 51 on 1.6.11), writes the pin from the version it is given, and leaves the `.dsc` with its files, both `.deb` files, the buildinfo, the changes and the build record in `OUT`.
4. **Compare with the predecessor in the dated view.** The predecessor's exact libspa version is gone from the live archive, so the build's gate cannot solve it; run `lean.release check-link` with `--previous-dir` (the published `.deb`), `--previous-archive-config` (the same archives at a `snapshot.debian.org` timestamp before the predecessor's round was signed) and `--previous-published-at` (that round's Release `Date`).
   deb-multimedia has no dated signed index, so the gate also needs `--previous-archive-policy`, the hashed search evidence lean/archive.md describes (the publisher's step); without it it stops with `dated view is later than predecessor publication` for deb-multimedia's InRelease. Until then compare the two plugins directly: `readelf -d` (NEEDED `libfdk-aac.so.2`, `libc.so.6` in both) and `nm -D --defined-only` (the same four exports).
5. **Check the plugin with Debian's PipeWire.** `tests/aac-codec/run.sh OUT NEW.deb [PUBLISHED.deb]` (build repository), no Bluetooth device: apt installs the codec beside Debian's library, PipeWire's own Bluetooth monitor loads it, a 1 kHz tone survives the codec's encode and decode, and the decoder refuses a buffer smaller than a frame; the predecessor's rows are printed beside.
6. **Into the round** as a successor (take rows, the pool, case e on live Debian with the dated view beside it); edition-packaging's publication-round.md has the round's side.

## What the checks show (2026-11-26)

`tests/aac-codec/run.sh` on Debian testing's index of 20:15 UTC (PipeWire 1.6.11-2, deb-multimedia's `libfdk-aac2 1:3.0.0-dmo1`), no Bluetooth device, the checks offline:

| | published 1.6.9-2+aac2+lc1 | successor 1.6.11-2+aac2+lc1 |
|---|---|---|
| apt beside libspa-0.2-bluetooth 1.6.11-2 | refused: `Depends: libspa-0.2-bluetooth (= 1.6.9-2) but 1.6.11-2 is to be installed` | installed |
| PipeWire 1.6.11's Bluetooth monitor | `loaded media codec aac from api.codec.bluez5.media.aac, endpoint:aac` (interface 16 in both) | the same line, and `aac_eld` |
| 1.5 s of 1 kHz at 48 kHz, encoded (70 packets, 5367 bytes) and decoded | both channels: share at 1 kHz 1.0000, RMS 0.3534 (0.3536 expected) | the same |
| one frame (4096 bytes) decoded into 3000 bytes with a guard after it | accepted, wrote 4096 bytes: 1096 guard bytes changed | refused (-22), 0 guard bytes changed |

So the binary refusal of the old plugin comes only from its Depends (the interface did not change), and the decoder row is upstream's fix measured.
The monitor runs without a system bus: `load_media_codecs` runs before `spa_dbus_get_connection` in `bluez5-dbus.c`, so the codec lines are logged (`PIPEWIRE_DEBUG=spa.bluez5.codecs:4`) before the monitor stops; without our package the line reads `Bluetooth codec plugin api.codec.bluez5.media.aac not available`.

## Traps (symptom, cause, fix, how found)

- **The recipe stops at once: `/recipe/build-in-container.sh: line 6: python3: command not found`, exit 127.**
  Cause: since the source-date change of 2026-11-06 (ORDER 421b) the container script computed the changelog date with python3 on its sixth line, before it installs python3; a bare `debian:testing` image has none. The published build is dated 2026-10-20, before that change.
  Fix: compute `SOURCE_DATE_RFC2822` right after the `apt-get install ... python3` line. Found by: the first line of the build log.
- **The build ends in dh_builddeb: `check-link needs --archive-config / --scratch (or SPARKY_LC_ARCHIVE_CONFIG / SPARKY_LC_SCRATCH)`**, after upstream's tests passed.
  Cause: Lean Code's debhelper step now runs the link and start gate, which needs the public archive to solve the package's dependencies in a bubblewrap root.
  Fix: as command-not-found's recipe does, `build.sh` requires `SPARKY_LC_ARCHIVE_DIR` (mounted at `/archive`), runs the container with `--security-opt seccomp=unconfined --security-opt apparmor=unconfined --security-opt systempaths=unconfined`, and the container installs bubblewrap and hands `SPARKY_LC_ARCHIVE_CONFIG` and `SPARKY_LC_SCRATCH` to `dpkg-buildpackage` through `runuser ... env`. Found by: the last lines of the build log.
- **`previous edition dependency qualification failed; provide the matching previous sibling snapshot`**, `pipewire-bluez5-codec-aac : Depends: libspa-0.2-bluetooth (= 1.6.9-2) but it is not going to be installed`.
  Cause: with `SPARKY_LC_PREVIOUS_DIR` the gate solves the predecessor in the same live archive, where 1.6.9-2 is gone; adding a snapshot source beside the live one does not help (apt keeps `1.6.9-2 ... not selected for install`, because the rest of PipeWire 1.6.9-2 that it pins is not the candidate there).
  Fix: no predecessor in the build; the dated comparison of step 4 afterwards (the debhelper route does not pass `--previous-archive-config`). Found by: the solver's lines in the build log, then lean/archive.md's "A dated view for an archive transition".
- **The successor Depends `libfdk-aac2t64 (>= 2.0.1)` where the published codec said `libfdk-aac2 (>= 1:3.0.0)`**, and on an installed edition `apt-get -s install` of it adds `Inst libfdk-aac2t64 (2.0.3-1 Debian:testing)`.
  Cause: the version with an epoch exists only at deb-multimedia (`1:3.0.0-dmo1`, the FDK every installed edition has; Debian never had an epoch for fdk-aac), but the recipe never named that archive, so a build in plain Debian linked Debian's non-free library. Debian's `libfdk-aac2t64` `Replaces: libfdk-aac2` without a version and takes over `libfdk-aac.so.2`: two copies of one library, against the edition's rule of one.
  Fix: the build container adds deb-multimedia with its keyring from the gate's folder, pins everything of it at 100 and `fdk-aac libfdk-aac-dev libfdk-aac2` at 990; the gate's `sources.json` names deb-multimedia too. Found by: `dpkg-deb -f` of the new package against the published one, then `apt-cache policy libfdk-aac2 libfdk-aac2t64` and `dpkg -S libfdk-aac.so.2` on the case e base.
- **The record says `recipeDirty: true` although the recipe folder is committed.** Cause: the provenance helper reads `git status -- sparky-os`, and any uncommitted file anywhere under `sparky-os` counts; `SPARKY_PROVENANCE_REQUIRED=1` stops only on a missing fact, not on a dirty tree. Fix: commit (or move out) every change under `sparky-os` before the build.
- **The codec check prints its results, then exits 139; gdb shows a jump to address 0 with no frames.** Cause: PipeWire builds with `-DSPA_AUDIO_MAX_CHANNELS=128u` (its `meson.build`), and the plugin's `validate_config` runs `spa_zero(*info)` on a `struct spa_audio_info` of that size; a caller compiled with SPA's default of 64 channels has a smaller struct on its stack, which the plugin overruns by 256 bytes. Fix: compile anything that calls the codec with PipeWire's own value (`tests/aac-codec/run.sh` reads it from `meson.build`). Found by: the gdb backtrace, then the compiler line in the build log.
- **The stage has no build record.** Cause: the recipe copied `*.deb`, `*.buildinfo` and `*.changes` out of the container, not the `*.sparky-build.json` that `lean.release check-debs` writes beside them. Fix: copy it with them (the published 1.6.9-2+aac2+lc1 left no record in any stage). Found by: the closure list of the round's acceptance rule.
- **`${VAR:?the link gate's folder}` makes bash stop with "unexpected EOF while looking for matching `''"`.** An apostrophe inside a double-quoted `${...:?word}` opens a quote for bash's parser (another recipe's message has two, so it parses). Write the message without one.

## Upstream

- 1.6.11 carries Wim Taymans' "bluez5: avoid heap overflow in AAC decoder" (35b4d051d48e on the 1.6 branch, cherry-picked from 136fc59765f4): "aacDecoder_DecodeFrame expects the number of destination INT_PCM samples, not bytes. Since INT_PCM is int16_t (2 bytes), passing dst_size in bytes tells the decoder the buffer is 2x larger than reality." The edition's 1.6.9 plugin carries the old call; rebuilding on 1.6.11 brings the fix.
- Upstream tagged 1.6.12 on 2026-11-26; Debian had not packaged it that day. When it reaches testing the same rebuild is due.

## Not proven

- A real Bluetooth headset or speaker with AAC: every row here runs without a Bluetooth device (house rule; the codec's own encode and decode stand in for the radio).
