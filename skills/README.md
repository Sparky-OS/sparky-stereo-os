# Skills for maintaining Sparky Stereo OS

**For distro maintainers, contributors and their AI partners:** reusable instructions, evidence and test recipes in plain Markdown.
Humans can follow them directly. Local and hosted models can read the same files; no account or provider is required.
These are edition-maintenance procedures, not a general application-development course.

Start with [AGENTS.md](../AGENTS.md), the [edition contract](sparky-stereo/SKILL.md) and [working together](ai-partners/SKILL.md).
Then choose one task below. Each domain starts with a short working recipe; detailed sections retain the measurements and traps that motivated it.
Historical versions and test results are evidence for their stated setup, not a guarantee about newer software.
Core skills are `sparky-stereo`, `ai-partners`, `making-skills`, `development-hooks`, `search-upstream-first`, `upstream-outreach`, `edition-packaging` and `writing-front-pages`; they always link.

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
| A test on a real machine or 3D television: baselines, recovery with a person at the bench, power and UPS, unattended labs with LAVA or labgrid | [test-bench](test-bench/SKILL.md) |
| Proving compositor/application stereo, or why the two eyes differ; a showcase stereo screenshot | [stereo-proof-rig](stereo-proof-rig/SKILL.md) |
| Kernel/display driver or virtual display modes; the edition kernel's configuration, DKMS modules on a new kernel | [drivers](drivers/SKILL.md), [vkms-stereo](vkms-stereo/SKILL.md) |
| A QEMU or SPICE VM viewer and its pointer/mode changes | [stereo-vm](stereo-vm/SKILL.md) |
| VR content on a TV or stereo spectator | [vr-to-3d](vr-to-3d/SKILL.md) |
| A desktop or media stream on a phone/headset | [3d-to-vr](3d-to-vr/SKILL.md); select the relevant receiver/transport section |
| Wine/Proton games; Steam started from a script; Easy Anti-Cheat on Linux | [proton-wine](proton-wine/SKILL.md) |
| Flight and racing simulators | [simulators](simulators/SKILL.md); select the engine and failing stage |
| Controllers, labels, focus or shell navigation | [gamecontroller](gamecontroller/SKILL.md) |
| Sound routing, formats or MIDI | [audio](audio/SKILL.md) |
| Idle, locking, lid, CEC, swap or hibernate | [power-idle](power-idle/SKILL.md) |
| Plasma search defaults, task manager, frozen windows and drive formatting | [kde-desktop-defaults](kde-desktop-defaults/SKILL.md) |
| Unix groups for desktop users | [user-groups](user-groups/SKILL.md) |
| Logs, retained kernels and cleanup | [system-housekeeping](system-housekeeping/SKILL.md) |
| Packages and their provenance, Paweł's formula, distro tasks and dependencies, apt pins and conffiles, the signed repository, the ISO | [edition-packaging](edition-packaging/SKILL.md) |
| One more program's stereo integration: the list, the pack format, the missing program, the proof | [stereo-integrations](stereo-integrations/SKILL.md) |
| Lean Code projection or resolving installed source | [lean-code](lean-code/SKILL.md) |
| Android Qt test reproduction | [qt-android-ci](qt-android-ci/SKILL.md) |
| Brazilian certificate sources and algorithms | [brazil-certificates](brazil-certificates/SKILL.md) |
| Sparky CA trust-store implementation | [certificate-manager](certificate-manager/SKILL.md) |
| A task brief, handoff or review for a person or an AI partner; an unattended runner that stops, loops or cannot write | [ai-partners](ai-partners/SKILL.md) |
| A new skill or an extension of one: the header and its limits, the description as a trigger clause inside the index's window, lessons files, the review that walks each rule against the diff, the cold-reader test | [making-skills](making-skills/SKILL.md) |
| Hooks: a rule an AI tool or git enforces by itself (the designs read after a compaction, briefs and hand-backs, the outreach guard, the publish check), the workspace layout they assume, a hook that refuses a tool call, adding one | [development-hooks](development-hooks/SKILL.md), with [`hooks/`](../hooks/README.md) |
| A bug in a program the edition did not write, before writing any fix | [search-upstream-first](search-upstream-first/SKILL.md) |
| Forks, pushing, and checking that the work is online; releases and DOIs, the Sponsor button, our own libraries' repositories, where large files go | [forks-and-online](forks-and-online/SKILL.md) |
| A maintainer message, contribution or follow-up | [upstream-outreach](upstream-outreach/SKILL.md) |
| An FFmpeg pull request: series, trailers, FATE, the review bot (with upstream-outreach) | [contrib-ffmpeg](contrib-ffmpeg/SKILL.md) |
| A HandBrake pull request (with upstream-outreach) | [contrib-handbrake](contrib-handbrake/SKILL.md) |
| A Universal Media Server pull request (with upstream-outreach) | [contrib-ums](contrib-ums/SKILL.md) |
| An MKVToolNix merge request (with upstream-outreach) | [contrib-mkvtoolnix](contrib-mkvtoolnix/SKILL.md) |
| An mpv pull request (with upstream-outreach) | [contrib-mpv](contrib-mpv/SKILL.md) |
| A Qt change through Gerrit (with upstream-outreach) | [contrib-qt](contrib-qt/SKILL.md) |
| A PeerTube pull request (with upstream-outreach) | [contrib-peertube](contrib-peertube/SKILL.md) |
| An x265 pull request (with upstream-outreach) | [contrib-x265](contrib-x265/SKILL.md) |
| A VLC merge request (with upstream-outreach) | [contrib-vlc](contrib-vlc/SKILL.md) |
| A KDE Invent change or Bugzilla report (with upstream-outreach) | [contrib-kde](contrib-kde/SKILL.md) |
| A Debian bug report with its fix inline, or a Salsa merge request (with upstream-outreach) | [contrib-debian](contrib-debian/SKILL.md) |
| A Linux kernel patch or bug report, reviewed by the human before it is sent (with upstream-outreach and drivers) | [contrib-kernel](contrib-kernel/SKILL.md) |
| An MPlayer patch, prepared but held until release is requested (with upstream-outreach) | [contrib-mplayer](contrib-mplayer/SKILL.md) |
| A README opening, About line or public introduction | [writing-front-pages](writing-front-pages/SKILL.md) |

## Installed and offline use

The revised `task-sparky-stereo-os-developer` recipe brings `sparky-stereo-skills` for distro maintenance.
It installs the public reference tree at `/usr/share/sparky-stereo-os`; `SOURCE` records the snapshot.
Ordinary application developers can install the skills separately when useful.
See [the maintainer workflow](../docs/maintainer-workflow.md) for package checks and source/publication boundaries.

- Read the files directly, or run `sparky-stereo-skills list`.
- Use `sparky-stereo-skills find "<task or symptom>"` when you do not know which skill applies: it ranks the skills by name, description and the task table above, offline and the same every time, and prints each path with the `context` command to run next.
- Use `sparky-stereo-skills context native-linux` for selected text suitable for a model without file tools.
- Use `sparky-stereo-skills context --list-sections 3d-to-vr`, then `--section '3d-to-vr:Exact heading'`, for a small part of a long skill.
- `sparky-stereo-skills link` retains the optional assistant-folder integration; it preserves the person's own skills.
- `sparky-stereo-skills export skills.zip` retains the skill-import format. `sparky-stereo-skills bundle reference.zip` instead preserves the full offline tree and its relative references.

In a checkout, run the installed `sparky-stereo-skills` on it with `SPARKY_STEREO_REFERENCE=$PWD sparky-stereo-skills context ...` and `SPARKY_STEREO_REFERENCE=$PWD sparky-stereo-skills find "<task or symptom>"`.
The context budget is in characters, not tokens; an oversized request fails rather than truncating instructions.
A selected section is explicitly labelled as an excerpt. Read additional linked references when the task needs them.

## Improving a skill

[making-skills](making-skills/SKILL.md) is the skill for this: its recipe, its checks and the traps this folder met.
The short form follows.

Keep its existing name and path so installed integrations keep finding it.
Write the decision, the minimum inputs, the operation and the observable result; preserve useful evidence and credits.
Keep substantial conditional detail in a linked reference, and individual run history in its evidence record.
Use a valid YAML `name` and `description`; run `python3 tools/check-skills.py` and check the actual instructions as a reader.
Count a description before you commit it: `python3 tools/check-skills.py --count <name>` prints its tokens against the index's window of 256 and its characters against 1024.
The description and the task table are how a reader finds a skill: name the programs, tools and symptoms a person would type, and add the symptom to `data/routing/symptoms-157.tsv` of the skills engine (sparky-os/skills-mcp in the build tree), which every change to the engine or to the descriptions is checked against when a new kind of work arrives.
Write the description as a trigger clause: what the skill is for, then the symptoms, error strings, programs and components that should bring a reader to it, then what it is not for and which skill is, within 1024 characters ([making-skills, the description routes](making-skills/SKILL.md#the-description-routes-the-body-executes)).
Write the skill as you go, while the work happens: the recipe first, each trap with its symptom, cause, fix and how the cause was found, the part's perks; longer harvests go to `references/lessons-<date>.md` ([making-skills, what goes in](making-skills/SKILL.md#what-goes-in-each-time)).
A local vector index or an MCP over these files finds a skill by the same description; the files stay the source and the index is rebuilt after every merge ([finding a skill locally](ai-partners/SKILL.md#finding-a-skill-locally)).
The validator checks discovery metadata, both limits of a description and local file targets, not technical truth, external URLs or every Markdown anchor.
