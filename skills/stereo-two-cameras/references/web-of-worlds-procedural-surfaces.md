# Procedural surfaces and WebXR in a Web of Worlds demo

Use this recipe when a small 3D world needs the published Dynamic Procedural Texture Rendering player on its surfaces and the browser’s own two-view presentation.
The Key applies it to a fictional studio with a public lobby, a members’ entrance, and a time-limited mandate.
The scene and explanation are individual input to the PM-KR Community Group.
The group’s repository keeps such a page under `demos/NAME/` and links it from `demos/index.html`.

## Build and run

1. Read the procedure declaration and graph files in the [published Dynamic Procedural Texture Rendering demo](https://w3c-cg.github.io/pm-kr/demos/procedural-texture-rendering/).
   In the example’s glTF, the root `KHR_texture_procedural_rendering` object lists procedures and each texture refers to an entry.
   The P2P v1 text names operator nodes, earlier inputs, hexadecimal parameters and a final `out` node.
   The existing WebGPU path calls `parse`, `unknownParts` and `GpuPlayer.drawRgb` in `gpu-player.js`. This path needs WebGPU and the published WGSL operators.
2. For plain static hosting, start the published `wasm-worker.js` as a module worker. Send `{kind: 'init', url: 'player/ptr-player.wasm'}` and wait for `ready`. The fetch URL resolves from the worker.
   To draw, send `{kind: 'piece', id, script, exp}`. The response holds a transferable RGB array, dimensions `2 ** exp`, and operator time in milliseconds.
   An optional `win: {x, y, s}` describes a normalized texture window and defaults to the full area.
   Handle `error` and bound the wait. Generate each shared material once and release the worker after it finishes.
3. Expand each RGB pixel to RGBA with alpha 255. Create a [three.js DataTexture](https://threejs.org/docs/#DataTexture), mark its colour space as sRGB, and set `needsUpdate`.
   Assign it to the `map` of a standard three.js material. Use the glTF top-left UV convention with DataTexture's default `flipY: false`.
   Those bytes are the operator result. The application uses WebGL 2 to display the geometry and standard materials.
4. Keep the generated maps in a name-to-material table and load geometry with [GLTFLoader](https://threejs.org/docs/#GLTFLoader).
   Before drawing, verify that every mesh has UV coordinates and that every authored material name has a procedure.
   Serve the repository root over localhost for development or HTTPS for a hosted review. The static demo needs its sibling generator directory.
5. Render one perspective camera on an ordinary screen. Query `navigator.xr.isSessionSupported('immersive-vr')`, offer the button when available, and give the reason on the page when unavailable.
   In the button handler, request the session and hand it to `renderer.xr.setSession`. Use `renderer.setAnimationLoop` and the session’s `local-floor` space.
   Put locomotion on a parent of the camera. Three.js uses the browser’s view poses, matrices and viewports. Separation, eye order and display format belong to the browser and desktop.
   Restore the desktop camera on the session’s `end` event, and test the transition back to 2D.

## One companion step for Blender models

The SVG & 3D Design workflow supplies a reference, connected geometry, an editable source and an inspected render for each prop.
Keep the plain Blender material name when you export glTF.
Treat that name as the lookup key in the site’s procedure table.
Remove image nodes and references before exporting, then inspect the glTF payload for UVs, the names and an empty image and texture list.
Use the browser drawing to review the actual surface.
An opaque QR plaque can use a white mapped plate and instanced black mapped square modules, with the code’s quiet zone preserved. The same destination belongs in the plain link.

When using a free prop, open the author’s own page and the notice in the download.
Record the author, licence, revision, download address and SHA-256.
Check that the asset’s licence applies to the delivered file. A source project can include a library, sample maps, fonts, and models under different terms.
If the model used an atlas, give its surfaces suitable UVs before assigning a repeatable procedural map.
Keep the author’s original licence notice next to the adapted model.
See [reading an asset licence](reading-an-asset-marketplace-licence.md).

## Prove the result

- Run a known constant Ramp through the worker and through a mapped WebGL quad. Read back the source and the framebuffer. Check the exact RGBA values and check that a misspelled operator reports an error.
- Drive the actual keyboard, pointer and touch paths in a headless browser. A synthetic standard-mapped Gamepad sample can exercise the Gamepad API path. Keep that result tied to the injected sample.
- For WebXR emulation, load the test runtime before the application and enable stereo in the test fixture. Request the real application button action and read both viewports synchronously after the XR draw. Keep the per-eye matrices and images.
- Freeze the same scene state in that render callback, turn off XR for one render in the test, and render one camera with the captured left pose and projection. Matching viewport extent, sample count and colour settings allow an exact pixel comparison. Comparing the right eye to that 2D control must give a difference. Place no capture settings in the site.
- Pack and unpack the left-then-right pair losslessly with the registered `sTER` mode 1 in a `.pns`. Pad between the eyes to the next multiple of eight pixels if necessary.
- Decode a browser image of the QR plate with a reader such as ZBar and compare the decoded string to the link. Give the reader a blank image as its negative control.
- Record the real WebGL renderer for any frame timings. The fact that a graphics card is visible to the container does not prove the browser used it.
- Compare with the installed browser and compositor when the packaged rig can start. Two emulated views prove the application’s use of WebXR. For the compositor method, see [the WebGL and WebXR control](webgl-control-on-a-gpu-and-without.md).

## Traps

- **Symptom** The Ramp control’s red and blue channels are reversed in the assertion. **Cause** The control interpreted the packed word in reverse. **Fix** Expect red from bits 16–23, green from 8–15 and blue from 0–7. **How found** The published `ops/common.wgsl` unpacking and the worker and framebuffer returned the same bytes.
- **Symptom** Blender saves a source but the GLB is missing. **Cause** The minimal Debian Blender install omitted Python NumPy, which the glTF exporter imports. **Fix** Include `python3-numpy` and use Blender’s `--python-exit-code 1`. **How found** The exporter traceback named the missing import, while an ordinary background invocation still exited successfully.
- **Symptom** A download named ZIP is an HTML page. **Cause** The asset site redirected an old direct download to the catalogue page. **Fix** Check the signature and use the author’s current download route or a different open asset from its author. **How found** The downloaded bytes began with the HTML doctype instead of the ZIP signature.
- **Symptom** The test cannot walk through a hall on software renderers within the expected travel time. **Cause** A small maximum frame delta discarded most elapsed time, and unnecessary per-fragment lights raised the frame cost. **Fix** Render the current room, keep the lights needed by the scene, and subdivide the bounded movement delta for collision checks. **How found** The same key was held for 14 seconds and the recorded avatar position advanced under half the expected distance.
- **Symptom** An emulated headset exists in the fixture but the page still reports no immersive display. **Cause** Chromium offered a native XR API with no device, so IWER 2.8 left it in place. **Fix** Use the pinned emulator’s `installRuntime({forceInstall: true})` only in the test fixture. **How found** The emulator’s startup check returned before installing the simulated runtime.
- **Symptom** Browser automation cannot click the page’s Exit 3D button during emulation. **Cause** IWER puts the canvas in an immersive overlay which catches the pointer. **Fix** End the emulated session through the runtime and check the app’s return to 2D. **How found** The click log identifies the emulator’s canvas as the intercepting element.
- **Symptom** The screenshot shows a QR plate but a reader cannot reliably scan it. **Cause** A carried object or HUD element crosses multiple modules, or the camera cuts off the quiet zone. **Fix** Keep the plate clear in the inspection view and check the whole screenshot with a decoder. **How found** The close view exposed the keyring crossing the code.
- **Symptom** Chromium cannot create WebGL 2 with software rasterization disabled, yet the NVIDIA card is visible. **Cause** The browser image lacked the GLVND EGL loader. **Fix** Install `libegl1` and `libgles2` in the container before adding the CDI device, pass the NVIDIA render node’s group, and use full Chromium headless with `--enable-gpu --use-gl=angle --use-angle=gl-egl`. Verify the renderer name with `WEBGL_debug_renderer_info`. **How found** The container's library list contained `libEGL_nvidia.so.0` and no `libEGL.so.1`. With the loader available, the EGL backend reported the GeForce RTX 3060 and the OpenGL ES driver.
- **Symptom** A pair opens as PNG but a parser finds no `sTER` chunk. **Cause** The PNG library discarded the requested ancillary chunk on save. **Fix** Encode mode 1 with its own length, type and CRC directly after IHDR, then reopen and compare the two cropped eyes. **How found** The first stage check decoded both eyes but found an empty `sTER` list.
- **Symptom** The attached browser runner stops streaming during a long walk, with incomplete console output. **Cause** The Docker attachment has ended while the container still owns the running test. **Fix** Start the named container detached, poll its recorded state with a deadline, and read its logs and exit code after it finishes. **How found** The container had exited zero and the timestamped JSON contained results recorded after the attachment’s last line.

## The edition's browser on a virtual output

Use the signed published round as the rig's APT source and start the installed `kwin_wayland --virtual` in a new D-Bus session with a short `XDG_RUNTIME_DIR`. Start Waterfox's Stereo Browser on that Wayland socket with a disposable profile and a local HTTP server. Install the matching Qt Wayland shell integration for `kscreen-doctor`. Give KWin the NVIDIA render node through CDI and its render group. Select the virtual side-by-side twin using KScreen and run a fresh 2D output as a control. Keep the browser's ordinary WebGL stereo route at its default for the before and after captures.

Enter immersive WebXR with the rig's Wayland fake pointer. The published flat device granted `viewer`, `local` and `local-floor`. An injected rejection of required `local-floor` returned to the page with the reason. Record the session projection, view matrices, per-eye viewport and compositor limits. `kde_stereo_content_v1.set_content(3)` in the Wayland trace identifies the full side-by-side declaration. Capture with ScreenShot2 and use the registered `sTER` mark when retaining a pair.

For a point in the scene, multiply its world position by each eye's view and projection and divide by clip W. Convert NDC to the supplied viewport and then to the eye rectangle in the capture. Calculate right minus left in pixels before measuring marker centroids. Measure the near prop at the pose where it is visible. Use swapped eyes and an ordinary 2D output as controls. Inspect the rig's `depth_limits` event. Check fixed scene points and camera-relative interface elements separately. The browser derives its flat presentation plane from depth samples, so moving an object can also change the next measured plane. Keep each trial's matrices with its screenshot and give the estimate time to settle.

The three.js WebXR manager mutates the desktop camera's lens fields while rendering a session. Save position, quaternion, field of view, clipping range and zoom before entering. Restore these on exit and resize the desktop renderer from its canvas area. For a fixed pose, compare the same visible region before entering and after Escape. Record the immersive projection separately. The published Waterfox flat device supplies its own field of view through `XRSession::GetWindowViews`. Derive vertical degrees as `2 × atan(1 / projection[5])`. With full-size viewports and no overscan, a narrow projection covers only a fraction of the normal scene. Keep the view as supplied and report the framing to the browser project.

## Adapting a kit to the scene

Find an open kit at its author's page and read the included original licence. Keep the licence and pin the source archive by SHA-256. The Key uses Kenney Vleugels's Modular Space Kit and Kay Lousberg's Space Base Bits and Adventurers kits. The original atlas can identify material regions in Blender. Sample it while labelling faces and create UVs in each face's dominant plane. Then export only the named surfaces and UVs. Compose repeated architecture as instanced meshes, and put separate rooms at separate locations so the browser can hide the rooms the player is outside. For the static helper, pose the supplied skinned model and export the evaluated mesh.

Game Studio appeared in the local catalogue as uninstalled. Its public [Three WebGL Game recipe](https://github.com/openai/plugins/blob/main/plugins/game-studio/skills/three-webgl-game/SKILL.md) gave enough guidance to use the three.js core, loaders and an isolated browser proof. Install the SVG & 3D Design plugin only when the workflow calls for it.

## Additional traps

- **Symptom** KWin aborts at `wayland-org.kde.kwin.qpa` before creating a Wayland socket. **Cause** The built-in Qt platform plugin recognizes the basename `kwin_wayland`. **Fix** Preserve that basename when copying the binary into the rig. **How found** The signed published build reproduces the abort under `kwin-wayland` and opens the socket under `kwin_wayland`.
- **Symptom** KWin has a socket but `kscreen-doctor` reports missing `xdg-shell` and cannot start. **Cause** The minimal package list omitted the Qt Wayland shell integration. **Fix** Install the matching integration and use the Wayland Qt platform. **How found** The Qt diagnostic lists the missing shell; the installed plugin list then contains `libxdg-shell.so`.
- **Symptom** WebXR reports an active session but ScreenShot2 replies that the screenshot was cancelled. **Cause** The virtual compositor has no render node. **Fix** Run the installed compositor on the isolated NVIDIA CDI path with its render group. **How found** KWin logged missing render nodes and failed output layer configuration. The CDI control produced both captured views.
- **Symptom** A kit imports but the material colour lookup has no pixels. **Cause** The glTF names an external atlas and the extraction lost its relative path. **Fix** Extract the atlas at the original relative path for adaptation and omit it from the export. **How found** The Blender exporter reached a zero-byte pixel array while sampling the atlas.
- **Symptom** A kit wall looks flat when its file has moulded wall details. **Cause** The assembled room showed the back of the mesh. **Fix** Check its bounds and face orientation in glTF units before repeating it. **How found** The kit coordinates put the detailed face at negative local Z. The first in-room capture showed the undecorated face.
- **Symptom** Ordinary rendering stays zoomed after ending the immersive session. **Cause** The page restored the pose but reused the lens fields updated by the XR manager. **Fix** Restore the recorded desktop lens fields and update the projection on resize. **How found** The station's same-pose before and after projection matrices differed and the cropped compositor pictures showed the changed view.
- **Symptom** The compositor test exits before running its script and prints `sh: 0: cannot open bash`. **Cause** A committed image inherited the package install container's shell entry point. **Fix** Set the entry point for every runtime case explicitly. **How found** The same script launched when the runtime container selected Bash directly.
- **Symptom** A key-cycle row reads the previous selection just after its key event. **Cause** The input changes story state synchronously and the inventory is repainted on the next frame. **Fix** Wait for the selected item's visible state after each input. **How found** Reading immediately failed under SwiftShader and the event was visible on the next frame.
- **Symptom** A terminal ends while the isolated proof is writing files. **Cause** The terminal lifetime is shorter than the complete cold proof. **Fix** Save each finished container's exit status, then resume verified stages against the same staged checksum. **How found** The runner stopped after ten minutes and the last test container had exited zero with all claim rows present.
