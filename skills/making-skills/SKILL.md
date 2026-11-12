---
name: making-skills
description: >-
  Make, extend, check and review a skill: the folder and its name, the
  header and its limits (64 and 1024 characters, the index window of 256 tokens counted by check-skills.py --count),
  the description as a trigger clause, the recipe first, each trap with symptom, cause, fix and how it was found,
  references and lessons files, requires-packages, the task table, the review that walks every rule against the
  diff, the cold-reader and small-model test. Load it to save what was learned for another contributor, move long
  troubleshooting notes, record a workaround not measured yet, or when a skill is never found for its symptom, find returns
  nothing, a description lost its last triggers, check-skills says over the index's window, a heading moved and links
  broke, a lesson was merged before the hardware ran, the next round broke a rule a skill already taught, or a brief
  names a skill to leave behind. Not for briefs and hand-backs (ai-partners) or hooks (development-hooks).
---

# Making a skill, and keeping it true

**Check freshness first.**
Written on 2026-11-12 by Claude Fable 5.2 with Daniel, from the practice that had grown inside [ai-partners](../ai-partners/SKILL.md) and from this repository's own history.
The format's limits were read that day from [agentskills.io/specification](https://agentskills.io/specification); read them again before relying on a number.

Daniel, 2026-10-07, on why the skills are public: the solutions "shall become one of our skill sets ... by doing so, we also facilitate contributions - and show anti-ai people how it's done properly".
Daniel, 2026-11-06: "we register skills as we go to make the next work easier to tackle and by doing so, we do the hard consuming part once and keep enhancing as we go, each time better and better"; "the easier we make, the less energy other people and partners will spend".
The same day he called the skills "the spine so humans also can bennefit".
A skill is written while the work happens, not reconstructed after it, and the skill folder is the one place the next person looks.

## Working recipe

1. **Extend or start new.** Find the skill that owns the part: `sparky-stereo-skills find "<the symptom, as a person would type it>"`, then the [task table](../README.md). Extend it; start a new skill only for a new kind of work ([which](#extend-or-start-a-new-skill)).
   The helper comes with the `sparky-stereo-skills` package; without it, read the task table and search the folder for the error's own words (`grep -rn "<the error string>" skills/`).
2. **Make the folder:** `skills/<name>/SKILL.md`, with `references/` beside it when the detail asks for one ([the folder and the name](#the-folder-and-the-name)).
3. **Write the header:** `name`, `description`, and `metadata: requires-packages` for a skill that only matters where a package is installed ([the header and its limits](#the-header-and-its-limits)).
4. **Write the description as a trigger clause and count it:** `python3 tools/check-skills.py --count <name>` prints `NNN of 256 tokens  NNN of 1024 characters`. Both numbers stay at or under their limit: 256 tokens and 1024 characters pass, one more fails ([the description](#the-description-routes-the-body-executes)).
5. **Write the body, recipe first:** the commands in order with the result to expect from each, then each trap with its symptom, cause, fix and how the cause was found ([what goes in](#what-goes-in-each-time)).
6. **Move detail to `references/`,** and the lessons of a review to `references/lessons-YYYY-MM.md` ([references and lessons](#references-and-lessons-files)).
7. **Register it:** a row in the [task table](../README.md) (one line: the task in a person's words, then the link to the skill), a row in [sparky-stereo's part four](../sparky-stereo/SKILL.md#part-four-which-skill-next), a link from each neighbour skill.
8. **Run the checks:** `python3 tools/check-skills.py` must print `PASS: N skill headers, descriptions within 1024 characters and the index window of 256 tokens, and local file targets in N instruction/reference pages`; then the publish check on every changed file ([the checks](#the-checks)).
9. **Hand it back with the work.** The hand-back's "Skill changes" names the branch, the commit and what each change saves the next worker; the review walks every rule against the diff ([the review](#reviewed-with-the-work)).
10. **Test that it is found and followed** by a reader who was not there ([the test](#found-and-followed-by-a-cold-reader)).
11. **After the merge, rebuild what is derived:** every index is made from the files, and the skills package takes the reviewed commit.
    Check the package's exported tree too: the skills, their linked pages and the hook programs must come from that same commit ([the archive trap](#traps-this-project-met)); the package's recipe is `packages/sparky-stereo-skills/build.sh` in the edition's build repository.

## Extend or start a new skill

Extend the skill that owns the part before creating a new one.
A new skill is for a new kind of work; a new trap in an old kind goes into the old skill.
If you keep explaining the same fix, save what was learned in the skill that owns the part while the result is fresh, so another contributor can repeat it.
Use the [recipe and trap fields below](#what-goes-in-each-time); the run's logs stay in your evidence.
When the finder prints nothing, or two skills fit, the part belongs to the skill whose programs or error strings the symptom names; say the choice in the hand-back, and write the symptom into that skill's description or task row so the next search finds it.
A new skill is right when no existing name is where a reader would look: another project to contribute to (`contrib-<project>`, opening with "The rules that come first"), another layer of the system, another kind of work with its own recipe and checks.
This skill is an example: making a skill had become work of its own, with its own checks and traps, inside a skill about briefs.

When you extend, keep the skill's name and path, so installed copies and links keep finding it.
When text moves from one skill to another, move it and never keep two copies: the old place keeps its heading with one line that points to the new place, because other pages link to that heading.
Count those links first (`grep -rn 'SKILL.md#the-old-anchor' .`); see the traps.

## The folder and the name

```text
skills/<name>/
├── SKILL.md           the header, the recipe, the traps; readable in one sitting
├── references/        detail a step needs only sometimes, and the lessons files; one level deep
└── scripts/           a program the recipe runs, when it is too long to print
```

The name is the folder's name: lower-case letters, digits and single hyphens, at most 64 characters, no hyphen at either end.
It says what a reader would look for: the subject (`stereo-video`), the project (`contrib-ffmpeg`), the work (`writing-front-pages`).
Do not take a name an AI tool ships a skill under, such as `skill-creator`: a tool that finds two skills of one name shows one of them.
Check with `sparky-stereo-skills list` and with your own tool's list.
A program in `scripts/` ships with the skill and is run by its path, from a checkout or from the installed folder; the recipe names what it needs and the result to expect ([edition-packaging's scripts](../edition-packaging/scripts) are examples).

## The header and its limits

```yaml
---
name: stereo-example
description: >-
  What it is for, in one clause: the programs, components and error strings that bring a reader to it. Load it when
  SYMPTOM, SYMPTOM or SYMPTOM. Not for X (other-skill).
metadata:
  requires-packages: some-package | another-package
---
```

| Field | Limit | Source |
| --- | --- | --- |
| `name` | 1 to 64 characters, lower-case letters, digits and single hyphens, equal to the folder's name | the format: "Must match the parent directory name" |
| `description` | 1 to 1024 characters | the format |
| `name` plus `description` | 256 tokens, the start token and the end token the model adds included (`--count` counts them) | the index's embedding model: "input text longer than 256 word pieces is truncated" |
| `metadata` | text keys to text values | the format: "A map from string keys to string values" |
| `SKILL.md` | under 500 lines | the format: "Keep your main `SKILL.md` under 500 lines" |

- **No other field.** A field only one tool acts on stays out of a skill other tools must read ([serving skills over MCP](../ai-partners/references/skills-over-mcp.md#the-skill-format)).
- **`requires-packages`** names the Debian packages that make the skill matter, separated by `|`; `sparky-stereo-skills link` links the skill while one of them is installed.
  A skill without it always links: the contract, the working method, the skills about contributing.
  Write the line exactly as above, under `metadata:` with two spaces in front: the helper reads that line as text, so the same value written as `metadata: {requires-packages: ...}` or with four spaces is valid YAML that `link` never sees.
  Every package named must exist: `apt-cache policy NAME` shows a candidate from the archive you expect, the edition's or Debian's ([a dependency must exist](../ai-partners/SKILL.md#security-habits-for-what-an-assistant-writes)).
- **A long description is a folded block,** `description: >-`, as above. Whatever reads the header must parse it as YAML: a reader that takes the first line gets `>-` for a description.

## The description routes, the body executes

A skill is found by its `description`, in the task table, through `sparky-stereo-skills find`, and through any local search or MCP that embeds the skills (ours is ACIG's `consult_skills` over Qdrant, one point per skill, name and description embedded, the file path in the payload, two tiers merged: a general collection and the project's).
[Finding a skill locally](../ai-partners/SKILL.md#finding-a-skill-locally) has the three doors.
So the description is written as a trigger clause, within 1024 characters:

1. what the skill is for, in one clause;
2. then the symptoms, error strings, programs and components that should bring a reader to it, as a person would type them ("Show Screen Contents says the process is not authorized to take a screenshot", "dpkg-stereo restore says original-mismatch");
3. then what it is not for, naming the skill that is, when two skills sit close.

Measured on 2026-11-06 with 157 real symptoms from the lane reports (one skill expected for each): the old one-line labels found the right skill first for 23 % of them and in the top three for 41 %; the trigger clauses found it first for 58 % and in the top three for 82 %, with the same index and embedding (sentence-transformers/all-MiniLM-L6-v2 through FastEmbed, 384 dimensions).
The misses that remain are symptoms whose words belong to a neighbouring skill (a Debian error routed to `contrib-debian` instead of `edition-packaging`), which is why the third clause names the neighbour.
Keep the test: `data/routing/symptoms-157.tsv` of the skills engine (sparky-os/skills-mcp in the build tree), which every change to the engine or to the descriptions is checked against for the offline finder, and a symptom list for the embedded index, and add the symptom of every new lesson to it.
That file has two columns separated by a tab, the symptom and the skill that should answer it, and it lives with the engine in the build repository, so a new line there is a change to that repository.

**The window.**
The embedding model reads only the first 256 tokens of name plus description (FastEmbed's tokenizer truncates there), which is about 170 words of plain text and fewer when the words are technical names, each cut into several tokens.
On 2026-11-06 the seven longest descriptions had grown past that window and lost their closing symptoms until they were cut, so the words that route go early, and a description stays within the window, not only within 1024 characters.
Measure a description's tokens with the same tokenizer before trusting its tail.
Since 2026-11-12 the repository's own check does that measuring:

```sh
python3 tools/check-skills.py --count stereo-video
#  254 of 256 tokens   803 of 1024 characters  stereo-video
python3 tools/check-skills.py --count          # every skill, largest first; exit 1 when one is over
```

The count follows the model's own word list and rules, which ship in `tools/skill-window/`, so it needs no model, no download and no package beyond python3 ([how](../../tools/skill-window/README.md)).
When a description is at the window and a new lesson brings a new symptom, take a trigger out for the one you add, or shorten two.
Nothing is lost: the body and the lessons files keep every symptom, and the index of the bodies finds them there.

## What goes in, each time

- **The working recipe:** the commands, in order, and the result to expect from each (the count, the exit status, the line the log prints).
  A recipe is one that ran: say what was not run, and never print a command from recall.
- **Each trap you hit:** the symptom as it appeared (the exact error line or the wrong result), the cause, the fix, and how the cause was found (the log line, the tool or the command that showed it), so the next person can tell the same trap from a new one.
- **The part's own perks:** a shortcut, a property or a tool that makes the next job easier.
- **A measured fact worth keeping,** with its setup and date.
- **How each thing is known.** A lesson says whether it comes from reading the source, from a model of it, from a test, from the installed package or from the device ([evidence and status](../ai-partners/SKILL.md#evidence-and-status)); a prediction is written as a prediction, with the run that will test it.
  For a workaround not measured yet, write "Untested workaround" beside it, name the source that suggests it, and say which result would confirm or refute it.
  Keep it out of the working recipe until that run succeeds; replace the prediction with the measured result when it does, or correct it when it fails.
- **Public-safe always:** no machine paths, hosts, addresses, accounts, private plans or personal matters; generalise a fact about one machine ("on a host whose /tmp is a tmpfs") or leave it out and hand it to the coordinator's record.
  Cite evidence by what it is, never by where it lies: the order or the lane, the command, the count and the date; the logs themselves stay with the lane's report.
  Say "Daniel", never "the owner"; one sentence per line; no dash in the middle of a sentence; every rule tied to its clause, its commit or its measurement.
- **Never lose knowledge:** move detail into a reference, never delete a measured fact or a trap; correct what is wrong and say where the correction came from.
  A corrected statement replaces the wrong one in the page; the old wording stays in the repository's history.

Open the body with a "Check freshness first" line that says when it was written, so a reader knows how old its versions are.
Keep the short working recipe first and the detail in `references/`; a skill's `SKILL.md` stays readable in one sitting.
The format's limit is 500 lines; the skills of this folder run from about 50 lines to under 400.

## References and lessons files

- **A reference** holds what one step needs only sometimes: a long recipe, a table of cases, the record of a study.
  It opens with a bold lead, "**For** who: what they get", and `SKILL.md` links it with one line that says what it holds and how many traps.
  Link from `SKILL.md` to the reference, not from reference to reference in a chain.
  When troubleshooting notes make the page too long, move each whole trap with its symptom, cause, fix and evidence together, and keep a short pointer under any heading that has incoming links.
  Keep a procedure's steps together too; a reference starts where a reader has enough context to follow it.
- **The lessons files:** each skill that gained more than a few lessons in a review keeps them in `references/lessons-2026-11.md` (or the next date), grouped as recipes, traps, perks and facts, each entry naming the lane it came from; shorter lists sit at the end of `SKILL.md` under "Lessons from the lanes".
  As a rule of thumb, more than five lessons from one review make a lessons file.
  Read a skill's lessons before changing its part.
- **Write the symptom first in every lesson.** The index of the bodies embeds the first 256 tokens of each entry, and a search for the error string finds the entry only if the string is there.
- **The run's own history stays out:** logs, captures and the list of attempts are the lane's evidence, not the skill's text.
  Keep the operational rule in the skill, substantial conditional detail in a linked reference, and individual run history in its evidence record.

## The checks

```sh
python3 tools/check-skills.py                      # headers, both description limits, every local link
python3 tools/check-skills.py --count <name>       # this skill's size against its two limits
python3 tools/check-skills.py --anchors            # after a heading moved or changed its name: every local #fragment lands on a heading
python3 tools/tests/test_check_skills.py           # only when the checker or its data changed: "Ran 18 tests ... OK"
python3 hooks/publish-check/publish_check.py --config YOUR/publish-check.json --files skills/<name>/SKILL.md    # "publish-check: clean", exit 0
```

`check-skills.py` needs `python3` and `python3-yaml`, nothing else, and no network.
`YOUR/publish-check.json` is the file that `python3 hooks/install.py init WORKSPACE` writes to `WORKSPACE/private/hooks/`, with your own names put in ([adopt the hooks](../development-hooks/SKILL.md#working-recipe-adopt-the-hooks)).
It checks the header, the limits and that every local link's file exists, in the skills, in the pages of `hooks/` and `tools/` and in the two entry pages; with `--anchors` it also checks that each local link with a `#fragment` lands on a heading or an `<a id>` of its page; it does not check that a fact is true or that an external address answers.
For a heading you moved or renamed, search the repository for links to its old anchor, and keep the heading or leave `<a id="old-anchor"></a>` where the text now starts ([keep every link that points in](../writing-front-pages/SKILL.md#keep-every-link-that-points-in)).
The [publish check](../../hooks/publish-check/README.md) looks for what must never be in a public file: a person's address, a secret, a name that is never published.
The skills package runs `check-skills.py` when it is built, so a header that fails stops the package, not only the merge.

## Reviewed with the work

Every brief names the skill to leave behind and every hand-back has its "Skill changes" ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
The skill's diff is reviewed in the same review as the work's diff, by the same reader:

1. **Walk the skill against the work.** Open the skill that owns the part, every rule of it and not only the new lines.
   For each rule write what it forbids, then search the work's diff for that.
   The result is a table: the rule, what it forbids, what was searched, what was found.
   A rule the diff breaks stops the review, however green the tests are.
   A skill whose rules are walked often can hold the walk itself, each rule with the search that finds a breach, as [contrib-ffmpeg's audit](../contrib-ffmpeg/references/pre-push-audit.md) does.
2. **Walk the new lessons against their evidence.** For each new trap, open the log line, the capture or the measurement it names.
   A lesson that says "on the hardware" needs the run on the hardware; a number from a model of the code is a prediction until the device confirms it.
3. **Run the checks above yourself;** a hand-back's "PASS" is a lead.
4. **Read it as the next reader:** is the recipe first, does each trap start with its symptom, could someone who was not there run it?
5. **Merge the skill with the work,** then rebuild the indexes.

## Found and followed by a cold reader

A skill that only its author can find or follow is not finished.

- **Found.** For each new symptom, `sparky-stereo-skills find "<the symptom>"` on your checkout (`SPARKY_STEREO_REFERENCE=$PWD` in front) must print the skill among its first three; with a local vector index, ask the same symptom there after the rebuild.
  The offline finder reads the files as they are, so an edited description is searched at once; an embedded index answers from its last rebuild.
  The offline finder ranks words, not meaning: a symptom whose words appear in no description and no task row is not found until one of them names it.
- **Followed.** Give a reader who was not there only the skill and one task it covers: a model from another lab with no project context, or a person.
  Give `SKILL.md` alone first, since it must carry the recipe; add a reference only when the step of the task names it (`context <name> --reference PATH`).
  The reviewer chooses the reader, not the author.
  For a model without file tools, `sparky-stereo-skills context <name>` makes the text.
  Ask for the commands in order, the result to expect from each, and what it would do when a named trap appears.
  It passes when the answer needs no fact the skill does not hold; every question the reader asks and every step it invents is a line the skill lacks.
- **By a small model too.** The skill holds the knowledge and the model follows: exact commands, the expected result to check after each, one task per recipe.
  A recipe a small local model can follow is one a tired person can follow.
- **Honestly.** Record the answers word for word, say which reader read what, change one thing and test again.
  One question to one reader, with the text and nothing private in it; a call that is refused is recorded and not sent again in a loop.
  A self-review is not a cold reader, and one lab asked twice is one reader ([the newcomer test](../writing-front-pages/SKILL.md#the-newcomer-test)).
  This page had its own test on 2026-11-12: a model of another lab, given `SKILL.md` alone, answered the four questions of a task from the text and listed twenty-two things the page did not say; its list became lines of this page.

## Traps this project met

- **Symptom:** the skills check passes in a checkout but fails in the package's snapshot, or an installed recipe names a hook that is absent.
  **Cause:** a recipe's `git archive` path list includes `skills` and `tools` but omits `hooks`, even though the new pages link there.
  **Fix:** include `hooks` in the snapshot, keep executable scripts executable, and run the check on the exported tree; verify its `SOURCE` commit and `MANIFEST.sha256` too.
  **How found:** running the skills package's archive and validation steps in isolation on 2026-11-12 failed before the archive-list patch and passed with all 49 tracked hook files after it.
  That proves the archive step; installing a built package is a separate check.
- **Symptom:** a skill stops being found for the symptoms written last in its description; nothing fails anywhere.
  **Cause:** every review adds triggers, and name plus description passes the index's 256 tokens; the index embeds the head and drops the tail without a word.
  Nothing in this repository counted tokens, so it showed only after each merge, when the index was rebuilt: on 2026-11-06 the seven longest descriptions were over, and from that day to 2026-11-11 sixteen commits say in their subject that a description was brought back inside the window.
  On 2026-11-11 alone `edition-packaging` (268 tokens), `drivers` (272) and `stereo-video` (269) were over, and the first cut of `stereo-video` landed at 262, still over, before a second reached 254.
  **Fix:** `tools/check-skills.py` counts with the model's own tokens and fails on a description over the window, naming the words the index would lose; count with `--count` before the commit, never by eye.
  **How found:** the indexing script, which lists every skill over the window and exits non-zero, after each merge; the numbers above are those commits' descriptions counted with the model's tokenizer.
- **Symptom:** a round's fix breaks a rule its own skill has taught for weeks.
  `stereo-video`'s geometry reference had said since 2026-10-20 "Use valid supplied geometry directly. Do not replace it with a guessed aspect threshold"; three weeks later a first fix chose by the frame's display aspect (2.5:1, 1.2:1) on files that declare their layout, and got 2.76:1 views and square or portrait views wrong.
  **Cause:** the skill was loaded at the start, and nobody walked its rules against the diff at the end; a test checks only the cases its author thought of.
  **Fix:** step 1 of the review above, before any rerun: each rule, what it forbids, searched in the diff.
  **How found:** fixtures with a square drawn at display size showed the wrong shapes, and Daniel named the rule (2026-11-12): "if a video declare 'i am stereo', why would you try to detect if it is stereo?"; the corrected lesson is in [stereo-video's lessons](../stereo-video/references/lessons-2026-11.md).
  It happened in a second skill on 2026-11-12: `contrib-ffmpeg` had said since October that a test prints what it observes and never decides, and a test helper that compared its own result with constants and called `exit(1)` reached a review, because the project's test suite passes on such a helper.
  That skill now holds the walk as a page, 26 rules, each with the search that finds a breach; run over the whole series, it found six more places beside the reported one ([the audit](../contrib-ffmpeg/references/pre-push-audit.md), [its lesson](../contrib-ffmpeg/references/lessons-2026-11.md#a-fifth-bot-round-a-rule-the-skill-already-had-order-530-2026-11-12)).
- **Symptom:** a lessons file states how a fix behaves, and the next merge the same evening says the hardware measured otherwise.
  For the soft-reset loop of an old Radeon, the lesson merged in the afternoon of 2026-11-11 came from reading the kernel's code and from a user-space model of it, which predicted about seventeen timeouts for one of two candidate fixes; with a 60 s job on the laptop it was three, 10.8 s after submission.
  **Cause:** the lesson was written and merged with the round, before the test kernels had run on the device; an 8 s job had not told the two fixes apart.
  **Fix:** say how each thing is known, write a prediction as a prediction with the run that will test it, and when the device refutes it correct the lesson in place and say where the correction came from; "a model's number is a prediction to test, never a result" ([drivers' lessons](../drivers/references/lessons-2026-11.md)).
  **How found:** building both test kernels and running the same kit on the same laptop.
- **Symptom:** after a section moves to another skill, links across the repository land on a page that no longer has the heading; `check-skills.py` still passes.
  **Cause:** the check proves that a linked file exists, not that its anchor does, and thirty pages linked the one heading that moved (`ai-partners/SKILL.md#skills-as-you-go`).
  **Fix:** before moving a heading, count who links to it; keep the heading in place with one line that points to the new home.
  Then run `python3 tools/check-skills.py --anchors`: since 2026-11-12 it fails on a fragment that no heading of the page answers.
  **How found:** `grep -rno 'ai-partners/SKILL.md#[a-z0-9-]*' . | sort | uniq -c`, run before this skill was cut out of ai-partners.
- **Symptom:** `check-skills.py` fails on a skill nobody touched: "metadata must map text keys to text values".
  **Cause:** a line `metadata:` with nothing under it, left on 2026-10-24 when its `requires-packages` line was removed; YAML reads it as an empty value, and no tool complained for nineteen days.
  **Fix:** remove the line with its last entry.
  **How found:** the first run of the check that reads `metadata` as the format defines it.
- **Symptom:** `sparky-stereo-skills find` prints nothing for a symptom the skill's lessons file holds word for word.
  **Cause:** the offline finder ranks the name, the description and the task table, not the bodies, and its stemmer is English only.
  **Fix:** put the symptom's own words into the description or the task row, and search the bodies' index for error strings (without an index: `grep -rn "<the error string>" skills/`).
  **How found:** the 28 of 157 symptoms the descriptions missed, 26 of which a body held ([ai-partners' lessons](../ai-partners/references/lessons-2026-11.md)).
  A separate list of 24 symptoms written before reading the `making-skills` and `development-hooks` descriptions missed this skill for saving a learned fix, long troubleshooting notes and an unmeasured workaround on 2026-11-12.
  Adding those triggers brought the expected skill into the first three for all 24, from 21 before, within 232 tokens for this description and its name.
  Keep the original queries and both runs; a list used to improve a description becomes a regression check, and another reader supplies the next independent test.
- **Symptom:** the check fails on a link from a skill to a page that exists only on another branch.
  **Fix:** link the page by its full address on the main branch until both branches are merged ([selling to a newcomer, traps](../writing-front-pages/references/selling-to-a-newcomer.md#traps-met-while-shrinking)).

## Perks

- `check-skills.py --count` with no name is the whole folder at a glance, largest first: the skills near the window are the ones whose next lesson needs a trigger taken out.
- The token counter needs no model and no network, so the same check runs on a laptop, in the package build and in a container with nothing but Python.
- A trap written with "how it was found" is a debugging recipe the next person gets for free.
