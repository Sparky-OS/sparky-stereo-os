# A camera in 3D: establish the capture and proof prerequisites

**For contributors adding stereo capture to Kamoso: verify the installed camera policy, media path and isolated desktop before changing the viewfinder.**
Checked on 2026-11-22 against Kamoso 26.04.0 and the edition's first default-camera patch.
This is a source audit and a measured dependency preflight, not a completed stereo camera implementation.
No capture, encoder, PipeWire layout round trip or compositor pixel comparison was completed in this audit.

## Preparation that was run

1. Read the archive's `Packages` and `Sources` stanzas for Kamoso.
   Resolve the binary through `Filename` and the source files through `Directory` and `Checksums-Sha256`.
   Verify every named file's hash, list the Debian archive with `tar tf`, and read its `debian/patches/series` and changelog.
   The checked package `26.04.0-1+stereo3d1+lc1` has one patch, `0001-follow-the-session-default-camera.patch`; this establishes default-camera selection, not stereo capture.
2. Configure the disposable environment with the required Debian snapshot, the edition's signed archive at priority 1001 and deb-multimedia's signed archive.
   Keep package downloads separate from running the camera or compositor.
3. Run `apt-cache policy kamoso kwin-wayland libkf6xmlgui6 libkf6iconthemes6 libkf6iconwidgets6` and `apt-get -s --no-install-recommends install kwin-wayland`.
   The expected result is dependency resolution with the edition's compositor and stereo libraries selected.
   Retain apt's exit status and its dependency chain, not just an absence of `Remv` lines.
4. Resolve the complete camera, compositor and metadata-reader environment too.
   A successful simulation for Kamoso alone does not prove that its compositor can be installed.

## Camera identity and packing

The Camera page's `src/camerastore.cpp` uses QSettings in IniFormat/UserScope with organization `sparky-stereo-camera` and application `cameras`.
Its group is V4L2 `bus_info`, then `|`, then the card name, with slash and backslash replaced by underscores.
The `packing` key holds a stereo-layer input ID.
Read the same identity; a PipeWire numeric node ID is not that persistent key.
The Camera page's own [reference](../../kde-desktop-defaults/references/camera-page.md) describes the separate session default and its preview.

Do not copy the Camera page's `packings.cpp` list into another application.
The audited version holds a literal list and omits temporal packings.
The current shared policy exposes `stereo_policy_input_format_count()` and `stereo_policy_input_format_at()` in `stereo-policy.h`.
Verify that the selected development package actually exports those APIs before depending on them.
A newer checkout's header is not evidence that the published library provides it.

## Boundaries still requiring runtime proof

| Boundary | Inspect and measure |
| --- | --- |
| V4L2 or PipeWire to GStreamer | Actual source caps, camera identity and the saved packing; no application-specific shape guess |
| Unpacking | Use shared policy and conversion; each output eye equals its source samples, without a resize |
| Viewfinder | Kamoso's drawing on one declared child surface beneath a hole in the ordinary window; controls and overlays stay in the ordinary surface |
| Effects | Apply the effect separately to each eye, or explain the refusal where the effect is chosen |
| Encoder | Read negotiated multiview caps immediately before and after the actual encoder; inspect the encoded SEI |
| Muxer | Read the container's own stereo field independently of the SEI |
| Published camera | Read the negotiated PipeWire format with another client, including multiview mode, flags and view count |

Kamoso's capture implementation is `src/video/webcamcontrol.cpp`, not `src/webcamcontrol.cpp`.
Search upstream history on the real path: a query on a nonexistent path returns an empty result too.
The inspected release uses GStreamer; an FFmpeg encoder fix does not establish that a GStreamer VA-API or NVENC element writes the same mark.
The [GPU encoder reference](gpu-encoder-marks.md) gives the FFmpeg boundary and its proven scope.
No GStreamer caps-loss location was measured in this audit.

## Photo and video writer ownership

The shared policy's `stereo-jpeg.h` provides `stereo_jps_encode()` and `stereo_mpf_encode_pair()` for the format descriptors.
The Qt layer's `Picture::saveCorrection()` edits metadata in an existing file; it is not a fresh camera-photo encoder.
Before implementing new capture saving, inspect the installed KImageFormats JPS/MPO writers and verify a complete writer-to-reader round trip.
Do not call a metadata-correction API a complete camera writer.

The specifications to check are H.264 Annex D frame packing arrangement syntax and semantics, CIPA DC-007 for MPF index and attributes, the VRex JPS descriptor, [RFC 9559 section 5.1.4.1.28.3](https://www.rfc-editor.org/rfc/rfc9559.html#section-5.1.4.1.28.3) for `StereoMode`, and Spherical Video V2 for MP4 `st3d`.
RFC 9559 section 18.10 also defines stereoscopic display dimensions.
Marks must be written by the encoder and muxer during recording; correcting the completed movie does not prove capture preserves its layout.
Parser and independent-reader evidence for these camera paths remains outstanding.

## Proof to prepare after dependencies resolve

Use an isolated PipeWire instance and a synthetic camera, with different colors and address patterns in the two eyes.
Enumerate inputs from the installed layer's complete list and test both eye orders.
Capture the committed viewfinder buffers and both compositor eyes, count declarations and compare samples before compositor scaling.
Use the [proof rig](../../stereo-proof-rig/SKILL.md) for the one-resize comparison and the unchanged 2D window control.
Check the saved photographs with an independent metadata reader and the layer's own reader; check each video stream and container separately.
Record an unmarked control that the mark checker rejects.
The v4l2loopback bridge needs a separate virtual-machine test; it is not a reason to load a kernel module on the working desktop.

## Traps from the preflight

- **Symptom:** Kamoso alone resolves, but installing `kwin-wayland` fails.
  **Cause:** in the measured snapshot, XMLGUI 6.32 requires IconThemes at least 6.32, while priority 1001 selects the edition's IconThemes 6.30 build.
  **Required fix:** qualify an edition package set compatible with that snapshot, preserving the stereo changes.
  **How found:** `apt-cache policy` plus `apt-get -s --no-install-recommends install kwin-wayland` exposes the direct chain through `kwin-common`; recommendations are not the cause.
  This fix was not built or tested by the camera audit.
- **Symptom:** apt stops at `libavcodec63` requiring a newer `libaom3`.
  **Cause:** the test environment omitted deb-multimedia.
  **Fix:** add its signed archive alongside the edition pin.
  **How found:** the failed solver chain and a successful Kamoso dependency simulation after adding that archive.
- **Symptom:** an upstream path search returns no commits.
  **Cause:** the queried capture path omitted its `video` directory.
  **Fix:** read the release archive's file list and query the actual path.
  **How found:** `tar tf` identifies `src/video/webcamcontrol.cpp`; an empty query is not evidence that the file exists or is unchanged.
