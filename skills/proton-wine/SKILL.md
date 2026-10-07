---
name: proton-wine
description: How Windows games and programs running through Wine, Proton, DXVK and gamescope reach a 3D display on Sparky Stereo OS: where their stereo comes from (an injector such as wiz3D, a VR mode, or the game's own side-by-side output), how it is handed to the desktop, and what is planned for Lutris. Load the general sparky-stereo skill first.
---

# Windows programs through Wine and Proton

**Check freshness first.** Written on 2026-10-07; much of this layer is planned, and each item says whether it is done. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

## The chain

A Windows game's Direct3D calls become Vulkan through DXVK (Direct3D 9 to 11) or VKD3D-Proton (Direct3D 12), and Vulkan reaches the GPU through Mesa, or through NVIDIA's driver with the edition's Vulkan layer. Stereo can enter at three places:

1. **An injector draws two cameras inside the game.** wiz3D does this for DirectX 9 games, the vendor-neutral way iZ3D did once: the camera moves at the API, one world and two cameras ([`stereo-two-cameras`](../stereo-two-cameras/SKILL.md)). Its Linux build is in review upstream ([effcol/wiz3D #33](https://github.com/effcol/wiz3D/pull/33)); our Proton work is on [danielcamposramos/wiz3D `stereo3d-proton`](https://github.com/danielcamposramos/wiz3D/tree/stereo3d-proton).
2. **The game has a VR mode.** Its two eyes go to a 3D display instead of a headset: load [`vr-to-3d`](../vr-to-3d/SKILL.md).
3. **The game draws side by side itself.** Some games and players have a side-by-side option. The window is declared as full side by side, and the game's own output menu is no longer the place where the format is chosen.

## gamescope

gamescope is Valve's micro-compositor. Running a game inside it, nested in the desktop, raced frames between the game and the nested output, and stereo made the race visible; letting the nested output's present mode be chosen ends it ([ValveSoftware/gamescope #2438](https://github.com/ValveSoftware/gamescope/pull/2438), in review). SteamVR on a 3D television runs inside gamescope (see [`vr-to-3d`](../vr-to-3d/SKILL.md)). In the edition the desktop draws the final 3D output; a game or gamescope packs the eyes for a screen only on systems without Stereo KWin.

## Done and planned

- **Done: 32-bit (i386) builds** of the edition's Mesa and FFmpeg, at the same versions as the 64-bit ones, so the 32-bit programs of Steam and Wine load the same stereo Mesa ([`edition-packaging`](../edition-packaging/SKILL.md)).
- **Planned: the stereo Lutris build:** a "Stereo 3D" switch, on by default, and a per-game "outputs side by side itself" checkbox; wiz3D as a clean package; the edition's own Wine and DXVK packages.
- **Planned: proof of each game family** on the capture rig, as below.

## Traps to check first

- **Does the game reach the edition's Mesa?** Steam's runtime, Flatpak and some launchers can load their own libraries. Check which Vulkan and OpenGL drivers the game actually loaded before testing stereo.
- **Never let a game pick its own 3D output format.** The game delivers full side by side; Stereo KWin's outputs decide the screen.

## Proof

As in the general skill: a known scene, both eyes captured, the left eye's view correct, one declaration, the game's interface (menus, HUD) where it belongs (see the formula's 2D layer rules), and the game with stereo off unchanged.
