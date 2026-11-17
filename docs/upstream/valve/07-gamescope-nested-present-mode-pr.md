# Draft 07: gamescope pull request, the nested output's present mode

Status: **POSTED 2026-09-26 as https://github.com/ValveSoftware/gamescope/pull/2438** (approved by Daniel; posted verbatim except `#8297 in Source-1-Games` written as `ValveSoftware/Source-1-Games#8297`, so GitHub links the right repository).
Disclosure line ("AI partners were leveraged in the production of this work.") appended to the body on 2026-09-26 at Daniel's request, per `docs/ai-contribution-policies.md` (gamescope: disclosure note in the body).
Target: https://github.com/ValveSoftware/gamescope/compare (from a fork of ValveSoftware/gamescope, branch `nested-present-mode`) Commit: `a552e8e` in `/K3D/GitHub/gamescope`, on upstream master `ad2763d`; the same change runs here as `gamescope-3dtv` (3.16.24, `tools/vr-stereo-spectator/gamescope/`).
Post this before draft 06, which links to it.

---

**Title:** Let the nested output's present mode be chosen (GAMESCOPE_NESTED_PRESENT_MODE)

@misyltoad, a gift from the 3D side, since #8297 in Source-1-Games already has you in copy.

The nested output (SDL and Wayland backends) always presents with FIFO.
With the game on vsync inside gamescope, that is a second queue behind the first.

**What it did:** frames reached the screen in 4 ms / 33 ms pairs, against 15.6 to 17.7 ms (5th to 95th percentile) without gamescope.
On a stereo 3D TV, and in red/cyan anaglyph, fast camera turns then read as walls moving in depth.
Measured with a per-frame log of Half-Life 2's view angles, VR mode driving a 3D TV (RTX 3060, KDE Plasma on Wayland, gamescope in an SDL window on X11).

**The change:** `GAMESCOPE_NESTED_PRESENT_MODE=mailbox` or `immediate` picks that mode when the surface offers it, and logs the mode in use.
Unset, or not offered, it stays FIFO, so nothing changes by default.

**Result:** with the game free-running and the nested output on IMMEDIATE, the 95th percentile frame time went to 4.5 ms and the depth swim was gone, in side by side and in anaglyph.
NVIDIA offers no MAILBOX for this window, so the fallback path is exercised too.
IMMEDIATE did not tear, since the host compositor still composites the window.

If a command-line option suits the project better than a variable, I will change it.

---

Notes for Daniel (not for posting):
- Fork `danielcamposramos/gamescope` created and branch `nested-present-mode` (`a552e8e`) pushed, 2026-09-26. Open the pull request against ValveSoftware/gamescope master from it.
- Built on master `ad2763d` with the patch (debian:testing container, 365/365 targets, no warning in `rendervulkan.cpp`), and built and run on 3.16.24 (runs p16b, p16c, p18, p19).
- Disclosure: once, at the end, if you want it (AI-assisted: Claude).
