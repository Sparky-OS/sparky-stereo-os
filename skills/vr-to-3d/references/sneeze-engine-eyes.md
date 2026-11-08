# Sneeze (the Open Metaverse Browser's engine): build it, measure its two eyes

Learned on Sneeze at 758de54 (2026-11-03), Halogen v1.1.22, ANARI-SDK 0.17.0, Filament (the Metaversal fork), Wasmtime 43, on Debian testing in a container (ORDER 474, milestone 1).
Sneeze is a static library a host links; Rubidium (MetaversalCorp/Rubidium, SDL3) is the host application, and its Linux canvas is an X11 child window reparented into the chrome frame.

## What the code does (read, then proved by running)

- The engine owns one OpenXR instance (`XR_RUNTIME`, created in `ENGINE::Initialize`, zero extensions) and **never creates a session**: the documentation says "Detection only" (SneezeDoc `systems/xr.md`). On a machine with the edition's runtime the log says `XR_RUNTIME: OpenXR 1.1.58 initialized - runtime: DisplayXR Runtime ... 'v2.66.3'` and nothing is ever submitted.
- One viewport has **one camera**: the compositor builds a perspective camera from an orbit or an absolute pose (`VIEWPORT::Camera`, metres, Z up, identity looks along +X), `fovy` 60 degrees at 1080 px tall scaled with the height (so the focal length is 540 / tan 30 degrees = 935.3 px at any height), `aspect` from the width, near and far from the scene.
- ANARI's perspective camera has `imageRegion` (the standard way to an off-axis frustum) and ANARI-SDK defines `KHR_CAMERA_STEREO` (`stereoMode` none, left, right, sideBySide, topBottom, `interpupillaryDistance`), but **Halogen's Camera.cpp reads only position, direction, up, fovy, aspect, near, far**, and its extension list is `HALOGEN_NATIVE_SURFACE`, `HALOGEN_MATERIAL_UNLIT`, `HALOGEN_GEOMETRY_SKINNING`. No device in ANARI-SDK implements the stereo camera.
- Two ways to present: the native surface (`IVIEWPORT::FrameWindow` returns a window; Filament's Vulkan swapchain draws into it) and the readback path (`FrameWindow` returns nullptr; `OnFrameReady` gets RGBA). Halogen issue 3 says OpenXR and native surface extensions are being proposed.
- A fabric is JSON (or a signed MSF) plus WebAssembly plus glTF. The three public example files (`stool.json`, `wasm/map.wasm`, `assets/Stool.glb`, from SneezeDoc's example 01) load from `http://127.0.0.1:PORT/` with no outside service.

## Recipe: build (Debian testing, clang and libc++, release)

1. Image: `debian:testing` by digest, apt over https only, packages from the README (`clang lld libc++-dev libc++abi-dev libvulkan-dev libgl-dev libx11-dev ninja-build`) plus `cmake rustc cargo golang-go nasm python3 git build-essential libegl1-mesa-dev libwayland-dev libxcb1-dev libxkbcommon-dev pkg-config`. **Do not install `libjsoncpp-dev`** (trap below).
2. `./scripts/build-linux.sh --deps` as your user, `--cpus 4`: about 45 minutes, 6.8 GB of dependency trees (4.8 GB of them source clones and intermediates, Filament 2.2 GB and Wasmtime 1.7 GB); the Sneeze library then builds in about a minute.
3. The first Sneeze-only build needs `./scripts/build-linux.sh --fresh` once.
4. A host of your own goes in as one more executable beside `SneezeTest` (`tests/CMakeLists.txt`, `target_link_libraries (host PRIVATE Sneeze)`).

## Recipe: measure two eyes through the host surface (no engine change)

1. Host: `IENGINE` (`sRenderer` "halogen"), `ICONTEXT` (all defaults), `IVIEWPORT` with `FrameWindow` nullptr. `Context_Open(url)`, `Resize`, `Activate`; `OnFrameReady` gives RGBA frames.
2. Wait until the lit area is steady **within 1 %** (the count jitters by a few pixels on every GPU).
3. Place the one camera at each eye with `VIEWPORT::Camera`: same quaternion (parallel axes, never toe-in), position plus or minus half the interaxial along the camera's lateral axis (identity looks +X with Z up, so the left eye is at +Y).
4. Render each eye `2 s` pixels wider than shown (`s = f b / (2 Zs)`, `f` = 935.3 px, `b` the interaxial, `Zs` the zero-parallax distance; the width changes only the aspect, not the focal length) and crop the left eye's window `s` pixels further right and the right eye's `s` pixels left: an off-axis frustum meeting at `Zs`, with no black bars.
5. Write one picture, left eye first, each eye at its own size, and show it as the 3D area of a window declared `kde_stereo_content_v1` full side by side (`sbs-present` in the lane's folder is the proof rig's `subdecl.c` with `--image FILE`).
6. Disparity in pixels is `f b / z - 2 s` (left centroid minus right centroid; positive in front of the screen). Fit `k / (D + delta) - 2 s` over several distances `D`.
7. Controls that must fail: the same file undeclared (both eyes identical, `stereo` false in ScreenShot2's reply), the two halves swapped (the sign flips: +8.03 against -8.03 px), the engine's mono render in both halves (0 pixels differ between the eyes).

Result (stool 0.3 m wide, `b` 64 mm, `Zs` 4 m, 640x360 per eye, lavapipe): measured disparity 18.2, 5.7, -0.5, -3.6, -5.7, -8.4, -9.9, -10.9 px at 2, 3, 4, 5, 6, 8, 10, 12 m; fit `k` 58.5 against `f b` = 59.9 (2 % low), `delta` -0.29 m (the model's centroid is 0.29 m nearer than its origin), rms 0.12 px. Through Stereo KWin (+stereo3d46, ScreenShot2): 5.9, -0.3, -8.0 px at 3, 4, 8 m, each eye's bounding box the same size as the source half (one resize, at KWin), the top row of the silhouette identical in both eyes (vertical disparity 0).

## Traps

- **Symptom:** `Error: .../builds/linux-x64/build is not a directory` from `build-linux.sh` with no flag.
  **Cause:** the Sneeze-only build assumes a configured tree. **Fix:** `--fresh` once, then the plain command. **How found:** the message.
- **Symptom:** link errors `undefined symbol: Json::Value::operator[](char const*) const` (and `isNull`, `asString`) in every executable.
  **Cause:** `libjsoncpp-dev` is installed (the README lists it as optional): the OpenXR loader then builds against the system jsoncpp, which is a libstdc++ library, while everything else is libc++.
  **Fix:** remove `libjsoncpp-dev` only (removing `libjsoncpp26` removes cmake), then `./scripts/build-linux.sh --only openxr-sdk --rebuild`, `--fresh`, build. **How found:** the symbol names; `ldd` of the loader.
- **Symptom:** the host does not compile: `reference to 'FILE' is ambiguous`, `use of undeclared identifier 'f'`.
  **Cause:** Sneeze has `SNEEZE::FILE`. **Fix:** write `::FILE`.
- **Symptom:** the log says `failed to load ANARILibrary 'halogen' ... libanari_library_halogen.so: cannot open shared object file`, `VIEWPORT: Failed to initialize renderer`, and the host's frames stay at 0 (size 0x0).
  **Cause:** the device library is looked up like any shared library. **Fix:** `LD_LIBRARY_PATH` with `deps/builds/linux-x64/release/libs/Halogen/install/lib`, `.../ANARI-SDK/install/lib` and `.../Wasmtime/install/lib`. **How found:** the log's two `could not open library` lines.
- **Symptom:** `error while loading shared libraries: libc++.so.1` in another image.
  **Cause:** the host is linked to libc++. **Fix:** copy `libc++.so.1.0` and `libc++abi.so.1.0` and make the two links (`docker cp` of the `.so.1` name copies a dangling link).
- **Symptom:** a wait loop for "the same lit pixel count twice" never ends.
  **Cause:** the count moves by a few pixels. **Fix:** compare within 1 %.
- **Symptom:** the 3D area is not shown 1 to 1: the captured eye is 648 px wide for a 640 px picture.
  **Cause:** `subdecl.c` sizes the hole from the window (`win / 16` margins, the bottom `win / 8` more). **Fix:** `--window 730x480` for a 640x360 area; check by comparing each eye's bounding box with the source half.
- **Symptom:** `dbus-launch: command not found` in the DisplayXR rig image. **Fix:** `dbus-daemon --session --address=unix:path=$XDG_RUNTIME_DIR/bus --nofork` (the lane's `stereo-in-container.sh`).
- **Symptom:** on the AMD iGPU (RADV, Mesa 26.1.6) the frames match lavapipe (largest channel difference 14 of 255 on 8 pixels) but the process ends with `libc++abi: terminating due to uncaught exception of type std::system_error: mutex lock failed: Invalid argument` (once) or does not exit (once); every run logs `Leaked 1 child fabric(s)` at `Context_Close`.
  **Cause:** not found; a shutdown race in the engine after `Deactivate` and `Context_Close`, in the documented order. **Fix:** none; write the frames before closing. A line printed with `printf` to a pipe is lost when the process aborts: flush it.
- **Symptom:** on the RTX through CDI, `Missing required instance extensions` and `Unable to create Vulkan instance`.
  **Cause:** the ICD file name was guessed (`VK_DRIVER_FILES=.../nvidia_icd.json`). **Fix:** read the file CDI mounts and set that name. Not run again.

## Perks

- Sneeze's own XR stub already logs which OpenXR runtime the loader found, so `grep XR_RUNTIME` on any run says which runtime a build would talk to.
- The 3D areas of the stereo proof rig and an engine that draws into an X11 child window (Rubidium's canvas) are the same shape: a declared child.

Credits: Sneeze, Rubidium and the Open Metaverse Browser Initiative (Metaversal Corporation, Dean Abramson, David Sernaque and contributors by the repository's history); Halogen by Jonathan Hale; Filament by Google and the Metaversal fork; ANARI by the Khronos Group; Wasmtime by the Bytecode Alliance; the Stool model by plaggy (CC BY 4.0); the rig and `subdecl.c` by the stereo-proof-rig skill's authors.
