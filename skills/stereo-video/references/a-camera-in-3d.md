# A camera in 3D: establish the capture and proof prerequisites

**For contributors adding stereo capture to Kamoso: verify the installed camera policy, media path and isolated desktop before changing the viewfinder.**
Checked on 2026-11-23 against Kamoso 26.04.0 and the edition's first default-camera patch.
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
The first strict window comparison found one differing pixel per eye, including between separate runs of the published camera.
Five published control pairs with ordinary hash randomization reproduced differences at two toolbar text positions.
With `QT_HASH_SEED=0` set only in the fixture, all five control pairs, 3D off versus published, and the ordinary controls with 3D on versus off compared at zero differing pixels. Nothing was masked or tolerated.
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

## Native samples, separate views and deterministic text

`Picture::fromPackedImage()` reconstructs interleaved pictures for ordinary picture consumers. Passing its `sideBySide()` result directly to a stereo surface therefore expands rows, columns, checkerboard and quincunx input.
Use `cropEyes(picture, picture.left.size()).packed` to select the original native samples with no zoom or pan. Apply the camera's mirror separately to the resulting views, after this selection; modifying the intermediate views first prevents the layer from recognizing their original sample phases.
Reject dimensions for which the library would fall back to resizing, with an explanation. The address-coded pipeline test must check native dimensions and every sample, including mirroring; constant red and blue alone would miss reconstruction.

A GStreamer `separated` buffer carries individual `GstVideoMeta` records with view IDs. Map IDs 0 and 1 with `gst_video_frame_map_id`, require exactly two views and give them to `Picture::fromViewsInTurn()` in the caps' declared order. Missing second-view metadata must produce the camera's visible refusal. The normal RGBA passthrough route retains these records; adding an unnecessary caps feature can instead stop negotiation before a frame reaches the application.
Test native caps against a contradictory saved packing. Test temporal input through appsrc/appsink with source ordinals, gaps, discontinuities and missing ordinals, as well as calling the pairing helper directly.

The Camera page's list remains complete even when its preview cannot show a source. Test the actual QML page against the synthetic camera for every installed policy entry: the preview button, its visible refusal and the ordinary Not 3D choice. A warning available only by hovering over a disabled control is too easy to miss. The temporal preview still needs its source ordinal; that work is separate from keeping the whole list.
Dynamic labels also need extraction: generate the xgettext input from `stereo_policy_input_format_count()` and `_at()` on the installed library. A plain scan of `i18n(format->text)` does not discover the 27 labels. Compare the generated catalogue with the runtime list; do not maintain a second literal packing list for translations.

### Toolbar text that differs by one sample

**Symptom:** two launches of the same published camera differ by one RGB sample in the Record a Video or Take a Picture toolbar label; comparisons between builds vary similarly.
**Cause:** Qt Quick's distance-field glyph atlas allocation depends on QSet iteration. Qt's randomized hash seed changes that order and thus glyph texture coordinates. In the measured renderer this changes a rounding result at a text edge; that last floating-point mechanism is an inference from the source and controlled seed comparison, not a captured shader trace.
**Fix:** set `QT_HASH_SEED=0` in the isolated test environment, for both published and changed programs. Do not set it as a product default or weaken pixel equality.
**How found:** five published pairs under each seed policy, followed by off/published and on/off comparisons, with all samples retained. Qt 6.11.2's [populate implementation](https://github.com/qt/qtdeclarative/blob/v6.11.2/src/quick/scenegraph/qsgadaptationlayer.cpp) collects new glyphs into a QSet; [requestGlyphs](https://github.com/qt/qtdeclarative/blob/v6.11.2/src/quick/scenegraph/qsgrhidistancefieldglyphcache.cpp) allocates atlas rectangles in its iteration order.


## Fresh MPO and JPS captures

The camera's latest normalized pair is given to QImageWriter with Stereo3DLayout=sideBySideLeftFirst. The edition's KImageFormats writers call the shared descriptor writers; do not assemble MPF or JPS bytes in Kamoso. MPO is the study's first/default choice; JPS is selectable. Use QSaveFile for a fresh local capture, and complete the temporary file before starting KIO for a remote destination. Preserve jpegenc's default quality (85 in the measured rig). Camera changes invalidate the retained pair. A missing or unwritable writer reports failure.

The real shutter and burst routes produced MPO disparity views (MPF 0x020002, two images, BaseViewpointNum=1) and JPS left-first side-by-side. ExifTool and KFileMetaData identify the marks; the layer returns two native 640×480 views. Native writer tests also reject malformed pairs and leave an existing destination unchanged.

Trap: a successful QSaveFile capture could not be reopened in the rig. Cause: the virtual-camera open interposer forwarded a mode only for O_CREAT, while Qt used O_TMPFILE. Fix: forward the third argument for either flag. Found by a real shutter capture (permission denied), source inspection and the repeated readable capture; changing product permissions would have concealed the fixture defect.

Declaration-library siblings are pinned at 1.12.2 beside layer 1.23.2. Earlier kam61-rig:1 used 1.12.1. Both are joint round dependencies. The local source-ordinal pairing is pending engine row 839; this camera work does not implement that row.


## Recording marks and a sustained camera fixture

x264enc takes side-by-side multiview caps and writes frame-packing arrangement SEI. qtmux needed an owning-element change to emit st3d in its visual sample entry; the source is deb-multimedia gst-plugins-good1.0-dmo 1.28.9-dmo1. Both container routes are written once, then checked independently with FFmpeg trace_headers and mkvinfo or a recursive MP4 box parser. Native camera pairs remain 1280×480 (640×480 per eye). The automatic audio source is retained; the isolated test selects audiotestsrc through GStreamer's feature rank, never a station sound device.

The MP4 preflight reads the muxer's writes-st3d capability. VA-API and NVENC H.264 and HEVC currently fail the SEI measurement, so their recording choices refuse before creating a file. Hardware repairs belong in gst-plugins-bad1.0-dmo, not in a later rewrite of the film. The H.265 codecparser currently has no frame-packing message writer, a shared boundary those encoder repairs must address.

Trap: the static viewfinder looked correct but recording received no new frames. A standalone 120-buffer PipeWire consumer, without Kamoso, also stalled on the fixture's default shared pool. With pipewiresink use-bufferpool=false the same consumer reached EOS at 120 frames. The producer then copies unchanged samples into PipeWire-owned buffers. Keep this fixture setting and a sustained-frame control; a single screenshot cannot prove a live source. No camera-pipeline product workaround is needed.

Photo clause audit: CIPA DC-007-Translation-2009 sections 5.2.3.2–5.2.3.3 cover image count and MP entries, 5.2.4.2 MPIndividualNum, 5.2.4.5 BaseViewpointNum, and 6.2.2.2 left-to-right disparity viewpoints. JPS uses the VRex descriptor's stereo type, SBS layout and left-first flag. Video clauses: H.264 Annex D frame packing arrangement; RFC 9559 section 5.1.4.1.28.3 StereoMode; Spherical Video V2 st3d visual sample entry and modes. These marks describe packing, not the person's display geometry.


## Repeated viewfinder and gallery lifetimes

A live fixture exposed failures that a static first buffer did not. Kamoso's sample getter creates and removes a temporary placeholder around its capture request; a synchronous replacement writer therefore loses the file and can notify QML reentrantly. Keep the complete fresh sample write asynchronous, as camerabin was. A QML sample binding must not compare its own value with its source. Gallery GL sink creation belongs on the render thread, and each bus watch must be removed before its PipelineItem is replaced or destroyed. These fixes preserve the original 2D gallery; they are not the stereo effect matrix.

A separate abort at gstqsg6material.cc:497 came from a recreated Qt scene-graph material lacking its caps. Upstream already fixed this in Will's [GStreamer MR !12461](https://gitlab.freedesktop.org/gstreamer/gstreamer/-/merge_requests/12461): mark caps changed when allocating each new material. Carry that owning-plugin fix with its credit. The separate pending-caps issue #4944 is already fixed in the measured source. Verify fifty hide/show cycles with live frames and one declaration for each child surface lifetime; one static screenshot cannot exercise this path.

For H.264 (08/2024), frame-packing syntax and semantics are Annex D.1.26 and D.2.26; older editions used D.1.25 and D.2.25. Name the edition when recording a clause.

Preserve and restore Qt's current OpenGL context around each gallery render job. A later stressed run lost the usable rendering context, emitted shader/EGL errors and died; restoring it made the repeated-action control pass. Keep that negative run rather than treating one successful drawer opening as a lifetime proof.

The lifecycle fixture first clicks the real checkbox off and on and checks its pixels. For the remaining cycles it invokes the existing named Qt Enable 3D action through the meta-object API, checks its returned state and persisted setting, and awaits child-surface destruction/new declaration in the Wayland trace. This separates a lifecycle test from fixed pointer coordinates in a scrolling drawer. It changes no product state directly and does not claim fifty pointer clicks.

## Per-eye effects and recording lifecycle evidence

Normalize the camera packing first, then give each native view to a separate ordinary GStreamer effect pipeline with mono caps.
Keep separate filter instances and frame history, and submit the same timestamp to both.
Poll appsink without waiting on the GUI thread; retain only one complete pair in flight.
Join the results only when both are ready and their dimensions still equal the input eye.
Feed this result to the viewfinder and the camera's photo/recording path.
Do not apply a spatial filter to the packed frame before splitting it.

The camera's 31 existing choices now pass the native matrix, enumerated from its QML model rather than a second test catalogue.
Pad probes check each eye's input samples and 160×120 dimensions exactly over three frames.
An address-coded bulge control compares the results against separately processed views.
Missing filters name the failed choice, explain the unfiltered view, and remain selectable by name in the stereo picker even when their thumbnail cannot render.
The original flat filter path is retained.

The real camera's grayscale JPS differs from the independent mono-filter/JPS reference in 614,290 decoded pixels before this change and zero afterward.
The live bulge pair also equals its reference, but the static source does not separate that case from no effect; the address-coded native control does.
Both saved images retain their JPS marks and native 640×480 eyes.
Do not interpret an ideal grayscale formula as the GStreamer oracle: its YUV conversion can leave a one-channel rounding difference.
Compare actual independent filter output exactly.

For a suspected missing recording, acknowledge the existing recording action before expecting a file and retain creation, close, rename and deletion events in the private video folder.
Keep the request, temporary name, EOS completion and final destination together.
A coordinate click that never reached Record is not evidence of a deleted film.
The repeated probe completes fifty MP4 starts/stops on two pinned CPUs while a test-only timer gives the application's main thread 60 ms of work per 150 ms.
Fifty marked films and fifty final renames, with no completed file deleted, did not reproduce the earlier two missing films.
This is explicitly not a fix for those uninstrumented observations.

Freeze launcher scripts while they run.
Editing a shell script that Bash is still reading can make its next read repeat a command: one development probe restarted its container and overwrote lifecycle logs after fifty recordings.
Its files did not substitute for the lost trace; a fresh run retained the complete trace.
No extra host stress is enabled by default.
Repeated GL cases use NVIDIA through zink or software rendering; the display-driving AMD card is not a soak device.
Record the actual renderer: these application tests used zink on the RTX 3060, while the rig's KWin fell back to QPainter.
They do not establish stereo output captures on that compositor.


## Publishing the processed camera through PipeWire (2026-11-23)

The camera's processed native-size pair is published by pipewiresink in provide mode, media.class Video/Source and media.role Camera.
Its node name starts with kamoso.stereo.; Kamoso excludes these nodes from capture inputs, including another instance's output.
Disable 3D, a flat input, source replacement and closing the program remove the node.
A failed publisher is named in the viewfinder while local capture keeps working.
The pair is copied unchanged to RGBA buffers, with two views, side-by-side mode and no half-aspect or eye-order flag.
It is the same post-effect pair used by photos and recording, not the unprocessed input camera.

**Lost layout at the adapter:** the source caps said side-by-side but an independent native PipeWire consumer read mode 0 and views 0.
PipeWire 1.6.9's src/gst/gstpipewireformat.c converted neither multiview mode, flags nor views in either direction; current main and its history/MR/issue searches supplied no fix.
The repair belongs to PipeWire's own GStreamer adapter, not a private node tag or an application format guess.
The pipewire-stereo-61 recipe retains Debian 1.6.9-2 and adds that conversion; Kamoso requires its new gstreamer1.0-pipewire binary.
Public enum/flag values are compile-time checked against both libraries.
Native checks cover all twelve defined modes and nine flag combinations in both directions (108 rows).
This proves format fields, not temporal buffer metadata or partial flag-mask negotiation.
The camera publishes complete SBS pairs only.

**Independent reader:** request RGBA and native dimensions through pw_stream, without requesting multiview fields; parse the negotiated SPA raw format, then read ten buffers.
Before the adapter fix the reader rejects mode 0/views 0; after it reads mode 3/flags 0/views 2 and every sample matches the source.
Exercise the shared Enable 3D action off/on and program exit, checking node removal/recreation and the input model (the output never appears as an input).
An unrelated device removal must not clear the currently selected camera: check the identity before changing selection in DeviceManager::deviceRemoved.

**Fixture traps:** a publisher node can take longer than a fixed startup sleep under shared station load; wait for the actual node.
An unconstrained Gst consumer can report target not found even when the publisher exists; give its raw sample format and dimensions.
Native SPA parsing is independent of the adapter under test.
Query a render node's group inside the CDI container when the tool's own namespace has no /dev/dri, then use that group with SYS_NICE and the installed KWin.
Client zink rendering still does not prove KWin's renderer: in this probe KWin reports EGL_NOT_INITIALIZED and falls back to QPainter.


**Concurrent effect construction:** a later fresh replay aborted in Cartoon's f0r_construct with a double free, although earlier effect matrices passed. frei0r.hpp clears, swaps and rebuilds a plugin-global parameter vector for every instance.
Its metadata must instead be built once by the registration instance and remain immutable; parameter values and their pointers stay per instance.
A deterministic paused-constructor check reads zero public parameters before and the expected two after; 2,000 constructions on two threads retain independent values, and the unchanged 31-effect matrix passes.
This is distinct from sharing one instance's frame history between threads (related upstream issue 188).
The owning frei0r-dmo source is 1:3.7.1-dmo1, not Debian's same-number release; query the installed binary's source before apt-get source.
The recipe successor is 1:3.7.1-dmo1+stereo3d1+lc1.
Native tests compile the three C++ choices against the corrected header; the full package must rebuild all plugins.
An isolated FREI0R_PATH must include the system directory after the new plugins to keep ordinary C plugins available.
Check the header's historical frame-parallelism fix separately: it does not repair metadata rewritten during construction.

**Measure ordinary recording before selecting stereo codecs:** published
Kamoso names its film .mkv but camerabin writes Ogg, Theora quality 48 and Vorbis quality 0.3.
Read the bytes and negotiated caps, not the suffix.
Theora/Ogg cannot provide the required H.264 frame-packing SEI plus Matroska StereoMode or MP4 st3d.
The marked route therefore uses H.264, keeping quality-based encoding, ordinary x264 quality defaults and full chroma instead of forcing zerolatency and I420.
Theora and x264 quality numbers are not equivalent scales.
Matroska can keep Vorbis; mp4mux cannot, so the MP4 choice names its AAC difference.
Remove extra audio resampling and test fixed source rate/channel combinations with an actual media reader.
Use a multiqueue for the two branches: x264's lookahead exceeds a plain audio queue's usual limit; disabling lookahead changes encoding quality.

**A viewfinder can work while a recording is empty:** the synthetic PipeWire source supplied buffers with GST_CLOCK_TIME_NONE timestamps.
Camerabin's videorate discarded every buffer, then oggmux reported no video headers on EOS.
GST_DEBUG=videorate:6 exposed the cause.
For this synthetic-camera fixture only, set its source's do-timestamp property to use the pipeline clock; leave the published program and its encoding profile intact.
The resulting Ogg can be read back with both audio and video.
This finding does not explain missing files from the separate stereo recorder, whose appsrc already timestamps its pairs.

**Force overload without stressing the desktop:** attach a blocking probe to the recorder's appsrc source pad, enqueue more than its eight-pair guard, then remove the probe.
The earlier guard destroyed the recording; drop whole pairs instead, notify once and keep finalization.
Check a second recording resets the notice.
Pausing immediately after pipeline creation is a bad fixture: a source still transitioning can return FLUSHING rather than exercise back pressure.

**Constant quality can still carry a bitrate ceiling:** x264enc's pass=qual retains its default 2,048 kbit/s VBV cap.
The ordinary Theora quality route has no such ceiling.
Disable it with vbv-buf-capacity=0, then read the actual x264 options in the film: rc=crf and normal lookahead, with no vbv_maxrate.
Looking only at the pass property would miss this restriction on a full stereo pair.


**Keep every recording action acknowledgement:** a final response with
`before=true, checked=false` describes a normal stop, not an automatic start.
Match its serial to the request before diagnosing a toggle.
Inspect the initial state, request the desired state, and repeat each desired state once to prove idempotence.
Consume the serial before invoking a Qt action, which may enter a nested event loop.
Preserve the whole journal rather than only its last reply.
Wait for buffers at the preview sink instead of sleeping after camerabin setup; log pad counts, timestamps and queue/state snapshots to distinguish a stalled stream from a failed action.
Ten fresh first-case ordinary recordings passed with this fixture.
The preceding empty-file stall was not reproduced or called fixed by that result.

**Mono input with Enable 3D still on:** select the saving route from the received frame, not the switch.
Keep mono frames for readiness and use camerabin's ordinary photo and film writers, including its effects and mirroring.
A source classification change rebuilds the source filter; discard the transition frame that still carries the preceding filter.
Stop the recorder that actually started.
The regression is an undeclared mono camera, Enable 3D on, with both photo and film read back: the former source rejected the photo and requested a stereo recording without a pair.

**An installed NVIDIA compositor, separately from its zink client:** the working
CDI route on this rig is `nvidia.com/gpu=all`, SYS_NICE, no added render group and no Mesa override for KWin.
Give only the client Mesa's EGL vendor first, NVIDIA's second, `__GLX_VENDOR_LIBRARY_NAME=mesa`, `MESA_LOADER_DRIVER_OVERRIDE=zink` and `LIBGL_KOPPER_DISABLE=1`.
Read KWin's supportInformation; a zink client proves nothing about its compositor.
For a software scene capture, CDI supplies a render node but `GBM_BACKEND=dri`, Mesa's EGL vendor, `LIBGL_ALWAYS_SOFTWARE=1`, `GALLIUM_DRIVER=llvmpipe` and a bounded LP_NUM_THREADS select llvmpipe.
Without the DRI allocator, EGL did not initialize and KWin fell back to QPainter.
The virtual backend's output allocation can still fail on the NVIDIA render node; its scene captures are not output readback.
Keep that limit explicit.

**A 2D output needs a different witness:** ScreenShot2 returns both scene eyes when a declared child is present, even with stereoOutput=false.
Nest the installed KWin on a separate private compositor, fullscreen on a 1920×1080 2D Wayland output.
Capture that outer compositor, where the inner output is an ordinary undeclared surface.
Record both window/output geometries and renderer strings.
This reads the nested output presented to its parent; it is not a DRM scanout claim.
The left-eye notice is an intentional overlay: read its exact QML bounds, check its visible text and drawn pixels separately, and compare the remaining view with the one source eye.
Never crop a ScreenShot2 stereo pair and call it the actual 2D output.

**A fractional viewfinder edge:** a default 700×525 client creates a
638.666×479 content rectangle.
The parent's fractional hole can cover one column of its child's rounded 639-pixel viewport; this lowered the complete-eye comparison to about 34 dB.
An integral 640×480 fixture (700×526 client) isolates packing/order checks, scoring over 81 dB for the side-by-side source against FFmpeg's one bilinear resize.
This fixture does not repair or certify arbitrary fractional resize boundaries; retain that observed limitation separately.

**Carry the fixture settings into every new launcher:** omitting QT_HASH_SEED from the five-pair wrapper reintroduced changing toolbar glyph samples; omitting the repaired Qt GStreamer plugin reintroduced its known material assertion on hide/show.
Record the actual renderer and loaded dependency, and make the seed part of the session script itself.
A fifty-cycle child-lifecycle row can invoke the same shared action directly; opening the gallery is a separate UI case.
Do not report a successful lifecycle run as proof of unrelated gallery transitions.

**Complete the mirror for the gate's empty-status solve:** an installed builder's prefetch list is not the release gate's dependency closure.
The Camera successor compiled and passed its packing-list and payload checks, then the gate selected `dbus-user-session` and `lsb-base` from frozen Debian instead of the packages the pinned builder already had.
Retain the gate's actual plan, run its unchanged empty-status solver for every predecessor binary of all affected sources, and fetch the union of selected archives.
Authenticate each exact filename, size and hash against the retained signed indexes; do not update the archive date or weaken the gate.
The unchanged Camera gate passed after those two inputs were added.
When later successors become siblings, keep their candidate universe separate from the predecessor universe used for comparison.

**Keep a successful source closure, not its disposable build tree:** take the binary and metadata names from the successful build record, then follow every file named by the source descriptor, buildinfo and changes files.
Verify their hashes before copying, create `.keep` first, and include hidden files in the stage's checksum list.
Retain the gate's signed-index, resolution, execution and link-check receipts before deleting its regenerable unpack and archive caches.
A source directory full of objects is neither the closure nor necessary for replaying it.
