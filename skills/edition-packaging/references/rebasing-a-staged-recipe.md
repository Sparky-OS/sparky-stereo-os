# Bringing a staged recipe onto a main that moved

A lane stages a package from a recipe commit; the build repository's main then moves (a shared prepare tool changes) before the stage is published.
Redo the recipe on the new main, prove the source is the same, rebuild, and rerun the tests; do not publish the old stage.

## Recipe

1. Clone the build repository at the new main into your scratch, branch off, and `git fetch` each lane's recipe branch from that lane's clone (use the branch name: a short hash is not a ref for `fetch`).
2. `git cherry-pick` each recipe commit (one commit per package keeps each independent). Expect a conflict only where the moved tool and the recipe edit the same lines (ffmpeg-dmo `make-source.py`).
3. Read the diff of the tool change on main (`git diff OLDMAIN NEWMAIN -- sparky-os/lean sparky-os/repo sparky-os/packages/<pkg>`) and give the recipe's prepare script the new options. ORDER 435: `plain-from-lc.py --save-plan FILE` (or `--drop-plan`), then `lean.debian_prepare --preserve-plan FILE` or `carried_plan=`. A published source without a plan writes no FILE and a missing FILE means no plan, so the call is safe for both.
4. Squash the adaptation into the recipe commit (`git commit --fixup`, `git rebase -i --autosquash` with `GIT_SEQUENCE_EDITOR=true`), keep the lane's `Assisted-by` lines and add your own.
5. Run in order: `tests/reproducible-sources/check_producers.py .`, `bash tests/supply-chain/test-wiring.sh`, and `tests/reproducible-sources/test.sh` in a container with dpkg-dev and devscripts (`--network none`). Make the producers check red on the lane's old script (`plan_findings` on `git show OLD:path`) to see it can fail.
6. Regenerate each source from the new recipe commit in a container and compare with the staged one (below).
7. Rebuild from the new clean recipe commit: check out exactly that commit (a package build records `recipeCommit` and `recipeDirty` from the checkout), keep scratch outside the clone, and give the build the newest published repository.
8. Stage with SHA256SUMS and a `.keep`, leave the old stage alone, remove the build tree.

## Comparing the regenerated source

- Compare the plain source first (`.dsc` and `.debian.tar.xz` of the plain step): it must be byte identical, because nothing in the toolkit reaches it.
- The `+lc1` source differs in exactly two ways. Everything under `debian/sparky-lean-toolkit/` is the toolkit of the new main, so the files the moved commits touched differ (here `lean/debian_prepare.py`, `lean/buildrecord.py`, `lean/standalone.py`). The changelog dates move when the recipe's date comes from a commit (ORDER 421): any commit that touches a recipe folder, even a README line, moves that folder's date.
- A package whose build runs `dpkg-buildpackage` on the Lean Code tree (kwin) packs its source again at the end: the `.debian.tar.xz` it leaves is not the prepare script's output. Files keep the prepare date, but the mtime of the directories that changed during the build (`debian/`, `debian/sparky-lean-toolkit/lean/`) takes the build's SOURCE_DATE_EPOCH, the recipe commit's date since ORDER 421b. Compare the prepare output with the staged source by `tar -tvf --numeric-owner` listings, and expect those two directory lines to differ; stage the build's own source, which is what the build record names.
- Extract both `.debian.tar.xz` files and `diff -rq`: any file outside those two causes is a real change, stop and find it.
- A recipe whose date comes from its commit changes again when the commit is re-made (cherry-pick, rebase, amend). Merge fast-forward, or regenerate and restage after the final commit.

## Traps

| Symptom | Cause | Fix |
| --- | --- | --- |
| `fatal: couldn't find remote ref 3011d66a` | `git fetch` needs a ref name | fetch the branch name into a local branch |
| make-source.py `ValueError: not enough values to unpack (expected 4, got 3)` | ORDER 435 added the PLAN argument | pass the PLAN path, even when no file will be written |
| red copy of a patched tree equals the green one | `patch -R` ran with a relative patch path after a `cd`, and the failure was hidden in a `&&` chain that printed "ok" | use absolute paths and test with `diff -rq` that red and green differ |
| a whole patch reversed removes the tests too | a patch carries code and test hunks | `filterdiff -i '*/path/file.c' PATCH \| patch -R -p1` reverses only the code file |
| a staged source differs from the regenerated one by two directory lines only | dpkg-buildpackage packs the source again with the build's date | see above; nothing to fix |
| a patched tree from `dpkg-source -x` of an `+lc1` source has the fix | patches are applied on extraction (use `--skip-patches` for the pristine tree) | extract once, copy for the red tree |
| the build of another lane's recipe checkout changes under a running build | the build mounts the clone live | use `git worktree add --detach` for any other commit while a build runs |

## A rebuilt package moved to a new upstream release

Learned on Xwayland 24.1.13 to 24.1.15 (ORDER 562, November 2026).
This changes the upstream archive as well as the recipe; the earlier same-source procedure alone does not cover it.

1. List the published source's series and the accepted staged source's series before editing the recipe.
   Read every upstream commit between the old and new tags, including each diff, and record which touch files our patches change.
   Compare Debian's packaging between the old base and its newest available package, separately from upstream's code.
   Carry an upstream replacement with its author named; drop our equivalent patch only when the comparison proves it is replaced.
2. Port only enough to apply the series mechanically, retaining upstream's added checks.
   Run the existing regression test on that tree before extending any exception, and keep the failing log and binary.
   Run the real client too: Xwayland's stereo Present test failed without glamor, and the top-level client completed as copies with glamor as well.
   A child recovered after its first copy because the existing child-redirection patch restored its backing pair; report that distinction.
3. Read the purpose of the upstream check before extending ours.
   Michel Dänzer's [abb1e9914df8](https://gitlab.freedesktop.org/xorg/xserver/-/commit/abb1e9914df8) keeps a flip from unexpectedly changing a surface's dimensions.
   The stereo exception in patch 0005 must cover the newly checked window pixmap too: it can still be one view wide before the first stereo flip, or already hold the pair.
   Keep the height checks, reject an unrelated backing width, and leave every other flip check in place.
4. Build the new upstream tree with Debian's current packaging and the complete accepted stereo series.
   Preserve the source-consumer plan when present, the existing changelog history, Debian's new stanza and patch authorship.
   Name the new version explicitly: Xwayland uses `2:24.1.15-1+stereo3d1+lc1`, restarting the stereo counter on the new upstream base.
   Pin every input archive by SHA-256, check its closure, and verify upstream's signature using the release key before pinning it.
5. Date the producer from its clean recipe commit, normalize the source, and run it twice under different zones and umasks.
   Compare the `.dsc`, Debian tarball and orig archive byte for byte.
   Also extract the `.dsc` and run the real `dpkg-buildpackage -S -us -uc -d`, including clean; the repacked source must match.
6. Build the one source through the release recipe, with the complete build record, Lean Code and link/start gates.
   Read the actual regression-test OK line in the build log and compare lintian output against the published build.
   Stage every source file and checksum, install through apt over the cohort, read the `Inst` lines, then rerun stereo and ordinary 2D from installed packages.
   An upstream rebase needs the existing route matrix again, even when the change to our exception is small.

### Traps from the release rebase

- **Symptom:** patch 0005 rejects while the other eleven patches apply.
  **Cause:** upstream changed the same size-check hunk, adding the backing-pixmap comparison.
  **Fix:** port the old exception mechanically first to retain the red, then extend it around the new width comparison while keeping the height checks.
  **How found:** the rejected hunk, the per-commit diff and the failing stereo Present suite.
- **Symptom:** the source producer stops with `no From:, Author: or Origin: line in its header` for patch 0009.
  **Cause:** the old published patch contained only a diff, and the new provenance helper correctly refuses to guess its author.
  **Fix:** add the author from the original recipe commit, preserving every hunk, then pass a filename glob (`*.patch`) to `provenance-files.py`.
  **How found:** the producer's failure and the original patch's git history.
- **Symptom:** `dpkg-source -b` says no upstream tarball was found even though it is beside the source tree.
  **Cause:** it resolves the orig archive against its current directory when invoked with an absolute source path.
  **Fix:** run it from the source tree's parent, where the orig archive was copied.
  **How found:** the failing invocation; the corrected producer and the clean/repack check both produced identical bytes.
- **Symptom:** the producer audit prints `0 source-writing scripts checked, 0 findings`.
  **Cause:** the checker was given `sparky-os` instead of the build repository root, so its tracked-path filters matched nothing.
  **Fix:** pass the repository root and read the nonzero checked count (256 in this run).
  **How found:** reading the checker's usage and path filters after noticing the zero count.
- **Symptom:** a pixel comparison reports zero differences for a one-level blue-channel change.
  **Cause:** converting the RGB difference to luminance rounds the blue difference to zero.
  **Fix:** count pixels where any RGB channel differs, before any colour conversion, and keep a one-pixel blue-change control that must fail.
  **How found:** checking the copied comparison script against that control before accepting its 2D rows.
