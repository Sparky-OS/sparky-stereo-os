# Audit a program before moving its correction save to the shared engine

## Working recipe

1. Identify the published source package and the recipe's exact commit before choosing a working branch.
   For a published Lean Code source, unpack it and use the distribution's `plain-from-lc.py` to recover plain packaging.
   Inspect the first changelog entry before choosing `--edition-entry`; that option is for an entry combining edition changes and the Lean Code item.
2. Compare the recovered source with the recipe commit, including tests and packaging.
   A `3.0 (native)` source may have no `debian/patches/series`; its changes are already in the source.
   Account explicitly for generated changelog dates/distribution fields and Git metadata files omitted by `dpkg-source`.
3. Search current upstream source, path history, pull requests and issues.
   Record upstream's final commit IDs and compare behavior before retiring equivalent downstream changes.
   A closed pull request can have its changes applied as separate commits even when the hosting service reports no merge.
4. Trace every caller of the descriptor encoder, not just the correction action.
   Separate metadata-only correction from Save As, snapshots, generic remux output and the application's settings store.
5. For each correction path, record validation, destination, write/flush/close checks, disk read-back, restoration and when the per-file correction is cleared.
   A buffer-transformer unit test that reopens output does not establish read-back in the production save action.
6. Keep real failing fixtures before changing the writer.
   Then use the [shared JPS/MPO codec and save contract](jps-descriptor.md#save-a-correction-without-recompressing-an-existing-jps-or-mpo).
   A non-Qt consumer uses the Qt-free policy codec; it must also implement or share the complete existing-file transaction and verify both chosen eyes.
   Calling a descriptor serializer alone does not supply that transaction.

## Source boundaries found in sView 26.9+stereo3d4

The published native source corresponds to [fork commit a2b1680b](https://github.com/Sparky-OS/sview/tree/a2b1680bbfbaaf88557c91a898d5cacab16d26cc).
These are source-inspection findings for that revision, not proof about a later package or a completed migration.

| Operation | Existing behavior | Migration check |
| --- | --- | --- |
| `StImageLoader::saveImageInfo` | JPEG/JPS through `setupJps` and direct `saveFile`; no disk read-back | Temporary file, checked I/O, read-back and replacement |
| `StImageLoader::savePngInfo` | Buffer transformation through `StPngStereo::setupSter`, then direct `saveFile`; no disk read-back | Validate input and verify the temporary file before replacement |
| `StAVImage::save` | New image encoding also calls `setupJps`; setup/write results are ignored | Cover this second serializer caller when removing descriptor duplication; keep new-image encoding separate from a correction |
| MPO input | A parsed second JPEG makes the correction unsavable before the save handler runs | Remove the offer guard for supported indexed two-view disparity MPO, keeping a reason for unsupported MPOs and separate-file pairs |

`setupJps` inserts its descriptor after DQT and writes a historical trailing NUL after its comment.
The shared codec accepts that old NUL but writes exact lengths.
The shared save inserts APP3 after initial APP0/APP1 segments and preserves compatible descriptor fields.
Measure these differences on fixtures; matching the four-byte layout word alone misses placement, comment and field-preservation differences.
Lossless JPEG remains a decoder-verification refusal with its reason; APP3 itself does not require a DQT marker.

The four JPS corrections discussed in [sView PR 186](https://github.com/gkv311/sview/pull/186) appear in upstream master as `29ca5ccd`, `207566a4`, `6e853bf7` and `6a77da35`.
That does not make upstream master identical to the edition branch: right-first rows and edition-specific input/output and save behavior still need reconciliation.
Retain the downstream single-output contract and per-file state clearing while replacing byte-writing code.

## Traps

**Symptom: the clone builds an older save implementation despite being the fork's default branch.**
Cause: the recipe pins a different branch/commit.
Found by comparing the recipe's `REV` with `git ls-remote --heads` and the archive's source files.
Fix: start from the recipe pin and compare the complete published source before editing.

**Symptom: a hand-back says every write is read back, but the image handler immediately reports success after writing.**
Cause: the production call path was inferred from a unit test or from the movie writer.
Found by tracing `saveImageInfo`, `savePngInfo`, `StRawFile::saveFile` and their callers independently.
Fix: record each format's actual boundary and test disk-write corruption through the production transaction.
The [container audit](../../stereo-video/references/correction-container-audit.md) covers why video read-back and rollback are separate checks.

## Working migration for a non-Qt application

The sView +stereo3d5 implementation uses policy 1.17.6's complete-file C entry points, `stereo_jpeg_inspect` and `stereo_jpeg_correct` in `stereo-jpeg.h`.
The earlier descriptor/MPF field codec remains the only byte authority.
The complete-file entry point checks scans, indexed image ranges and field compatibility; its caller supplies storage and receives a refusal status without partial output.
This avoids copying a Qt transaction into each application or adding a Qt dependency to a non-Qt player.

1. Preserve the accepted-save/3D guard. Read the original without following a symlink, keep its identity and hash, and create a sibling temporary file.
2. Pass the bytes and an absolute packing/order to the C codec. For an MPO eye-swap action, derive the absolute order from the stored B101 order and the requested swap.
3. Write and flush the temporary file, read it byte-for-byte and compare with the candidate. Decode through the application's usual reader and compare the original raster, or both chosen MPO eyes.
4. Preserve ownership, permissions, xattrs and ACLs; flush and verify again after metadata writes. Check the original identity and hash before replacing it atomically. A refusal removes only the temporary file; the original never needs an unchecked repair.
5. Clear the per-file packing after success. Clear swap only when the saved layout represents eye order; red/cyan anaglyph keeps that correction. Reload with default options to prove the saved MPO order, including MPO stored with a `.jpg` suffix.
6. Run the existing tests plus actual correction handlers without a window. For sView, configure `USE_STEREO_KWIN=ON`, build, and run `ctest --test-dir BUILD --output-on-failure` in a writable container working directory. The added groups are `correction-transaction`, `save-languages`, `video-correction` and `mpo-loader-save`.
7. Build/install the package in a fresh container and repeat the handlers against installed libraries. Compare full expected bytes built independently with Python `struct`, plus decoded pixels; parse MPO B101/B204 independently in both byte orders. Inject successful-but-corrupted writes and require refusal with an unchanged original.

Keep the shared C ABI additive: retain previous exports/SONAME, add only the new functions and require the version that actually exports them.
Do not claim a metadata-only correction transaction for unrelated new-image exports merely because their descriptor serializer now uses the codec.

### Compatibility and test traps

**Opaque trailers:** old sView successfully saves JPEG/JPS files with data after EOI, but the earlier shared save refused them.
Found by running both implementations on a JPS with the historical NUL and an opaque trailer, and on an unmarked JPEG with the same trailer.
Fix: extend the shared engine to preserve those bytes, with complete-byte positive fixtures and an immediate unindexed second-JPEG negative fixture. Never replace an old success with an unexplained refusal.

**A swapped MPO reloads unchanged:** writing B101/B204 alone is insufficient if the application's loader still selects physical file order.
Found by loading a real two-colour MPO, saving the swap and loading again with default options.
Fix: honor the validated MPF ordinals when selecting both images; normalize recognized indexed MPO even when its suffix is `.jpg`.

**A verification test corrupts only a trailer:** changing the final file byte no longer necessarily damages JPEG pixels.
Found when the semantic decoder correctly accepted an opaque trailer change.
Fix: corrupt the actual JPEG EOI obtained from the indexed image extent for the decoder-negative test; retain separate byte-exact transaction corruption tests.

**The existing test crashes in `fwrite`:** its relative output path is unwritable and it did not check `fopen`.
Found in a container backtrace, before changing production logic.
Fix: run tests in a writable build directory, with core dumps disabled; never run package binaries on the host.

**Qt MPO-in-JPEG coverage fails only with the distribution SDK:** the native Qt image reader lacks the edition's MPO sniffing.
Found by running the same public-API consumer against each QtGui build.
Fix: use the declared edition QtGui and KImageFormats SDK for Qt save tests; distinguish this from the non-Qt sView proof. A locally built image plugin also needs its depth-mark object; use `--no-undefined` to catch that missing object at link time.
