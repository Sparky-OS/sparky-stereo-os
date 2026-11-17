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
3. Run the real path without Dolphin: a small program calling `KIO::filePreview(items, QSize(256, 256), &plugins)` with `plugins = KIO::PreviewJob::defaultPlugins()` (what Dolphin uses until the person saves another list: `kfileitemmodelrolesupdater.cpp`, dolphin 26.08.0), offscreen, `HOME` and `XDG_CACHE_HOME` in scratch, inside `dbus-run-session`, with a passwd entry for the user. It prints GOT or FAILED per file and leaves the thumbnails in the freedesktop cache.
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

## F3D in stereo: our packages (ORDER 17, milestone 2)

Written 2026-11-17 from the build of `f3d` 3.5.0+dfsg-3+stereo3d1 and the new `libf3d1` and `libf3d-dev`.

- **The source:** Debian's own `f3d` source package (3.5.0+dfsg-3), five patches added to `debian/patches`, taken from branch `order17-stereo` of our F3D fork on upstream's v3.5.0: `render.stereo` (VTK's quad buffer through a stereo GLX window, declared by our Mesa as one full side-by-side surface under Stereo KWin through Xwayland), the per-eye shear, the size of one eye, the eye taken from the left-eye flag or from the caller, and the pair in an image (`renderToImage` with `render.stereo` returns left and right side by side).
- **Why 3.5.0:** it is the release Debian testing ships; the three older patches applied to it with `git am -3` without a conflict.
- **libf3d:** Debian builds F3D with `BUILD_SHARED_LIBS=OFF` and removes `/usr/lib`. Ours builds it ON, installs the default components into `debian/tmp`, the `sdk` component beside them (`cmake --install obj-... --component sdk`; it is `EXCLUDE_FROM_ALL`, so `dh_auto_install` skips it), and splits `libf3d1` and `libf3d-dev`.
- **The pair thumbnail:** `f3d-thumbnail-pair PLUGIN SIZE INPUT OUTPUT`, a small libf3d program in the package. It sets `render.stereo` on an offscreen engine and renders each eye in turn from a parallel, sheared camera (never a rotation of one camera); the picture is SIZE by SIZE/2, left eye first. libf3d's PNG writer keeps no text chunk (`image::setMetadata` is not written), so the program inserts the `tEXt` chunk `X-KDE::Stereo3DLayout=sideBySideLeftFirst` itself (zlib's crc32). The package rewrites the `Exec` line of F3D's five `.thumbnailer` files to call it.
- **Measured:** the pair of three squares at known depths: near -7.27 px, at the focal plane -0.08 px, far +5.00 px of horizontal disparity between the eyes, vertical disparity at most 0.17 px (`disp.py`), so the sign and the zero plane are those of two parallel sheared cameras. The numbers were not predicted: the helper's camera is oblique.
- **KIO carries the key:** (measured twice) a standard thumbnailer's PNG text chunk survives into the freedesktop cache (measured with a fake thumbnailer in the rig: the cached file holds the key), so no KIO change is needed for the pair; it shows as a pair where the file manager shows pairs and as its left half elsewhere.
- **MIME types:** the package `sparky-stereo-mime-models` defines `model/x-ply`, `model/x-gaussian-splat`, `model/x-spz`, `model/x-pts`, `model/x-fbx`, `model/vnd.collada+xml`, `model/x-off`, `model/x-draco`, `model/step`, `model/x-brep`, with F3D's `application/vnd.*` names as aliases. **KIO does not follow an alias:** it looks a thumbnailer up by the file's canonical type name, so the package also rewrites the `MimeType=` of F3D's `.thumbnailer` files to carry the canonical names beside the aliases. Search shared-mime-info's master first: STEP, BREP, IGES, OBJ, 3MF, glTF and STL are there already (STEP and BREP are not in the release Debian testing ships, so they are carried as they are upstream); PLY, splat, SPZ, PTS, FBX, COLLADA, OFF and Draco are not.

### Traps

- **Symptom:** a file typed `model/x-ply` shows no thumbnail although F3D's thumbnailer lists `application/vnd.ply` (`supported: false`, FAILED, no process started). **Cause:** `FilePreviewJob::preparePluginForMimetype` finds the plugin by the type's own name and its ancestors, never its aliases. **Fix:** list the canonical name in the thumbnailer's `MimeType=`. **Found by:** the thumbnail run printing `supported: false` for the new types while the old fake thumbnailer (on the canonical name) had worked.
- **Symptom:** the thumbnail is a pair but the cache file has no `X-KDE::Stereo3DLayout`. **Cause:** libf3d's `image::save` writes no PNG text chunk. **Fix:** insert it in the program. **Found by:** `textkeys.py` on the helper's own output (`{}`).
- **Symptom:** every thumbnail FAILED with a permission error on `thumbnails/large`. **Cause:** a cache folder in the mounted work folder was made earlier by a root run. **Fix:** the cache in the container's own `/tmp`, as the user.
- **Open, not solved (window):** under Stereo KWin `f3d --stereo` is a declared stereo window (capture two outputs wide, `_KDE_NET_WM_STEREO_CONTENT` 3) but the two halves are identical. Narrowed: our Mesa blits an FBO to `GL_BACK_LEFT` red and `GL_BACK_RIGHT` blue correctly (`blitstereo.c`, left red, right blue); VTK's window has the state it expects (crystal eyes, double buffered, `BlitToHardware`); F3D's renderer runs once per eye, left then right, with the camera's left-eye flag toggling; the shear works (at 20 degrees the near and far squares move) but the picture in both buffers is the right eye's. The left eye is lost between VTK's `StereoMidpoint` blit and the hardware blit. Next: read what F3D's render passes bind and draw at the end of each eye.

- **Symptom:** `dpkg-source: error: ... patch ... subprocess failed` with "Reversed (or previously applied) patch detected" at `dpkg-buildpackage`. **Cause:** a prep script appended the patch's name to `debian/patches/series` twice (it had run once before and failed after the append). **Fix:** make the script idempotent, `awk '!seen[$0]++'` on the series. **Found by:** the doubled "applying" line in the build log.
- **Symptom:** a script in a Debian base container says `python3: not found`. **Cause:** `debian:testing` has no Python. **Fix:** install `python3-minimal` first, or write the edit as a shell step.

## CloudCompare in the rig (stereo, both eyes and the 2D control)

1. Rig as the [proof-rig skill](../stereo-proof-rig/SKILL.md) says, with `QT_QPA_PLATFORM=xcb`, the render node and `XwaylandEisNoPrompt=true`. Start `CloudCompare FILE.ply`, press Return on the PLY dialog, capture with `capture.py` (a pair is twice the output's width).
2. The stereo action is the last button of the left toolbar (`actionEnableStereo`, F10 in the program). Its dialog offers Red-Blue, Blue-Red, Red-Cyan, Cyan-Red, NVidia Vision and Generic stereo display (the program's strings also hold Oculus; the first four and NVidia Vision were seen on screen).
3. Measured: the anaglyph modes draw one flat picture (the capture is one output wide, no declaration), which the edition's single-output rule removes from our build. NVidia Vision answers `Quad Buffered Stereo not supported` and goes to exclusive full screen, although the same stack runs `glxgears -stereo` as a pair (capture two outputs wide, left and right differing, `_KDE_NET_WM_STEREO_CONTENT` 3).
4. Lead, not proven: Qt's own example says `QSurfaceFormat::StereoBuffers` must be set on the default format, "just doing it on the widget is not enough"; Qt's GLX log (`QT_LOGGING_RULES="qt.qpa.gl=true"`) showed no stereo option in either requested format.

## Slicers, Qt Quick 3D

- PrusaSlicer 2.9.6, Cura 5.0.0 and MeshLab 2025.07 are in Debian testing; a string scan of their packages finds no GL_STEREO, quad buffer, anaglyph or stereo mode. OrcaSlicer and Bambu Studio are not in Debian.
- Qt Quick 3D (Debian 6.11.2) carries multiview rendering (`mainPassViewCount`, `multiview_dependent` shader uniforms, "Multiview rendering requires explicit cameras"), made for XR; whether a flat View3D can use it for a side-by-side pair is open.

See also [stereo-window-3d-area](../stereo-window-3d-area/SKILL.md) for the declared area, [stereo-pictures](../stereo-pictures/SKILL.md) for the thumbnail pair's mark, [stereo-two-cameras](../stereo-two-cameras/SKILL.md) for the cameras.
