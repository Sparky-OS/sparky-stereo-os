# Proving a Universal Media Server change in containers

Recipe, written on 2026-11-11 after the Flat Headset profile and the visible refusal of an unconvertible layout (UMS branch of the headset lane).
A television or phone is never needed: UMS, a scripted controller and an emulated renderer sit alone on an internal Docker network.

## Recipe

1. One internal network with a fixed subnet (`docker network create --internal --subnet 192.0.2.0/24 ...`), a fixed address per container, so no real renderer lists the test server.
   Keep one fixed server UUID in `UMS.conf` (`uuid = ...`) across runs, because renderers keep every server UUID they have seen.
2. Fixtures with ffmpeg, one second each, named neutrally (`full-sbs-left.mkv`, not `sbs_...`, so no file name guess confounds the result): left view solid red, right view solid cyan, the container's `stereo_mode` tag set (`left_right`, `top_bottom`, `right_left`), one file without a tag (2D) and one `checkerboard_lr` file.
   Keep each file's `ffprobe -show_streams` JSON beside it.
3. The server image: a JDK 17 image, ffmpeg, and `libmediainfo0v5`.
   Mount the profile directory at `/root/.config/UMS` (UMS.conf and SHARED.conf) and the program directory at `/opt/ums` (jar, `renderers/`, `UMS.sh`).
4. The emulated renderer answers SSDP, serves a device description whose `modelDescription` is the real app's string, and exposes `AVTransport` (`SetAVTransportURI`, `Play`, `Stop`).
   The controller browses `ContentDirectory`, sets the URI on the renderer, then fetches the stream as the renderer would, with its user agent, and saves it.
5. Check what the renderer received, not what the server said: `ffprobe` for container, codec, size and marks; `ffmpeg -frames:v 1 -f rawvideo -pix_fmt rgb24` and read one pixel in the middle of each eye (red left, cyan right, tolerance for MPEG-2 chroma: red reads r=253).
6. A control that must fail: an input UMS cannot convert (checkerboard to side by side).
   Pass when the controller finds it absent from the listing and the server log has the warning naming the file, the two layouts and the renderer.
   The same harness, run against a server with the profile not loaded, failed on the top-and-bottom clip (no `stereo3d` filter, the right eye still red): that is the proof that the pixel check can fail.

Expected on 2026-11-11 with the Flat Headset profile (`Output3DFormat = sbsl`):

| Source | UMS decision | Received |
|---|---|---|
| full side by side, left first | transcode, no layout filter | MPEG-PS 1920x1080, red left, cyan right |
| half side by side | transcode, no layout filter | 1920x540 (each eye 960x540, not scaled) |
| top and bottom, left first | `stereo3d=abl:sbsl` | 3840x540 (each eye 1920x540: the half top and bottom is not stretched) |
| side by side, right eye first | `stereo3d=sbsr:sbsl` | 1920x1080, eyes swapped back, red left |
| 2D (no mark) | no layout filter | 1920x1080, one picture; no 3D correction on 2D |
| checkerboard | refused, warning in the log | not listed |

## Traps

- **Symptom:** the server log has no `stereo3d=` and no `3D format` line, and the top-and-bottom clip arrives unchanged.
  **Cause 1:** the image lacks `libmediainfo0v5`; UMS then parses with FFmpeg only, and the FFmpeg parser does not read Matroska's `StereoMode`.
  **Fix:** install it; the log must show `Loaded MediaInfoLib - v24.01` at the first scan.
  **How found:** grep the server log for `MediaInfo`; the line was missing, and `find / -name 'libmediainfo*'` in the container returned nothing.
- **Symptom:** the log says `Renderer UnknownRenderer found on address ...` and no profile applies.
  **Cause:** UMS reads `UMS.conf` from `~/.config/UMS`, not from the folder with the jar, so a `renderer_default` placed next to `ums.jar` was never read; the first start also wrote a fresh default profile there.
  **Fix:** mount the profile folder at the profile path; the log then says `Using default media renderer "Flat Headset"`.
  A controller is not the renderer: it browses from its own address, so a profile that matches the renderer's UPnP description needs `renderer_default` in a test (the match itself is covered by `RendererConfigurationTest`).
- **Symptom:** the folder lists nothing and the scan finishes in 0 seconds.
  **Cause:** `shared_folders_previously_scanned` in `UMS.conf` names the folder already.
  **Fix:** delete that line in a fresh profile; browsing a folder parses its files.
- **Symptom:** a file the renderer cannot take is missing from its list and the log shows only a debug line (`Error adding child ...`).
  **Cause:** `StoreResource.addChild` catches the exception at debug level.
  **Fix:** the refusal logs a warning itself (`No supported conversion can convert ... so it is not offered to NAME`).
  A renderer that cannot take a layout is told, in the place the person reads.
- **Symptom:** the proof says the top-and-bottom clip should be 1920x1080 and is 3840x540.
  **Cause:** the check expected the desktop's old assumption; `stereo3d=abl:sbsl` repacks without resampling, and a half top and bottom 1920x1080 source gives two 1920x540 views.
  **Fix:** expect 3840x540 ([full side by side at any resolution](../../sparky-stereo/SKILL.md)).
- **Symptom:** `rm -r` of a proof folder says permission denied.
  **Cause:** containers ran as root and wrote the outputs.
  **Fix:** run the controller with `--user $(id -u):$(id -g)`, or clean through a container.
