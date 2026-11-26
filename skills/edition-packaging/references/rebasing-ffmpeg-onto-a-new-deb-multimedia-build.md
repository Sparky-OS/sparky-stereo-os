# Rebasing the edition's FFmpeg onto a new deb-multimedia build

**For whoever moves the edition's FFmpeg series to a newer `ffmpeg-dmo` from deb-multimedia**, a new Debian revision (`-dmoN`) or a new FFmpeg release.
Written on 2026-11-26 from queue row 916, which moved the series of `10:9.0.2-dmo1+stereo3d17` onto `10:9.1-dmo1` (FFmpeg 9.1) as `10:9.1-dmo1+stereo3d18`.
The patch-only recipe for one more fix on the same base is [rebuilding deb-multimedia's FFmpeg as ours](rebuilt-ffmpeg.md); this page is for a new base.

## Why it is due as soon as deb-multimedia moves

The link gate (`lean.release check-link`) pins only the packages it is given; every other package resolves from the archives by version ([archive.md](https://github.com/Sparky-OS/sparky-stereo-os-build/blob/main/sparky-os/lean/archive.md), `write_exact_pins`).
So once deb-multimedia publishes an FFmpeg that sorts above ours, a clean gate root installs deb-multimedia's libraries for every program that links FFmpeg, and the programs that call the edition's own symbols (`av_multiview_*`, the side data types) fail there unless our FFmpeg is fed in as a sibling.
The fix is our FFmpeg on deb-multimedia's current base, versioned so it sorts above it.

## Recipe

1. **Read deb-multimedia's index on the day, not the version a brief names.** In a container with deb-multimedia's keyring, `apt-cache madison ffmpeg-dmo libavcodec63` over `forky` and `sid`. On 2026-11-26 the brief said 9.0.2-dmo5; both suites carried only 10:9.1-dmo1 (uploaded 2026-11-21), and a dmo5 base would have sorted below it.
2. **Fetch through the signed index** (`apt-get source ffmpeg-dmo=VERSION`) and check the upstream tarball against FFmpeg's release key, which deb-multimedia ships as `debian/upstream/signing-key.asc` (`gpg --dearmor`, then `gpgv --keyring key.gpg orig.tar.xz.asc orig.tar.xz`; fingerprint FCF9 86EA 15E6 E293 A564 4F10 B432 2F04 D676 58D8).
3. **Diff deb-multimedia's packaging from the old base to the new** (`dpkg-parsechangelog --since OLD`, `diff -u` of `control`, `rules`, the install files, the series). Take it whole, then check every option it dropped against the new source before accepting the loss (9.1-dmo1 dropped `--enable-opengl`, already a no-op, and its xfade easing patch, a real feature: kept, below).
4. **Put the old series in git as one commit per patch**, on the old base, and the new base beside it in the same repository (`rebase-setup` in the lane: orig tarball, deb-multimedia's own first patch, then `patch -p1 -F0 --no-backup-if-mismatch` and one commit per file name). Check the tip equals the old source unpacked (`git ls-tree -r` against `git hash-object` of every file).
5. **`git rebase --onto NEWBASE LAST_DMO_PATCH BRANCH`**: git's three-way merges place most context moves themselves. Resolve each stop by kind, and log every decision:
   - both sides only added lines at the same place: upstream's, then ours;
   - ours only added lines next to a line upstream changed: our lines, then upstream's new line;
   - a `version.h` block: upstream's number plus our patch's own step (a minor bump stays a minor bump, micro back to 100);
   - **an enum whose values the edition already published** (`AVFrameSideDataType`, `AVPacketSideDataType`, `AVStereo3DType`): **our entries first**, upstream's new ones after them (below);
   - anything else by hand, with the upstream commit that changed the code read first.
6. **Write the patch files from the commits, keeping each original header.** A patch is carried "as is" only when the original file, applied without fuzz to its commit's parent (`GIT_INDEX_FILE` set to a temporary index, `git read-tree PARENT`, `git apply --cached`, `git write-tree`), gives exactly the commit's tree; then copy the file byte for byte. Otherwise regenerate the diff and add one dated line under the header: the context moved, or what was ported and why. Comparing hunk texts instead misjudges a patch whose diff git happens to align differently.
7. **Make the source from inputs named by sum**: deb-multimedia's `.dsc` and the published `+lc1` `.dsc` (for the changelog history and the Lean Code preserve plan), checked against a `sources.sha256` in the recipe folder; apply the edition's control and rules changes each exactly once (stop otherwise); put the edition's history between deb-multimedia's new stanzas and the old base's stanza, where the versions still sort (`9.0.2-dmo2` > `9.0.2-dmo1+stereo3d17` > `9.0.2-dmo1`). Make it twice under two zones and umasks; the sums must match. Unpack it with its patches and compare with the rebased git tree file for file.

8. **Before the first package build, compile the rebased tree once with `make -k`** (trap table: `mov_read_auxc`), so every error of the new release shows in one pass.
9. **Build amd64, then the i386 twin from the same `.dsc`** (`build-twin-i386.sh`, with the cohort's i386 x265 packages as inputs), and compare each with the build it replaces: exported symbols per library (none may leave: `exports-compare.sh`), `dpkg-deb -c` per package (`filelists-compare.py`: only build IDs, the versioned `.so` names and content-addressed Lean Code companions may change), and every path the two architectures of a `Multi-Arch: same` package share (`ma-same-compare.py`: identical bytes). On +18: no export lost on either architecture (libavcodec +21, libavfilter +1, libavformat +2, libavutil +14 on amd64 and +13 on i386), 53 packages as on +17, 23 `Multi-Arch: same` packages with identical shared paths.

## The published enum values (FFmpeg 9.1)

FFmpeg 9.1 added `AV_FRAME_DATA_DOWNMIX_MATRIX` (37) and `AV_FRAME_DATA_GAIN_MAP_PARAMS` (38) to `AVFrameSideDataType`, and `AV_PKT_DATA_GAIN_MAP_PARAMS` (43) to `AVPacketSideDataType`: the very numbers where the edition's +15 put `AV_FRAME_DATA_MULTIVIEW_SCENE_INFO` and its neighbours, and `AV_PKT_DATA_MULTIVIEW_SCENE_INFO`.
Every program built against +15 to +17 (players, editors, the stereo layer, HandBrake) has those numbers compiled in.
So the edition's entries keep their values and upstream's three new ones come after them; nothing the edition built changes meaning, and a binary built against deb-multimedia's 9.1 headers that uses one of the three new types reads another number on the edition.
Count the entries of each enum in the old base, our last build and the new base before resolving anything (`awk '/^enum NAME/,/^};/'`), and prove the result with a small program that prints every enumerator of the old build's header in both builds.

Measured on +18 against +17 (lane script `enum-values.py`, 122 enumerators of `AVFrameSideDataType`, `AVPacketSideDataType`, `AVStereo3DType`, `AVStereo3DView` and `AVStereo3DPrimaryEye`): every value equal but `AV_PKT_DATA_NB` (53 to 54, which the header says is not ABI); 9.1's three new types at 48, 49 and 53.

**FFmpeg 9.1 names every packet side data type** (`FF_PACKET_SIDE_DATA_HANDLES` in `libavcodec/packet_internal.h`, read by the new `side_data` bitstream filter; the `packet-side-data-handle` test fails on any type without a handle). Each edition patch that adds a packet type adds its handle there and the test's reference in the edition's numbering; without them the filter cannot name the edition's ten types.

## FATE: the whole suite on three builds

Run the recipe's `fate.sh` on the old edition build, deb-multimedia's new build and ours, with the merged samples (lane script `full-fate.sh`), and explain every failure by its first lines before counting it. Row 916, 26 November 2026:

| Build | Tests executed | Failed |
|---|---|---|
| +stereo3d17 (9.0.2) | 5621 | 23 |
| deb-multimedia 10:9.1-dmo1 | 5885 | 3 |
| +stereo3d18 (9.1) | 6152 | 22 |

- The 3 that fail everywhere are the frei0r tests: the FATE image has no frei0r plugins ("Could not find module 'distort0r'").
- Not run on every build: the 33 `scale_cuda` tests, `hwcontext-cuda` and `hwdevice` (no CUDA device in the container); on ours also the five `seek-acodec-*` tests, which read the output of the failed `acodec-*` tests.
- The other 19 are HandBrake's FFmpeg patches doing what they are for, with FATE references nobody updated (HandBrake does not run FATE). Read with `box-diff.py` (lane script: the MOV and MP4 box trees of both builds' outputs; FATE deletes the output of a passing test, so where only ours survives, list its boxes):
  - hb-A24 (version 2 sound description for PCM; no `chan` box for AAC and ALAC): `acodec-pcm-s8`, `-s16be`, `-s24be`, `-s32be` (deb-multimedia writes `sowt`, `twos`, `in24`, `in32`, ours `lpcm`), `acodec-alac`, `mov-channel-description`, `copy-trac236`, `adtstoasc_ticket3715`, `filter-meta-4560-rotate0`;
  - hb-A06 (more iTunes tags read and written): `caf-alac-remux`, `cover-art-flac-remux`, `matroska-alac-remux` (`TAG:tmpo=0`), `generic-tags-remux-mov` (`TAG:publisher`), `mov-cover-image` (a `tmpo` atom written back), and FFmpeg 9.1's new `mov-cover-reenc-keeps-audio-format-tags` and `mov-reenc-delete-format-metadata` (`TAG:tmpo=190`);
  - hb-A02 and hb-A04 (3GPP `titl` and `name` per track): `mov-mp4-chapters`;
  - hb-A08 to hb-A10 (DVD subtitle packets and their timestamps): `sub2video`, `sub2video_basic`, about 9 ms later or earlier.
- The edition's own tests are all green on +18: 66 of them, plus the two upstream tests the edition's patches change (`packet-side-data-handle`, the AVIF alpha grid); three had failed on +17 with stale references.

## The gate without siblings (row 916's purpose)

Run `lean.release check-link` on a consumer's packages with only the public archives, the published tree and the stage as signed archives (lane script `gate-nosiblings-in-container.sh`: the stage indexed with `apt-ftparchive` and signed with a throwaway key; no `SPARKY_LC_SIBLINGS_*`, no `SPARKY_LC_PREVIOUS_DIR`), and the same without the stage as the red row:

| Candidate | With the stage | Without it |
|---|---|---|
| mpv-dmo 1:0.41.0-dmo9+stereo3d12 | passes (4 packages), `libavutil61 10:9.1-dmo1+stereo3d18+lc1` from the stage | fails: `undefined symbol: av_multiview_real_to_double, version LIBAVUTIL_61` (deb-multimedia's 9.1 resolved) |
| MLT 7.40.0-1+stereo3d13 | passes (13 packages) | needs stereo-layer 1.23.2 from the stage; with the stage minus its FFmpeg it also passes on deb-multimedia's 9.1 |

The gate checks symbols at load. MLT calls no edition-only FFmpeg symbol, but it is built against the edition's side-data numbers, which deb-multimedia's 9.1 gives to other types: that mismatch loads cleanly and is invisible to the gate. Read a green row together with the enum proof above.

## Traps

| Symptom | Cause | Fix, and how it was found |
|---|---|---|
| `plain-from-lc.py` stops: `AssertionError:   * Import the HandBrake ...` | the `+lc1` entry holds the edition's own items (a `dch --newversion` on an UNRELEASED entry) | `--edition-entry`; found in the assertion's text |
| A rebased tree carries `*.orig` files | GNU `patch` keeps a backup whenever a hunk lands at an offset, and `git add -A` commits it | `patch --no-backup-if-mismatch`; found by comparing the series tip with the unpacked source |
| `git cherry-pick -q` prints the usage | `cherry-pick` has no quiet option | leave it out |
| A pickaxe or path-limited `git log` on a `--filter=tree:0` clone runs for minutes | each commit's tree is fetched lazily over the network | subject searches only (`git log --format=%s A..B`), `git diff A B -- PATH` between two tags, `GIT_NO_LAZY_FETCH=1` for existence checks |
| `cat-file -e HASH` takes minutes and fails with "not our ref" | a hash the clone lacks is asked of the server | `GIT_NO_LAZY_FETCH=1`; a treeless clone holds every commit, so a missing one is not upstream's |
| A conflict marker was committed in the middle of a rebase | a helper failed and the command went on with `;` to `git add` | `&&` between a resolver and `git add`; a `fixup!` commit, then `rebase -i --autosquash` with the tree compared before and after |
| `git checkout --conflict=diff3` shows more blocks than the merge did | the default style merges zealously; diff3 shows every overlap with its base | resolve all blocks it shows |
| `debian_prepare`: "Source preservation needs unique safe relative patterns" | the carried plan already names the file, and the call names it again | pass the published plan alone (`carried_plan=`) |
| `os.symlink` of the orig tarball: File exists | `dpkg-source -x` links the orig tarballs beside the tree it unpacks | link only what is missing |
| The package build stops: `error: redefinition of 'mov_read_auxc'` | the new release added its own reader for a box an edition patch also reads; both sides only added lines, so the merge kept both | one reader with both sides' work (the edition's parsing, upstream's flags with upstream's matching), and one parse-table entry; before a second package build, compile the rebased tree with `make -k` once (`dpkg-architecture -c fakeroot debian/rules override_dh_auto_configure`, then `make -k -j4`) to get every error in one pass |
| `--cc=-gcc` and "C compiler test failed" when running `debian/rules override_dh_auto_configure` by hand | `DEB_HOST_MULTIARCH` and `DEB_HOST_GNU_TYPE` are empty outside `dpkg-buildpackage` | `dpkg-architecture -c fakeroot debian/rules TARGET` |
| Half of the edition's FATE tests fail with "No such file or directory" under the samples folder | the edition's own samples (depth SEI, multilayer, AuxId) are not in FFmpeg's fate-suite; earlier lanes kept them in their folders | a merged sample folder of symlinks (FFmpeg's suite first, then the edition's sample folders), mounted read only at the same paths; list each test's first error line from its `.err` before counting it |
| `fate-*-frame-packing-persistence` prints `frame` where the reference says `frame\|` | FFmpeg 9.1's compact writer assembles a row in a buffer and writes no separator for a row without fields (42b8f75a6b, Kacper Michajłow) | the frames that carry the side data are unchanged; take the new reference with the reason in the patch header |
| A test's `-show_entries stream=...` output lost the streams nested in a program | FFmpeg 9.1 prints program streams only when selected by name (88f7fd9ec5, cuptu: `program_stream`) | the top-level streams carry the same side data; take the new reference, or select `program_stream` too |
| `fate-packet-side-data-handle` prints `43: (none)` to `53: (none)` | FFmpeg 9.1 names each packet side data type in `FF_PACKET_SIDE_DATA_HANDLES` and the test prints every type below `AV_PKT_DATA_NB`; the edition's types had none | each patch that adds a packet type adds its `HANDLE()` line and the test's reference in the edition's numbering (lane script `fixup-handles.py`, as `fixup!` commits, then `rebase -i --autosquash`) |
| `fate-mov-avif-demux-still-image-alpha-grid` shows two more fields on the alpha tiles | the edition's AuxId export (0035) and ffprobe's printing of it (0037) apply to FFmpeg 9.1's new AVIF alpha grid test too | the reference takes `aux_id=1` on the alpha tiles, in 0037 |
| FATE of deb-multimedia's own build fails 5234 of 5434 tests: `libfdk-aac.so.2: cannot open shared object file` | deb-multimedia builds with Fraunhofer's libraries; the edition's FATE image (built for ours) does not have them | install `libfdk-aac-dev libfdk-xhe-aac-dev` in the FATE container for that run (`EXTRA_PKGS` in `full-fate.sh`); then 3 fail |
| The i386 twin compiles, then `override_dh_builddeb` stops: `ffmpeg-dbgsym_..._i386.deb: already exists; never replace a published version` | the twin's work folder still held the packages of an earlier build of the same version (a source changed after it); the Lean Code step refuses to overwrite a package | before rebuilding a version, remove that version's packages, `tree/` and `link-scratch/` from the work folder, keeping `previous/`, `siblings.txt` and the cohort's input packages |
| A test container that installs `sparky-stereo-apt` fetches indexes from `repo.sparkyos.org`, and the station answers with a local address (`[IP: 192.168.0.60 443]` in apt's errors) | the package ships `sparky-stereo.sources` for the edition's repository host, which the station's `/etc/hosts` maps to a machine on the local network, so the container reaches that machine, which a lane must not | after installing the package, remove `/etc/apt/sources.list.d/sparky-stereo.sources` (the published tree is already mounted as `file:/repo`) and give `docker run` `--add-host NAME:127.0.0.1` for every local name in the host's `/etc/hosts`; grep the logs for `192.168.` afterwards. Found by row 916's own fdk proof, which broke the rule once |
| `sparky-stereo-ffmpeg-fdk` builds for 25 minutes, then stops at its link check: `certificate verify failed` for every archive | a bare Debian image has no `ca-certificates`; the rig's apt reads a mounted CA file, but the tool's own link check uses the system store | install `ca-certificates` in the rig, as every person's machine has it |
| `sparky-stereo-ffmpeg-fdk` builds every package as `+fdk1`, then stops: `isolated execution unavailable: bwrap: No permissions to create a new namespace` | the tool's Lean Code link check runs programs in bubblewrap, and Docker's default profile refuses new user namespaces; a person's Debian allows them | the lane's gate containers run with `--security-opt seccomp=unconfined --security-opt apparmor=unconfined --security-opt systempaths=unconfined`; row 916's permission system refused adding the same options to the fdk proof's container, so whether a proof container may have them is the main session's decision, and that proof stops here |
| 46 patch headers say `Origin: upstream, https://git.ffmpeg.org/...` with a hash FFmpeg does not have | the +15 header rewrite labelled fork commits as upstream | check every such hash in a clone of FFmpeg (`GIT_NO_LAZY_FETCH=1 git cat-file -e`); only three were FFmpeg's, two of them unmerged pull-request heads |
