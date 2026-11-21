# Vibe presets and captions

Check freshness first: source and published-package audit, 21 November 2026.
This reference records the integration contract and measured startup, installed-package initialization and caption behavior.
The optional role was installed and removed on the published desktop dependency set; graphical caption and dictation controls ran in private Plasma Wayland sessions.

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
The Linux v3.3.5 binary reads the store from `$XDG_DATA_HOME/github.com.thewh1teagle.vibe/app_config.json`, defaulting to `~/.local/share`.
An isolated first-start run proved that a file in the XDG config directory is ignored: its bytes stayed unchanged while the app created a different store under XDG data.
Do not infer the store path from `config_watcher.rs`, which watches the application config directory even though the store plugin loads from data.

| Preset value | Persisted key and handling |
|---|---|
| Default model | Recommend `ggml-large-v3-turbo.bin` in text; omit `model.path` because first start clears an absent model. |
| Light model | Recommend `ggml-medium-q8_0.bin` in the AppCenter and role description; omit the ineffective `model.path`. |
| Basic model | Same speech model as Light; keep ffmpeg, disable AI tasks. |
| GPU | `model.gpuDevice`: null in portable preset data; first-run selection must respect the shared graphics policy and the person's choice. A machine-specific ordinal is not portable. |
| Audio processing | `transcription.ffmpegOptions`: preserve loudness normalization and the other approved values. |
| Automatic export | `transcription.autoExport`: beside the source, SRT/JSON/Markdown, replacement disabled. |
| Transcript storage | `transcription.saveTranscripts`: false. |
| Timing and meetings | `transcription.stableTimestamps`, `recording.meetingDetectionEnabled`: false. |
| Appearance | `general.theme`: dark; `general.closeToTray`: true. |
| Analytics | `analytics_enabled`: false in every preset. |
| Update channel | `general.updateChannel`: `stable`, the upstream default; controls stable versus beta updater releases. |
| Transcript line layout | `transcript.lines`: `original`, the upstream default; retains engine segmentation rather than regrouping into sentences or paragraphs. |
| Transcript export | `transcript.exportOptions`: PDF settings with speakers and timestamps shown, light appearance. |
| AI | `ai.connection`, `ai.tasks`: never seed credentials or a private cloud-model selection; tasks remain disabled. Shared-engine configuration belongs to its own integration. |
| First run | `general.firstRun=false` survives, but cannot suppress upstream setup when no model is installed. Preserve the unmodified optional application's first start. |

Read the precise object shapes from the approved input and the matching release's consumers before generating presets.
Download no model in package installation or initialization. The optional application retains its own setup behavior; the pack must not claim that its preset selects the model or adds download consent.
Missing-model behavior was measured in an offline 1920-wide Xvfb rig using the signed v3.3.5 binary.
With Default, Light and Basic seeded in the actual data store, `general.firstRun=false` still reaches setup when no model exists: the first screen says “No Connection”, offers “Try Again” and “I prefer to download manually”, and shows no model size.
The app changes `model.path` to null in every case.
A separate control with `general.skippedSetup=true` opens the main view and offers “Download model”, again without a size.
That control proves a way to avoid automatic setup, not a complete consent-compatible integration.
The source explains the result: `pages/main/session.tsx` clears a missing model and navigates to setup unless skipped; setup's effect calls `downloadIfOnline()` on mount.
Without an explicit route URL, setup takes `config.modelUrls.default` (large-v3-turbo), not the cleared preset model.
No online run or model download was performed; automatic downloading when online is a source finding, not an observed transfer.
Do not ship the skip control. Keep upstream first start unchanged, and name the Light/Basic recommendation in the optional installation descriptions.
After removing model.path, isolated starts preserved all 15 Default and Light keys and all 14 Basic keys byte-for-value; this includes analytics off, AI tasks off, the two new default-valued keys and FFmpeg normalization. These offline tests do not claim an online download was observed.

## Seed once without replacing the person's file

The seeder implements exclusive publication of complete JSON. Both concurrency tests and installed-package arrival tests pass.

Compute the destination from the recipient's actual store directory, verified against the shipped binary; v3.3.5 uses XDG data.
An existing file, directory or symlink at that path must be left alone.
Write a complete temporary file beside the destination and commit it with an exclusive operation, such as `renameat2(RENAME_NOREPLACE)` or linking that newly created temporary file into the destination name.
A check followed by ordinary rename can replace a file created by the app in between.
Never hard-link a package stage or shared preset into a user's configuration.
After a successful exclusive commit, remove the temporary name and make the file writable by that user.
Prove competing seeds, app creation during seeding, failed writes, custom XDG paths, an existing symlink and unchanged contents on every subsequent start.

Runner 0.1.4 declares `program`, `worker` and `menus`; its presence check runs at actions and menu sync, not through a declarative initializer callback.
The candidate 0.1.5 runner adds `initialize=/absolute/executable`, emitted from pack.json by make-pack.py.
It runs an idempotent, noninteractive, offline callback only when the program exists, serialized by a per-user, per-pack lock.
One shared user path unit watches atomic dpkg status replacements and integrations.d changes; login sync and explicit actions call the same initializer.
A real systemd user manager in an isolated container proved both arrival orders, callback UID 1000, existing bytes, removed declarations and a burst of fifteen package events.
Disable the service start limit and path trigger limit for this event source; otherwise many package changes can leave initialization disabled.
Do not backport the declaration alone to 0.1.4 and claim it provides this behavior.
A login unit with only `ConditionPathExists=/usr/bin/vibe` does not by itself prove late installation works in an already-running user session.
Installed-package tests proved pack-first, program-first, late installation, byte-identical existing data and purge while the user manager was already running. Package purge removes its declaration and menu, and preserves personal data.
The seed must run without network access and must never wait for a model download.

## One GPU inventory

The hardware package's command is a root hardware installer, not an unprivileged RAM/GPU facts API.
No RAM-size interface was found in its inspected command.
Do not call it from the seed to probe the station or introduce a second GPU detector.

`sparky-stereo-graphics` owns the GPU inventory and policy.
Its `sparky-stereo-gpu-env --list --json` implementation exposes stable IDs, kind, driver, render node, main GPU and measured-best flags; `--app` resolves the program's saved policy.
Vibe's `vibe-server devices` returns ggml device indices, names and descriptions.
A shared graphics ID is not a ggml index, and a renderable DRM device is not proof that Vibe can use Vulkan on it.
Prove the bridge with each actual card and an explicit saved per-app choice. A unique exact name or description match maps to its ggml index; duplicated names or no exact match leave the index null.
Measured PCI marketing names differed from Vulkan descriptions on both AMD and NVIDIA, so both mappings were null. Single-card isolated transcription passed on both; that is not proof of a certain ordinal mapping on a dual-GPU system. Do not invent substring matching or a second inventory.

## Command-line output and captions

Source inspection of v3.2.2 `server/crates/vibe-server/src/cli.rs` shows `transcribe` printing plain text.
With `--word-timestamps`, it prints one `[start --> end] text` line per word, using VTT-style decimal timestamps; those lines are neither an SRT file nor a complete WebVTT document.
The v3.3.5 CLI retains that shape.

In v3.2.2 `server/transcription.rs`, the HTTP transcription handler accepts `response_format` values `verbose_json`, `text`, `srt` and `vtt`; its default returns JSON.
`server/format.rs` generates numbered SRT blocks with comma milliseconds from engine centiseconds.
The candidate uses `--word-timestamps --max-segment-len 80`, validates each timed line and converts it into a numbered SRT block with comma milliseconds.
Do not invent a CLI `--output-srt` option.
Tests cover spaces in filenames, existing captions, a racing caption writer, failed engines and rejection of untimed output. Actual installed action runs on AMD and NVIDIA produced the same three timed sentences from generated speech, and the movie hash remained unchanged. The real Dolphin context action also produced the sibling SRT.

The Dolphin action belongs to the shared integration runner: missing Vibe offers installation, while missing models and unreadable files must say what failed and how to proceed.
Write captions as a separate sibling file, without modifying the source media or replacing existing captions without consent.
Read back the SRT independently, then prove the action through KIO and both players.
A caption is identical 2D content in both eyes at the compositor's depth; compare after accounting for its horizontal disparity, and add no depth control in this package.

## Traps and how they were found

| Symptom | Cause | Fix or next proof | Evidence |
|---|---|---|---|
| Seeded theme and model settings are ignored. | The loader reads XDG data, while the seed was written to XDG config. | Seed the binary's actual store path, leaving existing files alone. | v3.3.5 first-start runs: wrong-path file byte-identical, separate data store created; corrected-path theme applied. |
| A dependency repair is proposed for an already-correct package. | An upstream archive was confused with the edition archive. | Inspect the signed repository's exact binary control first; no libgomp1 successor is needed for 3.2.2-1+lc1. | `dpkg-deb -f`, verified offline. |
| The generated map exists but Vibe still installs alone. | The published inherited AppCenter installer has no map reader. | Implement and exercise the existing main entry's companion-package path. The fork override and inherited direct-entry path both install the program and its pack. | Archive extraction, search of installed scripts, inspection of `also` handling. |
| A first-run seed replaces a person's new settings. | Existence check and ordinary rename are not one exclusive operation. | Exclusive publication using a fresh complete temporary JSON and link; never a hard link to a package file. | Twenty concurrent seeds produce one store, and a competing writer remains byte-identical. |
| Captions saved with an .srt suffix cannot be read as SRT. | CLI output was mistaken for its HTTP formatter. | Test a proper formatter or the API's SRT response. | Both release CLI sources and the v3.2.2 HTTP formatter dispatch. |
| GPU number 1 selects a different card after enumeration changes. | A personal engine ordinal was treated as hardware identity. | Use the shared resolver, then accept only a certain engine mapping; measured unmatched names remain null. | Graphics JSON schema and Vibe's device enumeration source. |

Primary sources: [Vibe v3.3.5](https://github.com/thewh1teagle/vibe/releases/tag/v3.3.5), [persisted keys](https://github.com/thewh1teagle/vibe/blob/v3.3.5/desktop/src/lib/config-keys.ts), [store loader](https://github.com/thewh1teagle/vibe/blob/v3.3.5/desktop/src/lib/config-store.ts), [CLI v3.2.2](https://github.com/thewh1teagle/vibe/blob/v3.2.2/server/crates/vibe-server/src/cli.rs), [HTTP transcription](https://github.com/thewh1teagle/vibe/blob/v3.2.2/server/crates/vibe-server/src/server/transcription.rs).

## Settings ownership

Templates are package data; the one live model and transcription store is Vibe's data-home app_config.json.
The seed never maintains a second profile selection file.
Read MemTotal directly from /proc/meminfo; use the approved Default threshold of 8 GiB or an engine-usable GPU, otherwise Light.
Basic remains an explicit template with the Light speech model, ffmpeg retained and AI tasks disabled.
GPU policy belongs to Graphics; the initial model.gpuDevice is only a mapping to Vibe's enumeration.
The captions action resolves Graphics' --app vibe.desktop policy on every invocation, so later Graphics choices apply without rewriting the person's native store.
Match one exact name/description only; an ambiguous match leaves the index null.
AI connection integration belongs to the Partners page; the pack introduces neither a separate provider store nor a provider-selection UI.

## Optional role task

Add a role through lists/make-meta.py and its role list, following the creator task.
The partner enhanced accessibility features task recommends Vibe and its data pack, with the standard sparky-stereo-desktop dependency.
Keep it in OPT_IN so the full image meta does not recommend it; do not remove Vibe from creator.
Future engine/page names live in the role's pending list and enter its recommendations only after the edition index publishes them.
The generator's ordinary apt lookup is insufficient for this future-package condition.
The generated catalogue is a separate package; declaring integrations.tsv does not change an already-built catalogue.

## Runtime traps

- **The desktop dependency cannot be installed.** A rig with Debian, deb-multimedia and the edition can still omit SparkyLinux's own AppCenter. Add authenticated core and tiamat indexes and their verified public key, matching the image's apt setup. The resolver names the missing sparky-aptus-appcenter dependency; do not replace it with a dummy package.
- **A selected installed model still leads to setup.** The frontend enumerates the native models folder before checking model.path. For an independently downloaded rig model, place it in that folder or set the native models_folder value to its directory. A file elsewhere being readable is enough for the CLI but not for the GUI's installed-model list. This was found by comparing session.tsx with get_models_folder in cmd/app.rs, then opening the signed binary.
- **A fake-input pointer click does nothing.** Its virtual pointer disappears when the short-lived client exits. Use one persistent input client, or navigate the selected file's context menu with keyboard events and confirm the highlighted action before Enter. Read back the resulting SRT and hash the media; a menu screenshot alone does not prove the action ran.

## Installed role and graphical evidence

A role uses the creator task's dependency convention: Depends on the desktop, Recommends for its programs.
Installing with recommendations can also bring a recommended program's existing runtime recommendations.
In the minimal desktop rig, the new task brought Vibe, its pack, xdg-desktop-portal, fuse3 and the two json-glib packages, with no removals.
Purging a task alone leaves the programs; explicitly purging the test additions restored the baseline package set.
The generated catalogue Breaks older integrations metas, so ship the matching integrations meta with it.
A catalogue-only upgrade removed the desktop meta in the negative test; the matching pair retained it and left Vibe and the optional task absent.
The inert data pack enters the shared integrations meta by the existing data-pack rule, without putting Vibe on the image.

Compare subtitle content with an independently captured no-subtitle control, not just whole eye buffers or a tolerance threshold.
The published VLC renderer had an exactly equal complete caption band with visible text and a scene box at +40 pixels disparity.
Haruna's complete band failed equality by one RGB code, including background dithering.
On a black-background marked clip, a separate no-subtitle capture established R=B=0 and G=0 or 1 in that band.
All 25,548 visible subtitle-ink pixels (R or B nonzero in either eye) then compared exactly in RGB, while the scene box retained its disparity.
Keep the full-band failure alongside this narrower content proof; neither a white-only glyph comparison nor a numerical tolerance proves all caption content identical.

For dictation, start a real private Plasma session, give it a synthetic PipeWire microphone, select the independently downloaded model through Vibe's native store and enable its own shortcut in that test account only.
Prove each target accepts an ordinary key and that the microphone received speech before testing the shortcut.
The signed 3.3.5 application inserted no speech into Kate, Konsole or a Qt Quick TextArea in the tested Plasma Wayland session; Konsole echoed two NUL shortcut characters, and the other fields remained empty.
This is a measured negative result, not a diagnosed cause or a claim that speech transcription fails: the same model and clip worked through the installed captions action.
Do not enable dictation in the shipped presets based on a failed insertion test.

The future Partners-page adapter reads sparky-stereo-partnersrc through KConfig: program-specific Program/vibe/text choices override Default/text, and Interface/<id> supplies Kind and Url.
An empty Model means none was selected; never invent a model or credential.
The adapter's destination is Vibe's native ai.connection object, and enabling tasks remains the person's choice.
The presets do not implement that adapter or maintain another connection store.
