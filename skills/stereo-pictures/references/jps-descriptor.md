# JPS reader and writer metadata

The writer implements VRex's *General Purpose Stereoscopic Data Descriptor* (1997), pages 3 to 6, available from the [2011 archive](https://web.archive.org/web/20111030182549id_/http://www.vrex.com/developer/sterdesc.pdf) and [Paul Bourke's mirror](https://paulbourke.org/stereoscopy/stereoimage/spec.pdf).
Both copies used for this implementation have SHA-256 `7532f98405731d0d73f1e57d6df8c4641fd41b272c18cc785f40d25d6feff59a`.

Pass a `QImage` to `QImageWriter` with format `jps`.
`Stereo3DLayout` describes the stored pixels: `mono`, `rowInterleavedLeftFirst` or `RightFirst`, `sideBySideLeftFirst` or `RightFirst`, `topBottomLeftFirst` or `RightFirst`, `anaglyphRedLeft` or `anaglyphRedRight`.
The two suffix variants are complete names, such as `topBottomRightFirst`.
An absent layout retains the existing writer convention: canonical left-first side-by-side input is exchanged into right-first storage.
An explicit layout preserves the input pixel arrangement.
The shared policy’s legacy `anaglyphCyanRed` name is accepted as red-left anaglyph.
Unsupported layouts fail before writing and log a refusal translated into ten languages.

Additional QImage text fields, also reported by the reader:

| Field | Values and default |
|---|---|
| `Stereo3DJpsHalfHeight` | 0 or 1; default 0 |
| `Stereo3DJpsHalfWidth` | 0 or 1; default 0 |
| `Stereo3DJpsSeparation` | 0 to 255 pixels between side-by-side or top/bottom views; otherwise 0 |
| `Stereo3DJpsDisplay` | Mono: 0 both eyes, 1 left, 2 right; stereo: 0 |
| `Stereo3DJpsComment` | ASCII; default empty; at most 65517 bytes |

The descriptor's low byte is type, then layout/display, flags, and separation/reserved, in increasing significance.
Type 0 is mono; type 1 uses layout values 1 rows, 2 side-by-side, 3 top/bottom, 4 anaglyph.
Bits 16 and 17 mark half height and width; bit 18 marks left first or red-left.
Other flag bits and the mono reserved byte are written zero.
The page 4 width description repeats “height”; the width flag's name on pages 3 and 6 establishes its meaning.
The separation diagram spans bits 24 to 31; the prose's “24-32” is an eight-bit-field typo.

APP3 contains `_JPSJPS_`, a big-endian 16-bit descriptor length of 4, the big-endian 32-bit descriptor, a big-endian 16-bit comment length and its bytes.
The earlier fixed right-first JPEG comment is removed because it would misdescribe explicit other layouts.
Readers report fields without changing pixels; half-size flags never trigger resampling.
The shared picture engine removes a declared separation when taking out the two eyes.

The writer tests inspect each APP3 independently and reopen every successful write.
They cover both orders, mono display choices, all four half-size flag combinations, separation including 255, comments, and refusals that leave the device bytes untouched.

When replacing an existing file, open a `QSaveFile`, pass that device to `QImageWriter`, and commit only after writing succeeds.
A filename-based `QImageWriter` can open and truncate its destination before the format handler validates the image.
The handler's unchanged-buffer refusal tests do not establish atomic replacement of an existing file.
Read the committed file back through the format reader.


## Save a correction without recompressing an existing JPS or MPO

With stereo-layer 1.17.5, call `Stereo::Picture::saveCorrection(path, options)` from the person's accepted **Save to file** action.
Use the returned `success` / `error`; clear the application's per-file correction only after success, then reload with default options.
Loading never saves.
Applications construct no descriptor bytes.

```cpp
Stereo::Picture::Options options;
options.inputLayout = Stereo::Picture::Layout::SideBySide;
options.inputOrder = Stereo::Picture::EyeOrder::RightFirst;
const auto saved = Stereo::Picture::saveCorrection(path, options);
if (saved.success) {
    clearPerFileCorrection();
    reloadPicture();
} else {
    showError(saved.error);
}
```

`None` uses the current declaration/picture policy; an explicit packing overrides an incorrect declaration.
`swapEyes` reverses that interpretation.
`View::Mono` writes mono JPS; left/right preview choices keep both views.
The legacy shared swap xattr is applied and consumed by a successful save.
Other attributes, ACLs, ownership and permissions are preserved; failure keeps the original file.
Use an absolute layout/order for an idempotent save.

The one Qt-free codec is `libstereo-policy`'s `stereo-jpeg.h`, used by the picture library and KImageFormats +stereo3d7.
Build stereo-layer first against plugin +stereo3d6, then the new plugin against policy >=1.17.5; this avoids a dependency cycle.
The format plugin handles image encoding; the picture library handles the existing-file transaction.
A temporary file beside the original is written, read byte-for-byte, decoded through the ordinary picture loader and compared against the chosen eyes before atomic replacement.
Keep saves serialized; the check before rename is not a lock against another program modifying the file in the last interval.
No JPEG encoder runs in this operation.

For JPS, the descriptor APP3 is replaced or inserted after initial APP0/APP1 segments.
All other bytes remain unchanged, including every scan of a progressive JPEG, EXIF/XMP, colour profiles, comments and opaque metadata.
Existing compatible half-size flags, separation, display, descriptor extensions and ASCII comments are retained.
Unknown/reserved fields, ambiguous duplicate descriptors and unsupported layouts are refused with a message.
Lossless JPEG is currently refused because the picture reader cannot verify its decoded eyes; inserting APP3 does not require DQT.
A missing DQT is a limit of older per-program writers, not a JPS format rule.

For MPO, read CIPA's *Multi-Picture Format*, DC-007-Translation-2009, [specification mirror](https://seos.fr/blog/doc/DC-007_E.pdf), §§5.2.3, 5.2.4.2, 5.2.4.5 and 6.2.2.2.
B101 (`MPIndividualNum`, LONG, count 1) numbers disparity viewpoints from left to right.
B204 (`BaseViewpointNum`, LONG, count 1) refers to that numbering: when B101 labels are swapped, update **both B204 references** to retain the same physical calibration camera.
Two B101 edits alone leave that reference pointing to the other camera.
Preserve numeric calibration, MPEntry offsets/sizes/dependencies and all other bytes.
Both TIFF byte orders are supported.
This operation requires an existing complete two-image disparity MPO with valid B101/B204 fields; it refuses gain maps, missing fields, unknown numbering, invalid ranges or cyclic directories instead of guessing or rebuilding indexed data.

**Verification:** run the library's `picturesavetest` with the candidate plugin in `QT_PLUGIN_PATH`.
Its expected MPO is built by a separate TIFF field parser: only the two B101 and two B204 LONG values may differ.
The JPS tests remove the changed APP3 and compare every remaining byte.
Reopen every write and compare layout/order and both decoded eyes.
Include sequential/progressive scans, both MPO byte orders, misleading signatures in opaque segments, truncated segments, duplicate descriptors, invalid TIFF offsets, and failures leaving the original unchanged.
Use a clean installed consumer which only calls `saveCorrection` and `load`, with no byte-writing workaround.

**Trap: a per-program lossless correction writer.** Symptom: an editor duplicates the JPS APP3 serializer or patches MPO ordinals itself.
Cause: the shared layer previously offered image encoding and a temporary swap xattr, but no descriptor-only save.
Found by tracing save handlers and comparing the written fields with the format specifications.
Fix: the explicit shared save above, one descriptor codec used by the format writer and the transaction, and a temporary copy verified before replacement.

**Trap: JPEG fill bytes dropped beside APP3.**
ITU-T T.81 Annex B permits extra `FF` fill bytes before a marker; they are outside the descriptor.
A replacement span starting at the first `FF` in `FF FF FF E3` drops two bytes even though the decoded eyes still match.
Keep the marker's own start separately from its fill prefix, preserve the prefix, and skip it when sniffing headers.
Found by the byte-equality regression: a swap shortened a 773-byte fixture to 771 bytes before the fix; the corrected save changes only its order flag.
The [JPEG specification](https://www.w3.org/Graphics/JPEG/itu-t81.pdf), Annex B.1.1, is the reference.
