# A C# OpenGL engine (Silk.NET, GLFW) handing Stereo KWin two eyes

Learned on Amoebius, Froglet Games' own C# engine inside Cosmic Shore (MIT, .NET 10, OpenGL 3.3 core on Silk.NET 2.22 with its bundled GLFW 3.4.0), at `bleeding-edge` 33a3e43ed (2026-10-28), on Debian testing in a container, Stereo KWin +stereo3d54, libstereo-declare 1.8.0, the RTX 3060 (driver 615.71.09) and the AMD iGPU (Mesa 26.1.6, which gives a 4.6 core context for the 3.3 request).
The ORDER was 494b; the engine's repository is froglet-studio/Cosmic-Shore (`Port/`), and the change is a branch of ours, offered back to its authors and shipped by nobody until they say.
The pattern is the one for any engine that draws its own frames: two cameras of one world, each eye drawn at its own resolution into its own half of one window, the window declared once as full side by side.

## The recipe

1. **Build it in a container, from Froglet's own SDK image.** `mcr.microsoft.com/dotnet/sdk:10.0` (Ubuntu 24.04, SDK 10.0.402), pulled by digest; `dotnet build src/CosmicShore.Player -c Release` as your user with `HOME` and `NUGET_PACKAGES` in scratch; NuGet's restore is the only network use.
   The game's scripts are compiled against the engine by the player's own build (about a minute); nothing runs on the host.
2. **Run it in the proof rig.** The rig image plus the .NET runtime copied from the SDK image (`COPY --from=<sdk digest> /usr/share/dotnet`, with `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1` set because the rig image has no ICU; not tried without), Stereo KWin on its virtual output with Xwayland, the player run as the lane user in that container.
   The player's own control port (`--control-port N`, JSON over HTTP on loopback) drives the menus: `do click X,Y`, `do type TEXT`, `wait N`, `screenshot PATH`, `state`.
3. **The pair.** In the engine's `Camera` (Unity's contract, so game scripts compile unchanged): `stereoSeparation`, `stereoConvergence`, `GetStereoViewMatrix(eye)`, `GetStereoProjectionMatrix(eye)`.
   Eye offset `x_e = -+ separation / 2` along the camera's right axis; view `T(-x_e, 0, 0) * V`; projection `P` with `P.m02 -= x_e * P.m00 / convergence` (a frustum window slid by `-x_e / C` in tangent units, so the plane `C` shows the same rectangle in both eyes).
   A point at depth `Z` lands `m00 * separation * (1 / C - 1 / Z)` apart in normalised x (right eye minus left, positive behind the plane); infinity sinks `separation * m00 / C`.
   A `RenderEye(eye, draw)` that makes every matrix the camera answers with the eye's for one draw keeps the renderer, the sky pass and every script that reads `camera.projectionMatrix` unchanged.
4. **Per eye, in the frame:** the camera's draw (the sky pass uses a rotation-only view, so the eye's sideways offset drops out and infinity gets the projection's shift alone, which is what infinity must have), the post stack, the UI.
   Lighting, fog and the sort order take the eye's position. State that belongs to the world (an environment probe updated once a frame) updates once, with the first eye.
   A post effect about the optical axis needs the axis: the Panini projection took `v.x += cx` and `src.x -= cx` with `cx = P.m02 / P.m00` of the eye (zero for a mono camera, so the 2D picture is the same bits).
5. **One frame, two halves.** Each eye is rendered into the same off-screen targets one after the other (no history between eyes) at its own resolution, then drawn into the window's default framebuffer with the viewport's x at 0 and at one eye's width (`glViewport(x, 0, w, h)`); the UI is drawn once per eye at the screen (zero parallax) and `Screen.width` is one eye's width, so the game lays its UI out for one eye.
6. **The declaration.** Create the window invisible, take its X11 handles from Silk (`window.Native.X11`: `Display`, `Window`), `stereo_declare_x11(display, window, STEREO_SBS_FULL, STEREO_CLASS_GAME, STEREO_GAME_3D)` through a P/Invoke of `libstereo-declare.so.1`, then show it.
   Stereo KWin makes the declared X11 window twice the created width (window 1280x720 becomes 2560x720 in the X server): take the eye size from the window (`width / 2`) or from the option, and draw nothing until the window is at least twice an eye wide.
   An eye drawn at another resolution than the size it is shown at: create the window at the eye's resolution and call `stereo_declare_x11_one_view_size(display, window, shown_w, shown_h)`.
7. **The depth is the person's.** Read `_KDE_NET_WM_STEREO_DEPTH_LIMITS` on the window (declaration support version 10; `XGetWindowProperty`, format 32 comes back as an array of C `long`s, two values in 24.8 fixed point: sunk, popped, in the screen's pixels) and solve the separation so infinity sinks exactly the sunk limit: `separation = 2 C S_eye / (m00 W_eye)`, `S_eye = S * W_eye / W_shown`.
   Put the zero-parallax plane at what the person looks at (the vessel the chase camera follows, else the camera's own convergence).
   With no limits, the eyes are the same picture and the log says so; on a desktop with no declaration support, say so and stay 2D.
8. **The proof, from a scene made for it.** A probe scene with no game code (a camera at the origin, six flat-coloured cubes at known depths and directions on black, optionally the Panini projection in the camera's volume) and a checker that predicts each cube's silhouette centroid per eye from the closed form, without the engine's matrices, then compares the measured centroids (colour-weighted) of the player's own frame.

## Results (1280x720 per eye, plane 16, the person's limits 10 / 4 px)

| Case | Disparity error rms | Largest | Vertical difference from the prediction rms |
| --- | --- | --- | --- |
| Flat, RTX 3060 | 0.067 px | 0.102 px | 0.012 px |
| Limits 24 / 9.5 from `kwinrc` | 0.051 px | 0.083 px | 0.023 px |
| Panini 0.4, RTX 3060 and the AMD iGPU (the separation divided by the projection's widest scale) | 0.135 px (both: the measured centroids are equal to two decimals; the frames differ in 240 pixels by at most 3 of 255) | 0.196 px | 0.016 px |
| Eye 960x540 shown at 1280x720 | 0.140 px | 0.216 px | 0.011 px |

With Panini the farthest cube at the side is 9.99 px apart for a limit of 10, and the real game's far world 9.4 to 9.9 px (the interface regions 0.00 to 0.04 px). Controls that fail as they must: the halves swapped 23.0 px rms, the limit read as 24 on a 10 capture 16.1 px, the plane read as 30 instead of 16 14.1 px.
The 2D control is the stock engine at the branch's parent, the same scripted run: 0 differing pixels in two scenes.
Unit tests of the matrices against the closed form turn red under four mutations (the shift's sign, no shift, no eye translation, the eyes swapped).

## Traps: the symptom, the cause, the fix, how it was found

- **Symptom:** Froglet's newest commit does not build: `CS0246 SpherecastCommand could not be found` (3 errors).
  **Cause:** the game's scripts moved ahead of the engine's API, and Froglet's own parity workflow had no green run in its last 200. After a shim for those two types there were 59 errors: the compiler stops at declaration errors (CS0246) before it binds method bodies, so "3 errors" hid the rest.
  **Fix:** bisect first-parent commits with the container build and the error count. 33a3e43ed (2026-10-28) compiles with 0; the next commits that were tried fail on an `override` that changes an access modifier.
  **How found:** `gh run list --workflow amoebius-parity-ci.yml` for Froglet's state, then the bisection; the error count is not monotonic, so it is a different error each time, not progress.
- **Symptom:** with `--stereo` on a Wayland session the player says its window is not an X11 window and stays 2D (`stereo 0` in ScreenShot2's capture); the same command in a shell with `WAYLAND_DISPLAY` empty works.
  **Cause:** Silk's bundled GLFW 3.4.0 has both platforms and picks Wayland when it can; the declaration and the depth limits property are an X11 window's. `GlfwProvider.GLFW` starts GLFW on its first use, so a `glfwInitHint(GLFW_PLATFORM, GLFW_PLATFORM_X11)` through it comes too late and does nothing.
  **Fix:** `GlfwProvider.UninitializedGLFW.Value.InitHint((InitHint)0x00050003, 0x00060004)` before the first window. **How found:** the player's own sentence (it says why it stays 2D), then the constants in GLFW 3.4's header and a run with `WAYLAND_DISPLAY` set in the rig, before and after.
- **Symptom:** Froglet's script for the vendor's native audio library fails with `FileNotFoundError: 'git'`.
  **Cause:** it runs `git remote get-url` to find the LFS endpoint, and the rig image has no git. **Fix:** a 20-line standard-library script of your own that takes the repository URL and the pointer file, asks the LFS batch endpoint, and keeps the object only when its SHA-256 and size equal the pointer's (the pointer is data). **How found:** the traceback.
- **Symptom:** the far world of a real scene is 13 to 14 px apart between the eyes against a sunk limit of 10 px, while the probe scene without post effects met it.
  **Cause:** a lens in the post stack (the Panini projection) moves each eye's image on the screen by its own local scale, about `1 / crop` in the middle and more at the sides, so a limit in screen pixels is exceeded wherever the scale is above 1. **Fix:** differentiate the effect's mapping over the frame (`PostPass.PaniniParallaxScale`) and divide the separation by its widest value: the limit is then met at the sides and never exceeded (the probe with Panini: 9.99 px at the side for 10). **How found:** a block match of the real scene's two eyes (UI regions 0.00 to 0.02 px, the world +13.3 to +13.9 px) against the limit; the first probe with Panini had agreed with its prediction at 11.3 px for the farthest cube, because the prediction had no limit in it; a check of the limit itself (the largest uncrossed disparity against the sunk limit) is part of the checker now.
- **Symptom:** a measurement of a flat-coloured cube is 1 to 2 px off in y in both eyes and in 2D.
  **Cause:** not found (it grows with the vertical tangent, 1.8 px at tangent 0.2 on a 720 px frame, and the stock engine draws the same frame). **Fix:** compare the eyes' difference with the prediction's difference, never an eye's position with the prediction's. **How found:** the same probe in the 2D player.
- **Symptom:** the game's first screen is a birth-year prompt, then a data-collection consent, then a pilot name, and no scene is reached.
  **Cause:** a fresh profile. **Fix:** a throwaway profile in the lane's own home folder, driven through the control port (`do click`, `do type`); answer the consent with "No thanks", the run is offline anyway. The profile is kept, so every later run starts at the menu. **How found:** the first screenshot.
- **Symptom:** a scene entered with `--scene NAME` shows a grey metal plate and none of the game.
  **Cause:** the scene is entered without the bootstrap chain (the game logs `AppManager ... not found at injection time`). **Fix:** go through the menu: the control port's `do arcade Bloomrush`, then `do arcade start`; wait for the scene named in `state`. **How found:** the first screenshots of three scenes.

## Perks

- A game scene and a probe scene both belong in the proof: the probe measures the geometry, the game scene shows that the UI, the post stack and the sky still stand together.
- The control port makes a scripted tour of the menus cheap; its `screenshot` is the player's own frame, so the half-and-half picture is the one the compositor gets, and ScreenShot2's capture of the output shows what KWin made of it (`stereo 1` for a declared window, `stereo 0` for the 2D control).
- NVIDIA's OpenGL 3.3 through Xwayland's GLX and Mesa's radeonsi (which gives a 4.6 core context for the 3.3 request) drew the same pixels to two decimals.
