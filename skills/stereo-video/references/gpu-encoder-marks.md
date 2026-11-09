# A GPU recording loses its stereo mark

## Writer and verification recipe

The encoder-client implementation prepared in November 2026 converts `AVStereo3D` during encoding.
Its shared `frame_packing.c` adapts Mark Thompson's 2019 conversion proposal; it does not use the metadata-filter helper's inverted temporal mapping.
For a library caller, attach `AV_FRAME_DATA_STEREO3D` to each input frame and supply the initial layout in `AVCodecContext.decoded_side_data` before opening the encoder.
The initial side data matters for HEVC parameter sets; frame metadata can then select the packing and temporal frame identity.
`AV_STEREO3D_VIEW_LEFT` means frame 0 even with `AV_STEREO3D_FLAG_INVERT`.

| Encoder | Marking option, enabled by default | Writer or refusal |
|---|---|---|
| H.264 / HEVC VA-API | `-sei +frame_packing`; disable with `-sei -frame_packing` | CBS payload 45 through the existing raw packed-header path; a driver without packed SEI support produces an error |
| H.264 / HEVC NVENC | `-frame_packing 1`; disable with `-frame_packing 0` | `NV_ENC_SEI_PAYLOAD` first in the existing array; the existing `extra_sei` master switch also controls it |
| H.264 / HEVC Vulkan Video | `-units +frame_packing`; disable with `-units -frame_packing` | CBS payload 45 in the encoder's extra headers |
| H.264 / HEVC QSV | `-frame_packing 1`; disable with `-frame_packing 0` | `mfxEncodeCtrl.Payload`; callback errors propagate. HEVC requires the SDK's returned VPS and SPS to establish clear non-packed constraints |
| H.264 / HEVC AMF | `-frame_packing 1`; disable with `-frame_packing 0` | A marked source is refused with its packing name and the opt-out, because the inspected API has no general SEI route |

H.264 supports standard types 0–7 and their permitted quincunx variants, in both eye orders.
The new side-data names are `AV_STEREO3D_TILED`, `AV_STEREO3D_TOPBOTTOM_QUINCUNX`, `AV_STEREO3D_LINES_QUINCUNX` and `AV_STEREO3D_COLUMNS_QUINCUNX`; the decoder exports these too.
H.265 accepts types 3–5 and their permitted quincunx variants; other marked layouts fail explicitly.
Ordinary 2D has no mark. Explicit H.264 type-6 side data produces the standard 2D arrangement with content interpretation 0; explicit HEVC 2D produces no arrangement.
Spatial packing is written at keyframes and layout changes; H.264 repetition period is 1.
Temporal packing is written on every frame, with H.264 repetition period 0 and HEVC persistence 0.

To verify an encoder change:

1. Use a public-API harness to supply every layout, both orders and explicit temporal views. Include initial-only metadata, per-frame metadata and B-frames.
2. Independently parse Annex-B payload 45 and compare each syntax field; also run `trace_headers` and a software decode with `showinfo`.
3. Read back HEVC's general and every applicable sublayer non-packed constraint. A marked stream requires 0; an unmarked stream retains the encoder's original value.
4. Decode every successful stream in mpv with `--no-config --vo=null --ao=null --hwdec=no --audio=no`; count decoded frames and require normal EOF.
5. Compare unpatched and patched elementary streams byte for byte for plain 2D and for a marked source with marking disabled.
6. Require the marker check to fail on unpatched output. Check named refusals, invalid tiled dimensions, late HEVC metadata, forced keyframes and the NVENC payload budget.

The implementation was run on AMD VA-API and NVIDIA NVENC/Vulkan Video for H.264 and HEVC: 156 layout/order cases, 108 successful streams, 48 expected refusals, and 1,728 frames decoded by both FFmpeg and mpv.
Twelve plain/disabled comparisons were byte-identical, and all 102 applicable unpatched marker controls failed as expected.
Additional controls passed temporal identity with B-frames, initial-only metadata, forced NVENC IDRs and oversized unregistered SEI.
QSV and AMF compiled and their early refusal paths were exercised; that does not qualify their hardware runtimes.
The tested HEVC streams had no additional temporal sublayers; the code clears applicable sublayer flags, but this run does not claim extra-sublayer hardware coverage.
The installed amd64 candidate repeated these stream checks with its shared libraries: all 108 streams and 1,728 frames passed FFmpeg and mpv decoding, and plain/disabled outputs matched the preceding package byte for byte.
The master-based GCC build passed 6,158 standard FATE tests. A separate hardware suite passed 32 of 35; the three CUDA scaling checksum mismatches produced identical output with the unpatched binary, so they are not evidence against the writer or a reason to change its references.

## Writer traps

| Symptom | Cause | Fix and how the cause was found |
|---|---|---|
| Right-first temporal input changes frame identity after conversion | An older helper XORs frame-0 identity with eye order | Follow the decoder: `frame0 = (view == LEFT)`. Compare parsed frame-0 bits with decoded views in display order, including B-frames; eye order remains a separate content field |
| HEVC metadata first appears after encoding starts | VA-API/Vulkan already emitted parameter sets with non-packed constraint 1 | Supply initial decoded side data before encoder open; otherwise fail with the packing and marking opt-out. `trace_headers` identifies the contradiction |
| A large optional NVENC payload consumes the HEVC SEI allowance | The runtime path has a 512-byte total budget | Put the mandatory arrangement first and keep it below the budget. Test with a 600-byte unregistered payload and explicitly enable `udu_sei`; without that option the control never exercises the budget |
| Tiled output is syntactically marked but has an invalid cropped size | H.264 type 7 requires both cropped dimensions divisible by three | Reject the size before writing; test an invalid width and its explicit marking opt-out |
| A QSV callback reports an error but encoding continues | The shared caller discarded `set_encode_ctrl_cb`'s return value | Propagate the negative result through encoder cleanup; validate HEVC's returned constraints before adding a payload |
| New decoder tests appear to retain the old mapping | A reused build's baseline object is newer than edited source | Check object/source times and force rebuilding changed inputs; keep the original failure and do not alter the expected reference |
| A reused build image cannot update apt | Its sources refer to build-only archive mounts absent in the new container | Read apt's exact missing path; provide those read-only inputs or use a verified HTTPS archive configuration appropriate to the disposable runtime image. Never bypass signature verification |
| A backport appears to need a second copy of an upstream fix | The package already carries the same change in a broader downstream patch | Compare the resulting source, preserve the broader validation and record the already-carried commit; retain the upstream regression test |
| A new side-data member is correct on master but changes the package's existing ABI | The package already appended its own public members | Append the new members after the package's existing fields and bump its minor version; compare the old and new header layouts before porting |
| A mantissa test passes on master but the packaged decoder exports zero in the new fields | The package uses a split common SEI-export helper instead of master's function | Trace the package's actual decoder call path and populate both its existing exact-value representation and the added syntax fields; do not replace the existing representation |
| A carried FATE test cannot open its input | Its external sample was never included in the available suite | Record the exact missing name and check the official sample location; obtain the original fixture before qualifying the test. Do not invent a substitute and bless its checksum |

## Find the boundary before changing the driver

1. Record the render node, PCI identity, `vainfo` driver string, Mesa/libva/client versions and negotiated packed-header attributes.
2. Give the client a source whose frame packing SEI has been verified by an independent parser and a real decode with `ffmpeg -vf showinfo`.
3. Record the packed parameter and data buffers actually submitted between `vaBeginPicture` and `vaEndPicture`.
4. Compare that baseline with a client that submits an SEI through `VAEncPackedHeaderRawData` before its first packed slice header.
5. Parse the returned elementary stream, compare the submitted NAL byte for byte, decode it with `showinfo`, and check both content interpretation values, 1 and 2.
6. Apply the same required-byte check to the baseline and require it to fail.

Run this in an isolated container with only the authorized render node, core dumps disabled and no display sockets.
The build tree's [packed-SEI diagnostic](https://github.com/Sparky-OS/sparky-stereo-os-build/blob/main/sparky-os/packages/mesa/tests/vaapi-packed-sei.md) keeps the commands and tests together.
That diagnostic exercises side by side in H.264 and HEVC; it is a boundary check, not a complete packing or hardware qualification.
It compares coded-picture NALs as well, so adding a marker cannot hide a changed picture.

If the client supplies no SEI but a supplied SEI survives, the missing generation belongs in the client encoder path.
A driver receives pixels and explicit API parameters; a wide picture does not tell it whether the content is stereo or which eye comes first.
Submit the standard marker during encoding, never repair the completed recording as the normal path.

## Existing support and its owners

Mesa already gained generic H.264/HEVC raw packed-header handling in David Rosca's [MR 30927](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/30927), merged on 10 September 2024.
The VA frontend change is [1866f4d89928](https://gitlab.freedesktop.org/mesa/mesa/-/commit/1866f4d89928d325218b05134bc072ac09600c0a); radeonsi's VCN output change is [c43f8cb0b9b9](https://gitlab.freedesktop.org/mesa/mesa/-/commit/c43f8cb0b9b911147f4f19f207e0eb35c2a1ac30).
Do not rebuild that feature under a stereo-specific name.
Mesa 26.1.6's VA frontend retains raw SEI NALs and its VCN encoder copies them into coded-buffer segments; parameter sets may be regenerated separately.
The VCE H.264 and UVD HEVC paths also contain raw-header copy paths in that source version, but source inspection does not qualify those devices.

In libva, Jonathan Bian added [VAEncPackedHeaderRawData](https://github.com/intel/libva/commit/78e19a725d86b67829d2a06517b03490e8234457), Haihao Xiang added its [capability flag](https://github.com/intel/libva/commit/0e3c19e747e9185f8a4b09552775cb37c9ca31d4), and Gwenole Beauchesne added the earlier [H.264 packed SEI API](https://github.com/intel/libva/commit/f24a627826b086da72a805a5d7dd97ff1a3585b1).
Read the installed headers: clients can still negotiate the deprecated `VA_ENC_PACKED_HEADER_MISC` capability while submitting raw-data buffers.
An encoder may also create a temporary configuration with no packed-header attributes before making its real configuration.
Check the actual submission configuration, not the first `vaCreateConfig` call alone.

VA-API is a shared API, not one driver implementation for every vendor.
Intel's [media-driver](https://github.com/intel/media-driver) provides `iHD_drv_video.so`; testing Mesa radeonsi does not test that encoder.
For NVIDIA, the lowest open layer that knows the intended layout is the encoder client calling NVENC, such as FFmpeg's `libavcodec/nvenc.c`.
The [NVENC interface](https://github.com/FFmpeg/nv-codec-headers/blob/master/include/ffnvcodec/nvEncodeAPI.h) accepts `NV_ENC_SEI_PAYLOAD` arrays in the H.264 and HEVC per-picture parameters before `nvEncEncodePicture`.
The encoder runtime remains closed; open kernel modules are not where this codec SEI is authored.

## Reconcile FFmpeg's encoder paths before adding a writer

Source audit on 9 November 2026, FFmpeg master [b2b543c07924](https://git.ffmpeg.org/gitweb/ffmpeg.git/commit/b2b543c079241a63692245c26c743328385dfff6).
This identifies existing routes and prerequisites; it does not claim a production writer has been implemented.

| Encoder | Existing insertion route | Stereo handling in that snapshot |
|---|---|---|
| H.264 / HEVC VA-API | `init_picture_params` selects messages; `write_extra_header` serializes CBS SEI into `VAEncPackedHeaderRawData`; existing `sei` flags | No FPA writer; HEVC's shared `hw_base_encode_h265.c` sets the non-packed constraint to 1 |
| H.264 / HEVC NVENC | `prepare_sei_data_array` creates `NV_ENC_SEI_PAYLOAD`; `nvenc_codec_specific_pic_params` supplies the array before `nvEncEncodePicture`; existing `extra_sei` master switch and per-message booleans | No FPA writer; the HEVC use of `AVStereo3D` configures multiview encoding, which is a different representation |
| H.264 / HEVC Vulkan Video | `init_pic_params` selects messages; `write_extra_header` serializes CBS into the encoder's header buffer; existing `units` flags | No FPA writer; HEVC copies the shared non-packed constraint into its Vulkan parameter structures |
| H.264 / HEVC QSV | Shared `mfxEncodeCtrl.Payload` array; H.264's callback already builds an A/53 `mfxPayload`; HEVC's callback currently supplies HDR extension buffers | No FPA writer; the shared caller ignores the callback's return value, so a new validation error must also be propagated |
| H.264 / HEVC AMF | FFmpeg sets AUD/header and HDR metadata properties; the inspected public `VideoEncoderVCE.h` and `VideoEncoderHEVC.h` expose no arbitrary-SEI payload property | No FPA writer; do not claim a general injection API from the presence of HDR or header insertion alone |
| libx264 | Frame side data reconfigures `i_frame_packing` | Maps types 0 through 6, warns and disables the mark for inverted input, and has no mapping for quincunx SBS or tiled input |
| libx265 | `x265_picture.userSEI` carries caption/unregistered data; explicit `x265-params` pass to the library | No automatic `AVStereo3D` mapping; a library's `frame-packing` option does not establish wrapper support |

The encoder files and their history credit Mark Thompson for the VA-API encoders, Timo Rothenpieler and Luca Barbato for the NVENC implementations, and Lynne for the Vulkan encoders.
These routes already own metadata during encoding; use them instead of adding a file-repair stage.

**An upstream predecessor exists.**
Mark Thompson posted [15/18, the AVStereo3D-to-SEI helper](https://ffmpeg.org/pipermail/ffmpeg-devel/2019-October/250967.html) and [16/18, H.264 VA-API integration](https://ffmpeg.org/pipermail/ffmpeg-devel/2019-October/250966.html).
The latter adds a default-on `frame_packing` member to `sei`.
The current source lacks both changes, but a new implementation should adapt and credit them.
Their original CBS interfaces have changed, the writer requests a message even without side data, and the temporal helper exchanges frame identity for inverted content.
The current decoder derives `AVStereo3D.view` directly from `current_frame_is_frame0_flag`, independently of `INVERT`; preserve that distinction when adapting the helper.

The edition's metadata-filter series also has `ff_cbs_sei_frame_packing_params`.
Inspect it before sharing it: its automatic unsupported-type path returns `ENOENT`, and its temporal mapping applies eye inversion.
Neither behavior meets a writer that must fail on unsupported marked input and preserve frame identity.
Keep independent tests for the writer's contract instead of assuming the filter helper has it.

**Whole-spec prerequisite:** this FFmpeg snapshot has no tiled `AVStereo3DType` for H.264 type 7, and its dedicated quincunx type describes SBS only.
Represent every required packing and quincunx variant in side data before claiming full coverage from that side data.
Check the decoder's export mapping too; parsing payload type 45 is not proof that the frame retains its layout.

**Cadence reference measured with FFmpeg 9.0.2 and libx264:** 100 frames at 25 fps, `keyint=12:min-keyint=12:scenecut=0:threads=1`, ultrafast preset.
Plain 2D produced zero FPA messages; `frame-packing=3` produced nine messages and nine keyframes, repetition period 1; `frame-packing=5` produced 100 messages, repetition period 0, with alternating frame-0 flags starting at 1.
The independent Annex-B reader counted payload type 45, `trace_headers` read the periods/flags, and `ffprobe -show_entries frame=key_frame` counted keyframes.
Use this as a cadence reference, not as proof that x264 covers both eye orders or every packing.

## Check the entire specification for the production writer

Read the edition of each standard, not an enum remembered from the other codec.
H.264 V16 (06/2026) §D.1.26, pp.346–347 defines syntax; §D.2.26, Table D-9, p.387 defines types 0 through 7: checkerboard, columns, rows, side by side, top and bottom, temporal interleaving, 2D, and tiled packing.
Its Table D-10, p.389 defines the eye order; type 6 requires content interpretation 0, not 1 or 2.
Type 0 requires quincunx sampling, and type 7 requires cropped width and height divisible by three (§D.2.26, p.388).
H.265 V11 (01/2026) §D.2.16, p.302 defines syntax; §D.3.16, Table D.8, p.351 defines types 3, 4 and 5 only, with eye order in Table D.9, p.352.
Other values of that H.265 field are reserved, not extra supported modes.
Segmented rectangular frame packing is a separate H.265 SEI (§D.2.29 and §D.3.29), not another value in Table D.8.
The [ITU H.264](https://www.itu.int/rec/T-REC-H.264-202606-I/en) and [ITU H.265](https://www.itu.int/rec/T-REC-H.265-202601-I/en) editions are the references; do not distribute their PDFs with a patch.

## Traps found by the boundary test

**Symptom: NVIDIA Vulkan returns `VK_ERROR_INCOMPATIBLE_DRIVER` although CDI supplies the ICD.**
First read the ICD path inside the container; CDI can place it under `/etc/vulkan/icd.d`.
In a minimal VA-API probe image, `VK_LOADER_DEBUG=all` found the manifest and `libGLX_nvidia.so.0` but could not obtain `vkCreateInstance`.
`LD_DEBUG=libs` then showed unsuccessful lookups for `libEGL.so.1`.
Installing the archive's verified `libegl1` package inside the disposable image allowed H.264 and HEVC Vulkan encoding to run.
An ICD file and successfully loaded vendor library alone do not establish a complete runtime.

**Symptom: unmarked HEVC has non-packed constraint 0, despite having no frame packing SEI.**
This was observed with FFmpeg 9.0.2's NVENC path; the Vulkan baseline set it to 1.
H.265 V11 §7.4.4, p.90 allows a zero constraint whether or not such SEI is present.
Read each backend's parameter sets before defining the 2D byte-identity control; forcing this bit to 1 changes an otherwise valid baseline.

**Symptom: FFmpeg's output banner says Stereo 3D, but decoding the encoded file reports none.**
The banner can describe carried side data even when the VA-API encoder never writes payload type 45.
The remedy belongs in the encoder's side-data-to-SEI conversion, with a visible failure for an unsupported requested representation.
Find the cause by comparing decoded input side data, submitted packed buffers and parsed output NALs, not by trusting the output banner.

**Symptom: HEVC decodes as stereo, but its profile constraint forbids the marker.**
An SEI-only diagnostic retains the client's `general_non_packed_constraint_flag=1` in VPS and SPS.
H.265 V11 §7.4.4, p.90 says this flag means there are “no frame packing arrangement SEI messages”; sublayer constraints follow on p.91.
The production client must clear the applicable constraints when it writes frame packing information.
Find the cause with `trace_headers` on both the submitted parameter sets and the final stream; decoding successfully is not a conformance check.
The diagnostic records this conflict explicitly and does not claim a complete encoder fix.

**Symptom: the first bytes of the encoded buffer contain headers, but the picture is missing.**
Raw headers and the hardware-produced slice can occupy separate `VACodedBufferSegment` entries.
Consume the whole returned segment chain in order, checking status and size, instead of only its first entry.
Find the ownership of each segment in the driver's raw-header output and feedback functions.

## Measured scope

On 9 November 2026, the mesa-vaapi-frame-packing-61b lane ran Debian Mesa 26.1.6, libva 2.24.1 and FFmpeg 9.0.2 on an AMD Renoir-family VCN path.
Four type-3 cases, H.264 and HEVC with both eye orders, retained the exact submitted SEI, decoded with the expected layout/order and kept identical coded-picture NALs against the baseline.
All four required-marker checks failed on the baseline as intended.
The HEVC diagnostic's non-packed constraint conflict was recorded separately.
This establishes the boundary for those cases; other packings, generations, profiles, temporal pairing and complete conforming production output still need their own checks.
