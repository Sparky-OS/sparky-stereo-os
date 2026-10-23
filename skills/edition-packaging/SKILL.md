---
name: edition-packaging
description: >-
  Maintain distro role tasks, dependency policy, native source/binary packages and installed-package validation for Sparky Stereo OS.
---

# Packaging the edition

## Working recipe

1. Record source commits, package versions, architecture, repository pins and the task that should install the result.
2. Write the control file, copyright file, script headers and changelog in [Paweł's formula](references/sparky-formula.md) with the edition's [provenance](#provenance-daniel-2026-10-02-always); rebuild upstream packages as [rebuilt packages](references/rebuilt-packages.md) says.
3. Build in isolation, inspect package contents and simulate installation/upgrade before the installed-payload checks below.
4. Return source/binary hashes, dependency resolution and runtime evidence. Separate local candidate, repository publication and ISO inclusion.

**Check freshness first.**
Written on 2026-10-07; the developer tasks and the skills package on 2026-10-16; provenance, Paweł's formula and rebuilt packages on 2026-10-23, from rules dated 2026-10-02 to 2026-10-22.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

## Provenance (Daniel, 2026-10-02): always

Every package of ours says who made it, the Sparky way, and [`provenance.sh`](https://github.com/Sparky-OS/sparky-stereo-os-build/blob/main/sparky-os/repo/provenance.sh) in the build tree writes it.

- `Maintainer:` is Daniel's packaging identity, `Daniel Ramos (Capitain Jack)` with his project address, as provenance.sh writes it; build scripts set `DEBFULLNAME` and `DEBEMAIL` to it, and git commits carry `Daniel Campos Ramos` with the same address. Never `root@<container>`, and never an address from a build account or an assistant's session (Daniel, 2026-10-22).
- `Original-Maintainer:` keeps whoever maintained a package we modified (Debian Qt/KDE Maintainers, NVIDIA), the convention of Debian derivatives.
- `Homepage: https://sparkylinux.org`, with no trailing slash, the form most of Paweł's packages use.
- `Bugs:` is the edition's [tracker](https://github.com/Sparky-OS/sparky-stereo-os/issues): a problem in our build never goes to the maintainer of the package we modified (Daniel, 2026-10-08).
- The copyright file keeps its holders and gains our `Files: debian/*` stanza with the credit in Daniel's wording of 2026-10-07: "Sparky Stereo OS, Daniel Ramos's (Capitain Jack) edition of SparkyLinux (https://sparkylinux.org, by Paweł "pavroo" Pijanowski)".
- Paweł's own packages keep his `Maintainer:` and are never modified in place: ship ours beside them, divert with `dpkg-divert`, or send him a pull request.
- **Order:** `provenance.sh --tree STAGING` runs before Lean Code and the final checksums. A package sealed with the lc mark is never restamped (wrong provenance there needs a fresh build), and `make-repo.sh` never rewrites archives.

## Paweł's way first

Everything we ship follows Paweł "pavroo" Pijanowski's way first (he created SparkyLinux); our side adds what the stereo stack needs.
The edition's own tools, themes and metapackages follow [his formula](references/sparky-formula.md), APTus included.
His review comes after publication, and anything on his side needs his approval first (Daniel, 2026-10-02; [working with Paweł](references/sparky-formula.md#working-with-paweł)).

## Tasks, the Debian way

People choose what they do, not package names.
The edition offers its programs as **tasks**, like Debian's `task-kde-desktop`: one metapackage per role, plus a description file so `tasksel` lists them.

| Task | For |
|---|---|
| `task-sparky-stereo-gamer` | games, Steam, the stereo Lutris build, runtimes, controllers |
| `task-sparky-stereo-designer` | drawing, painting, photo and 3D modelling, colour management |
| `task-sparky-stereo-creator` | video editing, streaming, encoding, subtitles |
| `task-sparky-stereo-musician` | audio production: plugins, synthesizers, routing |
| `task-sparky-stereo-scientist` | science and engineering programs that show stereo 3D today |
| `task-sparky-stereo-student` | education programs that show stereo 3D today |
| `task-sparky-stereo-simmer` | flight and racing simulators and the tools for their rigs |
| `task-sparky-scientist`, `task-sparky-student` | the programs of those fields with no stereo version yet |
| `task-sparky-stereo-developer` | code and game engines: KDE's development tools first, the Qt 6 and KDE Frameworks development files, compilers, debuggers and build systems for every language Debian carries, version control, containers and virtual machines, graphics and GPU debugging, game engines and libraries |
| `task-sparky-stereo-os-developer` | building, testing and packaging the edition itself: the development files of the stereo stack at the edition's versions, Debian packaging, the proof rig and the virtual display benches, KDE's CI run locally; it brings the developer task |

- **Stereo and 2D flavours** (science and education, where most programs are still 2D): the stereo task holds only programs whose stereo is proven on the edition. The 2D task holds the rest and never names a program the stereo task has, so installing it never replaces a stereo build. A program moves to the stereo task when its proof lands.
- **The core** stays in a few metapackages everyone gets (desktop, hardware support, languages, system). The top `sparky-stereo` depends on the core and recommends every task except the two developer tasks, which are installed on request (Daniel, 2026-10-16: "just install the meta and start developing").
- **Policy:** essentials and the stereo stack in `Depends`; programs in `Recommends`, so a user can remove one and keep the task. Never a versioned library name in `Depends`: Debian renames those at every transition.
- **Renaming:** the old package becomes transitional, depending on the new one, so upgrades keep working.
- **Every build of ours must be in some task.** A stereo build that no list names is never installed; this was found on 2026-10-07 for seven of our KDE and science builds.

## The skills for distribution maintainers and their partners

`sparky-stereo-skills` installs this repository's skills, with the documents and tools they link to, in `/usr/share/sparky-stereo-os`, taken from one commit of the repository and named in `/usr/share/sparky-stereo-os/SOURCE`.
`task-sparky-stereo-os-developer` depends on it directly. The revised ordinary developer task does not; it remains separately installable.
Read [the maintainer workflow](../../docs/maintainer-workflow.md) for human/offline use and bounded model context.
The package includes `AGENTS.md`, validates skill metadata/local links, and offers `context` and complete-tree `bundle` commands alongside the existing skill-import ZIP.
Source snapshots identify the exact commit or explicitly labelled local candidate; an old pin must never masquerade as the revised content.

A package never writes into home folders from its maintainer scripts, so each person runs `sparky-stereo-skills`, or answers the offer it makes once at login when an assistant is found.
It links every skill into the folders where the assistants read skills, and nothing else:

| Folder | Read by (each tool's documentation) |
|---|---|
| `~/.agents/skills` | [Codex](https://learn.chatgpt.com/docs/build-skills), [Gemini CLI](https://geminicli.com/docs/cli/skills/), [OpenCode](https://opencode.ai/docs/skills/), [GitHub Copilot](https://code.visualstudio.com/docs/copilot/customization/agent-skills), [Cursor](https://cursor.com/docs/skills), [goose](https://goose-docs.ai/docs/guides/context-engineering/using-skills) |
| `~/.claude/skills` | [Claude Code](https://code.claude.com/docs/en/skills), and also OpenCode, GitHub Copilot and goose |
| `~/.cline/skills` | [Cline](https://docs.cline.bot/customization/skills) |
| `~/.gemini/skills`, `~/.config/opencode/skills`, `~/.copilot/skills`, `~/.cursor/skills` | the tool named, when a person prefers its own folder |

- **By default** it links into the shared folder and the folders of the assistants it finds; the others are a choice by name.
- **A skill is linked only when its `SKILL.md` starts with a YAML header** whose `name` is the folder's name and which has a `description`. Cline and goose refuse a skill whose name differs from its folder, and a header joined into one line makes every tool skip the skill silently (certificate-manager's, from 2026-10-14 until 2026-10-16).
- **It never replaces a person's own skill** of the same name, removes only its own links, and after an upgrade the next login links new skills and drops removed ones.
- **Local models:** `ollama launch` starts Claude Code, Codex or OpenCode on a local or cloud Ollama model ([Ollama's CLI](https://docs.ollama.com/cli)), and those read the same folders. **Open WebUI** imports skills from a ZIP of skill folders (Workspace, Skills, Import; [its documentation](https://docs.openwebui.com/features/workspace/skills)): `sparky-stereo-skills export skills.zip` makes it.
- **Proof:** link, then have each tool read the skills back: a command that lists them (`gemini skills list`, `goose skills list`), or the tool's request to its model captured at a local endpoint, where every skill's name must appear.

## tasksel lists only ours

A small package ships `/usr/share/tasksel/descs/sparky-stereo.desc` (a parent task `sparky-stereo`, then one stanza per task with `Parent`, `Key`, `Section: user`).
It diverts Debian's description files to a name that does not end in `.desc` (`dpkg-divert --rename` in `preinst`, removed in `postrm`), because tasksel reads only `*.desc`.
Hardware-helper tasks such as isenkram's stay.

## Only our builds are candidates

The repository is pinned at 1001.
A generated pin file blocks, at priority −1, the Debian and deb-multimedia builds of every package the edition's repository ships, plus Debian's `task-*` and the multimedia blend's metapackages.
Generate it from the repository index, never by hand, and rebuild the apt-configuration package when the repository gains packages.
This is the rule that already kept Bino ours: our build declares full side by side, and other builds would hand the compositor a picture outside the contract.

A package set waiting for a rebuild is left out of the block until the rebuild lands (see the next section).

## The GPU vendors' repositories: compute updates, the display driver stays ours

NVIDIA and AMD publish their display drivers in the same repositories as CUDA and ROCm, and the hardware setup gives the CUDA repository priority 1002.
Without a guard, an ordinary upgrade replaces our NVIDIA module and our amdgpu with the vendor's, which have no HDMI 3D.
`sparky-stereo-nvidia-driver-lock` (its own package, built from the module's source and version, required by `nvidia-kernel-open-dkms-stereo3d`) ships `10sparky-stereo-nvidia-driver-lock`: NVIDIA's and Debian's NVIDIA kernel modules at -1, every driver package at our module's NVIDIA version at 1005, other versions at 100.
`sparky-stereo-hardware` ships `sparky-stereo-gpu-nvidia` (the container toolkit at 990, its release candidates at 100, our `libnvidia-egl-wayland1` over NVIDIA's) and `sparky-stereo-gpu-amd` (AMD's out-of-tree kernel driver and `*amdgpu*` graphics packages from `repo.radeon.com` at -1; ROCm keeps updating).
Intel is not guarded.
`sparky-stereo-hardware` is in `sparky-stereo-hardware-support`, so every install carries the pins; a pin for a repository that is not configured does nothing.
A pin file whose name starts with `10` is read before `nvidia-driver-pin`, and the first record that names a package wins over any `Package: *` record, whatever the numbers.
To move the NVIDIA driver, rebuild our module first and publish; the lock follows because it is generated from the module's version, and the first upgrade installs only the new lock.
Prove a change in a Debian testing container with NVIDIA's and AMD's real repositories at the edition's priorities and a newer driver published beside them, with both of apt's solvers.
The measurements and the file by file account are in [GPU vendors' repositories](../../docs/gpu-vendor-repositories.md).

## Each build of ours

Each is the distribution's source package plus our patch series, versioned with the suffix `+stereo3dN`, built in a fresh `debian:testing` container, and it keeps its source package, so the repository can offer `deb-src`.
A 32-bit twin (Mesa and FFmpeg, for Steam and Wine) comes from the same source build as the 64-bit package: `dpkg` refuses to install the two together when a shared file such as the Debian changelog differs (`Multi-Arch: same`).
The rest, Mesa's acceptance and the KDE CI run before a push to invent.kde.org included, is in [rebuilt packages](references/rebuilt-packages.md).

**Lean Code release requirement (Daniel, 2026-10-18):** every package and ISO we publish passes the edition's Lean Code pipeline. Finish provenance and notices before projecting the disposable package tree; calculate checksums from its lean payload, then assemble and sign. The versioned `lc1` control marker binds the coverage manifest and lets clients skip rendering. Publish exact HR documentation companions beside the packages, outside the ISO's default package set. The publisher rejects missing or stale evidence; never add the marker by hand or change a previously published version in place. See the [lc package contract](../../docs/lean-code-packages.md). The 0.1.7 development tooling qualifies the Android companion package set; other existing packages and the final ISO still require migration.

## Receiver packages must prove their installed interface

Checked 2026-10-16 with KRDC Catch and KRdp.
When a reviewed change targets development master, backport it to the distribution release and retain the release's existing plugins and behaviour.
Build the translated catalogs as distribution patches, with test-only capture and mutation hooks disabled in the shipping executable.
After a full upgrade from the published packages, compare installed payloads with the package archives and run the visible connection action in an isolated session.
Capture only the synthetic receiver display and check eye identity, per-eye fit, changing source timecodes and reconnect.
Swap the synthetic source eyes and freeze its animation to prove that the same checker rejects reversed and stale pictures without enabling hooks in the shipped app.
For certificate rejection, verify that the connection reached TLS and failed pin validation; a server that never listened is not a passing control.
The owning changes are [KRDC Catch](https://invent.kde.org/danielcamposramos/krdc/-/commit/b3cd02d484) and [KRdp's D-Bus descriptor fix](https://invent.kde.org/danielcamposramos/krdp/-/commit/6d9c6f3dbb).

## The media stack sits on deb-multimedia

Players and tools from deb-multimedia (VLC, mpv, OBS, HandBrake) link against its FFmpeg, which has a higher epoch than Debian's.
So our stereo patches for FFmpeg and mpv go on deb-multimedia's source packages (`10:…-dmoN+stereo3dM`), with identical sonames, not on Debian's.
Offer them to deb-multimedia in the agreed order, and upstream as before.

## Proof before shipping

Use [the KDE development checks](../native-linux/references/kde-development-practices.md) when packaging changed KDE applications: fresh message extraction, installed translations, relevant QML/static analysis and required CI results.
Preserve operational comments through their consuming build steps; Lean Code qualification includes generators and extraction, not only compiler token equivalence.

In a fresh `debian:testing` container with the repository as a local source and the edition's pins:
- `tasksel --list-tasks` shows the edition's tasks;
- `dpkg-divert --list` shows Debian's descriptions moved aside;
- `apt-cache policy <program>` gives our build as the candidate and Debian's at −1;
- `apt-get -s install <task>` resolves for every task, with nothing removed.

Check that each task's package list exists (`apt-cache show`) and that no package appears in both flavours of a role.
