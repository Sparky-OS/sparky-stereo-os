# KDE development practices for edition changes

Reviewed 2026-10-19 from Daniel's complete saved transcript of
[David Redondo and Harald Sitter's Akademy 2026 talk](https://media.ccc.de/v/kde2026-33-kde_development_best_practices)
and the linked API documentation. These edition review procedures do not replace the target project's contribution rules or establish a KDE policy on AI.

## Choose the checks for the change

| Changed surface | Check | Evidence to return |
| --- | --- | --- |
| Visible text | Context/plurals, fresh extraction, installed translated UI | Extracted messages and missing/ambiguous strings |
| QML/C++ interface | Module/type registration, generated type information, project lint target | Tool versions, imports and remaining diagnostics |
| Native lifetime or errors | Compiler warnings, relevant static analysis, regression case | Old failure and fixed behavior, including cleanup |
| Privileged action | Authorization boundary and overlapping requests | Validated inputs and concurrency behavior |
| Build/release | Required pipeline, licensing, installed-package checks | Revision, completed jobs and unresolved failures |

Run checks on the affected component and the upstream-required pipeline. A documentation edit does not need a new runtime test.
Make commands usable without an AI client. Record prerequisites rather than inventing a command for a target that does not exist.

## Internationalization is part of the interface

Use a context-aware translation call for new KDE UI text, especially short or ambiguous labels.
For example, `i18nc("@action:button Swap the left and right eye images", "Swap eyes")` tells a translator both the action and its location.
Use plural-aware calls and placeholders; do not concatenate fragments that translators must reorder.
[KI18n's API](https://api.kde.org/klocalizedstring.html) and [KUIT context markers](https://techbase.kde.org/Development/Tutorials/Localization/i18n_Semantics) define the conventions.

Run the repository's `Messages.sh` through its documented extraction environment in a disposable checkout with fresh output.
Check that new messages actually appear: a copied script, stale POT file or zero exit status alone proves little.
Keep extraction inputs and translator comments available until that consumer has run.
Where supported, `x-test` helps expose strings missing from extraction; verify its catalog is installed before interpreting unmarked text.
Then inspect real translations, placeholders, expansion and right-to-left layout where applicable.
For stereo controls, test the same text in both eyes, with fractional scaling and keyboard/controller focus.

## Make QML visible to its tools

For new interfaces, prefer a declared QML module and types whose properties are visible to tooling.
Use the target version's supported registration, such as [`QML_ELEMENT` with `qt_add_qml_module`](https://doc.qt.io/qt-6/qqmlintegration-h.html#QML_ELEMENT).
Check the installed [KI18n QML API](https://api.kde.org/ki18n-index.html) before replacing translation context injection with an explicit import.
Do not copy a newer talk's import into an older packaged Frameworks release without checking availability.
Run the project's [`qmllint`](https://doc.qt.io/qt-6/qtqml-tooling-qmllint.html) target with real import paths and generated type information.
Missing imports are an environment failure to fix, not a reason to suppress every warning.

For the proposed Theme Editor/StyleKit bridge, expose depth intent as typed properties with documented units and ownership.
Keep the ordinary 2D fallback and one shared control state; tooling visibility does not itself supply stereo rendering.
Use [the depth reference](../../stereo-window-3d-area/references/qt-kde-depth.md) for eye geometry, clipping and input transforms.

## Keep failure signals useful

Run the required pipeline for the revision being integrated. Do not describe a red or unrun pipeline as validated.
Compare failures with the base revision, identify the owner and resolve the failure before ordinary integration.
A retry that happens to pass does not explain a flaky test; retain its original failure and investigate it.
If a maintainer explicitly accepts a documented exception, report the exception and its coverage limit instead of an unconditional pass.

Keep the project's KDE CMake/compiler settings and warnings enabled.
Use its supported C++ analysis tools (for example Clazy, cppcheck or clang-tidy) where relevant; do not assume all belong in every CI configuration.
Check significant return values, especially file opening and privileged operations.
Run `reuse lint` where REUSE is adopted, preserve copyright and SPDX declarations, and attribute new material accurately.
Never copy another author's name merely because it came from a template.

## Lifetime, compatibility and privilege boundaries

Make ownership explicit: unique ownership, QObject parent ownership, a guarded `QPointer`, and shared ownership have different purposes.
Do not change everything to shared ownership or ban `unique_ptr` in APIs because of a talk's shorthand; review deleter types and ABI commitments for the actual library.
With QStringBuilder enabled, materialize a `QString` before concatenation escapes its operands' lifetime; `auto` can retain an expression template. See [Qt's explanation](https://doc.qt.io/qt-6/qstring.html#more-efficient-string-construction).
Use RAII or a scope guard for cleanup across early returns. Check captures and asynchronous lifetimes too.
Use spans/ranges when the target compiler and standard library support them, with valid backing lifetimes; measure repeated evaluation or copies in streaming/rendering loops.
Prefer exhaustive switches for a controlled enum. Validate external integer values first; compiler coverage is not input validation.

For a privileged action, identify the authenticating service, caller identity, validated arguments and resource ownership.
Exercise overlapping requests and multiple client instances. The talk flags KAuth concurrency concerns; inspect the shipped version and obtain relevant code review before choosing KAuth or direct polkit integration.
Changing authorization libraries does not itself make a helper secure.
For edition network setup, keep authorization and network changes in their owning service, with per-connection scope and recovery on failure.

## Keep the reason in authored source and history

Comments should explain constraints, non-obvious decisions or a specific unresolved problem. A bare FIXME is not a useful handoff.
Commit messages should identify the problem, why the change belongs here and the observed result; the diff supplies mechanics.
Review AI-assisted messages against the actual diff and evidence. Avoid invented rationale and generic summaries; follow the recipient project's current policy.
The talk's skepticism about generated commit prose is a quality concern to address, not authorization to conceal assistance.

This applies directly to [Lean Code](../../lean-code/SKILL.md): retain complete authored source, licensing and exact recovery information.
A comment used by a generator, translator, compiler directive or documentation consumer is operational input, even if it looks like prose.
Qualify the complete build path before removing it from a disposable build tree. Keep unqualified files unchanged.
The edition's FreeRDP build retains `settings_types_private.h` because its generator reads IDs from comments.
Source recovery maps a matching projection to its preserved authored revision; it cannot reconstruct missing intent from arbitrary optimized binaries.
