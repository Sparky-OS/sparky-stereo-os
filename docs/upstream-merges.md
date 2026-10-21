# Merged outside Sparky Stereo

**For maintainers and distributions:** fixes and collaborative contributions to other projects, merged or in review, with links and dates.

**Sparky Stereo is also a campaign.**
Where a program breaks stereo or deep colour on the way to the screen, the fix goes to that program's own project, in its own style.
Each merge below was reviewed and accepted by that project's maintainers.
Each one shows the next project the same problem already fixed elsewhere, and Sparky Stereo is the desktop where all of them meet.

## Registered identifiers

**IANA registration, 20 October 2026:** [Matroska Track Plane Types](https://www.iana.org/assignments/matroska#matroska-track-plane-types) now assigns **3, 4 and 5** to the depth maps of the left-eye, right-eye and background planes, respectively, with Daniel Ramos as change controller and the [stereo-layer v1.9.0 specification](https://github.com/Sparky-OS/stereo-layer/blob/v1.9.0/docs/depth-marks.md) as reference.
This gives separate picture and depth tracks shared identifiers through `TrackCombinePlanes`, so readers can preserve their relationship before rendering stereo views.
The separate request for six packed-frame `StereoMode` values (proposed 15–20) remains under designated-expert review; those values are not assigned.

This registry milestone is separate from the software merges below.

**Merged:**
- **HandBrake** ([#8100](https://github.com/HandBrake/HandBrake/pull/8100), merged by Damiano Galassi (galad87) on 16 September 2026): the x264 encoder writes the H.264 frame packing arrangement SEI (ITU-T H.264, Annex D), so an encoded side by side or top and bottom video declares itself.
- **Universal Media Server** ([#6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330), merged by SubJunk on 19 September, released in [15.9.0](https://github.com/UniversalMediaServer/UniversalMediaServer/releases/tag/15.9.0) on 5 October 2026): 3D video keeps its declaration through H.264 transcoding, so televisions and players switch to 3D on their own; the Sony Bravia profiles of 2011 and 2012 are corrected too.
- **Universal Media Server** ([#6389](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6389), merged by SubJunk on 16 October 2026): every path that outputs 3D video writes the frame packing declaration, and 3D is found in files that signal it only in the video stream.
- **MKVToolNix** ([ebd8445b](https://codeberg.org/mbunkus/mkvtoolnix/commit/ebd8445b1185d35d6bdbb9c1463757fbc9aa7c29), from [!6311](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6311), merged by Moritz Bunkus on 21 September 2026): mkvmerge sets the Matroska StereoMode ([RFC 9559](https://www.rfc-editor.org/rfc/rfc9559)) from the AVC frame packing SEI.
- **MKVToolNix, HEVC** ([70889f220e](https://codeberg.org/mbunkus/mkvtoolnix/commit/70889f220e), from [!6312](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6312), merged 11 October 2026 with Moritz Bunkus's own tests, [db3410509d](https://codeberg.org/mbunkus/mkvtoolnix/commit/db3410509d)): the same StereoMode from the HEVC frame packing SEI.
- **mpv** ([#18490](https://github.com/mpv-player/mpv/pull/18490), merged by Kacper Michajłow (kasper93) on 23 September 2026, after a careful review by llyyr): the player detects the layout signalled in the stream itself, the frame packing SEI and the MP4 `st3d` box.
- **Teams for Linux** (our report [#3067](https://github.com/IsmaelMartinez/teams-for-linux/issues/3067), fixed by the maintainer, Ismael Martinez, in [#3070](https://github.com/IsmaelMartinez/teams-for-linux/pull/3070), merged 7 October 2026, released in [2.25.0](https://github.com/IsmaelMartinez/teams-for-linux/releases/tag/v2.25.0), a pre-release for now): the .deb declares ALSA and libgbm among its dependencies, so the app starts on a minimal Debian or Ubuntu system.
- **Qt Multimedia** ([778399](https://codereview.qt-project.org/c/qt/qtmultimedia/+/778399), merged 8 October 2026; in Qt 6.12 too, [778580](https://codereview.qt-project.org/c/qt/qtmultimedia/+/778580), merged 9 October 2026): the FFmpeg backend reports the mastering display's peak luminance in nits, as `QVideoFrameFormat::maxLuminance()` promises; it reported 10,000 times the value, so HDR video (PQ and HLG) was tone mapped against a peak 10,000 times too high. Tim Blechmann, the Qt Multimedia maintainer, improved its test and approved it.
- **Bino** ([e1be2918fe](https://github.com/marlam/bino/commit/e1be2918fe), applied by Martin Lambers on 9 October 2026): videos whose frame packing puts the right eye first are shown with the eyes in the right order.
- **spice-gtk** ([!159](https://gitlab.freedesktop.org/spice/spice-gtk/-/merge_requests/159), merged by Marc-André Lureau on 10 October 2026): a crash in the display channel whenever a surface is destroyed, which appeared once the project moved to GLib 2.68 (GLib's newer `g_clear_pointer` clears the pointer before its destroy function is read); found while adding stereo display to SPICE for the stereo virtual machine.
- **PeerTube** ([#7816](https://github.com/Chocobozzz/PeerTube/pull/7816), merged by Chocobozzz on 13 October 2026 after he reshaped it into the transcoding profile and handled rotation, [899cb02](https://github.com/Chocobozzz/PeerTube/commit/899cb0208850f2238d551a9bf687fd96460dc3f0)): a video that declares its 3D packing in its container keeps it through transcoding, right eye first included.
- **wiz3D** ([#33](https://github.com/effcol/wiz3D/pull/33), merged by effcol on 13 October 2026 after an MSVC rebuild on both architectures): a Linux build of its DirectX 9 stereo path, with three portability fixes that are also correct on Windows (CComPtr through varargs, a log format, an SSE store).
- **x265** ([#988](https://github.com/Multicorewareinc/x265/pull/988), merged by kirithika7 on 15 October 2026): with `--single-sei` and `--no-aud`, the one SEI NAL unit of a picture no longer starts with the previous picture's slice header bytes. vunguyen1989 found it while reviewing #986 and asked for it as its own pull request, since it affects master.

- **x265, field-coding follow-up** ([#999](https://github.com/Multicorewareinc/x265/pull/999), merged by kirithika7 on 21 October 2026): Akilan Sivakumar removed the unnecessary `--b-adapt 0` restriction for `--field` and added regressions and input-layout documentation. Daniel reported the restriction during #986 review; our [48 combined encodes and 24 byte-identical field-input comparisons](https://github.com/Multicorewareinc/x265/pull/999#issuecomment-6278374499) supplied supporting validation. This is a collaborative report/testing contribution; #986’s frame-packing option remains in review.

**In review:**
- **FFmpeg** ([#24628](https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/24628)): the H.264 and H.265 decoders honour the SEI's persistence, so the declaration holds for every frame, not only the first; [#24643](https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/24643): the stream's own declaration wins over the container's by default.
- **Media3, Android's media framework** ([androidx/media#3439](https://github.com/androidx/media/pull/3439)): the frame packing SEI read in MP4 and fragmented MP4, the right-eye-first modes, StereoMode in the WebM muxer.
- **x265** ([#986](https://github.com/Multicorewareinc/x265/pull/986)): a `--frame-packing` option that writes the H.265 frame packing arrangement SEI.
- **VLC** ([!10366](https://code.videolan.org/videolan/vlc/-/merge_requests/10366)): the x264 module signals the input's stereo layout by default.
- **gamescope** ([#2438](https://github.com/ValveSoftware/gamescope/pull/2438)): the present mode of the nested output can be chosen, which ends a frame race seen when stereo games run through it.
- **NVIDIA's open kernel modules** ([#1386](https://github.com/NVIDIA/open-gpu-kernel-modules/pull/1386)): HDMI deep colour at the depth the display declares in its EDID (DC_30, DC_36, DC_48).
