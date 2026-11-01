---
name: search-upstream-first
description: >-
  Before fixing a bug in software the edition did not write, search upstream's current branch, its merge requests and its issues for the same fix; carry upstream's commit with its author's credit when it exists, and write our own fix only when nothing does.
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
