---
name: forks-and-online
description: >-
  Record failures that cannot be filed upstream; push edition work only to the edition's forks (Sparky-OS, danielcamposramos), never to the upstream project; keep
  every branch online the same day and gone at the merge, each branch outside main with a reason (branch-keeper); audit clones for work that exists only locally ([gone] branches, ahead and behind,
  commits in no branch, worktrees, partial clones, uncommitted files, git rev-list --not --remotes with patch-id) and
  tell merged, superseded, missing and uncommitted work apart; cut releases that Zenodo keeps for good, the Sponsor
  button, our own libraries' repositories, where large files go. Load it when a report says done but nothing is online,
  origin points at upstream, a released upstream fix may retire a carried patch or local tree, a push is refused by branch protection or a public-surface rule, KDE Invent runs CI on a
  push, a release or DOI is needed, an audit of many clones is due, branches pile up, or branch-keeper refuses a removal.
---

# Forks and keeping the work online

## Working recipe

1. Before any push, read the push address: `git remote -v`. In many clones `origin` is the upstream project, not our fork.
2. Push only to the edition's forks (table below), as a branch, the same day the work exists. Work that is only on one disk is not done.
3. Before saying something is online, audit: fetch every remote, list what no remote holds, and sort it with the rules below.
4. Read what you publish. Run the repository's own audit, if it has one, and look for credentials before the first push of anything new.
5. Record what you pushed (repository, branch, commit) where the task's report or receipt lives.

For retiring released fixes, start with [retiring carried patches and local copies](references/retiring-released-work.md).
Prove the release before dropping its patch, the complete remaining distribution changes before retiring a package, and every local change before freeing a tree.

**Check freshness first.**
Written on 2026-10-29, after a full audit of more than a hundred clones found work that had been reported as done but was never pushed, and clones whose `origin` was the upstream project.
How to speak of the forks, and the conventions for releases, the Sponsor button, our own libraries and large files, added on 2026-11-02.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; [`ai-partners`](../ai-partners/SKILL.md) covers hand-backs and [`upstream-outreach`](../upstream-outreach/SKILL.md) covers sending work to the upstream project.

## Where the edition's work goes

| Forge | Our namespace | Typical projects |
| --- | --- | --- |
| GitHub | `Sparky-OS` (the edition's forks and programs), `danielcamposramos` (Daniel's own repositories and some forks) | Qt, Mesa, glfw, Blender, fastfetch, the edition itself |
| KDE Invent | `danielcamposramos/<project>` | KWin, Plasma, libkscreen and every other KDE program |
| Codeberg | `capitain_jack` | MKVToolNix |
| code.videolan.org | `capitain_jack` | VLC |
| gitlab.freedesktop.org | `danielcamposramos` | Mesa, SPICE, freedesktop projects |

- **Never push to the upstream project's repository.** Upstream receives work only as a reviewed merge request, through [`upstream-outreach`](../upstream-outreach/SKILL.md).
- **SparkyLinux's own repositories are upstream too.** They are Paweł's: fork them (for example `danielcamposramos/sparky-backup-core`) and push there.
- **Name the remote `fork`** when `origin` is the upstream project, and set the branch's upstream to it (`git push -u fork <branch>`).
- **No fork yet:** create one in `Sparky-OS` with `gh repo fork <owner>/<project> --org Sparky-OS --clone=false --remote=false`, then add it as `fork`.
  A project hosted outside GitHub with an official GitHub mirror (Blender's `blender/blender`) is forked from the mirror; the history is identical, so only our commits travel.
- **Push branches, not over the fork's main**, unless the fork's main is the edition's own line.
  Edition branches are named after the work (`stereo3d`, `stereo3d-6.7`, a feature name).
- **KDE Invent runs CI on every push.** Push a branch you do not want tested yet with `git push -o ci.skip invent <branch>`; never use upstream CI as a test bench.

## Failures that cannot be filed upstream

Keep a failure with its evidence even when its report cannot go upstream.
Use the [unfiled failures recipe](references/unfiled-failures.md) for the inventory, the issue template, duplicate counting and checking whether upstream has fixed it since.
The destination is the repository Daniel approved in his own namespace; the current KDE list uses one repository on Invent for issues alone.
An inventory or draft does not authorize creating that repository, posting issues or sending mail.

## A fork ships; it is not a waiting room

Daniel, 2026-10-23, on a plan that called the edition's forks "awaiting upstream".

- The work in the edition's forks runs in the edition: it ships in its packages, on every image.
  Carrying changes a project is not ready to take is how open source has always worked, and forks first is the edition's own order.
- Never write "awaiting upstream", "not yet upstream" or "pending acceptance" as a judgement on the work.
  Those words adopt a measure where work counts only once a gatekeeper accepts it.
- Where projects judged the work on its merits, it merged: those merges are the record of its quality, kept in one list as [`upstream-outreach`](../upstream-outreach/SKILL.md) says.

## Branches

Daniel, 2026-11-16: "why do we have so many brenches? consolidation is due, that also explain lost progress and rework, like the kernel source lost".
That day the edition's three repositories had 81, 219 and 9 branches online, and 71, 215 and 8 of them were already inside main.
Those 294 were deleted, the three repositories were set to delete a merged pull request's branch by themselves, and 15 branches stayed with work outside main and no recorded reason.

### Recipe

1. **One branch per piece of work, named by its number first:** `order612-branch-keeper`.
   Before making it, look for every branch that carries the same number, in every repository, local and online, and build on what exists instead of starting over:
   `git for-each-ref --format='%(refname:short)' refs/heads refs/remotes | grep -E '(^|[^0-9])612([^0-9]|$)'`.
2. **Pushed to our fork the same day**, as the [working recipe](#working-recipe) says. A branch that lives in one clone only is not done.
3. **Gone at the merge, online and locally.** The edition's repositories delete a merged pull request's branch by themselves; a branch merged with `git merge` is deleted with `git push REMOTE --delete BRANCH` once main is pushed; every clone deletes its copy with `git branch -d BRANCH` after `git fetch --prune`.
4. **Every branch outside main has a reason.** It is merged, or it has a row in the register: one private file, never in a repository that has a remote, with repository, branch, `kept` or `superseded`, the reason and the date, separated by tabs.
   Kept says what it is kept for; superseded says what replaces it.
   A squash or rebase merge is never inside main by ancestry, so its branch gets `superseded`, "squash-merged as COMMIT", before it is deleted.
5. **Nothing is removed before it is somewhere else.** Before a clone, a worktree, a branch or a stash goes: its commits on our fork or in a bundle in the lane folder, its uncommitted files committed on a branch ([uncommitted work](#uncommitted-work)), its stashes made branches (`git stash branch NAME stash@{0}`), its linked worktrees removed first.
6. **A clone traced piece by piece goes with a row.** When an audit proved that every local commit and every uncommitted file of a clone is in main by content, delivered another way, superseded or scratch ([the trace](references/lessons-2026-11.md#tracing-work-left-in-a-build-folder-order-617-2026-11-16)), write one row for the clone's own folder in the clones register, the second private file: full path, verdict, proof, and the date and time of the trace (`2026-11-16T03:43Z`), separated by tabs.
   The row lets that clone go and no other (not the clones inside a folder it names), and stops counting when anything in the clone is newer than its date: trace again, write again.
7. **A remote branch in main by content goes without a row,** as a local one does: `git cherry origin/main origin/BRANCH` with only `-` lines. A `kept` row still stops it.

The hook [branch-keeper](../../hooks/branch-keeper/README.md) stands at each of these moments: at session start it says, per repository, the branches outside main with their reasons and the work on no remote; it refuses `rm -r` of a clone or a worktree, `git branch -D`, the deletion of a remote branch and `git stash drop` or `clear` when they would lose work that exists nowhere else; it shows a new branch every branch with its number; it reminds a merge that the branch goes, and clears the register row of a branch once it is inside main.
It reads each command of a line in the folder that line's own `cd` gives it, so one line may visit several clones; a folder or a branch written as a shell variable (`git -C $R`, `for r in ...; do git -C /X/$r ...`) is refused for a deletion and said for anything else: write deletions with literal folders and names, one command per repository.

### The audit of branches

```sh
python3 hooks/branch-keeper/hook.py audit [--fetch] [--config FILE] [REPOSITORY...]
```

It prints, per repository, every branch outside main (where it is, how many commits main lacks, its last date, its reason or NO REASON RECORDED), the branches inside main that still exist, the branches with commits on no remote, the stashes and the uncommitted files; then each row of the clones register with `counts`, `DOES NOT COUNT`, `NO LONGER COUNTS` (what changed since the trace) or `folder gone`.
Exit status 0: nothing owed; 1: a branch outside main without a reason, work on no remote, or a clones row that does not count; 2: something could not be read.
`--fetch` is its only network use; without it the answer is as of each clone's last fetch, which it states.

The same questions by hand, after `git fetch --prune`:

```sh
git for-each-ref --no-merged=origin/main --format='%(refname:short) %(ahead-behind:origin/main) %(committerdate:short)' refs/heads refs/remotes/origin
git for-each-ref --merged=origin/main --format='%(refname:short)' refs/heads refs/remotes/origin   # inside main: they can go
git rev-list --branches --not --remotes --oneline                                                 # on no remote
git stash list
```

`--remotes` counts every remote, including a folder on the same machine; only a network remote is online, which the hook checks and this line does not.

### Traps of 2026-11-16

- **Symptom:** hundreds of branches online, most of them already inside main (215 of 219 in this repository).
  **Cause:** nothing deleted a branch at its merge, online or locally.
  **Fix:** the repositories delete a merged pull request's branch; the hook's reminder at the merge; `git branch -d` in each clone after `git fetch --prune`.
  **How found:** `git for-each-ref --merged=origin/main` counted against all the remote branches, repository by repository.
- **Symptom:** work redone, or lost, after a cleanup ("lost progress and rework, like the kernel source lost").
  **Cause:** the losses seen so far came from work outside git or in one local clone only, so removing the folder removed the only copy.
  **Fix:** push or bundle first; the hook refuses `rm -r` of a clone whose work is on no remote; the audit of clones and stages is part of consolidation.
  **How found:** the consolidation of 2026-11-16, which traced the losses to their places.
- **Symptom:** fifteen branches outside main that nobody could explain.
  **Cause:** no place recorded why a branch stays.
  **Fix:** the register; the audit exits 1 while a branch outside main has no row.
  **How found:** `--no-merged` after the merged branches were deleted.
- **Symptom:** after a pull request merged, its branch is still outside main and `git branch -d` refuses it.
  **Cause:** a squash or rebase merge makes new commits, so the branch's own commits never become part of main; git deletes with `-d` only a branch that "must be fully merged in its upstream branch, or in HEAD if no upstream branch was set" (git-branch(1)).
  **Fix:** a `superseded` row naming the squash commit; then `git branch -D` and the remote deletion pass the hook.
- **Symptom:** `rm -r link/` leaves the link and empties the folder it points to.
  **Cause:** GNU rm resolves a symbolic link named with a trailing slash.
  **Fix:** name a link without the slash; the hook looks inside the target in that one case and never follows a link inside a folder.
  **How found:** measured in a scratch folder on 2026-11-16: "cannot remove 'link/': Not a directory", and the file inside the target was gone.
- **Symptom:** a check of a clone finds nothing to lose although the clone has local commits.
  **Cause:** its `.git` could not be read, so git looked upwards and answered for the repository around it.
  **Fix:** compare `git rev-parse --show-toplevel` with the folder asked about; the hook refuses when they differ.
  **How found:** a test with an unreadable clone inside another repository.
- **Symptom:** commits count as online that no hosting service holds.
  **Cause:** `--remotes` counts a remote that is a folder on the same machine (a test remote, another lane's clone) and a remote-tracking ref of a remote that was removed.
  **Fix:** count only remotes with a network address; the hook does (`online_remotes`).
  **How found:** the online audits of lane clones (ORDER 351b) found work counted online whose only remote was another lane's folder.

**In main by content.** `git cherry origin/main BRANCH` with no `+` line means each of its commits has an equivalent change in main; the branch can go although its hashes are in no remote. The hook reads this itself, for a local branch and for a remote one. On 2026-11-16 that settled 36 old local branches of one clone in one command.

The four traps of the hook's first day (a remote branch in main by content refused, a traced clone that could not go, a long line read in the wrong folder, a shell variable in a path) are in [the lessons](references/lessons-2026-11.md#the-branch-hooks-first-day-order-612c-2026-11-16).

## The audit

Fetch first, so the answer is about today's remotes:

```sh
git fetch --all --prune
git status --porcelain -uall | wc -l          # uncommitted and untracked files, counted one by one
git log --branches --not --remotes --oneline   # commits that no remote branch holds
git for-each-ref refs/heads --format='%(refname:short) %(upstream:short) %(upstream:track)'
```

Across many clones, loop over every `.git` folder with `find <root> -maxdepth 3 -name .git` (no `-L`: never follow symlinks into other trees) and record the fetch exit code too: a failed fetch means the answer is stale.

Sort each local-only branch before pushing anything:

- **`[gone]` upstream with local commits:** the remote branch was deleted after its pull request was squash-merged, so the commits look unpushed while their content is on main.
  Confirm with `gh pr list -R <owner>/<repo> --head <branch> --state all`; when it says MERGED, the work is online and the local branch can be deleted.
  No pull request, or a closed one: the content may exist only here; push it again or ask.
- **Ahead and behind the same-named remote branch:** the remote branch was rewritten.
  Run `git cherry -v <remote>/<branch> <branch>`: a `-` line has an equivalent commit online; a `+` line does not.
  Then read the remote branch's subjects: a reworked version of the same change (a later draft) means the local commit is superseded, not missing.
- **No upstream at all:** look for our fork, add it, fetch it and count again. The same work is often already there, pushed from another clone.
- **A commit in no branch** (reachable only by hash, for example from a report): check `git cherry -v origin/main <hash>`; a `-` means an equivalent commit is online.
- **A folder that is a worktree:** `git rev-parse --git-common-dir` shows the real repository, which may be a partner's clone elsewhere; remotes are configured there.
- **Partial clones** (`blob:none`) push normally; only the missing blobs are fetched when needed.

## Uncommitted work

- **Count files one by one before committing.** `git status --porcelain` shows an untracked folder as one line; one such line held 80,844 files.
  Use `-uall`, and look at the largest folders (`git status --porcelain -uall | awk -F/ '{print $1"/"$2}' | sort | uniq -c | sort -rn | head`) before deciding what belongs in the commit.
- **Read it before it goes online.** Run the repository's own audit when it has one (for example `tools/public-audit.sh`), search for keys, tokens, private addresses and personal paths, and stop on any hit.
- **Keep work online without touching the working tree or the current branch** by committing through a temporary index onto a new branch:

  ```sh
  export GIT_INDEX_FILE=$(mktemp -u)
  git read-tree HEAD
  git add -A -- <the paths you reviewed>
  tree=$(git write-tree)
  commit=$(git commit-tree "$tree" -p HEAD -m "<what it is, and that it is work in progress>")
  unset GIT_INDEX_FILE
  git branch wip/<name-and-date> "$commit"
  git push -u <our-remote> wip/<name-and-date>
  ```

  The working tree, the real index and the checked-out branch stay exactly as they were.
- **Leave alone what a handoff says to preserve**, such as a dirty submodule kept as evidence.
- **Ask Daniel first** about a branch named `private/...`, a repository with no remote, or a first commit to a repository that is still empty online.

## Daniel's protected repositories

Daniel's own repositories require a review on main, which keeps outside changes reviewed.
For our own reviewed change: open a pull request, wait for its checks, then merge it with Daniel's administrator bypass (`gh pr merge <n> --repo <owner>/<repo> --squash --admin --delete-branch`), one merge per command.
A link check that fails on a line the pull request does not touch (a third-party page answering 500 or 503) is the outside site, not the change: re-run the failed job (`gh run rerun <run> --failed`) and merge when it passes.
Never use the bypass on someone else's pull request or on a repository Daniel does not own.

## Releases, the Sponsor button, our own libraries and large files

- **A GitHub release is permanent where Zenodo archives it.** Since 2026-10-12 Zenodo archives every new release of the repositories Daniel switched on, forks among them, as a snapshot with a DOI that cannot be deleted, listed in his ORCID record.
  - Cut releases on purpose, as versions people cite: a list after it has really grown, the edition at its ISO.
  - Never use a release for a temporary download there; use a draft release, the edition's own download server, or a repository that is switched off.
  - Never cut a release in a switched-on fork: its DOI would name Daniel as the creator of someone else's project.
  - Before a repository's first release, add `.zenodo.json` and `CITATION.cff` (as this repository has), and check the citation file with `cffconvert`.
- **The Sponsor button is for our own work only** (Daniel, 2026-10-23).
  - Turn it on for a repository that is the edition's or Daniel's own work: GraphQL `updateRepository(input: {repositoryId: ..., hasSponsorshipsEnabled: true})`.
  - Keep it off on forks, on upstream programs carried with our patches, on partners' projects, and on a program its creator keeps in the organization (org.kde.video is Jeromy Streets's, wiz3D is effcol's).
    A button on someone else's code reads as taking money for their work.
  - The `FUNDING.yml` in the organization's and Daniel's `.github` repositories names Daniel's GitHub Sponsors and SparkyLinux's donation page, and every repository without a file of its own shows both.
    A fork's or port's own `FUNDING.yml` stays as it is.
- **Our own library or format gets a public repository** (Daniel, 2026-10-14: "this is a default yes and a must").
  - A library or tool that the edition's packages use gets `Sparky-OS/<name>` at its first accepted release, such as [stereo-layer](https://github.com/Sparky-OS/stereo-layer).
  - It also gets a mirror on KDE Invent, `danielcamposramos/<name>`, whose description ends "(mirror of github.com/Sparky-OS/<name>)".
    Invent refuses a branch named `main`, so push `main:master` there.
  - The Invent mirror carries the same history without `po/` (`git filter-repo --path po --invert-paths`), because Invent refuses translation commits ([`contrib-kde`](../contrib-kde/SKILL.md)); GitHub keeps the whole repository.
  - A format or namespace we define gets its specification page at the URI it names before the format appears anywhere public, as [SVGStereo](https://github.com/Sparky-OS/svgstereo) did.
- **Large files never go to GitHub** (Daniel, 2026-10-12), neither as release assets nor as committed files: ISOs, builds, root file systems, virtual machine images, package sets and toolchains.
  - They go to the edition's own download server: a plain folder with a `README.txt` for a public download the documents link to, a folder no page lists for a private one.
  - Put `SHA256SUMS` beside the files, and check it on the server after the upload.
  - It keeps the DOIs clean too, since a release in a switched-on repository is archived for good.

## Partners and hand-backs

- A partner commits in its own clone; whoever integrates the work pushes it to the fork the same day and writes the branch and commit into the report.
- A hash in a report or receipt should resolve to a remote branch or a tag. After a batch of hand-backs, check every hash with one `git cat-file --batch-check` per clone, then `git branch -r --contains <hash>` for the commits found.
- Author commits as Daniel Campos Ramos <Capitain_Jack@yahoo.com> and name the model that actually helped in the trailer the project expects, as [`ai-partners`](../ai-partners/SKILL.md) describes.

## Never

- Push to an upstream project's repository or to SparkyLinux's own repositories.
- Force-push over a branch someone else may have built on, or delete a remote branch you did not create.
- Publish a file you have not read, or credentials of any kind.
- Put a large file on GitHub, or cut a release in a switched-on fork.
- Report work as online before the audit above says so.

## Bringing a fork up to a packaged recipe

[Fork to recipe patch stack](references/fork-to-recipe-patch-stack.md) holds the recipe: patches to commits with their authors, the tree check against the packaged source, the baseline of fork-only files, reference branches on Invent, and the traps (ORDER 445, KWin +stereo3d42 to +stereo3d46).

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (5 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
