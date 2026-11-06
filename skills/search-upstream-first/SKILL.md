---
name: search-upstream-first
description: >-
  Before fixing a bug in software the edition did not write: search upstream's default branch for commits on the file or
  function since our base, then its merge requests or pull requests, then its issues and mailing lists (lore.kernel.org
  for the kernel), then our own published debian/patches; carry upstream's commit with its author's credit (DEP-3
  Origin: upstream, Applied-Upstream) when it exists, write our own fix only when nothing does. Load it at the first
  step of any fix in a pinned upstream release, when a diagnosis is already done, when a brief says the published
  package lacks a fix, before writing our own lock or workaround, or before reporting a bug upstream.
---

# Search upstream before fixing

Daniel, 2026-11-01: "we should always do this search before venturing into fixing things alone".
A bug in the release the edition builds is often fixed already on upstream's development branch, by a person who knows the code.
Finding that fix first saves the diagnosis and the build, keeps upstream's own commit and its author's credit in our package, and spares the maintainers a report about something they solved.

**Check freshness first.**
Written on 2026-11-01.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first. [`upstream-outreach`](../upstream-outreach/SKILL.md) covers sending our own fix, [`forks-and-online`](../forks-and-online/SKILL.md) covers where our branches go, and [`edition-packaging`](../edition-packaging/SKILL.md) covers the recipe's patch series.

## Working recipe

1. **Name what is broken:** the file, the function, and the base, which is the release or commit the edition builds.
2. **Search upstream's default branch** for commits on that path since the base.
   - With a clone: `git fetch upstream`, then `git log --oneline <base>..upstream/<default> -- <path>`, then `git log -S '<the code you would change>' upstream/<default> -- <path>`.
   - GitHub without a clone: `gh api "repos/<owner>/<repo>/commits?path=<path>&since=<date of the base>"`, then `gh api repos/<owner>/<repo>/commits/<sha>` to read a candidate's diff.
   - GitLab without a clone: `GET /api/v4/projects/<id>/repository/commits?path=<path>&since=<date>`.
   - A project that reviews on a mailing list (the kernel): search the list's archive through its public git mirror, `git clone --shallow-since=<date of the base> https://lore.kernel.org/<list>/0`, then `git log --grep` for the function or the error; it works where the web pages show an anti-bot wall. Check the subsystem's tree (for DRM, drm-misc's `-fixes` and `-next` branches) before calling a posted patch merged or missing.
3. **Search the merge requests or pull requests,** open and merged, that touch the path or name the symptom.
4. **Search the issue tracker** for the symptom, the function name and the error text.
5. **Record what you searched and what you found,** whatever it is: the forge, the queries, and each candidate with its URL, author and date, or "nothing found". The record goes in the work's report or hand-back.
6. **Decide by what you found:**

| Upstream has | We do |
| --- | --- |
| A merged commit | Carry that commit as the patch, credited (header below). Our test is our build without it (red) and with it (green). |
| An open merge request | Carry its commit, credited, naming the merge request; follow its review and replace it with the merged commit when it lands. |
| A report, no fix | Write the fix, prove it red and green, and offer it on that report through [`upstream-outreach`](../upstream-outreach/SKILL.md). |
| Nothing | Write the fix, prove it red and green, then report it upstream through [`upstream-outreach`](../upstream-outreach/SKILL.md). |

7. **At the next rebase,** drop the carried commit when the new base contains it.

## The header of a carried commit

Debian's patch tagging guidelines, [DEP-3](https://dep-team.pages.debian.net/deps/dep3/), define the fields.
`Origin: upstream` is for a commit that applies unchanged; `Origin: backport` is for one adapted to our older base.

```
Description: <upstream's subject line>
Origin: upstream, <commit URL>
Author: <name and address as upstream's commit records them>
Applied-Upstream: <the version that contains it, or the branch and commit>
Last-Update: <YYYY-MM-DD>
```

Name the author and the commit in the recipe's credits and in the edition's ATTRIBUTIONS, with the name as upstream's records give it.

## Where the rule came from

- **DXVK, 2026-11-01.** DXVK 2.7.1 drew the first frame after a window resize from the old-size buffer in D3D10 and D3D11, in mono and in stereo.
- **The diagnosis.** A partner spent a full milestone on it: 24 installed cases, a DRI3 trace of the stale pixmap, and the cause in `D3D11SwapChain::ChangeProperties`, which passed the old extent to the presenter. It proposed a one-line correction.
- **Upstream already had it.** The identical line was merged on 2026-09-25: [3dbf33cb](https://github.com/doitsujin/dxvk/commit/3dbf33cb2205dd0d573cbc7a65e3855d97a4800b), "[d3d11] Fix incorrect swapchain resize dimensions", by ficool2. One search of the file's history would have found it.
- **What the diagnosis still gave us.** Its first-frame fixture became the red and green test for carrying ficool2's commit.
- **The same search, on a mailing list (nouveau, 2026-10-02).** An RTX 3060 on nouveau without its GSP firmware has no graphics engine, and the `GET_ZCULL_INFO` ioctl dereferenced the missing engine when Mesa's NVK started, so KWin died.
  The fix was already on the nouveau list, not yet in drm-misc: Jim Cromie's "drm/nouveau: Fix NULL pointer dereference in GET_ZCULL_INFO ioctl" of 2026-08-15.
  The edition's kernel carried his patch under his authorship, with Zhenhao Wan's fix for `GETPARAM_GRAPH_UNITS`, which the same machine hit next, instead of a duplicate of our own.

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (6 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
