# Draft 01: Half-Life 2 VR mode on a 3D display (ValveSoftware/Source-1-Games, new issue)

Status: **POSTED 2026-09-24 21:53 UTC as https://github.com/ValveSoftware/Source-1-Games/issues/8297** (approved by Daniel; posted verbatim except `source-sdk-2013 #268` written as `ValveSoftware/source-sdk-2013#268` so GitHub links it).
Target: https://github.com/ValveSoftware/Source-1-Games/issues/new Evidence: `tools/vr-stereo-spectator/sourcevr/README.md` and `FORMULA.md` in this repository; logs under `/K3D/temp/hl2-bench/` (local).
Post this one first; drafts 02-04 link to it.

---

**Title:** [HL2] [Linux] VR mode drives a 3D TV through a replacement sourcevr.so: six things that would make it clean

@kisak-valve for triage. cc @misyltoad, since this touches the engine side you synced into the SDK.

Half-Life 2 plays in stereo 3D on a 3D television on Linux, through the game's own VR interface.
I wrote a replacement `sourcevr.so` that implements `SourceVirtualReality001` for a display instead of a headset: off-axis eyes sharing one window at the screen plane, side by side or top and bottom, the game's view in place of head tracking.
It is public, under the Source 1 SDK License: https://github.com/danielcamposramos/sony-bravia-linux/tree/main/tools/vr-stereo-spectator

**Tested:** current Half-Life 2 (`hl2_complete`), Linux native, `-vulkan`, RTX 3060 on the proprietary driver, Sony KDL-46HX855 and KDL-46EX725 in side-by-side 3D.
A real playthrough worked: old saves, the canals and the airboat chase, two save loads and two level transitions in one launch, shadows right, no crash.

Getting there needed workarounds for six behaviours of the VR mode.
None of them hurts a headset the way it hurts a display, which is why I am reporting them.

**1. `sourcevr_<game>.cfg` does not run.**
When VR mode starts from `ShouldForceVRMode()`, neither `hl2/cfg/sourcevr_hl2.cfg` nor `hl2_complete/cfg/sourcevr_hl2_complete.cfg` executed (an `echo` line in each never printed with `-condebug`).
So your own Half-Life 2 VR settings (`vr_first_person_uses_world_model 0`, `hud_draw_fixed_reticle 0`, `r_flashlightscissor 0`) never apply.
The module now issues them itself.

**2. `CreateRenderTargets()` is never called, and `_rt_gui` does not exist.**
With VR forced at start, the engine never called `CreateRenderTargets()`, not even with `VRModeAdapter "0"` in `videoconfig_linux.cfg`.
The client then looks for `_rt_gui` (`couldn't find materials/_rt_gui.vtf`) and the HUD has nowhere to go.
The module creates its targets on first use, inside the render-target allocation bracket.

**3.
The HUD shows as a purple and black checkerboard: the material is never precached.**
This is the same symptom as source-sdk-2013 #268 (2014, "a black/pink checkerbox right in the FOV", confirmed to be the HUD).
With the threaded material system, a material first used from the render thread without a precache on the main thread draws as the error material, whatever its texture.
Precaching the HUD material once (`IncrementReferenceCount()` plus `CacheUsedMaterials()`) fixed it (`IsPrecached()` went from 0 to 1).

**4.
The crosshair is painted for a 640x480 screen.**
In VR mode the client paints the crosshair into each eye at the centre of its 640x480 UI screen, unscaled (measured at eye pixel 314,240 of a 960x1080 eye).
At any other eye size it lands off-centre.
The module offers 640x480 eyes, or turns `crosshair` off and draws `crosshair_default` itself.

**5.
The muzzle flash sprite misses the gun, and `viewmodel_fov` is a cheat.**
In VR mode the weapon is drawn with the eye projection, but `FormatViewModelAttachment()` still converts the attachment from `viewmodel_fov` to the world's field of view.
With `viewmodel_fov 90` (under `sv_cheats 1`, in a demo) the sprite sits exactly on the muzzle.
**The ask:** allow `viewmodel_fov` while VR mode is active, or skip the conversion when the weapon uses the eye projection.
A stereo view changes only the cameras, so it gives no advantage the 2D view does not have.

**6.
The UI cursor lives in window pixels, the UI in a 640x480 corner.**
The UI cursor moves 1:1 with the window, while the VR UI sheet is the window's top-left 640x480, so the cursor walks off what the eyes show.
The module confines the pointer to that rectangle with `SDL_SetWindowMouseRect`.

**And one crash:** with `-opengl` (ToGL), every VR run that lasted past 20 seconds crashed at about that point in the material system's render thread (`materialsystem.so`, `studiorender.so`, `shaderapidx9.so`, then libc).
With `-vulkan` the same runs are stable.
Core dumps are available.

**Related:** #3782 (is sourcevr supported on Linux: yes, with this), #1013 (the 2013 request for side-by-side 3D, "pretty much all 3D ready DLP projectors support SBS"), source-sdk-2013 #268 (the checkerboard).

Why this matters beyond one game: a VR engine already renders two eyes, so it can drive every 3D television, projector and monitor people still own, with no headset.
Half-Life 2 showed what has to change for that, and the list is short: https://github.com/danielcamposramos/sony-bravia-linux/blob/main/tools/vr-stereo-spectator/FORMULA.md

---

Notes for Daniel (not for posting):
- Disclosure, if you want it, goes once at the end of this post, per the repo's rule.
- Evidence per point: 1 the `echo` markers (runs a10/a13, 2026-09-24 16:23); 2 module log and console; 3 the module log (`precached 0 -> 1`) and the T1/T3 tests (the error pattern even with `_rt_FullFrameFB`); 4 the `svrtv-frame.tga` dump; 5 your eye, runs with `viewmodel_fov 75` (almost) and `90` (exact); 6 the mouse log (cursor started at 960,540, left the sheet down to y 819); crash: coredumps 15:34, 16:23, 16:25, runs a08/a10/a13/a14/a19.
- The first-playback stop of timed demos (2 frames) is a separate, non-VR issue; not in this draft.
