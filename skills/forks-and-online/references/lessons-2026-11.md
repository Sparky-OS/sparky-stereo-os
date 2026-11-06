# forks-and-online: lessons from the lanes of 25 October to 6 November 2026

Harvested by ORDER 429 from the accepted lane reports; each line names the lane it came from.
A trap gives its symptom, its cause, its fix and how the cause was found; a recipe gives the commands and the result to expect.

## Recipes that worked

- Moving build machinery out of a driver repository: back up first (mirror, old .git, uncommitted diff, tar, private originals), re-point briefs, keep symlinks only in the private build tree; a pre-commit hook refusing evidence/, captures/, REPORT*.md and never-named files; lanes clone and hand back patches, never workspace symlinks (lane machinery-placement-196)
- Find work that exists only locally: `git fetch` the fork heads into refs/forkcheck/*, then `git rev-list --branches --not --remotes --glob='refs/forkcheck/*'`; match each commit to the build repo's patch files with `git patch-id --stable`, then by subject for context-changed ones, then by content search for folded ones; for a kernel fork `gh api compare`, a 404 means the commit is absent; save patches of what is not online; `git status -uall` for uncommitted state. (lane k3d-parked-trees-381)

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: published boot packages (sparky-stereo-boot 0.1.4, grub-l10n 0.1.1 and 0.1.2) are missing from the build main. Cause: the lane branch was never merged, so later work built on a tree without them. Fix: merge the accepted commit and audit that every published package's source exists on main. (lane boot-no-fallbacks-345)
- Symptom: `git push` of asked work from a lane is refused by the auto-mode classifier ("Create Public Surface"). Cause: no scoped allow entry. Fix: add a scoped allow entry for pushes of existing branches to the edition's own forks, and have the main session run the listed fast-forward pushes. A failed fetch leaves `tmp_pack_*` files in objects/pack (harmless litter). Found by: the refusal text. (lane k3d-parked-trees-381)

## Perks of the part

- Skill audit table vocabulary: "Already" (grep found the rule), "Added" (commit), "Should go" (not written). Pending adds: kernel config traps (zfs-dkms 2.4.4 supports up to kernel 7.2, Debian nvidia-kernel-dkms 550 fails on 7.3, the rt kernel needs `CONFIG_EFI_DISABLE_RUNTIME=n` for MOK-signed modules) to drivers; a shell started with another XDG_RUNTIME_DIR starts Steam broken, to proton-wine. (lane skills-gap-323)

