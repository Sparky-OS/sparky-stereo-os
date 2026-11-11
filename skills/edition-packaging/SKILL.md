---
name: edition-packaging
description: >-
  Build, sign and ship the edition's packages: provenance, rebuilt upstream packages (+stereo3dN, i386 twins),
  dependency policy, apt pins (:any, Signed-By), conffiles, the signed repository and a publication round, DEP-11 and
  Contents, the ISO, reproducible sources (SOURCE_DATE_EPOCH), the build record and the Lean Code gate,
  installed-package proof, ten languages. Load it when a package will not install (Breaks, Multi-Arch: same, dpkg
  --auto-deconfigure), apt picks Debian's build or swaps in a dummy at dist-upgrade, two builds of one source differ,
  apt-get update exits 0 on a failed fetch, lc1 says the build record is not complete, a Qt header is missing after a
  qt6-base update, a pin leaves a binding or development package uninstallable, a systemd unit is proven only by hand
  or journalctl -u shows none of its lines, a preinst prompt stops a non-interactive install, a language probe shows
  English, a CMake consumer reports a missing imported library or include directory, or an index must be regenerated.
---

# Packaging the edition

## Working recipe

1. Record source commits, package versions, architecture, repository pins and the task that should install the result.
2. Write the control file, copyright file, script headers and changelog in [Paweł's formula](references/sparky-formula.md) with the edition's [provenance](#provenance-daniel-2026-10-02-always); rebuild upstream packages as [rebuilt packages](references/rebuilt-packages.md) says.
3. Build in isolation, inspect package contents and simulate installation/upgrade before the installed-payload checks below.
4. Return source/binary hashes, dependency resolution and runtime evidence. Separate local candidate, [repository publication](references/repository.md) and [ISO inclusion](references/iso.md).
5. A fix that upstream made on its stable branch after the release a patched package was built on is carried as upstream's own commit, as [carrying a stable-branch fix](references/carrying-upstream-stable-fixes.md) says.
6. A staged recipe that waited while a shared tool moved is redone on the new main as [rebasing a staged recipe](references/rebasing-a-staged-recipe.md) says.
7. A package that downloads licensed data during installation follows [licensed data at install time](references/licensed-data-at-install.md): inspect consent, declare the download once, keep the data off the ISO and test refusal and retry.
8. A development package must install every payload its CMake export needs; use [CMake development dependencies](references/cmake-development-dependencies.md) to check sibling packages with a clean installed consumer.

**Check freshness first.**
Written on 2026-10-07; the developer tasks and the skills package on 2026-10-16; provenance, Paweł's formula, rebuilt packages, the repository and the ISO on 2026-10-23, from rules dated 2026-10-02 to 2026-10-22; pins by architecture and the packages that are not ours on 2026-10-31; the i386 blocks, the order of pin files and the conversion to conffiles on 2026-11-01.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

## Provenance (Daniel, 2026-10-02): always

Every package of ours says who made it, the Sparky way, and [`provenance.sh`](https://github.com/Sparky-OS/sparky-stereo-os-build/blob/main/sparky-os/repo/provenance.sh) in the build tree writes it.

- `Maintainer:` is Daniel's packaging identity, `Daniel Ramos (Capitain Jack)` with his project address, as provenance.sh writes it; build scripts set `DEBFULLNAME` and `DEBEMAIL` to it, and git commits carry `Daniel Campos Ramos` with the same address. Never `root@<container>`, and never an address from a build account or an assistant's session (Daniel, 2026-10-22).
- `Original-Maintainer:` keeps whoever maintained a package we modified (Debian Qt/KDE Maintainers, NVIDIA), the convention of Debian derivatives.
- `Homepage: https://sparkylinux.org`, with no trailing slash, the form most of Paweł's packages use.
- `Bugs:` is the edition's [tracker](https://github.com/Sparky-OS/sparky-stereo-os/issues): a problem in our build never goes to the maintainer of the package we modified (Daniel, 2026-10-08).
- The copyright file keeps its holders and gains our credit (the whole `Files: debian/*` in our own packages; in a rebuilt Debian package only our own files, after Debian's paragraph: [crediting our additions](references/rebuilt-packages.md#crediting-our-additions-without-overriding-the-packagers)), with the credit in Daniel's wording of 2026-10-07: "Sparky Stereo OS, Daniel Ramos's (Capitain Jack) edition of SparkyLinux (https://sparkylinux.org, by Paweł "pavroo" Pijanowski)".
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

A pin's names carry their architectures ([apt_preferences(5)](https://manpages.debian.org/testing/apt/apt_preferences.5.en.html)):

- **A plain name means the native architecture only.** apt_preferences(5): "By default, only packages of the native architecture are matched. To match binary packages of any architecture, add the :any suffix to the package name. You can also limit matching to a specific architecture by appending the architecture name to the package name, separated by a colon character." So the generated file writes each name with the architectures the repository ships it for (`krdc:amd64 krdc:arm64`, `wine32:i386`). A plain `kio6` blocked Debian's arm64 kio6 on arm64 machines, where we ship none, and never blocked Debian's i386 builds on amd64 machines.
- **An Architecture: all name follows the architectures of its source** (`libkscreen-data:amd64` when we build libkscreen for amd64 only). apt files an Architecture: all package under the native architecture: `libkscreen-data:amd64` matches it on amd64 machines and not on arm64 ones, and a plain name matches it everywhere (measured with apt 3.3.3; the manual does not say). On the architectures where we do not build its source, our Architecture: all build is ranked at 100, under the other archive's 500, because Debian's arm64 libkf6screen8 needs Debian's libkscreen-data at its exact version and apt's solver takes only the candidate to satisfy an exact dependency (measured). A name stays plain only when its source has no architecture-specific package: then ours serves every architecture.
- **A Multi-Arch: same library in a hand-written pin is named with `:any`** (`libnvidia-egl-wayland1:any`, `libnvidia-container1:any`, `bino:any` for a block on every architecture). apt_preferences(5): "The :any suffix makes sure to select binary packages from any architecture. Without that suffix, apt implicitly assumes the :native suffix which would only select packages from the native architecture." Every architecture of a Multi-Arch: same package must be at the same version, so a pin that leaves the i386 copy to another archive lets that archive's i386 build win (NVIDIA's i386 egl-wayland at 1002, found on 31 October 2026).
- **The i386 builds of what we ship for amd64 only are blocked too** (Daniel, 2026-11-01: "why are you even asking if we have 64 bit versions?"): Debian's and deb-multimedia's i386 builds of every architecture-specific name the repository ships for amd64 and not for i386 are pinned at −1, and the generator's `I386_FROM_UPSTREAM` list is the one place for an exception a 32-bit program needs.
  Each of those i386 builds needed the other archive's Architecture: all companion at its exact version, which ours replaces, so apt listed it but could never install it beside our amd64 build (29 such packages from 17 sources, measured on 2026-10-31).
  `I386_FROM_UPSTREAM` is empty today, and Steam, wine32, dxvk-wine32 and Lutris install with nothing removed.

[`check-installable.py`](https://github.com/Sparky-OS/sparky-stereo-os-build/blob/main/sparky-os/repo/check-installable.py) in the build tree checks both sides: every package of ours, and every Debian or deb-multimedia package that depends at an exact version on an Architecture: all package whose candidate the pins decide.

The packages the repository carries that are not ours (another archive's package, only repackaged or rebuilt through Lean Code, such as deb-multimedia's own keyring) are listed by name, each with its reason, in the generator; their builds are not blocked, and ours ranks under them (400), so their archive's updates reach the edition.
The pin and source files are conffiles (Debian Policy 10.7.3), and a package that once shipped its `/etc` files as ordinary files converts them as [Paweł's formula](references/sparky-formula.md#files-under-etc-are-conffiles) says.
A person keeps pins of their own in `/etc/apt/preferences` or in a file that sorts before `sparky-stereo-only-ours` (`00-local`), never after it.
apt_preferences(5) of apt 3.3.3: "/etc/apt/preferences is parsed first, followed by the files in /etc/apt/preferences.d in lexicographic order", and "The first specific-form record matching an available package version determines the priority of the package version", so a later file never overrides the block list (measured with a `zz-local` file: Debian's krdc stayed at −1).
Lifting a block is not enough on its own: our build stays the candidate at 1001, so a person who wants another archive's build writes two records, one ranking that build and one ranking ours under it; the package's README shows both.

A package set waiting for a rebuild is left out of the block until the rebuild lands (see the next section).

A package of another archive that ships our files under another name (deb-multimedia's `libmlt7-data` owned our MLT data) is not caught by a block by name: find it from the two Contents files, pin it out and settle the machines that have it, as [a package of another archive that ships our files](references/shadowed-by-another-archive.md) says. A pin that leaves a person's other package of that archive uninstallable (MLT's Perl and Ruby bindings) is answered by building the function ourselves under names that clash with nobody, the same page's second half.

## The GPU vendors' repositories: compute updates, the display driver stays ours

NVIDIA's and AMD's repositories carry their display drivers beside CUDA and ROCm, so the edition pins them: compute keeps updating, and the display driver stays ours, with [HDMI®](https://www.hdmi.org/resource/brand) 3D.
The packages, the pin files and how to prove a change are in [the repository](references/repository.md#the-gpu-vendors-repositories-compute-updates-the-display-driver-stays-ours).

## Each build of ours

Each is the distribution's source package plus our patch series, versioned with the suffix `+stereo3dN`, built in a fresh `debian:testing` container, and it keeps its source package, so the repository can offer `deb-src`.
A 32-bit twin (Mesa and FFmpeg, for Steam and Wine) comes from the same source build as the 64-bit package: `dpkg` refuses to install the two together when a shared file such as the Debian changelog differs (`Multi-Arch: same`).
The rest, Mesa's acceptance and the KDE CI run before a push to invent.kde.org included, is in [rebuilt packages](references/rebuilt-packages.md).

**Lean Code release requirement (Daniel, 2026-10-18):** every package and ISO we publish passes the edition's Lean Code pipeline. Finish provenance and notices before projecting the disposable package tree; calculate checksums from its lean payload, then assemble and sign. The versioned `lc1` control marker binds the coverage manifest and lets clients skip rendering. Publish exact HR documentation companions beside the packages, outside the ISO's default package set. The publisher rejects missing or stale evidence; never add the marker by hand or change a previously published version in place. See the [lc package contract](../../docs/lean-code-packages.md). On 2026-10-23 every package in the published repository carries the lc1 mark (690 amd64, 122 i386, 2 arm64 and 181 architecture-independent entries, 141 of them HR companions), and the client was dpkg-stereo 0.1.16 (0.1.28 on 2026-11-06). Since 2026-10-22 the publisher also runs the link and start gate (`lean.release check-link`) on every new package. Release ISOs are packed with `LEAN=1` and sealed with an lc1 attestation; the final ISO's boot, installation and hardware tests remain separate.

## Receiver packages must prove their installed interface

A changed receiver (KRDC Catch, KRdp; checked 2026-10-16) is proved after a full upgrade from the published packages, with eye-swap and frozen-source controls, as [rebuilt packages](references/rebuilt-packages.md#receiver-packages-must-prove-their-installed-interface) says.

## The media stack sits on deb-multimedia

Players and tools from deb-multimedia (VLC, mpv, OBS, HandBrake) link against its FFmpeg, which has a higher epoch than Debian's.
So our stereo patches for FFmpeg and mpv go on deb-multimedia's source packages (`10:…-dmoN+stereo3dM`), with identical sonames, not on Debian's.
Offer them to deb-multimedia in the agreed order, and upstream as before.
The recipe for adding a fix to that FFmpeg, with the traps met: [rebuilding deb-multimedia's FFmpeg as ours](references/rebuilt-ffmpeg.md).
A test image that installs from our repository needs deb-multimedia's source and our pin, as [the repository](references/repository.md#the-repository-sits-on-deb-multimedia) says.

## A publication round

A round runs from a frozen worktree of the build repository, passes the pre-round checks (the whole lean suite, reproducible sources, wiring; in containers), and proves the upgrade on the edition's own dpkg, judged on apt's `Inst` and `Remv` lines.
The recipe, what the proof fails on, how to read a failed round, a package whose receipts bind another package's files (pin it exactly, gate the round) and the traps already met: [publication round](references/publication-round.md).

## The repository and the ISO

The development and published repositories, the key and a publication's order: [the repository](references/repository.md).
Packing the image, in containers or from the development VM: [the ISO](references/iso.md).

## Names and sources are checked before they are written down

OpenSSF's [Security-Focused Guide for AI Code Assistant Instructions](https://best.openssf.org/Security-Focused-Guide-for-AI-Code-Assistant-Instructions) (Best Practices and AI/ML Working Groups, 2025-08-01), "Addressing Software Supply Chain Security", asks that an assistant not add "dependencies that may be malicious or hallucinated", and that it show how to verify what it adds.
The packager's side of that is short and applies to a person as much as to an assistant.
These are habits that orient the work; no tool is refused because of them.

- **Every package name exists in the archive before it enters a file.**
  The `Depends`, `Recommends`, `Suggests` and `Build-Depends` fields, a task's list, a pin file and a Dockerfile are checked with `apt-cache policy NAME` in the build container, which must show a candidate from the origin you expect.
  A name that comes from an assistant's memory, a forum post or an old recipe is checked like any other, and an assistant's list of names it is unsure of is a place to start the lookup, not the lookup.
- **An upstream tarball is verified, not only downloaded.**
  Debian Policy 4.11 (`debian/watch`) recommends, when upstream signs releases, the `pgpsigurlmangle` option and the signing keys in `debian/upstream/signing-key.asc`, so that `uscan` checks the signature; Lintian's `debian-watch-does-not-check-openpgp-signature` is the reminder.
  Where upstream signs nothing, fetch from the project's own release page and record the file's SHA-256 in the recipe's notes.
- **Container bases are pulled by digest and the digest is recorded.**
  The guide, "Container and Deployment Considerations": "pin image versions using immutable digests (e.g., SHA256 hashes) instead of mutable tags".
  A `debian:testing` tag changes under a lane; on 2026-10-13 it became an i386 image and a bench installed i386 packages without saying so.
- **The task check covers every name,** not only the tasks: the list of what the work added or changed goes in the handoff, with its source and version, as [`ai-partners`](../ai-partners/SKILL.md#handoff) asks.

## Workflows and a repository's own safety, measured with Scorecard

[OpenSSF Scorecard](https://github.com/ossf/scorecard) scores a repository from 0 to 10 on a list of checks, each with its reason, and the instructions guide asks the same of generated pipelines: "ensure secrets are stored securely ... and not hard-coded in the workflow files" and "lock the version to specific SHA" ("Operational Security").
In a repository of ours that has a GitHub Actions workflow:

- the workflow starts with `permissions: contents: read`, and a job asks for more only for the step that needs it;
- each `uses:` line names a commit, with the release tag in a comment (`actions/checkout@<40-hex commit> # v5`), and a `.github/dependabot.yml` entry for `github-actions` keeps the commits current;
- no secret is written in the file; a workflow reads it from the repository's secrets.

The organisation's `SECURITY.md` lives in its `.github` repository and applies to every repository without one of its own; Scorecard's Security-Policy check looks there too.
To measure a repository, run the pinned container from the documented registry, with the token read inside the command and never printed:

```sh
GITHUB_AUTH_TOKEN="$(gh auth token)" docker run --rm -e GITHUB_AUTH_TOKEN \
  ghcr.io/ossf/scorecard@sha256:c0a21a1c33a2d8819937d0a8a62e6f4189c800639abd9f0bfbe61c90c71fae90 \
  --repo=github.com/OWNER/NAME --format=json --show-details
```

That digest is v5.6.0 (the registry `gcr.io/openssf/scorecard`, which older instructions name, answered "requires billing" on 2026-11-04).
A score is a measurement of the repository, not a gate: some checks (required reviews, signed releases, branch protection) change how people work, and those are Daniel's to switch on.
On a fork, Scorecard mostly measures upstream's code and settings, so a fork's low score is not ours to fix.

## Proof before shipping

For a QML application that fails before opening its window, check [required QML modules and selected styles](references/required-qml-modules.md).
Install the player without recommendations in the proof; a required QML module must arrive through `Depends`.

Use [the KDE development checks](../native-linux/references/kde-development-practices.md) when packaging changed KDE applications: fresh message extraction, installed translations, relevant QML/static analysis and required CI results.
Preserve operational comments through their consuming build steps; Lean Code qualification includes generators and extraction, not only compiler token equivalence.

In a fresh `debian:testing` container with the repository as a local source and the edition's pins:
- `tasksel --list-tasks` shows the edition's tasks;
- `dpkg-divert --list` shows Debian's descriptions moved aside;
- `apt-cache policy <program>` gives our build as the candidate and Debian's at −1;
- `apt-get -s install <task>` resolves for every task, with nothing removed.

Check that each task's package list exists (`apt-cache show`) and that no package appears in both flavours of a role.

## An upstream program from its release tag

A program with no Debian package (DisplayXR's OpenXR runtime, ORDER 58) is built from its release tag, with every source its build would download carried as a source component and its own packaging script reused where it can stage a finished build.
A part Debian cannot build (a .NET program) is carried from upstream's release, checked by SHA-256, in a package of its own; `debian/copyright` comes from the tree's SPDX tags (`reuse lint --json`, [`scripts/reuse2dep5.py`](scripts/reuse2dep5.py)) plus the files REUSE cannot see.
An OpenXR runtime joins the `openxr1-active-runtime` alternatives group Debian's Monado uses, never writing the loader's link itself; the edition builds its simulated display with one output, full side by side.
The recipe, the coexistence rules with their specification clauses, the proof and the traps: [packaging an OpenXR runtime](references/openxr-runtime-package.md).

## Lessons from the lanes, October to November 2026

[Adding a required language to the whole edition](references/adding-a-required-language.md): the audit, where language lists hide, the generator and test traps.

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (114 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).

HDMI®, HDMI® High-Definition Multimedia Interface and the HDMI® Logo are trademarks or registered trademarks of HDMI Licensing Administrator, Inc.
