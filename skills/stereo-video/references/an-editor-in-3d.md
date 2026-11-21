# An editor in 3D: Kdenlive and MLT (ORDER 61e, 2026-11-21)

Part of the [`stereo-video`](../SKILL.md) skill.

Check freshness first: written on 2026-11-21 from Kdenlive 26.08.1-1+stereo3d8+lc1 and MLT 7.40.0-1+stereo3d7+lc1 (the edition's build tree, `sparky-os/packages/kdenlive-stereo-61e`), on Stereo KWin +stereo3d59.

An editor shows media, so it is a player for its monitors and a writer for its renders.
Each of the five parts below has its own place and its own proof.

## The recipe

| Part | Where it lives | What the person gets |
|---|---|---|
| The monitor as the 3D area | Kdenlive patches 0002, 0004, 0007 (`src/monitor/stereolayer.cpp`: a `wl_subsurface` under the window, declared full side by side) | Preview: Packed Frame as It Is, Left Eye Only, 3D |
| 3D by default | Kdenlive patch 0009 (edition only): the kcfg defaults `stereo3d_preview` and `stereo3d_clip_preview` are 2 | A 3D clip is shown in 3D wherever the compositor takes stereo content |
| Told when 3D cannot be shown | Kdenlive patch 0010: `StereoLayer::failed(reason)`, the monitor's message area, once per choice | The reason in the monitor, and the packed frame |
| Clips of any packing in one project | MLT 0013 (`stereo3d_unpack` with `in_producer`, `target_views`) and Kdenlive patch 0012 | The project's frames are full side by side, left eye first |
| Render presets | Kdenlive patch 0011 (`data/profiles.xml`, group Stereoscopic 3D) and MLT 0014 (the HEVC SEI) | H.264 and HEVC in MP4 and Matroska, marked in the stream and the container |
| Thumbnails | Kdenlive patch 0013: `stereo3d_unpack` with output left first in the thumbnail producer | One picture, the left eye, at the view's shape |

### The default, and how it is decided

- **Where the default lives:** the setting exists only in the edition's patches, so its default is set in an edition-only patch of the program, not in `/etc/xdg`. Both keep a person's choice, because KConfig writes a value that differs from the default (below); the patch keeps one place and no new conffile.
- **What decides 3D:** the menu offers 3D only when the compositor announces `kde_stereo_content_manager_v1` with `wl_subcompositor`, `wp_viewporter` and `wl_shm` (`StereoLayer::isSupported()`). Stereo KWin always announces it, also with only 2D outputs, where KWin shows the left view (Daniel, 2026-10-14: "our defaults are 3d always, when in a 2d monitor, we display left side"). On any other compositor the menu has no 3D entry and nothing is said.
- **X11:** the 3D area is a Wayland surface. Kdenlive on xcb under Stereo KWin's Xwayland (`stereo_supported_x11() > 0`) says once that the monitor shows 3D only on Wayland.

### What a 3D render preset writes

```
f=mp4 movflags=+faststart strict=-1 vcodec=libx264 crf=%quality g=15 acodec=aac ab=%audiobitrate+'k' stereo3d=side_by_side
f=matroska vcodec=libx264 crf=%quality g=15 acodec=aac ab=%audiobitrate+'k' stereo3d=side_by_side
properties=x265-medium f=mp4 movflags=+faststart strict=-1 vcodec=libx265 crf=%quality:open-gop=0 acodec=aac ab=%audiobitrate+'k' stereo3d=side_by_side
properties=x265-medium f=matroska vcodec=libx265 crf=%quality:open-gop=0 acodec=aac ab=%audiobitrate+'k' stereo3d=side_by_side
```

MLT's avformat consumer turns `stereo3d` into frame side data (libx264 writes the H.264 SEI, D.2.26) and stream side data (Matroska `StereoMode`, RFC 9559 5.1.4.1.28.3; MP4 `st3d`).
A render with a 3D preset of a project with no 3D clip, or whose frames the person declared packed another way, is refused with the reason: a 2D video is never marked 3D.

### Clips of different packings in one project

Every clip whose frames hold both views gets `stereo3d_unpack` (`packing`, `invert`, `output=side_by_side`, `in_producer=1`, `target_views`) on its timeline producer, while the project's packing comes from its clips.
In a producer the filter takes the views out of the producer's own picture and fits each, keeping its shape, to its half of a frame of the profile's size: the one resize an editor makes of any clip.
`target_views=half` is for a profile whose frames carry half views squeezed to half their width (a 1920x1080 side by side profile, the shape the players' shared rule reads as half views); the view is fitted to a half shown twice as wide.
A clip already side by side, left eye first, with views of the project's kind keeps its frames as they are (no RGBA conversion).
Frame sequences are not taken apart in a producer.

### Proof

The rig is the lane's scripts (a headless Stereo KWin as in [`stereo-proof-rig`](../../stereo-proof-rig/SKILL.md), Kdenlive with a generated one-track project):

- **Monitor:** one fresh session per case, `kwin_wayland --virtual --width 1920 --height 1080` with the AMD render node, `WAYLAND_DEBUG=client`, ScreenShot2 `CaptureWorkspace`. A pair is a 3840x1080 capture; inside the area where the eyes differ the left eye is red and the right eye blue, outside it 0 pixels differ; one `kde_stereo_content_v1.set_content(3)`.
- **Renders:** `kdenlive --render --render-preset NAME project.kdenlive out.EXT` with `QT_QPA_PLATFORM=offscreen`; the marks read back with FFmpeg's `trace_headers` (H.264 `frame_packing_arrangement_*`, H.265 `fp_*`), ffprobe's stream side data, `mkvinfo` and an MP4 box walker for `st3d`; one frame per clip analysed for red left, blue right, the picture filling the frame and the white square at the same place and size in both eyes.
- **Thumbnails:** the bin's first row of the capture: red only, and the fixture's square square.
- **Controls:** a 2D clip; a 2D desktop (a preloaded library that hides `kde_stereo_content_manager_v1` from every `wl_registry`); an account that chose Packed Frame or Left Eye Only; the same 2D project rendered by the published and the new build (identical decoded frames).

## Traps

- **Symptom:** a person who chose Packed Frame as It Is in the published Kdenlive gets 3D after the default changed. **Cause:** with the default 0, choosing 0 writes nothing: `KConfigSkeletonGenericItem::writeConfig()` reverts to the default when the value equals it and no system-wide default exists (`if ((mDefault == mReference) && !cg.hasDefault(mKey)) cg.revertToDefault(...)`), so that account's file holds no choice. **Fix:** none possible for that account; with the new default every choice, Packed included, is written and kept. **How found:** a KCoreConfigSkeleton test writing 0, 1 and 2 under default 0 and default 2.
- **Symptom:** `stereo3d_unpack` on a clip's producer gives a 7680x540 frame, or a pillarboxed pair with the views squashed. **Cause:** the producer's normalizing filters (swscale, resize) are asked for the profile's size and pad the packed frame before the filter sees it; `resize` reads the frame's `meta.media.width`, `meta.media.height` and `aspect_ratio` when the frame is made. **Fix:** `in_producer`: the filter announces its output in `filter_process`. **How found:** a small C program with a loader producer, the filter first or last.
- **Symptom:** in Kdenlive the same filter still gives a half-black, squashed picture. **Cause:** Kdenlive's clips are MLT chains: their normalizers are links (`chain_normalizers.ini`), before every filter, so no filter order puts one before them. **Fix:** the filter asks the links for the producer's own picture with the frame's `distort` set, and fits each view to the profile itself. **How found:** `mlt_chain_attach_normalizers()` in `src/framework/mlt_chain.c`.
- **Symptom:** a project's clips keep their packing after loading a saved project. **Cause:** the timeline's producers come from the document (`ProjectClip::giveMasterAndGetTimelineProducer`), not from `getTimelineProducer`. **Fix:** attach in both, removing a filter marked `kdenlive:stereo3d_unpack` first.
- **Symptom:** an HEVC render is marked in the container and not in the stream. **Cause:** FFmpeg's libx265 wrapper writes no frame packing SEI from frame side data, and x265 4.3 silently ignores `-x265-params frame-packing=3` (only payload type 5 in the stream). **Fix:** MLT's consumer sends HEVC packets through FFmpeg's `hevc_metadata` with `frame_packing=insert` (the edition's FFmpeg, patch 0012), which also clears `general_non_packed_constraint_flag`.
- **Symptom:** an MP4 render has no `st3d` box. **Cause:** FFmpeg's MP4 muxer writes `st3d` and `sv3d` only with `strict` at unofficial or below. **Fix:** `strict=-1` in the MP4 presets.
- **Symptom:** a clip marked only by its SEI is not taken apart, and its first thumbnail is the pair. **Cause:** MLT's avformat producer knows `meta.media.stereo3d.type` only after a frame is decoded. **Fix:** the clip learns it from its first thumbnail's frame, and a render of a 3D project decodes one frame of each clip whose packing is not known.
- **Symptom:** the published `kdenlive --render --render-preset "3D Matroska-H264/AAC"` writes an MP4 into a `.mkv` name. **Cause:** an unknown preset name falls back to the default H.264 profile with a warning in the log only.
- **Symptom:** the rig's Kdenlive waits in a configuration wizard or a Clip Problems dialog. **Cause:** a fresh account runs the first-run wizard; a project naming `frei0r.cairoblend` without frei0r installed lists it as missing. **Fix:** seed `[version]`, `[env]` (renderer, ffmpeg and melt paths) and `[sdl] sdlAudioBackend` as the wizard's OK leaves them, none of them a 3D key; composite tracks with `qtblend`.
- **Symptom:** from the second case of a container on, Kdenlive opens with "Kdenlive crashed on last start" and Reset Configuration. **Cause:** Kdenlive keeps its lock file `kdenlivelock` in the temporary folder, and a case that ends Kdenlive with a kill leaves it there. **Fix:** a `TMPDIR` of its own for each case.
- **Symptom:** a capture shows only Kdenlive's splash, and the check reports no pair. **Cause:** the program had not finished starting (a clip whose packing only its SEI says is decoded first). **Fix:** look at the capture before reading the numbers; wait longer (60 s) for that case.
- **Symptom:** ScreenShot2 answers "Screenshot got cancelled". **Cause:** without a render node `kwin_wayland --virtual` falls back to QPainter. **Fix:** give the container the render node.
- **Symptom:** a log search finds no declaration. **Cause:** `WAYLAND_DEBUG` names objects `interface#id`, not `interface@id`.

### Packaging traps

- **Symptom:** MLT's build ends with `libmlt-perl_7.40.0-1+stereo3d6+lc1_amd64.deb: previous edition dependency qualification failed` and the new packages are removed. **Cause:** the link and start gate qualifies the predecessor too, and the published libmlt-perl depends on `perlapi-5.42.3`, which Debian testing no longer has (perl 5.44.0-3 on 2026-11-21): it can no longer be installed at all. **Fix:** the recipe leaves that one predecessor out of `previous-mlt`, saying why; the successor links today's perl. **How found:** the gate's `case-*-solve.log`.
- **Symptom:** removing a finished build folder is refused because "a repository could not be read". **Cause:** MLT's tarball carries glaxnimate's thorvg submodule pointer, a `.git` file naming a gitdir that does not exist. **Fix:** remove that file first, then the folder.
- **Kdenlive needs the new MLT:** its `Depends` is raised to `libmlt7 (>= 7.40.0-1+stereo3d7+lc1)`, and the link gate of its build takes the new MLT as an edition sibling (`release/build-from-lc-dsc.sh` with `SPARKY_LC_SIBLINGS_DIR`).
