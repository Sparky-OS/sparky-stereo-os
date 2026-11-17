# Draft 06: #8297 update, three display modes and the gamescope frame race (comment)

Status: **POSTED 2026-09-26 as https://github.com/ValveSoftware/Source-1-Games/issues/8297#issuecomment-5842650764** (approved by Daniel; posted verbatim with the placeholder filled in as `ValveSoftware/gamescope#2438`).
Target: https://github.com/ValveSoftware/Source-1-Games/issues/8297 (comment) Evidence: angle logs `svrtv-angles.tsv` of runs p13-p19 under `/K3D/temp/hl2-bench/` (local); gamescope logs of p16b, p16c, p18; `tools/vr-stereo-spectator/gamescope/`.
No new pings: the issue already cc's misyltoad.

---

We found and fixed the gamescope frame race behind the depth swim, for 3D TVs and for anaglyph over gamescope: <link to the gamescope pull request>

**Discovery.**
In fast mouse turns, static walls moved in depth through gamescope, in anaglyph and in side by side alike.
Native side by side stayed solid.
A per-frame log of the view angles showed frames reaching the screen in 4 ms / 33 ms pairs through gamescope, against 15.6 to 17.7 ms native.
Two queues in a row: the game's vsync, then gamescope's nested output, hard-coded to FIFO.

**Solution.**
The game renders freely inside gamescope, and gamescope's nested output presents with IMMEDIATE (the pull request adds `GAMESCOPE_NESTED_PRESENT_MODE`; the default stays FIFO).
95th percentile frame time 4.5 ms in anaglyph, and side by side through gamescope now looks like native.

---

Notes for Daniel (not for posting):
- Numbers: p13 native p5/p95 15.56/17.68 ms; p14 gamescope FIFO 4.03/33.66 ms; p16a (free, stock gamescope) p95 15.80 ms, 28% of frames over 1.5x median; p16c (free, IMMEDIATE) p95 5.67 ms, 8%; p18 anaglyph modern p95 4.52 ms, 2%. p16b asked for MAILBOX and got FIFO (gamescope log: "not offered by the surface").
- "PERFECTION!" is your line from p18; keep it or drop it, your call.
- p19 (CRT) passed too ("also a perfect run"). The three display modes and the in-game offer go in the SDK pull requests, not here.
