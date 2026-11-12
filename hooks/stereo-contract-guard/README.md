# stereo-contract-guard

**For** anyone who writes briefs, drafts or patches for the edition: a tool call that would carry a broken stereo contract into a lane brief, a text for another project or a pushed branch is stopped and put to the person.

## The contract it guards

Programs read every stereo input and hand the desktop one format: full side by side, left eye first, declared once.
The formats a screen needs are made by the desktop's outputs only: Stereo KWin, KScreen and gamescope.
In a program, anaglyph is input only: the program detects an anaglyph picture and rebuilds the pair.
The whole contract is in [the sparky-stereo skill](../../skills/sparky-stereo/SKILL.md).

## What it does

| Event | What happens |
| --- | --- |
| Before a write or an edit of a file under the lanes' queue or the drafts folder | The new text is read sentence by sentence. |
| Before a shell command that publishes text (`gh issue`, `gh pr`, a `gh api` body, `git send-email`, the configured commands) | The command's text and the files it sends are read the same way. |
| Before a shell command that appends to a brief or a draft with a here-document | The same. |
| Before a shell command that runs `git push` | The commits no remote has yet are read: the lines they add, and the files in the pushed tip. |
| A finding | The person is asked, with each finding, its rule and its fix. Nothing else is ever stopped. |

The four checks, each with its own switch:

| Check | What it finds | What passes |
| --- | --- | --- |
| `program_output_modes` | A sentence that gives a program a screen format of its own to show, and an added code line that does so in a repository outside the display stack. | Input wording (detect, convert, rebuild), the desktop's outputs, a virtual monitor of the compositor, and any sentence that says never or not. |
| `declaration` | A declaration that is not full side by side, left eye first. | A file or a stream that is read or unpacked in another packing. |
| `keeping_own_modes` | A sentence where a program's own stereo modes stay beside the declared pair. | A sentence where they go, are removed or are hidden. |
| `lane_notes_in_push` | Reports, briefs, next prompts and evidence folders in the tip about to be pushed. | The same files once a later commit removed them. |

A program's own stereo modes go in the edition's build, and that is not removing functionality: Stereo KWin gives every program every output on every screen.

## Why

Daniel, 2026-10-09: "time to start putting some hooks partner, this is wasting my precious money".

A sentence in a brief becomes code, and a sentence in a draft becomes a post on another project, so that is where the guard stands.

## Configuration

One file, `private/hooks/stereo-contract-guard.json`; [`config.example.json`](config.example.json) shows every key.

| Key | Default | What it sets |
| --- | --- | --- |
| `enabled` | `true` | The whole hook. |
| `checks.program_output_modes`, `.declaration`, `.lane_notes_in_push`, `.keeping_own_modes` | all `true` | Each check, switched on its own. |
| `watch_write_paths` | the queue and the drafts folder | The folders whose writes are read. |
| `display_stack` | KWin, KScreen, gamescope and their kin | Words in a repository's path or remote that mark it as part of the display stack, where output code belongs. |
| `allow_words` | none | More words that make a sentence pass, for a workspace's own display projects. |
| `lane_paths_regex` | reports, briefs, evidence | What counts as lane notes in a push. |
| `publish_commands` | none | More commands that publish text, as patterns. |
| `on_finding` | `ask` | `ask`, or `deny`. |
| `ask_becomes` | `deny` | What an "ask" becomes where the tool cannot ask from a hook: `deny` or `context`. |

## How it fails

Open, and it says so: a failure inside the hook lets the call through, is written to `errors.log` and told to the person in one line.
It reads sentences with patterns, so it can ask about a sentence that is fine; then the person says yes, and a word that keeps coming up goes into `allow_words`.
A finding is a stop, not an argument: fix the text or the code.

Logs, in `state/hooks/stereo-contract-guard/`: `findings.log`, `errors.log`.

## Tests

`python3 hooks/tests/run.py stereo-contract-guard` runs 13 tests in [`tests/`](tests/test_stereo_contract_guard.py): eight sentences that break the contract and twelve that keep it, the switches, pushes from real repositories made for the test.
The sentences that break the contract are put together while the test runs, so the test file holds none the guard would stop.
