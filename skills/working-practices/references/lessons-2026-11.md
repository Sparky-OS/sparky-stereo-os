# working-practices: lessons from the lanes of 25 October to 15 November 2026

Harvested by ORDER 591 from the hand-backs of lanes 551b, 572, 572b, 575, 576, 578, 579, 580 and 587, from what was really on the disks afterwards (measured with `du`), and from the check written for this skill.
A trap gives its symptom first, then its cause, its fix and how the cause was found; a recipe gives the commands and the result to expect.

## Recipes that worked

- **Measure what a lane left, per kind.** `du -sx --block-size=1M /scratch/LANE /build/LANE`; `docker image inspect --format '{{.Size}}' NAME` for each image of `.artifacts`; `find LANE -name .keep` for what a cleaner will skip. Expect the lane folder to hold text, bundles and small evidence (the fourteen measured lanes: 1 to 342 MB) and scratch you can name.
- **Make a bundle that proves itself.** `git bundle create LANE/NAME-order123.bundle BRANCH`, then unbundle it into a throwaway repository that borrows the clone's objects, which reads the whole pack and does not touch the clone: `git init --bare T; echo CLONE/.git/objects > T/objects/info/alternates; GIT_DIR=T git bundle unbundle LANE/NAME-order123.bundle` (expect one `sha refs/heads/BRANCH` line per head); remove T.
- **Check the stage the way a cleaner will meet it.** `LC_ALL=C sha256sum -c SHA256SUMS | grep -vc ': OK$'` prints 0, and `wc -l SHA256SUMS` is the number of files you expect; `head -1 .keep` is a sentence.
- **A hand-back's last command** is the lane check; paste its output. `RESULT: PASS` or the lines that failed, each with what to do.

## Traps

- Symptom: a task stops "blocked" on a scratch cap or a free-space floor while another solid-state disk has tens of GB free (lane 587 on 2026-11-15, / at 45 GB free against an 8 GB cap in its brief; before that, 58 briefs and AGENTS files carried a 10 GB floor against the house's 2 GB, and lane 94 stopped at 9.4 GB free).
  Cause: a caution written into a brief is read as a rule, and a lane takes the stricter line.
  Fix: a brief gives a starting place and says the lane may move scratch to any solid-state disk with room; only the workspace's floors stop work. The stage and the evidence stay, scratch moves; say where it went.
  Found by: comparing the brief's figure with the house rules and with `df -BG` at the minute the lane stopped.
- Symptom: a lane's report says its work is done, and the branches exist only in a clone under scratch (lane 578: `build-repo`, `skills-repo` and a `patchwork` clone with local commits on master and 3 modified tracked files; lane 551b: six clones in scratch, "not in `.artifacts` for that reason").
  Cause: a lane cannot push, so it leaves its clones where it built, and scratch is what the cleaner removes.
  Fix: bundle every branch that is on no remote into the lane folder before cleaning, unbundle it once to prove it, and list the clone in Kept only if it stays. A clone inside the lane folder is already kept.
  Found by: `git rev-list --branches --not --remotes` in every clone found under the lane folder and its scratch, which the lane check runs.
- Symptom: `git bundle verify` says a bundle is okay, and the bundle is useless.
  Cause: `verify` checks the header and the prerequisites, not the pack: a bundle with its last bytes damaged still verifies, a bundle whose header was cut off verifies with no heads, and a bundle made as `main..branch` (thin) cannot verify alone because it needs its base commits. Fetching an old bundle from a shallow source fails later on a parent that was never there (see [upstream-outreach, craft-apps](../../upstream-outreach/references/craft-apps.md)).
  Fix: unbundle into a throwaway repository, alone first, then borrowing the objects of the clone the branch came from; refuse a bundle that lists no heads.
  Found by: the red test of the check, which flipped 30 bytes near the end of a good bundle and still got "okay" from `verify`.
- Symptom: an image or folder of a finished lane stays for days. The lane (576) made `/var/tmp/dolphin-3d-thumbnails-576` and images `dt-576-rig:green` for a lane folder called `dolphin-3d-thumbnails-fractional-scale-576`.
  Cause: a cleaner matches `<lane folder name>` and `<lane folder name>-*`; a shorter name is found only if `.artifacts` lists it.
  Fix: name scratch and images with the lane folder's name, or write the short prefix in `.prefix` and list every folder and image in `.artifacts` as you make it; the check reads both.
  Found by: `du` on the scratch places by the lane's order number, after the lane's own name found nothing.
- Symptom: `.artifacts` and Kept disagree. Lane 572's `.artifacts` lists six images, all still present, and Kept names one; lane 580 lists 37 entries, 29 already gone and three present images that Kept does not name; lane 575 lists one scratch folder ten times.
  Cause: `.artifacts` grew as a log of every command, and Kept was written once, from memory.
  Fix: one line per thing, each once; at hand-back list in Kept every image and folder that still exists, with its size; entries already gone may stay (they are cleaned).
  Found by: comparing each `.artifacts` line with `docker image inspect` and `test -e`, and with the Kept text.
- Symptom: Kept gives no sizes or an estimate ("below the 10 GB scratch cap" over 2.5 GB; `/var/tmp/LANE` named with no figure while it held 2.0 GB), so the next partner cannot tell what a leftover costs.
  Cause: the sizes were never measured at hand-back.
  Fix: measure with `du -sx --block-size=1M` in the hand-back's last minute and write the figure and the date.
  Found by: running `du` on each place after acceptance.
- Symptom: a stage folder's `.keep` is empty (lanes 572, 578, 579), so a later reader cannot tell why it waits or what reads it; lane 579 also had a second folder called `stage` in scratch, a flat working copy.
  Cause: `touch .keep` satisfies the cleaner, which only looks for the file.
  Fix: write the first line (why it waits, what reads it); call a working copy `work-stage` or delete it, so only one folder is "the stage" and it is not under a temp folder.
  Found by: `find LANE /build/LANE -name .keep -size 0`.
- Symptom: a publication gate stops with "supplied input changed after its universe was frozen", with `0 files verified` or with a hash that changed, after a lane "just linked" the staged files.
  Cause: a hard link (`ln`, `cp -al`, `rsync --link-dest`) moves the change time of the shared inode; and `sha256sum -c` on an empty or unreadable `SHA256SUMS` can exit 0 and verify nothing.
  Fix: copy staged files; check the count of verified files, not only the exit status ([edition-packaging, lessons](../../edition-packaging/references/lessons-2026-11.md)).
  Found by: `stat -c 'links=%h ctime=%z'` on the file the gate names.
- Symptom: a terminal opened for a lane, a `sleep`, a wait loop or a container was still alive 14 hours after it started (lane 580's shell, found with `/proc/PID/cwd` inside the lane folder), and the lane keeps showing as running.
  Cause: a loop started with `until ...; sleep 15` or `( ... &)` belongs to the shell that started it, not to the task; a background function run as a subshell leaves its command orphaned when you kill `$!`.
  Fix: start long runs with the tool's background mode, `exec` the command inside a function you background, keep the PID, stop it by PID, never by pattern (`pkill -f` and `pgrep -f` match their own command line).
  Found by: listing processes whose working directory or whose docker socket belongs to the lane, which the check does.
- Symptom: Qdrant, a browser service or another lane's work is gone after a lane's cleanup.
  Cause: a loop over `docker ps -q` with `kill` or `rm` acted on the whole daemon, which every lane's proxy shares.
  Fix: remove by literal name or with `--filter name=PREFIX`; never a prune; a lane that sees the reference index refuse connections says so at once and does not count its empty answers as evidence.
  Found by: another lane reporting the index down 34 minutes later.
- Symptom: a long build ends at the free-space floor with every object compiled (lane 551b, digiKam: 3,137 object files, stopped at 24,079 MB free on a 25 GB floor); the rerun needed the floor plus about 35 GB free at the start.
  Cause: the estimate came from the object files, and the last half hour of the packaging step takes a third of the peak.
  Fix: record the peak from the first run, free or move scratch to another solid-state disk before the second, and say in the report where it went.
  Found by: the watch's one-line-a-minute log.
- Symptom: a round-two or follow-up report has only the sections of the round (lane 575: "What changed in round 2", proofs, Design check, Kept) and lacks Read, Reconcile, Corpus consulted, Credits, Skill changes and Memory proposals.
  Cause: the new text replaced the file instead of extending it.
  Fix: keep every owed section in the current `REPORT.md`; move the earlier round's report to `evidence/REPORT-roundN.md` and say so in the first lines.
  Found by: the check's sections line.
- Symptom: a lasting file is lost, or a stage is cleaned, because it sat in a folder that a system cleaner or a person empties (`/tmp`, `/var/tmp` where the distribution's `tmp.conf` ages files out after 30 days, a folder named `temp`).
  Cause: the name says it is temporary, and it is.
  Fix: scratch only in a temp folder; the stage, bundles, evidence and the report in the lane's own places. The File Hierarchy Standard, as Lintian's `symlink-target-in-tmp` quotes it, lets the administrator remove files in `/tmp` and `/var/tmp`, and Debian Policy 4.7.4.1 (Source packages, `debian/rules`) lets a build write there but never depend on what it left.
  Found by: Daniel's rule of 2 November 2026 on the house rules kept in a temp folder, and the check's `places` line.
- Symptom: files in a lane's scratch cannot be removed by the lane (`Permission denied`, owner root).
  Cause: a container ran as root and wrote them.
  Fix: run the container as your user (`--user $(id -u):$(id -g)`), or remove them through a container before it exits; the coordinator may remove what is left.
  Found by: `find SCRATCH ! -user $(id -un)`.
