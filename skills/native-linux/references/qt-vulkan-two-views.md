# Two views on Qt's Vulkan path

Learned on ORDER 556 (November 2026), on qt6-base 6.11.2+dfsg-5+stereo3d21, Qt Quick 6.11.2+dfsg-3+stereo3d3, Stereo KWin +stereo3d54 and Mesa 26.1.6-1+stereo3d21 with its Vulkan stereo layer; extended on ORDER 573 and 574 (qt6-base +stereo3d22, Mesa +stereo3d24): [a surface that stops being a pair](#a-surface-that-stops-being-a-pair), [QVulkanWindow](#qvulkanwindow), [two views asked, one given](#two-views-asked-one-given).
Load it with [native-linux](../SKILL.md) when a Qt Quick window drawn once per eye is flat with `QSG_RHI_BACKEND=vulkan`, when a window that stopped showing depth is shown as two halves, when a QVulkanWindow program that asks for stereo buffers is flat, when a window is flat and nothing told the person, or when a change to Qt's Vulkan swapchain, the Wayland Vulkan window or the Vulkan stereo layer needs its proof.

The result first: from qt6-base `6.11.2+dfsg-5+stereo3d21` a Qt Quick window whose style shows the depth of its elements is a declared pair with the Vulkan renderer too, on radv, on NVIDIA's Vulkan driver and on lavapipe, with the parallaxes of the OpenGL path to a thousandth of a pixel.
Before, such a window was flat on every driver: Qt gave a window its two views in the Wayland EGL window only.

## The chain

1. **The engine asks.** Qt Quick sets the window's `_q_stereo_views` to 2 while a style shows depth (`_q_stereo_depth`), and draws a pair as soon as the swapchain has a right target (`QRhiSwapChain::currentFrameRenderTarget(RightBuffer)` differs from the left one). Nothing in Qt Quick knows the backend.
2. **The platform answers.** `QWaylandVulkanWindow` keeps the request (an event filter on the window's dynamic property, an atomic read by the render thread) and wants two views when the window asked for stereo buffers itself or when the engine asks and the compositor takes such a pair (`kde_stereo_content_manager_v1` version 3, `QWaylandStereoDepth::isSupported`).
3. **Whoever makes the swapchain asks the platform.** `QRhiVulkan` reads the window's `_q_stereo_views` native resource (`QPlatformNativeInterface::nativeResourceForWindow`, a number, not a pointer) and makes the swapchain with `imageArrayLayers` 2 where the surface allows it: "imageArrayLayers must be greater than 0 and less than or equal to the maxImageArrayLayers member of the VkSurfaceCapabilitiesKHR structure" ([VUID-VkSwapchainCreateInfoKHR-imageArrayLayers-01275](https://registry.khronos.org/vulkan/specs/latest/man/html/VkSwapchainCreateInfoKHR.html)). On a platform that does not answer, the window's format decides, as in upstream Qt.
4. **It says what it got.** After `vkCreateSwapchainKHR` the swapchain tells the platform its views (`setWindowProperty(..., "_q_stereo_surface_views", n)`). The window then reports a stereo format and marks the pair as the desktop's own depth (`kde_stereo_depth_v1.set_desktop_depth(1)`), which takes effect with the driver's next commit.
5. **The swapchain follows at the start of a frame.** `QRhiVulkan::beginFrame` builds the swapchain again when the wanted number changed, and only when the frame acquires a new image: Qt Quick renders the left eye in a frame ended with `SkipPresent` and the right eye in the next, and the views must not change between the two.
6. **With one view again the swapchain is built again on the same surface,** naming the old one as `oldSwapchain`. Up to qt6-base +stereo3d21 the surface was made again too (`QPlatformWindow::invalidateSurface()`), because the Vulkan stereo layer kept its declaration for the surface's life; from Mesa +stereo3d24 the layer withdraws it with the pair, and qt6-base +stereo3d22 keeps the surface (o574-0003) and breaks an older layer. See the first trap and [a surface that stops being a pair](#a-surface-that-stops-being-a-pair).

No new virtual function was added to `QPlatformWindow`: other projects build their own platform windows against Qt's private headers, and a new virtual would shift their tables. The two existing native interface calls carry the question and the answer.

## What Stereo KWin takes from a Vulkan client

- **A swapchain with two image layers.** Mesa's Wayland presentation (radv, lavapipe and the other Mesa drivers) packs layer 0 and layer 1 full side by side into one buffer and sends `kde_stereo_content_v1.set_content(3)` before the first attach, on a queue of its own; it destroys that object with the swapchain.
- **Over a driver outside Mesa** (NVIDIA's), the Vulkan stereo layer (`VK_LAYER_MESA_stereo`, package `mesa-vulkan-layer-stereo`, an implicit layer) raises `maxImageArrayLayers` to 2, makes the driver's swapchain twice as wide and declares the surface the same way. Up to Mesa +stereo3d23 it kept its declaration until `vkDestroySurfaceKHR`; from +stereo3d24 the declaration follows the swapchain that is current on the surface.
- **The mark is Qt's.** The pair of a window's own elements is the desktop's depth, not stereo content, so Qt adds `kde_stereo_depth_v1.set_desktop_depth(1)` on its own queue. Both requests reach the compositor before the first buffer of the pair.
- Lines to expect in the client's protocol log (`WAYLAND_DEBUG=client`), in this order: `kde_stereo_content_manager_v1.create(... wl_surface#N)`, `kde_stereo_content_v1.set_content(3)`, `kde_stereo_content_manager_v1.get_depth(... wl_surface#N)`, `kde_stereo_depth_v1.set_desktop_depth(1)`, then the compositor's `depth_state`.

## Recipe: prove a pair on a backend

The fixture and its tools are in [`scripts/qt-quick-pair`](../scripts/qt-quick-pair): `qdiscs.cpp` (six coloured discs on neutral grey, each with a parallax), `case.sh` (one fresh Stereo KWin session and one capture) and `disc-parallax.py` (the six parallaxes of a capture).

1. Build the fixture against the Qt under test: `cmake -G Ninja -S scripts/qt-quick-pair -B build && ninja -C build`.
2. Run one case per session, in a container with a render node for KWin (the capture is cancelled without one):
   `BACKEND=vulkan ICD=lvp APP=build/qdiscs CAPTURE=../stereo-proof-rig/scripts/capture.py bash scripts/qt-quick-pair/case.sh OUT`
   `ICD` picks the Vulkan driver the client gets (`lvp`, `radeon`, `nvidia`); KWin draws on the container's card either way.
3. Read it: `python3 scripts/qt-quick-pair/disc-parallax.py OUT/shot.png`, the `STATE` line in `OUT/client.out` and the requests in `OUT/wire.txt`.
4. The same case with `BACKEND=opengl` is the reference: the parallaxes must be equal.
5. The cases that matter, as `CLIENT_ENV`: nothing (the pair), `QDISCS_FLAT=1` (no depth, the 2D control, on a 3D mode and with `STEREO=0`), `QDISCS_LIFECYCLE=1` (resized, hidden, shown), `QDISCS_TOGGLE=1` (two views, one, two), `QDISCS_OFF=1` (two views, then one for good), `QDISCS_STRESS=1` with `WARM=10` (sixty changes in six seconds over a hide, a show and a resize; the window must end alive and as a pair), `KSCALE=1.25`, `QDISCS_FRAMELESS=1 QDISCS_WIDTH=941` at 125 %, and `DISABLE_LAYER_MESA_STEREO=1` on a driver outside Mesa (one picture, and the warning).

Measured, with the asked parallaxes 0.5, -0.5, 1.5, -1.5, 0.25 and 1 device pixels:

| Reading | Before (qt6-base +stereo3d20) | After (+stereo3d21) |
|---|---|---|
| Vulkan on lavapipe, radv, NVIDIA, 100 % | 0 pixels differ between the eyes, `views-asked 2 pair 0`, no `set_content` | 0.5, -0.478, 1.5, -1.383, 0.25, 1.0 on the three |
| OpenGL on the same three (llvmpipe, radeonsi, zink over NVIDIA) | 0.5, -0.478, 1.5, -1.383, 0.25, 1.0 | the same pictures |
| Vulkan at 125 % | flat | 0.5, -0.5, 1.5, -1.396, 0.25, 1.0, as OpenGL |
| Two views, then one, on NVIDIA | (never two) | 0 pixels differ; 244,232 before the surface was made again |

The two sunk discs read -0.478 and -1.383 on both backends: a deeper element is cut to its own rectangle, which moves the centroid of what is left.

Qt's own tests that cover the path:

- `tst_qrhi`, row `vulkanSwapChainFollowsWantedViews` (new, in the same patch): the swapchain gets two views at the start of the frame after the request, keeps them between the parts of a frame, has one again after it, and two over a resize. It needs a window surface and, to fail instead of skip on a platform that should give two views, `QTEST_STEREO_TWO_VIEWS=1`.
- Qt Quick's `tst_qquickwindowstereo` with `QSG_RHI_BACKEND=vulkan`: `drawsEachEyeInAPass` and `drawsThePairAfterAnExpose` fail before and pass after, on the three drivers.

Both are built outside a whole Qt build: `qt-cmake-standalone-test tests/auto/gui/rhi/qrhi` in a development build of the changed modules, run under a Stereo KWin with `LD_LIBRARY_PATH` at that build for the changed libraries and without it for the installed ones.

## Traps

- **Symptom:** on NVIDIA's Vulkan driver a window that stopped showing depth is shown as two squeezed halves, one per eye (a flat window whose eyes differ in 244,232 pixels); on radv and lavapipe it is right.
  **Cause:** the Vulkan stereo layer declares the surface when a two-layer swapchain is made and withdraws only when the surface is destroyed (`destroy_surface_data()` in `stereo_layer.c`), so a one-layer swapchain on the same surface is still shown as a pair. Mesa's own presentation ends its declaration with the swapchain.
  **Fix:** first in Qt (qt6-base +stereo3d21): with one view again the swapchain was released and the platform made the surface again. Then in the layer itself (Mesa +stereo3d24, patch 0040), which withdraws its declaration when its pair is no longer the swapchain presented on the surface; Qt's step was measured redundant with it and removed (qt6-base +stereo3d22, o574-0003). The protocol log shows `kde_stereo_content_v1.destroy()` at the change either way.
  **How found:** the toggle case ended on two views and passed; a case that ends on one view (`QDISCS_OFF=1`) showed it, and the protocol log had no `destroy` and no second `set_content`. A change of state is proved by capturing each state it can end in.
- **Symptom:** a test that changes the number of views dies in `QRhiVulkan::releaseSwapChainResources`, inside the Vulkan driver.
  **Cause:** `recreateSwapChain()` stored the new swapchain's stereo flag before it released the old swapchain's image resources, and the release walks `bufferCount * (stereo ? 2 : 1)` entries: a one-view swapchain's array was read past its end. Upstream never changes the number, so it never showed.
  **Fix:** the flag is stored after the release.
  **How found:** the new `tst_qrhi` row crashed where the Qt Quick fixture had passed by luck; `gdb -batch -ex run -ex bt` inside the container (never a host core dump) named the function.
- **Symptom:** the `STATE` line of a stress run says `views-asked 0 pair 0` although the capture is a pair.
  **Cause:** every change of views builds the swapchain again, which holds the timers back, so the sixty changes were not over when the line was printed at 7 s.
  **Fix:** capture later (`WARM=10`) and judge the capture and `client.alive`, not the line.
- **Symptom:** the "2D output" row of a matrix shows a pair's left eye, not the flat window.
  **Cause:** a fixture that sets `_q_stereo_depth` by itself draws a pair on a 2D output too (Stereo KWin shows a 2D output the left eye); a real style asks for depth only while the screen shows it.
  **Fix:** the 2D control is the window without depth (`QDISCS_FLAT=1`), on a 2D output and on a 3D one, compared pixel for pixel between the old and the new library.
- **Symptom:** a matrix's later rows behave differently from its first rows though nothing was changed in between.
  **Cause:** the rows mount a built library file from the build tree, and a rebuild during the run replaced it: containers already started keep the old file, later ones get the new one.
  **Fix:** stop the matrix before a rebuild, keep each library's rows in a folder of their own, and run the final matrix whole on the final library.
- **Symptom:** `qt-cmake-standalone-test tests/auto/wayland` stops at `.../QtStandaloneTestTemplateProject/src/3rdparty/wayland/protocols/...xml missing`, then at `libQt6OpenGL.so ... missing`.
  **Cause:** those tests name protocol files relative to the project's source folder, which for a standalone build is the template project, and they link Qt OpenGL.
  **Fix:** link the template project's `src` to the source tree's `src` in the scratch build tree, and build the `OpenGL`, `Test` and `qtwaylandscanner` targets first.
- **Symptom:** adding the round's repository to an image that holds a newer locally staged build makes `apt-get dist-upgrade` want to downgrade that build.
  **Cause:** the image's pin at 1001 for the edition's origin prefers the repository's version over the installed one.
  **Fix:** move `/etc/apt/preferences.d` aside for that one step and put it back; read the `Inst` lines.
- **Symptom:** after a window is hidden and shown, the protocol log has a new `set_content(3)` but no new `set_desktop_depth(1)`.
  **Cause:** Qt 6.11 keeps the `wl_surface` over a hide (only its role goes) and the mark is surface state, so it is still there; the Vulkan surface and the swapchain are made again.
  **Fix:** none needed; do not count requests, read the capture.
- **Symptom:** a search of Qt's Gerrit from a script answers 403.
  **Cause:** the review server refuses scripted clients.
  **Fix:** read the `dev` branch's history of the files on the GitHub mirror (`api.github.com/repos/qt/qtbase/commits?sha=dev&path=FILE`) and Jira's REST search, and say that open Gerrit changes were not searched.

## A surface that stops being a pair

Learned on ORDER 573 (November 2026), on Mesa `26.1.6-1+stereo3d23` and its Vulkan stereo layer, fixed in Mesa `26.1.6-1+stereo3d24` (patch 0040).

A program can make a swapchain with two image layers, then one with one layer, on the same surface: Qt Quick does it when a style stops showing depth, a game when the person turns 3D off.
The declaration of a pair must follow the swapchain that is current on the surface; a declaration that outlives its pair makes Stereo KWin show the one picture as two halves, one per eye.

| Route | Before 0040, two layers, one, two, one | With 0040 |
|---|---|---|
| Wayland, Mesa's own presentation (radv, lavapipe) | right: pair, flat, pair, flat | the same |
| Wayland, the Vulkan stereo layer (NVIDIA) | pair, **halves**, pair, **halves** | pair, flat, pair, flat |
| X11 through Xwayland, the layer (NVIDIA) and Mesa's own presentation (radv, lavapipe) | pair, **mixed**, pair, **mixed**; the window keeps `_KDE_NET_WM_STEREO_CONTENT` 3 | pair, flat, pair, flat; the declaration goes 3, 0, 3, 0 |

"Mixed" is the one-layer picture over half of each eye with the last pair's colour in the other half.
Both orders a program can use were measured: the next swapchain naming the previous one as `oldSwapchain`, and the previous one destroyed first.

**The rule as built.** Mesa's Wayland presentation already had it: the declaration is an object of the swapchain, and the retired swapchain's goes when a new one replaces it (patch 0024).
The layer and Mesa's X11 presentation now keep, per surface, the pair swapchain that is current there:

- a swapchain they do not pack (one layer, or a driver that has two layers itself) made on the surface withdraws the declaration;
- the current pair swapchain destroyed with nothing after it withdraws it;
- a pair swapchain retired by a newer one ("Upon calling vkCreateSwapchainKHR with an oldSwapchain that is not VK_NULL_HANDLE, oldSwapchain is retired", VkSwapchainCreateInfoKHR) leaves the declaration as the newer one has it.

On Wayland the withdrawal is `kde_stereo_content_v1.destroy`, which "resets layout, class and sub-class to zero on the next wl_surface commit", so the first one-view picture is the first one shown flat; a new declaration may follow at once.
On X11 the window's `_KDE_NET_WM_STEREO_CONTENT`, its version and its place in the stereo children list of the window that holds it (`_KDE_NET_WM_STEREO_CONTENT_CHILDREN`) go, one helper shared with the take-back of a pair the X server copies (`u_x11_stereo_withdraw()`).

**Recipe.** [`stereo-proof-rig/scripts/vk-views`](../../stereo-proof-rig/scripts/vk-views/README.md): `PHASES="2:4,1:4,2:4,1:0"`, with `OLD=1` and `OLD=0`, `X11=0` and `X11=1`, on each driver, captures at 2, 6, 10 and 14 seconds (X11: 3, 7, 11, 15, the window takes a second to map); `views.py` must read `PAIR FLAT PAIR FLAT` and the X11 lines `3`, `0`, `3`, `0`.
To prove a layer or a driver from a development tree without a package, mount the built `libVkLayer_MESA_stereo.so`, `libvulkan_radeon.so` or `libvulkan_lvp.so` over the installed one in the rig container; the rest of Mesa stays the staged one.

**Qt's own step went by measurement.** With the fixed layer, a window that goes from two views to one for good, two views, one, two, and sixty changes in six seconds gave the same pictures with Qt's surface remake and without it on NVIDIA's driver; the remake cost a new Wayland surface for the layer, and its registry round trip, at each change to one view (30 bindings of the stereo content manager in the sixty changes, 2 without). With the older layer and without the remake the window was two halves again (244,232 differing pixels, 556's number). So qt6-base +stereo3d22 keeps the surface and `libqt6gui6` breaks `mesa-vulkan-layer-stereo (<< 26.1.6-1+stereo3d24~)`.

## QVulkanWindow

Learned on ORDER 573 (qt6-base +stereo3d22, o574-0002).
`QVulkanWindow` built its own swapchain with one image layer and gave its renderer one framebuffer a frame, so a program asking for stereo buffers was flat on every driver, nothing declared, nothing told, while its format already claimed stereo.

**What a program does now.** Ask as for any Qt window: `QSurfaceFormat format = window.requestedFormat(); format.setStereo(true); window.setFormat(format);` before the window is shown.
In `startNextFrame()`, record the default render pass twice, once into `currentFramebuffer(QVulkanWindow::LeftBuffer)` and once into `currentFramebuffer(QVulkanWindow::RightBuffer)`, with each eye's camera, then `frameReady()`.
When the swapchain has one view the right eye's framebuffer is the left one, so draw the right eye only when the two differ (Qt Quick's own test for a pair, `currentFrameRenderTarget(RightBuffer)` against the left one, is the same idea).
A renderer with its own render passes takes `swapChainImageView(idx, RightBuffer)`, `msaaColorImage(idx, RightBuffer)` and `msaaColorImageView(idx, RightBuffer)`; the depth-stencil buffer is shared by the eyes, as in Qt's own Vulkan swapchain.

**How it is built.** The request is the platform's answer (the window's `_q_stereo_views` native resource on Wayland) or the window's requested format; the swapchain gets `imageArrayLayers` 2 where the surface offers it (VUID-VkSwapchainCreateInfoKHR-imageArrayLayers-01275); each swapchain image gets a view of layer 0 and one of layer 1 (`baseArrayLayer` 1), a framebuffer for each and a multisample color image for each; the platform hears the device and the views (`_q_stereo_surface_device`, `_q_stereo_surface_views`), so the Wayland window's format says what the surface has and a window given one view is told.

**A renderer that never asks for the right eye** (written before this, or a program that set a stereo default format for its OpenGL parts) would leave layer 1 undefined. Until the renderer asks for the right eye's framebuffer or image view, QVulkanWindow copies layer 0 into layer 1 at the end of each frame (`vkCmdCopyImage`, the swapchain made with transfer usage where the surface allows it), as an OpenGL program drawing to `GL_BACK` fills both buffers of a stereo window: the window is flat and right, 0 pixels differ between the eyes.

**Proof.** [`scripts/qvulkanwindow-pair`](../scripts/qvulkanwindow-pair/): six coloured squares on grey drawn with `vkCmdClearAttachments` (no shader), each eye moved by half an even parallax, so the disparity a capture reads is exactly the one asked; `-DQVKDISCS_STEREO_API=ON` builds it against the new API, `OFF` against today's (the unaware program).
Read a capture with stereo-proof-rig's `eyes.py` (lane 556's disc reader takes squares too).

| Row | Before (qt6-base +21) | After (+22) |
|---|---|---|
| Pair asked, lavapipe, radv, NVIDIA (layer) | flat, 0 pixels differ, nothing declared | 2, −2, 6, −6, 4, 10 px, exactly the prediction, on all three |
| The same at 125 % | (not run) | 2, −2, 6, −6, 4, 10 px |
| A still program (one frame) | (not run) | the same pair |
| A program built for today's QVulkanWindow, asking for stereo | flat | flat, eyes identical (the copy) |
| Not asked | flat | flat, nothing declared, nothing told |
| NVIDIA without the layer (`DISABLE_LAYER_MESA_STEREO=1`) | flat, nothing told | flat, told once |

Qt's own test: `tst_qvulkan`, row `vulkanWindowTwoViews` (two framebuffers and image views where the surface offers two layers, the left eye's for both without the request, the grab's left eye); `QTEST_STEREO_TWO_VIEWS=1` turns a surface with one layer into a failure instead of a skip.

Traps:

- **Symptom:** the new row fails its grab on lavapipe only: the red left eye comes back blue, also for a window that did not ask for stereo.
  **Cause:** lavapipe offers `VK_FORMAT_B8G8R8A8_SRGB` first and QVulkanWindow takes it; `grab()` swaps red and blue for `VK_FORMAT_B8G8R8A8_UNORM` only, as its documentation says.
  **Fix:** the test asks for `B8G8R8A8_UNORM` or `R8G8B8A8_UNORM` with `setPreferredColorFormats()`, as the fixture does.
  **How found:** the row printed `format 50 ... pixel ff0000ff` for the window that did not ask.
- **Symptom:** `tst_qvulkan`'s `vulkanWindowGrab` fails with `blueFuzz` 15 on NVIDIA and radv, and the test ends with a segmentation fault on NVIDIA.
  **Cause:** not this change: the same test built from the unchanged source fails the same way on the unchanged qt6-base +stereo3d21 under Stereo KWin's virtual output.
  **Fix:** none here; run the unchanged test on the unchanged library as the control before reading a failure as yours.
- **Symptom:** the test binary built with the new row exits 127 on the unchanged library.
  **Cause:** it needs the new exported functions, and the libraries are bound at start.
  **Fix:** build the control from the unchanged test file (`git show BASE:tests/auto/gui/qvulkan/tst_qvulkan.cpp`).
- **Symptom:** `qt-cmake-standalone-test tests/auto/gui/qvulkan` stops at configure with `Qt6QmlTypeRegistrarPrivateTargets.cmake ... but not all the files it references`.
  **Cause:** the template loads every module's standalone-test configuration, and Qt Quick's names tools the image does not have.
  **Fix:** in the test container only, lay an empty file over `cmake/Qt6BuildInternals/StandaloneTests/QtDeclarativeTestsConfig.cmake`; the gui tests do not need it.

## Two views asked, one given

Learned on ORDER 574 (qt6-base +stereo3d22, o574-0001).
A window asks for two views of its surface when it asks for stereo buffers itself or while an engine draws the depth of its elements; where the driver gives one view the window is shown flat.
Until +stereo3d21 that was a line in the program's log on the Vulkan path and nothing on the OpenGL path.

**What the person sees now.** One problem in the edition's problems engine (sparky-stereo-problems), package `libqt6waylandclient6`, for the driver that gives one view, because a driver that cannot give a second view gives none to any program:

| Key | Message | When |
|---|---|---|
| `one-view:vulkan:DEVICE` (the physical device's name, as `vkGetPhysicalDeviceProperties` gives it) | `LOCAL2`: the program, the device | a Vulkan swapchain got one image layer where two were asked |
| `one-view:opengl:VENDOR` (`EGL_VENDOR`) | `LOCAL3`: the program, the vendor | the EGL has no `EGL_EXT_multiview_window` |
| `one-view:opengl:zink` | `LOCAL4`: the program | zink was asked for by name without `LIBGL_KOPPER_DISABLE=1`, so its own swapchain shows one view |

`LOCAL1` ("A window is shown flat") is the title; the ten languages are in the package's catalog.
The first program that met the driver is named; a later program on the same driver finds the problem kept and leaves it as it is (the engine's `ssp_list_json` read first), so the person is not told again; a window that gets its two views from the same driver ends it (`ssp_clear`), and a later failure is a new problem naming its own program.
Nothing is said when the pair works, when the window never asked, or where the compositor takes no such pair (no `kde_stereo_content_manager_v1` version 3).

**Where it is decided.** In the platform, which knows what was asked and what the surface has: `QWaylandVulkanWindow::setSurfaceViews()` (the swapchain's maker says the device first, `_q_stereo_surface_device`, then the views) and `QWaylandEglWindow` when it makes its surface or, at the start of a frame, when the request changed while the surface could not. Both call `QWaylandStereoProblem` in the Wayland client library, which opens the engine's library at run time from the path the build gives (`-DQT_SPARKY_STEREO_PROBLEMS_LIBRARY=...`, empty upstream: there it stays a log line), and runs the engine's command where the library cannot be loaded, as [a library that tells the person](../../system-housekeeping/references/problems-from-a-library.md) says.

**Recipe.** In the rig, `PROBLEMS=1` lists `sparky-stereo-problems list --json` at each capture and after the program ends, in English and with `LC_ALL=pt_BR.UTF-8`:

- Vulkan, one view: NVIDIA's driver with `DISABLE_LAYER_MESA_STEREO=1` (the layer is the only thing giving NVIDIA a second view).
- OpenGL, one view: NVIDIA's own EGL (`__EGL_VENDOR_LIBRARY_FILENAMES=.../10_nvidia.json`), and zink without `LIBGL_KOPPER_DISABLE=1`.
- Controls: the pairs on every driver, and a window without depth (`QDISCS_FLAT=1`) on the faulty route: no problem.
- Told once and ended: several programs in one session ([`seq-session.sh`](../../stereo-proof-rig/scripts/vk-views/seq-session.sh), the programs in a folder mounted at `/bin-fx`): the first on the faulty route keeps the problem with generation 1, a second program and the first again leave it at generation 1 with the first program's name, a working pair ends it, a new failure keeps a new one.

Traps:

- **Symptom:** the list in Portuguese shows Portuguese titles and the English text.
  **Cause:** the package's catalog is not installed (a development library mounted over the installed one); the record's `text_en` is used.
  **Fix:** judge the languages from the installed package.
- **Symptom:** a Qt Quick window that asks for depth is flat on OpenGL and nothing is told, on every driver, in a new rig image.
  **Cause:** the rig had no KWin decoration plugin, so Qt drew its own frame, and that path is flat on OpenGL (and not one of the cases above: the driver gave two views). See stereo-proof-rig's lessons.

## Still to build

- **Qt Widgets on the Vulkan RHI** (`QT_WIDGETS_GPU_PAINT=batch` with `QT_WIDGETS_RHI_BACKEND=vulkan`) asks for two views the same way and gets them from the same code: one row on NVIDIA's driver gave the pair of the OpenGL RHI pixel for pixel (flat before). The other drivers, scales and Qt's own frame around such a window were not measured.
- **A window with Qt's own frame on OpenGL** (client-side decorations) asks for two views, gets them, and is drawn flat, and nothing tells it; the telling covers drivers that give one view, not this path of Qt.
- **X11.** Qt asks for no second view on xcb, so a Qt Quick window with depth is flat there and not told; a QVulkanWindow asking with its format gets two layers wherever the X11 surface offers them (Mesa's X11 presentation, the layer), not measured.
- **The layer on X11 without DRI3** refuses the two-view swapchain (`VK_ERROR_FEATURE_NOT_PRESENT`) and says so in the log only.
