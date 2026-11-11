# JPS reader and writer metadata

The writer implements VRex's *General Purpose Stereoscopic Data Descriptor* (1997), pages 3 to 6, available from the [2011 archive](https://web.archive.org/web/20111030182549id_/http://www.vrex.com/developer/sterdesc.pdf) and [Paul Bourke's mirror](https://paulbourke.org/stereoscopy/stereoimage/spec.pdf).
Both copies used for this implementation have SHA-256 `7532f98405731d0d73f1e57d6df8c4641fd41b272c18cc785f40d25d6feff59a`.

Pass a `QImage` to `QImageWriter` with format `jps`.
`Stereo3DLayout` describes the stored pixels: `mono`, `rowInterleavedLeftFirst` or `RightFirst`, `sideBySideLeftFirst` or `RightFirst`, `topBottomLeftFirst` or `RightFirst`, `anaglyphRedLeft` or `anaglyphRedRight`.
The two suffix variants are complete names, such as `topBottomRightFirst`.
An absent layout retains the existing writer convention: canonical left-first side-by-side input is exchanged into right-first storage.
An explicit layout preserves the input pixel arrangement.
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
