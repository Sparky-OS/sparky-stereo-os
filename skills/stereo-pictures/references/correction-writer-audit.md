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
