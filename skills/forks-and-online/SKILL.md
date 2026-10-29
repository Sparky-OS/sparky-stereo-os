---
name: forks-and-online
description: >-
  Push edition work only to the edition's forks, never upstream; keep every branch online the same day; audit clones for work that exists only locally and tell merged, superseded, missing and uncommitted work apart.
---

# Forks and keeping the work online

## Working recipe

1. Before any push, read the push address: `git remote -v`. In many clones `origin` is the upstream project, not our fork.
2. Push only to the edition's forks (table below), as a branch, the same day the work exists. Work that is only on one disk is not done.
3. Before saying something is online, audit: fetch every remote, list what no remote holds, and sort it with the rules below.
4. Read what you publish. Run the repository's own audit, if it has one, and look for credentials before the first push of anything new.
5. Record what you pushed (repository, branch, commit) where the task's report or receipt lives.

**Check freshness first.**
Written on 2026-10-29, after a full audit of more than a hundred clones found work that had been reported as done but was never pushed, and clones whose `origin` was the upstream project.
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

## Partners and hand-backs

- A partner commits in its own clone; whoever integrates the work pushes it to the fork the same day and writes the branch and commit into the report.
- A hash in a report or receipt should resolve to a remote branch or a tag. After a batch of hand-backs, check every hash with one `git cat-file --batch-check` per clone, then `git branch -r --contains <hash>` for the commits found.
- Author commits as Daniel Campos Ramos <Capitain_Jack@yahoo.com> and name the model that actually helped in the trailer the project expects, as [`ai-partners`](../ai-partners/SKILL.md) describes.

## Never

- Push to an upstream project's repository or to SparkyLinux's own repositories.
- Force-push over a branch someone else may have built on, or delete a remote branch you did not create.
- Publish a file you have not read, or credentials of any kind.
- Report work as online before the audit above says so.
