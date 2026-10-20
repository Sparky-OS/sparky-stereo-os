# Sparky Stereo OS architecture infographic

**For readers who want the whole display path in one picture, with a text version below.**

[![Applications provide full side-by-side stereo content to KWin; shared composition connects to several display paths. Desktop depth, media metadata, colour validation and Cushion Swap are separate parts of the system.](images/spatial-computing-architecture.png)](images/spatial-computing-architecture.png)

[Open the full-size image](images/spatial-computing-architecture.png) · [Read the architectural synthesis and its sources](architectural-synthesis.md)

Daniel requested the original research and infographic in Gemini / NotebookLM.
The published image preserves its visual layout, with factual corrections made using Codex and OpenAI's built-in image editor on **20 October 2026**.
The original remains in the project's private research archive.
The status labels describe the work on that date.

## The diagram in text

**Applications and media:** the internal content contract is full side by side, with both eyes complete at the content's resolution and the left eye first.
Ordinary 2D controls remain separate.
Applications declare stereo once; KWin adapts its presentation to each screen.
See [how it works](how-it-works.md) and [the house formats](house-formats.md).

**Stereo KWin:** shared desktop composition brings together the eye views.
Each output needs its appropriate layout, geometry, timing and device signalling.
Preserving source precision and colour metadata is the goal throughout the path; the actual result depends on the application, compositor, driver and display.
See [colour and verification](architectural-synthesis.md#colour-system-services-and-verification).

**Desktop depth:** the screen plane has zero disparity.
Sunk planes sit behind it; popped planes sit in front.
Window depth is implemented, while finer UI transforms and the central Theme Editor remain planned.
Theme and user choices determine the depth within supported limits.
See [the theme-design guide](for-theme-designers.md).

**Media and verification:** H.264/H.265 frame-packing SEI and Matroska `StereoMode` carry layout and eye-order information.
Virtual display tests support automated checks; physical-device qualification remains separate.
Hibernation and resume checks concern system reliability and the configured swap target.
See [the program inventory](programs-in-detail.md) and [virtual display testing](../skills/vkms-stereo/SKILL.md).

**Display drivers:** HDMI stereo presentation combines the pixel layout with appropriate timing and signalling.
Available modes depend on both driver and display.
Colour description, range and output timing need validation on the actual hardware path.
See [the driver guidance](../skills/drivers/SKILL.md).

**Cushion Swap File:** disk swap normally stays off.
When available memory becomes low or falls quickly, the service enables the configured swap area as a reserve against memory pressure.
It disables that area again when the recovery calculation says this is safe, using kernel pressure signals where available.
This policy helps absorb memory spikes; it does not establish a stereo frame-rate improvement.
See the [implementation and thresholds](https://github.com/danielcamposramos/driver_stereodisplay/blob/main/sparky-os/packages/sparky-stereo-cushion-swap/README.md).

## Display paths and status

| Presentation | Transport and qualification | Display |
| --- | --- | --- |
| HDMI stereo layout | HDMI 3D timing and signalling; driver and display dependent. | 3D TV or projector |
| One eye, or red-cyan anaglyph | An ordinary 2D display connection; one eye gives full colour without anaglyph filters. | Regular colour monitor |
| Stereo pair for spatial displays | DisplayXR integration is in development; optical weaving belongs to the vendor integration. | Autostereoscopic display |
| Stereo desktop in a passive viewer | Flat Headset uses USB or a network stream; the current tested receiver has no head tracking. Performance varies by device and connection. | Android phone and viewer |
| Tracked headset presentation | Compositor VR / Big Picture mode is planned. | Tracked VR headset |

The [architectural synthesis](architectural-synthesis.md) links the implementation records, device-test results and remaining work behind these labels.
