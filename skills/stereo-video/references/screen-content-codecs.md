# Screen-content codec comparisons (checked 2026-10-14)

Part of the [`stereo-video`](../SKILL.md) skill.

Compare codecs at matched decoded text quality and unchanged eye geometry, not equal QP numbers.
Record each eye's text-region SSIM, the tolerance used to match it, frame count, refresh, GOP and B-frame/lookahead settings, and encoded packet bytes separately from container and network overhead.
Keep a coarse-quality negative control and an eye-swap control.
A short static-text chart with a moving window is not a sustained bandwidth or latency qualification.
Use Matroska's registered `StereoMode` for fixtures and preserve the mark after transport.

[Upstream x265 SCC](https://x265.readthedocs.io/en/master/cli.html#screen-content-coding-scc-options) needs an `ENABLE_SCC_EXT` build and describes intra-block-copy modes.
This does not prove palette or adaptive colour transform support.
The measured FFmpeg/x265 combination logs `Unknown option: scc` but returns success and writes ordinary Main-profile HEVC.
Reject that result as an SCC comparison; check the emitted profile/extension and decoder support as well as the exit status.
A VA-API profile query and a real encode are required before claiming hardware support; an encoder listed in FFmpeg help is insufficient.
Credits: FFmpeg, x264/VideoLAN, x265/Multicoreware, Mesa, libva and Android developers.
