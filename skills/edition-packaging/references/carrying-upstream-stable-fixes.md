# Carrying a stable-branch fix into a patched KDE package

A KDE project keeps fixing its stable branch (KWin's `Plasma/6.7`) after the release a package was built on.
The edition's source is that release plus its own patches, so the fixes come as upstream's own commits, one patch each, with their authors.
First done for KWin 6.7.4 (ORDER 449): three fixes of 6.7.5 and 6.7.6, one of them a crash.

## Recipe

1. **Find them.** Clone the project bare from its read-only mirror into scratch (`git clone --bare https://github.com/KDE/kwin.git`), then `git log --format='%h %ad %an %s' --date=short vBASE..origin/Plasma/6.7 -- FILES` for the files the edition's patches do not own, and `git log --grep=BUG` for crash reports.
   The stable branch holds cherry-picks: the commit you carry is the branch's, and its message names the master commit (`(cherry picked from commit ...)`) and the person who wrote the change (`Co-authored-by:`).
   `git tag --contains HASH` says which release carries it. Check master for a later commit on the same lines (`git log HASH..master -- FILE`) before you carry one.
2. **Try it on the real tree.** Unpack the staged plain source in a container (`dpkg-source -x`; the patches apply on extraction), `git format-patch -1 HASH --zero-commit` and `patch -p1 --dry-run` in that tree. An offset is normal (the edition's code sits above); a failed hunk is an adaptation, kept apart from upstream's change.
3. **Write the DEP-3 header** under upstream's message, keeping its `Co-authored-by` line: `Origin: upstream, <commit URL>`, `Author:` (the commit's name only, no address), `Applied-Upstream: <release>, <short hash> (<branch>), <short hash> (master)`, `Last-Update:`, then the lane's `Assisted-by`. Say in one line what you changed (nothing, or the offset) and why the edition's own code was or was not affected.
4. **Number them as the next version's patches** (`s47-0001..`), one patch per upstream commit, in upstream's order, and put the edition's own test in a last patch marked `Origin: vendor`, `Forwarded: no`.
5. **Copy the previous version's recipe** (prepare-source, build, build-in-container, changelog) and change only the version, the patch glob and the changelog list; `diff` the copies against the old ones to see nothing else moved.
6. **Prove the crash fix red and green** (below), then the whole autotest suite on the patched tree, then build the package.

## Proving a crash fix red and green

- **A unit test that cannot pass without the fix.** A bug that depends on the allocator is made deterministic in the test: make the two objects in the same storage (`new (buf) A`, destroy, `new (buf) B`), give their states different types, and check the type with `dynamic_cast` where the code under test would `static_cast`. BUG 510116: red on 6.7.4 (2 mismatches), green with the one-line fix.
- **A client that follows the bug's steps.** The report's backtrace and its comments say which objects are involved (here a pointer confinement, then a pointer lock, on one `wl_surface`). A small C client against the generated protocol code reproduces it (`stereo-proof-rig/scripts/ext510116.c`, with `fake-input.xml` beside it); build it in the rig container with `wayland-scanner client-header` and `private-code`.
- **Make the corruption loud.** A heap overflow of 24 bytes may corrupt silently for thousands of rounds. Start KWin with `LD_PRELOAD=libc_malloc_debug.so.0 MALLOC_CHECK_=3 MALLOC_PERTURB_=165` and the first bad `free()` aborts it (`free(): invalid pointer`, exit 134). Say in the report that the plain run did not crash in 2000 rounds.
- **Keep a control that must stay green:** the same client against the fixed package, same flags, same rounds. A heap corruption is not deterministic: on 6.7.4 the client killed KWin in 5 of 6 fresh sessions (at round 1, 120, 405 and 638; the sixth survived 300 rounds), and the plain run without the allocator check survived 2000 rounds; the fixed package survived 5 of 5 sessions (300 and 2000 rounds). Say "5 of 6", never "reproduces".
- **Show the declared picture still works** in the same session before the crash steps: a declared client (`subdecl.c` of stereo-proof-rig) with the left eye red and the right eye blue, ScreenShot2 counts, and the same window undeclared as the control (both eyes identical).

## Traps

| Symptom | Cause | Fix |
| --- | --- | --- |
| the rig client's `confine_pointer` dies with `null value passed for arg 2` | the request takes a `wl_pointer`, and a `--virtual` KWin has no pointer until an input device exists | bind `org_kde_kwin_fake_input` (`KWIN_WAYLAND_NO_PERMISSION_CHECKS=1`), authenticate and send one `pointer_motion`; read the seat's capabilities with a listener added at bind time |
| the seat's pointer capability never shows | the `wl_seat.capabilities` event arrives in the first roundtrip, before a listener added afterwards | add the listener in the registry callback, right after `wl_registry_bind` |
| the rig container never ends | the script `wait`ed for KWin, which runs until it is stopped | test `kill -0`, then stop it yourself and say which happened |
| a `t.sh` that installs `/extra/*.deb` fails with an empty folder | the glob stays literal | `compgen -G` first |
| the rig image has no `jeepney`, `wayland-info`, `gdb` | the image holds only the staged KWin | install them in the throwaway container from the archive (`sh /run/https-only-apt.sh` first), never into the image |
| the autotests list of the last lane misses the new test | the lane's `ALL` list is hand-written | add the new program to the list and run the other `autotests/wayland/server` programs by name too |
| `publish-check` stops on an upstream author's address in a patch header (`From:`, `Author:`, `Co-authored-by:`) | `git format-patch` writes `Name <address>`, and no third-party address stays in our files | write names only; `Origin: upstream, <commit URL>` carries the full record. Strip the same from an older carried patch in the recipe's prepare script (`sed -i -E '1,40{/^(From\|Author\|Co-authored-by): /s/ *<[^>]*>//}'`) and say so in the changelog. The fork branch keeps git's own author metadata (`git am` needs it) |
| the copyright file would credit a carried commit to Daniel | `repo/provenance-files.py` (ORDER 451) reads the patch headers: `Origin: upstream` or `backport` leaves a patch out, a `From:`/`Author:` with Daniel's address and `Origin: vendor` or none names it | write the headers as above, run the helper in the prepare script and read its "ours" and "left out" lines |
