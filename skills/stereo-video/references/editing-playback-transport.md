# Editing, playback and transport boundaries (2026-10-19)

Part of the [`stereo-video`](../SKILL.md) skill.

Kdenlive's render-comparison approach suggests a small reusable regression project: a labelled stereo clip, one title/overlay, one effect and an export.
Check source metadata, timeline preview, proxy/transcode, render output and independent playback separately; effects may assume an ordinary single view.
Keep per-eye history separate where needed, and compare an unchanged 2D project.
A successful monitor preview does not qualify every effect or higher-bit-depth MLT path.

Keep input eye-order correction separate from the display output format.
Offer the same per-file Swap Eyes action in applicable playback menus and keep it in the player's own per-file store; write it to the source file only when the person chooses to save it there.
Include portrait mono clips: being taller than wide is not sufficient evidence for top-and-bottom stereo.
Compare fullscreen controls, double-click behavior and restored file choices as interaction checks, separately from decoded pixels.

For a slow phone stream, measure source playback, compositor capture, conversion/encode, socket delivery, decode and presentation separately.
Start with a fixed synthetic moving chart over a stable route, then the same clip, resolution, codec and duration over USB, ordinary Wi-Fi and Direct Wi-Fi.
Confirm the actual route; a USB cable connected for diagnostics does not establish the streaming route.
Link utilization alone cannot locate the bottleneck. Packet-size changes need loss, latency and queue evidence; do not assume jumbo or tiny packets improve delivery.
Record viewer-reported usability as an observation, not a measured frame rate or universal performance claim.
