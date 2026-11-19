# A maker's program that has no source

**For** a maintainer who must ship a program its maker publishes only as binaries (no source the edition can build, a licence that allows redistribution or not), for a device the maintainer does not own.
First built for SenseGlove's SenseCom and C++ API (ORDER 40, app center 0.1.19).
Read with [edition-packaging](../SKILL.md), [an app center entry that needs tools](app-center-entry-tools.md) and [licensed data at install time](licensed-data-at-install.md).

Check freshness first: measured on 2026-11-19 against SenseCom 1.9.2 (commit dbfd4266f040) and SenseGlove-API commit 31900b320aa0.
Recheck the maker's repositories before reusing a pin.

## The rule

What has source is an edition package built from source by the edition's route.
What has none is fetched from the maker, on the person's machine, by the app center entry the person chooses: pinned by address and SHA-256, its licence shown, never rebuilt, modified or mirrored.
The maker's own updater is neither run nor removed; the installed copy is the pinned one, and a newer version arrives by a newer pin.

## Working recipe

1. **Split the maker's tree by what has source.** In SenseGlove's API, the 61 headers, the example and the licence are source: package them (`senseglove-api-dev`, built from the files fetched at build time and checked against a committed `sources.tsv` of size and SHA-256). The two libraries have no source: they are the entry's.
2. **Find the exact bytes the person will get.** Releases may carry no assets (SenseCom's releases carry none; the download is a folder of the git tree). Read the tree at a commit (`api.github.com/repos/OWNER/REPO/git/trees/COMMIT?recursive=1`), keep `truncated: false`, and take size and mode from it; take the SHA-256 of each file from the bytes (the tag archive once, in scratch, never in a repository or the stage).
3. **Pin file by file, not the archive.** SenseCom's tag archive is 235 MB (Windows, Android and Linux builds together) for a Linux tree of 186 MB, of which the maker's own tree holds the 33 MB Unity player twice (in the updater's folder): fetching the Linux files at the commit from `raw.githubusercontent.com` and each different content once is 101.5 MiB. The pin is a JSON file in the app center (`stereo/vendor/NAME.json`: `base` address at the commit, then for each file `src`, `dest`, `size`, `sha256`, `mode`), and the catalogue row carries that file's own SHA-256, so a changed list is refused before any download.
4. **The row's kind is `tree`** (`stereo/vendortree.py`): licence fetched first and printed; one `curl --fail-early --proto =https` for every different file; each checked for size and SHA-256; the tools the entry declares installed; everything placed at once (staged next to the target and renamed), then the links and the menu entry; a folder that is not ours is never replaced; a failed re-install leaves the first one untouched.
5. **The card says, before the button:** size, address, the commit, the list's SHA-256 (first 16 hex), the licence and its holder, what the program is and what it needs; on a metered connection the shared notice says the size first. Say what the program cannot do on this system: SenseCom's own Linux README says it is "not yet compatible with Nova Gloves", and the card says so.
6. **Every failure is said in the ten languages and installs nothing:** a file that does not match (by name), no network (the host and curl's exit status, 6 when the name cannot be resolved), a pinned list that is damaged, an old glibc (read the highest `GLIBC_` version of the binaries with `objdump -T`), a folder that is not ours, a computer without a Bluetooth adapter (`/sys/class/bluetooth` has no `hciN`).
7. **A library has no menu entry:** its row has no `desktop`, the message says where it is installed, and the `-dev` package's CMake config (`find_package(SenseGlove)`) fails with a message that names the entry when the files are not there.

## Proofs without the device

Run in your own containers from the installed packages, the first with network, the runs of the program with `--network none` (a program that discovers devices never runs on a Docker network).

| Proof | Red | Green |
| --- | --- | --- |
| The entry installs from the maker | the pinned SHA-256 of one big file changed in the installed copy: the file is named, exit 1, the first installation unchanged | exit 0, 357 files at their sizes and SHA-256, link and menu entry in place |
| No network | `--network none`: host and `curl exit 6`, nothing installed | |
| The program starts and says no glove | | Stereo KWin on a virtual output, the program from its menu entry's Exec line as a person: a capture (the window says "We are not detecting any SenseGlove connections on your system...") and the program's own `Player.log` |
| The `-dev` package links | `find_package` before the entry's libraries: names them and the entry | cmake builds the example and `ldd` resolves |
| The serial node's group | udev's default rules masked: `rfcomm0` is not in dialout | umockdev `rfcomm0` is in dialout with Debian's own rule; a new account is in dialout from the edition's list, and not with the list removed |

## Traps

- **Symptom:** the plan says "a 33 MB archive". **Cause:** that was another file (an older zip in the API repository); the tag archive of SenseCom is 235 MB. **Fix:** list the tree, sum the Linux files, count identical contents once. **Found by:** downloading the tag archive once into scratch and summing it.
- **Symptom:** `undefined reference to SGCore::HapticGlove::ToString[abi:cxx11](...)` linking SenseGlove's own example with g++. **Cause:** the prebuilt libraries (v20, v21 and v22 alike) were built with LLVM's libc++: every exported name says `std::__1`, so no libstdc++ program links them. **Fix:** the `-dev` package's CMake targets add `-stdlib=libc++` for Clang and refuse another compiler, saying why; the toolchain is clang, libc++-dev and libc++abi-dev (suggested by the package, not depended on). **Found by:** `nm -DC libsgcore.so | grep ToString`; a first reading ("old `std::string` ABI", `-D_GLIBCXX_USE_CXX11_ABI=0`) did not link either: read the second missing symbol before writing a fix.
- **Symptom:** the maker's example never stops without a glove. **Cause:** it waits with `system("pause")`, a Windows command, so on Linux the loop prints its message again and again. **Fix:** bound the run (`timeout`) and read the first lines; list it for the maker.
- **Symptom:** the whole-page status of the app center takes minutes in a rig. **Cause:** it reads every package record of apt for the install-time download notice (older than this entry). **Fix:** ask the card's own part (`tree_note`) in the proof.
- **Symptom:** `apt install` of the app center in a rig fails with "none of the choices are installable". **Cause:** `sparky-aptus-appcenter` and `sparky-apt` are SparkyLinux's own packages, not in the edition's repository nor in Debian. **Fix:** install its other dependencies by apt, `dpkg --force-depends` the package, copy the one install-download reader out of `sparky-stereo-apt` with `dpkg -x` (installing it adds the edition's apt sources and stops at a conffile prompt), and say so in the report.
- **Symptom:** the recipe's `catalogue.py` test fails (`required <= packages`) before any change. **Cause:** it compares the catalogue with the build tree's lists, which are newer than the app center's master. **Fix:** run it on the unchanged catalogue too and report that the failure is the same.
- **Symptom:** the build stops at `No such file ... packages/dpkg-stereo/LICENSE`. **Cause:** a sparse checkout of the build tree lacks what the Lean Code standalone adapter copies. **Fix:** add `sparky-os/packages/dpkg-stereo`, `sparky-os/lists` and the packages the tests read to the sparse set.
- **Symptom:** a Unity program's log is not found by `find -exec sh -c '... {}'`. **Cause:** the folder is named `SenseCom 1.9.2` (a space). **Fix:** `find ... -exec cp {} DEST \;`.
- **Symptom:** a UI string test passes while a language shows English. **Cause:** a catalogue test that only checks keys. **Fix:** require every required language to differ from English and to keep the placeholders (`tests/vendortree.py`).

## Not covered

A real glove, a Bluetooth adapter and a run of the program on a television: the maker's own program decides what it shows, and the edition only starts it.
A report to the maker's tracker is a separate, approved act (their organisation publishes no AI policy; read it again before writing).
