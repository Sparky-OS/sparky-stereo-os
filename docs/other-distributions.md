# Sparky Stereo OS and other distributions

**Short answer:** we do not package Sparky Stereo OS for other distributions, and every fix it needs is open for any distribution to adopt.

## Why we do not package it for other distributions

**Stereo 3D is not one app here.**
It is the whole path from a program to the screen: the kernel and its graphics drivers, Mesa, the desktop (KWin and its display settings), and each program that shows 3D.
Shipping all that on top of another distribution means replacing its kernel and graphics stack, and then it is no longer that distribution.

**The part that could travel alone is small.**
A desktop limited to red-cyan anaglyph could be installed elsewhere.
3D TVs, 3D monitors and projectors need the rest, so it would be a lesser copy, and we would rather put that effort into the real thing.

**The goal is upstream.**
These features belong in KDE, the kernel, Mesa, FFmpeg and each program, where every distribution gets them the normal way.
A copy that never goes upstream splits the work, and the people using it never learn where it came from or how to help.
What helps most is people asking their own projects for it.

**Who it is for now.**
Engineers, scientists and content creators first.
Then players, video lovers and hi-fi audio listeners, as the features land.

**To try it without installing:** when the edition's image is out, it runs live from a USB stick.

## For distribution maintainers: adopt our fixes

Everything is free software under each project's own licence, and it is public:
- **The forks:** most projects we change have a fork in the [Sparky-OS organisation](https://github.com/Sparky-OS), with our changes as commits on top of upstream, in its `stereo3d` branch, and a section at the top of its README saying where it comes from and what it adds. KDE's are also on [invent.kde.org](https://invent.kde.org/danielcamposramos).
- **What each change does:** [Programs](programs.md), one entry per program, with the finding behind it.
- **KDE changes and their CI results:** [Our branches on KDE's GitLab](kde-branches.md).
- **Already merged upstream:** [Merged outside Sparky Stereo](upstream-merges.md). These arrive with each project's own releases.
- **The rule every change follows:** [How it works](how-it-works.md) and [Stereo labor division](stereo-labor-division.md), tied to the specifications.
- **Instructions for people and AI assistants:** [Skills](../skills/README.md).

Two requests if you adopt a change: keep its credit, and help it reach upstream.
Questions, or a plan to adopt something: open an [issue](https://github.com/Sparky-OS/sparky-stereo-os/issues), and we will gladly help.
