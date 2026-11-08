---
metadata:
  requires-packages: monado-service | steam-installer
name: vr-to-3d
description: >-
  Adapt a VR engine's eye images for a flat stereo display and spectator viewing: the formula (eyes to a window, the
  game drives the view, composition, the 2D layer, the crosshair, the weapon and its effects), SteamVR on a television
  inside gamescope, the Stereo Spectator, a headset's cameras kept, blur and effects that keep state between frames,
  Android XR as a source, an OpenXR runtime (DisplayXR) declaring its window full side by side. Load it when a VR game
  should play on a 3D TV, the HUD or crosshair doubles, effects smear across the eyes, a spectator view must keep the
  headset's camera, or any OpenXR app should show in 3D on Stereo KWin.
---

# From a VR engine to a 3D display

## Working recipe

1. Choose flat-display play or spectator mirroring; identify eye images, poses/FOV, HUD and tracking ownership.
2. For play, apply the formula below. For spectators, retain the headset view relationship and test both eyes reaching one declared desktop surface.
3. Return pose/image evidence, input/restoration checks and device limits. A WebXR session-support result alone does not prove or disprove stereo image presentation.

**Check freshness first.**
Written on 2026-10-07; the established solutions linked on 2026-11-02; an OpenXR runtime as a source on 2026-11-07.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

## The formula

A game with a VR mode already renders two eyes.
A 3D display can show them directly.
What stands in the way is everything the VR mode does *for a headset*.
[The formula](../../docs/formula.md), learned on Half-Life 2's own VR interface, lists what changes, and most VR games share its structure:

1. **The eyes go to a window,** not a headset: no lens distortion, each eye at the render resolution the person chose (the display's size by default), handed over as it is; Stereo KWin resizes it once.
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
  **Before any change to the module, read its [established solutions](https://github.com/danielcamposramos/sony-bravia-linux/blob/main/tools/vr-stereo-spectator/sourcevr/README.md#established-solutions-check-before-every-change)** (Daniel, 2026-09-26): each was found by testing on the television and kept on purpose, from the interface laid out at the 2D size to nothing resized for a format.
  A change that touches one says so and keeps its purpose; one "simplified" away brought its old bug back.
- `steamvr/`: a SteamVR display driver for a 3D television.
- `gamescope/`: `gamescope-3dtv`, and the nested present-mode patch (upstream as [gamescope #2438](https://github.com/ValveSoftware/gamescope/pull/2438), in review).
- `anaglyph/`: an anaglyph shader for gamescope's ReShade, for screens without a 3D mode.

The requests to Valve, with what would make the path clean: [Source-1-Games #8297](https://github.com/ValveSoftware/Source-1-Games/issues/8297) and [SteamVR-for-Linux #961](https://github.com/ValveSoftware/SteamVR-for-Linux/issues/961).
Other open routes: [VRto3D](https://github.com/oneup03/VRto3D), an OpenVR driver for 3D displays, and the universal VR mods per engine listed in awesome-stereoscopy.

## Rules learned

- **SteamVR on a television runs inside gamescope,** never in a plain desktop window.
- **The Stereo Spectator:** while someone plays in a headset, the room sees the same two eyes in stereo on any of the registered outputs, instead of a flat mirror. It is the same composition, sent to the desktop instead of only to the headset.
- **A headset's cameras, too.** Passthrough headsets carry two cameras about an eye's distance apart, so the room can also watch what the cameras recorded (spatial photos and video) and what they see live (a stereo camera feed streamed to the desktop). Apple Vision Pro and Pico 4 Ultra record stereo natively, Galaxy XR with Samsung's software, Quest 3 and 3S through apps on Meta's Passthrough Camera API, Steam Frame with a colour-camera add-on ([immerNews, 2026-09-03](https://immernews.com/spatial-cameras-in-vr-from-quest-3-to-steam-frame-arcturus-with-project-phoenix-on-the-horizon/)). All of it ends as full side by side in Stereo KWin; only the input formats differ, and each device's real files are tested before the edition claims support ([`stereo-video`](../stereo-video/SKILL.md), [`stereo-pictures`](../stereo-pictures/SKILL.md)).
- **In the edition** the desktop draws the final output; the game hands over full side by side.
- **Blur and other effects that keep state between frames** must be per eye, or off: Half-Life 2's motion blur shared its previous view between the eyes and broke.

## Android XR as a source (checked 2026-10-07)

[Android XR supports OpenXR 1.1](https://developer.android.com/develop/xr/openxr).
Its immersive apps submit [per-view poses, fields of view and images](https://registry.khronos.org/OpenXR/specs/1.1/man/html/XrCompositionLayerProjectionView.html) through that runtime.
A desktop adapter must preserve the view information before applying the camera rules above.
For recorded spatial video, [Jetpack XR documents side-by-side and MV-HEVC playback](https://developer.android.com/develop/xr/jetpack-xr-sdk/add-spatial-video).
Decode the two views, resolve their eye order, and deliver full side by side to Stereo KWin.
An XR API or a headset's ordinary mirror is not proof that both eyes reach a desktop surface; the Android-to-KWin bridge still needs the capture proof below.

## An OpenXR runtime as a stereo source (checked 2026-11-07)

Any OpenXR app reaches Stereo KWin's outputs when the runtime presents its two views as one window declared full side by side.
On DisplayXR: the display processor says its output is a stereo pair (`xrt_dp_scanout_caps::stereo_layout` = 3, HDMI 1.4b's Side-by-Side (Full), sim_display's `SIM_DISPLAY_OUTPUT=sbs_full`); the runtime then presents a buffer twice the window's width, each view at the window's resolution, and declares the app's native Wayland surface once (`kde_stereo_content_v1` value 3, bound at version 2 so the window stays one view wide).
A plain OpenXR app runs in the runtime's own X11 window: the runtime sets `_KDE_NET_WM_STEREO_CONTENT` = 3 on it when the root announces version 3 or later, Stereo KWin makes the X window twice as wide while keeping its place, possibly seconds later, and the swapchain follows the X window only once it is twice as wide (checked 2026-11-07, ORDER 34b).
Where it cannot declare, it says so and the window shows the two views side by side, flat; a 2D rendering mode withdraws the declaration.
The proof recipe on a headless Stereo KWin, the controls and the traps are in [openxr-runtime-full-sbs.md](references/openxr-runtime-full-sbs.md).
The installed runtime is found by the OpenXR loader through `/etc/xdg/openxr/1/active_runtime.json`, which Debian's Monado and the edition's DisplayXR package share through the `openxr1-active-runtime` alternatives group; a person picks one with `update-alternatives --config openxr1-active-runtime`, for themself with a link in `~/.config/openxr/1/`, or for one program with `XR_RUNTIME_JSON` ([packaging an OpenXR runtime](../edition-packaging/references/openxr-runtime-package.md), checked 2026-11-07, ORDER 58).
Monado, the OpenXR SDK, VRPN and OSVR take no material generated by a machine learning model (their maintainer's own rule), so AI-assisted work of this kind goes only to runtimes whose rules welcome it, after reading each project's contribution rules.

## Proof

Angles logged per eye against the expected separation, both eyes captured in play, the HUD and crosshair identical in both eyes, settings restored after exit, and a run on the real display at the very end.
