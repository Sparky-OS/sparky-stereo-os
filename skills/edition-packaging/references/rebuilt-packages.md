# Rebuilt and patched upstream packages

**For maintainers of the stereo stack's packages:** the kernel, Mesa, NVIDIA's open modules, KWin and KScreen, PipeWire plugins and every other Debian or deb-multimedia package the edition rebuilds.

## Build

- Build in throwaway `debian:testing` containers, never by changing the host: `kernel/build-deb.sh`, `sparky-os/packages/*/build.sh` and the KWin and KScreen build scripts in [the build tree](https://github.com/Sparky-OS/sparky-stereo-os-build).
  Limit the build's threads so the machine keeps a margin for its own work.
- **Build in a freshly updated `debian:testing` (2026-10-04).**
  Testing moved to Qt 6.11.2 while an older build image still had 6.10.2, and KDE packages pin Qt's private ABI exactly, so the stale image produced packages that did not install on a fresh system.
  Record the Qt and KDE Frameworks versions of every build.
- **Debian's packaging stays as Debian has it (2026-10-04),** after a KWin build that switched its tests on.
  Add only our patch, our changelog entry and the dependencies our change needs.
  Debian builds KWin with `-DBUILD_TESTING=OFF` and its build-time tests disabled, since they need DRM devices; our tests run in our own harness during review, never inside the package build.
- Every architecture comes from the one source package: `sparky-os/repo/build-from-dsc.sh` builds each architecture from the published `.dsc`, as [the skill](../SKILL.md#each-build-of-ours) says.
- `DEBIAN_FRONTEND=noninteractive apt-get -y` everywhere: the host, containers, the VM and scripts.
- Build trees go on a persistent disk, never under `/tmp`, which may be wiped at boot; `sync` after a build worth keeping.
- Root commands on a person's machine run only on that person's go. Tests never change a television's mode, and anything that will open on a television is announced first.

## Versions and replacements

- The version is the Debian or upstream version plus our suffix: `+stereo3dN` for stereo changes, `+aacN` for the AAC codec of PipeWire's Bluetooth plugin (`1.6.9-2+aac2`).
  The repository's pin makes ours win.
- A package that replaces one that other packages depend on exactly takes its own name and `Provides:` the original at its exact version.
  `nvidia-kernel-open-dkms-stereo3d` provides `nvidia-kernel-open-dkms (= ${nvidia:Version})`, for example `nvidia-kernel-open-dkms (= 615.71.09-2)`, with `Conflicts:` and `Replaces:` of the original, and the original's versioned `Breaks` and `Replaces` kept.

## Patches and provenance

- Patches live in our forks, on their `stereo3d` branches, and as files beside the build script.
  GitHub forks live in the [Sparky-OS organisation](https://github.com/Sparky-OS), with the distribution branch as the default branch (Daniel, 2026-10-09); KDE forks live on [invent.kde.org](https://invent.kde.org/danielcamposramos), listed with their CI in [our KDE branches](../../../docs/kde-branches.md).
- AI assistance goes in each commit as an `Assisted-by:` trailer.
  An assistant never adds Daniel's `Signed-off-by`: he signs what he sends.
- Keep Debian's copyright file and append our `Files: debian/*` credit; `provenance.sh` does it (see [provenance](../SKILL.md#provenance-daniel-2026-10-02-always)).
- Prove each build before shipping: compile against our kernel where the package builds modules, compare the package trees with the previous build, and simulate the installation with apt.

## Receiver packages must prove their installed interface

Checked 2026-10-16 with KRDC Catch and KRdp.
When a reviewed change targets development master, backport it to the distribution release and retain the release's existing plugins and behaviour.
Build the translated catalogs as distribution patches, with test-only capture and mutation hooks disabled in the shipping executable.
After a full upgrade from the published packages, compare installed payloads with the package archives and run the visible connection action in an isolated session.
Capture only the synthetic receiver display and check eye identity, per-eye fit, changing source timecodes and reconnect.
Swap the synthetic source eyes and freeze its animation to prove that the same checker rejects reversed and stale pictures without enabling hooks in the shipped app.
For certificate rejection, verify that the connection reached TLS and failed pin validation; a server that never listened is not a passing control.
The owning changes are [KRDC Catch](https://invent.kde.org/danielcamposramos/krdc/-/commit/b3cd02d484) and [KRdp's D-Bus descriptor fix](https://invent.kde.org/danielcamposramos/krdp/-/commit/6d9c6f3dbb).

## Mesa acceptance (2026-10-13)

Mesa `+stereo3d9` shipped with no EGL configurations on the surfaceless and device platforms, on every driver: Waterfox's media process could not upload video and KWin's surfaceless tests failed.
Before a Mesa build ships, check from the installed packages, on the AMD render node and on llvmpipe, beside Debian's build of the same version as the control:

- `eglinfo -B -p surfaceless` names a renderer. `EGL_NOT_INITIALIZED` ("No DRI config supports native format") fails the build.
- `eglinfo -B` lists every EGL device under "Device platform" (`EGL_EXT_platform_device`), each with a renderer.
- KWin's `testStereoDownscale` passes with `EGL_PLATFORM=surfaceless`; it initialises EGL from `EGL_DEFAULT_DISPLAY`.
- The stereo checks pass under Stereo KWin, from a capture of both eyes (left red, right green, one declaration; [the proof rig](../../stereo-proof-rig/SKILL.md)): EGL two-view windows on Wayland and X11, the GLX quad-buffer window, the two-layer Vulkan swapchain through the stereo layer, and the mono GLX window, which must stay mono.
- Mesa's own tests in the build pass, for amd64 and for the i386 twin, each against the previous build's totals.

Platforms that offer only pbuffers are the ones a window-only change breaks: check them whenever EGL's configuration code changes.

## Before any push to an invent.kde.org fork

Run `tools/kde-ci-local/kde-ci-local <tree> [--ci-name <branch as pushed>]` from the build tree first, and push only when it ends green.
It runs the pipeline's own jobs (reuse, clang-format, xml, yaml, qml-lint, the SUSE builds with their tests on the Qt versions KDE's pipeline names, and a FreeBSD proxy) in KDE's own images, with the dependencies KDE's registry gives them.
A fork cannot make KDE's CI build a dependency from another fork.
So every stereo part that needs our change in a dependency (MpvQt, libkscreen, plasma-wayland-protocols, QtMultimedia, stereo-declare) is detected at configure time, and the program builds without it.
`.kde-ci.yml` names its dependency branches (`Plasma/6.7`, `@latest-kf6`), because `@same` finds none on an unprotected fork branch.
How the CI works, its current jobs and the routine's limits: [KDE-CI.md](https://github.com/Sparky-OS/sparky-stereo-os-build/blob/main/tools/kde-ci-local/KDE-CI.md).
