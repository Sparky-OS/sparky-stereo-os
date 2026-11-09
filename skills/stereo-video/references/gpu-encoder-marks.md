# A GPU recording loses its stereo mark

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
