# Split interleaved stereo work into reviewable UMS offers

Use this recipe when an integration branch mixes renderer profiles, conversion support and fixes to existing conversions.
Read the current UMS contribution rules before preparing offers.

## Recipe

1. Fetch upstream `main` and record its hash.
   Search commits on the affected paths, open and merged pull requests, then issues for each subject.
2. Keep the integration branch intact.
   Make separate worktrees from the recorded upstream revision for independent subjects.
   Rebuild each subject from its complete final diff rather than picking its first commit and assuming later repairs are unrelated.
3. Commit a refusal fix with its warning and allowed-stream controls.
   Commit a stale-mark fix separately, with tests that encode and inspect the received layout.
   A renderer profile gets its own branch and matching tests, including identities that must not match.
4. If new enum values depend on both fixes, merge those prerequisite branches into a temporary baseline and put only the new-layout change above it.
   Record the baseline hash and export the new-layout patch relative to that baseline.
   Wait for the prerequisites to merge before targeting upstream `main`, or explicitly target the prerequisite base during review.
5. Build every branch in its own target directory.
   Reuse a dependency cache, never compiled classes from another branch.
   The Java-only offline recipe used here is:

   ```sh
   mvn -o -B -Dmaven.gitcommitid.skip=true \
     -Dskip.installnodecorepack -Dskip.corepack -Dmaven.antrun.skip=true \
     -Dmaven.repo.local="$CACHE" -Dtest="$TESTS" test jar:jar
   mvn -o -B -P linter -Dmaven.repo.local="$CACHE" \
     -Dcheckstyle.includes="$CHANGED_JAVA" validate
   ```

   To check test sources as well, set `<includeTestSourceDirectory>true</includeTestSourceDirectory>` in the Checkstyle plugin configuration of a temporary POM.
   That parameter has no Maven user property in plugin 3.6.0; a similarly named `-D` flag does not enable it.
   Remove the worktree's Checkstyle cache before that audit and inspect the generated XML to confirm both production and test paths were checked.
   Cached clean files are omitted from the XML, so a successful empty audit is not evidence that the requested files were visited.

   These flags skip frontend installation and external binary downloads.
   They establish a Java build and the selected tests, not a distribution assembly or the complete CI matrix.
   Run in an isolated container with no network for tests.
6. Keep the new tests while restoring only the affected production code to its base.
   Record the expected failures, restore the patch, then build and test green again.
   A new enum can make an old production file fail compilation, so use a semantic mutation for that case instead of calling a compiler failure a regression test.
7. Save one template-shaped pull-request body per subject, with exact tests and device gaps.
   State dependencies explicitly.
   A Java profile match or an emulated SSDP announcement does not establish playback on a physical phone.

## Traps

- **Cherry-picking interleaved repairs conflicts or builds an incomplete fix.**
  The initial refusal, a forced-streaming repair, a warning and newly accepted enum values touched the same method across unrelated subjects.
  Comparing the final `StoreItem` diff against upstream showed that the refusal only needed a guard before the forced-streaming return and a supported-input classifier.
  Rebuild those together with their tests, leaving layout mappings for the later offer.
- **A successful conversion keeps the old 3D mark.**
  FFmpeg 6.1.1 copied Stereo 3D frame side data through `stereo3d`.
  Encoding top and bottom as side by side with x264 still emitted top and bottom; mono MPEG-2 still carried JP3D stereo data.
  End the conversion with `sidedata=mode=delete:type=STEREO3D` and inspect the encoded output.
  Stock MPEG-2 then has no replacement stereo mark, so do not claim this fixes MPEG-2 automatic 3D switching.
- **A passing byte comparison skips its actual FFmpeg check.**
  Returning normally when no FFmpeg executable exists reports a pass.
  Use a JUnit assumption so the missing executable appears as a skip, and record whether the measured run skipped anything.
- **Old production code cannot compile against the new enum's tests.**
  Missing enum constants and helper methods are a compiler result, not a measured wrong picture.
  Keep the new API and plant a wrong eye order or remove the conversion dispatch to demonstrate a runtime failure.

- **A renderer profile test inherits unrelated style failures from a large test class.**
  Enabling test-source linting exposed existing whitespace and varargs errors in `RendererConfigurationTest`.
  Put the new profile assertions in a dedicated test class and keep the unrelated class unchanged.
  The changed-file audit then checks exactly the new test, without unrelated cleanup in the offer.

## Useful properties

A formula-coded luma image identifies both the eye and the sample address.
Compare raw 4:4:4 output against an independently constructed reference, not a checksum that may stay unchanged when the views swap.
For alternating frames, write left and right raw frames independently, concatenate in each eye order, then check the paired output against the same reference.
The encoded mark regression can use the actual `getVideoFilterOptions` result with an existing SEI-only fixture, so a test of a copied filter string cannot conceal a missing production filter.

Recorded from the UMS offer split in November 2026, lane ums-dlna-headsets-94.
