---
name: contrib-peertube
description: >-
  Contribute to PeerTube on GitHub with its issue-first workflow, exact test
  gates and public transcoding review record. Load with upstream-outreach
  before a pull request.
metadata:
  requires-packages: nodejs | npm
---

# Contributing to PeerTube

Written on 2026-10-24 from PeerTube's contribution guide, repository `AGENTS.md`, pull-request template and public pull request [#7816](https://github.com/Chocobozzz/PeerTube/pull/7816), read 2026-10-24.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is PeerTube's own practice.
Re-read those files in the current `develop` tree before every round.

## Where
- Work on GitHub against PeerTube's `develop` branch.
- The guide says: "Always talk about features you want to develop by creating/finding and commenting the issue tackling your problem before you start working on it, and inform the community that you begin coding by claiming the issue."

## Pull stages and linking
- Submit a draft pull request to show work in progress.
- Submit a full pull request when it is ready for code review before merge.
- Link it with PeerTube's exact instruction: `fixes #issue_number`.
- The template asks for a description with context, related issues and screenshots where relevant.
- The guide says development happens on `develop` and that a new branch in the contributor's fork must be supplied to push: `git push --set-upstream me <your branch name>`.

## Proof and tests
- The template offers four truthful choices: you added tests, the PR is a draft still needing work, the PR does not update server code, or you need help.
- `AGENTS.md` sets Node.js 22 or newer, `pnpm >= 10.9`, PostgreSQL, Redis and FFmpeg as the project's tools.
- It says do not use npm or yarn for install; install dependencies with `pnpm install --frozen-lockfile`.
- It requires `npm run build:server` and `npm run lint` to pass before pushing.
- Changing the OpenAPI surface requires `npm run swagger-cli -- validate support/doc/api/openapi.yaml`.
- A schema change requires a new migration and `LAST_MIGRATION_VERSION` in `server/core/initializers/constants.ts` to be incremented.
- For a transcoder change, record a small generated input, the exact invocation and the resulting stream metadata; verify the declared stereo layout survives PeerTube's FFmpeg path.
- PeerTube's existing FFmpeg transcoding configuration is the surface for codec or container behavior, not a parallel stereo copy of it.

## AI policy
- PeerTube's contribution guide and pull-request template state nothing about AI assistance.
- Its repository `AGENTS.md` contains agent guardrails for dependencies, migrations, locking and CI but no AI-authorship policy.
- Both files were checked on 2026-10-24.

## Public record
- Merged pull request [#7816](https://github.com/Chocobozzz/PeerTube/pull/7816) used the issue-and-draft route.
- On 2026-10-13, maintainer `Chocobozzz` merged pull request #7816 as commit `341818e`.
- GitLab reshaped the proposed behavior into an existing transcoding profile and handled rotation during that review.
- That review shows that PeerTube prefers fitting a stereo change into its existing transcoding profile system, not adding a parallel path.

## Replies
- Answer each review point with its relevant command, migration, OpenAPI check or playback path.
- Thank the reviewer for the specific review work.
