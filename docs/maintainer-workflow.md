# A working guide for distribution maintainers

**For people building, testing and packaging Sparky Stereo OS:** the same instructions and checks are usable by hand or with a local or hosted AI partner.

## Choose the role

`task-sparky-stereo-os-developer` is the distro-maintainer task: it brings the ordinary developer tools, the edition's stack development files, packaging tools, proof benches and `sparky-stereo-skills`.
`task-sparky-stereo-developer` is the application/game-development task; the revised recipe does not make the distro workflow a dependency of that task.
Both tasks are opt-in. The skills package is also installable on its own.
These describe the source recipes; a local build is not a claim that the repository or ISO already contains it.

The current development system can receive tested updates while the final end-user ISO is still being assembled.
For Android desktop transmission, follow the [Flat Headset development channel instructions](https://github.com/Sparky-OS/flat-headset/tree/main/apk) and update the PC packages first, whether running a live USB or an installed system.
A live session without persistence loses those updates when rebooted; repeat the update before testing the matching APK.
This channel is part of distribution development, with its own published version list and limits.

The skills package puts the public reference tree in `/usr/share/sparky-stereo-os`.
Read `SOURCE` for its revision and `AGENTS.md` for the starting path.
`SOURCE-MANIFEST.sha256` identifies the authored snapshot; the package's `lc1` manifest records installed file hashes after projection.
Use a writable source checkout for edits; installed documentation is a versioned reference.
The generic source tree remains useful to other distributions under its existing licences; adoption does not mean installing our whole graphics stack over theirs.

## Work through one change

1. Record the source revision, installed package versions and existing dirty work. Pick the layer that owns the behavior.
2. Open [the contract](../skills/sparky-stereo/SKILL.md), [the working method](../skills/ai-partners/SKILL.md) and one [domain skill](../skills/README.md).
3. Reproduce with a small fixture. Write down expected and actual behavior before changing code.
4. Run relevant checks. For a regression, retain the old failing result beside the fixed result. Check 2D behavior as well as stereo.
5. Build source and binary packages, record provenance, and test the installed payload in isolation. Check dependency resolution and upgrade behavior when changed.
6. Hand back the patch, commands, evidence and limits. Upstream acceptance, repository publication, ISO inclusion and physical-device qualification are separate milestones.

Prefer getting reusable stereo support accepted upstream. When a suitable upstream release includes our changes,
test that release and retire the corresponding downstream patches. We still own distro integration, packaging,
Lean Code qualification and user-facing bug triage; upstream acceptance does not replace those checks.

For Lean Code use [its skill](../skills/lean-code/SKILL.md) and current release contract.
Documentation and skill instructions remain authored text; the package must not erase the instructions its maintainers need.

## Small contexts and offline use

Humans can open the Markdown directly. No AI account or service is needed.
From a checkout, create a selected text bundle:

```sh
python3 tools/skills-context.py native-linux --output /tmp/native-linux-context.txt
python3 tools/skills-context.py --section '3d-to-vr:Phone link formats and late-frame recovery (checked 2026-10-15)' --output /tmp/phone-context.txt
```

From the updated package, the equivalent entry is `sparky-stereo-skills context native-linux`.
It includes the entry guidance, contract and working method, selected content, source identity and file hashes.
Add a needed document explicitly with `--reference docs/house-formats.md`; other references are not silently loaded.
The size limit counts characters, not model tokens. Choose it for your client; an over-limit request fails without a partial output.
A local model without tools should return a proposed patch and unrun commands for a human to check.

`sparky-stereo-skills link` retains its existing opt-in assistant-folder integration.
`sparky-stereo-skills export skills.zip` makes the existing skill-import ZIP; clients differ in handling references outside a skill folder.
Use `sparky-stereo-skills bundle reference.zip` for the complete offline reference tree, preserving `skills/`, `docs/`, `tools/` and `AGENTS.md` paths.
That archive is for extraction and file access, not a promise that every client's import screen accepts a whole documentation tree.

## Updating the instructions package

Run `python3 tools/check-skills.py` in the public checkout.
Review changed claims and links, then pin a reviewed source commit in the package build.
Do not label a package with an old commit while copying uncommitted files into it.
Local candidate snapshots must say they include working-tree changes and carry a file manifest; release snapshots must name the actual committed source.
The helper tests exercise linking, user-file preservation and removal; context and bundle checks exercise use without an AI client.
Avoid installing the large developer task merely to test documentation packaging.
