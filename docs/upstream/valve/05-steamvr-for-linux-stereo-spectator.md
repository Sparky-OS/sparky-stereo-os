# Draft 05: SteamVR on 3D displays (ValveSoftware/SteamVR-for-Linux, new issue)

Status: **POSTED 2026-09-24 21:57 UTC as https://github.com/ValveSoftware/SteamVR-for-Linux/issues/961** (approved by Daniel; his LTT forum comments added at his request; `openvr #706` written as `ValveSoftware/openvr#706` so GitHub links it).
Target: https://github.com/ValveSoftware/SteamVR-for-Linux/issues/new

---

**Title:** [Feature Request] Stereo spectator: VR games on a 3D TV or projector, side by side

@kisak-valve for triage. cc @charleslvalve and @aaronleiby, since part of this is an OpenVR driver question.

#337 asked for the opposite direction, flat games in a headset, and was closed as out of scope.
This is the other way around: VR games shown in stereo on the 3D televisions, projectors and monitors people already own, packed side by side or top and bottom, watched with the display's own glasses.
Every VR game already renders two eyes, so nothing has to be invented, only packed and sent to a different screen.

**It works.**
Half-Life 2's own VR interface drives a 3D TV on Linux through a replacement `sourcevr.so`, and a real playthrough ran clean: ValveSoftware/Source-1-Games#8297 What a VR engine needs to change for a display instead of a headset is written up here: https://github.com/danielcamposramos/sony-bravia-linux/blob/main/tools/vr-stereo-spectator/FORMULA.md

**Two modes, two small asks.**

1. **Spectator.** Someone plays in the headset and the room watches in 3D on the TV. The VR View mirror window already shows the eye images on the desktop, in 2D. The ask: a side-by-side and a top-and-bottom option for that window, with the two eyes as rendered, so any 3D display next to the headset shows the game in depth. Linus Tech Tips' first look at the Frame names the problem it solves: it is "a little inconvenient for certain games that involve swapping who's wearing the VR headset a lot" (https://www.youtube.com/watch?v=dU3ru09HTng&t=505s). With a stereo spectator, the rest of the room is in the game too, in depth, while one person wears the headset.

2. **Player.** No headset: an OpenVR driver presents the 3D display as the headset, the view follows the mouse or controller, and the compositor's output is one side-by-side frame. ValveSoftware/openvr#706 tried exactly this in 2018 and found the compositor refusing a double-width viewport unless it is a valid display resolution; it was never answered. The ask: is there a supported way for a driver to receive both eyes in one frame, side by side or top and bottom, at the display's own resolution? I will write the driver; I only need to know the path the compositor accepts.

**Why now.**
Valve told Road to VR (Ben Lang, 4 December 2025) that "stereoscopic 3D content on [Frame], we don't currently support it, but it's on our list": https://roadtovr.com/valve-steam-frame-stereoscopic-3d-support-flat-games-spatial-video/ A stereo spectator output is that same side-by-side frame, going the other way.
One side-by-side output would serve the Frame and every 3D display at once.
And people want it.
Building a passive 3D home theater, Linus Tech Tips said that "almost no new hardware supports 3D anymore" (https://www.youtube.com/watch?v=_4Sz6J49jho&t=52s), then asked the audience for "the best way" to "play games in Stereo 3D", "the greatest stereo 3D gaming setup of all time" (https://www.youtube.com/watch?v=_4Sz6J49jho&t=1012s). I answered that call on the LTT forum (https://linustechtips.com/topic/1589907-i-built-a-3d-theater-in-my-basement/?do=findComment&comment=16936161), and again under the Frame review (https://linustechtips.com/topic/1642726-the-steam-frame-changes-everything-full-review/?do=findComment&comment=16936512). In their Frame review, asked about stereoscopic content, the answer was "there's so little content available for it" (https://www.youtube.com/watch?v=3PGKMwgjla0&t=1261s). A stereo spectator output turns every VR game into that content, for the displays people already have.

---

Notes for Daniel (not for posting):
- The LTT quotes come from YouTube's auto-generated captions (your subtitle files in `sony-bravia-linux.private/docs/research/LTT videos/`); only short, clean phrases are quoted, each with its timestamp. Worth a listen at those three points before posting.
- kisak-valve's words on #337, for your reading, not for quoting back at him: "too far outside of the scope of SteamVR or Proton", and "If you dig into this and figure out how to wire it up, it most likely would need to go to a popular third party Proton build". The spectator ask is a feature of SteamVR's own mirror window; the player ask we build ourselves.
- Disclosure, if you want it, goes once at the end.
