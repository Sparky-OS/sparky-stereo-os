# Dynamic Procedural Foveated Rendering

**For people building spatial worlds and stereo renderers:** surface detail that adapts to where a person looks and to the device drawing it.
**Status:** a proposal combining established techniques, named by Daniel Campos Ramos on 25 October 2026 for his input to [TPAC 2026 breakout #40](https://github.com/w3c/tpac2026-breakouts/issues/40).
This page describes the idea and its requirements; it does not report an implemented or measured DPFR path in Sparky Stereo OS.

## What it means

Dynamic Procedural Foveated Rendering (DPFR) stores surface detail, starting with textures, as procedures and evaluates them every frame at the detail each part of each eye needs.
The gaze point gets every octave of detail the sampling rate can resolve, with fewer toward the periphery, adapting as the gaze, the device and the GPU's load change.
One procedure serves current 2D and 3D devices and headsets at their own resolutions.

The procedure must limit its frequencies to what each sample can represent, including the larger area covered by a coarse peripheral sample.
This makes peripheral filtering part of generating the detail, rather than a blur applied afterwards.
Smooth changes in those frequency limits are needed to keep detail from popping when the gaze moves.
Procedural storage alone guarantees neither filtering nor smooth transitions.

Texture memory traffic becomes computation, and evaluating fewer octaves toward the periphery reduces that computation.
The balance still needs measuring on each device.
For streaming, the procedure travels instead of the pixels, and each receiving device evaluates it for its own gaze and resolution.

## Why it fits stereo

Both eyes evaluate the same procedure at the same surface point in object or world space, with the same parameters and animation time.
That gives them the same underlying surface detail, anchored to the object rather than to either eye's screen coordinates.
Each eye still needs filtering for its own projected sample footprint, and the detail choices need coordination between the eyes.
Shared coordinates alone do not guarantee identical filtered samples or comfortable stereo.

This belongs in the renderer that produces the eye views.
The edition's [presentation contract](how-it-works.md) still carries those views to Stereo KWin as declared full side by side, each eye at its own resolution.

## Part of the answer

DPFR is part of the answer to foveated rendering, world size and streaming, not the whole answer.
Textures come first; procedural geometry can follow the same way, as the demoscene already generated models.
Eye tracking and lighting remain separate problems.
Photographs and scanned assets can remain images where a procedure does not describe them adequately.
The name combines established techniques; it does not claim to invent procedural textures or foveated rendering.
Daniel's [spatial-browser input](https://github.com/w3c-cg/pm-kr/tree/main/talks/2026-10-28-tpac-spatial-browser) and [Web of Worlds input](https://github.com/w3c-cg/pm-kr/tree/main/talks/2026-10-30-tpac-web-of-worlds) put the idea in its discussion context.

## Sources

- Matt Pharr, Wenzel Jakob and Greg Humphreys, [Physically Based Rendering, chapter 10: Texture](https://pbr-book.org/3ed-2018/Texture), explain how texture functions can adjust their frequency content to the sampling rate to avoid aliasing.
- Khronos, [`VK_KHR_fragment_shading_rate`](https://docs.vulkan.org/features/latest/features/proposals/VK_KHR_fragment_shading_rate.html), describes shading multiple pixels with one fragment invocation.
  Reducing the shading rate does not itself filter a procedural texture.
- Fabian Giesen's [April 2004 account of .kkrieger](https://www.flipcode.com/archives/04-20-2004.shtml) describes .theprodukkt's procedural textures and models and its first place in Breakpoint 2004's 96k game competition.
  The [archived release](https://files.scene.org/view/parties/2004/breakpoint04/96kgame/kkrieger-beta.zip) contains a 97,280-byte executable.
  This is a precedent for compact procedural assets, not evidence of DPFR.
- Farbrausch's [fr_public](https://github.com/farbrausch/fr_public), released in April 2012, includes the tools and the .kkrieger branch, with BSD or public-domain terms stated per project.
- Unity's [foveated rendering documentation](https://docs.unity.com/en-us/engine/6000.6/manual/xr/graphics/foveated-rendering/introduction.md) uses "dynamic foveation" for foveation strength that follows the GPU's load; DPFR's "dynamic" includes that, together with the gaze and the device.
- Khronos' [`KHR_texture_procedurals` draft proposal, glTF #2381](https://github.com/KhronosGroup/glTF/pull/2381), opened on 3 April 2024, remains a draft checked on 25 October 2026.
  It is a related asset-format proposal, not an adopted DPFR standard.

The term is Daniel Campos Ramos's, dated 25 October 2026.
In Portuguese: Renderização Foveada Procedural Dinâmica.
