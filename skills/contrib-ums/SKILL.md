---
name: contrib-ums
description: >-
  Contribute to Universal Media Server on GitHub: its three accepted checks, the Java style gate (STYLEGUIDE.md),
  device-level proof on a real renderer, the pull-request template. Load it with upstream-outreach for a UMS
  transcoding, renderer profile or 3D bug: the frame packing SEI kept through a transcode, Output3DFormat, a renderer
  configuration that outranks the generic one.
---

# Contributing to Universal Media Server

**Check freshness first.**
Written on 2026-10-24.
The project's own contribution rules, read again before each round, win over this page.

Written on 2026-10-24 from Universal Media Server's `CONTRIBUTING.md`, `STYLEGUIDE.md`, pull-request template and public pull requests [#6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330) and [#6389](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6389).
The rules that come first were added on 2026-11-02 from `Code_Of_Conduct.md`, `CONTRIBUTING.md`, `STYLEGUIDE.md` and `.github/pull_request_template.md` on `main` and from the knowledge base's [development page](https://github.com/UniversalMediaServer/knowledge-base/blob/main/docs/development/development.md), read that day.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is Universal Media Server's own practice.
Re-read those files in the current tree before every round; its default branch is `main`.

## The rules that come first
- **Universal Media Server's Code of Conduct** (`Code_Of_Conduct.md`, the Contributor Covenant 2.1) applies "within all community spaces", and when someone officially represents the community in public.
  - Its standards include empathy and kindness, respect for differing opinions, giving and gracefully accepting constructive feedback, and "Accepting responsibility and apologizing to those affected by our mistakes, and learning from the experience".
  - Community leaders enforce it through its four steps (correction, warning, temporary ban, permanent ban); reports go to them on the [UMS forum](https://www.universalmediaserver.com/forum/).
- **The route:** a pull request on GitHub that a reviewer can check three ways (below).
  An issue carries the debug information packed from the Logs tab at the Trace level, attached to the issue or to the forum's attachments thread and linked from the issue.
- **AI:** Universal Media Server's code of conduct, `CONTRIBUTING.md`, `STYLEGUIDE.md`, pull-request template and the knowledge base's development page state nothing about AI assistance (checked 2026-10-24, and on 2026-11-02 with the code of conduct and the development page).

## Merge decisions
- `CONTRIBUTING.md` says the project will merge changes only if they do not break automated tests.
- It adds a second condition: "code review by one of our developers".
- It adds a third condition: manual testing.
- It also says to "please try to use the code conventions we use".
- Plan the description so a reviewer can perform all three checks.

## The pull request
- Use the template's three-part checklist: description, every relevant issue linked, and every relevant Knowledge Base article written or modified.
- The same checklist requires relevant tests to be written or modified.
- Keep renderer profile and Knowledge Base changes in one pull request only when the profile adds the documented article the template asks for.
- `STYLEGUIDE.md` says to follow the Google Java Style Guide with block K&R style.
- When resolving conflicts, `STYLEGUIDE.md` says "We prefer pulling" into the branch.
- It explains that merge commits make conflict history easier to inspect than strategies that rewrite history.

## Device and media proof
- Run the automated build and tests on the changed code.
- Exercise the exact affected renderer profile and media path by hand.
- Record the profile, client, exact input, command or configuration, old behaviour and new behaviour.
- Do not claim a device works without testing that device or a demonstrably equivalent public profile.

## Public record
- Public pull request [#6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330) was a focused renderer and media-fix change.
- Public pull request [#6389](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6389) was a focused media declaration change.
- The reviewer asked for 3D test files on [#6389](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6389).
- Treat that request as evidence that device and file-level proof matter for stereo changes.

## Replies
- Answer each review point with the automated result, code-review note or manual check that resolves it.
- Thank the reviewer for the specific review work.

## Lessons from the lanes, October to November 2026

From the lanes of 25 October to 6 November 2026; add the next lesson here as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).

- Nothing UMS specific in the hand-back: the lane packaged ORDER 223 (hardware decode) for nine source packages (116 archives), with the check-debs marker removal control and check-link unresolved library control; the UMS and MPlayer messages were held, none sent. (lane ums-3d-bugs-178-gpt)

## Tests that must pass on Windows (ORDER 272b, November 2026)

UMS's CI runs the Java tests on Windows, macOS and Linux, and a test that denies writing with POSIX permissions fails only on Windows.

- **Trap:** `File.setWritable(false, false)` on a folder returns `false` on Windows, so `assertTrue(folder.setWritable(false, false))` fails in the setup, and Windows has no read-only folder to test against. Linux and macOS pass, which is why only the `Windows` job is red (`SubtitleCacheOwnershipTest`, PR 6423: `expected: <true> but was: <false>` at the `setWritable` line).
- **Technique:** put a regular file where the cache folder should be (`new File(tempDir, "cache").createNewFile()`). Everything written below it fails with `IOException` on every platform, root included, and needs no cleanup.
- **How it was found:** the failed job's log is `gh api repos/UniversalMediaServer/UniversalMediaServer/actions/jobs/<job id>/logs` (job ids are in `gh pr view <n> --json statusCheckRollup`); `gh run view --log` printed nothing here. Reading a log starts no CI.
- **Local run without Docker:** Maven 3.9.x from archive.apache.org (verify the `.sha512`), then `mvn -B -q -Dtest=<Class> -Dsurefire.failIfNoSpecifiedTests=false test` with `-Dmaven.repo.local` in scratch; a JDK 17 or newer is enough (the build targets release 17). The first run downloads dependencies and takes several minutes. For red, delete the production line under test, rerun, restore it.
- **What only Windows CI confirms:** that the regular-file technique also fails the write on Windows. Java's `FileOutputStream` opening `<file>\name` fails there too (the parent is not a directory), but no Windows JVM was run locally.
