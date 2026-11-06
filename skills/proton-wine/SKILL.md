---
metadata:
  requires-packages: wine64 | libwine | dxvk-wine64
name: proton-wine
description: >-
  Windows programs through Wine, Proton, DXVK and gamescope on the stereo desktop: identify the runtime libraries in use
  (a DXVK DLL's PE debug CRC), the chain from Direct3D to Vulkan to Stereo KWin, the stereo DXVK fork, wiz3D and the
  stereo Lutris build, StereoPhoto Maker under Wine, a WoW64 prefix and 16-bit programs, start Steam in the person's
  session environment (XDG_RUNTIME_DIR, wayland-0, pipewire-0), game-specific proof, Easy Anti-Cheat Linux v2
  requirements (Secure Boot, TPM 2.0, measured boot, IOMMU, lockdown). Load it when a game shows one eye or picks its
  own 3D output format, Wine prints Present returned status 1000001003, krnl386.exe16 failed to initialize, wineserver
  is not found, Wine menus come out flat, a wiz3D game quits after a second, Steam started from a script sees no
  display, DXVK resizes wrongly on the first frame, or an anti-cheat refuses the system.
---

# Windows programs through Wine and Proton

## Working recipe

1. Record game, Wine/Proton, DXVK and runtime versions and the libraries actually loaded; select injector, VR or native-pair input.
2. Use a fixed scene and private prefix. Check both eye images, UI, resize and restoration after exit; compare stereo off.
3. Return captures, declaration and runtime evidence. A source route or launcher option does not qualify every game in that family.

**Check freshness first.**
Written on 2026-10-07; much of this layer is planned, and each item says whether it is done.
Steam started from another environment, and Easy Anti-Cheat's Linux requirements, added on 2026-11-02.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

## The chain

A Windows game's Direct3D calls become Vulkan through DXVK (Direct3D 9 to 11) or VKD3D-Proton (Direct3D 12), and Vulkan reaches the GPU through Mesa, or through NVIDIA's driver with the edition's Vulkan layer.
Stereo can enter at three places:

1. **An injector draws two cameras inside the game.** wiz3D does this for DirectX 9 games, the vendor-neutral way iZ3D did once: the camera moves at the API, one world and two cameras ([`stereo-two-cameras`](../stereo-two-cameras/SKILL.md)). Its Linux build is merged upstream ([effcol/wiz3D #33](https://github.com/effcol/wiz3D/pull/33), 13 October 2026); our Proton work is on [Sparky-OS/wiz3D `stereo3d-proton`](https://github.com/Sparky-OS/wiz3D/tree/stereo3d-proton).
2. **The game has a VR mode.** Its two eyes go to a 3D display instead of a headset: load [`vr-to-3d`](../vr-to-3d/SKILL.md).
3. **The game draws side by side itself.** Some games and players have a side-by-side option. The window is declared as full side by side, and the game's own output menu is no longer the place where the format is chosen.

## gamescope

gamescope is Valve's micro-compositor.
Running a game inside it, nested in the desktop, raced frames between the game and the nested output, and stereo made the race visible; letting the nested output's present mode be chosen ends it ([ValveSoftware/gamescope #2438](https://github.com/ValveSoftware/gamescope/pull/2438), in review).
SteamVR on a 3D television runs inside gamescope (see [`vr-to-3d`](../vr-to-3d/SKILL.md)).
The variable `GAMESCOPE_NESTED_PRESENT_MODE` takes `fifo`, `mailbox` or `immediate`; unset or empty means FIFO; an unknown value, or a mode the host surface does not offer, logs an error and uses FIFO.
Building and proving it the way gamescope's own CI does is a recipe in [the lessons](references/lessons-2026-11.md#gamescope-build-and-prove-the-nested-present-mode).
In the edition the desktop draws the final 3D output; a game or gamescope packs the eyes for a screen only on systems without Stereo KWin.

## Done and planned

- **Done: 32-bit (i386) builds** of the edition's Mesa and FFmpeg, at the same versions as the 64-bit ones, so the 32-bit programs of Steam and Wine load the same stereo Mesa ([`edition-packaging`](../edition-packaging/SKILL.md)).
- **Planned: the stereo Lutris build:** a "Stereo 3D" switch, on by default, and a per-game "outputs side by side itself" checkbox; wiz3D as a clean package; the edition's own Wine and DXVK packages.
- **Planned: proof of each game family** on the capture rig, as below.

## Traps to check first

- **Does the game reach the edition's Mesa?** Steam's runtime, Flatpak and some launchers can load their own libraries. Check which Vulkan and OpenGL drivers the game actually loaded before testing stereo.
- **Never let a game pick its own 3D output format.** The game delivers full side by side; Stereo KWin's outputs decide the screen.
- **A Steam started from another environment breaks everything it launches.** Steam hands its own environment to every game and tool it starts.
  An automation shell (a sandbox, a service, a remote login) often has another `XDG_RUNTIME_DIR` than the person's session, which is where `wayland-0` and `pipewire-0` live.
  A `steam` command from such a shell, when Steam is not running yet, starts Steam with that environment.
  Measured on 2026-09-28: SteamVR's compositor "Couldn't create wayland display" (error 497), vrserver "Failed to connect to pipewire", gamescope "Failed to connect to wayland socket".
  Before any `steam` command, check that Steam already runs (`pgrep -x steam`); if it does not, have the person start it from the desktop, or set `XDG_RUNTIME_DIR=/run/user/$(id -u)` for the command.
  When a launched program cannot reach Wayland, PipeWire or PulseAudio, compare `/proc/<Steam's pid>/environ` with the session's environment first.

## Easy Anti-Cheat Linux v2

Epic's announcement of 2026-10-14, [Awesome Gaming on Linux Without Cheating](https://onlineservices.epicgames.com/news/introducing-easy-anti-cheat-linux-v2) (read on 2026-11-02), lists what a system needs for the games that will use it.
It has no kernel module of its own: an anti-cheat systemd service runs only while a protected game runs, with eBPF programs.

1. **A signed kernel and signed modules,** "signed with a well-known key"; an out-of-tree module, such as NVIDIA's, must be "built by an organization and signed with a well-known key".
2. **TPM 2.0,** enabled in the firmware.
3. **Secure Boot,** booted only with well-known keys.
4. **Measured boot:** the boot manager's measurements must be present.
5. **IOMMU** enabled in the firmware and in the kernel, with passthrough off (not required on handhelds).
6. **Kernel lockdown in integrity mode,** "explicitly enabled at boot time".
7. **kexec disabled** at boot time.
8. **The BPF LSM** loaded and active.

What it means for the edition, from Epic's FAQ and the edition's kernel:

- The well-known list of 2026-10-14 names Canonical's, Fedora's, Universal Blue's, Debian's, openSUSE's, SUSE's, Rocky Linux's, AlmaLinux's and Microsoft's UEFI CA keys.
  The edition's own Secure Boot key is not on it.
- Because every enrolled MOK is trusted for module signatures, Epic requires every enrolled MOK to be well-known; a person's own keys for other boot entries go into the firmware's db instead.
- A module that DKMS signs on the person's machine with its own key does not meet the first requirement.
- The edition's default boot keeps hibernation, so lockdown is a boot option and not automatic under Secure Boot ([`drivers`](../drivers/SKILL.md#the-editions-kernel-configuration)).
  Epic's FAQ allows exactly that: "You can maintain a separate boot entry with the required kernel and command line, and select that entry when you want to play a protected game."
- A game started without the requirements shows an error; Epic says the account is not banned for it.
- The Steam Deck does not meet the requirements yet, by Epic's FAQ.

## Proof

As in the general skill: a known scene, both eyes captured, the left eye's view correct, one declaration, the game's interface (menus, HUD) where it belongs (see the formula's 2D layer rules), and the game with stereo off unchanged.

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (10 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
