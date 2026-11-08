# Who runs whose VR software, and where the two eyes pass

Learned in November 2026 (ORDER 478), by reading each project's own repository.
Every row below was read from the repository on 2026-11-08; a closed product is marked "reported" and comes from press or the vendor's page.

## The funnel is OpenXR

Every route ends at the host's active OpenXR runtime: the application submits one projection layer with one view per eye through `xrEndFrame`.
Each view carries a pose, a field of view and a sub image: a swapchain, an `imageRect` and an `imageArrayIndex` (OpenXR 1.1 registry, `XrCompositionLayerProjectionView` and `XrSwapchainSubImage`).
The eye of each view is fixed by the view configuration type (`xrLocateViews`: "The eye each view corresponds to is statically defined in XrViewConfigurationType").
If the application submits other poses or fields of view than the runtime located, "the runtime will map the view and FOV to the system display appropriately" (`XrCompositionLayerProjectionView`).
That sentence is what lets a runtime built for a 3D screen show a headset application.
`xrLocateViews` data "may change on subsequent calls", so the runtime may hand out its own eye offsets and fields of view, which is how separation is set per display.

So the one engine is the runtime: a runtime that presents the two views as one window declared full side by side (see [openxr-runtime-full-sbs.md](openxr-runtime-full-sbs.md)) serves every route that reaches OpenXR.

## Routes, and where the eyes cross a boundary

| Route | Layers | Where the two eyes pass |
|---|---|---|
| OpenXR application on a desktop | app, loader, runtime | swapchain images in the runtime's compositor |
| OpenVR game (SteamVR only) | game, xrizer or OpenComposite, OpenXR runtime | the shim turns OpenVR submit calls into `xrEndFrame` projection layers |
| Android OpenXR application on Android hardware | app, Khronos loader, runtime broker (a content provider), runtime package | `AHardwareBuffer` swapchains in the runtime's service |
| Android application in a container on a PC (Valve Lepton) | app, loader replaced by Valve's, host SteamVR runtime mounted into the container | the host's SteamVR runtime (closed) |
| Quest application on a PC (Android XR Bridge) | app, AXRB runtime package, bridge protocol, host bridge, host OpenXR runtime | equal sized array slices, then shared GPU textures (Windows today), `protocol/gpu_frame.h` keeps a dma-buf descriptor for Linux |
| PC game on a standalone headset (GameNative XR, WinlatorXR) | game, OpenComposite, a Windows side OpenXR runtime in Wine, a socket, the headset's runtime | GameNative: left, right and a third quad surface as separate buffers with pose and field of view per eye |
| PC game streamed to a headset (WiVRn, ALVR, Virtual Desktop, Steam Link) | host runtime or driver, encoder, headset client, headset runtime | both views are encoded and sent; the layout inside the stream was not read |
| Phone in a viewer | app, Monado's Cardboard driver on the phone | the phone's own compositor, rotation only from the IMU |

Older APIs (Oculus Mobile VrApi, Daydream) have no route of their own: Meta applications that still use Oculus loaders are patched (OVRPort) or fail ("Support Iron Man VR legacy Oculus loader startup", AXRB issue 18).
Cardboard is a phone viewer API; Monado implements it as an OpenXR driver, so it joins the funnel.

## How an Android application reaches a runtime

The loader on Android finds the active runtime through a content provider (authorities `org.khronos.openxr.runtime_broker` or `org.khronos.openxr.system_runtime_broker`) and the marker service `org.khronos.openxr.OpenXRRuntimeService` (OpenXR-SDK-Source, `specification/loader/runtime.adoc`, "Android Active Runtime Location" and "Android IPC and Runtime Access").
A runtime package declares its library in service metadata (`org.khronos.openxr.OpenXRRuntime.SoFilename`).
Monado's Android build is exactly that package (`src/xrt/targets/openxr_android`), with an out of process service reached through Binder and swapchains as `AHardwareBuffer`.
Its Linux build reaches the same service logic through a Unix socket that passes file descriptors (`doc/ipc-design.md`).
So a guest in a container needs a client runtime that finds a socket mounted from the host and exchanges buffers that can cross as dma-buf.
Valve's Lepton does the host side differently: it mounts the host SteamVR runtime's `androidarm64` files into the container (`compat_tool/liblepton/mounting.sh`) and swaps the loader by build id (`soreplacements.txt`).

## Reading a project's real state: traps found

- **Symptom:** the README says Windows only, yet the project is the answer for Linux. **Cause:** the history differs from the page: Android XR Bridge was started on 2026-06-17 as a Waydroid and Monado bridge with a dma-buf transport and a Monado host backend, then moved to Windows. **How found:** `git fetch --unshallow` on a blobless clone and `git log --format='%h %ad %s' | grep -i waydroid`, then `git show <commit>:README.md`.
- **Symptom:** a licence recorded last month is wrong. **Cause:** Android XR Bridge went MIT, then source available (2026-09-30), then MIT again (2026-10-15), launcher GPL. **How found:** `git log -- LICENSE`. Read the licence file's history, not only today's file.
- **Symptom:** an AI position recorded last month is wrong. **Cause:** ALVR's CONTRIBUTING now forbids LLMs in code, comments, documentation, discussions and artifacts; WiVRn's `AGENTS.md` says "You are not allowed to submit pull requests" and "report issues"; Monado has only a draft policy (merge request 3066, open) and its DCO text says only a human can certify. **How found:** read `AGENTS.md`, `CONTRIBUTING.md` and open merge requests, not the README.
- **Symptom:** the repository's API answer is a 404. **Cause:** the project lives on a Valve or freedesktop GitLab, not GitHub. Lepton is `gitlab.steamos.cloud/frame-public/lepton`; the news pages name no address. **How found:** the repository link inside a news page, then `git clone --depth 1 --filter=blob:none`.
- **Symptom:** a name suggests more than the code has. Lepton's image is `lepton_arm64_only`, so it targets Arm hosts; it is not a drop in for an x86 PC. **How found:** `TARGET_ARCH` in `image-14/android_device_valve_lepton/lepton_arm64_only/BoardConfig.mk`.
- **Symptom:** an upstream tree stopped but its fork moves. OpenComposite's own branch has no commit since 2025-07-21; GameNative's fork of it is current.
- **Symptom:** the emulator does not run OpenXR. The Android XR Emulator page says "The Android XR emulator is not supported for Unity or OpenXR apps."
- A component named in a notices file as closed (GameNative's `libredirect.so` and `libkgslshim.so`) decides "ownable" before any licence line of the rest does.
- Commit trailers show how a project treats AI: Android XR Bridge's history carries `Co-Authored-By: Claude` on 31 commits and says nothing against it.

## Rule of thumb for choosing a project

A project is worth building into the edition when it is open and buildable from source with no outside service, active in the last month, has an AI position that lets us work with it, runs on Linux, and meets the funnel.
Where AI help is forbidden, use the program as it is and let the person write any contribution.
