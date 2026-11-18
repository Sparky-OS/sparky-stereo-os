# Processing models as install-time profiles

## Working recipe

1. Keep one functional profile in one selectable package.
   The application and AppCenter never depend on all of the profiles.
   Meta and large profiles remain separate choices.
   Pin every owner address, byte count and SHA-256; include the original licence text and its own hash, not the model body.
   A software licence does not establish rights to unrelated training weights or data.
2. Use the shared engine in `sparky-stereo-apt`, beside its existing install-download reader.
   Source control declares `XB-Sparky-Install-Download-Size` and `XB-Sparky-Install-Download-Source`; inspect the resulting binary control and Packages index too.
   Both apt and AppCenter use that one declaration and NetworkManager metering decision.
   Show the current pinned size, publisher, terms and purge behavior before transfer.
3. Put profile declarations and verbatim terms under `/usr/share/sparky-install-models/` and installer-owned models under `/var/lib/APPLICATION/models/`.
   The shared `model-postinst` presents the terms and a default-No debconf consent question when required.
   No package, image, test preseed or application preference may accept the model publisher’s terms for a person.
   Stop a rig proof at that question unless the brief explicitly authorizes the particular download without a separate acceptance act.
4. Stage all transfers, check length and SHA-256, then install atomically.
   Refuse insecure redirects, path traversal, symbolic-link parents and writable or non-root-owned destination parents.
   Record exact owned paths before starting postprocessing, including partial converter outputs.
   Hash locally generated models separately and verify those hashes in the application.
   Do not label a transformed model’s hash as the publisher’s original hash.
5. Removal retains downloaded data; purge removes only installer-owned, unshared paths.
   A pre-existing file with matching content can be used but must not become installer-owned.
   A differing unowned file causes an explicit failure rather than replacement.
   Keep shared-file references across profiles and preserve unrelated files belonging to the person.
6. Application code verifies the installed profile instead of downloading at first use.
   A missing or corrupt profile reports its package and opens that package’s installation page.
   Register and test the actual desktop URI handler; an internal HTML link handler alone cannot serve another application.
   Derived models need a generated-file-to-profile mapping as well as the original input mapping.
7. Test the real package transaction in a fresh container.
   Prove the shared size notice with a fake NetworkManager service on the real private system bus, keeping apt and metadata unchanged.
   Prove required consent remains No and causes no model request.
   Fetch only the smallest model the brief authorizes, check its hash, remove, reinstall and purge, and retain a personal-file preservation control.
   Use locally generated fixture bytes over TLS for hash failure, interrupted conversion, ownership and retry tests.
   Package bodies and source archives must contain no publisher model weights.

## Traps

- **Symptom:** debconf rejects a maintainer-script notice as an unsupported command, or a translated graphical question loses its large licence note.
  **Cause:** notices printed before confmodule initialization are replayed as protocol commands after debconf re-executes the script; dynamically substituting a large multiline terms body also proved unreliable in the translated frontend.
  **Fix:** initialize confmodule before any human output, print notices to stderr and generate immutable per-profile note/consent templates from the pinned legal texts.
  Source the shared maintainer script from each profile wrapper so debconf loads that real package’s templates and purge clears the same package’s records.
  Keep every consent question default No and show the original terms with the ten translated questions.
  **How found:** a real-debconf re-execution regression failed before the ordering fix and passed after it; English and Portuguese private-session screenshots distinguish the dynamic-note failure from the working static templates.
  The KDE CAPB diagnostic was incidental and needed no library patch.
- **Symptom:** choosing an application feature opens nothing although its AppCenter link works inside AppCenter.
  **Cause:** the `aptus://` scheme had only an HTML-view callback, without a desktop MIME registration.
  **Fix:** register a hidden scheme-handler desktop entry, strictly validate the package URI and reuse the existing administrator authorization and package-detail page.
  **How found:** desktop handler inspection and URI dispatch tests distinguished an external `xdg-open` from the internal callback.
- **Symptom:** purging a profile deletes a model file that existed before installation.
  **Cause:** content verification was incorrectly treated as ownership acquisition.
  **Fix:** preserve matching unowned files and refuse differing ones before any transfer; receipts include only paths actually created by the installer.
  **How found:** independent matching-file and differing-file fixture controls, followed by purge.
- **Symptom:** a locally converted Marigold model is always reported missing or silently bypasses integrity checks.
  **Cause:** the declaration listed only publisher inputs, while the application looked for a derived output name.
  **Fix:** map both derived outputs and original inputs to the functional profile, track converter partials and verify a separately generated checksum sidecar.
  **How found:** comparing `GeometryRunner`’s expected filenames with the installer declarations and converter output paths.
- **Symptom:** the first native package reaches its last step and has no link/start archive configuration or host build identity.
  **Cause:** running the inner source builder directly omitted the host provenance wrapper and public archive gate inputs.
  **Fix:** initialize `build-provenance.sh` on the host, pass its Docker arguments, require the signed archive configuration and run `lean.release check-debs` after ordinary `.buildinfo` and `.changes` exist.
  **How found:** comparison with the native packaging recipe and the gate’s required environment; the partial compilation is not a qualified binary package.
- **Symptom:** a failed native profile install returns to a package page without its reason.
  **Cause:** that detail renderer did not read the existing saved-problems entry.
  **Fix:** use the same problem text helper as the other AppCenter pages.
  **How found:** a saved-error fixture reaches the native profile page and must retain the failure text before its install action.
- **Symptom:** an installed NVIDIA entry exits before opening its window, although the same launcher starts on AMD.
  **Cause:** an uppercase-only environment-name validator rejects Graphics’ valid `__VK_LAYER_NV_optimus` key.
  **Fix:** accept valid environment identifiers, including lowercase letters, from the trusted Graphics helper while preserving its same stable GPU identity.
  Continue to reject malformed names and remove inherited device-selection overrides.
  **How found:** the installed menu launch reports the exact key; a three-control launcher regression is red before the fix and green after it.
- **Symptom:** the model-installation page opens a status-read error only when reached through polkit; the same problems command succeeds directly.
  **Cause:** the published problems engine rejects an inherited `PKEXEC_UID`, treating the fixed-purpose package caller as a direct privileged engine invocation.
  **Fix:** use the same authorized caller environment as AppCenter’s existing entry actions, clearing the inherited marker for the fixed read-only query.
  Reuse that reader for the detail page and the post-install failure path.
  **How found:** the deployed 0.2.1 engine is red with the inherited marker and green through the corrected caller; the owning engine’s later source already records its own general fix.
- **Symptom:** an incremental native package rebuild refuses an already marked staging tree.
  **Cause:** ordinary preparation cleared the runtime staging directories but retained a previously processed automatic dbgsym root under `debian/.debhelper`.
  **Fix:** recreate generated staging before the normal archive step; reuse compiler products only after comparing their consumed source bytes with the newly extracted authored source.
  Keep the binary output directory empty before a helper that identifies new archives by their filenames, and use a new frozen gate workspace when candidate hashes change.
  **How found:** the second archive attempt failed before its first debug package; fresh generated staging removes the stale marker without bypassing projection or release checks.

The installed Spirula profile proof used only ALIKED n16rot, a 2,997,054-byte owner download under BSD-3-Clause, without an account or separate consent act.
It extracted features from two generated pictures on each Graphics-selected PCI device, failed visibly before profile installation and on an invalid PCI identity, retained data on removal, and removed only owned data on purge.
A separate application-purge test verified receipt-based cleanup after the profile declarations had already been removed.
The actual apt-driven SAM3 questions in English and Brazilian Portuguese stopped at default No, with no owner model body transferred.
The model owner’s legal text remains unmodified; the question, metered warning and purge notice have ten translations.

## A long-running lane joins newer mains

- **Symptom:** a proposed AppCenter successor is older than master, conflicts in shared dispatch/language files, and would replace entries added while the lane was building.
  **Cause:** its version and source pointer were chosen from an earlier base; a coincidentally equal package version does not mean equal functionality.
  **Fix:** join the current mains before acceptance, preserve both catalogues and every language key/value, inspect every staged gitlink, and state the merged source pointer in the successor changelog.
  When existing build records name earlier commits, merge rather than rebase so those records remain reachable.
  Compare the actual successor payload against the current staged predecessor, explain every differing file and refuse unexplained removals.
  **How found:** the Spirula review compared the lane’s 0.1.13 branch with AppCenter 0.1.16, finding four newer entries and six newer application commits; both merges and a two-sided dictionary/catalogue audit preserved them in 0.1.17.
- **Symptom:** a missing model opens no profile page even though apt says the application’s dependency is satisfied.
  **Cause:** its minimum AppCenter version names a number used by another branch before the profile route existed.
  **Fix:** depend on the first integrated version that actually supplies the route, here 0.1.17, and prove apt rejects the predecessor when it is the only candidate.
  Keep entry-specific URI and consent-renderer tools on the application entry, so AppCenter’s own dependency fields stay equal to its predecessor.
  **How found:** the actual store/dependency test and 0.1.16 payload comparison exposed the version collision and two added AppCenter helper dependencies; moving those helpers to Spirula preserved the agreed entry-owned policy.
