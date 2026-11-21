# Vibe presets and captions

Check freshness first: source and published-package audit, 21 November 2026.
This reference records the integration contract and inspected interfaces; the preset package, seeding service and captions action are not yet implemented or runtime-qualified by this audit.

## Reconcile before building

1. Inspect the published edition archive with `dpkg-deb -f FILE Package Version Depends` and `dpkg-deb -c FILE`.
   Vibe 3.2.2-1+lc1 declares `libgomp1 (>= 6)` and `ffmpeg`; the upstream archive's dependency omission is not an edition defect.
2. Compare upstream's `desktop/src/lib/config-keys.ts` at the published version and latest release, and inspect the actual store loader.
   Between v3.2.2 and v3.3.5, the declared keys grow from 55 to 57: `general.updateChannel` and `transcript.lines` are added, none removed.
   This key comparison alone does not prove unchanged value semantics.
3. Read [issue 1646](https://github.com/thewh1teagle/vibe/issues/1646) and the store code.
   The issue was open without replies; `config-store.ts` still loads a per-user store with empty defaults, and Rust setup uses the application's config directory.
   No system-wide default lookup was found in these loading paths.
4. Inspect `lists/integrations.tsv`, `lists/make-meta.py`, the installed catalogue and the installed AppCenter action.
   Declare a data pack as `vibe`, `sparky-stereo-vibe`, `data`, and its description in the four tab-separated columns.
   A data pack Enhances Vibe; it does not depend on Vibe.
   The generator excludes packs absent from the repository index, so merely adding the row cannot put an unpublished pack into the meta package.
5. Check both AppCenter paths.
   In 0.1.12+lc1, Vibe is an inherited main-page entry whose package variable is only `vibe`.
   The edition's `stereo/main-entries.json` supports main-page overrides, while `stereo/catalogue.json` holds edition entries.
   Apt rows use `kind: apt`, `package` and optional `also`; `stereo/actions/entry` passes `also` to apt.
   The map is owned by `sparky-stereo-integration-catalogue`, but the inherited installer does not consume it in that published version.
   An integration must prove the existing Vibe entry installs both packages, rather than create a duplicate entry and leave the original incomplete.

The package checks above ran in an offline container against downloaded archives whose hashes matched the signed repository indexes.
These checks execute neither maintainer scripts nor Vibe.

## Presets and persisted keys

The package contract has three JSON presets in `/usr/share/sparky-stereo/vibe/presets/`.
Vibe stores dotted keys literally at the top level of `app_config.json`; do not turn `model.path` into a nested `model` object.
The `ai` value itself is an object.
On Linux the user file is under `$XDG_CONFIG_HOME/github.com.thewh1teagle.vibe/`, defaulting to `~/.config`.

| Preset value | Persisted key and handling |
|---|---|
| Default model | `model.path`: resolve `ggml-large-v3-turbo.bin` inside this user's model directory; never copy another account's absolute path. |
| Light model | `model.path`: `ggml-medium-q8_0.bin`; no smaller-model substitution. |
| Basic model | Same speech model as Light; keep ffmpeg, disable AI tasks. |
| GPU | `model.gpuDevice`: null in portable preset data; first-run selection must respect the shared graphics policy and the person's choice. A machine-specific ordinal is not portable. |
| Audio processing | `transcription.ffmpegOptions`: preserve loudness normalization and the other approved values. |
| Automatic export | `transcription.autoExport`: beside the source, SRT/JSON/Markdown, replacement disabled. |
| Transcript storage | `transcription.saveTranscripts`: false. |
| Timing and meetings | `transcription.stableTimestamps`, `recording.meetingDetectionEnabled`: false. |
| Appearance | `general.theme`: dark; `general.closeToTray`: true. |
| Analytics | `analytics_enabled`: false in every preset. |
| Transcript export | `transcript.exportOptions`: PDF settings with speakers and timestamps shown, light appearance. |
| AI | `ai.connection`, `ai.tasks`: never seed credentials or a private cloud-model selection; tasks remain disabled. Shared-engine configuration belongs to its own integration. |
| First run | `general.firstRun`: coordinate the app's setup and missing-model UI with the no-prompt seed and explicit model-download click. Do not claim that a JSON value alone proves this flow. |

Read the precise object shapes from the approved input and the matching release's consumers before generating presets.
Download no model in package installation or the seed unit; show the model's size before the person's download click.
Missing-model behavior with a seeded configuration remains a required runtime test.

## Seed once without replacing the person's file

The following is an untested implementation pattern, not a shipped service recipe.

Compute the destination from the recipient's XDG config directory.
An existing file, directory or symlink at that path must be left alone.
Write a complete temporary file beside the destination and commit it with an exclusive operation, such as `renameat2(RENAME_NOREPLACE)` or linking that newly created temporary file into the destination name.
A check followed by ordinary rename can replace a file created by the app in between.
Never hard-link a package stage or shared preset into a user's configuration.
After a successful exclusive commit, remove the temporary name and make the file writable by that user.
Prove competing seeds, app creation during seeding, failed writes, custom XDG paths, an existing symlink and unchanged contents on every subsequent start.

A login unit with only `ConditionPathExists=/usr/bin/vibe` does not by itself prove late installation works in an already-running user session.
Exercise pack-first, program-first, late installation and purge; define how the unit is activated before Vibe first creates its store.
The seed must run without network access and must never wait for a model download.

## One GPU inventory

The hardware package's command is a root hardware installer, not an unprivileged RAM/GPU facts API.
No RAM-size interface was found in its inspected command.
Do not call it from the seed to probe the station or introduce a second GPU detector.

`sparky-stereo-graphics` owns the GPU inventory and policy.
Its `sparky-gpu-env --list --json` implementation exposes stable IDs, kind, driver, render node, main GPU and measured-best flags; `--app` resolves the program's saved policy.
Vibe's `vibe-server devices` returns ggml device indices, names and descriptions.
A shared graphics ID is not a ggml index, and a renderable DRM device is not proof that Vibe can use Vulkan on it.
The bridge between the shared policy and the engine's enumeration still needs a runtime proof, including an explicit user selection and a dual-GPU default.
Do not silently substitute another device when the selected one cannot run.

## Command-line output and captions

Source inspection of v3.2.2 `server/crates/vibe-server/src/cli.rs` shows `transcribe` printing plain text.
With `--word-timestamps`, it prints one `[start --> end] text` line per word, using VTT-style decimal timestamps; those lines are neither an SRT file nor a complete WebVTT document.
The v3.3.5 CLI retains that shape.

In v3.2.2 `server/transcription.rs`, the HTTP transcription handler accepts `response_format` values `verbose_json`, `text`, `srt` and `vtt`; its default returns JSON.
`server/format.rs` generates numbered SRT blocks with comma milliseconds from engine centiseconds.
Choose and test either a correct CLI-to-SRT formatter or this HTTP route; do not invent a CLI `--output-srt` option.
These interface facts are from source, not a transcription run in this audit.

The Dolphin action belongs to the shared integration runner: missing Vibe offers installation, while missing models and unreadable files must say what failed and how to proceed.
Write captions as a separate sibling file, without modifying the source media or replacing existing captions without consent.
Read back the SRT independently, then prove the action through KIO and both players.
A caption is identical 2D content in both eyes at the compositor's depth; compare after accounting for its horizontal disparity, and add no depth control in this package.

## Traps and how they were found

| Symptom | Cause | Fix or next proof | Evidence |
|---|---|---|---|
| A dependency repair is proposed for an already-correct package. | An upstream archive was confused with the edition archive. | Inspect the signed repository's exact binary control first; no libgomp1 successor is needed for 3.2.2-1+lc1. | `dpkg-deb -f`, verified offline. |
| The generated map exists but Vibe still installs alone. | The published inherited AppCenter installer has no map reader. | Implement and exercise the existing main entry's companion-package path. This repair is not yet implemented here. | Archive extraction, search of installed scripts, inspection of `also` handling. |
| A first-run seed replaces a person's new settings. | Existence check and ordinary rename are not one exclusive operation. | Untested pattern: exclusive destination creation; confirm with a concurrent app writer. | Filesystem operation semantics; no race test yet. |
| Captions saved with an .srt suffix cannot be read as SRT. | CLI output was mistaken for its HTTP formatter. | Test a proper formatter or the API's SRT response. | Both release CLI sources and the v3.2.2 HTTP formatter dispatch. |
| GPU number 1 selects a different card after enumeration changes. | A personal engine ordinal was treated as hardware identity. | Use the shared graphics resolver, then validate the engine mapping; runtime proof still owed. | Graphics JSON schema and Vibe's device enumeration source. |

Primary sources: [Vibe v3.3.5](https://github.com/thewh1teagle/vibe/releases/tag/v3.3.5), [persisted keys](https://github.com/thewh1teagle/vibe/blob/v3.3.5/desktop/src/lib/config-keys.ts), [store loader](https://github.com/thewh1teagle/vibe/blob/v3.3.5/desktop/src/lib/config-store.ts), [CLI v3.2.2](https://github.com/thewh1teagle/vibe/blob/v3.2.2/server/crates/vibe-server/src/cli.rs), [HTTP transcription](https://github.com/thewh1teagle/vibe/blob/v3.2.2/server/crates/vibe-server/src/server/transcription.rs).
