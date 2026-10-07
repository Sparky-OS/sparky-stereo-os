---
name: 3d-to-vr
description: How stereo content and the stereo desktop of Sparky Stereo OS reach a headset or a phone viewer: the headset as one more output of the desktop, 360 and VR180 video, what open software exists today, and what is planned. An early skill; load the general sparky-stereo skill first.
---

# From 3D content to a headset

**Check freshness first.** Written on 2026-10-07. This is the youngest part of the work: the principles are settled, the edition's headset output is planned. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

## The principle

A headset is a stereoscope you wear, so in the edition it is **one more output of Stereo KWin**: programs keep handing over full side by side, exactly as for a 3D television, and the headset's output filter does what only a headset needs (lens correction, head tracking, placing the picture in space). No program has to know a headset exists.

- **Flat stereo content** (a 3D film, a stereo photo, a 3D window) appears on a virtual screen in front of the viewer, each eye seeing its own view.
- **360 and VR180 video** carries its projection in the stream (`sv3d` in MP4, mpv's `demux-projection`); in a headset the viewer looks around by turning their head, on a television by the mouse, from the same file ([`stereo-video`](../stereo-video/SKILL.md)).
- **The phone viewer** (Cardboard-style lenses) is the cheapest headset: the same output filter with the phone's lens correction, the picture streamed from the PC.

## What open software exists today

Each a piece, none the whole desktop out of the box; awesome-stereoscopy's [desktop in a headset](https://github.com/danielcamposramos/awesome-stereoscopy#the-desktop-in-a-headset-2018-to-2026) section lists them with sources:

- [Monado](https://monado.dev), the open OpenXR runtime;
- xrdesktop (KDE and GNOME windows in VR), Safespaces, Simula and Stardust XR;
- KWin's own "VR Mode" draft ([plasma/kwin !8671](https://invent.kde.org/plasma/kwin/-/merge_requests/8671)), closest to KDE itself;
- [ALVR](https://github.com/alvr-org/ALVR) and [PhoneVR](https://github.com/PhoneVR-Developers/PhoneVR) with the open [Cardboard SDK](https://github.com/googlevr/cardboard), to wear a phone;
- on the web, the [WebXR Layers API](https://www.w3.org/TR/webxrlayers-1/), whose `stereo-left-right` and `stereo-top-bottom` layouts are the web's only standard stereo vocabulary, inside an immersive session.

## Planned in the edition

- The headset and phone outputs of Stereo KWin, starting when a headset is on the desk.
- The Cardboard look as a KWin output filter, for phone viewers.
- The Stereo Spectator's other direction ([`vr-to-3d`](../vr-to-3d/SKILL.md)): the headset player's eyes shown in stereo to the room.

## Proof, when it starts

The output filter's two eyes captured and compared with a reference lens model, the content's own left and right views in the right eyes, 360 orientation the same in both eyes, and a person in the headset at the end.
