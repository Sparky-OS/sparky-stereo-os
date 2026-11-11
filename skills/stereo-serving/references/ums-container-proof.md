# Proving a Universal Media Server change in containers

Recipe, first written on 2026-11-11 for the Flat Headset profile and the visible refusal of an unconvertible layout, and extended the same day to every input packing, the other outputs, the live SSDP match, MPEG-TS with a seek and the control calls.
A television or phone is never needed: UMS, a scripted controller and emulated renderers sit alone on an internal Docker network.
One command reruns all of it, unit tests and proof, offline, and prints one line per case (see "The rerun" below).

## The rerun

[`scripts/ums-container-proof/rerun.sh`](../scripts/ums-container-proof/rerun.sh) (with the Python and fixture scripts in `proof/` and the PC renderer in `rygel/`) does, in this order, each step in a container.
The copies here have their image, scratch and network names set by environment variables; they were generalised from the runner that was run and are not themselves rerun.
It needs three local images (a JDK 17 with Maven, FFmpeg and libmediainfo0v5; FFmpeg with libx264, ffprobe and Python 3; Python 3), an internal network on 192.0.2.0/24 and a Maven repository filled once.
The steps:

1. Copies the UMS source to a scratch folder and runs the unit tests with Maven offline (a JDK 17, Maven and FFmpeg image with libmediainfo, a copy of the Maven repository, `-o`, no network).
2. Builds the jar with its dependencies.
3. Generates the fixtures with FFmpeg when `generate-fixtures.sh` changed.
4. Starts the server on a fixed address with a fixed UUID and a fresh profile folder.
5. Starts seven emulated renderers, each on its own address.
6. Runs one controller per renderer inside that renderer's network namespace, and prints `PASS` or `FAIL` and the case.
7. Pushes a film to the PC as a renderer (below), when its image exists.
8. Checks the server log: the live SSDP match of the headset and of the Bravia, the warning for the refused file, the fixtures' SHA-256 unchanged.
9. Stops and removes every container it started; the exit status is 0 only when no line says `FAIL`.

The control: a renderer without a profile must get no conversion, so the same pixel check that every other case passes must fail on it.
The runner prints `PASS control` only when that check went red.
The unit tests carry their own controls: a checkerboard read with the other eye first must differ from the reference.

Maven flags that make a clean offline build work: `-o -B -Dmaven.gitcommitid.skip=true -Dskip.installnodecorepack -Dskip.corepack -Dmaven.antrun.skip=true -Dmaven.repo.local=...`.
`package` ends in an assembly step that needs UMS's own FFmpeg download and fails offline, after the jar with its dependencies is built, so the runner checks the jar's age and not Maven's exit status.

## The pieces

1. One internal network with a fixed subnet (`docker network create --internal --subnet 192.0.2.0/24 ...`), a fixed address per container, so no real renderer lists the test server.
   Keep one fixed server UUID in `UMS.conf` (`uuid = ...`) across runs, because renderers keep every server UUID they have seen.
2. Fixtures with FFmpeg, one second each, named neutrally (`full-sbs-left.mkv`, `rows-first-left.mkv`), left view solid red, right view solid cyan, the container's `stereo_mode` tag set; the layouts that mix the views inside a 2x2 chroma block (rows, columns, checkerboard) are 4:4:4, because 4:2:0 averages red and cyan to grey.
   One file without a tag (2D), one H.264 file with the frame packing SEI and no container tag for each of side by side and top and bottom, and one anaglyph file that must be refused.
   Keep each file's `ffprobe -show_streams` JSON in a folder of its own, not beside the media: UMS scans every file in a shared folder.
3. The server image: a JDK 17 image, FFmpeg, and `libmediainfo0v5`.
   Mount the profile folder at the path UMS reads (`-Duser.home=...` and `.config/UMS` in it, with an empty `data` folder) and the program folder (jar, `renderers/`, `UMS.sh`, `web/`) at `/opt/ums`.
4. The emulated renderer announces itself on SSDP (NOTIFY alive every five seconds, and answers M-SEARCH), serves a device description whose strings a renderer profile matches, keeps the state of a real renderer (AVTransport and RenderingControl) and, on Play or Seek, pulls the stream itself with its own User-Agent and saves it.
   Two of its identities match shipped profiles (Flat Headset and the Sony KDL-46EX725), and the others stay off SSDP so that UMS knows them by User-Agent only, through test profiles (`UserAgentSearch`).
5. The controller finds the server by an SSDP search (it must set `IP_MULTICAST_IF`: on an internal network the default route is missing and `sendto` fails with "Network is unreachable"), browses the library as the renderer, pushes the resource with `SetAVTransportURI` and `Play`, waits for the renderer to have pulled it, and checks what arrived.
   It runs inside the renderer's network namespace (`--network container:NAME`), because UMS lists a folder for the address that asks, so a controller from its own address sees another renderer's list.
6. Check what the renderer received, not what the server said: container, codec, size, frame rate, the Stereo 3D mark of the first frame as FFmpeg's `showinfo` prints it (the same words UMS reads), and the colour in the middle of each view (red left, cyan right, tolerance for MPEG-2 chroma: red reads r=253).

## Expected, 2026-11-11, Flat Headset (`Output3DFormat = sbsl`), FFmpeg 6.1.1

| Source (one file each) | UMS does | Received |
|---|---|---|
| full side by side, left first | transcode, no layout filter | MPEG-PS 1920x1080, red left, cyan right |
| half side by side | transcode, no layout filter | 1920x540 (each view 960x540, not scaled) |
| top and bottom, left first | `stereo3d=abl:sbsl` | 3840x540 (each view 1920x540, not stretched) |
| side by side, right eye first | `stereo3d=sbsr:sbsl` | 1920x1080, views swapped back, red left |
| rows, left first or right first | `stereo3d=irl:sbsl` or `irr:sbsl` | 3840x540 |
| columns, left first or right first | `stereo3d=icl:sbsl` or `icl:sbsr` | 1920x1080 |
| checkerboard, either order | `geq` unpack, nearest sample | 1920x1080 |
| alternating frames, either order, 50 fps | `stereo3d=al:sbsl` or `ar:sbsl` | 2560x720 at 25 fps for 1280x720 views |
| 2D (no mark) | no layout filter | 1920x1080, one picture; no 3D correction on 2D |
| anaglyph | refused, WARN in the log | not listed |

The other outputs, same sources: a 2D renderer (`ml`, `mr`) receives one view at the size the view has (960x1080 from a full side by side file, 1920x540 from top and bottom, the left view from a right-eye-first file); an anaglyph-only renderer (`arcc`) receives white from a red left view and a cyan right view, which only happens when each view reached its own channel (a swapped pair gives black); a renderer that takes H.264 in MPEG-TS receives the frame packing SEI `side by side` after a conversion; the Bravia profile's MPEG-2 output of an H.264 file with the SEI keeps the layout's mark (`side by side` or `top and bottom`) as MPEG-2 user data; a `Seek` of 0:00:05 makes UMS start the transcode with `-ss 5.0` and the first picture is the green one.

## Traps

- **Symptom:** the server log has no `stereo3d=` and no `3D format` line, and the top-and-bottom clip arrives unchanged.
  **Cause 1:** the image lacks `libmediainfo0v5`; UMS then parses with FFmpeg only, and the FFmpeg parser does not read Matroska's `StereoMode`.
  **Fix:** install it; the log must show `Loaded MediaInfoLib - v24.01` at the first scan.
  **How found:** grep the server log for `MediaInfo`; the line was missing, and `find / -name 'libmediainfo*'` in the container returned nothing.
- **Symptom:** the log says `Renderer UnknownRenderer found on address ...` and no profile applies.
  **Cause:** UMS reads `UMS.conf` from `~/.config/UMS`, not from the folder with the jar.
  **Fix:** mount the profile folder at the profile path.
  A profile that matches the renderer's UPnP description needs the renderer to announce itself on SSDP; the log line is `Matched media renderer "Flat Headset" based on dlna details ...` and it is a DEBUG line, so read the profile folder's `debug.log`, not the container's console.
- **Symptom:** the folder lists nothing and the scan finishes in 0 seconds.
  **Cause:** `shared_folders_previously_scanned` in `UMS.conf` names the folder already.
  **Fix:** delete that line in a fresh profile; browsing a folder parses its files.
- **Symptom:** a file the renderer cannot take is missing from its list and the log shows only a debug line (`Error adding child ...`).
  **Cause:** `StoreResource.addChild` catches the exception at debug level.
  **Fix:** the refusal logs a warning itself (`No supported conversion can convert ... so it is not offered to NAME`).
- **Symptom:** the proof says the top-and-bottom clip should be 1920x1080 and is 3840x540.
  **Cause:** `stereo3d=abl:sbsl` repacks without resampling, and a half top and bottom 1920x1080 source gives two 1920x540 views.
  **Fix:** expect 3840x540 ([full side by side at any resolution](../../sparky-stereo/SKILL.md)).
- **Symptom:** `rm -r` of a proof folder says permission denied.
  **Cause:** containers ran as root and wrote the outputs.
  **Fix:** run every container with `--user $(id -u):$(id -g)`.
- **Symptom:** Maven stops at `.git directory is not found!`, or at a `corepack yarn install` that wants the network, or at an Ant `get` of UMS's FFmpeg.
  **Cause:** the build is made for a git checkout with network access, and the platform profile that matches the machine runs the front end and the binary download.
  **Fix:** the flags in "The rerun". **How found:** each failure names its plugin and goal; the flag is the plugin's own `skip` property.
- **Symptom:** `StoreItemStereoTest` fails with `expected: not <null>` and nothing else.
  **Cause:** no FFmpeg executable, so UMS finds no engine and returns no transcoding settings.
  **Fix:** run the tests in an image that has FFmpeg and libmediainfo. `FFmpegParserTest#testParser` also fails there, the same way on upstream's own commit, because it expects `Format Profile: flv` from the FFmpeg UMS bundles; leave it out and say so.
- **Symptom:** a conversion's last column or a row of the picture is wrong, by a little.
  **Cause:** `geq`'s `p(x,y)` interpolates bilinearly by default and returns the neighbouring sample at the last column.
  **Fix:** `interpolation=n`. **How found:** the output and an independently made reference differed in 159 of 12288 bytes, all in the edge column; printing the first mismatches showed it.
- **Symptom:** the eyes are swapped, or a mono output is the wrong view, only for some packings.
  **Cause:** in FFmpeg 6.1, `stereo3d=icr:...` returns the views swapped (even to `sbsr`), and `stereo3d=irr:ml` returns the right view; the same source through `sbsl` is exact.
  **Fix:** send every packing to side by side with the left view first, read right-first columns as left first and put them on the other side, then convert from there.
  **How found:** each conversion compared byte for byte with a picture made by a formula that does not use FFmpeg, with each pixel's value telling its view and place; the matrix of input and output formats showed which pairs fail.
- **Symptom:** a converted film arrives marked with the layout it no longer has (top and bottom in the SEI of a side by side picture; side by side user data on one view).
  **Cause:** `stereo3d` copies the source frame's Stereo 3D side data, and x264 and the MPEG-2 encoder write the mark from the frame, ignoring the `frame-packing` option.
  **Fix:** `sidedata=mode=delete:type=STEREO3D` after the conversion; x264's `frame-packing` value then writes the output layout's mark. MPEG-2 has no way to write it with FFmpeg 6.1 (no filter sets the side data), so it carries none.
  **How found:** the pixels were right and `showinfo` printed `top and bottom` on a side by side file; the filter chain was run by hand with and without the extra filter.
- **Symptom:** a recognised layout that is not anaglyph is treated as anaglyph and its 3D handling is switched off.
  **Cause:** `MediaVideo.multiViewIsAnaglyph()` returns true for every layout it does not list.
  **Fix:** list the new layouts. **How found:** reading the method while adding the modes; a unit test now asserts it for each MediaInfo word.
- **Symptom:** a checkerboard file is not recognised.
  **Cause:** MediaInfo spells the layout `Checkboard (left eye first)`, and `Both Eyes laced in one block (...)` for alternating frames; the FFmpeg path says `checkerboard`.
  **Fix:** match both spellings. **How found:** the library called through `ctypes` (`MediaInfoA_Get(... "MultiView_Layout" ...)`) on each fixture.
- **Symptom:** the received stream has a `Stereo 3D` side data entry but the check cannot tell which layout.
  **Cause:** `ffprobe -show_entries frame=side_data_list` prints the type name only.
  **Fix:** read the first frame with `ffmpeg -vf showinfo`, which prints `Stereo 3D: type - side by side`, the form UMS parses.
- **Symptom:** a seek to 0:00:05 of a copied video still starts at the first picture.
  **Cause:** with `-c:v copy` the stream can start only at a keyframe, and the fixture had one.
  **Fix:** a keyframe every second in the seek fixture (`-g 25`).
- **Symptom:** an H.264 file marked only in its Matroska tag arrives in MPEG-TS, copied, with no frame packing SEI.
  **Cause:** UMS copies the video, and stock FFmpeg has no `frame_packing` option for `h264_metadata` to write the SEI into a copy.
  **Fix (not done here):** the edition's FFmpeg has the option; with stock FFmpeg UMS would have to transcode, and that is a choice for the person, not a default to change quietly. The runner expects the missing mark and names the case so.
- **Symptom:** the controller's browse finds no folder, or a different list from the one the renderer should see.
  **Cause:** UMS lists a folder for the address that asks.
  **Fix:** run the controller in the renderer's network namespace.
- **Symptom:** `play without media` succeeds in the control run.
  **Cause:** the renderer used by the stream cases already holds a URI.
  **Fix:** a renderer of its own for the control calls.

## The PC as a renderer (Rygel)

`rygel/build.sh` builds a Debian testing image with Rygel 46.1 (LGPL-2+, in Debian), an MPRIS2 player (VLC, or mpv with mpv-mpris) and a D-Bus session.
Rygel's MPRIS plugin makes every MPRIS2 player on the session bus a UPnP AV MediaRenderer: it announces it on SSDP, and `SetAVTransportURI`, `Play`, `Pause`, `Seek` and volume go to the player's MPRIS2 methods.
The runner starts it on its own address, the controller (in its network namespace) finds UMS and Rygel by SSDP, takes the film's URL from UMS's folder as the PC, sets it on Rygel with the item's DIDL-Lite and plays it.
Checks: UMS lists the film, Rygel announces the player, Play is accepted, Rygel reports `PLAYING`, its position moves, its track URI is the URL UMS gave, the player itself says `Playing` with that `xesam:url`, UMS's decision for the file is "will be streamed" (the file as it is, no conversion), and UMS matched Rygel's description to `PcStereoPlayer.conf` (manufacturer "Rygel Developers", model "Rygel").
The pair that a stereo player declares to the compositor is not part of this run: no compositor is in the container.

- **Symptom:** `SetAVTransportURI` returns UPnP error 714 `Illegal MIME-type`.
  **Cause:** Rygel refuses an item whose `protocolInfo` type is not in the player's MPRIS2 `SupportedMimeTypes`, and mpv-mpris advertises only `application/ogg` and `audio/mpeg`; VLC's list has `video/x-matroska`, `video/mp4` and the rest.
  **Fix:** a player that stands behind Rygel must list the video types it plays; the edition's players are checked for it.
  **How found:** the fault's `errorCode`, then `gdbus call ... Properties.Get org.mpris.MediaPlayer2 SupportedMimeTypes` on the session bus Rygel talks to (read from `/proc/PID/environ` of the rygel process).
- **Symptom:** `dbus-daemon` exits with "Looking up user ID 1000: not found".
  **Cause:** the image has no passwd entry for the uid the container runs as.
  **Fix:** `useradd --uid 1000` in the image.
- **Symptom:** the position does not move and the player says `Stopped`.
  **Cause:** the one-second fixture ended.
  **Fix:** push an eight-second film.
