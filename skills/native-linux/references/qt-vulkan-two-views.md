# Two views on Qt's Vulkan path

Learned on ORDER 556 (November 2026), on qt6-base 6.11.2+dfsg-5+stereo3d21, Qt Quick 6.11.2+dfsg-3+stereo3d3, Stereo KWin +stereo3d54 and Mesa 26.1.6-1+stereo3d21 with its Vulkan stereo layer.
Load it with [native-linux](../SKILL.md) when a Qt Quick window drawn once per eye is flat with `QSG_RHI_BACKEND=vulkan`, when a window that stopped showing depth is shown as two halves on NVIDIA's Vulkan driver, or when a change to Qt's Vulkan swapchain or to the Wayland Vulkan window needs its proof.

The result first: from qt6-base `6.11.2+dfsg-5+stereo3d21` a Qt Quick window whose style shows the depth of its elements is a declared pair with the Vulkan renderer too, on radv, on NVIDIA's Vulkan driver and on lavapipe, with the parallaxes of the OpenGL path to a thousandth of a pixel.
Before, such a window was flat on every driver: Qt gave a window its two views in the Wayland EGL window only.

## The chain

1. **The engine asks.** Qt Quick sets the window's `_q_stereo_views` to 2 while a style shows depth (`_q_stereo_depth`), and draws a pair as soon as the swapchain has a right target (`QRhiSwapChain::currentFrameRenderTarget(RightBuffer)` differs from the left one). Nothing in Qt Quick knows the backend.
2. **The platform answers.** `QWaylandVulkanWindow` keeps the request (an event filter on the window's dynamic property, an atomic read by the render thread) and wants two views when the window asked for stereo buffers itself or when the engine asks and the compositor takes such a pair (`kde_stereo_content_manager_v1` version 3, `QWaylandStereoDepth::isSupported`).
3. **Whoever makes the swapchain asks the platform.** `QRhiVulkan` reads the window's `_q_stereo_views` native resource (`QPlatformNativeInterface::nativeResourceForWindow`, a number, not a pointer) and makes the swapchain with `imageArrayLayers` 2 where the surface allows it: "imageArrayLayers must be greater than 0 and less than or equal to the maxImageArrayLayers member of the VkSurfaceCapabilitiesKHR structure" ([VUID-VkSwapchainCreateInfoKHR-imageArrayLayers-01275](https://registry.khronos.org/vulkan/specs/latest/man/html/VkSwapchainCreateInfoKHR.html)). On a platform that does not answer, the window's format decides, as in upstream Qt.
4. **It says what it got.** After `vkCreateSwapchainKHR` the swapchain tells the platform its views (`setWindowProperty(..., "_q_stereo_surface_views", n)`). The window then reports a stereo format and marks the pair as the desktop's own depth (`kde_stereo_depth_v1.set_desktop_depth(1)`), which takes effect with the driver's next commit.
5. **The swapchain follows at the start of a frame.** `QRhiVulkan::beginFrame` builds the swapchain again when the wanted number changed, and only when the frame acquires a new image: Qt Quick renders the left eye in a frame ended with `SkipPresent` and the right eye in the next, and the views must not change between the two.
6. **With one view again the surface is made again** (`QPlatformWindow::invalidateSurface()` after the swapchain is released), so that whatever declared the pair for the surface withdraws it. See the first trap.

No new virtual function was added to `QPlatformWindow`: other projects build their own platform windows against Qt's private headers, and a new virtual would shift their tables. The two existing native interface calls carry the question and the answer.

## What Stereo KWin takes from a Vulkan client

- **A swapchain with two image layers.** Mesa's Wayland presentation (radv, lavapipe and the other Mesa drivers) packs layer 0 and layer 1 full side by side into one buffer and sends `kde_stereo_content_v1.set_content(3)` before the first attach, on a queue of its own; it destroys that object with the swapchain.
- **Over a driver outside Mesa** (NVIDIA's), the Vulkan stereo layer (`VK_LAYER_MESA_stereo`, package `mesa-vulkan-layer-stereo`, an implicit layer) raises `maxImageArrayLayers` to 2, makes the driver's swapchain twice as wide and declares the surface the same way. It keeps its declaration until `vkDestroySurfaceKHR`.
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
  **Fix:** in Qt, with one view again the swapchain is released and the platform makes the surface again; the protocol log then shows `kde_stereo_content_v1.destroy()` at the change. The layer's own fix (withdraw when its last two-layer swapchain of a surface goes) is the piece to build in Mesa; with it Qt's step is harmless.
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

## Still to build

- **The Vulkan stereo layer** withdraws its declaration when the last two-layer swapchain of a surface is destroyed or replaced by a one-layer one (`stereo_DestroySwapchain` and `stereo_CreateSwapchain` in Mesa's `src/vulkan/stereo-layer/stereo_layer.c`); its test is a client that makes a two-layer swapchain, then a one-layer one on the same surface, and reads the protocol log for the `destroy`.
- **`QVulkanWindow`** builds a swapchain of its own with one layer (`QVulkanWindowPrivate::recreateSwapChain`) and gives its renderer one framebuffer per frame, so it has no way to draw an eye; a program with its own Vulkan code on a `QWindow` can already make two layers itself.
- **Telling the person** when a surface offers one layer only is a warning in the program's log today, once per window; the OpenGL path says nothing at all. Both belong in the edition's problems engine, as Mesa's GLX does for a pair it cannot keep.
- **Qt Widgets on the Vulkan RHI** (`QT_WIDGETS_GPU_PAINT=batch` with `QT_WIDGETS_RHI_BACKEND=vulkan`) asks for two views the same way and gets them from the same code: one row on NVIDIA's driver gave the pair of the OpenGL RHI pixel for pixel (flat before). The other drivers, scales and Qt's own frame around such a window were not measured.
