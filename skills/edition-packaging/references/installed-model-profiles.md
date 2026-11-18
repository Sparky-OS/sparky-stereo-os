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

- **Symptom:** debconf treats lines of a model licence as commands.
  **Cause:** a multiline terms body was sent through `db_subst` without the escape capability.
  **Fix:** request `db_capb escape`, collect the helper’s successful output first, then pass it through `debconf-escape -e` before substitution.
  **How found:** the real frontend protocol rejected the first unescaped licence line; the corrected protocol presents the unchanged legal body.
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
