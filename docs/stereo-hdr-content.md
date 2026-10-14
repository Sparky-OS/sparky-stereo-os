# Stereo and HDR in one declaration: `kde-stereo-hdr-content`

Design, 2026-10-13, by Daniel Ramos for Sparky Stereo OS.
Status: design; nothing is built yet, and it has not been tried on an HDR screen.

## 1. The problem

Upstream colour management (`wp_color_management_v1`, wayland-protocols staging) gives **one image description per `wl_surface`**.
KWin 6.7 implements it: `wp_color_management_surface_v1_set_image_description` (`src/wayland/colormanagement_v1.cpp:217`), per-surface feedback (`:83`), tone mapping in `src/core/colorpipeline.cpp`.

That model fails the ordinary case:
- **An ordinary program's window is one SDR surface.** An HDR video or photo inside it has nowhere to be declared. The program would have to turn its whole window, interface included, into HDR, and normal programs never do. So upstream HDR needs "HDR-programmed" programs.
- **Two pictures in different HDR specs in one window** (an Apple HDR photo beside an Ultra HDR one, an HLG clip beside a PQ one) cannot be described at all; the program must convert both into one description itself, before the compositor sees them.
- **Gain-map photos have no carrier.** A gain-map photo is two pictures: a base and a map of how much brighter each pixel may go. No Wayland protocol carries the second picture.

Stereo 3D hit the same wall first, and solved it: the content gets **its own layer** (a subsurface inside the flat window), declared on its own, with no work by the program.

## 2. The principle

The same contract as stereo: **programs describe what the content is; KWin's outputs decide the screen.**
- The declaration belongs to **each content layer**: a video, a photo, a canvas. Not the window, not the display.
- The rest of the desktop stays SDR, exactly as it stays flat around a 3D window.
- One declaration carries both halves: a layer declared for HDR carries its stereo layout in the same object, and a stereo layer can carry HDR.

## 3. Who creates the layer: the shared frameworks, never the program

Players and viewers need **no HDR code and no stereo code**.
The shared layer reads the stream or file and declares:

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
6. **Encode** at the output's bit depth from a composition kept at half float, so no step in the middle loses depth (house formats: one format inside, conversions at the edges).
7. **Signal the screen**: HDMI General Control Packet colour depth; on HDR outputs the Dynamic Range and Mastering InfoFrame (CTA-861) describing the composited output, not any one layer.

## 7. Compatibility (nothing removed)

- `kde-stereo-content-v1` keeps working; its surfaces are SDR unless the program also uses upstream colour management.
- Programs that use `wp_color_management_v1` alone keep working as upstream intends.
- libstereo-declare gains the HDR calls in the same library (SONAME kept); libstereo-layer gains the HDR layer.

## 8. Does it complete HDR on the desktop?

It completes the path **from any content to any screen** for static HDR:
- every HDR video and photo is declared by the shared layer, with no HDR code in programs;
- several contents in different HDR specs share one window;
- gain-map photos get a carrier for the first time;
- each output converts for its own screen: HDR, deep-colour SDR, 8-bit;
- 3D and HDR travel together, each eye with its own view and its own map.

Still outside it, to plan next:
- **Dynamic metadata** (per-frame tone mapping): HDR10+ (SMPTE ST 2094-40) is open and fits as per-frame layer state later; Dolby Vision's RPU is proprietary.
- **Capture and authoring in HDR**: Spectacle saving HDR with a gain map (AVIF/JPEG XL), Krita painting for an HDR layer.
- **The driver side**: confirm the HDR InfoFrame and deep colour on amdgpu, i915, nouveau and NVIDIA for our kernel.
- **Per-output calibration**: KWin's ICC profiles in the same chain.

## 9. First steps of the round

1. Measure KWin 6.7 as it is: HDR content on a deep-colour SDR output (vkms with a 12-bit EDID) and on an HDR output; record what is tone-mapped, at what depth.
2. Write the protocol XML in our plasma-wayland-protocols fork beside `kde-stereo-content-v1`.
3. KWin: the layer state and the per-output gain-map weight in the colour pipeline.
4. libstereo-layer and the frameworks (Qt Multimedia, MpvQt) declare from the stream and file.
5. Proof: LEFT and RIGHT captures per output, with known test patterns (a PQ ramp, a gain-map pair with different maps per eye) and their measured values on the HDR and the 12-bit outputs.
