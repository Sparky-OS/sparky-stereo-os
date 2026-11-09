# Sneeze (the Open Metaverse Browser's engine): build it, measure its two eyes

Learned on Sneeze at 758de54 (2026-11-03), Halogen v1.1.22, ANARI-SDK 0.17.0, Filament (the Metaversal fork), Wasmtime 43, on Debian testing in a container (ORDER 474, milestone 1).
Sneeze is a static library a host links; Rubidium (MetaversalCorp/Rubidium, SDL3) is the host application, and its Linux canvas is an X11 child window reparented into the chrome frame.

Milestone 2 (below, "The engine draws the two eyes") put an off-axis camera per eye into Halogen and Sneeze; the host-side crop of the first recipe is kept as the way to measure an engine that has none.

## What the code does (read, then proved by running)

- The engine owns one OpenXR instance (`XR_RUNTIME`, created in `ENGINE::Initialize`, zero extensions) and **never creates a session**: the documentation says "Detection only" (SneezeDoc `systems/xr.md`). On a machine with the edition's runtime the log says `XR_RUNTIME: OpenXR 1.1.58 initialized - runtime: DisplayXR Runtime ... 'v2.66.3'` and nothing is ever submitted.
- One viewport has **one camera**: the compositor builds a perspective camera from an orbit or an absolute pose (`VIEWPORT::Camera`, metres, Z up, identity looks along +X), `fovy` 60 degrees at 1080 px tall scaled with the height (so the focal length is 540 / tan 30 degrees = 935.3 px at any height), `aspect` from the width, near and far from the scene.
- ANARI's perspective camera has `imageRegion` (the standard way to an off-axis frustum) and ANARI-SDK defines `KHR_CAMERA_STEREO` (`stereoMode` none, left, right, sideBySide, topBottom, `interpupillaryDistance`), but **Halogen v1.1.22's Camera.cpp read only position, direction, up, fovy, aspect, near, far** (the m2 patch below adds `imageRegion`), and its extension list is `HALOGEN_NATIVE_SURFACE`, `HALOGEN_MATERIAL_UNLIT`, `HALOGEN_GEOMETRY_SKINNING`. No device in ANARI-SDK implements the stereo camera.
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

## The engine draws the two eyes (milestone 2: Halogen `imageRegion`, Sneeze `VIEWPORT::Stereo`)

Learned on Halogen v1.1.22 (which is its master head) and Sneeze 758de54; two local patches, each small, written to be offered back to its authors: Halogen reads `imageRegion` on the perspective and orthographic cameras and lists `ANARI_KHR_CAMERA_PERSPECTIVE` and `ANARI_KHR_CAMERA_ORTHOGRAPHIC`; Sneeze gets `VIEWPORT::Stereo({bEnable, dInterpupillaryDistance, dZeroParallaxDistance})`, a function `Stereo_Eyes` in `Compositor.cpp`, `RENDERER::SetCameraStereo`, and its frame becomes the left view and the right view side by side (`2 w` by `h`, `GetFrameWidth()`).

**The frustum.** The image plane is the one `fovy` and `aspect` describe; `imageRegion` `[x0, y0, x1, y1]` (lower left origin) is the part of it the frame shows, and may reach outside `[0, 1]`: the frustum grows on that side. Filament takes it cleanly: `Camera::setProjection(PERSPECTIVE, left, right, bottom, top, near, far)` with `left = -halfW + x0 * 2 halfW` (and the rest alike), `halfH = near * tan(fovy / 2)`. Without the parameter, or with `[0, 0, 1, 1]`, keep the old `setProjection(fov, aspect, ...)` call so a mono camera is untouched. For an eye `b / 2` to the left of the centre, the region is `[delta, 0, 1 + delta, 1]` with `delta = (b / 2) / (2 Zs tan(fovy / 2) aspect)` (the right eye `-delta`): the zero-parallax plane `Zs` shows the same rectangle in both views, nothing is cropped, and no column is empty. In Sneeze the metres become render units with the scene's render scale (`b` and `Zs` times `dRenderScale`; `b` is ANARI's `interpupillaryDistance`), the same scale the camera pose already uses; the eyes sit along `direction x up`.

**Recipe: build and test.**
1. Halogen: `git clone` at the tag Sneeze pins, `git submodule update --init external/corrade`, configure in a container against the Sneeze deps' ANARI-SDK and Filament installs with `-DBUILD_TESTS=ON`, and add `-isystem <ANARI-SDK>/include` and `-L<ANARI-SDK>/lib` to the flags (the test targets expect the SDK as a subdirectory). A rebuild after editing `Camera.cpp` takes seconds. Run `CameraTest` (and the other Corrade tests) in the rig image with `VK_DRIVER_FILES=.../lvp_icd.json`, then on the RTX.
2. Sneeze: the usual `./scripts/build-linux.sh` (one minute; `--fresh` once after adding a test file); `SneezeTest --stereo` needs no GPU. Put `libanari_library_halogen.so` of your build first on `LD_LIBRARY_PATH`.
3. Measure with the **flat square**, not the stool: a uniform 1 m square in the plane x = 0 (a glTF quad in its x = 0 plane faces world X; glTF Y is world Z), camera at `x = -D`, interpupillary distance 0.064 m, zero-parallax distance 4 m. Its centroid is its centre, a flat square shows the other eye no new surface, so disparity is exactly `f b (1/D - 1/Zs)` with `f = (h / 2) / tan(fovy / 2)` = 935.3 px at any height and nothing to fit. Weight the centroid by the red channel over the interior value: a threshold counts an edge pixel whole and is wrong by up to half a pixel. A wide wall (200 by 100 m) in the same plane fills both views: count columns that are black from top to bottom (0 expected; a mono picture shifted by `s` pixels shows `s`).
4. Show the engine's `2 w` by `h` frame as the 3D area of a declared window in the proof rig (`run-kwin-sbs.sh`); each eye's square keeps the size of its source half, the halves swapped flip the sign, the undeclared control gives 0.000 with `stereo` false.

**Results** (flat square, 640x360 per eye, `b` 64 mm, `Zs` 4 m): disparity 15.0, 5.0, 0.0, -3.0, -5.0, -7.6, -9.0, -10.0 px at 2, 3, 4, 5, 6, 8, 10, 12 m, against 14.97, 4.99, 0.00, -2.99, -4.99, -7.48, -8.98, -9.98 predicted: rms error 0.037 px on llvmpipe and 0.036 px on an RTX 3060 (driver 615.71.09), largest 0.09 px (at 8 m, on both GPUs), vertical difference at most 0.003 px, 0 black columns on the wall in four settings (`b` up to 0.5 m, plane down to 1.5 m). The first recipe's crop on the same square: error -1.01 px rms (see the first trap).

## Traps (milestone 2)

- **Symptom:** the first recipe's disparity sits 1.0 px under the prediction at every distance (zero parallax at 4.6 m, not 4 m).
  **Cause:** the crop shift `s = f b / (2 Zs)` = 7.48 px was rounded up to 8, and the wider render adds `2 s` of margin. **Fix:** do not crop on the host; use `imageRegion`, which takes any real shift. **How found:** a flat square instead of the stool: the error was the same at all distances.
- **Symptom:** the stool needs a fitted scale and offset (`k` 2 % low, `delta` -0.29 m) and the residual cannot go under 0.15 px.
  **Cause:** the stool is a solid object; the two eyes see different surfaces, so the centroid of what is lit moves by more than the camera does. **Fix:** measure a flat square. **How found:** the lit pixel counts differed between the eyes (2371 against 2438) while the camera was symmetric.
- **Symptom:** `git diff --stat` shows 7 640 lines changed in `AnariRenderer.cpp` and 415 in `include/Viewport.h` after a small edit.
  **Cause:** both files are CRLF, and a script that read them in text mode wrote LF. **Fix:** read and write with `newline=''`, or `sed -i 's/$/\r/'` back; a patch for them needs `git am --keep-cr` (plain `git am` strips the CRs and refuses it). **How found:** the diff stat; `git show HEAD:file | grep -c $'\r'`.
- **Symptom:** a new test segfaults in the first call of a freshly built scene.
  **Cause:** `anariNewArray1D(device, localArray, nullptr, nullptr, ...)` lends the caller's memory (no deleter), and the arrays were locals of the constructor. **Fix:** static arrays, or pass null memory and map/copy. **How found:** the crash came after "Starting" and before any engine line; the existing tests keep their arrays on the stack of the test function.
- **Symptom:** Halogen's test targets do not build: `'anari/anari.h' file not found`; `ScreenshotTest` and `render_scene` need `stb_image_write.h`.
  **Cause:** with `ANARI_ROOT` set, Halogen takes the SDK as a package, but the test targets link a plain `anari` target; the stb headers sit in a submodule not fetched. **Fix:** the include and library flags above; build with `-- -k` and ignore the two stb targets. **How found:** the compiler line.
- **Symptom:** two renders of the same frame differ.
  **Cause:** dithering: up to 2 levels per channel on llvmpipe and the RTX; in the stool scene up to 34 levels on about 40 000 pixels at 640x360 (the scene moves a little), also on the RTX. **Fix:** compare within that tolerance and never claim "byte identical" from frames; the mono path is identical in calls (no `imageRegion` sent, no second render, same buffer), and its frames fall inside the same noise (the flat square on the RTX, two runs of each Halogen: baseline against patched, 0 differing pixels in one pair and about 70 000 pixels by at most 2 levels in the others, the same as baseline against baseline). **How found:** a baseline rendered twice.
- **Symptom:** the ANARI status callback of a Corrade test never prints, whatever the severity, so a camera's `reportMessage` cannot be asserted.
  **Cause:** not found (the callback given to `anariLoadLibrary` and the one set as the device's `statusCallback` both stayed silent for Halogen's own existing messages). **Fix:** test the behaviour (the whole image is used), not the message. Not understood.
- **Symptom:** an older Halogen is used with the patched Sneeze and both views are identical and symmetric.
  **Cause:** the device ignores `imageRegion` and says nothing. **Fix:** Halogen lists `ANARI_KHR_CAMERA_PERSPECTIVE` from the patch on, and Sneeze refuses stereo without it: one error line (`stereo is on, but the ANARI device does not offer ANARI_KHR_CAMERA_PERSPECTIVE`) and one view of `w` by `h`. Run the other way round to prove it: `HALOGEN_LIB` pointing at the old library.
- **Symptom:** on the RTX in a container, `Missing required instance extensions`.
  **Cause:** milestone 1 guessed `/usr/share/vulkan/icd.d/nvidia_icd.json`; the CDI device brings `/etc/vulkan/icd.d/nvidia_icd.json` (`library_path` `libGLX_nvidia.so.0`). **Fix:** `VK_DRIVER_FILES=/etc/vulkan/icd.d/nvidia_icd.json` with `--device nvidia.com/gpu=0`; `vulkaninfo --summary` then shows the RTX 3060. **How found:** `ls /etc/vulkan/icd.d` inside the carded container.

## Perks (milestone 2)

- A stereo toggle in a running host is cheap: switching `Stereo` on, off, and resizing while on all work frame to frame (`resized while stereo: 640x180`), because the renderer resizes its side by side buffer with the viewport.
- Filament has its own stereo (`Camera::setCustomEyeProjection`, `Engine::Config::stereoscopicEyeCount`); the m2 patch does not use it, so the same two cameras serve the readback path now and two views of one double-width swapchain later.

## Perks

- Sneeze's own XR stub already logs which OpenXR runtime the loader found, so `grep XR_RUNTIME` on any run says which runtime a build would talk to.
- The 3D areas of the stereo proof rig and an engine that draws into an X11 child window (Rubidium's canvas) are the same shape: a declared child.

Credits: Sneeze, Rubidium and the Open Metaverse Browser Initiative (Metaversal Corporation, Dean Abramson, David Sernaque and contributors by the repository's history); Halogen by Jonathan Hale; Filament by Google and the Metaversal fork; ANARI by the Khronos Group; Wasmtime by the Bytecode Alliance; the Stool model by plaggy (CC BY 4.0); the rig and `subdecl.c` by the stereo-proof-rig skill's authors.
