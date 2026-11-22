# Partners: the edition's AI engines, on this computer and at providers

**For** whoever packages an AI engine for the edition or wires a program's AI feature to the person's choice (KMail and the other KDE programs through ktextaddons, Vibe, Kdenlive, Spirula Studio, Betterbird with ThunderAI): the engine package as built, how a computer gets the runner its card can use, what each program reads today, what "off" means, and the traps already met.

**Check freshness first.**
Written on 2026-11-21 from ORDER 70: the engine packages `ollama`, `ollama-cuda` and `ollama-rocm` built and proved; the Partners page in System Settings designed and not built yet (its settings file, `sparky-stereo-partnersrc`, is the design's).
Read against Ollama v0.40.16, Debian testing's llama.cpp 1:0.9.0+dfsg-1 and ggml 0.29.0-1, ktextaddons 2.1.2-8, kdepim-addons 26.08.2, Kdenlive 26.08.2, Vibe 3.2.2, ThunderAI 5.2.0, Betterbird 153.7.0esr-bb13 and NVIDIA's repository for Debian 13 (CUDA 13.1 to 13.5).

## The design it follows

Daniel, 2026-11-21: "Partner, not assistant, add the page, it must have interface, model and card choices for the system defaults - allow cloud models on ollama right away. do a similar thing for each AI program, we should have a dedicated partner page, there will be lots of AI and can mix and match different providers, local and cloud, text, image, 3d and such".
- **One place.** The system defaults per kind of work (interface, model, card) and each program's own choice live in one settings file the Partners page writes; programs read it, never a copy of their own.
- **Nothing before the person's choice.** Nothing listens and nothing is downloaded until the person chooses on the page; a download shows its size first and waits on a metered connection, and that is said.
- **Said per choice.** The page says, for each choice, whether it runs on this computer or sends what the person writes to a provider; "nothing you write leaves this computer" is said only where it is true. Ollama's cloud-hosted models are allowed from the start.
- **Keys in KDE Wallet**, never in a plain file.
- **It works, or the person is told**: a failed start or download is told with its cause and kept by the problems engine.

## The engine: Ollama, split by hardware

The recipe is `sparky-os/packages/ollama` in the edition's build repository: upstream's release build, repackaged, nothing compiled.

1. `make-orig.sh DOWNLOADS OUT` fetches only what `release.tsv` pins (https only), checks each file's size and SHA-256, checks both bundles against the release's own `sha256sum.txt`, and checks the tag's source by the commit its tarball's pax header names and the git tree id of its files (`git write-tree` on a bare index).
   It writes `ollama_V.orig.tar.xz` (the tag's source) and `ollama_V.orig-release.tar.xz` (the kept payload, AMD's licence texts, `EXCLUDED.tsv` with each left-out file's size, SHA-256 and reason, and `MANIFEST.sha256`).
2. `build.sh OUT DOWNLOADS` runs that step once (its output is kept in `DOWNLOADS/orig-V` and reused), then builds in a container with no network: `prepare-lean.py` qualifies the payload for Lean Code without claiming a compilation, `dpkg-buildpackage`, `lean.release check-debs`, lintian.

| Package | Holds | Depends on |
| --- | --- | --- |
| `ollama` | the program, the processor runners, llama.cpp's libraries and the Vulkan runner in `/usr/lib/ollama`; the user service | Debian's libvulkan1 and glibc |
| `ollama-cuda` | the CUDA 13 runner only (Turing and newer) | NVIDIA's `cuda-cudart-13-*`, `libcublas-13-*` and `cuda-nvrtc-13-*` from NVIDIA's repository and the driver's libcuda1; recommends `libnvjitlink-13-*` and `libnvfatbin-13-*` |
| `ollama-rocm` | the ROCm 7.2 runner with AMD's ROCm 7.2.1 libraries and their licence texts | Debian's libdrm2, libdrm-amdgpu1, libnuma1, libelf1t64, zlib1g, libzstd1; `ollama-rocm-data` |
| `ollama-rocm-data` (`Architecture: all`) | rocBLAS's GPU kernels (671 MB of code objects and tables) in `/usr/share/ollama`, linked from `ollama-rocm` where rocBLAS looks (`$ORIGIN/rocblas/library`) | nothing |

What the repack leaves out, and why:
- **NVIDIA's CUDA libraries.** NVIDIA's CUDA EULA (last updated 2026-01-26) lets "applications developed by you" carry the files its Attachment A lists, and `libnvfatbin` is not listed; the edition did not develop Ollama. NVIDIA's own packages put `/usr/local/cuda-13/targets/x86_64-linux/lib` on the loader's path (`cuda-toolkit-13-config-common`'s `/etc/ld.so.conf.d/987_cuda-13.conf`, an alternative to the newest 13.x), so the runner finds them with no file of ours.
- **The CUDA 12 runner**: NVIDIA's CUDA 12 runtime has no package in NVIDIA's repository for Debian 13 nor in Debian; Maxwell, Pascal and Volta use the Vulkan runner.
- **GCC's OpenMP library**: nothing in the bundle links it.
- **The ROCm bundle's libdrm, libdrm_amdgpu, libnuma and libelf**: Debian's serve them.
- **The MLX bundle**: not packaged, a third copy of a GPU runtime with no machine to prove it.
AMD's ROCm libraries stay: Debian ships ROCm 6.4, and the runner needs ROCm 7.2's `libamdhip64.so.7`; their licences (MIT, BSD 2-clause, NCSA, Apache 2.0 with LLVM exceptions) allow redistribution, and the texts come from AMD's repositories at the tag `rocm-7.2.1`.

The service: `ollama.service`, a user service installed with `dh_installsystemduser --no-enable`; `OLLAMA_HOST=127.0.0.1:11434`, `OLLAMA_ORIGINS=moz-extension://*` (the setting ThunderAI documents for mail add-ons); models in Ollama's own place, `~/.ollama/models`; Ollama's cloud-hosted models allowed, as upstream ships it; the card is upstream's own rule (every card it finds, Vulkan on) until the Graphics page gives the engine one.

## Proofs, as run on 2026-11-21

The recipe's `tests/` folder, each in a throwaway Debian testing container where the packages were installed by apt from a flat repository of the build:
- `unit-off.sh` (root, after `apt install ollama`): the user service is installed and `disabled`, no link under `/etc/systemd/user`, nothing listens, no engine runs. Its red control `unit-default-red.sh` gives "enabled".
- `engine-empty.sh` (an ordinary user, `--network none`): the unit's own `ExecStart` and `Environment` lines; listening on `127.0.0.1:11434` and nothing else; no model in the store; a `moz-extension://` origin gets `Access-Control-Allow-Origin`, a web page's origin `403 Forbidden`; a model download fails with its cause ("dial tcp: lookup registry.ollama.ai ... network is unreachable") and the store stays empty.
- `runners-link.sh ollama ollama-rocm`, and `ollama-cuda` with NVIDIA's CUDA 13.5 runtime installed: every program and ggml back end resolves its libraries (`ldd` with `/usr/lib/ollama` on the path, since the engine loads `libggml-base` before it opens a back end).
- `gpu-discovery.sh CUDA` (the RTX 3060 through CDI, NVIDIA's driver 615 on the host): `library=CUDA compute=8.6 "NVIDIA GeForce RTX 3060" libdirs=ollama,cuda_v13 driver=13.4`; the 13.5 runtime runs on the driver's CUDA 13.4.
- `gpu-discovery.sh Vulkan` on the same card without `ollama-cuda` (with the rig's `libxext6` and `libegl1`, see the traps): `library=Vulkan description="NVIDIA GeForce RTX 3060" libdirs=ollama,vulkan`.
- Since `0.40.16+ds-2` the tests take the Partners card: `CARD=CHOICE gpu-discovery.sh LIBRARY@PCI...` starts the unit's own `ExecStart` and passes only when the engine reports exactly those cards; `card-start.sh USER CHOICE=EXPECTED...` does the same through `systemctl --user` in a container booted with systemd (`--cgroupns=private --security-opt writable-cgroups=true --tmpfs /run --tmpfs /tmp --cap-add SYS_RESOURCE`, the account in the group of the host's render nodes). On the workstation with `sparky-stereo-graphics` 0.2.16 and the engine's four packages installed: Automatic and the RTX 3060 gave `CUDA@0000:01:00.0` alone, the APU `Vulkan@0000:0b:00.0` alone, Processor only `cpu`, each listening on 127.0.0.1:11434 and stopping cleanly; a card that is not here failed the service once with status 4, kept the problem with "Use the processor only" among its actions, and nothing listened. The Graphics command gave the APU's memory from sysfs (536,870,912 bytes, its carve-out) and the RTX 3060's through NVML (12,884,901,888).
- Not proven: the ROCm runner on an AMD card (none here that its gfx list covers).
- Perks of the engine's own log: `OLLAMA_DEBUG=2` prints each `llama-server` discovery run with its `libDirs`. Discovery runs once for each runner folder (`discover/runner.go`: `llama-server --list-devices` with `LD_LIBRARY_PATH` and `GGML_BACKEND_PATH` set to that folder), then a native probe (`ollama gpu-discover --lib-dir ...`). A runner that finds no card (CUDA with `CUDA_VISIBLE_DEVICES=-1`) makes that probe exit 1 ("native GPU discovery failed"), and discovery goes on with the next folder: it does not hide the other runners.
- At its first start the engine writes a key pair, `~/.ollama/id_ed25519` and its `.pub`, and prints the public key to its log (Ollama's identity for its own service); nothing is sent then.
- With cloud-hosted models allowed, the running engine asks `ollama.com` at start for its hosted model list and its model recommendations (no text is sent): seen as two failed requests in a run with no network.

## Which card the engine uses: the Partners choice, measured on Ollama 0.40.16

The card is one choice shared by the Graphics and Partners pages, `[Render] Partners` in `sparky-stereo-graphicsrc` (Automatic, any card, or `cpu`, Processor only).
The service starts `sparky-stereo-gpu-run --compute --category partners /usr/bin/ollama serve`, which takes the variables of `sparky-stereo-gpu-env --category partners --print compute-env`: only the chosen card is visible to every runner, and `ollama-cuda` stays installed whatever the choice.
Ollama reads no variable for its runner folders: `OLLAMA_LIBRARY_PATH` is only a label in its log, and its library root is the executable's own folder after `filepath.EvalSymlinks` (`ml/path.go`), so a folder of links cannot move it; the visibility variables are what work.

The workstation, every runner installed (`ollama`, `ollama-cuda`, `ollama-rocm`), the RTX 3060 through CDI and the Renoir APU through its own render node (`--device /dev/dri/renderD128`), no model:

| Variables | What the engine computes on |
| --- | --- |
| none | CUDA on the RTX 3060 (the APU is left out as integrated) |
| `OLLAMA_IGPU_ENABLE=1` | CUDA on the RTX 3060 and Vulkan on the APU, both |
| the RTX 3060 chosen: `CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 HIP_VISIBLE_DEVICES=-1 VK_LOADER_DRIVERS_SELECT=*nvidia* DRI_PRIME=pci-0000_01_00_0! OLLAMA_IGPU_ENABLE=1` | CUDA on the RTX 3060 alone |
| the APU chosen: `CUDA_VISIBLE_DEVICES=-1 HIP_VISIBLE_DEVICES=-1 VK_LOADER_DRIVERS_SELECT=*radeon* DRI_PRIME=pci-0000_0b_00_0! OLLAMA_IGPU_ENABLE=1` | Vulkan on the APU alone |
| the same without `OLLAMA_IGPU_ENABLE=1` | the processor: "dropping integrated GPU" |
| the processor: `CUDA_VISIBLE_DEVICES=-1 HIP_VISIBLE_DEVICES=-1 GGML_VK_VISIBLE_DEVICES=` | the processor |
| `OLLAMA_LLM_LIBRARY=vulkan` | Vulkan on the RTX 3060 (one runner folder only) |
| `OLLAMA_LLM_LIBRARY=cpu` | the processor |

Vulkan's choice between the two cards without the CUDA runner (`ollama` only, `OLLAMA_IGPU_ENABLE=1`): `GGML_VK_VISIBLE_DEVICES=0` gave the APU and `=1` the RTX 3060 (the order is the loader's, after Mesa's device-select layer puts its default first, so an index is not a name); `MESA_VK_DEVICE_SELECT=1002:1638!` and `=10de:2504!`, `DRI_PRIME=pci-0000_0b_00_0!` and `=pci-0000_01_00_0!`, and `VK_LOADER_DRIVERS_SELECT=*radeon*` and `=*nvidia*` each gave that card alone.
`compute-env` uses the PCI form of `DRI_PRIME` with `!` (two identical cards have the same vendor and device ids) beside the loader's driver filter; Mesa's environment variables page: "For Vulkan it's possible to append !, in which case only the selected GPU will be exposed to the application".
For CUDA it uses the card's UUID from `/proc/driver/nvidia/gpus/SLOT/information`, and `-1` for any other card (CUDA C++ Programming Guide 13.0: "If one of the indices is invalid, only the devices whose index precedes the invalid index are visible"); for ROCm, the card's place among the KFD's graphics nodes, matched by `drm_render_minor` in `/sys/class/kfd/kfd/topology/nodes/N/properties`, with `HIP_VISIBLE_DEVICES=0`, since HIP otherwise falls back to `CUDA_VISIBLE_DEVICES` (ROCm's HIP environment variables page). The ROCm part is not proven here: the APU is gfx90c, which the runner does not carry, and `/dev/kfd` was not passed.

## The Partners page (sparky-stereo-partners 0.1.0)

- **Where it sits:** a category of its own at the top of System Settings: `share/settings-partners.desktop` in `/usr/share/systemsettings/categories/` (`X-KDE-System-Settings-Category=partners`, an empty parent, weight 55, between Apps & Windows and Security & Privacy), and the page's metadata names `partners` as its parent. Plasma 6.7's System Settings reads every `categories/*.desktop` on the data path (`app/SettingsBase.cpp`), so a package adds one without a patch; seen on screen in the rig.
- **One command for every fact and change:** `sparky-stereo-partners status --json | resolve --kind K [--program ID] | set-default | program | card | engine on|off | models | download | provider | install-plan | install`. The page (a thin `KQuickConfigModule`) runs it, so programs, tests and the page read the same answers; choices wait for Apply, actions run at once.
- **Settings:** `/etc/xdg/sparky-stereo-partnersrc` (shipped) under `~/.config/sparky-stereo-partnersrc`, key by key; the command writes only the person's file, through `kwriteconfig6`. The card is not in it: it is Graphics' `[Render] Partners`.
- **Install:** `pkexec /usr/libexec/sparky-stereo-partners/install-engine plan|install`, root, with the hardware setup's own `partner` lines (`sparky-stereo-hardware --auto --dry-run` needs root, so the sizes of the runner are shown after the one authentication, `auth_admin_keep`, before anything is downloaded).
- **Downloads:** the model's size from the registry's manifest first; held on a metered connection and when NetworkManager cannot say (exit 5, "Download anyway" is the person's explicit choice), through `sparky-stereo-apt`'s `metered()`.
- **The wallet row, as run:** on a new account the first key makes KDE Wallet show its new-wallet dialog (driven by fake input in the rig: Classic, a password twice); the key read back from the wallet is the key written, the settings file holds only `Wallet=sparky-stereo-partners/provider-ID`, and no file in the home folder or `/etc/xdg` holds the key.
- **Rows, as run (`tests/partners-test.sh`, 49 checks):** in a container booted with systemd, the packages installed by apt, no network: the engine on and off through `systemctl --user`, its address taken (exit 6, the other program named, kept), the card that cannot be used (exit 4, kept by Graphics), the model list from a stand-in registry, a download held when metered and when unknown, the stand-in's few kilobytes downloaded, the registry gone (exit 3, kept), a provider and a program's own choice, `resolve`.

## The page's traps

- **Symptom:** a stand-in registry serves a blob and Ollama 0.40.16 says "http: no Location header in response".
  **Cause:** Ollama follows a redirect inside the registry's origin and takes the Location of one that leaves it (`server/download.go`, `downloadDiscoveryRedirect`), as the real registry sends a blob to its CDN.
  **Fix:** the stand-in answers a blob with 307 to another origin of this computer (`127.0.0.2` for `127.0.0.1`; `localhost` resolved to `::1` and was refused).
  **How found:** the engine's error, then the source.
- **Symptom:** `kwallet-query -w` on a new account: "Wallet kdewallet not found".
  **Cause:** `kwallet-query` never makes a wallet; since KF 6.18 Debian's `kwallet6` runs `ksecretd` behind a `kwalletd6` shim.
  **Fix:** ask KDE Wallet to open the wallet over D-Bus (`org.kde.KWallet.open`, `gdbus call`), which makes it through its own dialog.
  **How found:** the command's own message in the rig.
- **Symptom:** in a rig session, the wallet's daemon dies at once ("Process org.kde.kwalletd6 received signal 6").
  **Cause:** D-Bus activates it with the environment `dbus-run-session` had before `WAYLAND_DISPLAY` was set.
  **Fix:** `dbus-update-activation-environment WAYLAND_DISPLAY QT_QPA_PLATFORM XDG_RUNTIME_DIR`, as a Plasma login does.
  **How found:** the command's message, then the daemon run by hand.
- **Symptom:** asking KDE Wallet to make a wallet with `gdbus call` returns an error after 25 seconds while its dialog is still open.
  **Cause:** gdbus's own call limit; KWallet opens a wallet synchronously and waits for the person (KIO's `kpasswdserver.h`: "KWallet opens a wallet synchronously with a timeout of 24 days").
  **Fix:** `gdbus call --timeout 600`, and the command's own limit above it.
  **How found:** the kde_corpus query on opening a wallet.
- **Symptom:** KDE Wallet's dialog for a new wallet offers GPG first.
  **Cause:** with gpgme present, `ksecretd`'s new-wallet page (KF 6.30) selects "Use GPG encryption, for better protection"; "Classic, blowfish encrypted file" is the other choice.
  **Fix:** none needed: the choice is the person's; a test that drives the dialog clicks Classic first.
  **How found:** the rig's picture of the dialog.
- **Symptom:** KDE Wallet makes the wallet through its dialog (`kdewallet.kwl` appears), yet the step that asked reports it was not made.
  **Cause:** the handle `org.kde.KWallet.open` answered through KF 6.30's `kwalletd6` shim was not a usable answer.
  **Fix:** ask the wallet itself afterwards (`kwallet-query -l`), write the key, read it back with `-r`, and count the step only when the key read back is the key written.
  **How found:** the rig's wallet folder and the command's message.
- **Symptom:** fake input built into `$XDG_RUNTIME_DIR` says "Permission denied" when run.
  **Cause:** the user manager mounts `/run/user/UID` without exec.
  **Fix:** build it in the home folder. In the wallet's dialog, the first click on "Classic, blowfish encrypted file" only focuses the window: click twice, then Enter (Next), type the password, Tab, type it again, Enter (Finish).
- **Symptom:** the page's lists show "None" for an interface that is set.
  **Cause:** `currentIndex: indexOfValue(...)` ran before the ComboBox had its model, and is not evaluated again when the model arrives.
  **Fix:** read the index from the list itself: `model.findIndex(o => o.value === current)`.
  **How found:** the rig's picture.
- **Symptom:** an apt install in a rig stops at "Configuration file '/etc/apt/sources.list.d/sparky-stereo.sources' ... end of file on <standard input> at conffile prompt".
  **Cause:** the rig wrote the edition's source file before installing `sparky-stereo-apt`, which ships it as a conffile.
  **Fix:** `-o Dpkg::Options::=--force-confnew`.
- **Symptom:** the link gate, or a rig's apt, cannot install an edition package: "sparky-stereo-apt Depends sparky-apt", then "sparky-stereo-hardware Depends nvidia-detect".
  **Cause:** the edition's packages depend on SparkyLinux's own repository (`repo.sparkylinux.org`, suites `core` and `tiamat`) and on Debian's `non-free`.
  **Fix:** both in the gate's `sources.json` (with SparkyLinux's public key) and in the rig, and the edition's packages the page depends on as the gate's siblings.
- **Symptom:** `systemsettings kcm_sparkystereo_partners` shows no window after 15 seconds in the rig.
  **Cause:** the page runs `status --json` before it shows (about 5 s in the rig: the Graphics command is asked five times).
  **Fix:** wait for KWin's window list (a KWin script printing `workspace.windowList().length`), never a fixed sleep.

- **Symptom:** a web page in the browser can read what Debian's `llama-server` answers on `127.0.0.1`.
  **Cause:** its CORS default is every origin (`--cors-origins` default `*`, credentials allowed), unlike Ollama's `OLLAMA_ORIGINS`.
  **Fix:** the page's unit starts it with `--cors-origins localhost` (the Origin header is reflected only for this computer's own pages); measured: `Origin: https://example.com` gets no `Access-Control-Allow-Origin`, `http://localhost:3000` gets it.
  **How found:** `llama-server --help` (0.9.0) in a container, after the reconcile's empty run logged "CORS allows all origins".
- **Symptom:** KMail's AI follows Ollama from the page but nothing happens on llama.cpp or a provider.
  **Cause:** ktextaddons 2.1.2's llama.cpp add-on is unfinished (`LLamaCppManager::loadModels`, `getChatCompletion`, `getResponses` are `// TODO`, also on master on 2026-11-21), and the generic add-on knows only its listed providers, never an address.
  **Fix:** the patched library follows only an Ollama interface and logs why otherwise; the page's KMail row says it.
  **How found:** reading `plugins/llamacpp/llamacppmanager.cpp` at Debian's tag and on master.
- **Symptom:** the language check fails for the eight other languages as soon as one English sentence is added.
  **Cause:** `msgcmp` counts an untranslated message as missing, and `msgfmt --statistics` reports it.
  **Fix:** `msgcmp --use-untranslated`, and a list of sentences waiting for the translations lane (`po/pending-translation.txt`); any gap not on the list still fails (red: one sentence taken off the list).
- **Symptom:** the command's `--help` stays English with a translated catalogue.
  **Cause:** `tr(CONTEXT, __doc__)`: `xgettext` extracts only literals.
  **Fix:** the help text is a literal in the `tr()` call; the module's docstring says where it is.
- **Symptom:** a new sentence in Graphics fails its translations test in eight languages.
  **Cause:** `autotests/translations-test.py` requires all ten languages complete.
  **Fix:** reuse a sentence the page already has in ten languages (the partners' memory reasons show as "not measured on this computer yet" and "Now: the processor only"), and say the rest on the Partners page, whose waiting sentences are listed.
- **Symptom:** Flathub's Betterbird would not see the person's ThunderAI manifest.
  **Cause:** its sandbox has no access to `~/.mozilla` (`finish-args`: `--persist=.thunderbird` only).
  **Fix:** not built: it needs `flatpak override --user --filesystem=~/.mozilla/managed-storage:ro eu.betterbird.Betterbird`; the app center places the maker's archive instead.

- **Symptom:** under Stereo Union the Partners page in System Settings shows no element depth: both eyes are identical at `ElementLimit` 12.
  **Cause:** System Settings hosts a page in a `QQuickWidget` (`WAYLAND_DEBUG=client`: no `kde_stereo_depth_v1` at all), which the edition's Qt never draws as a pair; and in a rig with NVIDIA's card a Qt Quick window on NVIDIA's EGL is never drawn as a pair either (`get_depth` and `depth_state(1, 0)` arrive, no `set_desktop_depth`), with the page and with plain controls alike.
  **Fix:** none in the page. Measure the page's own QML in a Qt Quick window of its own (`KQuickConfigModuleLoader::loadModule` and `mainUi()` in a `QQuickWindow`) on Mesa's EGL (`__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json`): every button and list stands at +12.000 (left +6, right −6), as Union's CSS predicts (their one shadow is the strongest in the window). Two buttons flush with that window's right edge read flat; not explained.
  **How found:** the wire record of each case, then a plain-controls window as the control.

## The page, 0.1.1: llama.cpp, signing in, programs that read a file of their own

- **llama.cpp, the other local engine** (Daniel's "Ollama, with llama.cpp as the fallback", a path the person chooses): interface `llamacpp-local` (`openai-compatible`, `http://127.0.0.1:8080/v1`). Install through the same helper (`install-engine plan|install llamacpp`): Debian's `llama.cpp-tools` and `libggml0-backend-vulkan` (any card with a Vulkan driver; the processor back ends come with `libggml0`). Debian's `llama.cpp-services` is not installed: its system service starts at installation. The page's own user service, `sparky-stereo-llama-server.service`, installed off (`dh_installsystemduser --no-enable`), runs `llama-server` in router mode on the person's folder `~/.local/share/llama.cpp/models` with `--host 127.0.0.1 --port 8080 --offline --cors-origins localhost`, through `sparky-stereo-gpu-run --compute --category partners`. It downloads no model: the page says where to put GGUF files and lists them (from `/v1/models` while on, from the folder while off).
- **Signing in to Ollama's service** is Ollama's own route, through the engine (0.40.16, `server/routes.go`): `POST /api/me` answers the account, or 401 with `https://ollama.com/connect?name=HOSTNAME&key=BASE64URL(public key)`; the engine signs its requests to ollama.com with `~/.ollama/id_ed25519`, which it wrote at its first start. `POST /api/signout` makes the engine `DELETE /api/user/keys/KEY` at ollama.com. The command's `account`, `signin` (opens the connect page with `xdg-open`, exit 7) and `signout`; the page asks when it opens while Ollama is on, and says what signing in links (the computer's name and Ollama's key). Proof without the real service: `127.0.0.4 ollama.com` in `/etc/hosts`, a certificate authority of the test's own in `/usr/local/share/ca-certificates` before the engine starts (Go reads the system pool), `tests/standin-ollama-com.py` on port 443.
- **KDE's text add-ons follow the page** (ktextaddons 2.1.2-8+stereo3d1, `partners-follow.patch`): with no instance in `autogeneratetextinstances`, the library asks `sparky-stereo-partners resolve --kind text --program DESKTOP-ID` and makes one Ollama instance in memory (nothing written until the person changes it). KMail's choice answers Kontact and the Sieve editor (`ProgramInfo` `Also=`). "Start Ollama" becomes "Open Partners".
- **Betterbird with ThunderAI** (ThunderAI offered, not installed): ThunderAI reads `browser.storage.managed` in its background page, once at start. Betterbird 153.7.0esr-bb13 answers it from an enterprise policy naming the add-on (`/etc/thunderbird/policies/policies.json`, then `<install>/distribution/policies.json`), else from a managed-storage manifest: per person `~/.mozilla/managed-storage/ID.json`, system-wide `/usr/lib/mozilla/managed-storage/` (its `ext-storage.js`, `NativeManifests.sys.mjs`). `sparky-stereo-partners sync` writes the person's manifest from the text choice (ThunderAI's keys: `connection_type` `ollama_api` with `ollama_host`, `ollama_model`, or `openai_comp_api` with `openai_comp_host`, `openai_comp_model`, `openai_comp_use_v1`), unlocked, no key, after every change and at login; a system policy would override every account, so none is shipped. The app center places Betterbird from its maker's archive in `/opt/betterbird` (the vendor tree kind with an `archive`).
- **Automatic for the partners' card** (Graphics 0.2.17): a machine record `[MeasuredPartners]` names the card the partners computed fastest on; the A10's (qwen3.5:2b, three runs, 2026-11-21) is the integrated Carrizo (3.73 tokens a second against the processor's 3.43 and the discrete Hainan's 3.17, which held 12% of the model). Without a record a card whose own memory is under 3 GiB is not Automatic's pick (`--print reason`: `measured`, `unmeasured`, `unmeasured-memory`, `cpu-memory`).
- **The page's lists** take the width of their longest entry (`implicitContentWidthPolicy: ComboBox.WidestText`, capped by the page); a label beside a button is `Layout.fillWidth` with `elide` and a `ToolTip` when `truncated`; a block's name is `Layout.alignment: Qt.AlignTop`.
- **Languages:** `tests/check-lang.py` runs in the build's test step; sentences waiting for the translations lane are listed in `po/pending-translation.txt` (one `CONTEXT|TEXT` per line) and named in its output, any other gap fails. From 0.1.2 every catalogue is whole (119 sentences each, 1071 values checked) and the list is gone. The page on screen in German and Japanese needs the rig's `de_DE.UTF-8` and `ja_JP.UTF-8` generated and `fonts-noto-cjk` installed, with `LANG`, `LC_ALL` and `LANGUAGE` set together.

## Speech back ends: Vibe in KDE's speech-to-text library (ORDER 72)

**For** whoever gives KDE programs dictation through a local engine: the library's interface, the server's lifetime, the stand-in server, the virtual microphone, and the traps met (written 2026-11-22, ktextaddons 2.1.2-8+stereo3d3; continued the same day for +stereo3d4: every engine says why it cannot dictate, the server starts at the press; and for +stereo3d5: the language field, after the first run with a real model; Vibe 3.3.5, read against 3.3.8).

### What the library is, read before building

- KDE's text add-ons have a speech-to-text library, `libkf6textspeechtotext1`: engines are Qt plugins in `kf6/speechtotext/` (`TextSpeechToText::SpeechToTextClient`, `EngineType` `Locale` or `Network`), each making a `SpeechToTextPlugin` that gets the microphone through `audioDevice()` at `sampleRate()` (mono, 16 bits) and answers with `speechToTextDone(text)`; programs use `SpeechToTextAction` or `SpeechToTextToolButtonWidget`, whose `textAvailable(text)` the program inserts where the person types.
- At 2.1.2 (Debian testing) the library is unfinished: nothing calls `SpeechToTextManager::switchEngine()`, `initializeInput()` (the microphone) has no caller, the Whisper and Google engines print "Not implemented yet", and the action calls into an engine that was never made. Laurent Montel finished the manager upstream in September 2026 (in v2.2.0 and v2.3.0: the engine stored in the program's settings is loaded at the first dictation, the action starts and stops the capture, the engine gives its result at `stop()`).
- The engines upstream, at v2.1.2, v2.3.0 and master alike, are `google`, `vosk` and `whisper`. Google is a stub at v2.3.0 too (`// TODO`). v2.3.0's Whisper engine is real but runs `whisper_helper.py` from a Python environment of its own (`pip install faster-whisper`, which brings ctranslate2 and tokenizers; models from Hugging Face). Vosk is off by default (`SPEAK_TO_TEXT_VOSK_PLUGIN`, "Experimental") and needs alphacep's `vosk-api` library. On Debian testing (snapshot 2026-11-19) there is no `python3-faster-whisper`, `python3-ctranslate2`, `libvosk*`, `vosk-api` or `python3-vosk`; there is whisper.cpp 1.9.5 (`libwhisper1`). Upstream's open merge request !71 (arojas) builds Vosk against a system library.
- Upstream exported the settings dialog only in v2.3.0 (`46f09141`, "Export class"): before, `SpeechToTextConfigureDialog` was a test export, and Debian builds with `-DBUILD_TESTING=OFF`, so no program could open the engine choice.
- No program in Debian links the library: on the dated snapshot of 2026-11-19, `apt-cache rdepends libkf6textspeechtotext1` names only `libktextaddons-dev`; KMail and kdepim-addons link the text-generation and text-to-speech parts, not this one. So the engine is proved through the library's own tool button, and a program needs one action in its editor to offer dictation.

### The recipe as built

1. Carry upstream's manager (`speech-to-text-manager-v2.3.0.patch`, `Origin: backport`, Laurent Montel as author): the files of v2.3.0 for the manager, the plugin's `stop()`, the engine-name helpers, the action, the tool button and the test program `speechtotextgui`; keep the 2.1.2 entry point `speechToText()` beside `speechToText(QObject *)` so no symbol goes; leave out the Whisper Python installer of later versions.
2. The engine (`vibe-speech-to-text.patch`): `speechtotext/plugins/vibe/`, a client named `vibe`, `EngineType` `Locale`, metadata `{"X-KTextAddons-RequiredExecutable": "vibe-server"}`; the loader skips a plugin whose required program is not on `PATH`, so without Vibe the engine is not offered and nothing else changes.
3. When the person presses the dictation button, a job starts `vibe-server serve MODEL --host 127.0.0.1 --port 0`, so the model loads while they speak, and the plugin records into a `QBuffer`; the job reads the ready line `{"status":"ready","port":N,...}` (printed after the model is loaded); at `stop()` it posts the recording as a 16 kHz mono 16-bit WAV (`file`, `response_format=json`, and `language` only when Vibe's settings name one; never `detect_language`, see the traps) to `/v1/audio/transcriptions` as soon as the server is ready (at once when it already is), takes `{"text": ...}`, and stops the server with SIGTERM, then SIGKILL after 5 s, whatever the outcome. A server that ends or does not answer while the person still speaks is said at once and ends the capture. The job logs `vibe-server started, process N` and `vibe-server ended by the engine, process N`. `vibe-server` also exits within a second of its parent (`--exit-with-parent`, on by default). A second dictation while the first is still transcribed waits and says so (one server, one model in memory). Read against Vibe 3.3.8 (2026-11-21): `cli.rs`, `server/mod.rs` (the ready line) and `parent.rs` are as in 3.3.5; the transcription route keeps its fields and its `{"text"}` and `{"error":{"code","message"}}` answers, now streams the upload into a temporary file with a 64 KiB limit per form field (the file's limit stays 15 GiB), and answers `internal_error` (500) when ffmpeg itself fails, which the engine says as a failed transcription with the server's own reason.
4. The model: the one the person selected in Vibe (`model.path` in Vibe's data-home `github.com.thewh1teagle.vibe/app_config.json`; Vibe reads its store from the data folder, not the configuration folder), or a file chosen in Partners; the language: Vibe's own `transcription.modelOptions.lang`; with none, or `auto`, no language field, and the model detects the language and transcribes (Vibe 3.3.5's `whisper-rs` `full()`: a language that is absent, empty or `auto` is detected first; `server/form.rs` turns an empty field into none; Vibe's own desktop sends `language` only when set, and its handoff leaves it absent for automatic). No model selected: nothing starts and nothing is downloaded; the person is told the model Vibe's preset recommends for this computer (Default `ggml-large-v3-turbo.bin`, 1,624,555,275 bytes, with 8 GiB of memory or a device `vibe-server devices` lists; Light `ggml-medium-q8_0.bin`, 823,369,779 bytes, otherwise; the sizes are the publisher's file listing), and to download it in Vibe.
5. The card: the environment lines `sparky-stereo-partners resolve --kind speech` prints after its `PARTNER_*` lines are the server's environment, so it computes on the card chosen for partners.
6. The default: with no engine stored in the program (`[SpeechToText] engine` of its own settings), the library asks `sparky-stereo-partners resolve --kind speech --program DESKTOP-ID`; `PARTNER_KIND=vibe` makes `vibe` the engine, interface `none` turns dictation off and says so; nothing is written until the person chooses an engine in the library's settings. With nothing chosen anywhere (no Partners command), the first engine that can take a dictation is used, in name order: Vibe where it is installed.
8. An engine that cannot take a dictation is said, never replaced: `SpeechToTextEngineLoader::engineNotReadyReason(name)` gives one sentence for an engine that is not installed, one whose program is missing (the plugin's metadata names it: `X-KTextAddons-Engine`, `X-KTextAddons-EngineName`, `X-KTextAddons-RequiredExecutable`), and one this version only lists (`X-KTextAddons-NotAvailable` in the Google and Whisper metadata); the manager says it at the dictation, and the settings show it under the engine list as soon as the engine is chosen (`KMessageWidget` `mEngineMessage`).
9. Cancel: `SpeechToTextManager::cancel()` stops the capture, gives nothing, and deletes the engine's plugin (its job's destructor ends the server and emits nothing), then makes a fresh one. It runs on Escape on the library's dictation button while it records, when the requester of the dictation is destroyed (its window closed), when the application quits (`aboutToQuit`), and when the microphone cannot be opened after the server started.
7. Failures are said: the plugin's `speechToTextFailed(message)`, the manager's `speechToTextFailedFor(requester, message)`, and the action's and tool button's `errorOccurred(message)`; when no program listens to that signal the widget shows the sentence in a message box. One sentence each: the server did not start (with its own last line), the model did not load, the audio was refused (`invalid_audio`), the transcription failed (`busy`, others), no speech heard, nothing recorded, no model selected, the microphone not opened, no engine ready, no partner for speech.

### Proofs

- `tests/speech-to-text.sh SOURCE NEW_BUILD` in the recipe folder builds the library's speech targets with tests and runs them against the stand-in (`autotests/data/vibe-server-standin.py`: Vibe's command line, ready line, route and error shapes; modes `ok`, `clip`, `noload`, `noready`, `silent`, `invalid-audio`, `busy`, `empty`; it records its process number, its arguments, the form and the audio). Rows: the WAV header and bytes, the form, the command line, each failure's sentence, the server gone when the result is given, nothing started without audio or model, the engine offered with `vibe-server` on `PATH` and not without.
- Red control: with the job's stop removed, five cases fail on "the server is gone when the result is given"; with the loader's check removed, the loader test without `vibe-server` fails.
- The rig: the packages installed by apt, a private session bus with PipeWire, WirePlumber and pipewire-pulse of the container's own, a virtual microphone made of two null devices (`pactl load-module module-null-sink sink_name=vmic channel_map=mono rate=16000`, the sink the clip is played into; `pactl load-module module-null-sink media.class=Audio/Source/Virtual sink_name=mic channel_map=mono rate=16000`, the microphone; `pw-link vmic:monitor_MONO mic:input_MONO`; `pactl set-default-source mic`), a spoken clip (`espeak-ng`, then `sox` to 16 kHz mono) played with `pw-play --target vmic`, the tool button clicked by a small program built against the installed `libktextaddons-dev`, the text read back from its field. The stand-in in mode `clip` answers the known text only when the received audio's loudness follows the clip's (20 ms envelopes, correlation at least 0.6), so a silent recording answers "UNRECOGNISED AUDIO": that is the control that the microphone carried the clip.
- No model is loaded or run on a shared station; the row with a real model is a kit for a test machine.
- Since +stereo3d5 the stand-in follows the real server for the language fields: `detect_language` with a true word (`server/form.rs`: 1, t, T, true, TRUE, True, yes, on) is answered with `{"text": ""}`, and `language` absent, empty or `auto` with the text. A stand-in that answers whatever the fields are cannot see a request the real server answers with nothing: read the server's handling of every field the engine sends and make the stand-in do the same. `vibespeechtotextplugintest` writes Vibe's store per case (no language, `auto`, `pt` as the control) and reads the fields the stand-in received; red on +stereo3d4 for the first two (the sentence "Vibe heard no speech in the recording." instead of the text), green on +stereo3d5. The rig's R1, R20 (`en` set in Vibe) and R21 (`auto`) read the same, and R1p and R20p run the same rows on +stereo3d4's rig image as the red control; R22 reads the "not available in this version" sentence in each of the eight other languages from the message box (the rig image generates the nine locales; `%1` is the engine's own name in that language, "Szept" in Debian's Polish catalogue). A kind whose rig image and stage are gone is printed as not run (N/A), never as passed.
- Since +stereo3d4 the stand-in also has a set model-load time (`STANDIN_LOAD_SECONDS`, before the ready line and before the failures of `noload` and `noready`) and answer time (`STANDIN_ANSWER_SECONDS`), and writes when it `started`, was `ready`, got the `request` and was `terminated` (seconds since the epoch), so a row reads the server's lifetime against the driver's clicks.
- Tests that must run red against the previous build use only the library's public interface: `vibespeechtotextplugintest` gets the engine through `SpeechToTextEngineLoader::createSpeechToTextClient("vibe")->createTextToSpeech()` and drives `speechToText()`, `audioDevice()` and `stop()`; `speechtotextmanagertest0` and `1` (without and with `vibe-server`, one process each because the loader is one per process) drive `switchEngine()` and `speechToText()`; `speechtotextenginemessagetest` reads the settings widget. Red on +stereo3d3: 17 failures (the text 2052 ms after the stop with a 2000 ms load, against 12 ms green; the generic "No speech-to-text engine is ready" for a missing, Whisper or Google engine; no message in the settings).
- The rig's driver also presses Escape (`--escape-after-ms`), closes its window (`--close-after-ms`) and chooses an engine in the exported settings dialog (`--configure-engine`); the first build's image runs the same clip with the same 2 s load as the comparison row.
- A real model's comparison on a test machine needs no package installed: unpack each build's `libkf6textspeechtotext1` and run the same driver with `LD_LIBRARY_PATH` and `QT_PLUGIN_PATH` set to each; a watcher reads `/proc/PID/maps` for the library loaded and the driver's `vibe-server` children for when the server ran.

### Traps

- **Symptom:** the speech-to-text action of ktextaddons 2.1.2 does nothing, or a program crashes at the first dictation.
  **Cause:** the 2.1.2 manager never loads an engine and never opens the microphone; `speechToText()` calls the plugin pointer unchecked.
  **Fix:** carry upstream's manager of v2.3.0 (step 1).
  **How found:** reading `speechtotextmanager.cpp` at Debian's version and searching the tree for callers of `switchEngine` and `initializeInput`; the upstream commits on `textspeechtotext` since v2.1.2 (126 of them) through KDE's GitLab API.
- **Symptom:** a test that checks the server is gone after a transcription still passes with the job's stop removed.
  **Cause:** `QProcess`'s destructor kills its child when the job object is deleted, so "gone later" is true by another path.
  **Fix:** check the server's process at the moment the result is emitted (a slot connected to `finished` and `failed`).
  **How found:** the red control.
- **Symptom:** a build image made with `apt-get build-dep ktextaddons=2.1.2-8` stops the recipe at once: "dpkg-checkbuilddeps: error: unmet build dependencies: node-acorn nodejs".
  **Cause:** the Lean-prepared source adds the comment checkers' build dependencies (`gcc`, `node-acorn`, `nodejs`, `perl`, `python3`, `python3-yaml`).
  **Fix:** install those beside the package's own build dependencies.
  **How found:** the recipe log.
- **Symptom:** a size for `ggml-medium-q8_0.bin` cannot be found in Vibe's model catalogue.
  **Cause:** Vibe's catalogue (`website/public/models.json`) lists `ggml-large-v3-turbo.bin` but not the quantized medium model the Light preset names.
  **Fix:** read both sizes from the publisher's file listing (`https://huggingface.co/api/models/ggerganov/whisper.cpp/tree/main`, metadata only, nothing downloaded).
  **How found:** searching the release source for both file names.
- **Symptom:** the clip played with `pw-play --target NAME` into a virtual source (`media.class=Audio/Source/Virtual`) never reaches the recording (RMS 0, the stand-in's correlation 0.0).
  **Cause:** WirePlumber links a player's output only to a sink; the player went to the default null sink (`pw-link -l` shows `pw-play:output_FL |-> auto_null:playback_FL`).
  **Fix:** play into a null sink and link its monitor port into the virtual source's input port with `pw-link` (the recipe above); measured: RMS 0.075 recorded, correlation 0.978.
  **How found:** `pw-link -io` and `pw-link -l` in a throwaway session while the clip played.
- **Symptom:** `dbus-run-session` in the rig container: "Could not get password database information for UID of current process", then "Failed to start message bus".
  **Cause:** the container runs as an ordinary uid that has no account in the image.
  **Fix:** mount a small `/etc/passwd` and `/etc/group` naming that uid.
  **How found:** the session log.
- **Symptom:** a program whose chosen engine is gone (Vibe removed, a name from another version) dictates with another engine, or answers "No speech-to-text engine is ready for dictation: choose one in the speech-to-text settings."
  **Cause:** upstream's `switchEngine()` falls back to `fallbackFirstEngine()`, the first key of a `QHash`, whose order changes from process to process; on the edition that can be an engine that does nothing.
  **Fix:** `engineNotReadyReason()`, and no fallback for a named engine (recipe step 8); with nothing chosen at all, the first engine that can dictate, in name order.
  **How found:** reading `switchEngine()`; the manager test on +stereo3d3 gave the generic sentence for `nosuchengine`.
- **Symptom:** the person chooses Whisper or Google in the speech-to-text settings, presses the button and is told only to choose an engine in those settings.
  **Cause:** both engines of 2.1.2 only log "Not implemented yet" and refuse `loadSettings()`; 2.3.0's Google is still a stub, and 2.3.0's Whisper needs faster-whisper and ctranslate2 from PyPI, which Debian does not ship.
  **Fix:** they stay listed, marked `X-KTextAddons-NotAvailable`, and say "not available in this version" at the choice and at the dictation; the settings dialog carried as exported (upstream `46f09141`), so a program can show the choice.
  **How found:** the plugins read at the v2.1.2, v2.3.0 and master tags; `apt-cache policy` on the snapshot for the Python packages and Vosk.
- **Symptom:** the text arrives the whole model-load time after the person stops (2052 ms with the stand-in's 2000 ms load).
  **Cause:** the first build started `vibe-server` only at `stop()`, so the model loaded after the person finished.
  **Fix:** start the server at the press (recipe step 3): 12 ms from the stop to the text in the same case.
  **How found:** the plugin test with `STANDIN_LOAD_SECONDS=2`, red against +stereo3d3 and green after.
- **Symptom:** a dropped dictation (the job deleted) emits "Vibe could not transcribe the recording: it stopped with status 0." while it is destroyed.
  **Cause:** the destructor stops the server with `waitForFinished()`, which delivers `QProcess::finished` synchronously into the job's own handler.
  **Fix:** the destructor marks the job done and disconnects the process before stopping it.
  **How found:** the job test that expects no signal from a dropped job.
- **Symptom:** a test that the server is gone after the microphone failed finds no process number from the stand-in.
  **Cause:** the server is started and ended within milliseconds, before the Python stand-in writes anything (the log shows exit status 15, a crash exit).
  **Fix:** the engine logs the server's process number when it starts it; the test reads its own log through a message handler, then checks `/proc/N`.
  **How found:** the manager test's first green run, and its log.
- **Symptom:** with a real model every dictation ends "Vibe heard no speech in the recording.", with a clip and with a real microphone, while every rig row passes.
  **Cause:** the engine sent `detect_language=true` when Vibe's settings named no language. Vibe 3.3.5's server hands it to `whisper-rs`, whose `full()` detects the language and returns before decoding when `detect_language` is set (`server/crates/whisper-rs/src/full.rs`), so the answer is `{"text": ""}`; whisper.cpp's own option of that name does the same. The stand-in answered with the text whatever the fields were, so no rig row could see it. Vibe's `/openapi.json` lists no form field of the route at all, so the fields' meaning is only in the source.
  **Fix:** send `language` only when Vibe's settings name one; with none or `auto`, no language field (the model detects and transcribes). The stand-in answers `detect_language` with an empty text, as the server does.
  **How found:** the main session's run on the test machine with `ggml-medium-q8_0.bin`: the same recording posted to the real server gave the text with `language=en` (20.2 s) and with neither field (28.5 s), and `{"text":""}` in 6.4 s with `detect_language=true`; then Vibe 3.3.5's source (`routes/transcriptions.rs`, `server/transcription.rs` `build_options`, `server/form.rs`, `whisper-rs` `context.rs` `full_params` and `full.rs`).
- **Symptom:** a test-machine kit stops at once with no message on a machine without `/sys/class/thermal/thermal_zone*`.
  **Cause:** under `set -euo pipefail`, `sort -n /sys/class/thermal/thermal_zone*/temp` with no match fails and ends the script.
  **Fix:** read the processor's own hwmon sensor (`name` k10temp, coretemp, zenpower or cpu_thermal), else the thermal zones, else every `hwmon*/temp*_input`, with `nullglob`; skip a sensor that cannot be read; write "unknown" when none can, and name which sensors gave the reading. "The hottest sensor" is not the processor: on the station an NVMe drive read 66.9 C beside the processor's 55.8 C, and the kit waited on the drive.
  **How found:** the main session's run on the A10, which has hwmon only; then the kit's check on the station with the thermal zones hidden (`--mount type=tmpfs,dst=/sys/class/thermal`), which sat in its wait.
- **Symptom:** a recording carries silence now and then on a loaded machine, and the engine rightly says nothing was recorded.
  **Cause:** a fixed wait (six seconds of `pw-link` retries) before the private PipeWire was ready, so the virtual microphone was never linked.
  **Fix:** wait by condition (`pactl info` and `pw-link -o` answer, then the link is listed by `pw-link -l`, then the default source reads `mic`), up to 60 s, and make the setup its own row that stops the run when the microphone is not linked; record the microphone beside each run (`parecord --device=mic`) and write its level into the result.
  **How found:** the rig's second run of continuation 1 (37 of 44, the microphone not linked under a load of 34), then the same wait found still fixed in the test-machine kit.
- **Symptom:** one rig session in several has no virtual microphone ("default @DEFAULT_SOURCE@, not linked"), and its recordings say "Nothing was recorded from the microphone."
  **Cause:** WirePlumber started right after PipeWire, before PipeWire's socket existed, and exited at once ("Failed to connect to PipeWire"); with no session manager no link and no default source are made.
  **Fix:** start WirePlumber and pipewire-pulse only once `$XDG_RUNTIME_DIR/pipewire-0` exists (wait by condition), in the rig and in the test-machine kit; the setup row fails the run when it happens anyway.
  **How found:** the setup row of the rig's first run of continuation 2 (the +stereo3d4 session), then `wireplumber.log`.
- **Symptom:** a row that reads a message box the library shows has no `recording_started` in the driver's result.
  **Cause:** the box runs inside the button's click, and the driver's watch reads it and prints before the click returns.
  **Fix:** check the box's text on that route; prove that no recording starts on the `--listen-errors` route (R11, R12).
  **How found:** the eight language rows' first run (the text right, the row failed).
- **Symptom:** a Qt test class builds and then fails to link: "undefined reference to `vtable for ...`", and AutoMoc says "No relevant classes found. No output generated."
  **Cause:** moc counts braces inside raw string literals: JSON written as `R"({...` in a member function left one brace open, and moc skipped the class.
  **Fix:** build the JSON with `QJsonObject` and `QJsonDocument::toJson`, or keep the braces in each raw string balanced.
  **How found:** the build log's AutoMoc line for the test.
- **Symptom:** a row run with `LANG`, `LC_ALL` and `LANGUAGE` set to Brazilian Portuguese shows the size with a decimal comma (Qt took the locale) and the sentence still in English, though the `.mo` holds it.
  **Cause:** gettext translates nothing in a locale that is not generated (glibc falls back to C), whatever `LANGUAGE` says.
  **Fix:** install `locales` and run `localedef -i pt_BR -f UTF-8 pt_BR.UTF-8` in the rig image.
  **How found:** `msgunfmt` on the shipped catalogue, then the edition's own rule for translation tests.

## Which runner a computer gets

The hardware setup answers, as it answers for every per-vendor piece: `sparky-stereo-hardware`'s detection prints a plan line of its own kind, `partner`, naming `ollama-cuda` for the cards the edition's open modules run (Turing and newer, which run CUDA 13).
The setup never installs it; the Partners page reads the line (`sparky-stereo-hardware --auto --dry-run`, as root) and installs it with the engine.
Cards on NVIDIA's 580 driver, Kepler and unknown cards get no line.
AMD has no line yet: the ROCm runner carries gfx1030, gfx1100 to gfx1102, gfx1150, gfx1151, gfx1200, gfx1201 and four Instinct targets, and turning a card's PCI id into its gfx target needs a table the setup does not have; until then AMD cards use the Vulkan runner of `ollama`.
`tests/nvidia-branches.py` in the hardware recipe checks the line (it fails on the published 0.1.32's detection and passes with the change).

## Reading each part without pulling a model

1. **The engine's release.** `gh api repos/ollama/ollama/releases/latest` lists every asset with its size and `sha256:` digest; the bundle's parts come from the tag's `Dockerfile` and `scripts/build_linux.sh`, and a downloaded bundle is listed with `zstd -dc FILE | tar -tvf -` before anything is extracted.
2. **What a runner links.** `readelf -d` for `NEEDED` and `RUNPATH`, and `strings -a FILE | grep -o 'libnvrtc[^ ]*'` for what it opens at run time (cuBLASLt 13 opens `libnvrtc.so.13`).
3. **Debian's side.** In a testing container with `deb-src` added: `apt-cache policy`, `showsrc` and `rdepends`, then `apt-get download` of the small packages and `dpkg-deb -c` / `-x`.
4. **NVIDIA's side.** The repository's `Packages.gz` (`https://developer.download.nvidia.com/compute/cuda/repos/debian13/x86_64/`) gives every package's version, size and dependencies; download only the small config packages to read their `ld.so.conf.d` files and postinst.
5. **The library every KDE program uses.** ktextaddons at Debian's tag: `textautogeneratetext/core/textautogeneratetextinstancesmanager.cpp` and the plugins' `*settings.cpp`.
6. **A program's plugins and settings.** KDE's GitLab serves a tag's files without a login (`https://invent.kde.org/pim/kdepim-addons/-/raw/v26.08.2/...`, `https://invent.kde.org/multimedia/kdenlive/-/raw/v26.08.2/src/kdenlivesettings.kcfg`); its code search answers 401 without one. Qt 6 embeds a plugin's metadata as CBOR: read the `.json` in the source.
7. **Candidate models.** `curl -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' https://registry.ollama.ai/v2/library/NAME/manifests/TAG` gives every layer's size; the licence layer is a few kilobytes, fetched from `/v2/library/NAME/blobs/DIGEST` and checked against its digest. Languages come from the model's own card.

## What each program reads today (2026-11-21)

| Program | Kind of work | Reads |
| --- | --- | --- |
| KMail, Kontact, Sieve editor (ktextaddons 2.1.2) | text | one shared file for every program built on the library, `autogeneratetextinstances` (cascades from `/etc/xdg`): `[General] currentInstance`, `[Instance #N]` `enabled` (default false), `pluginName`, `uuid`, `Name`, `CurrentModel`, `ServerUrl` (default `http://127.0.0.1:11434`); KMail's three AI editor plugins are `EnabledByDefault: false` |
| Programs on KDE's speech-to-text library (ktextaddons 2.1.2-8+stereo3d5) | speech | the program's own settings `[SpeechToText] engine`, else `sparky-stereo-partners resolve --kind speech`; the Vibe engine then reads Vibe's `app_config.json` (`model.path`, `transcription.modelOptions.lang`); no program in Debian links the library yet |
| Vibe 3.2.2 | speech; text | `app_config.json`: `ai.connection.platform`, `ai.connection.model`, `ai.connection.ollamaBaseUrl`, `ai.tasks.{dictation,summary}.enabled` |
| Kdenlive 26.08.2 | speech to text; masking | `kdenliverc`: `[speech] speechEngine` (default `whisper`), `whisperModel` (default `turbo`), `whisperDevice`, VOSK's paths; `[sam] samModelFile` |
| Spirula Studio | 3D | its model profiles; the card through `sparky-stereo-gpu-env --app spirula-studio.desktop --3d --print id`, then `--choice ID --print env` |
| ThunderAI 5.2.0 | text | Thunderbird's enterprise policy (`3rdparty` → `Extensions` → its id), `connection_type` (`ollama_api`), `ollama_host`, `ollama_model` |
| Debian's llama.cpp 0.9.0 | text | `llama-server` answers OpenAI-style routes (`/v1/models`, `/health`), not Ollama's `/api/*`; it downloads no model by itself and allows every CORS origin unless told otherwise |

## Traps

- **Symptom:** a person installs "Ollama" from the app center's Chatbot page and no program finds an engine.
  **Cause:** that entry (`aptus://accbot_python3-ollama`, from SparkyLinux's APTus) installs `python3-ollama`, the client library.
  **Fix:** the engine is its own package, installed from the Partners page.
  **How found:** the app center's `accessories-chatbot.html` and its handler, `aptus-app python3-ollama`.
- **Symptom:** a plan writes one default per KDE program for the engine.
  **Cause:** at ktextaddons 2.1.2 every program's instances are in one shared file, not per program (an October reading of master said otherwise).
  **Fix:** read the version the edition installs before choosing the route.
  **How found:** `instanceConfigFileName()` returns `autogeneratetextinstances`, opened with KConfig's default cascade.
- **Symptom:** with the engine off, KMail offers "Start Ollama", which starts an engine outside the person's choice.
  **Cause:** when it cannot connect and `ollama` is on `PATH`, the plugin runs `ollama start` (an alias of `serve`) as its own child with its own variables.
  **Fix:** the edition's ktextaddons points the action to the Partners page (planned with the page).
  **How found:** `plugins/ollama/ollamaplugin.cpp` and `ollamastartprocessjob.cpp`.
- **Symptom:** after Ollama's own install script an engine listens at every boot and NVIDIA's repository appears in apt's sources.
  **Cause:** `install.sh` writes an always-on system service and, with an NVIDIA card, installs `cuda-drivers` from NVIDIA.
  **Fix:** never use the script; the package installs files only.
  **How found:** the release's `install.sh`.
- **Symptom:** a user unit meant to stay off is enabled for every user after installation.
  **Cause:** `dh_installsystemduser` adds `deb-systemd-helper --user enable` to the postinst by default.
  **Fix:** `dh_installsystemduser --no-enable`.
  **How found:** measured on 2026-11-21: a throwaway package with the same unit and debhelper's default gives `systemctl --global is-enabled` "enabled" and creates `/etc/systemd/user/default.target.wants/`'s link; `ollama` gives "disabled" and no link (the recipe's `tests/unit-default-red.sh` and `tests/unit-off.sh`). The restart snippet `--no-enable` leaves in the postinst goes through `deb-systemd-invoke`, which neither starts nor restarts a disabled user unit that is not running (init-system-helpers 1.69+nmu3, lines 118 to 148), so only a person who turned the engine on sees it restarted by an upgrade.
- **Symptom:** a brief asks for the engine "from its signed release" and there is no signature to check.
  **Cause:** Ollama publishes only checksums for its Linux bundles.
  **Fix:** pin size and SHA-256 in the recipe, check them against the release's `sha256sum.txt`, and say in the description that the check is a pinned checksum from the same origin as the file.
  **How found:** the release's assets (no `.sig`, `.asc` or `.minisig`) and GitHub's attestations API (404).
- **Symptom:** `dh_auto_configure` runs cmake on a package that compiles nothing, and stops with "Can't exec cmake".
  **Cause:** debhelper picks its build system from the source tree, and Ollama's tag has a top-level `CMakeLists.txt`.
  **Fix:** `dh $@ --buildsystem=none` for a repack of upstream's binaries.
  **How found:** the first build's log, `dh_auto_configure: error: exec (for cmd: cmake ...)`.
- **Symptom:** `dpkg-shlibdeps` stops on a runtime library a runner needs (libnuma, libdrm), in a build container with no network.
  **Cause:** it maps each `NEEDED` library to the package installed on the build system, so each must be installed there.
  **Fix:** name them in `Build-Depends` (here libvulkan1, libdrm2, libdrm-amdgpu1, libnuma1, libelf1t64, zlib1g, libzstd1); give `dh_shlibdeps` the private folders with `-l` and `--ignore-missing-info`, and leave out the package whose libraries come from another vendor's repository (`-Nollama-cuda`, its Depends written by hand).
  **How found:** reading `dpkg-shlibdeps`'s rule before the second build.
- **Symptom:** a CUDA runner copied from upstream's bundle cannot ship in the edition's repository.
  **Cause:** the CUDA EULA's distribution grant is the application developer's, and not every bundled file is in its Attachment A.
  **Fix:** depend on NVIDIA's own packages from NVIDIA's repository (the edition's hardware setup configures it on NVIDIA machines; `spirula-studio-cuda` already depends on `cuda-cudart-13-5`).
  **How found:** NVIDIA's EULA page, Attachment A's Linux list, read on 2026-11-21.
- **Symptom:** Lean Code's link and start gate stops the build with "https://developer.download.nvidia.com/.../libnvjitlink-13-5_13.5.37-1_amd64.deb: downloaded package identity differs from signed index".
  **Cause:** the gate compares a dependency's SHA-256, size and relationship fields (Depends, Pre-Depends, Provides, Conflicts, Breaks, Multi-Arch) with its signed index; NVIDIA's package declares `Provides: libnvJitLink.so.13 (= 13.5.37)` while NVIDIA's index lists `libnvjitlink.so.13` (Debian Policy allows only lowercase in package names).
  **Fix:** depend only on what the runner links or opens (`readelf -d` for `NEEDED`, `strings -a` for libraries opened at run time); nvJitLink and nvFatBin are neither, so they are Recommends, and apt still installs them by default.
  **How found:** the gate's message, then the package's control read from its first 256 KB (an HTTP range: a `.deb`'s control member comes before its data) against `Packages.gz`.
- **Symptom:** the link gate stops on hundreds of lines like "rocblas/library/TensileLibrary_..._gfx1030.hsaco: loader error ELF machine does not match amd64".
  **Cause:** rocBLAS's kernels are ELF files for the AMD GPU; the gate takes another machine's ELF as data only in an `Architecture: all` package under `/usr/share` (its rule follows Debian's qemu-system-data and Lintian's binary-from-other-architecture), and fails it anywhere else by design.
  **Fix:** move the kernel folder to an `Architecture: all` package under `/usr/share/PROGRAM`, with a `debian/PACKAGE.links` line that puts it back where the library looks, and a Lintian override naming why for all four tags that fire on such files: `arch-independent-package-contains-binary-or-object`, `unstripped-binary-or-object`, `arch-dependent-file-in-usr-share` and `shared-library-lacks-prerequisites` (848 files each here). An override hides its tag from `lintian -I` without `--show-overrides`, so a build that overrides one tag shows only the others: compare two builds, or run with `--show-overrides`, before calling a tag unused.
  **How found:** the gate's messages after the NVIDIA fix, and its rule in `sparky-os/lean/linkcheck.py` (`GUEST_DATA`).
- **Symptom:** the Vulkan runner on an NVIDIA card in a container: `load_backend: failed to initialize backend from .../libggml-vulkan.so: ggml_backend_init returned NULL`; `vulkaninfo` says "Failed loading library associated with ICD JSON libGLX_nvidia.so.0", then "Could not get 'vkCreateInstance' via 'vk_icdGetInstanceProcAddr'".
  **Cause:** CDI brings NVIDIA's libraries without their package dependencies: `libGLX_nvidia.so.0` links `libXext.so.6` and opens `libEGL.so.1` at run time, and a minimal container has neither (a desktop has both through NVIDIA's driver packages).
  **Fix:** in the rig, install `libxext6` and `libegl1` with `vulkan-tools`; nothing changes in the package.
  **How found:** `vulkaninfo --summary` in the container named the first library; the second is the stereo-two-cameras skill's trap for the same message (`LD_DEBUG=files vulkaninfo`).
- **Symptom:** a rig that should reach the NVIDIA card through Vulkan leaves the engine on the processor, though the image was made with `libxext6` and `libegl1`; `ldd libGLX_nvidia.so.0` says "libX11.so.6 => not found".
  **Cause:** the image had `ollama-cuda` installed with `dpkg -i --force-depends` (its `libcuda1` comes from CDI), so the next `apt-get install` refused everything ("Unmet dependencies") and the script committed the image anyway.
  **Fix:** run every `apt-get install` before the forced `dpkg -i`, and commit an image only when the install step exited 0.
  **How found:** `dpkg-query -W libxext6 libegl1` in the image named neither; a rig built in that order found the card. The lane's first selection table (processor only with `OLLAMA_LLM_LIBRARY=vulkan`) came from that image and was withdrawn.
- **Symptom:** the card chosen for partners is an integrated one (an APU) and the engine still computes on the processor: `dropping integrated GPU; to enable, set OLLAMA_IGPU_ENABLE=1`.
  **Cause:** Ollama leaves integrated cards out by default (`discover/runner.go`: allowed by default only for CUDA and for ROCm's gfx1151).
  **Fix:** the unit sets `OLLAMA_IGPU_ENABLE=1`; only the chosen card is visible, so the flag never adds a card the person did not choose.
  **How found:** the rig's APU row, with and without the variable.
- **Symptom:** `journalctl -t ollama` shows nothing for the running engine; its lines are under `sparky-stereo-gpu-run`.
  **Cause:** systemd names a service's journal lines after the first word of `ExecStart` (the wrapper), and the wrapper's `exec` keeps that name.
  **Fix:** `SyslogIdentifier=ollama` in the unit.
  **How found:** the systemd rig's journal, read with `-o cat --output-fields=SYSLOG_IDENTIFIER`.
- **Symptom:** the publish check stops a recipe on a mail add-on's id as "another person's email address".
  **Cause:** a Gecko extension id may have the form of an address (ThunderAI's does).
  **Fix:** Daniel, 2026-11-21: "addon IDs look alike emails huh? that place then is not an exeption, it's not an email": in a policy's own key for the add-on it is an identifier and stays as it is; the coordinator teaches the check that place.
  **How found:** the public publish check on a page naming the id.

## Credits

Ollama, by its authors ("Copyright (c) Ollama"); llama.cpp and ggml, by Georgi Gerganov and the ggml authors; AMD's ROCm libraries, by Advanced Micro Devices, Inc.; ktextaddons, by Laurent Montel and Florian Richer; ThunderAI, by Mic.
The speech-to-text manager and the exported settings dialog carried into the edition's build are Laurent Montel's (ktextaddons v2.3.0); Vibe and its `vibe-server`, by thewh1teagle; whisper.cpp, by Georgi Gerganov and the ggml contributors.
