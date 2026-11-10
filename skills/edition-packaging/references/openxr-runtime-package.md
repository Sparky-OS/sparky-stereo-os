# Packaging an OpenXR runtime from its release tag (DisplayXR, ORDER 58)

Learned on DisplayXR 2.66.3, November 2026: an upstream program with no Debian package, built from its release tag with the edition's patches, through Lean Code, installed beside Debian's Monado, and proved on a headless Stereo KWin.
The packaging lives in [Sparky-OS/displayxr-packaging](https://github.com/Sparky-OS/displayxr-packaging) (reviewed by DisplayXR), the recipe in the build repository (`sparky-os/packages/displayxr-runtime/build.sh`).

## Recipe

1. **Read what upstream ships first.** Download the release `.deb`, check its SHA-256 against the digest the release lists (`gh api repos/OWNER/REPO/releases/tags/TAG --jq '.assets[].digest'`), and list it: `dpkg-deb -I`, `dpkg-deb -c`, `dpkg-deb -e` for the maintainer scripts.
   Read the script that makes it (DisplayXR: `scripts/package_deb_linux.sh`) and its CI job: the payload, its checks and the configuration it builds with are the reference.
2. **Find every download the build makes.** `git grep -n -E 'FetchContent_Declare|GIT_REPOSITORY|URL https|file\(DOWNLOAD'` over the CMake files, then the same in each fetched project at its pinned tag, following only the branches the build takes.
   Each fetched source becomes a source component of the package (`NAME_V.orig-COMPONENT.tar.xz`, unpacked in `COMPONENT/`), and the configure step points CMake at it: `-DFETCHCONTENT_SOURCE_DIR_<UPPERCASE_NAME>=$(CURDIR)/COMPONENT`. debhelper passes `-DFETCHCONTENT_FULLY_DISCONNECTED=ON`, so a source that is missing stops the configure instead of downloading.
   The recipe checks that the tag it carries is still the one the CMake file pins, so a new release that moves a pin stops the build with a message.
3. **Give the version a source.** A tree from `git archive` has no git metadata; a build that versions itself from `git describe` takes an override (DisplayXR: `-DDXR_RUNTIME_VERSION_OVERRIDE=vX.Y.Z`; the runtime then reports exactly the tag).
4. **Build the configuration upstream ships** (DisplayXR: `--hybrid`, Release, qwerty on, no debug GUI, no SDL), and **stage with upstream's own script** when it can reuse a build (`package_deb_linux.sh --no-build` with `BUILD_DIR` and `DIST_DIR`): the files, their places and its checks (the hybrid runtime, qwerty, the Wayland present path, the soname list) stay upstream's, and `debian/*.install` split the staged tree into packages. `dh_missing --fail-missing` proves nothing is left behind.
5. **A part that cannot be built from source in Debian** (DisplayXR's dashboard is a self-contained .NET 10 program; Debian has no .NET) is carried from upstream's release package as a source component (`orig-release`), its SHA-256 checked in `debian/rules` before extraction, in its own binary package, with a description that says so. Never strip it (`dh_strip -X`, `dh_dwz -X`): a .NET single-file bundle is appended to its ELF host.
   To know what such a bundle carries, read its manifest: `scripts/netbundle.py BUNDLE` lists the files, `scripts/netbundle.py BUNDLE NAME.deps.json` prints the package list with versions; each NuGet package's licence is in its `.nuspec` (`https://api.nuget.org/v3-flatcontainer/ID/VERSION/ID.nuspec`).
6. **debian/copyright file by file** from the tree's own SPDX tags: `reuse lint --json` on each source tree (Debian's `reuse`, in a container), then `scripts/reuse2dep5.py LINT_JSON PREFIX DEFAULT_LICENCE HOLDERS_FILE` writes the Files paragraphs (a folder becomes `FOLDER/*` when every file in it has one licence).
   Then list the files REUSE gives the default licence although they carry a licence of their own: `python3 -c` over the JSON for files with copyrights but no `spdx_expressions`, and `licensecheck -r` as a second reader. Write those paragraphs by hand from each file's text.
7. **Source package and build:** `release/build-dh-lean.sh WORK SOURCE VERSION+lc1 REPO` builds the authored source, the Lean Code source and the packages, and runs the gate; it carries the component tarballs since ORDER 58.
8. **Prove the installed package** in a rig image made by installing the staged `.deb` files with apt (their maintainer scripts run), then run the program with no runtime, plug-in or output setting given: the loader and the runtime must find everything where the package put it.

## An OpenXR runtime beside others

- **The loader's rule** (OpenXR loader specification, "Linux Active Runtime Location"): `XR_RUNTIME_JSON` for one program, else `openxr/1/active_runtime.<arch>.json` or `active_runtime.json` under `$XDG_CONFIG_HOME`, then each of `$XDG_CONFIG_DIRS`, then `/etc`; the first found wins.
  "Linux Installed Runtimes Enumeration": a runtime installs its manifest in one of those directories, and "Tools that want to change the current active runtime should only update the `active_runtime.<arch>.json` and/or `active_runtime.json` symlink to the active runtime, and not move, copy, or delete any other files."
- **Debian's Monado owns that link through update-alternatives**: group `openxr1-active-runtime`, link `/etc/xdg/openxr/1/active_runtime.json`, its manifest `/usr/share/openxr/1/openxr_monado.json`, priority 50 (its postinst; the edition's Monado build keeps it).
  Another runtime joins the same group (`update-alternatives --install LINK openxr1-active-runtime MANIFEST PRIORITY` in postinst, `--remove` in prerm on remove and deconfigure). Then `update-alternatives --config openxr1-active-runtime` lists both, a choice made by hand is kept across upgrades, and removing one hands the link to the other.
- **Per person:** a link at `$XDG_CONFIG_HOME/openxr/1/active_runtime.json` to a manifest overrides the system's choice for that person; deleting it returns to the system's. **Per program:** `XR_RUNTIME_JSON=MANIFEST`.
- The manifest in `/etc/xdg/openxr/1/` is a conffile: a person who deletes it keeps it deleted, so the postinst checks that it exists before `update-alternatives --install` and says how to restore it when it does not.
- Which runtime is active in automatic mode is the priority: a default, so it goes to the design (memory, Daniel), never chosen by the packager alone.

## One output in the edition's build

The edition's contract: a program hands Stereo KWin full side by side, declared, and KWin's outputs make every display format.
For a runtime with display processors, the simulated one is the program's own output: build it with only 2D and full side by side (DisplayXR: `XRT_SIM_DISPLAY_FULL_SBS_ONLY=ON`, patch 0008 of the packaging), so the other outputs' shaders are not compiled and their modes are not offered.
Check it three ways: `strings` on the plug-in finds the build's own log lines ("2D and full side by side only"), the runtime's log at start says so, and a request for another output (`SIM_DISPLAY_OUTPUT=anaglyph`) logs that it is not built and stays full side by side, declared.
Vendor display processors (a glasses-free panel's weaving) are display drivers behind the runtime and stay as their vendors ship them.

## Traps

- **Symptom:** after installing DisplayXR's own release `.deb` on a machine with Monado, `dpkg --verify libopenxr1-monado` reports `??5?????? /usr/share/openxr/1/openxr_monado.json`; after removing DisplayXR no OpenXR program starts (the loader reads `/usr/lib/displayxr/lib/openxr_displayxr.so`, which is gone).
  **Cause:** the postinst ran `cat > /etc/xdg/openxr/1/active_runtime.json`, and that path was Monado's alternatives link, so it wrote into Monado's packaged manifest; its "backup" was a copy of the link.
  **Fix:** join the alternatives group instead (above); a fix for DisplayXR's own `.deb` was drafted with this test.
  **How found:** a container installing the edition's Monado, then the release `.deb`, printing `ls -l /etc/xdg/openxr/1`, the alternatives state, the `library_path` the loader would read and `dpkg --verify`, in both install orders and after a removal.
- **Symptom:** `update-alternatives: warning: not replacing /etc/xdg/openxr/1/active_runtime.json with a link` when Monado is installed after a runtime that wrote a plain file there; Monado can never be chosen.
  **Cause and fix:** as above; a postinst that finds a plain file naming its own library replaces it by the link, and leaves a plain file naming another runtime with a message.
- **Symptom:** `update-alternatives: error: alternative path /etc/xdg/openxr/1/openxr_displayxr.json does not exist`, the package left unconfigured.
  **Cause:** the manifest conffile was deleted while the package was removed but not purged; dpkg keeps a deleted conffile deleted on the next install.
  **Fix:** check for the manifest in the postinst and say how to restore it (`--force-confmiss`). **How found:** a test that deleted `/etc/xdg/openxr` between two cases.
- **Symptom:** the build reaches the network during the configure (or fails offline) although the source package is complete.
  **Cause:** `FetchContent_Declare` with `GIT_REPOSITORY` in the project's CMake files (DisplayXR: displayxr-mcp in the top-level file, displayxr-common in `src/xrt/auxiliary/math`).
  **Fix:** source components and `FETCHCONTENT_SOURCE_DIR_*` (recipe step 2). **How found:** reading the CMake files with `git grep FetchContent_Declare`, then the configure log of the build (`-- Populating ...` must not appear).
- **Symptom:** a trial build with `DEB_BUILD_OPTIONS=nocheck` and a later `ctest` say "No tests were found".
  **Cause:** under `nocheck` debhelper configures with `-DBUILD_TESTING:BOOL=OFF`. **Fix:** run the test suite from a build configured without `nocheck` (or reconfigure the tree with `-DBUILD_TESTING=ON`).
- **Symptom:** a test fails in the package build. Before excluding it, build the same test from the unpatched release with the same flags in the same container and run it three times: DisplayXR 2.66.3 has four tests that fail the same way there (`tests_mirror_calib`, `tests_component_loader`, `tests_service_orchestrator_linux`, `tests_tracking_host`) and one that passes and fails on both builds under load (`tests_desktop_control`), which `ctest --repeat until-pass:3` absorbs. Name each excluded test and why in `debian/rules`.
- **Symptom:** the edition's provenance step appended a second `Files: debian/*` paragraph under GPL-2+ to a packaging published under BSL-1.0.
  **Cause:** `repo/provenance.sh` wrote its credit paragraph with GPL-2+ for every package. **Fix:** write the packaging's own paragraph last, in the provenance shape (`Files: debian/*`, then `Comment: Sparky Stereo OS packaging. ...`, `Copyright:`, `License: BSL-1.0`); since ORDER 58 provenance.sh keeps that licence.
- **Symptom:** a container test of the edition's Monado (or anything depending on libheif) does not install: `libheif-plugin-aomdec ... Depends libaom3 (>= 1:3.15.2) but none of the choices are installable`.
  **Cause:** the edition's libheif is built on deb-multimedia; the lane 34 rig image has no deb-multimedia source. **Fix:** add `deb [signed-by=KEYRING] https://www.deb-multimedia.org forky main non-free`, as an installed edition has it.
- **Symptom:** REUSE puts the vendored Wayland protocol XML, a vendored cJSON and stb headers under the project's own licence.
  **Cause:** those files have no SPDX tags, only their licence text. **How found:** the list of files with copyright lines and no `spdx_expressions` in `reuse lint --json`.
- **Symptom:** the recipe's check that the runtime still fetches the tag it carries failed on a tree that does.
  **Cause:** the pin line was `GIT_TAG v0.5.6)` with the closing parenthesis. **Fix:** match `^[[:space:]]*GIT_TAG TAG\)?$`, and test the check with a wrong tag once.

- **Symptom:** the installed `displayxr-dashboard` exits 1 at once, prints nothing and writes no log, while `displayxr-dashboard --version` works.
  **Cause:** not determined; it happened only with `DOTNET_BUNDLE_EXTRACT_BASE_DIR` pointed at the session's runtime directory (a tmpfs). **Fix:** leave it unset (the bundle extracts to `~/.net`); the window then opens on Xwayland ("DisplayXR Dashboard", 1280x820) and shows the active runtime the alternatives link resolves to. **How found:** `strace -f -e trace=mkdir,exit_group` in a container without the variable got further and logged to `/tmp/DisplayXR/`.
- **Symptom:** `apt-get install` of the runtime with its Recommends installs no KWin window-geometry publisher in a rig image.
  **Cause:** the publisher depends on its exact KWin version; on an image whose KWin is a staged build (not the published one) apt cannot satisfy it and drops the Recommends. On the published edition (`apt-get -s`) apt picks `displayxr-window-geometry-publisher-kwin`.
- **Symptom:** a capture of Debian's own KWin (no stereo announcement) passed the LEFT/RIGHT colour rule.
  **Cause:** that KWin answers ScreenShot2 with one picture (`stereo 0`), and the rule split it in two halves, which hold the two squeezed views in red and blue. **Fix:** check such a control with `--expect flat-single` and read the capture's `stereo` flag and the geometry check, which fails (the views are half as wide).
- **Symptom:** a rig image named in a brief is gone (`pull access denied for openxr-target-34-rig`).
  **Cause:** the lane cleaner removes an accepted lane's images. **Fix:** build lane images on an image that is still there and say which KWin it carries.

## A program's failure through the problems engine (a C or C++ program, ORDER 58b)

Rule (memories no-silent-fallbacks, problems-engine-350): a reason that reaches only a log is a silent fallback; the package hands it to sparky-stereo-problems, never a notifier or a store of its own.
DisplayXR's runtime, when it cannot declare its window to the desktop (no announcement, a window it does not declare, a build without wayland-scanner), shows the two views flat and used to say why in its log only.

**Recipe, in the order it worked:**
1. **Say what the failure is and who meets it.** One key per thing that stops working (`declare`), the person's scope (`SSP_PERSON`: the program runs as the person), one message per cause in `debian/lang/{en,pl,pt_BR,fr,de,ja,ko,zh_CN,zh_TW}` (`LOCAL1` the title, `LOCAL2..` the causes, one `%s` for the program's own words at the end of the sentence, never inside it, because a detail in brackets mid-sentence reads badly in nine languages). A cause the person chose (an environment switch that turns the feature off) keeps nothing.
2. **Call the C ABI from the program with `dlopen`**, not a link: the library is private (`/usr/lib/MULTIARCH/sparky-stereo-problems/libsparky-stereo-problems.so.0`, path from `pkg-config --variable=libdir sparky-stereo-problems`, given to the compiler as a define), so a link adds a DT_NEEDED and RPATH to a library every other program loads (DisplayXR's packaging script checks DT_NEEDED against a list of sonames and would refuse it). `ssp_keep(SSP_PERSON, package, key, "LOCALn", args, 1, details)` with `{"text_en": "..."}` in the details for a machine without the catalog, `ssp_clear(SSP_PERSON, package, key)` when it works.
3. **An engine that is absent is said**: an ERROR line when there is something to tell ("the person cannot be told"), an INFO line when the call only wanted to end an old problem. Never a quiet return.
4. **Behind an option that is OFF upstream** (`DXR_SPARKY_PROBLEMS`): a configure that asks for it and does not find the engine fails (`pkg_check_modules REQUIRED`), the source keeps its other builds as they were, and the patch carries `Forwarded: not-needed`.
5. **The package:** `Build-Depends` and `Depends` on `sparky-stereo-problems (>= 0.1.2)` (amd64 only: the engine is, so on other architectures the reason stays in the log and the build record says so); `sparky-stereo-problems catalog PACKAGE debian/lang debian/PACKAGE/usr/lib/systemd/catalog --subject LOCAL1` in `execute_after_dh_install` (make the folder first); a postrm that runs `sparky-stereo-problems clear --all PACKAGE` on remove and purge when the command exists.
6. **The proof, red and green, in the rig** (stereo-proof-rig): the same case on a desktop that announces nothing (Debian's own KWin image), once with the previous package (the log has the reason, `sparky-stereo-problems list --json` is `[]`: red) and once with the new one (the record is listed, in the person's language with `LC_ALL=pt_BR.UTF-8`; started again it is still one record with the same `first`: said once), then on Stereo KWin with the same HOME (the window is declared and the record is gone: cleared). A unit run of the program's own source file in a container (harness: keep, keep again, other cause, ok, ok on an empty store, engine absent, option off) takes seconds and catches what the rig takes minutes to show.

**Traps (symptom, cause, fix, how found):**
- **Symptom:** the window is declared and the earlier problem is still listed. **Cause:** the first version cleared only a problem its own process had kept (a static flag "so a start that never failed does not call the engine"); the program that failed was an earlier process. **Fix:** clear on every declared start (`ssp_clear` ends nothing that is not there), only the engine's absence changes to INFO. **Found:** the green case on Stereo KWin listed the record from the Debian KWin case before it.
- **Symptom:** a native Wayland window on a desktop with no stereo global is told as "the declaration could not be made" (the catch-all message) and not as "the desktop announces nothing". **Cause:** the program's reasons were free English sentences and the kind was chosen by `strstr` on one of them; the pattern said "offers kde_stereo_content_manager_v1" and the sentence says "offers no kde_stereo_content_manager_v1". **Fix:** match the part both sentences share, and run every cause once in the rig, not only the first one. **How found:** the second green case (Wayland on Debian's KWin) listed LOCAL5 where LOCAL2 was expected. A cleaner way, where the program's code allows it, is to return the kind from the place that makes the sentence.
- **Symptom:** the record shows the reason twice, in the sentence and in brackets, and a translated sentence has a hole in the middle. **Cause:** the program's English reason passed as `%s` inside the sentence. **Fix:** the program's words go last ("DisplayXR says: %s").
- **Symptom:** `LANGUAGE=pt_BR sparky-stereo-problems list` answers in English in the rig. **Cause:** the rig's locale is C.UTF-8, where the engine does not read LANGUAGE. **Fix:** `LC_ALL=pt_BR.UTF-8`.
- **Symptom:** the build container is refused by the lane's Docker proxy. **Cause:** `release/build-dh-lean.sh` named its container `lean-dh-...`, with no prefix. **Fix:** `SPARKY_CONTAINER_PREFIX` (ORDER 58b).
- **Symptom:** a script that stops the build kills the shell that runs it. **Cause:** `pkill -f` on a pattern that is also in the shell's own command line. **Fix:** `pgrep -af` first and `kill PID`.

## Perks

- DisplayXR's packaging script refuses a build that lost a feature silently (no hybrid runtime, no qwerty, no Wayland present path, a soname outside its list), so reusing it brings those checks into the Debian build for free.
- `XR_LOADER_DEBUG=info` makes the OpenXR loader log every place it looked and the manifest it loaded: the cheapest proof of which runtime a program got.
- The runtime's log names the reason for every stereo decision (`FULL_SBS: ...`), so a case that did not declare says why.

Credits: DisplayXR by David Fattal and its contributors; Monado by Collabora and its contributors, which DisplayXR derives from; Monado's Debian packaging by its maintainer; the OpenXR loader specification by the Khronos Group.
