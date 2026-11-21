# An editor in 3D: Kdenlive and MLT (ORDER 61e, 2026-11-21)

Part of the [`stereo-video`](../SKILL.md) skill.

Check freshness first: written on 2026-11-21 from Kdenlive 26.08.1-1+stereo3d9+lc1 and MLT 7.40.0-1+stereo3d8+lc1 (the edition's build tree, `sparky-os/packages/kdenlive-stereo-61e`; ORDER 61e, two milestones), on Stereo KWin +stereo3d59.

An editor shows media, so it is a player for its monitors and a writer for its renders.
Its 3D options are the contract's: Enable 3D, the render resolution per eye (the project's resolution), a shortcut to Display Settings, and for each clip the input corrections.
Each part below has its own place and its own proof.

## The recipe

| Part | Where it lives | What the person gets |
|---|---|---|
| The monitor as the 3D area | Kdenlive patches 0002, 0004, 0007 (`src/monitor/stereolayer.cpp`: a `wl_subsurface` under the window, declared full side by side) | The 3D picture in the monitor |
| The program's 3D options | Kdenlive patch 0016: the layer's `Stereo::Enable3DAction`, Left Eye Only below it, Display Settings… (`kcmshell6 kcm_kscreen`) | Enable 3D; off shows the frames as they are and declares nothing |
| Both monitors in 3D at once | Kdenlive patch 0018: one libstereo-declare set-up per process, shared by the 3D areas | The clip monitor and the project monitor each show their pair |
| 3D by default | Kdenlive patch 0009 (edition only): the kcfg defaults `stereo3d_preview` and `stereo3d_clip_preview` are 2 | A 3D clip is shown in 3D wherever the compositor takes stereo content |
| Told when 3D cannot be shown | Kdenlive patch 0010: `StereoLayer::failed(reason)`, the monitor's message area, once per choice | The reason in the monitor, and the packed frame |
| Clips of any packing in one project | MLT 0013 (`stereo3d_unpack` with `in_producer`, `target_views`) and Kdenlive patch 0012 | The project's frames are full side by side, left eye first |
| A clip's input corrections | Kdenlive patch 0015: the clip's Properties, kept as `kdenlive:stereo3d_input` and `kdenlive:stereo3d_swap` in the project | The layer's 3D Input Format, Swap left and right eyes, Save the correction into the file |
| The render resolution per eye | Kdenlive patch 0014 (`RenderRequest::prepareStereoRender()`) | A 1920x1080 3D project renders 3840x1080, each eye 1920x1080 |
| Render presets | Kdenlive patch 0011 (`data/profiles.xml`, group Stereoscopic 3D) and MLT 0014 (the HEVC SEI) | H.264 and HEVC in MP4 and Matroska, marked in the stream and the container |
| The source's depth | MLT 0015: `stereo3d_unpack` works in RGBA64 for a deep request and hands back the asked format | A 10 bit clip comes out at 10 bits through the conversion |
| Half or whole views in a player | MLT 0016: the shared rule reads the producer's own frame, not the monitor's | A clip shown in the clip monitor keeps its eyes' shape |
| An unknown preset name | Kdenlive patch 0017 | `kdenlive --render` stops and says so, exit status 1 |
| Thumbnails | Kdenlive patch 0013: `stereo3d_unpack` with output left first in the thumbnail producer | One picture, the left eye, at the view's shape |

### The default, and how it is decided

- **Where the default lives:** the setting exists only in the edition's patches, so its default is set in an edition-only patch of the program, not in `/etc/xdg`. Both keep a person's choice, because KConfig writes a value that differs from the default (below); the patch keeps one place and no new conffile.
- **What decides 3D:** the menu offers 3D only when the compositor announces `kde_stereo_content_manager_v1` with `wl_subcompositor`, `wp_viewporter` and `wl_shm` (`StereoLayer::isSupported()`). Stereo KWin always announces it, also with only 2D outputs, where KWin shows the left view (Daniel, 2026-10-14: "our defaults are 3d always, when in a 2d monitor, we display left side"). On any other compositor the menu has no 3D entry and nothing is said.
- **X11:** the 3D area is a Wayland surface. Kdenlive on xcb under Stereo KWin's Xwayland (`stereo_supported_x11() > 0`) says once that the monitor shows 3D only on Wayland.

### The program's 3D options, and what "off" shows

- **Where:** each monitor's menu (its toolbar's overflow, More Options, Stereoscopic 3D): Enable 3D, Left Eye Only, Display Settings…, and in the project monitor Packing of the Project. +stereo3d6 to +stereo3d8 had Preview (Packed Frame as It Is, Left Eye Only, 3D), Packing of the Project and Right Eye First there.
- **Enable 3D** is the stereo layer's action (`Stereo::Enable3DAction`, its words and catalogue). The setting keeps its values (`stereo3d_preview`, `stereo3d_clip_preview`): 0 off, 1 the left eye, 2 3D; a choice saved before reads the same.
- **Off** shows the frames as they are, nothing declared: in a 3D project that is the project's full side-by-side frame, in the clip monitor the clip's packed frame.
- **Left Eye Only** is a view of one eye below the switch; choosing it enables 3D again, as in the picture programs (ORDER 551c).
- **Display Settings…** opens Display Configuration (`kcmshell6 kcm_kscreen` through `KIO::CommandLauncherJob`). Each screen's 3D format and its swap of the eyes are there. When the program cannot be started the person is told what did not start and where the screens' 3D formats are (`kcmshell6` comes from `libkf6kcmutils-bin`, which Plasma's desktop recommends).
- **No swap for everything.** The project-wide "Right Eye First" of +stereo3d6 to +stereo3d8 is gone. A project saved with it gets that packing with the right eye first as the input format of each video clip; it then takes its packing from its clips, and the project monitor says so once.

### The render resolution per eye

- A 3D project's resolution is one eye's. A 1920x1080 project whose packing comes from its clips renders 3840x1080: the render document's profile is doubled in width and in display aspect.
- Each clip's `stereo3d_unpack` fits its views to whole pictures (`target_views=full`). A clip with no filter in the project (a side-by-side clip of the project's own kind) gets one in the render.
- A clip whose frame is the doubled frame itself (3840x1080, square samples, left eye first) is taken as it is, decoded at its own depth.
- A project whose own frame already holds two whole views (3840x1080) is written as it is. So is a project whose packing the person declared by hand.
- **The monitors** show the project's frame at its resolution: in a 1920x1080 3D project both eyes are in that frame at half width, and the monitor hands them to the compositor as they are (KWin scales once).
- **Plain presets** in a 3D project write the same doubled frame, marked: the resolution is one eye's whatever the preset.
- **Matroska's DisplayWidth** is one plane's. RFC 9559 section 18.10 (and Matroska's own notes, "Multi-planar and 3D Videos"): "The pixel count of the track (PixelWidth/PixelHeight) is the raw number of pixels (for example, 3840x1080 for full HD side by side), and the DisplayWidth/DisplayHeight in pixels is the number of pixels for one plane (1920x1080 for that full HD stream)." FFmpeg's muxer writes half the frame's width for side by side.
  - A 3840x1080 render carries 1920x1080, which is right.
  - The 1920x1080 renders of +stereo3d8 carried 960x1080 for views holding a 16:9 picture squeezed to half width: by the specification they said "show each eye at 960x1080", that is squeezed.

### A clip's input corrections

- **Every video clip's Properties** offer the stereo layer's "3D Input Format": every entry of the layer's list, both eye orders, the anaglyph pairs and the picture-with-depth layouts.
  - The ids are the file marks' `Stereo3DLayout` words.
  - The words are the layer's, in its `Stereo::FileChoiceMenu` context, translated by the layer's own catalogue.
  - The layer 1.22 has no public list yet (its C list `stereo_policy_input_format_at()` came in 1.23), so Kdenlive keeps a copy of the table in `src/utils/stereo3d.cpp`. A format Kdenlive shows as one picture says "(one view shown here)".
- **Swap left and right eyes** is shown for a clip shown in 3D, or to take back a swap the clip has; **Save the correction into the file** for a clip shown in 3D (greyed while there is nothing to save) or holding a correction (a 3D clip set to Not 3D can be saved as 2D). A clip shown flat with no correction gets the list only, so an unmarked 3D clip can be declared, and nothing else.
- **Kept in the project** (`kdenlive:stereo3d_input`, `kdenlive:stereo3d_swap` on the clip, undoable), never in the file. The packing a clip is shown with (monitors, thumbnails, the project's conversion, renders) is the file's unless the person corrected it.
- **The save** writes the file's own mark through the layer's libstereo-av (`stereo_mark_save()`: Matroska's StereoMode with mkvpropedit, MP4's st3d in place). The library reads it back; Kdenlive then takes the correction off the clip and reads the clip again from the file.
  - A refusal says why: a container with no mark, a value the mark has not, the stream's own SEI declaring another format, an MP4 without room, mkvpropedit missing.
  - On a refusal the file is as it was and the correction stays in the project.

### The source's depth

- MLT's `stereo3d_unpack` asked every producer for RGBA, 8 bits a sample, so a 10 bit 3D clip taken apart lost its depth: 256 luma levels in a row of a 10 bit ramp, where the source has 877.
- MLT 0015: asked for more than 8 bits a sample, the filter works the views in RGBA64 and hands back the format asked for, an opaque picture with no alpha mask. The result is 877 levels in each eye, through Kdenlive's headless render with its track compositing.
- Kdenlive itself keeps a 10 bit clip at 10 bits in a 2D project with no effect (877 levels with a 10 bit preset). Kdenlive's own presets are 8 bit.

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
- **Symptom:** Kdenlive stays at its splash for minutes, its log ending at "qt.multimedia.ffmpeg: Using Qt multimedia with FFmpeg". **Cause:** KWin's Xwayland "failed to start" (kwin.log) under a long runtime folder (87 characters, under a deep evidence path), and Qt Multimedia's VDPAU probe then waits on `DISPLAY` :0. **Fix:** a short `XDG_RUNTIME_DIR` (`mktemp -d /tmp/rt-XXXXXX` inside the container), and wait for Kdenlive's window instead of a fixed time. **How found:** the same case passed through one launcher and not the other; a probe of KWin with one X client under each path.
- **Symptom:** a 3D project rendered with a 10 bit preset is black from the command line, and right through `melt`. **Cause:** after the deep conversion the frame carried an alpha mask, so Kdenlive's track compositing (qtblend) composited it as a picture with transparency, and drew it black. The headless render's `QT_QPA_PLATFORM=offscreen` is what makes qtblend run at all: without a display MLT's Qt module does not load. A full alpha summed in float also came out at 65534, not 65535. **Fix:** MLT 0015 clears the mask of an opaque picture after converting it, and sums in double. **How found:** a `meltpath` wrapper kept Kdenlive's render playlist (the path melt gets is percent-encoded, and `kdenlive_render` deletes the playlist when it ends); the environment was bisected one variable at a time; prints in a debug build of `libmltqt6`.
- **Symptom:** in a doubled render, a clip marked side by side with an anamorphic frame (1920x1080, sample aspect 2:1, which MLT reads from Matroska's DisplayWidth) fills a quarter of each eye. **Cause:** MLT's own scaling of a frame of another size or shape into the doubled frame is not one per eye. **Fix:** only a clip whose frame is the doubled frame itself is taken as it is; every other clip goes through `stereo3d_unpack`.
- **Symptom:** `kdenlive --render` with an unknown preset name crashed (exit 139) after the new message. **Cause:** the early return skipped `closeCurrentDocument()` before `Core::clean()`. **Fix:** end as the render's own end does.
- **Symptom:** a catalogue patch named `*-catalogues.patch` was never checked by `tests/translations-shipped.py`. **Cause:** it globbed `*.po.patch`. **Fix:** it reads every patch in `translations/` that changes a gettext `.po` file, and names the ones it cannot read (Qt `.ts`, sView `.lng`, JSON or desktop files only).
- **Symptom:** opening a 3D clip in the clip monitor while the project monitor shows one in 3D, the clip monitor says "the stereo declaration library could not start". **Cause:** libstereo-declare is set up once in a process (`stereo_declare_wayland_init()` answers `-EBUSY` to a second call), and each monitor's 3D area set it up on its own queue. **Fix:** Kdenlive patch 0018: one set-up, on a queue of its own, shared by every 3D area and ended by the last. **How found:** with SDL's dummy audio the rig's clip monitor opens at all (below), then the message showed on +stereo3d8 too.
- **Symptom:** an unmarked clip given its packing in its properties shows letterboxed in the project monitor, each eye twice as wide. **Cause:** its timeline producer is made before the clip's type and frame size are known: the correction was skipped for a clip not yet known as video, and the shortcut "already side by side, views of the project's kind" was taken with a 0x0 frame. **Fix:** the correction applies as soon as the producer exists, and the shortcut needs a known size or a views mark. **How found:** each eye's square measured (`monitor-shape.py`: the square's width over its height, inside the area where the eyes differ).
- **Symptom:** the same clip in the clip monitor has its eyes twice as wide. **Cause:** `stereo3d_unpack` judged half or whole views by the frame it was given, the clip fitted with bars into the monitor's 1920x1080. **Fix:** MLT 0016 judges by the producer's own frame.
- **Symptom:** after "Save the correction into the file" the project monitor is black until the playhead moves. **Cause:** the save reads the clip again from the file, and the project monitor shows the next frame it is asked for. Not fixed; the file, the clip and the clip monitor are right at once.
- **Symptom:** in the rig, opening a clip in the clip monitor says "Could not create the video preview window" (the published Kdenlive too). **Cause:** the second monitor's consumer cannot open SDL's audio in the container. **Fix:** `SDL_AUDIODRIVER=dummy` for Kdenlive only (`APP_ENV`).
- **Recipe (driving the clip's properties):** with KWin's fake input (the proof rig skill's `fakeinput`): click the clip in the bin (it opens in the clip monitor), the Clip Properties tab, the pencil (the Properties page), the 3D Input Format list, `Down` `Down` `Enter` (Automatic, Not 3D, then the first side by side), then the save button. The window opens at the same place in every case: positions are read once from a capture.
- **Symptom:** Display Settings… in a system without `kcmshell6` shows an error dialog that says only "kcmshell6". **Cause:** `KIO::CommandLauncherJob` sets the program's name as the error text and `KDialogJobUiDelegate` shows that text as it is (KJob, not a KIO job, so no sentence is built). **Fix:** handle `KJob::result` and say what did not start and where the screens' 3D formats are. **How found:** the rig has no `kcmshell6`; the menu clicked by fake input.
- **Symptom:** the monitor's 3D menu is not in the monitor's context menu. **Cause:** it is in the monitor's configuration menu, which a narrow monitor puts behind its toolbar's overflow (`>`), then More Options. **How found:** captures after each click.
- **Symptom:** `tests/validate-po-patches.py` passes a patch with no output. **Cause:** run from the wrong folder it finds no patch (its build root defaults to the current folder); run from the build clone's root it says "no file section" for a quilt-refreshed patch (it needs a `diff --git` line before each file) and "no DSC mapping" for a patch not in its table. **Fix:** a `diff --git` line in the patch (quilt keeps it); the package build proves the rest (quilt applies it, msgfmt -c).
- **Symptom (open):** in a 3D project a 2D clip shows a different half of its picture in each eye: in the monitors and the published renders it fills the packed frame (left half in the left eye), in a +stereo3d9 render it sits at its own shape in the middle of the doubled frame (columns 960 to 2879 of 3840). **Cause:** only 3D clips get `stereo3d_unpack`; a 2D clip, a title or a picture is fitted to the profile like any producer. **Fix owed:** by the doubling rule each 2D element of a 3D project is drawn into both eyes, the same picture (a mono packing for `stereo3d_unpack` that fills both halves, given to every 2D producer of a 3D project, in the monitors and the renders alike). **How found:** a render of a 3D clip followed by a 2D clip, the 2D clip's columns measured.
- **Symptom:** ScreenShot2 answers "Screenshot got cancelled". **Cause:** without a render node `kwin_wayland --virtual` falls back to QPainter. **Fix:** give the container the render node.
- **Symptom:** a log search finds no declaration. **Cause:** `WAYLAND_DEBUG` names objects `interface#id`, not `interface@id`.

### Packaging traps

- **Symptom:** MLT's build ends with `libmlt-perl_7.40.0-1+stereo3d6+lc1_amd64.deb: previous edition dependency qualification failed` and the new packages are removed. **Cause:** the link and start gate qualifies the predecessor too, and the published libmlt-perl depends on `perlapi-5.42.3`, which Debian testing no longer has (perl 5.44.0-3 on 2026-11-21): it can no longer be installed at all. **Fix:** the recipe leaves that one predecessor out of `previous-mlt`, saying why; the successor links today's perl. **How found:** the gate's `case-*-solve.log`.
- **Symptom:** removing a finished build folder is refused because "a repository could not be read". **Cause:** MLT's tarball carries glaxnimate's thorvg submodule pointer, a `.git` file naming a gitdir that does not exist. **Fix:** remove that file first, then the folder.
- **Kdenlive needs the new MLT:** its `Depends` is raised to `libmlt7 (>= 7.40.0-1+stereo3d7+lc1)`, and the link gate of its build takes the new MLT as an edition sibling (`release/build-from-lc-dsc.sh` with `SPARKY_LC_SIBLINGS_DIR`).
