# Bringing a fork up to a packaged recipe's patch stack

Learned in ORDER 445, when Sparky-OS/kwin stopped at +stereo3d41 while the packages were at +stereo3d46.
The recipe (the patches next to prepare-source-NN.sh) is the source of truth; the fork must carry the same changes on the project's own history, each commit with its patch's author and message, and a check must show that the fork's tree is what the package was built from.

## Recipe

1. Full clone of the fork (`git clone`, never shallow; the Invent remote is added to the same clone with `git remote add invent <url>` and `git fetch invent`).
2. Say what each existing fork branch equals before adding anything. A branch `stereo3dNN` is checked by unpacking the packaged source and popping its series back to patch NN (step 5), then comparing trees (step 6).
3. Find out whether the recipe's patches already exist as commits. A mailbox patch starts with `From <sha> ...`; run `git cat-file -t <sha>` and `git branch -r --contains <sha>` in the fork. When the commits exist and `git diff --quiet` shows the same tree for each, point the branch at the existing tip instead of creating new commits (same hashes as the reports and as the lane branches that are already online).
4. Apply the rest in the order of the version's `debian/patches/series`, each version on a branch of its own, on the previous one:
   - mailbox patches: `GIT_COMMITTER_NAME=... GIT_COMMITTER_EMAIL=... git am --committer-date-is-author-date PATCH...` (the committer comes from the environment, so no git config changes);
   - DEP-3 patches (`From:` and `Subject:` header, no `From <sha>` line, no date): `git am` accepts them, but the commit gets today's date as its author date. Put a mailbox line and a `Date:` taken from the version's changelog entry in front, in a scratch copy outside the clone, then `git am` the copy. The commit keeps the patch's author and message and a date that does not move.
5. Unpack the sources in a container, never on the host: `dpkg-source -x X.dsc dir` applies the whole series. For an intermediate version copy the tree, then `QUILT_PATCHES=debian/patches QUILT_PC=.pc quilt pop <last patch of that version>`.
   A version that was never published on its own (+44, +45 of KWin) is checked from the later source's series popped to its last patch.
   The published repository holds only the +lc1 sources; they differ from the plain source only in `debian/`, so the rest of the tree compares directly.
6. Compare: `LC_ALL=C diff -rq branch-tree package-tree -x debian -x .pc`, where `branch-tree` comes from `git archive BRANCH | tar -x`. Expect differences only in files the package does not take from the fork (step 7).
7. Prove the patches add no difference: take the unified diff (`diff -ru ... | sed` to hide the directory names), hash it, and compare the hashes across versions. The same hash at +40 to +46 means the patches of +42 to +46 contribute 0 differences, whatever the baseline holds.
   Then remove the baseline: apply the series' own `*.po.patch` files to a copy of the fork tree with `patch -p1` (the fork carries no translations, Invent refuses them). What remains is the list of fork-only files.
8. Writing the push commands: a branch that is an ancestor of the new tip moves as a fast-forward (`git merge-base --is-ancestor old new`). Numbered reference branches go to Invent with `-o ci.skip`. Check that the new commits touch no `po/` and no `Name[xx]=` lines (`git diff --stat old new | grep -E 'po/|\.desktop|notifyrc'`) before Invent's pre-receive audit sees them.

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: a branch rebuilt tomorrow has different commit dates. Cause: the recipe's DEP-3 patches have no `Date:`, so `git am` stamps the time of the run. Fix: add the `Date:` from the changelog entry in a scratch copy (step 4). Found by: `git am` of the raw s43 patch gave a commit dated the minute of the run (and, run by mistake on the +42 branch, moved it: `git reset --hard` to the saved tip, and keep a note of every branch tip before experimenting).
- Symptom: new commits carry new hashes that no report knows, although the same commits were online for days. Cause: the recipe patches were exported from lane branches (order366-view-source, order414-depth-limits), and `git am` makes a new commit. Fix: step 3; check `git cat-file -t` of the sha in each `From` line. Found by: the sha in the `From` line existed in the clone after the fetch.
- Symptom: the recipe has two patches for a version, the lane branch four commits. Cause: the recipe folds a lane's fix-up commits. Fix: keep the recipe's commits; prove `git diff --quiet stereo3dNN origin/<lane branch>` is empty, then say so. Found by: comparing the branches with `git diff --stat`, which printed nothing.
- Symptom: the tree check scripts see no "Only in" lines. Cause: `diff` prints its messages in the user's language (pt_BR "Somente em"). Fix: `LC_ALL=C` in every diff. Found by: reading the first output.
- Symptom: the fork and the package never compare as 0 differences. Cause: the fork carries what the package does not take (CI files, README, docs, the fork's own audit tests) and the package applies the translation patches the fork may not carry. Fix: step 7, and list the baseline in the report instead of calling it a failure. Found by: the same 24-line difference list at every version from +40, whatever the patches added.
- Symptom: a version cannot be compared because it was never published. Cause: the recipe ships several versions in one source (prepare-source-46.sh says +44 and +45 were never published on their own). Fix: pop the later source's series, step 5.
