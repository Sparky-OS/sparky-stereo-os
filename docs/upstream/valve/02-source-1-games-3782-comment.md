# Draft 02: comment on ValveSoftware/Source-1-Games #3782 ("Is sourcevr supported on linux?", 2022, no reply)

Status: **POSTED 2026-09-24 as https://github.com/ValveSoftware/Source-1-Games/issues/3782#issuecomment-5822863780** (approved by Daniel, posted verbatim).
Target: https://github.com/ValveSoftware/Source-1-Games/issues/3782

---

It can work on Linux today, with a replacement `sourcevr.so`.
The one Half-Life 2 ships needs OpenVR and a headset, which is where "Unable to get VRMode adapter from OpenVR" comes from.

I wrote a replacement that implements the same interface for a 3D television instead, no headset and no SteamVR, and Half-Life 2 plays with it in stereo on Linux: https://github.com/danielcamposramos/sony-bravia-linux/tree/main/tools/vr-stereo-spectator

What the VR mode still gets wrong on this path is in #8297.
