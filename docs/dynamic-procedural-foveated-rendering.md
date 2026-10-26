# Dynamic Procedural Foveated Rendering

**For people building spatial worlds and stereo renderers:** surface detail that adapts to where a person looks and to the device drawing it.
**Status:** a proposal combining established techniques, named by Daniel Campos Ramos on 25 October 2026 for his input to [TPAC 2026 breakout #40](https://github.com/w3c/tpac2026-breakouts/issues/40).
This page describes the idea and its requirements; it does not report an implemented or measured DPFR path in Sparky Stereo OS.

## What it means

Dynamic Procedural Foveated Rendering (DPFR) renders in layers: procedures first, the image last.
The procedural layers come first, starting with textures, and are evaluated every frame at the detail each part of each eye needs.
The gaze point gets every octave of detail the sampling rate can resolve, with fewer toward the periphery, adapting as the gaze, the device and the GPU's load change.
One procedure serves current 2D and 3D devices and headsets at their own resolutions.
In this proposal, a world shows at once, at any resolution, while nothing has been downloaded but the procedures.

The last layer is a high-resolution texture that loads while the procedural layers already render.
When it arrives, it blends in and replaces the procedural approximation without a jump.
It carries detail that a procedure cannot describe well, such as photographic or scanned detail.
The procedure and the image must agree on the surface's coordinates and colour range so that the blend has no jump.
The texture's tiles can load where the person looks first, applying the same foveation to loading.
That loading order is part of the design to explore, not a measured result.

The procedure must limit its frequencies to what each sample can represent, including the larger area covered by a coarse peripheral sample.
This makes peripheral filtering part of generating the detail, rather than a blur applied afterwards.
Smooth changes in those frequency limits are needed to keep detail from popping when the gaze moves.
Procedural storage alone guarantees neither filtering nor smooth transitions.

The procedural layers trade texture memory traffic for computation, and evaluating fewer octaves toward the periphery reduces that computation.
The balance still needs measuring on each device.
For streaming, a small procedure arrives first and each receiving device evaluates it for its own gaze and resolution while the high-resolution texture loads.

## Size

The proposed design uses one high-resolution texture per surface plus a small procedure.
The procedure covers every coarser level of detail, so the asset does not need lower-resolution copies, per-device versions or repeated variants for those levels.
The single image covers only the finest level.
The small procedure is downloaded first so the world shows at once; the one high-resolution texture follows as the last layer.
That texture still has its own size.
Whether the GPU builds sampling levels from it on the device is an implementation choice to measure.
Theoretically, this replaces the lower-resolution copies and per-device versions assets carry today; the savings still need measuring.

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
Stored images are DPFR's final layer, including photographs and scanned detail that procedures do not describe adequately.
This applies Daniel's 56k-era practice to 3D: the shapes were generated, and real images were used only where they were needed.
The name combines established techniques: procedural textures with frequency limits, foveated rendering and texture streaming.
It claims to invent none of them.
Daniel's [spatial-browser input](https://github.com/w3c-cg/pm-kr/tree/main/talks/2026-10-28-tpac-spatial-browser) and [Web of Worlds input](https://github.com/w3c-cg/pm-kr/tree/main/talks/2026-10-30-tpac-web-of-worlds) put the idea in its discussion context.

## Tiles and two resolutions (26 October 2026)

The procedures do not need to change, not even 2004 code.
Their evaluation is tiled: each frame evaluates as many tiles as the device's compute allows, each at the resolution it needs.
The gaze decides which tiles come first and at what resolution, and evaluated tiles stay cached until they need more or less detail.
So the same procedure scales from a phone to a workstation by the number of tiles per frame, not by rewriting it.
The high-resolution image's tiles load the same way, as the last layer.

Each eye has two resolutions: the rendering resolution and the output resolution.
The rendering resolution is where the procedures and the scene are evaluated; the output resolution is the screen's.
On modern devices an upscaler, often AI-based, brings the rendered views to the output resolution; elsewhere the compositor scales once, at the output.
For stereo, the upscaler treats both eyes alike, so the two views keep the same detail.
In Sparky Stereo OS this is the presentation contract: a program offers the rendering resolution per eye, and the views reach Stereo KWin as full side by side at any resolution per view.

## Sources

- Matt Pharr, Wenzel Jakob and Greg Humphreys, [Physically Based Rendering, chapter 10: Texture](https://pbr-book.org/3ed-2018/Texture), explain how texture functions can adjust their frequency content to the sampling rate to avoid aliasing.
- Khronos, [`VK_KHR_fragment_shading_rate`](https://docs.vulkan.org/features/latest/features/proposals/VK_KHR_fragment_shading_rate.html), describes shading multiple pixels with one fragment invocation.
  Reducing the shading rate does not itself filter a procedural texture.
- Khronos' [Vulkan specification, Sparse Resources](https://docs.vulkan.org/spec/latest/chapters/sparsemem.html), describes partially resident images whose regions can be populated as needed, a mechanism for texture streaming.
  It establishes the mechanism, not DPFR or its proposed gaze-based loading order.
- Fabian Giesen's [April 2004 account of .kkrieger](https://www.flipcode.com/archives/04-20-2004.shtml) describes .theprodukkt's procedural textures and models and its first place in Breakpoint 2004's 96k game competition.
  The [archived release](https://files.scene.org/view/parties/2004/breakpoint04/96kgame/kkrieger-beta.zip) contains a 97,280-byte executable.
  This is a precedent for compact procedural assets, not evidence of DPFR.
- Farbrausch's [fr_public](https://github.com/farbrausch/fr_public), released in April 2012, includes the tools and the .kkrieger branch, with BSD or public-domain terms stated per project.
- Unity's [foveated rendering documentation](https://docs.unity.com/en-us/engine/6000.6/manual/xr/graphics/foveated-rendering/introduction.md) uses "dynamic foveation" for foveation strength that follows the GPU's load; DPFR's "dynamic" includes that, together with the gaze and the device.
- Khronos' [`KHR_texture_procedurals` draft proposal, glTF #2381](https://github.com/KhronosGroup/glTF/pull/2381), opened on 3 April 2024, remains a draft checked on 25 October 2026.
  It is a related asset-format proposal, not an adopted DPFR standard.
- Epic Games, [Runtime Virtual Texturing in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine): texel data created "on demand using the GPU at runtime", with a limit on the "Runtime Virtual Texture Tiles being updated in a frame".
  It is a precedent for tiled evaluation on a per-frame budget, not for its gaze-driven order.
- Darwyn Peachey, [Texture On Demand](https://graphics.pixar.com/library/TOD/), Pixar Technical Memo #217 (January 1990): textures stored as fixed-size tiles, read only when needed and kept in a cache that drops the least recently used.
  It is a precedent for the tile cache and for loading the image by tiles.
- AMD, [FidelityFX Super Resolution](https://gpuopen.com/fidelityfx-superresolution/): "producing high resolution frames from lower resolution inputs", open source under the MIT licence, with an ML-based upscaler.

The term is Daniel Campos Ramos's, dated 25 October 2026.
In Portuguese: Renderização Foveada Procedural Dinâmica.
