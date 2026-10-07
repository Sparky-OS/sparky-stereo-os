---
name: vr-to-3d
description: How a game or engine with a VR mode is shown on a 3D television, projector or monitor instead of a headset on Sparky Stereo OS, and how a headset player's view is mirrored in stereo for the room (the Stereo Spectator): the formula learned on Half-Life 2, the tools, and the rules. Load the general sparky-stereo skill first.
---

# From a VR engine to a 3D display

**Check freshness first.** Written on 2026-10-07. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

## The formula

A game with a VR mode already renders two eyes. A 3D display can show them directly. What stands in the way is everything the VR mode does *for a headset*. [The formula](../../docs/formula.md), learned on Half-Life 2's own VR interface, lists what changes, and most VR games share its structure:

1. **The eyes go to a window,** not a headset: no lens distortion, each eye at the display's size.
2. **The game drives the view,** not a head tracker: mouse and controller turn the camera as in the 2D game.
3. **Composition:** each eye renders into its target, and the targets are placed into one full side-by-side frame.
4. **The 2D layer** (HUD and menus) sits on the screen plane, not on a floating panel.
5. **The crosshair** is 2D, centred, identical in both eyes.
6. **The weapon and its effects** are drawn for both eyes from the same cameras.
7. **Input:** one window, two eyes; the cursor maps to the interface, not to window pixels.
8. **Settings** are applied on entry and restored on exit.

## The tools, public

[sony-bravia-linux/tools/vr-stereo-spectator](https://github.com/danielcamposramos/sony-bravia-linux/tree/main/tools/vr-stereo-spectator):

- `sourcevr/`: a replacement VR module for Half-Life 2 that drives a 3D display, and `SPECTATOR.md`, the spectator design (the 2D game with a second camera, so observers and SourceTV get the stereo view too).
- `steamvr/`: a SteamVR display driver for a 3D television.
- `gamescope/`: `gamescope-3dtv`, and the nested present-mode patch (upstream as [gamescope #2438](https://github.com/ValveSoftware/gamescope/pull/2438)).
- `anaglyph/`: an anaglyph shader for gamescope's ReShade, for screens without a 3D mode.

The requests to Valve, with what would make the path clean: [Source-1-Games #8297](https://github.com/ValveSoftware/Source-1-Games/issues/8297) and [SteamVR-for-Linux #961](https://github.com/ValveSoftware/SteamVR-for-Linux/issues/961). Other open routes: [VRto3D](https://github.com/oneup03/VRto3D), an OpenVR driver for 3D displays, and the universal VR mods per engine listed in awesome-stereoscopy.

## Rules learned

- **SteamVR on a television runs inside gamescope,** never in a plain desktop window.
- **The Stereo Spectator:** while someone plays in a headset, the room sees the same two eyes in stereo on the television or projector, instead of a flat mirror. It is the same composition, sent to the desktop instead of only to the headset.
- **A headset's cameras, too.** Passthrough headsets carry two cameras about an eye's distance apart, so the room can also watch what the cameras recorded (spatial photos and video) and what they see live (a stereo camera feed streamed to the desktop). Apple Vision Pro and Pico 4 Ultra record stereo natively, Galaxy XR with Samsung's software, Quest 3 and 3S through apps on Meta's Passthrough Camera API, Steam Frame with a colour-camera add-on ([immerNews, 2026-09-03](https://immernews.com/spatial-cameras-in-vr-from-quest-3-to-steam-frame-arcturus-with-project-phoenix-on-the-horizon/)). All of it ends as full side by side in Stereo KWin; only the input formats differ, and each device's real files are tested before the edition claims support ([`stereo-video`](../stereo-video/SKILL.md), [`stereo-pictures`](../stereo-pictures/SKILL.md)).
- **In the edition** the desktop draws the final output; the game hands over full side by side.
- **Blur and other effects that keep state between frames** must be per eye, or off: Half-Life 2's motion blur shared its previous view between the eyes and broke.

## Proof

Angles logged per eye against the expected separation, both eyes captured in play, the HUD and crosshair identical in both eyes, settings restored after exit, and a run on the real display at the very end.
