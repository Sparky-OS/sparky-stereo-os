# Skills for maintaining Sparky Stereo OS

**For distro maintainers, contributors and their AI partners:** reusable instructions, evidence and test recipes in plain Markdown.
Humans can follow them directly. Local and hosted models can read the same files; no account or provider is required.
These are edition-maintenance procedures, not a general application-development course.

Start with [AGENTS.md](../AGENTS.md), the [edition contract](sparky-stereo/SKILL.md) and [working together](ai-partners/SKILL.md).
Then choose one task below. Each domain starts with a short working recipe; detailed sections retain the measurements and traps that motivated it.
Historical versions and test results are evidence for their stated setup, not a guarantee about newer software.

| Your task | Read next |
| --- | --- |
| Native toolkit, GLX/EGL/Vulkan or window integration | [native-linux](native-linux/SKILL.md), then [stereo-window-3d-area](stereo-window-3d-area/SKILL.md) |
| Theme, Canvas Painter, StyleKit or KWin effects depth | [stereo-window-3d-area](stereo-window-3d-area/SKILL.md) and its [Qt/KDE depth reference](stereo-window-3d-area/references/qt-kde-depth.md) |
| A scene with cameras and view-dependent rendering | [stereo-two-cameras](stereo-two-cameras/SKILL.md) |
| Video decoding, editing, export or streaming | [stereo-video](stereo-video/SKILL.md) |
| Serving or casting to a television, player or phone over the network | [stereo-serving](stereo-serving/SKILL.md) |
| Photos, format marks or thumbnails | [stereo-pictures](stereo-pictures/SKILL.md) |
| Colour precision or HDR metadata | [deep-colour](deep-colour/SKILL.md) |
| Artwork, animated pairs or theme assets | [stereo-artwork](stereo-artwork/SKILL.md) |
| Proving compositor/application stereo | [stereo-proof-rig](stereo-proof-rig/SKILL.md) |
| Kernel/display driver or virtual display modes | [drivers](drivers/SKILL.md), [vkms-stereo](vkms-stereo/SKILL.md) |
| A VM viewer and its pointer/mode changes | [stereo-vm](stereo-vm/SKILL.md) |
| VR content on a TV or stereo spectator | [vr-to-3d](vr-to-3d/SKILL.md) |
| A desktop or media stream on a phone/headset | [3d-to-vr](3d-to-vr/SKILL.md); select the relevant receiver/transport section |
| Wine/Proton games | [proton-wine](proton-wine/SKILL.md) |
| Flight and racing simulators | [simulators](simulators/SKILL.md); select the engine and failing stage |
| Controllers, labels, focus or shell navigation | [gamecontroller](gamecontroller/SKILL.md) |
| Sound routing, formats or MIDI | [audio](audio/SKILL.md) |
| Idle, locking, lid, CEC, swap or hibernate | [power-idle](power-idle/SKILL.md) |
| Plasma search defaults, task manager, frozen windows and drive formatting | [kde-desktop-defaults](kde-desktop-defaults/SKILL.md) |
| Unix groups for desktop users | [user-groups](user-groups/SKILL.md) |
| Logs, retained kernels and cleanup | [system-housekeeping](system-housekeeping/SKILL.md) |
| Packages and their provenance, Paweł's formula, distro tasks and dependencies, the signed repository, the ISO | [edition-packaging](edition-packaging/SKILL.md) |
| Lean Code projection or resolving installed source | [lean-code](lean-code/SKILL.md) |
| Android Qt test reproduction | [qt-android-ci](qt-android-ci/SKILL.md) |
| Brazilian certificate sources and algorithms | [brazil-certificates](brazil-certificates/SKILL.md) |
| Sparky CA trust-store implementation | [certificate-manager](certificate-manager/SKILL.md) |
| A maintainer message, contribution or follow-up | [upstream-outreach](upstream-outreach/SKILL.md) |
| A README opening, About line or public introduction | [writing-front-pages](writing-front-pages/SKILL.md) |

## Installed and offline use

The revised `task-sparky-stereo-os-developer` recipe brings `sparky-stereo-skills` for distro maintenance.
It installs the public reference tree at `/usr/share/sparky-stereo-os`; `SOURCE` records the snapshot.
Ordinary application developers can install the skills separately when useful.
See [the maintainer workflow](../docs/maintainer-workflow.md) for package checks and source/publication boundaries.

- Read the files directly, or run `sparky-stereo-skills list`.
- Use `sparky-stereo-skills context native-linux` for selected text suitable for a model without file tools.
- Use `sparky-stereo-skills context --list-sections 3d-to-vr`, then `--section '3d-to-vr:Exact heading'`, for a small part of a long skill.
- `sparky-stereo-skills link` retains the optional assistant-folder integration; it preserves the person's own skills.
- `sparky-stereo-skills export skills.zip` retains the skill-import format. `sparky-stereo-skills bundle reference.zip` instead preserves the full offline tree and its relative references.

In a checkout use `python3 tools/skills-context.py` in place of `sparky-stereo-skills context`.
The context budget is in characters, not tokens; an oversized request fails rather than truncating instructions.
A selected section is explicitly labelled as an excerpt. Read additional linked references when the task needs them.

## Improving a skill

Keep its existing name and path so installed integrations keep finding it.
Write the decision, the minimum inputs, the operation and the observable result; preserve useful evidence and credits.
Keep substantial conditional detail in a linked reference, and individual run history in its evidence record.
Use a valid YAML `name` and `description`; run `python3 tools/check-skills.py` and check the actual instructions as a reader.
The validator checks discovery metadata and local file targets, not technical truth, external URLs or every Markdown anchor.
