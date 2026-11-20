# Reconciling an old plan against what shipped

Use it when a plan written weeks ago (a study, a numbered request with lettered sub-items) must be briefed again. Output: one table, one row per sub-item, each cell with the evidence line read.

## Order of evidence
1. The published round: the package's version, `dpkg-deb -c`, `dpkg-deb -f Depends`, and the source's `debian/patches/series` and `debian/changelog` read with `tar -xJOf SRC.debian.tar.xz debian/...` (no unpacking needed). A Qt binary's strings are 16-bit: `strings -a -el`.
2. The build tree at origin/main (`git show`, `git ls-tree`, never a checkout). A folder there is not proof of what ships.
3. The queue rows and the lane REPORT files; staged stages are read with `dpkg-deb` too.
4. Absence: search the feature's own names (the fork's commit log, the patch subjects), not the word the plan used.

## Traps met on request 61
- A sub-item letter can be reused: "61c" was the Kamoso slot in the study and the GPU encoder marks in the journal. Say which in every row.
- A default the plan wanted (Kdenlive's 3D preview on) can be absent while the feature ships: read the kcfg `<default>` in the patches and look for an /etc/xdg file in the package.
- Strings of a patched program are untranslated unless the built `.mo` holds the msgid: check the `.mo` of the published data package for the English msgid.
- A pack "in nine languages" predates Spanish: list the pack's `usr/share/sparky/<pack>/` language folders.
- "HEIF multiView" in a changelog is not EXR multiView: grep the patches for the format's own name.
- Work moves lanes: Kamoso's stereo mode became the Camera page; the emulators moved to row 39. Follow the row text before calling something dropped.
