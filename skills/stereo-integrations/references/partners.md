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
