# What stereo costs KWin on a 2016 laptop

Measured on 23 October 2026 on Daniel's field laptop, driven from the workstation over the network so the laptop ran nothing but the test.
Every case Daniel watched passed his visual check; the numbers below say how much each one cost.

## The machine

- Lenovo ideapad 310-15ABR (80ST): AMD A10-9600P from 2016 (Bristol Ridge, 4 CPU cores and 6 GPU compute units), 11 GiB RAM.
- The integrated Radeon R5 drives every connector; the discrete Radeon R5 M430 has no outputs.
- Laptop panel 1366x768 at 60 Hz; a Sony 3D TV on HDMI.
- Sparky Stereo OS: kernel 7.3.0-rc6-stereo3d10, KWin 6.7.4 +stereo3d30, Mesa 26.1.6 +stereo3d14.
- Films decoded in software (the players' default at the time; hardware decoding is now being made the default) and played without audio.
- More about both machines: [hardware.md](../hardware.md).

## Method

- KWin's own per-frame log (`KWIN_LOG_PERFORMANCE_DATA=1`), one file per output.
- Render: the time between KWin's render start and render end for each presented frame, per output, in milliseconds.
- Late: frames presented more than half a refresh after the time KWin aimed for.
- A 1 Hz machine log beside it: CPU busy, the integrated GPU's `gpu_busy_percent`, temperature.
- Each case: 2 minutes of idle desktop, then 3 minutes of a 2D film, then 3 minutes of a 3D film, full screen on the output named.
- The 2D film is Everything Everywhere All at Once (1080p); the 3D film is Life of Pi (side by side).
- Modes: the laptop at 1366x768 in 2D or anaglyph; the TV at 1080p30 in 2D or 1080p30 frame packing; the copy case with the TV as source uses 720p60 frame packing.
- One machine, one run per case. The scripts below repeat it.

## Results

24 fps is the films' own rate, so 24 means every film frame was shown.
On two outputs, the table gives the output with the higher render time.

| Setup | Film | Render, median | fps | GPU busy | Late frames |
|---|---|---|---|---|---|
| Laptop alone, 2D | 2D / 3D (one picture) | 11.0 / 12.7 ms | 24 / 24 | 11 / 13% | 74 / 12 of about 4,330 |
| Laptop alone, anaglyph | 2D / 3D | 26.1 / 30.2 ms | 24 / 24 | 26 / 30% | 91 / 321 |
| TV alone, 2D 1080p30 | 2D / 3D (one picture) | 17.0 / 19.8 ms | 24 / 24 | 19 / 21% | 989 / 277 |
| TV alone, frame packing 1080p30 | 2D / 3D | 54.6 / 57.3 ms | 24 / 24 | 61 / 61% | 333 / 409 |
| Both screens, extended, 2D | 2D / 3D | 10.7 / 13.7 ms | 24 / 24 | 11 / 13% | 200 / 917 |
| Laptop anaglyph, TV 2D, extended | 2D / 3D | 23.2 / 31.8 ms | 24 / 24 | 24 / 32% | 49 / 529 |
| Copy, 2D, TV as source | 2D / 3D | 12.6 / 16.8 ms | 24 / 24 | 21 / 25% | 60 / 113 |
| Copy, 3D, TV as source | 2D | 33.4 ms | 24 | 51% | 2,583 |
| Copy, 3D, TV as source | 3D | 196 ms | 18.5 | 96% | 3,310 |
| TV frame packing as main, laptop anaglyph, extended | Coyote Falls 3D, default | 196 ms | 18.8 | 99% | 3,384 |
| Same | Coyote Falls 3D, PRIME offload | 145 ms | 22.3 | 98% | 4,017 |
| Same | Life of Pi, default | 180 ms | 19.9 | 95% | 3,529 |
| Same | Life of Pi, PRIME offload | 119 ms | 20.9 | 92% | 3,571 |
| Both screens off (DPMS), 2D and 3D | idle | no frames | 0 | 0% | none |

Late frames on the TV at 30 Hz include the 24-on-30 cadence itself, so they are not all stutter.
Full tables, with p95, p99, maximum, CPU and temperature: [results-matrix.txt](a10-2026-10-23/results-matrix.txt) and [results-inverse.txt](a10-2026-10-23/results-inverse.txt).

## What it says

Drawing the desktop twice costs about twice: on the laptop, anaglyph takes 26 ms where 2D takes 11 ms, inside the 42 ms a 24 fps frame allows.
Frame packing on a 1080p TV costs about three times the TV's 2D render and still shows every film frame.
The only cases below 24 fps are a full-screen 3D film on 3D outputs, at 18.5 to 20.9 fps, and their three causes are known:
- a KWin bug that grew each surface's damage by one pixel into the neighbouring output, so both eyes were redrawn in full; it is fixed in our KWin branch (b1ccebcfed) and not yet in the build measured here;
- software video decoding on a 2016 quad core; the players' hardware decoding default is the next change;
- the hand-over between the two GPUs: mpv drew on the discrete GPU in both runs, and PRIME offload alone took Coyote Falls from 18.8 to 22.3 fps.
The before and after of those three fixes will be measured on the same machine with the same scripts.

## What Daniel saw

In his words, during the runs:
- Laptop 2D with the 3D film: "3d movie, one picture only, so working as expected."
- Copy, both 2D: "2d mode - perfect, no issues".
- Copy, TV as source, 3D: "3d copy tv source 2d movie - it works"; with the 3D film: "pass".
- Coyote Falls with PRIME offload: "wow! it's perfect right now".
- On the baseline: "we're doing all this software based in a A10 quad core ... we're prooving this is light partner, not heavy at all".
- One case failed and is a known bug: copy with both screens in 3D and the laptop as source showed no frames ("both are in 3D, but nothing runs"); the same setup with the TV as source passed.

## Cost to maintain

On the KWin side, the build measured here (branch stereo3d30) is 200 commits on top of KWin 6.7.4:
- 285 files, 24,187 lines added and 363 existing lines replaced or removed;
- 46% of the added lines are tests: 11,175 lines in 70 files;
- moving it to KWin 6.7.5 conflicts in 2 files (`src/backends/drm/drm_output.cpp` and `src/plugins/screenshot/screenshot.cpp`);
- a port to KWin's 6.8 beta (v6.7.91) already exists as branch stereo3d-6.8, 154 commits, made on 10 October.
The branches are public: https://invent.kde.org/danielcamposramos/kwin/-/tree/stereo3d30 and https://invent.kde.org/danielcamposramos/kwin/-/tree/stereo3d-6.8

## Not measured yet

- The same 2D cases on unmodified KWin, which would show what the stereo code costs a desktop that never turns 3D on.
- How long the 6.8 port took.
- Other machines.

## Files

- [matrix.sh](a10-2026-10-23/matrix.sh): every display setup with idle, 2D film and 3D film, the PRIME pass and the screens-off floors.
- [inverse.sh](a10-2026-10-23/inverse.sh): the copy cases with the TV as source.
- [analyse.py](a10-2026-10-23/analyse.py): reads KWin's per-frame logs and the machine log inside each window.
- [marks-matrix.csv](a10-2026-10-23/marks-matrix.csv) and [marks-inverse.csv](a10-2026-10-23/marks-inverse.csv): the start and end of every window.
- Raw data (KWin's per-frame logs, the machine log, mpv logs and the screen layouts): https://repo.sparkyos.org/measurements/a10-kwin-cost-2026-10-23-raw.tgz (8.9 MB), SHA-256 17eb0a700fbcda3f066c2a6a2108d890032d57b57ea0e55ac9885e1d21da5544.
