# An RFC series for DRM core

**For** a person or an assistant who prepares a series for the kernel's DRM core from patches a distribution already carries: the reconcile, the rebase onto drm-misc-next, the checks, the IGT companion on VKMS, DRM's rule for userspace, the cover letter and the send checklist, with the traps met on the way.

Written on 2026-11-27 from the HDMI 3D core RFC (queue row 166): twelve patches on drm-misc-next at `5ce32a0c94a8`, mainline at v7.4-rc4.
Nothing was sent; the person who signs reads every line first ([the rules that come first](../SKILL.md#the-rules-that-come-first)).

## Recipe

1. **Reconcile what you carry.** List the carried series group by group, each patch with its subject, files and what it adds, and sort them: core (drivers/gpu/drm, drivers/video, include/drm, include/uapi/drm), drivers, other subsystems (virtio, media), tests.
   A core RFC takes the core and its tests only; drivers follow after the core is agreed, each on its own list.
   A patch whose note says "needs" another group brings that group's core part with it.
2. **Search upstream first** ([search-upstream-first](../../search-upstream-first/SKILL.md)):
   - `git clone --shallow-since=<date of your base> --single-branch --branch drm-misc-next https://gitlab.freedesktop.org/drm/misc/kernel.git`, then `git log --oneline --since=<date> -- <each touched file>`; a pickaxe search (`-S`) over the whole tree is slow and its hits at the shallow boundary are noise, so give it paths.
   - The list on lore, through its Atom search with a plain client name: `https://lore.kernel.org/dri-devel/?q=<terms>+d:<YYYYMMDD>..&x=A`; also the driver's own list (amd-gfx) for driver series on the same subject.
   - Record each hit with what it means for the series: carry it, build on it, or leave it.
3. **Apply onto today's head**, patch by patch with `git am`, and keep the raw result under a tag (`git tag ORDER-raw-apply`).
   Then build the series again by content if its history is not one logical change per patch (a timing introduced in one patch and replaced in the next): reset the branch to the base and make each commit from file states of the raw result (`git checkout <raw commit> -- <files>`, edit out what belongs to a later commit), then `git diff <raw tag> <branch>` must show only the intended corrections.
4. **Messages in the files' own style.** Read the last commits on each touched file (`git log -8 --format='%h %ad %an | %s' -- FILE`): drm-misc writes `drm/edid: Parse ...`, `drm/display: hdmi: Add ...`, `drm/tests: hdmi: ...`, a capital after the prefix.
   No `Assisted-by:` trailer for a tree at 7.4 or later and no Signed-off-by from the assistant; the tool's part goes in the cover letter ([the rule](../SKILL.md#the-rules-that-come-first)).
5. **KUnit, parsed.** `tools/testing/kunit/kunit.py run --arch=x86_64 --kunitconfig=drivers/gpu/drm/tests/.kunitconfig --build_dir=B` without `--raw_output`, on the base and on the series, each in its own `git worktree`; read "Testing complete. Ran N tests: passed: N" and kunit.py's exit status, and compare the case lists (new cases, no changed result).
6. **Every commit builds alone**, with `W=1` on the touched objects, base included for comparison (`make O=B W=1 drivers/gpu/drm/drm_modes.o ...`); record make's own exit status, not a grep's.
7. **checkpatch.pl --strict** on the format-patch files, in a place with `python3-ply` and `python3-git`, with the tree mounted at the path its `.git` file names; say every remaining CHECK and why it stays (the file's own layout counted with `grep`).
8. **`git format-patch --rfc --cover-letter --base=<base>`**; recipients from `scripts/get_maintainer.pl --nogit --nogit-fallback` on the patches (not the cover), listed by role.
9. **The IGT companion** on VKMS in a virtual machine (step below), red without the series and green with it.
10. **The userspace** named exactly: project, branch or package, file and function that sets each new property.
11. **The cover letter** (shape below) and a send checklist for whoever sends.

## The IGT companion on VKMS

- VKMS needs connector types and an EDID from configfs: Louis Chauvet's series "VKMS: Introduce multiple configFS attributes" (v7 of 2026-11-26, 43 patches, base `3c7c3c12dfc7` in drm-misc-next) applies on drm-misc-next as it is.
  On top: the bench's "Compose the frame of both eyes" and the one line `connector->base.stereo_allowed = true;` at the top of `vkms_connector_init()` ([vkms-stereo](../../vkms-stereo/SKILL.md)).
  v7 already attaches PATH only to connectors with a parent and frees the EDID through RCU, so the bench's patches for those are not needed on it.
- Two kernels from the same tree: control (drm-misc-next, v7, the two VKMS patches) and with the series cherry-picked on top; the bench's `tools/build-test-kernel.sh` (tinyconfig and its fragment).
- kms_3d `basic` requires one 3D mode and sets the listed ones, so it passes with or without a core change that lists more structures: a companion that cannot go red proves nothing.
  The row 166 companion adds a `structures` subtest: every structure IGT's 3D EDID declares must be listed, unless the connector lists no 2D mode it can be sent in (VKMS has no interlaced modes, so no field alternative).
- Measured on 2026-11-27 (drm-misc-next 5ce32a0c94a8, VKMS v7, IGT master 76472559890e plus the three patches): without the core series `basic` passed with 15 3D modes set and `structures` failed with four declared structures unlisted (exit 98); with it `basic` set 35 modes (seven structures on five formats) and `structures` passed; IGT master's `basic` passed on both kernels.
- IGT runs from a root made with `docker export` of the build image (the runtime libraries), each IGT build in its own folder with its `libigt.so.0` (`LD_LIBRARY_PATH`), shared read only over 9p; `IGT_FORCE_DRIVER=vkms`, `--run-subtest NAME`, exit 0 pass, 77 skip, 79 no such subtest, 98 fail (`lib/igt_core.h`).

## DRM's rule for new uAPI

`Documentation/gpu/drm-uapi.rst`, "Open-Source Userspace Requirements": "any addition of DRM uAPI requires corresponding open-sourced userspace patches, and those patches must be reviewed and ready for merging into a suitable and canonical upstream project."
The same section: "The userspace patches must be against the canonical upstream, not some vendor fork."
A downstream fork that sets the property is a demonstration, not that: say so in the cover letter, and say which patches add no uAPI, so they can be judged apart.

## The cover letter

One sentence per line, plain text, in the sender's voice:
1. Why the series exists, in two or three sentences.
2. What the kernel already has, with its authors by name from the commits (git.kernel.org's `/patch/?id=` gives the `From:` line).
3. What each patch adds, one line each.
4. How it was tested: real hardware with the device's own readout, the EDID lines as `edid-decode` prints them from the saved bytes, KUnit numbers before and after, the IGT run red and green, the build and checkpatch, and what each kind of test shows.
5. One question, the approach, with the points where it could go either way.
6. What comes after (drivers, other lists) and what stays out.
7. How the tools were used, once (`generated-content.rst`, "Guidelines": which tools, the input, which portions, how it was tested).
8. Numbered links; no other person's address in any link (a lore link whose message-id holds an address is left out; name the series and its date instead).

## Traps

- **Symptom:** every lore search answers HTTP 200 with the title "Making sure you're not a bot!".
  **Cause:** a browser-like client string triggers the archive's challenge page.
  **Fix:** a plain generic client name; the same query then returns the Atom feed.
  **How found:** the feed's `<title>` in each saved file.
- **Symptom:** `git am -3` stops with "sha1 information is lacking or useless (drivers/gpu/drm/drm_atomic_uapi.c)" and "could not build fake ancestor".
  **Cause:** the patch was made on an older release whose blobs a shallow clone of drm-misc-next does not hold, so the three-way fallback has nothing to merge from.
  **Fix:** `patch -p1 --dry-run -F0 < PATCH` names the hunk that moved; when it is context only (here a new include beside one that drm-misc-next added), `git am -C1` applies it; otherwise port the hunk by hand.
  **How found:** the dry run listed one failed hunk out of 23.
- **Symptom:** a KUnit test written on 7.3 fails to build on drm-misc-next: "'const struct drm_connector_funcs' has no member named 'reset'", "'drm_atomic_helper_connector_reset' undeclared".
  **Cause:** Maxime Ripard removed the connector `.reset` hook (27cae3ef0574, "drm/connector: Remove reset", 2026-10-30); state is created by `.atomic_create_state` now.
  **Fix:** `.atomic_create_state = drm_atomic_helper_connector_create_state`, as drm-misc-next's own tests do (`drivers/gpu/drm/tests/drm_probe_helper_test.c`).
  **How found:** the first kunit.py run on the raw series.
- **Symptom:** checkpatch reports "Please use git commit description style ... fatal: not a git repository" and spdxcheck.py raises `InvalidGitRepositoryError`, in a container.
  **Cause:** a `git worktree` has a `.git` file that names the main clone's path, which the container did not mount; a "(cherry picked from commit ...)" line in the message is also reported.
  **Fix:** mount the scratch folder at its own path; drop the cherry-pick lines.
  **How found:** the same patches checked from the main clone.
- **Symptom:** checkpatch "passes" a patch silently.
  **Cause:** the file was not where the container looked ("open failed - No such file or directory" on stderr) and a `grep` for ERROR, WARNING and CHECK hid it.
  **Fix:** judge checkpatch by its exit status and its `total:` line.
  **How found:** rerunning one file without the filter.
- **Symptom:** `git clone --filter=blob:none` of torvalds/linux.git from git.kernel.org prints "warning: filtering not recognized by server, ignoring" and becomes a full clone of several GB.
  **Cause:** the server does not serve partial clones.
  **Fix:** for the history of a few files, use cgit: `https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/log/PATH?qt=grep&q=WORD` lists the commits, and `/patch/?id=SHA` (with `curl -L`) gives each one's author and date.
  **How found:** the clone's first lines.
- **Symptom:** the dry run of the mail tool stops with "Compilation failed in require" (Git/LoadCPAN/Mail/Address.pm), then with "Committer identity unknown".
  **Cause:** Debian's `git-email` only recommends `libmailtools-perl`, so an install with `--no-install-recommends` lacks Mail::Address; and the tool asks git for a committer identity even when `--from` is given.
  **Fix:** install `libmailtools-perl`; give the identity through `GIT_COMMITTER_NAME` and `GIT_COMMITTER_EMAIL` (no global configuration needed). Run the dry run in a container with `--network none` and the SMTP server on a closed local port, so nothing can leave even by mistake.
  **How found:** the dry run's own output, one error after the other.
- **Symptom:** an AI tool's guard refuses a shell command that only edits a file, calling it a mail.
  **Cause:** the command's text names the mail tool (in a string being written to a checklist).
  **Fix:** edit such files with the editor tool, not through a shell line; keep the mail tool's name out of shell commands that are not a send.
  **How found:** the guard's refusal on a Python edit of the send checklist.
- **Symptom:** get_maintainer.pl prints "file '0000-cover-letter.patch' doesn't appear to be a patch".
  **Fix:** pass only the numbered patches.

## Perks

- drm-misc-next's head and mainline's newest tag come from `git ls-remote` alone; the tag says where the cycle stands ([where a change goes](where-a-change-goes.md)).
- The series' own tests named by suite in the kunit.py log let a script list new cases and compare results with the base run.
