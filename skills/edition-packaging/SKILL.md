---
name: edition-packaging
description: >-
  How Sparky Stereo OS packages itself the Debian way: role tasks (task-sparky-stereo-<role>), stereo and 2D flavours for science and education, tasksel, blocking Debian's builds of our packages, the media stack on deb-multimedia, and how to prove a package set before it ships. Load the general sparky-stereo skill first.
---

# Packaging the edition

**Check freshness first.** Written on 2026-10-07. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

## Tasks, the Debian way

People choose what they do, not package names. The edition offers its programs as **tasks**, like Debian's `task-kde-desktop`: one metapackage per role, plus a description file so `tasksel` lists them.

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

- **Stereo and 2D flavours** (science and education, where most programs are still 2D): the stereo task holds only programs whose stereo is proven on the edition. The 2D task holds the rest and never names a program the stereo task has, so installing it never replaces a stereo build. A program moves to the stereo task when its proof lands.
- **The core** stays in a few metapackages everyone gets (desktop, hardware support, languages, system). The top `sparky-stereo` depends on the core and recommends every task.
- **Policy:** essentials and the stereo stack in `Depends`; programs in `Recommends`, so a user can remove one and keep the task. Never a versioned library name in `Depends`: Debian renames those at every transition.
- **Renaming:** the old package becomes transitional, depending on the new one, so upgrades keep working.
- **Every build of ours must be in some task.** A stereo build that no list names is never installed; this was found on 2026-10-07 for seven of our KDE and science builds.

## tasksel lists only ours

A small package ships `/usr/share/tasksel/descs/sparky-stereo.desc` (a parent task `sparky-stereo`, then one stanza per task with `Parent`, `Key`, `Section: user`). It diverts Debian's description files to a name that does not end in `.desc` (`dpkg-divert --rename` in `preinst`, removed in `postrm`), because tasksel reads only `*.desc`. Hardware-helper tasks such as isenkram's stay.

## Only our builds are candidates

The repository is pinned at 1001. A generated pin file blocks, at priority −1, the Debian and deb-multimedia builds of every package the edition's repository ships, plus Debian's `task-*` and the multimedia blend's metapackages. Generate it from the repository index, never by hand, and rebuild the apt-configuration package when the repository gains packages. This is the rule that already kept Bino ours: our build declares full side by side, and other builds would hand the compositor a picture outside the contract.

A package set waiting for a rebuild is left out of the block until the rebuild lands (see the next section).

## Each build of ours

Each is the distribution's source package plus our patch series, versioned with the suffix `+stereo3dN`, built in a fresh `debian:testing` container, and it keeps its source package, so the repository can offer `deb-src`. A 32-bit twin (Mesa and FFmpeg, for Steam and Wine) comes from the same source build as the 64-bit package: `dpkg` refuses to install the two together when a shared file such as the Debian changelog differs (`Multi-Arch: same`).

## The media stack sits on deb-multimedia

Players and tools from deb-multimedia (VLC, mpv, OBS, HandBrake) link against its FFmpeg, which has a higher epoch than Debian's. So our stereo patches for FFmpeg and mpv go on deb-multimedia's source packages (`10:…-dmoN+stereo3dM`), with identical sonames, not on Debian's. Offer them to deb-multimedia in the agreed order, and upstream as before.

## Proof before shipping

In a fresh `debian:testing` container with the repository as a local source and the edition's pins:
- `tasksel --list-tasks` shows the edition's tasks;
- `dpkg-divert --list` shows Debian's descriptions moved aside;
- `apt-cache policy <program>` gives our build as the candidate and Debian's at −1;
- `apt-get -s install <task>` resolves for every task, with nothing removed.

Check that each task's package list exists (`apt-cache show`) and that no package appears in both flavours of a role.
