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
