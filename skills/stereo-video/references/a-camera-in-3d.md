# A camera in 3D: establish the capture and proof prerequisites

**For contributors adding stereo capture to Kamoso: verify the installed camera policy, media path and isolated desktop before changing the viewfinder.**
Checked on 2026-11-22 against Kamoso 26.04.0 and the edition's first default-camera patch.
The installed stereo-layer 1.23.2 now supports the shared input list and native-size viewfinder prototype.
The prototype has an AMD Stereo KWin capture and native conversion tests; this does not establish completed camera recording or publication.

## Preparation that was run

1. Read the archive's `Packages` and `Sources` stanzas for Kamoso.
   Resolve the binary through `Filename` and the source files through `Directory` and `Checksums-Sha256`.
   Verify every named file's hash, list the Debian archive with `tar tf`, and read its `debian/patches/series` and changelog.
   The checked package `26.04.0-1+stereo3d1+lc1` has one patch, `0001-follow-the-session-default-camera.patch`; this establishes default-camera selection, not stereo capture.
2. Configure the disposable environment with the required Debian snapshot, the edition's signed archive at priority 1001, the accepted round's indexed pool at the same priority, and deb-multimedia's signed archive.
   Record the deb-multimedia InRelease hash and date on every run because that archive moves independently of Debian's snapshot.
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
The audited Camera 0.1.1 holds 22 literal entries and omits temporal packings.
The repair enumerates all 27 entries from the installed 1.23.2 policy and tests count, IDs and ordering against that library.
The current shared policy exposes `stereo_policy_input_format_count()` and `stereo_policy_input_format_at()` in `stereo-policy.h`.
Verify that the selected development package actually exports those APIs before depending on them.
A newer checkout's header is not evidence that the published library provides it.
In a follow-up measurement, the accepted pool had no stereo-layer binary or source entry, so the combined archives still selected published `1.22.0-1+lc1`.
That package's checked headers and the policy library's dynamic symbol table contain neither enumeration function; its picture header also lacks `fromViewsInTurn`.
Its JPS and MPF descriptor encoder declarations and exported functions are present.
Do not compile against a development checkout to hide a missing accepted dependency.

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
On the installed GStreamer 1.28.9 elements, x264 passed the caps through H.264 parsing to Matroska and wrote frame-packing SEI type 3, interpretation 1; Matroska contained StereoMode 1.
With the same declared input, the VA-API and NVENC H.264 elements produced Matroska StereoMode 1 but no frame-packing SEI.
The MP4 muxer produced no `st3d` box with any of the three encoders.
These are element measurements, not a successful recording implementation.
Preserve the failing rows and implement the missing mark at the owning encoder or muxer boundary; never repair the completed camera film.

## Photo and video writer ownership

The shared policy's `stereo-jpeg.h` provides `stereo_jps_encode()` and `stereo_mpf_encode_pair()` for the format descriptors.
The Qt layer's `Picture::saveCorrection()` edits metadata in an existing file; it is not a fresh camera-photo encoder.
Before implementing new capture saving, inspect the installed KImageFormats JPS/MPO writers and verify a complete writer-to-reader round trip.
Do not call a metadata-correction API a complete camera writer.

The specifications to check are H.264 Annex D frame packing arrangement syntax and semantics, CIPA DC-007 for MPF index and attributes, the VRex JPS descriptor, [RFC 9559 section 5.1.4.1.28.3](https://www.rfc-editor.org/rfc/rfc9559.html#section-5.1.4.1.28.3) for `StereoMode`, and Spherical Video V2 for MP4 `st3d`.
RFC 9559 section 18.10 also defines stereoscopic display dimensions.
Marks must be written by the encoder and muxer during recording; correcting the completed movie does not prove capture preserves its layout.
Parser and independent-reader evidence for these camera paths remains outstanding.

## A native-size viewfinder

1. Use the Camera page's V4L2 identity and packing key.
   PipeWire may expose the path as `object.path=v4l2:/dev/videoN` rather than `api.v4l2.path`; handle the same two properties the Camera page reads.
2. Feed GStreamer's appsink into the shared `Stereo::Picture` conversion, then a `QVideoSink`.
   Mark its canonical frame side by side and select Qt VideoOutput's explicit full-side-by-side interpretation.
   The word full describes the layout: a half-width source eye stays half width.
3. Let the edition's Qt VideoOutput own the declared child surface and the hole in its ordinary parent.
   Use the shared `Enable3DAction`; retain the original sink for 3D off.
   Keep the window alpha-capable so enabling the child later can open the hole.
4. A temporal source needs an ordinal from the source, not a counter of received frames.
   Accept an even first frame followed immediately by its odd partner; a gap or discontinuity invalidates a pending pair.
   Refuse an unknown ordinal instead of reversing the eyes after a dropped frame.
   The Camera page must still list temporal choices even if its own preview cannot preserve that ordinal; keep its preview refusal visible.
5. Stop and recreate the camera wrapper when switching sink types, and remove the old bus watch through `gst_bus_remove_watch`.
   A watch created by the render thread can belong to another GLib context, so `g_source_remove(id)` on the GUI thread is not reliable.

The measured native test sends nonuniform pixel patterns through appsrc and appsink for both eye orders, side-by-side and top/bottom, two native eye widths, and caps-declared inputs.
It compares every resulting pixel and the exact output size.
A separate temporal test covers starting halfway through a pair, gaps, discontinuities, missing ordinals and reversed input order.
The initial compositor capture recorded one child declaration and 18 identical 1280-by-480 buffers, with 640-by-480 eyes.
A fresh replay also reads the synthetic camera through an independent PipeWire client and compares every RGB pixel with each submitted buffer: zero differ.
Real input events switch the shared action off and on; both sinks remain live and the settings persist.
The strict window comparison still finds one differing pixel per eye, including between two separate runs of the published camera.
That control failure has no established cause and the zero-difference requirement remains failed.
The complete packing, GPU, recording and publication matrix remains to be run.

## Proof still required

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
  **Fix:** include the accepted round's indexed pool at the edition's priority alongside the published archive.
  **How found:** `apt-cache policy` plus `apt-get -s --no-install-recommends install kwin-wayland` exposes the direct chain through `kwin-common`; recommendations are not the cause.
  The corrected preflight selected IconThemes `6.32.0-1+stereo3d1+lc1` and KWin `4:6.7.4-2+stereo3d64+lc1`; both the minimal KWin and complete camera-rig dependency simulations returned zero.
  A subsequent real install and upgrade completed with no packages left to upgrade; the stereo capture still has its own separate checks.
- **Symptom:** the corrected rig resolves, but the required shared camera-packing enumeration still cannot be used.
  **Cause:** the accepted pool has no stereo-layer entries and APT selects the older published layer without those APIs.
  **Fix:** install the checksum-pinned 1.23.2 siblings before build dependencies and pass the same siblings to the link gate, at a priority above the published archive; do not substitute a work-tree library.
  **How found:** both pool indexes match their Release hashes, their layer entry counts are zero, and the selected package's header and dynamic-export audits agree that the functions are absent.
- **Symptom:** apt stops at `libavcodec63` requiring a newer `libaom3`.
  **Cause:** the test environment omitted deb-multimedia.
  **Fix:** add its signed archive alongside the edition pin.
  **How found:** the failed solver chain and a successful Kamoso dependency simulation after adding that archive.
- **Symptom:** an upstream path search returns no commits.
  **Cause:** the queried capture path omitted its `video` directory.
  **Fix:** read the release archive's file list and query the actual path.
  **How found:** `tar tf` identifies `src/video/webcamcontrol.cpp`; an empty query is not evidence that the file exists or is unchanged.
- **Symptom:** the original viewfinder fails at `gst_bin_add_many`, because `glupload` is null.
  **Cause:** a no-recommends rig omitted `gstreamer1.0-gl`; the published camera fails there too.
  **Fix:** include the GL plugin package and require a functioning published video control before comparing pixels.
  **How found:** actual 3D-off switching and the published camera log, not the stereo viewfinder's successful capture.
- **Symptom:** a synthetic encoder probe cannot link `videotestsrc` with side-by-side caps.
  **Cause:** that source advertises mono; declaring its output in the source caps filter is refused before encoding starts.
  **Fix:** generate the intended packed test frame, then set its multiview caps at the interpretation boundary with `capssetter` or appsrc.
  **How found:** the failed link occurred before the encoder; the corrected probes completed and exposed distinct SEI and container outcomes.

- **Symptom:** a switch test expects pure blue but reads RGB (1, 0, 255).
  **Cause:** the independently captured camera input already has that value; the test assumed the generator's nominal color survived its format conversion.
  **Fix:** read the same camera through an independent client and compare exact source values, while retaining the separate expected eye identity check.
  **How found:** the independent source and every submitted native buffer have the same hash and zero differing RGB pixels.
  This fixture correction does not waive the separate zero-difference window comparison.
