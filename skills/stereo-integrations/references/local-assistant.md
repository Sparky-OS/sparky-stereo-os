# The one local assistant engine

**For** whoever wires a program's AI feature to the edition's local engine (KMail and the other KDE programs through ktextaddons, Vibe, Betterbird with ThunderAI): what each part offers today, where its settings live, what "off" means for it, and the traps already met.

**Check freshness first.**
Written on 2026-11-21 from the reconcile milestone of ORDER 70, read against Ollama v0.40.16, Debian testing's llama.cpp 1:0.9.0+dfsg-1 and ggml 0.29.0-1, ktextaddons 2.1.2-8, kdepim-addons 26.08.2, Vibe 3.2.2, ThunderAI 5.2.0 and Betterbird 153.7.0esr-bb13.
The engine package, the switch, the per-program defaults and the stand-in server for proofs are not built yet; their recipes join this page with the milestone that builds them.

## The design it follows

- **One engine, one place.** The model's name and the engine's address are written once, in `/etc/xdg/sparky-stereo/ai-engine.conf`, and every program reads from there; no program gets its own engine or its own copy of the choice.
- **Off until the person turns it on.** Nothing listens, nothing is downloaded and no AI task is enabled before the one switch; a model is pulled only on the person's click, with its size shown first, and held and said on a metered connection.
- **It works, or the person is told.** With the switch off, each program says the assistant is off and where to turn it on; a failed start or pull is told with its cause; another engine is a path the person chooses, never one taken behind their back.
- **Loopback only, no keys in plain files.** The engine binds to 127.0.0.1; keys and accounts belong in KDE Wallet; the local engine needs none.

## Recipe: reading what each part offers

1. **The engine's release.** `gh api repos/ollama/ollama/releases/latest` lists every asset with its size and a `sha256:` digest; `sha256sum.txt` in the same release lists the same digests.
   `gh api repos/ollama/ollama/git/ref/tags/TAG` then `gh api repos/ollama/ollama/commits/SHA --jq .commit.verification` says whether the tag's commit carries a verified signature.
   The bundle's parts are read from the tag's own `Dockerfile` and `scripts/build_linux.sh` (`gh api "repos/ollama/ollama/contents/PATH?ref=TAG"`), so nothing large is downloaded to learn them.
2. **Debian's side.** In a testing container with `deb-src` added: `apt-cache policy`, `apt-cache showsrc` and `apt-cache rdepends` for `ollama`, `llama.cpp`, `ggml`, `ktextaddons` and `libkf6textautogeneratetext1`, then `apt-get download` of the small packages and `dpkg-deb -c` / `-x` to read units and plugins.
3. **The library every KDE program uses.** Clone ktextaddons at Debian's tag (`git clone --depth 1 --branch v2.1.2 https://invent.kde.org/libraries/ktextaddons.git`) and read `textautogeneratetext/core/textautogeneratetextinstancesmanager.cpp` and the plugin's `*settings.cpp` for where settings are read.
4. **A program's plugins.** KDE's GitLab serves a tag's files without a login (`https://invent.kde.org/pim/kdepim-addons/-/raw/v26.08.2/kmail/editorplugins/aitool/kmail_aitooleditorplugin.json`); its code search answers 401 without one.
   Qt 6 embeds a plugin's metadata as CBOR, so `strings` or a JSON parser on the `.so` finds nothing: read the `.json` in the source.
5. **Candidate models, without pulling one.** `curl -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' https://registry.ollama.ai/v2/library/NAME/manifests/TAG` gives every layer's size and digest; the layer of media type `application/vnd.ollama.image.license` is a few kilobytes, fetched from `/v2/library/NAME/blobs/DIGEST` and checked against its digest.
   The languages come from the model's own card (the library page `https://ollama.com/library/NAME` or the publisher's card), never from recall.

## What each part offers (read on 2026-11-21)

| Part | Fact | Where it was read |
|---|---|---|
| Ollama v0.40.16 (MIT, "Copyright (c) Ollama") | Linux amd64 bundle 1,545,767,640 bytes (`bin/ollama` and `lib/ollama`: CPU, CUDA 12, CUDA 13 and Vulkan runners); ROCm 7.2 bundle 1,053,876,146; MLX on CUDA 13 bundle 1,214,961,201 | release assets |
| Ollama's runners | llama.cpp's own `llama-server`, built per back end from llama.cpp `b12177` fetched at build time with Ollama's compatibility patch applied (`llama/compat/`: a 4.9 KB hooks patch and 171 KB of compatibility source) | `llama/server/CMakeLists.txt`, `llama/README.md` |
| Ollama's integrity | no detached signature or attestation for the Linux bundles; `sha256sum.txt` and GitHub's asset digests (same origin); the tag is lightweight on a commit GitHub shows as verified | releases and git API |
| Ollama's settings | `OLLAMA_HOST` (default `127.0.0.1:11434`), `OLLAMA_ORIGINS` (added to a built-in list of localhost, `app://`, `file://`, `tauri://` and `vscode-*` origins), `OLLAMA_MODELS` (default `$HOME/.ollama/models`), `OLLAMA_VULKAN` (on unless set false), `OLLAMA_NO_CLOUD` (or `disable_ollama_cloud` in `~/.ollama/server.json`) | `envconfig/config.go` |
| Ollama's cloud | a model with a remote host sends the prompt to `ollama.com` (the default of `OLLAMA_REMOTES`); with `OLLAMA_NO_CLOUD=1` the server answers 403 instead, and skips its model-recommendation fetch | `server/routes.go`, `server/model_recommendations.go` |
| Ollama's GPU choice | `CUDA_VISIBLE_DEVICES`, `HIP_VISIBLE_DEVICES`, `ROCR_VISIBLE_DEVICES`, `GGML_VK_VISIBLE_DEVICES` | `discover/runner.go` |
| Debian testing | no `ollama` package; `python3-ollama` 0.6.3-1 is the Python client library; `llama.cpp` 1:0.9.0+dfsg-1 is upstream v0.9.0 (build 12110), 67 commits before Ollama's pin; `ggml` 0.29.0-1 with Vulkan, HIP and BLAS back ends and no CUDA | container, `apt-cache`, GitHub compare |
| Debian's `llama-server.service` | a system unit (`llama.cpp-services`), `WantedBy=multi-user.target`, user `_llama-server`, settings in `/etc/default/llama-server` | the package's files |
| deb-multimedia | no Ollama, llama.cpp or Betterbird (testing and unstable indexes) | `Packages.xz` |
| ktextaddons 2.1.2 | every program's engines are "instances" in one shared file, `autogeneratetextinstances` (`KSharedConfig::openConfig(name)`, so `/etc/xdg/autogeneratetextinstances` cascades as a system default): `[General] currentInstance`, then `[Instance #N]` with `enabled` (default false), `pluginName`, `pluginIdentifier`, `uuid`, `Name`, `CurrentModel`, `ServerUrl` (default `http://127.0.0.1:11434`), `VulkanSupport`, the `*VisibleDevice` keys and `Expose` | `core/textautogeneratetextinstancesmanager.cpp`, `plugins/ollama/ollamasettings.cpp` |
| ktextaddons' global file | `autogeneratetextrc` holds only text-to-speech and font settings | `textautogeneratetextglobalconfig.kcfg` |
| KMail (kdepim-addons 26.08.2) | three editor plugins use the library: "AI Chat", "Ask IA", "AutoGenerate Quick Answer", each `EnabledByDefault: false`; KMail Recommends kdepim-addons; Debian's other users are the Sieve editor (`pim-sieve-editor`, `libkpim6ksieveui6`) | plugin `.json`, `apt-cache` |
| Kate 26.08.2 | no AI plugin, no ktextaddons dependency | the tag's `addons/` |
| Vibe 3.2.2 | `ai.connection.platform` (`ollama`), `ai.connection.model`, `ai.connection.ollamaBaseUrl` (`http://localhost:11434`), `ai.tasks.dictation.enabled`, `ai.tasks.summary.enabled`, `ai.tasks.summary.autoOnFinish`; its own default model on Ollama is `gemma4:e2b` | `desktop/src/lib/ai/config.ts` |
| ThunderAI 5.2.0 (GPL-3.0, Mic) | reads Thunderbird's enterprise policy (`3rdparty` → `Extensions` → the add-on's id, its manifest's `browser_specific_settings.gecko.id`) through `browser.storage.managed`, with locked and unlocked values; keys `connection_type` (`ollama_api`), `ollama_host`, `ollama_model`; its own default `connection_type` is empty | `claude-spec/08-managed-configuration.md`, `options/mzta-options-default.js` |
| Betterbird 153.7.0esr-bb13 | Linux x86_64 tarballs of about 81 MB per language, full builds in de, en-US, es-ES, fr, it, ja, nl, pt-BR and ru; integrity by a same-origin SHA-256 list (`sha256-153.txt`), no signature | its downloads page |

## Traps

- **Symptom:** a person installs "Ollama" from the app center's Chatbot page and no program finds an engine.
  **Cause:** the entry (`aptus://accbot_python3-ollama`, inherited from SparkyLinux's APTus) installs Debian's `python3-ollama`, the client library, not a server.
  **Fix:** the engine is its own package with its own entry; the library entry stays what it is.
  **How found:** the published app center's `accessories-chatbot.html` and its handler, which run `aptus-app python3-ollama`.
- **Symptom:** a plan writes one default per KDE program for the engine.
  **Cause:** an older reading (ktextaddons 2.2.47 on master, October 2026) described the settings as per application; at 2.1.2 the instances live in one shared file.
  **Fix:** one `/etc/xdg/autogeneratetextinstances` reaches every program built on the library; read the version the edition installs before choosing the route.
  **How found:** `instanceConfigFileName()` returns `autogeneratetextinstances` and is opened with KConfig's default cascade.
- **Symptom:** with the engine switched off, KMail offers a "Start Ollama" button that starts an engine anyway.
  **Cause:** when it cannot connect and an `ollama` executable is on `PATH`, the Ollama plugin offers the action, which runs `ollama start` (an alias of `serve`) as the program's own child, with the plugin's variables and none of the edition's (no cloud refusal, the default model folder).
  **Fix:** not built yet; the choice of route is the next milestone's (see ORDER 70's report).
  **How found:** `plugins/ollama/ollamaplugin.cpp` (the action) and `ollamastartprocessjob.cpp` (the process).
- **Symptom:** after Ollama's own install script, an engine listens at every boot and NVIDIA's repository appears in apt's sources.
  **Cause:** `install.sh` writes `/etc/systemd/system/ollama.service` (`User=ollama`, `Restart=always`, `WantedBy=default.target`), enables and starts it, and on a machine with an NVIDIA card adds NVIDIA's CUDA repository and installs `cuda-drivers`.
  **Fix:** never use the script for the edition; the package installs files only, and the display driver stays the edition's.
  **How found:** reading the release's `install.sh`.
- **Symptom:** a user unit shipped "off" is enabled on every machine after installation.
  **Cause:** `dh_installsystemduser` generates maintainer-script code that enables the user units it finds, on all machines (debhelper 14.5's manual).
  **Fix:** `dh_installsystemduser --no-enable` (override in `debian/rules`), so only the switch enables it.
  **How found:** the manual, read in the Debian packaging reference index; not yet measured in a build.
- **Symptom:** a brief asks for the engine "from its signed release" and there is no signature to check.
  **Cause:** Ollama's release publishes only checksums for its Linux bundles.
  **Fix:** pin the reviewed size and SHA-256 of each bundle in the recipe and check both the release's `sha256sum.txt` and GitHub's digest; say in the package description that the check is a pinned checksum, not a signature.
  **How found:** the release's asset list (no `.sig`, `.asc` or `.minisig`) and GitHub's attestations API (404).
- **Symptom:** a client of the Ollama API gets 404 from Debian's llama.cpp server.
  **Cause:** `llama-server` 0.9.0 answers the OpenAI-style routes (`/v1/models`, `/health`) and not Ollama's `/api/tags`, `/api/version` or `/api/pull`; it pulls no model by itself.
  It also logs at start that no API key is set and CORS allows all origins.
  **Fix:** llama.cpp is reached through each client's OpenAI-compatible or llama.cpp setting, not its Ollama setting; an origin limit and an API key are its own settings.
  **How found:** measured on 2026-11-21: Debian's `llama-server` started empty in router mode (`--models-dir` on an empty folder, `--host 127.0.0.1`) in a container with no network, each route asked with curl.

- **Symptom:** the publish check stops a page with "another person's email address" on a mail add-on's id.
  **Cause:** a Gecko extension id may have the form of an address (ThunderAI's does), and the check cannot tell it from one.
  **Fix:** in public text, name the id by where it is read (the add-on's manifest, `browser_specific_settings.gecko.id`); a policy file that must carry the id is a case to settle with the coordinator before it is committed.
  **How found:** the public publish check on this page, 2026-11-21.

## Credits

Ollama, by its authors ("Copyright (c) Ollama"); llama.cpp and ggml, by Georgi Gerganov and the ggml authors; ktextaddons, by Laurent Montel and Florian Richer; ThunderAI, by Mic.
