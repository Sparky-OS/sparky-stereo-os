# Proofs

Each piece of Sparky Stereo OS is shown working before it is called done.
These pages keep the proof for everyone to check: what changed, the test that would fail without it, the numbers, and the pictures.

## How to look at the pictures

Every proof picture comes as a pair:
- the **anaglyph** (`-anaglyph.jpg`), red/cyan, to see with paper 3D glasses in any browser;
- the **MPO** (`.mpo`), the stereo photo format, to open on a 3D TV, in a stereo viewer, or in Dolphin on Sparky Stereo OS.

The full evidence of each test (captures of both eyes, logs, the measured tables) is on [repo.sparkyos.org/proofs](https://repo.sparkyos.org/proofs/).

## The proofs

- [Lean Code on a 2016 laptop: lean, original, lean again](lean-code-a10-aba.md), 3 November 2026: builds against the kernel headers 6 to 9 % faster, Plasma's shell, System Settings and Dolphin 3 to 6 % smaller, boot the same; Discover's difference traced to its catalog cache, not to Lean Code; a year of heavy use projected.
- [Dolphin shows stereo files in 3D](dolphin-stereo-previews.md), 14 October 2026: thumbnails, tooltips, the information panel and stereo icons; passed on Daniel's own 3D TV.
- [Waterfox: stereo video marks and WebXR on a flat 3D screen](waterfox-stereo-m3.md), 14 October 2026: 30 of 32 test cases, from 17.
