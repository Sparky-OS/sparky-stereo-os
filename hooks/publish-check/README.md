# publish-check

**For** anyone about to push, post or mail: one look at what is about to go public, before it goes.

It is three things that share one checker and one configuration file:
- [`publish_check.py`](publish_check.py), a command anyone runs on a draft, a picture, a repository or text on stdin;
- [`hook.py`](hook.py), the same check before an AI partner's shell command pushes or publishes;
- [`git/pre-commit`](git/pre-commit) and [`git/commit-msg`](git/commit-msg), the same check when anyone commits, person or partner.

## What it finds

| Finding | Kind | What to do |
| --- | --- | --- |
| Location data in a photo or a video | hard | The finding prints the `exiftool` command that strips it. |
| Another person's email address in our text | hard | Name the person and link the public page; contacts stay private. |
| A name the configuration lists under `never_name` | hard | Use the public wording the entry's `why` points to. |
| A secret: a forge token, a cloud key, a private key, a password written as a literal | hard | Remove it, and rotate it if it was real. |
| A dash in the middle of a sentence, a listed phrase, a hard-wrapped Markdown line | style | Fix it in our own text; text for another project follows that project's style. |

Addresses that are not a person's contact pass: our own identities, the allowed ones, addresses in commit trailers (`Signed-off-by:`, `Reviewed-by:`), copyright lines in code, message ids in archive links, and the domains reserved for examples.
Only our own commits are checked (the author is one of `our_identities`), and only those no remote has yet; a remote that matches `private_remotes_regex` is skipped.

## What each part does

| Part | Event | What happens |
| --- | --- | --- |
| The tool hook | Before a shell command that runs `git push` | Our unpushed commits are checked: their messages and the lines they add. |
| The tool hook | Before a shell command that publishes text (`gh issue`, `gh pr`, `gh release`, a `gh api` write, `git send-email`, the configured commands) | The command's own text and the files it sends are checked. A mail may name its recipients. |
| The tool hook | A hard finding | The person is asked (`on_hard_finding`: `ask`, or `deny`). Where a tool cannot ask from a hook, the call is refused and the reason says so. |
| The tool hook | Style notes only | They come back as context; nothing is stopped. |
| `pre-commit` | `git commit` | Staged paths of the private record (`evidence/`, `captures/`, any `REPORT*.md`) are refused, with or without a configuration. Then the staged version of every added or changed file is checked; a hard finding refuses the commit. Addresses in provenance files (copyright, changelog, patches) stay. |
| `commit-msg` | `git commit` | The message is checked; a hard finding refuses the commit. |

## Why

Daniel approved it on 2026-10-14: one check that runs before every push, pull request, comment and mail.
Each of its findings had been caught by hand at least once before the check existed: a photo with its location, a credential printed into a log, a name that is never published.

## Configuration

One file, `private/hooks/publish-check.json`, read by all three parts; [`config.example.json`](config.example.json) shows every key.
This is the file that holds a workspace's private lists, so it stays outside every repository.

| Key | Default | What it sets |
| --- | --- | --- |
| `enabled` | `true` | The tool hook and the git hooks. The command itself always runs. |
| `our_identities` | one example | The author addresses whose commits are ours. With none, no commit would be checked, and the command says so. |
| `allowed_emails`, `allowed_email_regex` | none; the forge's no-reply addresses | Addresses that may appear. |
| `never_name` | one example | Patterns that are never published, each with a `why` shown in the finding. |
| `private_remotes_regex` | remotes ending in `.private` | Remotes whose pushes are not checked. |
| `checks.never_name`, `.secrets`, `.emails`, `.location_data`, `.style` | all `true` | Each check, switched on its own. |
| `style.mid_sentence_dash`, `.hard_wrapped_markdown`, `.phrases` | on; on; "the owner" | The style notes. A phrase in quotes names the phrase and passes. |
| `on_hard_finding` | `ask` | What the tool hook answers on a hard finding: `ask` or `deny`. |
| `ask_becomes` | `deny` | What an "ask" becomes where the tool cannot ask from a hook: `deny` or `context`. |
| `publish_commands`, `mail_commands` | none; two | More commands that publish or mail, as patterns. |
| `never_commit_paths_regex`, `provenance_paths_regex` | see the example | What `pre-commit` refuses by path, and where addresses stay. |

For the git hooks, name the file once per repository: `python3 hooks/install.py git REPOSITORY WORKSPACE` prints the two `git config` commands.

## How it fails

The tool hook fails open and says so, like every hook here.
The git hooks say so on the terminal: without a configuration, or with one that cannot be read, they print that the check did not run and that the commit goes ahead unchecked.
The private-record paths are refused even then, because that check needs no configuration.
A picture is never passed unchecked: without `exiftool` the finding is "location data NOT checked", which is hard.
The command exits 0 when clean or with style notes only, 1 on a hard finding, 2 on a usage or setup error.

## Try it by hand

```sh
W=$(mktemp -d) && python3 hooks/install.py init "$W" >/dev/null
C="$W/private/hooks/publish-check.json"
printf 'It works \342\200\224 on every screen.\nAsk the owner.\n' | python3 hooks/publish-check/publish_check.py --config "$C" --text
python3 hooks/publish-check/publish_check.py --config "$C" --files README.md
```

The first command prints two style notes and exits 0.

## Tests

`python3 hooks/tests/run.py publish-check` runs 28 tests in [`tests/`](tests/test_publish_check.py): the checker, the tool hook and both git hooks in real repositories made for the test.
The secrets and addresses they plant are put together while the test runs, so the test file itself passes the check.
