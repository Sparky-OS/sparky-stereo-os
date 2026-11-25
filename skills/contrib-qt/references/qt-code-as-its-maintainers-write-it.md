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
   A folder holds code of several years by one person, and the reviewer judges new code by how he writes today.
   The file you copy from may be the oldest one: date it with `git log --reverse --format='%ad %s' --date=short -- FILE | head -1`.
3. **Count before you choose a form.**
   For each choice between two forms (a `const char *` or a view, `std::find` or the module's ranges helper, a sentinel or `std::optional`), `git grep -c` both in the folder and take the one the folder uses.
   The counts of 2026-11-25 are in the table below.
4. **Read every helper you replace.**
   When the change stops calling a function of the module and does the work itself, open that function and list each case it handled.
5. **Measure every claim about another program before it is written into the code or the message.**
   A sentence such as "one more roundtrip is needed" is an experiment, not a comment.
6. **Write the commit message last, for a reader who will never open the diff** ([the message](#the-commit-message)).
7. **Run the [pre-upload check](#the-pre-upload-check)** on the diff, then the module's tests red and green ([preparing a change on dev](preparing-a-change-on-dev.md)).

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

- **A string from a C API is a `std::string_view`; one that can be absent is a `std::optional<std::string_view>`.**
  The backend has 57 uses of `std::string_view`, 30 of them `std::optional<std::string_view>` (every getter of `qpipewire_propertydict_p.h`, added by commit 1a5552789), and one struct with `const char *` members, the oldest one, which the review asked not to copy: "all those members should be string_view".
  A view cannot be made from a null pointer, so check what the C API sends before choosing between the two ([the trap](#traps-symptom-cause-fix-how-found)).
- **No sentinel values: `std::optional`, or a precondition that is asserted.**
  The backend has 135 uses of `std::optional` and no `return -1`.
  The review: "either return a `std::optional` or assert".
  `Q_ASSERT` states a precondition 42 times in the backend.
- **A handler that reports nothing returns `void`;** `int` stays at the C callback that the library defines.
  The backend has nine `void` handlers and one member function returning `int`, again the one that was copied: "returning 0 in all codepaths? consider returning void".
- **`std::variant` only where both alternatives are stored.**
  A parameter that is a value or nothing is `std::optional`: "the variant only seems to be used in this function signature and doesn't seem to be stored".
- **`std::optional` in the pointer-like form.**
  Things To Look Out For In Reviews, std::optional 1 and 2: "Don't use value(), has_value(), use pointer-compatible subset: if (opt), *opt, opt->foo"; "Avoid the default constructor, explicitly use std::nullopt."
- **`Q_EMIT`, `Q_SIGNALS` and `Q_SLOTS`, never the lower-case keywords,** in sources and private headers.
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
- **The levels the module uses are debug and warning.**
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
  A module tree has no format file of its own; the file is in qt5.git.
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

Walk these against the diff before the tests are run again, and write the result of each in the hand-back.
`BASE` is the commit the change sits on, and `D` is `git diff BASE -- src tests`.

| # | Rule | Search | A hit means |
| --- | --- | --- | --- |
| 1 | The message is about the design | `git log -1 --format=%b \| grep -n -E '[a-z]\(\)\|m_[a-z]\|operator'` | Each identifier named in the body: is it public API the reader knows, or the implementation retold |
| 2 | The message's form | `git log -1 --format=%B \| awk 'length > 72'`; `git log -1 --format=%B \| tail -1` | A long line; a last line that is not `Change-Id:` |
| 3 | Drive-by changes are named | `git diff --stat BASE` | A file outside the subject that the message does not mention |
| 4 | No C strings kept | `D \| grep -n -E '^\+\s+const char \*\w+;'` | A member to turn into a view |
| 5 | No sentinel | `D \| grep -n -E '^\+.*(return -1;\|== -1\|!= -1\|npos)'` | A result to turn into `std::optional` or an asserted precondition |
| 6 | No handler that returns a constant | `D \| grep -n -E '^\+\s+return 0;'` | A function, other than a C callback, whose every path returns the same status |
| 7 | No variant as a parameter | `D \| grep -n -E '^\+.*std::variant'` | A variant that nothing stores |
| 8 | `std::optional` in the pointer-like form | `D \| grep -n -E '^\+.*\.(has_value\|value)\(\)\|^\+\s+std::optional<[^>]+> \w+;'` | `value()`, `has_value()`, or a local optional made without `std::nullopt` (a member declaration is not a hit) |
| 9 | The module's ranges | `D \| grep -n -E '^\+.*std::(find\|find_if\|equal\|sort\|all_of\|any_of\|none_of\|copy\|transform\|for_each)\('` | An algorithm to write as `ranges::` |
| 10 | No hand-written search | `D \| grep -n -A3 -E '^\+\s+for \(.*:'` | A loop whose body is `if (...) return` or `continue` |
| 11 | No stored "already said" | `D \| grep -n -i -E '^\+.*(reported\|warned\|alreadyLogged\|mutable )'` | State kept for a log line |
| 12 | Log levels | `D \| grep -n -E '^\+.*q(C)?Info'` | A level the module barely uses |
| 13 | No likely or unlikely before a warning | `D \| grep -n -B2 -E '^\+.*q(C)?(Warning\|Critical\|Fatal)' \| grep UNLIKELY` | The macro to remove |
| 14 | Upper-case signal macros | `D \| grep -n -E '^\+\s+emit \|^\+\s*(signals\|public slots\|private slots):'` | A lower-case keyword outside a test class |
| 15 | Every comment earns its place | `D \| grep -n -E '^\+\s*//'` | Read each: does it say why, or repeat the line under it |
| 16 | Names | `D \| grep -E '^\+' \| grep -o -E '\bm_[A-Za-z]+' \| sort -u`, then the same on `BASE`'s files to see which are new | A new member whose name is shorter than what it holds |
| 17 | Includes | `D \| grep -n -E '^\+#include'` | A header of a neighbouring part; a group out of the file's order |
| 18 | Layout | clang-format with qt5.git's file on the changed lines only (`--lines=A:B` per hunk of `git diff -U0 BASE`) | A difference in a file that was clean on BASE |
| 19 | Nothing lost | `D \| grep -n -E '^-.*\w+\(.*\);'` | A call that was replaced: open the function and list its cases |
| 20 | Test names and order | `git diff BASE -- tests \| grep -n -E '^\+\s+void \w+\(\);'`; `git diff BASE -- tests \| grep -n -E '^\+\s+QCOMPARE'` | A row not named as its neighbours; an expected value in the first place |
| 21 | Stable tests | the changed test binary twenty times | A run that fails |
| 22 | Claims | `D \| grep -n -i -E '^\+\s*//.*(roundtrip\|server\|session\|daemon\|always\|never)'` and the same words in the message | A sentence about another program with no run behind it |
| 23 | The patch set you amend is the newest | fetch `refs/changes/NN/NUMBER/*` from Gerrit (it needs the account) | A patch set uploaded by a reviewer |

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
  Cause: the audio context manager, which the camera change mirrored, is the backend's oldest code (2025); the same author's camera files are of August to November 2026 and use views, `std::optional`, `void` handlers and the ranges helpers.
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
  A backend that promises to follow the session must be able to bind the surviving object after the current one disappears.
- **Symptom: the three last lines of a Gerrit suggestion are indented four columns less than the rest, and its empty line holds spaces.**
  Cause: the suggestion was typed in the web editor.
  Fix: apply what it means (here: the lambda's body one level deeper), and check the result with clang-format, which gave the same form.
- **Symptom: clang-format wants to change lines the change did not write.**
  Cause: the folder was formatted over the years by different versions of the tool.
  Fix: run it on the same file as it is on the base first; if that file is clean, the tool is the form for it; leave a line of the base alone when the change only renames something on it.
- **Symptom: `git ls-remote https://codereview.qt-project.org/qt/qtmultimedia 'refs/changes/02/792002/*'` answers "could not read Username".**
  Cause: Qt's Gerrit serves patch sets only to an account.
  Fix: whoever holds the account fetches the newest patch set before the amended one is uploaded (check 23); a contributor without it says in the hand-back that this was not done.
- **Symptom: a comment on `/COMMIT_MSG` names line 29, and the message has 28 lines.**
  Cause: Gerrit's view of the message starts with six lines of header (parent, author, dates), so line 29 is line 23 of the message.

## Perks

- A session's Metadata objects, their names and ids: `pw-cli ls Metadata`.
- An instrumented build answers "is it needed" in minutes: copy the tree, add one `fprintf` at each side of the step, rebuild the one file, and start the program ten times.
- The reviewers' list has stable anchors: a comment such as "Includes Item 2.1.1" points into `https://wiki.qt.io/Things_To_Look_Out_For_In_Reviews#Includes`.
