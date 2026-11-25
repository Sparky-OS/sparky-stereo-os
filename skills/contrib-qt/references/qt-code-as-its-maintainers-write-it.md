# Qt code as its maintainers write it (ORDER 879, 2026-11-25)

**For** anyone preparing or reviewing a change for a Qt module: the rules a Qt reviewer applies, each with its source, and a check that searches a diff for each one before it is uploaded.

Written on 2026-11-25 from Tim Blechmann's public review of [change 792002](https://codereview.qt-project.org/c/qt/qtmultimedia/+/792002) ("PipeWire camera: follow the session's default video source"), from Qt's own documents read that day, and from qtmultimedia `dev` 766f608 with its full history.
Tim Blechmann wrote Qt Multimedia's PipeWire backend: 173 of the 191 commits on `src/multimedia/pipewire` are his.
His fifteen comments on patch set 1 are the source of what this page teaches, and every rule below names the document, the commit or the count that stands behind it.
Check freshness first: the counts are of one day, the wiki pages carry their revision dates, and the project's own pages win over this one.

The documents, with the revision each was read at:

| Document | Address | Revision read |
| --- | --- | --- |
| Commit Policy | `https://wiki.qt.io/Commit_Policy` | 2026-07-30 |
| Qt Coding Style | `https://wiki.qt.io/Qt_Coding_Style` | 2026-07-30 |
| Coding Conventions | `https://wiki.qt.io/Coding_Conventions` | 2026-01-20 |
| Review Policy | `https://wiki.qt.io/Review_Policy` | 2025-02-04 |
| Things To Look Out For In Reviews | `https://wiki.qt.io/Things_To_Look_Out_For_In_Reviews` | 2026-11-11 |
| API Design Principles | `https://wiki.qt.io/API_Design_Principles` | 2025-07-02 |
| The commit template | `https://code.qt.io/cgit/qt/qt5.git/plain/.commit-template` | read 2026-11-25 |
| The format file | `https://code.qt.io/cgit/qt/qt5.git/plain/_clang-format` | read 2026-11-25 |

"Things To Look Out For In Reviews" is the reviewers' own list: it calls itself "a low-entry-bar staging area for potential project-wide guidelines", and reviewers link its items from Gerrit.
Read it whole before a first change to a module; it is the nearest thing to this page that Qt itself keeps.
A raw copy of any wiki page comes with `curl 'https://wiki.qt.io/index.php?title=Commit_Policy&action=raw'`, and its revision date with `https://wiki.qt.io/api.php?action=query&prop=revisions&titles=Commit_Policy&rvprop=timestamp&format=json`.

## Recipe: before the first line

1. **Find who writes the folder, and read their newest work first.**
   `git log --format='%an' -- DIR | sort | uniq -c | sort -rn` names the people; `git log -20 --format='%h %ad %s' --date=short --author='NAME' -- DIR` lists the last twenty commits of the one who will review.
   Read those twenty diffs, newest first.
   A clone made with `--depth` hides them: `git fetch --unshallow` first (qtmultimedia's full history is about 60 MB).
2. **Mirror the structure of the nearest twin, and write it in the forms of the newest files.**
   A folder holds code of several years by one person, and the newest additions show which forms coexist.
   The file you copy from may be the oldest one: date it with `git log --reverse --format='%ad %s' --date=short -- FILE | head -1`.
3. **Count before you choose a form.**
   For each choice between two forms (a `const char *` or a view, `std::find` or the module's ranges helper, a sentinel or `std::optional`), `git grep -c` both in the folder and read the exceptions in their functions.
   The counts of 2026-11-25 are in the table below.
4. **Read every helper you replace.**
   When the change stops calling a function of the module and does the work itself, open that function and list each case it handled.
5. **Measure every claim about another program before it is written into the code or the message.**
   A sentence such as "one more roundtrip is needed" is an experiment, not a comment.
6. **Write the commit message last, for a reader who will never open the diff** ([the message](#the-commit-message)).
7. **Run the [pre-upload check](#the-pre-upload-check)** on the diff, then the module's tests red and green ([preparing a change on dev](preparing-a-change-on-dev.md)).

### Read the folder and build its idioms table

Run this in the module clone. Set `dir` to the affected directory, for example `src/corelib/io` in qtbase, `src/qml` in qtdeclarative or `src/client` in qtwayland. Record the SHA, folder, author, matching line count and counterexample. Open the newest files in full, including their tests. Read the *whole changes* by the reviewer to see why their code takes that form.

```sh
base=$(git rev-parse HEAD)
dir=src/multimedia/pipewire
git shortlog -sn "$base" -- "$dir"
reviewer='Tim Blechmann'
git log --diff-filter=A -5 --format='%h %as %s' --name-only "$base" -- "$dir"
git log -20 --author="$reviewer" --format=%H "$base" -- "$dir" |
    while read -r change; do git show --format=medium "$change"; done
pattern='std::optional<'
git grep -nIE "$pattern" "$base" -- "$dir"
git grep -nIE "$pattern" "$base" -- "$dir" | wc -l
```

At 766f60872 these are **matching source lines** in the PipeWire folder. Re-run both sides using the same scope. A count of zero calls for reading the available helper and the toolchain requirements.

| First pattern | Lines | Comparison pattern | Lines |
| --- | ---: | --- | ---: |
| `std::optional<` | 135 | `return -1;` | 0 |
| `std::string_view` | 57 | `optional<std::string_view>` (subset) | 30 |
| `ranges::(find\|find_if\|equal\|sort\|all_of\|any_of\|none_of\|copy\|transform\|for_each)\(` | 10 | Same expression starting with `std::` | 2 |
| `Q_EMIT ` | 9 | `^[[:space:]]*emit ` | 5 |
| `qCDebug\(` | 37 | `qCWarning\(` / `qCInfo\(` | 19 / 1 |

The new camera portal client (884ce91ab), the camera implementation (5a93ce909) and the video stream (71e3a2f08) illustrate the difference between folder and module scope. Public API compatibility, a C callback signature or a nullable input can determine the choice even when a different spelling has a larger count.

### Which rules apply across Qt

The six wiki documents in the source table were checked at revisions 46202, 46200, 45266, 43870, 46897 and 44544 respectively. A permanent link is `https://wiki.qt.io/index.php?oldid=REVISION`. Use the live page when preparing the next change.

| Source | Decision it supports |
| --- | --- |
| Coding Conventions and Qt Coding Style | Check the supported language level, source and binary compatibility, includes and lambda indentation. Check the file and the module's formatter configuration before changing layout. |
| API Design Principles | Write the caller's example first. Compare neighbouring APIs for a minimal interface, predictable names and clear semantics. For a property, check its initial value, its notification and the behaviour of a value already obtained. |
| Things To Look Out For In Reviews | Read the whole list, then walk the applicable API, documentation, tests, ownership, container, logging and commit sections. Its introduction describes it as a staging area for guidance. Individual items can have explicit exceptions. |
| Commit Policy and Review Policy | Give a self-contained reason for each logical change. Separate preparatory refactors. Leave the prescribed review time after each patch set and let reviewers inspect material changes again. |
| [QUIP 12](https://code.qt.io/cgit/meta/quips.git/tree/quip-0012-Code-of-Conduct.rst?id=f396c4d), revised 2026-03-08 | Conduct in review. Answer the technical point and preserve a colleague's contribution. |
| [QUIP 16](https://code.qt.io/cgit/meta/quips.git/tree/quip-0016-branch-policy.rst?id=c6359c1), revised 2026-10-18 | Select the branch and check backport eligibility. Refactoring belongs on dev. |
| [QUIP 17](https://code.qt.io/cgit/meta/quips.git/tree/quip-0017-Change-log-creation.rst?id=f396c4d), revised 2026-03-08 | Give significant user-visible changes a change-log entry. Here it belongs on the camera change. The internal parser move has its own message. |

Select other QUIPs by what the diff touches. The filenames below link through the [QUIP tree at c6359c1](https://code.qt.io/cgit/meta/quips.git/tree/?id=c6359c1).

| Change surface | QUIP (last revision of the document) |
| --- | --- |
| New third-party code or attribution | 4 (2026-06-07), 7 (2026-10-18) |
| Public API, source compatibility or a new nodiscard annotation | 10 (2026-03-08), 6 and 19 (2026-10-18) |
| New source files, security-sensitive headers or a blacklisted test | 18 and 23 (2026-03-08), 24 (2026-10-18) |
| Examples or documentation | 13 (2026-06-23), 21 (2026-10-18), 25 (2026-03-08) |

The ranges wrapper, log-category levels, include groups and camera test names below describe Qt Multimedia. Tim Blechmann requested a more explicit member name, a `void` internal handler and immediate fallback logging in change 792002. Those review decisions carry over when the new code has the same constraints.

## The rules

Each rule gives its source: Qt's document, the module's practice with the file or commit that shows it, or "this reviewer's preference" where nothing else stands behind it.
"The backend" is `src/multimedia/pipewire` on `dev` 766f608.

### The commit message

- **It says what was wrong and what the change does for the design, not how the code does it.**
  Commit Policy, item 9.2: "Tell why you changed something unless it is completely self-evident"; "Make the commit self-contained, so people do not have to research the historical context to make sense of it. Conversely, do not add unnecessary trivia."
  Things To Look Out For In Reviews, Commit Message 1.1: "Does the commit message answer the questions "Why was the old code wrong/worse?" and "Why is the new code correct/better?"?"
  The review of 792002: "keep it high-level and focus on the architectural change rather implementation details".
  The module's own messages are two short paragraphs: the old behaviour and why it was wrong, then the new behaviour (commits cada2e61e and 486c4af43 are the model).
- **A change outside the subject is spelled out in the message.**
  Commit Message 2.1: "Ask for drive-by changes to be spelled out explicitly in the commit message."
  A fault that was already there is a commit of its own before the change: Gerrit 4.2, "(pre-existing) ... If it's cut-n-paste, suggests that a prequel commit fixing the issue and then rebasing the current patch on top is in order."
- **One self-contained change per commit.**
  Commit Policy 9.1: "do not mix unrelated changes"; "Fix the coding style only in exactly the lines which contain the functional changes".
  Gerrit 7: "Prefer smaller commits to larger ones."
- **The form:** imperative mood (Commit Message 5), capitals where they belong (6), the body wrapped at 72 columns (the commit template), `Change-Id` last with `Task-number`, `Fixes` and `Pick-to` before it (7).

### Types and signatures

- **In this callback, borrow present C strings with a view and preserve null as an absent optional.**
  The backend has 57 uses of `std::string_view`, 30 of them `std::optional<std::string_view>` (every getter of `qpipewire_propertydict_p.h`, added by commit 1a5552789), and one struct with `const char *` members, the oldest one, which the review asked not to copy: "all those members should be string_view".
  A view cannot be made from a null pointer, so check what the C API sends before choosing between the two ([the trap](#traps-symptom-cause-fix-how-found)).
- **For this index the reviewer asked for an optional or an asserted precondition.**
  The backend has 135 uses of `std::optional` and no `return -1`.
  The review: "either return a `std::optional` or assert".
  `Q_ASSERT` states a precondition 42 times in the backend.
- **A handler that reports nothing returns `void`;** `int` stays at the C callback that the library defines.
  The backend has nine `void` handlers and one member function returning `int`, again the one that was copied: "returning 0 in all codepaths? consider returning void".
- **Check whether a parameter needs a variant.**
  A parameter that is a value or nothing is `std::optional`: "the variant only seems to be used in this function signature and doesn't seem to be stored".
- **`std::optional` in the pointer-like form.**
  Things To Look Out For In Reviews, std::optional 1 and 2: "Don't use value(), has_value(), use pointer-compatible subset: if (opt), *opt, opt->foo"; "Avoid the default constructor, explicitly use std::nullopt."
- **Prefer the module’s uppercase signal macros in new code.** The same maintainer also added lowercase emissions to the camera backend. Check whether the target disables the keywords.
  Commit 7a907ff8c (2026-09-30): "qt's pseudokeywords can clash with application code, e.g. libcamera."
  `src/multimedia` has 229 `Q_EMIT` against 5 `emit` in code; test classes keep `private slots:` (112 against 6).

### Algorithms

- **The module's ranges helpers, not `std::find(begin, end, ...)`.**
  `QtMultimediaPrivate::ranges` in `qmultimedia_ranges_p.h` gives `find`, `find_if`, `equal`, `sort`, `any_of` and the rest in the C++20 form on every compiler; commit b2fc0ff28 (2026-05-11, "stl: use ranges wrapper") moved the module to it.
  The backend has 12 uses against 2 of the `std::` form, `src/multimedia` 43 against 25.
- **"(repeats)" in a comment means the author finds every other instance.**
  Gerrit 4.1: "there are more instances of this elsewhere (maybe earlier in the patch). It's the commit author's responsibility to find them all, and fix them."
  A hand-written loop that searches a container is an instance too.

### Logging

- **A message is logged where the condition is seen; no object keeps "already said".**
  The review: "typically warnings are shown immediately and we avoid keeping them in the state".
  No member in `src/multimedia` stores a reported message.
  Where once per process is needed, the module uses a function-local `std::once_flag` (`video/qeglimagefunctions.cpp`).
  Measured without the stored message: the line appears once in a freshly started program and once more at each later rebuild of the camera list.
- **Debug and warning predominate in this module.**
  `src/multimedia` has 253 `qCDebug`, 177 `qCWarning` and one `qCInfo`.
  A new `qCInfo` will be read as a choice: be ready to say why the line must show by default.
- **No `Q_UNLIKELY` or `Q_UNLIKELY_BRANCH` on the way to a warning.**
  Things To Look Out For In Reviews, QDebug 3: "Don't use Q_UNLIKELY on conditions leading to qWarning()/qFatal() ... qWarning() etc are marked as Q_DECL_COLD_FUNCTIONS".

### Names and comments

- **A member is named for what its value is in the domain.**
  The review renamed `m_defaultSourceName` to `m_defaultVideoSourceObjectName`: the key it holds is `default.video.source`, and its value is the name member of an object.
  This reviewer's preference; the audio twin still has the short names.
- **A comment says what the code cannot: a reason, an order that matters, a rule of another program.**
  The review: "the comment does not tell us more than the code".
  The comments in the reviewer's newest files are of that kind ("The listener has to go before the formats are handed out, so that no further param event can append to them").

### Layout

- **A lambda's body is indented under its first line.**
  Coding Conventions, Lambdas: "Place the capture-list, parameter list, return type, and opening brace on the first line, the body indented on the following lines, and the closing brace on a new line."
- **`clang-format` on the touched lines only, and only where the neighbouring file is clean under it.**
  Qt Coding Style: "clang-format cannot be configured to correctly reproduce the Qt style, so unless a module was developed with clang-format from the get-go, it's best to disable git-clang-format."
  This qtmultimedia revision has no format file of its own; the file is in qt5.git.
  With clang-format 21.1.8 and that file, 24 of the backend's 54 files would change (552 lines), while the two newest camera files change by 0 lines: in those the tool's output is the maintainer's form.
- **Includes:** the module's private headers as `<QtMultimedia/private/x_p.h>` in alphabetical order, then QtCore, then the library's own headers (`pipewire/`, `spa/`), then the standard library, each group after an empty line.
  Things To Look Out For In Reviews, Includes 2 and 3, asks for groups, alphabetical order and "Include everything the file needs"; where its order of groups differs from the folder's, the folder wins (all nine backend sources with both kinds put the library's headers first).
- **Helpers of one file go into an anonymous namespace,** without `static` (15 such namespaces in the backend against one `static` function), although Coding Conventions asks for `static` too.
- **A part of the code stays free of the part beside it.**
  No camera file of the backend includes an audio header, and commit 1fcea7263 removed the shared helpers' dependency on the audio context.
  A helper both sides need belongs in the shared support files, moved there by a commit of its own.

### Tests

- **Rows are named `function_expectation_condition`,** as the file already names them (47 of the camera unit tests' 50 functions).
- **`QCOMPARE(actual, expected)`,** in that order (Things To Look Out For In Reviews, Tests 3).
- **A new or changed test function must pass many times in a row.**
  The commit template: "CI then does not require the function to pass repeatedly, as it does for new or modified tests."
  Run it twenty times before upload.

### Answering on Gerrit

- **"Done." where the point is taken, the fact where a question was asked, the reason where the code stays.**
  One or two lines, and nothing about how the first form came about.
- **The new patch set goes up before the answers.**
  Gerrit 3: "Push "Done" comments only after you push the new version."
- **A reviewer's question about behaviour is answered with a measurement,** and a point that does not hold is answered the same way.
- **Fetch the latest patch set before amending.**
  Gerrit 6.1: "As the patch author, be mindful when pushing over already-approved changes ... An approver may have made edits to your change".
- **Give each patch set its time.**
  Review Policy 1.2: "a full working day waiting time is the absolute minimum; three days are reasonable", and "This applies to every new Patch Set in turn."

## The pre-upload check

Use the parent of the proposed commit as the base, including when an earlier commit in the series moved a helper. Run the [line search](../scripts/review-diff.py) from the module's Git tree. It prints the rule, path, line and excerpt. Supply the production directory whose conventions you measured. The PipeWire-specific checks select matching API and member names.

```sh
tip=$(git rev-parse HEAD)
base=$(git rev-parse "$tip^")
python3 "$contrib_qt/scripts/review-diff.py" "$base" "$tip" --module-dir "$dir"
git diff --check "$base" "$tip"
git diff --stat "$base" "$tip"
git log -1 --format=%B "$tip"
```

Walk each candidate against the surrounding function and the cases below. The program finds places to read. A reviewer decides whether any of them need a change. Walk rows 3, 18, 20, 21 and 23 separately.

| # | Evidence to inspect | Decision |
| --- | --- | --- |
| 1–3 | Message identifiers, prose line lengths, Change-Id and whole diffstat | Describe the old and new behaviour. Public API names or an ownership invariant can explain the reason. Read the whole footer block. Distinguish review trailers added after integration. Check every changed file for a prerequisite. |
| 4 | Raw string-pointer fields in changed headers | Consult the producer's nullability and lifetime contract. Make an owning copy before queued delivery. |
| 5–7 | Empty-container sentinels, index casts at the caller, integer member handlers returning only zero, a variant in a function signature | Prove the precondition at every caller. Preserve mandated ABI return types at C callbacks. Ask which variant alternatives actually need to be stored. |
| 8–10 | Presence-only conditions, standard iterator pairs in a module with a range wrapper, range loops next to return or continue | Check optional construction and unwrapping by hand. Confirm the wrapper exists and preserves the range. Some loops build results, manage resources or return different representations. |
| 11–13 | Reported-message fields, info-level logging, cold branches before logging | Trace where the message is emitted and repeated, and run with the default category settings. Absence of an optional session choice can be routine and still warrant an explanation. |
| 14–17 | Signal keywords where disabled, a comparison comment beside the comparison, source/sink member names, a camera include from the audio implementation | Check build flags as well as local spelling, read every comment for a reason, compare names to the domain, and trace each include to the symbol it supplies. The name and include searches here are specific to this backend. |
| 18 | For each changed C++ file get new-line ranges from `git diff -U0 "$base" "$tip" -- "$file"`. Run the same clang-format version with the module's style on its parent copy, and with one `--lines=FIRST:LAST` for each added range on its new copy. | Compare actual statements on adjacent nesting levels. On an existing clean parent an indentation shift can pinpoint a misplaced callback body. A new file has no clean-parent control. Read its layout against neighbouring files and the written conventions. A wrap or a dirty baseline alone is insufficient. |
| 19 | Removed cache, notification, lock and listener calls | Open the removed helper in the base, including its first-use and failure paths. Compare the replacements with a client already subscribed and a client that has never queried the value. |
| 20 | `git diff "$base" "$tip" -- tests`; inspect new slots and each `QCOMPARE` | Compare names with neighbouring test functions. Exclude Qt Test's lifecycle slots. Check actual then expected, and what a mutation makes fail. |
| 21 | Run each changed test function repeatedly on the final commit | Record the total and the named failures on a known bad implementation. Twenty consecutive runs was the local control for this change. |
| 22 | Adjacent identical synchronizations across the hunk boundary, and each claim about a server or session in comments and the message | Compare one call with two. Record the first observable value in fresh and running clients. Source-trace older versions separately. |
| 23 | Confirm the latest patch set on Gerrit immediately before upload | An anonymous refusal leaves this check open for the uploader. |
| 24 | A metadata object selected by a property lookup | Enumerate distinct names, duplicate names and ids. Remove the bound and unbound objects in opposite orders. Compare the surviving provider's value with the public API. |

On change 792002 this walk found all thirteen code comments in Tim Blechmann's review. The original walk identified eleven directly from code or the message. It had no specific question for provider identity or for the unsigned use of the index. The revised check includes both. Twenty integrated changes by the same author touching the directory supplied a second control. Identifiers in messages, loop exits, equivalent lock replacements and formatter wrapping all occurred in accepted code. Read these in context before requesting changes.

## The counts of 2026-11-25

qtmultimedia `dev` 766f608; "backend" is `src/multimedia/pipewire`, "module" is `src/multimedia`.

| Form | Count | Against | Count |
| --- | --- | --- | --- |
| `std::optional<` in the backend | 135 | `return -1;` | 0 |
| `std::string_view` in the backend | 57 | structs with `const char *` members | 1 |
| `ranges::` algorithms in the backend | 12 | `std::` algorithms with `begin` and `end` | 2 |
| `ranges::` algorithms in the module | 43 | `std::` algorithms with `begin` and `end` | 25 |
| `void` handlers in the backend | 9 | member functions returning `int` | 1 |
| `Q_EMIT` in the module | 229 | `emit` in code | 5 |
| `qCDebug` in the module | 253 | `qCInfo` | 1 |
| `qCWarning` in the module | 177 | members that keep a reported message | 0 |
| anonymous namespaces in the backend | 15 | `static` free functions | 1 |
| backend files clean under clang-format 21.1.8 | 30 | files it would change | 24 |

## Traps (symptom, cause, fix, how found)

- **Symptom: six of fifteen review comments land on lines copied from the file next door.**
  How the forms arose is an inference from history. The camera change mirrored the backend’s older audio context manager (2025); the same author's camera files are of August to November 2026 and use views, `std::optional`, `void` handlers and the ranges helpers.
  Fix: mirror the structure of the twin, and write each line in the form of the newest files (recipe steps 1 to 3).
  How found: the review itself, then `git log --reverse` on both files and the counts above.
- **Symptom: "why do we need to sync twice here?"**
  Cause: a second registry roundtrip had been added on the belief that the first list would otherwise miss the session's default, and nobody had run it with one.
  Fix: one sync.
  With one, 30 of 30 fresh starts had the session's default in the first list, as with two.
  The "default" metadata is bound when the registry announces it, and each camera's format enumeration makes its own roundtrip afterwards; PipeWire holds a client that binds a metadata object busy until the object's owner has answered (`pw_impl_client_set_busy()` in `global_bind()`, `src/modules/module-metadata/metadata.c`), so the next answer the client gets comes after the metadata's values.
  How found: two builds, one and two syncs, each printing whether the default was known before and after the enumeration loop: with one sync it was unknown before in 10 of 10 starts and known after in 10 of 10.
- **Symptom: a program that listens to `QMediaDevices::videoInputsChanged` without reading the list first gets no signal for the first camera plugged in.**
  Cause: the change had replaced `QPlatformVideoDevices::updateVideoInputsCache()` with its own comparison, and that function's `QCachedValue::update()` treats an empty cache as a change; the replacement filled the cache and found nothing changed.
  Fix: keep the case (signal when nothing was cached).
  How found: reading `QCachedValue::update()` during the walk of check 19, then a program that only listens, started in a session without a camera before one was plugged in: the unmodified build signalled, patch set 1 stayed silent, patch set 2 signalled.
- **Symptom: `std::string_view` members crash, or cannot be written, for a metadata event.**
  Cause: `pw_metadata_events::property` carries null pointers: a null type for a key set without one, a null type and value for a removed key, and a null key, type and value when a subject is cleared.
  Fix: `std::optional<std::string_view>` members, filled by one helper that maps null to `std::nullopt`; a function that parses the value takes the view, not `data()`.
  How found: a twenty-line listener that prints each event with its nulls, run in a private session while `pw-metadata` set, removed and cleared keys.
- **Symptom: a reviewer asks whether a session has one Metadata object, and the code selects it by name.**
  Fact: a session with WirePlumber 0.5.19 lists nine (`settings`, `sm-settings`, `default`, `filters`, `route-settings` and four more); a second object named `default` can exist, since any client can create one through the `metadata` factory; ids differ from session to session.
  PipeWire's own clients select by `metadata.name` (`pw-metadata`, `module-combine-stream.c`, the GStreamer device provider), and an object made without a name is named `default` (`module-metadata.c`).
  Select by name and track removal by global id. Exercise both removal orders when two objects share the name.
  The local patch set 2 candidate for change 792002 warned and discarded the second announcement. When the first object disappeared, a running application fell back to the first camera even though the surviving object named another.
  To check the handover, start the application on the first provider, announce the replacement, and remove the first provider. Read the surviving value with `pw-dump`, then compare `QMediaDevices::defaultVideoInput()` and a newly constructed `QCamera` in both the running application and a fresh one. Keep the original open camera separate in the measurements.
  In a three-camera session the first provider selected cam-b and WirePlumber's surviving object selected cam-c. A hotplug triggered another list update. Both queries returned cam-a in the running application and cam-c in the fresh one.
  Fix: retain compatible global ids in announcement order. Keep the incumbent listener until its own id disappears, detach, clear its value, then bind the survivor. Removing only a waiting provider preserves the incumbent. Removing the last one clears the selection. Re-run all three orders through the public API. Copying the audio listener also copied its assumption about a single provider.
- **Symptom: the three last lines of a Gerrit suggestion are indented four columns less than the rest, and its empty line holds spaces.**
  Cause: the suggestion was typed in the web editor.
  Fix: apply what it means (here: the lambda's body one level deeper), and check the result with clang-format, which gave the same form. How found: diff the proposed callback against the base and the formatter result.
- **Symptom: clang-format wants to change lines the change did not write.**
  Cause: the folder was formatted over the years by different versions of the tool.
  Fix: run it on the same file as it is on the base first; if that file is clean, the tool is the form for it; leave a line of the base alone when the change only renames something on it. How found: format both revisions with the same version and configuration.
- **Symptom: `git ls-remote https://codereview.qt-project.org/qt/qtmultimedia 'refs/changes/02/792002/*'` answers "could not read Username".**
  Cause: Qt's Gerrit serves patch sets only to an account.
  Fix: whoever holds the account fetches the newest patch set before the amended one is uploaded (check 23); a contributor without it says in the hand-back that this was not done. How found: compare the anonymous Gerrit response with the local change refs.
- **Symptom: a comment on `/COMMIT_MSG` names line 29, and the message has 28 lines.**
  Cause: Gerrit's view of the message starts with six lines of header (parent, author, dates), so line 29 is line 23 of the message. Fix and check: inspect the Gerrit header and count from the subject before editing the cited paragraph.

## Perks

- A session's Metadata objects, their names and ids: `pw-cli ls Metadata`.
- An instrumented build answers "is it needed" in minutes: copy the tree, add one `fprintf` at each side of the step, rebuild the one file, and start the program ten times.
- The reviewers' list has stable anchors: a comment such as "Includes Item 2.1.1" points into `https://wiki.qt.io/Things_To_Look_Out_For_In_Reviews#Includes`.
