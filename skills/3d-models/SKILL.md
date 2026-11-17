---
name: 3d-models
description: >-
  3D model, point cloud and splat files on the edition's desktop: what Dolphin shows for a model (KIO's freedesktop
  thumbnailer support, F3D's .thumbnailer files, the MIME types shared-mime-info lacks), F3D and libf3d in Debian
  and in the edition, CloudCompare's stereo modes measured on the stack, the slicers, Qt Quick 3D's multiview. Load it
  when a model's thumbnail is missing or flat, .ply, .splat, .spz or .3mf gets no preview, a thumbnail test says
  FAILED with no process started, KIO::filePreview returns nothing for every file, CloudCompare says Quad Buffered
  Stereo not supported, a 3D viewer is planned, or a 3D program's own anaglyph mode must be classified.
---

# 3D models, point clouds and splats

**Check freshness first.**
Written on 2026-11-17 (ORDER 17, milestone 1) from measurements in a throwaway container of Debian testing with the edition's repository: KIO 6.30.0, kio-extras 26.04.0+stereo3d5, F3D 3.5.0, CloudCompare 2.13.2+git20240821 (it shows itself as v2.14.alpha), Mesa 26.1.6+stereo3d21, Stereo KWin 6.7.4+stereo3d54.
Package versions move: read `apt-cache policy` again before relying on one.

## Working recipe: what Dolphin shows for a model

1. Install `f3d` in the container. It ships five freedesktop thumbnailers (`/usr/share/thumbnailers/f3d-plugin-*.thumbnailer`, `Exec=f3d --config=thumbnail ... --output=%o --resolution=%s,%s %i`) listing the MIME types of its readers.
2. KIO reads them: `FilePreviewJob::standardThumbnailers()` collects every `*.thumbnailer` file of `$XDG_DATA_DIRS/thumbnailers` as a plugin of category `standardthumbnailer` and runs its `Exec` through `StandardThumbnailJob` (kio 6.30.0, `src/gui/filepreviewjob.cpp`, `standardthumbnailjob.cpp`). `KIO::PreviewJob::availableThumbnailerPlugins()` lists them beside the compiled ones.
3. Run the real path without Dolphin: a small program calling `KIO::filePreview(items, QSize(256, 256), &plugins)` with `plugins = KIO::PreviewJob::defaultPlugins()`, offscreen, `HOME` and `XDG_CACHE_HOME` in scratch, inside `dbus-run-session`, with a passwd entry for the user. It prints GOT or FAILED per file and leaves the thumbnails in the freedesktop cache.
4. Read the cache's text chunks: a marked picture's thumbnail carries `X-KDE::Stereo3DLayout=sideBySideLeftFirst`, a model's carries only `Thumb::Mimetype`. Measured 2026-11-17: STL, OBJ, GLB and glTF get a flat 256x256 render; a marked `.pns` gets a 256x128 pair.
5. Put a wrapper named `f3d` first in `PATH` that logs its arguments to learn whether KIO started the thumbnailer at all.

## What does not get a preview, and why (measured)

- **`.ply`, `.splat`**: shared-mime-info has no type for them, so KIO types `.ply` as `text/plain` and `.splat` as `application/octet-stream`, and F3D's thumbnailer lists `application/vnd.ply` and `application/vnd.splat`. F3D itself renders both when called directly (1.8 to 11 kB PNGs). The fix is a MIME package with globs for the model formats, not a thumbnailer.
- **`.3mf`**: the compiled `opendocumentthumbnail` plugin lists `model/3mf` (the thumbnail a slicer embeds) and comes before the standard thumbnailers, so a 3MF without an embedded thumbnail fails and never reaches F3D. With only F3D's plugins enabled the same file gets a preview.
- **STEP, FBX, DAE, OFF, PTS, SPZ, E57, LAS, LAZ, XYZ**: no glob in the rig's `/usr/share/mime/globs2` either (the file has stl, obj, glb, gltf, 3mf, 3ds, dxf and blend); grep it before blaming a thumbnailer.

## Traps

- **Symptom:** `KIO::filePreview` fails every model, log line `Could not get plugin for ... emitting result`, no thumbnailer process. **Cause:** a null plugin list enables only the directory, image and JPEG thumbnailers (`PreviewJob::PreviewJob`, `enabledPlugins` null: `PreviewSettings` `Plugins` default), so no standard thumbnailer is enabled. **Fix:** pass `defaultPlugins()` or Dolphin's own list. **Found by:** `QT_LOGGING_RULES="kf.kio.gui=true"` (the category is `kf.kio.gui`; `kf.kio.gui.*` matches nothing) and reading `previewjob.cpp`.
- **Symptom:** `dbus-run-session` says `Failed to start message bus: Memory allocation failure`. **Cause:** the container user has no passwd entry. **Fix:** mount a passwd file naming the uid read-only over `/etc/passwd`.
- **Symptom:** `xdotool key F10` opens KWin's window overview, not the program's action. **Cause:** F10 is a KWin global shortcut in the rig. **Fix:** click the toolbar action.
- **Symptom:** a combo box in a Qt dialog ends on another item, once. **Cause:** `Down Down Return` sent at once races the popup. **Fix:** open the popup, wait two seconds, then `xdotool key --delay 400 Home Down Down`, and capture before pressing Return so the evidence shows the chosen item.

## F3D and libf3d

- Debian testing has `f3d` 3.5.0+dfsg-3 (readers: native, assimp, draco, hdf, occt; glTF, GLB, OBJ, STL, PLY, 3DS, PTS, SPZ, splat, STEP, 3MF, FBX and more) and **no libf3d, libf3d-dev or f3d library package at all** (`apt-cache search f3d`, `dpkg -L f3d`: no `.so`, no headers). A front end on libf3d needs our own libf3d package.
- The edition's stereo work on F3D is three patches in the build tree (`render.stereo` through VTK's quad buffer, the per-eye shear, one eye's size in a stereo GLX window); no F3D package is in the published pool. The metas of the maker, designer and scientist roles recommend Debian's stock `f3d`.

## CloudCompare in the rig (stereo, both eyes and the 2D control)

1. Rig as the [proof-rig skill](../stereo-proof-rig/SKILL.md) says, with `QT_QPA_PLATFORM=xcb`, the render node and `XwaylandEisNoPrompt=true`. Start `CloudCompare FILE.ply`, press Return on the PLY dialog, capture with `capture.py` (a pair is twice the output's width).
2. The stereo action is the last button of the left toolbar (`actionEnableStereo`, F10 in the program). Its dialog offers Red-Blue, Blue-Red, Red-Cyan, Cyan-Red, NVidia Vision and Generic stereo display (the program's strings also hold Oculus; the first four and NVidia Vision were seen on screen).
3. Measured: the anaglyph modes draw one flat picture (the capture is one output wide, no declaration), which the edition's single-output rule removes from our build. NVidia Vision answers `Quad Buffered Stereo not supported` and goes to exclusive full screen, although the same stack runs `glxgears -stereo` as a pair (capture two outputs wide, left and right differing, `_KDE_NET_WM_STEREO_CONTENT` 3).
4. Lead, not proven: Qt's own example says `QSurfaceFormat::StereoBuffers` must be set on the default format, "just doing it on the widget is not enough"; Qt's GLX log (`QT_LOGGING_RULES="qt.qpa.gl=true"`) showed no stereo option in either requested format.

## Slicers, Qt Quick 3D

- PrusaSlicer 2.9.6, Cura 5.0.0 and MeshLab 2025.07 are in Debian testing; a string scan of their packages finds no GL_STEREO, quad buffer, anaglyph or stereo mode. OrcaSlicer and Bambu Studio are not in Debian.
- Qt Quick 3D (Debian 6.11.2) carries multiview rendering (`mainPassViewCount`, `multiview_dependent` shader uniforms, "Multiview rendering requires explicit cameras"), made for XR; whether a flat View3D can use it for a side-by-side pair is open.

See also [stereo-window-3d-area](../stereo-window-3d-area/SKILL.md) for the declared area, [stereo-pictures](../stereo-pictures/SKILL.md) for the thumbnail pair's mark, [stereo-two-cameras](../stereo-two-cameras/SKILL.md) for the cameras.
