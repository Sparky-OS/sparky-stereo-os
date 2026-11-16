# branch-keeper

**For** anyone whose work lives in git clones that partners and people share: branches stay few, every branch outside main has a recorded reason, and no command removes the only copy of a piece of work.

## What it does

| Event | What happens |
| --- | --- |
| Session start, and after a compaction | For each configured repository, read from its local refs: the counts first (branches not inside main and how many have no reason, branches inside main that still exist, local branches with commits on no remote, stashes, uncommitted or untracked files), then at most `max_names` names in each list, each branch outside main with its row from the register or the words NO REASON RECORDED, and how old the last fetch is. A repository that cannot be read is said, never left out. |
| Before `rm -r` of a folder that is, or holds, a clone, a worktree, a bare repository or a repository's `.git` | The folder is searched first. Refused when the removal would lose commits that no online remote and no bundle holds, uncommitted or untracked files (ignored files apart), stashes, commits of a detached HEAD in no branch, or a linked worktree's repository. Nothing to lose: it passes without a word. |
| Before `git worktree remove` | Refused when the worktree holds uncommitted or untracked files or commits of a detached HEAD in no branch. Its branch stays in the clone, so commits on it only bring a line of context. |
| Before `git branch -D` (or `--delete --force`) | Refused when the branch holds commits that no online remote, no bundle and no other local branch or tag holds, unless the register marks it superseded with a reason. |
| Before a deletion of a remote branch (`git push --delete`, `git push REMOTE :BRANCH`, `git push --mirror` or `--prune`, `gh api -X DELETE .../git/refs/heads/BRANCH`) | Passes when the branch is inside main. Otherwise refused unless the register marks it superseded with a reason; a branch the clone has not fetched cannot be judged and is refused with the command to fetch. |
| Before `git stash drop` or `git stash clear` | Refused while that stash exists, with the way to keep it: `git stash branch NAME STASH`, then push or bundle. |
| Before a new branch (`git switch -c`, `git checkout -b`, `git branch NAME`, `git worktree add -b`, a first push of a new name) | The rule as context, and every branch, local or online, in any configured repository, that carries the same work number, so nobody starts over work that exists. A name outside `name_patterns` is told, asked or refused, as `name_rule_outside` says. |
| Before a merge into main (`gh pr merge`, `git merge` of a branch while main is checked out) | The branch goes, online and locally; for a squash or rebase merge, the register row to add before deleting it; the branch's register row, if it has one. |
| After a merge, a push, a fetch or a branch command | A register row whose branch is now inside main (local or online), or a superseded row whose branch exists nowhere any more, is cleared; the whole row goes to `cleared.log`. The same happens at session start and in `audit`. A kept row whose branch is gone is said as KEPT WORK GONE, an undecided one as a row without its branch, and both stay. |

The hook deletes, pushes and fetches nothing.
Every git command it runs reads only: `GIT_OPTIONAL_LOCKS=0` keeps `git status` from writing the index, `GIT_NO_LAZY_FETCH=1` and `-c protocol.allow=never` keep a partial clone from downloading behind its back, and `GIT_DIR`, `GIT_INDEX_FILE` and their kind are taken out of its environment so each command reads the folder it names.

### The audit, from the command line

```sh
python3 hooks/branch-keeper/hook.py audit [--fetch] [--config FILE] [REPOSITORY...]
```

It prints the whole table per repository: each branch not inside main with where it is (local, online or both), how many commits main lacks, the date of its last commit and its reason; the branches inside main that still exist; the branches with commits on no remote; stashes; uncommitted and untracked files.
`REPOSITORY` is a configured name or any folder; a folder not configured is read with the defaults.
`--fetch` runs `git fetch --prune` on each repository's remote first, the only network use; a failed fetch is said and counts as not read.
Exit status: 0 when nothing is owed, 1 when a branch outside main has no reason, any work is on no remote (commits, stashes, uncommitted files) or a register row's branch is gone, 2 when something could not be read (a repository, the register, a fetch).
That is what a person, a lane check or a publication round calls.

### The register

One private file, `private/branches.tsv` in the default layout (`paths.register`), one row per branch outside main, fields separated by tabs:

```text
repository	branch	kept or superseded	reason	date
```

`repository` is the configured `name` (default: the folder's name), `branch` the name without its remote.
Only `kept` or `superseded` with a reason counts as a reason; any other state is shown with its text and still counts as none, so the audit stays at 1 until someone decides.
The register is never read from inside a repository that has a remote: the hook says so and reads no reason from it.

## Why

Daniel, 2026-11-16: "why do we have so many brenches? consolidation is due, that also explain lost progress and rework, like the kernel source lost".
That day 294 branches already inside main were deleted from the edition's three repositories and fifteen branches were left with work outside main and no recorded reason; lane clones held commits that no remote had.
The rule of [forks-and-online](../../skills/forks-and-online/SKILL.md#branches) is one branch per piece of work, named by its number, pushed the same day and gone at the merge, and every branch outside main merged, superseded with its reason or kept with its reason.
A rule that lives only in a skill is followed when someone remembers to load the skill; this hook stands at the moments where the rule is kept or broken: the session start, a removal, a new branch, a merge.

The design of its four parts is the edition's, not Daniel's words.

## Configuration

One file, `private/hooks/branch-keeper.json`; [`config.example.json`](config.example.json) shows every key.

| Key | Default | What it sets |
| --- | --- | --- |
| `enabled` | `true` | The whole hook. |
| `repositories` | this repository in `repos/` | Each repository the session start and the audit read: a path (relative to the workspace or absolute), or an object with `path`, `name`, `remote` (`origin`), `main` (found from the remote's `HEAD`, else `main` or `master`) and `deletes_merged_head` (the hosting service deletes a merged pull request's branch by itself; it changes the merge reminder). `install.py init` names this checkout when `repos/` does not hold it. |
| `paths.register` | `private/branches.tsv` | The register. `install.py init` makes it with its header. |
| `paths.queue` | `partners/queue` | Where bundles count as kept, unless `bundle_folders` names other folders. |
| `bundle_folders`, `bundle_depth` | the queue, 3 | Folders searched for `*.bundle` files, and how deep; a commit inside a bundle's tips counts as kept. |
| `on` | all `true` | `session_start`, `removal` (`rm -r`, `worktree remove`, `branch -D`), `remote_deletion`, `stash`, `branch_creation`, `merge_reminder`, `clear_settled_rows`. |
| `online_remotes` | `network` | Which remotes count as online: `network` (an `ssh`, `https`, `git` or `user@host:path` address), or `any`. A remote that is a folder on the same machine is not online, and neither is a remote-tracking ref of a remote that was removed. |
| `name_patterns` | `^order[0-9]+…`, `^wip/`, `^lane/` | The branch names that follow the rule: the work number first (`order612-branch-keeper`); `wip/NAME-DATE` for uncommitted work kept online and `lane/FOLDER/BRANCH` for a lane's work found by an audit, both from [forks-and-online](../../skills/forks-and-online/SKILL.md). |
| `number_pattern` | `order([0-9]+)` | Where the work number is in a name; existing branches are searched for that number as a whole number (612 does not find 6120). |
| `name_rule_outside` | `context` | A new name outside the patterns: `context`, `ask` or `deny`. |
| `on_unresolved_path` | `context` | An `rm -r` target the hook cannot resolve (a variable, a substitution): `context`, `ask` or `deny`. It is never passed in silence. |
| `max_names` | `10` | Names per list at session start; the audit lists all. |
| `scan_limit`, `scan_seconds`, `scan_depth` | 100000, 10, 12 | The search of a folder before `rm -r`; a search cut short by any of them refuses, because a pass without looking would say nothing is lost without knowing it. |
| `git_timeout_seconds` | `15` | Each git command; a command that takes longer is a failure to read, said as such. |

## How it fails

Open, and it says so, as every hook here: a failure inside the hook (a broken configuration, a value that is not `context`, `ask` or `deny`) lets the command through, is written to `errors.log` and is told to the person in one line.
A repository, a register or a folder it cannot read is not such a failure: the hook ran and could not look, so a removal or a deletion is refused with the reason, and the session start and the audit say NOT READ.
A clone whose `.git` cannot be read makes git answer for the repository around it; the hook checks that the repository it reads is the folder it was asked about.

Not seen: what a script file, an alias or a program started by another does; `rm` of files inside a work tree that is not a clone's top folder; `git reset --hard`, `git checkout -- .`, `git clean -fdx`; a clone nested in another clone's ignored folder (the search stops at a repository's top folder); a branch deleted on the hosting service's web page.
The hook trusts a bundle's header; the lane check unbundles each bundle in full.

Logs, in `state/hooks/branch-keeper/`: `refused.log`, `asked.log`, `cleared.log` (each cleared register row, whole), `errors.log`.

## Try it by hand

```sh
W=$(mktemp -d) && python3 hooks/install.py init "$W" >/dev/null
printf '{"hook_event_name":"SessionStart","source":"startup","session_id":"demo","cwd":"/"}' \
  | python3 hooks/branch-keeper/hook.py --config "$W/private/hooks/branch-keeper.json"
python3 hooks/branch-keeper/hook.py audit --config "$W/private/hooks/branch-keeper.json"
```

The first prints this checkout's branches as a session start would receive them; the second the whole table.
Nothing is changed in the checkout.

## Tests

`python3 hooks/tests/run.py branch-keeper` runs 41 tests in [`tests/`](tests/test_branch_keeper.py), on repositories made in a temporary folder with bare repositories as their remotes: every command shape above, refused and passing; quoting, `cd X &&`, `git -C`, a path with spaces, a loop, `bash -c`, a here-document a shell reads and one that is only written; a repository that cannot be read, and one inside another repository; a symbolic link to a clone, inside a folder and with the trailing slash `rm` follows; a bundle in the queue; the default rule for online remotes; the register cleared after a merge; the audit's exit statuses, `--fetch` and its options in any order; the Codex dialect.
Each rule was also taken out once and its tests failed (17 rules).

## Credits

What git does is read from its own manuals (git 2.53): [`GIT_OPTIONAL_LOCKS`](https://git-scm.com/docs/git#Documentation/git.txt-GITOPTIONALLOCKS) ("this will prevent git status from refreshing the index as a side effect") and [`git status`, background refresh](https://git-scm.com/docs/git-status#_background_refresh); [`--no-lazy-fetch` and `GIT_NO_LAZY_FETCH`](https://git-scm.com/docs/git#Documentation/git.txt---no-lazy-fetch); [`protocol.allow`](https://git-scm.com/docs/git-config#Documentation/git-config.txt-protocolallow); [`%(ahead-behind:)`, `--merged` and `--no-merged`](https://git-scm.com/docs/git-for-each-ref); [`git worktree list --porcelain -z`](https://git-scm.com/docs/git-worktree); the bundle header from [gitformat-bundle](https://git-scm.com/docs/gitformat-bundle) ("signature *prerequisite *reference LF pack").
The keep step before removing a clone, and the linked worktree left without its repository, are from the edition's [cleanup recipe](../../skills/system-housekeeping/references/shared-build-machine-cleanup.md); which remotes count as online, from the edition's audits of lane clones.

A branch whose every commit outside main is in main by content (`git cherry` shows no `+` line: a rebase, a cherry-pick, a squash of one commit) loses nothing when it goes: its deletion passes with one line, the session start lists it under "In main by content", and it is owed no reason. A branch whose several commits were squashed into one is not recognised this way and needs its superseded row.
