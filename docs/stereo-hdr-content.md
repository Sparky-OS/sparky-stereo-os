# Stereo and HDR in one declaration: `kde-stereo-hdr-content`

Design, 2026-10-13, by Daniel Ramos for Sparky Stereo OS.
Status: design; nothing is built yet, and it has not been tried on an HDR screen.

**Engineering limit, clarified 19 October 2026:** Daniel's choice of full side by side rests on stereo device testing. He has not yet done the equivalent cross-format HDR testing needed to make an equally informed choice of HDR interchange representation. This document is a proposal based on specifications and architectural reasoning. PQ, HLG and gain-map images impose different decoding and reconstruction requirements; a shared presentation contract does not make them one encoding. Working colour space, pixel representation, precision and metadata handling remain choices to validate. Existing stereo and deep-colour measurements do not validate this HDR path, and deep colour alone is not HDR.

## 1. The problem

Upstream colour management (`wp_color_management_v1`, wayland-protocols staging) gives **one image description per `wl_surface`**.
KWin 6.7 implements it: `wp_color_management_surface_v1_set_image_description` (`src/wayland/colormanagement_v1.cpp:217`), per-surface feedback (`:83`), tone mapping in `src/core/colorpipeline.cpp`.

This leaves work for applications or their shared frameworks:

- **SDR controls and HDR content submitted in one buffer** share one surface description. To describe the HDR picture independently, the application or framework needs to give it a separate surface; otherwise it must compose both into a common colour representation before submission.
- **Two pictures with different HDR descriptions in one window** likewise need separate surfaces or client-side conversion. The proposed shared layer would make that separation reusable across viewers and players.
- **Gain-map photos need reconstruction data as well as a base picture.** The proposal adds a carrier for the map and its metadata, letting the compositor reconstruct for each output's headroom.

Stereo 3D uses the same separation: the content gets **its own layer** (a subsurface inside the flat window), declared on its own. The HDR proposal extends that shared-framework approach.

## 2. The principle

The same contract as stereo: **programs describe what the content is; KWin's outputs decide the screen.**

Decoded picture samples with their stereo layout and colour description play the same role as PCM with its sample rate and channel layout in audio. Full side by side keeps both views associated with one presentation frame; HDR additionally needs the colour and luminance description and any reconstruction data preserved until the output can adapt them. The shared principle is to describe each content layer once, preserve its information through the stack, and convert for the screen at the output.

- The declaration belongs to **each content layer**: a video, a photo, a canvas. Not the window, not the display.
- The rest of the desktop stays SDR, exactly as it stays flat around a 3D window.
- One declaration carries both halves: a layer declared for HDR carries its stereo layout in the same object, and a stereo layer can carry HDR.
- Mono/stereo and SDR/HDR are independent properties; a mono HDR picture does not need stereo packing.

## 3. Who creates the layer: the shared frameworks, never the program

The goal is for players and viewers to need **no display-specific HDR or stereo code**, with shared frameworks taking on decoding, layer creation and declaration. The HDR integrations below are proposed work:

| Content | Framework that creates and declares the layer | Programs served |
|---|---|---|
| Video | Qt Multimedia (VideoOutput's layer) | Dragon Player, Plank Player, any QML player |
| Video | MpvQt (its video subsurface) | Haruna, PlasmaTube |
| Video | mpv's own Wayland video layer | mpv |
| Video | VLC core (embedded video) | VLC Stereo |
| Video | MLT (monitors) | Kdenlive |
| Photos | libstereo-layer (C++ and QML), fed by KImageFormats | Gwenview, digiKam, Showfoto, KolourPaint |
| Web | Waterfox's native compositor surfaces | pages |

libstereo-layer becomes the stereo **and** HDR layer library: one subsurface per picture, declared.

## 4. What one declaration carries (one object per layer)

1. **Packing** (the existing value, unchanged): none, or full side by side with the left eye first. It applies to every buffer of the layer below.
2. **The base colour description**: an upstream `wp_image_description_v1` object passed **as an argument** of our request, so the colour vocabulary stays upstream's (primaries, transfer function, luminances, mastering display, MaxCLL/MaxFALL; ITU-T H.273 code points) and nothing is duplicated, while the act of declaring stays in our object.
3. **The gain map** (optional): a second buffer, packed with the **same** packing value, so each eye has its own gain map; and its metadata per ISO 21496-1 (per channel: gain map min and max, gamma, base and alternate offsets; base and alternate HDR headroom; which rendition is the base; the alternate colour space). With side by side packing the metadata may differ per eye, so the request takes it per eye.
4. All of it is double-buffered state, applied atomically with the surface commit, like the stereo value today.

Sketch (names provisional):
```
kde_stereo_hdr_content_manager_v1.get_content(id, wl_surface)
kde_stereo_hdr_content_v1.set_packing(packing)                 # none | side_by_side_full
kde_stereo_hdr_content_v1.set_image_description(wp_image_description_v1)
kde_stereo_hdr_content_v1.set_gain_map(wl_buffer)              # same packing as the base
kde_stereo_hdr_content_v1.set_gain_map_metadata(eye, ...)      # ISO 21496-1 fields
```

## 5. Where the description comes from (no guessing for colour)

**Stereo**, as decided: the stream's frame packing SEI first, then the container's mark (Matroska StereoMode with DisplayWidth/DisplayHeight, RFC 9559; MP4 `st3d`), then the user's choice, then the shape as the last safety net.

**Colour**, same order and no shape-like guess:
1. The stream: H.264/H.265 VUI colour code points (ITU-T H.273), the mastering display colour volume SEI and the content light level SEI. FFmpeg exports them as the frame's colour properties and side data.
2. The container: Matroska's Colour element (RFC 9559), MP4 `colr`/`mdcv`/`clli`.
3. The file, for photos: Ultra HDR (JPEG with the gain map as a secondary image and its metadata), Apple's HDR photos (HEIF with a gain map auxiliary image), ISO 21496-1 metadata in HEIF, AVIF and JPEG XL; KImageFormats decodes base, map and metadata.
4. Nothing: BT.709 SDR.

## 6. KWin, per output: the end of the chain

For each output, each frame, each layer:
1. **Unpack the eyes** for the output's stereo mode (existing): frame packing, side by side, anaglyph, or one eye.
2. **Per eye, base to linear light** with the transfer function of the description (PQ, SMPTE ST 2084; HLG, ITU-R BT.2100; sRGB/BT.709).
3. **Apply the gain map** with a weight from **this output's** HDR headroom placed between the file's base and alternate headroom (clamped to 0..1, ISO 21496-1). Two screens get two weights: the HDR TV shows the highlights, the SDR 3D TV gets the base rendition.
4. **Gamut map** to the output's primaries (EDID colorimetry; BT.2020 or BT.709).
5. **Tone map** to the output's range:
   - HDR output: PQ up to the output's maximum luminance (EDID HDR static metadata, CTA-861); SDR windows at reference white (ITU-R BT.2408, 203 cd/m²) or the user's brightness.
   - **SDR deep-colour output (the 2010-2013 3D TVs, 12 bits per channel):** HDR content tone-mapped into SDR and encoded at the output's declared depth (HDMI deep colour 30/36/48-bit, DC_30/DC_36/DC_48), so the gradients keep the source's steps instead of banding. This is "HDR to 12-bit": a property of the output, never of the program.
   - 8-bit output: the same, dithered.
6. **Encode** at the output's bit depth from a working representation with measured, adequate precision. Floating-point composition, including half float, is a candidate; it does not by itself prove lossless conversion. Working colour space, precision and handling of luminance and gamut must be evaluated before choosing it.
7. **Signal the screen**: HDMI General Control Packet colour depth; on HDR outputs the Dynamic Range and Mastering InfoFrame (CTA-861) describing the composited output, not any one layer.

## 7. Compatibility (nothing removed)

- `kde-stereo-content-v1` keeps working; its surfaces are SDR unless the program also uses upstream colour management.
- Programs that use `wp_color_management_v1` alone keep working as upstream intends.
- libstereo-declare gains the HDR calls in the same library (SONAME kept); libstereo-layer gains the HDR layer.

## 8. Does it complete HDR on the desktop?

It proposes a more complete path for static HDR and gain-map images. These are design goals, not demonstrated coverage of every format or screen:
- every HDR video and photo is declared by the shared layer, with no HDR code in programs;
- several contents in different HDR specs share one window;
- gain-map photos get an explicit carrier in this proposal;
- each output converts for its own screen: HDR, deep-colour SDR, 8-bit;
- 3D and HDR travel together, each eye with its own view and its own map.

Still outside it, to plan next:
- **Dynamic metadata** (per-frame tone mapping): HDR10+ (SMPTE ST 2094-40) is open and fits as per-frame layer state later; Dolby Vision's RPU is proprietary.
- **Capture and authoring in HDR**: Spectacle saving HDR with a gain map (AVIF/JPEG XL), Krita painting for an HDR layer.
- **The driver side**: confirm the HDR InfoFrame and deep colour on amdgpu, i915, nouveau and NVIDIA for our kernel.
- **Per-output calibration**: KWin's ICC profiles in the same chain.

## 9. First steps of the round

Before settling the HDR representation, compare PQ, HLG and gain-map reference images on HDR, deep-colour SDR and 8-bit displays, including mixed SDR/HDR content and mirrored outputs. Measure colour, luminance, clipping and banding; check that metadata stays with the correct frame and that both eyes receive consistent processing. Virtual-output captures can test buffer handling, but cannot establish the physical display's luminance or colour accuracy.

1. Measure KWin 6.7 as it is: HDR content on a deep-colour SDR output (vkms with a 12-bit EDID) and on an HDR output; record what is tone-mapped, at what depth.
2. Write the protocol XML in our plasma-wayland-protocols fork beside `kde-stereo-content-v1`.
3. KWin: the layer state and the per-output gain-map weight in the colour pipeline.
4. libstereo-layer and the frameworks (Qt Multimedia, MpvQt) declare from the stream and file.
5. Proof: LEFT and RIGHT captures per output, with known test patterns (a PQ ramp, a gain-map pair with different maps per eye) and their measured values on the HDR and the 12-bit outputs.
