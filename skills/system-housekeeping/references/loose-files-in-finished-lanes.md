# Loose files outside a finished lane's clones

A clone audit does not settle the files beside the clones. A finished build
folder can also contain a hand-written compiler probe, an earlier patch, a
modified dependency without Git metadata, a source archive and the only copy of
an experiment's evidence. Give those files their own trace before removal.

## Recipe

1. Read the owning lane's report and request. List top-level entries with a
   bounded walk on one filesystem, never following symlinks. Stop at repository
   boundaries already covered by another trace; record that trace instead of
   auditing the repositories again. Protected homes, configuration, credentials
   and key files stay outside content scans. Record their names and sizes only
   where permitted. An exclusion inside a directory prevents claiming that the
   whole directory was checked.
2. Give every completed top-level entry one verdict and a proof. Keep deferred
   and excluded entries in a separate pending table. A partial milestone's
   removal script must cover only its completed entries, never the enclosing
   root. Use a per-file manifest for directories containing several kinds of
   material, and let any unmatched authored file hold the whole entry.
3. Prove **generated** by its input and regeneration command. For an unpacked
   source tree, compare both its complete relative regular-file list and every
   file's SHA-256 against archive members. Keep the archive independently before
   relying on it. Matching a few files or a directory name is insufficient.
   CMake outputs, objects and caches need their own proof; a hand-written source
   can live inside a build directory.
4. Prove **delivered** with a named retained regular file and equal hashes, or
   with a demonstrated equivalent patch. Check the path's symlink components and
   the device/inode: a lane's sources link can resolve back into the candidate.
   An already-proved clone may supply a content comparison without repeating its
   branch audit, but it must remain available under that earlier trace's terms.
5. For **evidence kept elsewhere**, identify the report citing the retained copy
   and verify the copy. A download receipt alone does not preserve the downloaded
   snapshot. Treat ambiguous research evidence conservatively when the brief
   requires preservation.
6. Preserve **found** files independently under a keep directory with the
   original relative paths. Record original path, size, SHA-256, copy path and
   request line. Check both hashes again after copying and reject symlinks or
   identical inodes as independent copies. Enforce the brief's preservation cap
   before copying; report a prospective overflow rather than omitting files.
   Say explicitly when this verdict means uncertainty within a bounded search,
   rather than an exhaustive proof that no other copy exists.
7. Separate preservation from landing. Read a patch against the current design
   and delivered generation. A draft may add nothing beyond a shipped patch, or
   may contain an error already corrected there. Preserve the draft if required,
   but name the correction rather than recommending the older draft for landing.
   Identify useful unmatched tests separately from downloaded references and
   conservative binary backups.
8. Hand back a tab-separated top-level trace, per-file proofs, found-file list,
   verified-copy manifest and a literal removal script. Report candidate sizes
   separately from actual reclaimed space; do not double-count hard-linked
   inodes or nested entries. Recheck source/copy hashes before applying a later
   removal. Never execute a script delivered only for review.

## Removal script form

```sh
#!/bin/sh
set -eu
# REVIEW ONLY: source tree matches every archive member by SHA-256 and file list.
# The archive is independently preserved at the path named in the trace.
rm -rf -- /absolute/literal/path/to/checked-source
# HOLD: found file; its independent copy is verified in the keep manifest.
# Review the found-work disposition before authorizing this entry's removal.
```

Use one literal command per approved top-level entry with its proof immediately
above it. Do not use a glob, loop variable or a command naming the whole held
root. Omit commands for pending entries and for found entries still held by the
review. If the brief permits removing a found entry after preservation, its
comment must name the verified-copy manifest and the completed hash check.

## Observed traps (ORDER 617c, first slice)

- **Symptom:** a lane's retained sources appear to match the candidate exactly.
  **Cause:** the sources path is a symlink back into the held folder.
  **Fix:** inspect links and device/inode before accepting the second copy.
  **Found by:** listing the lane's sources links before the content comparison.
- **Symptom:** an extracted source tree appears fully checked after a hash walk.
  **Cause:** credential exclusions silently omitted some files.
  **Fix:** make exclusions visible and hold the entire top-level entry; a strict
  completed-entry walk must reject any unexamined boundary.
  **Found by:** the metadata file count exceeded the content manifest count.
- **Symptom:** `git patch-id --stable` emits no identifier for a nonempty delta.
  **Cause:** the generated unified diff has no Git file headers.
  **Fix:** provide a `diff --git a/path b/path` header for each file, then require
  a nonempty identifier before comparing it with the delivered patch.
  **Found by:** a four-file pose delta produced no output; with headers it had
  the same stable patch identifier as the delivered bridge patch.
- **Symptom:** an older embedding patch has a different patch identifier.
  **Cause:** the delivered generation removes a duplicate disconnect button.
  **Fix:** inspect the complete payload difference and the prior trace's named
  correction; preserve the older draft without proposing its error for landing.
  **Found by:** comparing the complete patch bodies isolated one XML hunk.

The first slice established archive equality for two unpacked trees and retained
uncertain loose files with verified hashes. It did not establish that every build
directory, cache or protected file in the held roots was removable.

## Completing mixed build, cache and stage trees

- Read a CMake build's `CMAKE_HOME_DIRECTORY`, source recipe and target/dependency
  manifests, or Meson's `build.ninja` and `meson-info`, before naming its
  regeneration command. Generated-header tags, ELF/object formats and declared
  output locations support a generated verdict. Preserve unmatched scripts,
  patches, source inputs and useful logs rather than classifying everything below
  the build directory by its name. An install manifest identifies an installed
  prefix; compare installed bytes with build outputs and source archive members
  where available.
- A Gradle user-home cache is identified by its actual `wrapper/dists`,
  `caches/modules-2`, transforms, journals, native helpers and daemon state.
  Name the Gradle version and dependency-resolution/build recipe that recreates
  those outputs. An `init.d` script or other unexpected authored input needs a
  separate verdict. For ccache, inspect `CACHEDIR.TAG` and its cache-directory
  signature along with the result/manifest layout. Do not read a protected user
  home merely to establish a cache verdict for its neighbour.
- A staged APK's release metadata can name its source commit, build helper and
  expected hash. Verify that hash before calling it that build's output, and
  preserve the release metadata if no retained copy exists. This identifies the
  artifact and its recipe; it does not prove a fresh build is byte-reproducible or
  repeat the original runtime qualification. Never open a signing key to do it.
- Check staged packages against independent published pool files by full hash,
  not directory names containing `published`. Unmatched packages or source
  tarballs remain held when the available evidence does not settle their
  provenance. Source copies already present in a lane or an already-audited clone
  can be compared by content without fetching or repeating its branch audit.
- **Symptom:** retained content fits a byte cap but `du` exceeds it.
  **Cause:** many small files consume whole filesystem blocks and directories
  consume additional space. **Fix:** budget allocated space as well as content
  bytes before each new copy. If adjusting a newly-created duplicate, verify the
  unchanged original before removing only the duplicate, record it as uncopied,
  and hold its containing source entry. **Found by:** a preservation pass remained
  below 300 MB of content while its allocated footprint exceeded that cap.
- **Symptom:** final manifest assembly stalls after file comparisons finish.
  **Cause:** testing every file against every top-level entry with repeated path
  parent construction. **Fix:** group rows by root/entry while scanning, or use
  normalized path prefixes; checkpoint the per-file results before copying and
  aggregation. **Found by:** the file comparisons completed before the final
  grouping step; replacing repeated parent construction removed that delay.

Keep explicit metadata-only rows for protected files and excluded repositories.
A copied subset never authorizes removing their enclosing directory. If the
preservation cap prevents keeping every uncertain file, list each uncopied path,
size and available hash, mark the whole top-level entry held, and still report
the completed verdicts for the other entries. A review-only removal script can
include a found-bearing entry only when the brief permits it and every found
file has an independent verified copy, with no protected, uncopied or unexamined
boundary inside that entry.
