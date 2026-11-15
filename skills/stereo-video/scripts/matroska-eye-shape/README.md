# Measuring the shape of an eye in a Matroska pair

The tools of [the shape of an eye in a Matroska pair](../../references/eye-shape-in-matroska.md).
Each runs in a throwaway container with the fixtures' folder mounted; the scripts expect themselves at `/scripts` and the proof rig's [`capture.py`](../../../stereo-proof-rig/scripts/capture.py) beside them (or `CAPTURE=path`).

| Script | What it does |
|---|---|
| `fixtures.py OUTDIR [CASE...]` | the fixtures: each eye drawn at its display shape (a circle and a square), resized to its coded size, packed, FFV1, muxed by mkvmerge with the case's StereoMode and display size; `cases.json` and `SHA256SUMS` beside them |
| `measure.py` | the circle's and the square's width over height in one eye (a module) |
| `probe-ffmpeg.py FIXTURES` | FFmpeg's own reading: ffprobe's ratios, each eye of the first frame at the stream's SAR, the left eye rendered by ffmpeg |
| `render-eye.sh FIXTURES OUT NAME...` | ffmpeg's picture of a frame at its SAR, for a pixel comparison of two builds |
| `rig-case.sh PLAYER FIXTURE OUT [WAIT]` | one case: a fresh Stereo KWin on a virtual output, a fresh home, the player, ScreenShot2's picture of both eyes, the declarations |
| `rig-run.sh LIST FIXTURES OUT [WAIT]` | the cases of a list of `PLAYER FIXTURE` lines, each measured |
| `analyze-capture.py CAPTURE EYE_WIDTH` | each eye's picture found by its colour and measured |
| `reanalyze.sh ROOT`, `table.py` | measure a run's captures again; one line per case |
| `thumb-driver/`, `thumb-run.sh` | the Dolphin video thumbnail: the ffmpegthumbs plug-in run through KIO's `ThumbnailCreator` API, each view measured |
| `store-test.sh` | a packing stored for the file (libstereo-policy's store) wins over the file's mark |

The rig needs a render node and its group (`--device /dev/dri/renderD128 --group-add GID --user 1000:1000`) and `--cap-add SYS_NICE`; mpv on the software renderer needs `--gpu-sw`.
