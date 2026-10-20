# Working on Sparky Stereo OS

These instructions serve human contributors and AI partners, including local models.
Treat every partner as a capable colleague: explain evidence, challenge a mistaken assumption and own corrections.

## Start with the task

1. Read [the edition contract](skills/sparky-stereo/SKILL.md), then [the working method](skills/ai-partners/SKILL.md).
2. Choose only the relevant domain from [the skills index](skills/README.md). Follow its working recipe; open detailed references when that step needs them.
3. Read the task's shared project-memory index and relevant decisions, then check the target repository's status and instructions before editing. Preserve unrelated work and identify the source revision and installed package separately.
4. State the intended result, affected layer and observable check. Use existing tools and fixtures before making another implementation.
5. Make the change, run the relevant checks, and leave the result and next action in a small handoff. A missing environment is an explicit gap, not a passing test.

The current user's task and authorization take precedence over historical examples here.
Continue already authorized work; ask only for missing information or a genuinely new boundary.
Public messages and submissions need the responsible maintainer's authorization of their content; do not infer it from a draft or a skill.

## Locate the right evidence

- Specifications define a format; source inspection shows an implementation; a test establishes only what it exercised.
- Keep **proposed**, **implemented**, **tested**, **packaged**, **published** and **accepted upstream** distinct.
- Source versions, dates, commands, expected results, actual results and limitations belong beside evidence.
- Desktop plane depth can use synchronized 2D views with disparity. Actual 3D scenes need coherent per-eye projections. See the contract before choosing a renderer.
- Use public source and synthetic fixtures in distributable material. Private correspondence, contact addresses, credentials and personal records stay outside this repository and its packages.

## Distribution maintenance

[Maintainer workflow](docs/maintainer-workflow.md) covers the `task-sparky-stereo-os-developer` role, the skills package, isolated checks and release handoffs.
The installed reference tree is `/usr/share/sparky-stereo-os`; its `SOURCE` identifies the snapshot.
It is documentation, not the writable source checkout. Use a checkout to make changes.
No model service, account or particular assistant is required to read these files or run the documented checks.

For a model without file access, use `python3 tools/skills-context.py --help` to assemble a bounded text context from selected skills and references.
Commands in skills run in the named test environment; they are not permission to alter a person's active desktop, phone or displays.
