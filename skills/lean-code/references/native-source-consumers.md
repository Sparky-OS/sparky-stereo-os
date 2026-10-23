# Native source consumers: migration findings, 20 October 2026

Part of the [`lean-code`](../SKILL.md) skill.

The 0.1.9 migration candidate conservatively leaves C/C++ files with structured documentation or translator annotations unchanged.
Keeping only the comment is insufficient: an inserted `#line` between the comment and its declaration can confuse a textual generator.
CMake and Meson configuration templates also remain inputs to their generators, even when their filenames end in `.h`.

For additional known consumers, `lean.debian_prepare --preserve-source PATTERN REASON` retains a reviewed `debian/sparky-lean-preserve.json` in the source package.
Patterns are relative to the source root, and the native report records each retained file and its reason.
A pattern matching no eligible source or a changed plan fails the build.
This handles XScreenSaver's resource checker, which parses C text; SDL's manual generator separately needs the original header documentation.
Run the real generators and tests; do not suppress validation or remove manuals to pass a build.
These are migration safeguards, not a claim that all repository packages have completed migration.

The 0.1.12 migration candidate also carries these upgrade and packaging safeguards:

- GLSL is preserved until a shader-specific checker is qualified. A C preprocessor cannot qualify GLSL directives. On upgrade, `dpkg-stereo --repair-consumers` restores earlier local shader projections from exact original bytes, preserves user changes and retries if an original is unavailable. Verify that recovery before declaring an existing installation migrated.
- Generated Debian control files must agree with their templates. Keep Wine's `check-control` guard and QEMU's control generator enabled; carry dependency changes into the retained template. Locate the actual `Source` stanza: a leading licence-comment paragraph is not package metadata. Preserve comment lines inside `Build-Depends` without splitting its relations. Debian's own control and dependency parsers are the check.
- Assembly-bearing kernel headers and inactive architecture-specific headers need their own consumer qualification. Preserve explicitly identified inputs instead of accepting a C-only check for them.

The 0.1.14 migration candidate adds explicit recovery layouts for installed source copies and checks the original shell grammar before transformation. Use [the source-copy recipe](../../../docs/lean-code-packages.md#installed-source-copies) when different originals produce identical projected bytes. Preserve an input that its declared interpreter cannot parse; do not silently select another interpreter or call it optimized.

Blender's `discover_nodes.py` reads namespace-closing comments in node `.cc` files to generate registration symbols. Those comments are machine input. Preserve these files in the source-consumer plan and rebuild the generated registrations if that plan changes. Preservation patterns must follow the source walker's exclusions; a `build/*` pattern cannot match a directory already excluded from projection.

Linux's SMB mapping generators read trailing error mappings and class-section comments in `fs/smb/client/nterr.h`, `fs/smb/client/smberr.h` and `fs/smb/common/smb2status.h`. Preserve all three headers. Before compilation, run the actual Perl generators and compare all four generated tables with a retained authored-input baseline, requiring nonempty mappings: `gen_smb2_mapping` can return success with an empty table after its annotations are removed. On a repair, invalidate generated tables and dependent objects; a C-token check or a zero generator exit code alone does not qualify these inputs.

Linux also stores cryptographic OID values in `include/linux/oid_registry.h` comments and CPU/VMX feature names in quoted comments in `arch/x86/include/asm/{cpufeatures,vmxfeatures}.h`. Preserve those headers and compare the real `lib/build_OID_registry` and `arch/x86/kernel/cpu/mkcapflags.sh` outputs with their authored baselines. Require the expected registry entries, not just successful generator exits. An empty OID table can compile and boot yet reject signed modules; disappearing CPU feature names can change what userspace detects. Final boot/module tests remain necessary after these build-input checks.

For compiler-input size claims, intersect the projection report with actual build dependency records and verify the final file hashes. A whole source-tree total also includes files that this configuration never compiled or that configure regenerated afterward. Retain versioned registry inputs for such generators, as with Wine's Vulkan bindings. Report unique input bytes separately from repeated parsing, filesystem reads and elapsed time.

The 0.1.15 candidate preserves installed `/usr/include/wine/*` headers: WIDL and WRC also preprocess them, and their parser rejects filename-less `#line` directives accepted by GCC. Preserve the shared native headers too, through the source-consumer plan. A successful C check does not qualify these other preprocessors. Similarly, UniFFI's `BridgingHeaderTemplate.h` contains binding-generator syntax; its extension does not make it a C input. Preserve generator templates until their own consumer is qualified.

For vendored Cargo inputs, retain the original crate identities and checksum manifests in source. A disposable build may update only checksum entries whose original and final hashes match its qualified native projection report; an unrelated edit must fail, and cleanup must restore the exact original manifests. Pin external compilers to specific archives and verify the complete file/mode/link inventory before building. On an interrupted packaging retry, recreate both ordinary and debug-symbol staging trees from the compiled outputs; do not remove an existing lc marker merely to project that staging tree again.

If vendor checksums already disagree with the accepted source, establish that baseline separately: verify each discrepancy against the pinned source commit, retain the original manifest and record the exact accepted hashes or absent paths. Any build-time reconciliation must reject other edits and restore the original metadata on clean. This repairs provenance metadata; it is not a Lean Code transformation or saving.

Check the actual language of shared headers, not only their extension. Mesa's shader includes and BVH headers can feed both C and GLSL; preserve them until both consumers are qualified. Inactive architecture branches can also contain target pragmas that the host compiler rejects during a preprocessing check. Preserve those reviewed inputs with an explicit reason, or use the appropriate target checker; never remove the pragma to make a check pass.
