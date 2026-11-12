# Read-back is one part of a container correction transaction

## Working recipe

1. Identify the published writer and the exact format branch.
   Confirm the person's accepted save action is its caller and that a failed save keeps the per-file correction.
2. Record whether the writer changes the original file or a temporary copy.
   Check partial-write/tool failures, flush/close failures, read-back mismatches and the result of any restore attempt separately.
3. For a verified replacement, edit a temporary file beside the original, read it through the normal player and an independent format parser, then replace only after validation.
   Preserve the original on every failure and report the reason.
4. Keep container metadata, stream SEI precedence, track selection and media payload preservation as independent assertions.
   A metadata reader reporting the requested layout does not prove that every other byte or packet stayed intact.

## sView 26.9+stereo3d4 source audit

At [the published-source commit](https://github.com/Sparky-OS/sview/blob/a2b1680bbfbaaf88557c91a898d5cacab16d26cc/StMoviePlayer/StVideo/StVideoStereoMark.cpp), `StVideoStereoMark::save` reads the layout after a successful write.
It also refuses a conflicting stream declaration before changing the container.
Neither branch uses a temporary file.

| Format branch | Existing write and read-back | Remaining transaction gap |
| --- | --- | --- |
| Matroska/WebM | Runs `mkvpropedit` on the original, then reads the first decoded picture/container layout | Tool failure can leave changes; on read-back mismatch it re-edits the old StereoMode, not a saved byte copy, and ignores that restore result |
| MP4/MOV | Edits moov in place, checks positional writes/fsync/close and then reads the player layout | Saves only the overwritten region and file length; ignores failed restoration after write or read-back failure; no verified temporary replacement |

MP4's existing size rule is separate from transactional safety.
Its st3d insertion is allowed only when moov can grow without moving media offsets, at the end or using adjacent free/skip space.
Preserve that refusal unless the shared engine gains and tests a broader operation.
Matroska/WebM's layout allowlist and stream-first conflict refusal remain distinct from whether a save is atomic.

**Symptom: a failed read-back is reported as restored even if restoration failed.**
Cause: the caller ignores `restoreRegion` or the second `mkvpropedit` result.
Found by following every exit after the first write, including tool/write failure before the read-back branch.
Fix: exercise failures before and after partial writes; keep the original untouched until a verified replacement is ready.
Do not treat restoration of the old layout value as proof that the original file's bytes were restored.

The table records the +stereo3d4 baseline. The +stereo3d5 migration uses the verified replacement below.
For image callers and the native-source/recipe traps, see the [correction-writer audit](../../stereo-pictures/references/correction-writer-audit.md).

## Verified replacement recipe

Copy large media files to a sibling temporary file with bounded streaming I/O; do not keep a whole movie in a byte vector.
Run `mkvpropedit` or the moov/st3d edit only on that copy.
Read the resulting layout through the normal player. For MP4, also read back the exact edited moov region.
Compare codec identity/extradata and every compressed packet before and after; a tool's success exit status and the new layout alone are insufficient.
Flush, seal the verified temporary bytes with a streaming hash, preserve file attributes, and check both that hash and the original's identity/hash before replacement.
Keep the existing unsupported-layout, conflicting-SEI and no-room refusals.

Test real Matroska files through all 15 StereoMode values using `mkvmerge -J` as an independent oracle.
Include a second video track, checking that the first stays unchanged, and WebM's narrower allowlist.
For MP4, walk boxes independently to inspect st3d for both insertion and update; retain the faststart/no-room refusal.
Use `ffprobe -show_packets -show_data_hash sha256` to compare compressed packet bytes, sizes, stream indices and timestamps.
These are exact media-payload checks, separate from container metadata that the tool may legitimately reorganize.

**Symptom: the failed-save test returns a reason but the original bytes changed.**
Cause: the tool edited the original before failing, or returned success after corruption; the old rollback did not restore its bytes.
Found with a tiny executable named `mkvpropedit` at the front of the test-only PATH, which overwrites the target header and exits either 2 or 0.
Fix: apply the tool to the sibling temporary file. Both tests must refuse, retain byte-identical originals and remove their temporary files.
Run the same test on the baseline first; sView +stereo3d4 fails both cases.

**Symptom: a frame-packing fixture appears to lack its detailed layout in ffprobe JSON.**
Cause: the installed FFmpeg reports only the Stereo 3D side-data type in that output schema.
Found by inspecting the actual bounded side-data output and the `trace_headers` bitstream-filter log.
Fix: verify the fixture's `frame_packing_arrangement_type` directly with `trace_headers`, then exercise the real player's stream-conflict refusal. Do not substitute guessed JSON fields.
