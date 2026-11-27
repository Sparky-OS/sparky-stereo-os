# A web world the person composes: splat people, a held tablet, services from several origins, real keys

Started in ORDER 949 (November 2026) on The Key (w3c-cg/pm-kr `demos/the-key/`, after [the procedural surfaces page](web-of-worlds-procedural-surfaces.md)).
It shows, in today's browsers and on the edition, what a "spatial browser" is said to need: people in the world, an old-internet window held as a thing, services from many origins composed by the visitor, and keys from today's internet.

## Working recipe

1. **People as Gaussian splats in the world's own WebGL.** Read Dave Raggett's `SPLT` and `ANIM` files with his `splat-format.js` (its header specifies both layouts). Put positions in an RGBA32F texture and normal, colour, bone indices and weights in an RGBA32UI texture (2048 wide), and the skin matrices of each person in a small float texture (4 texels per bone). Draw instanced quads with a `RawShaderMaterial` (GLSL 3): skin each splat in the vertex shader (`A = Σ w_k S_k`), build the disk covariance `σu² L Lᵀ + (σn² − σu²)(Ln)(Ln)ᵀ`, project it with the Jacobian `J = [fx/−z, 0, fx·x/z²; 0, fy/−z, fy·y/z²]` (three.js looks down −z), add 0.3 px², and size the quad at 3√λ along the eigenvectors. Sort each person back to front on the processor once per frame with a 16-bit counting sort on the dominant bone's position; one sort serves both WebXR eyes. Levels of detail are prefixes of one fixed shuffle, with σ scaled by √(N/n) so coverage holds. The splats share the world's depth buffer and both eyes, which a separate WebGPU canvas cannot.
2. **Behaviour, not baked motion.** A fixed 1/30 s step and a seeded generator (`mulberry32`) make every proof pose repeat: `?seed=949&simTime=20&freeze=1` gives the same people in Chromium and Gecko. Walk clips are held in place (the root's horizontal position kept at rest) and turned back to the rest heading (the root's yaw about the display up), then the figure is moved and turned by the steering; clip time runs at `speed / clipSpeed`, where the clip's own speed is measured from its hips.
3. **The held tablet.** Size it as the specification does (8 or 12 inches diagonal, 16:10, or wall-sized). In 2D hold it low in the camera's frame; in an immersive session put it at the browser's own zero-parallax plane, read every frame from the two eye matrices: `z0 = |P00 · b / (P02,right − P02,left)|` with `b` the distance between the eye cameras. Full screen binds a view of the tablet with navigation none (an orthographic camera filling the viewport in 2D, a head-locked plane at `z0` filling the browser's field in WebXR) and unbinding returns the camera matrix unchanged.
4. **The tablet's routes, each the person's choice.** The browser's picker (`getDisplayMedia`, Screen Capture §5.1): a `VideoTexture`, picture only. A desktop window over VNC: noVNC's `RFB` into an off-page canvas, a `CanvasTexture`, clicks forwarded as synthetic `mousedown` and `mouseup` on noVNC's canvas at the mapped point, keys with `rfb.sendKey(getKeysym(e), getKeycode(e), down)` from a capture-phase listener while bound. A page placed over the view: three.js `CSS3DRenderer` with the iframe on the tablet's screen, 2D only.
5. **Services from several origins.** Each placed card becomes `<iframe sandbox="allow-scripts allow-same-origin" src="https://SERVICE/service.html">` (allow-same-origin keeps the service's own origin; it is still cross-origin to the world). On `load`, post `{type: 'connect'}` with a `MessageChannel` port to that exact origin; the service answers with what to draw, as data. The world draws it, loads its pictures with `crossOrigin = 'anonymous'`, shows an empty box with the name at a distance and the dense form near, sends the person's place or the people only when the person allows, and links two services by giving each a port of one new channel.
6. **Real keys on a local origin set.** One Node process serves every `.test` host (RFC 6761) by its Host header over HTTPS from a throwaway CA: OAuth 2.0 code flow with PKCE S256 in a popup that redirects to a same-origin callback which posts the code to its opener; OpenID Connect with an ES256 ID token verified in the page with `crypto.subtle`; WebAuthn with the server checking CBOR attestation, COSE keys and DER signatures; a second port with `requestCert: true` for the TLS client certificate.
7. **The rig.** Mount one hosts file at `/etc/hosts` for both browsers (`--network none`). Chromium: the full binary (`channel: 'chromium'`), the CA in `$HOME/.pki/nssdb`, the client certificate with `pk12util` and `AutoSelectCertificateForUrls` in both `/etc/chromium/policies/managed/` and `/etc/opt/chrome_for_testing/policies/managed/`, WebAuthn through CDP (`WebAuthn.enable`, `addVirtualAuthenticator`). The Stereo Browser: the CA and client certificate in the profile's `cert9.db` with `certutil` and `pk12util`, `security.default_personal_cert` set to "Select Automatically", WebAuthn through Marionette's `WebAuthn:AddVirtualAuthenticator`, the processes from the chrome context.
8. **Live rows with a full browser.** Read the deployed page through an egress guard container that resolves only the demo's own name to its server and every other site to its public address; give the browser container `--network container:GUARD` and `--proxy-server` to the guard. Full Chromium headed needs a display: `xvfb-run -n 6 -s '-screen 0 1920x1080x24' node run.mjs` with `headless: false` and `DISPLAY=:6`. Keep the rows read-only (`GET`, `HEAD`, `OPTIONS` only, service workers blocked). The headless shell is not the visitor's browser: run every conformance row in the full binary too.
9. **A world on any screen, at its own scale.** The scene's container is `position: fixed` at `100dvw` by `100dvh` (with `100vw`, `100vh` before them for older engines), the page itself does not scroll, and the viewport meta carries `viewport-fit=cover` so the scene reaches under a notch while every control is placed inside `env(safe-area-inset-*)`. The camera keeps one focal length in CSS pixels per device, taken from the long side of `screen` (`f = long / 2 / tan(48°)`, `fov = 2·atan(h / 2f)`, `aspect = w / h` on every resize), so the address bar, a rotation or a resized window show more or less of the world and never zoom it. Draw at `devicePixelRatio` up to the pixel count of a 1920x1080 frame (`min(dpr, max(1, √(1920·1080 / (w·h))))`); above it the browser scales the picture uniformly.
10. **Touch, by capability and orientation, bound to the same actions.** `matchMedia('(pointer: coarse)')` (the primary pointer) with `(orientation: landscape)` chooses the layout, never the browser's name: a touch-first device held sideways gets a stick (walk), a drag on the scene (look), Action and inventory buttons, with the text out of the way; held upright it keeps the text; a mouse-first device that receives a `pointerdown` of type `touch` keeps its text and gains the stick. Keys, the touch controls, a standard gamepad and an immersive session's controllers call one set of actions (walk, look, Action, open the inventory, choose in it).
11. **A menu in the world, for both eyes.** The inventory is an object of the scene (a selection wheel: items on a ring, a hub that names the highlighted item with a Use plate, a plate below with its mechanism and the hint for the device that opened it), drawn over the world (`depthTest: false`) but writing its depth, placed when it opens from the view that draws it: in 2D one metre in front of the camera, sized to the smaller side of the view; in an immersive session with a shared screen plane its items on that plane and its backing 15 % of the distance behind it; in a headset 1.3 m away. It stays where it opened. Choosing: hover and click, a tap, Q and E then F, a gamepad's stick by direction then A, a controller's ray then the trigger; Q and E outside it still change the item in hand at once and show the wheel for a moment.

## Measured in this work (Chromium 159, Stereo Browser 6.7.5-0+stereo3d16 on Stereo KWin +stereo3d64)

- A cross-origin picture without CORS is shown in a page, but `texImage2D` throws `SecurityError` (WebGL "Origin Restrictions"), `copyExternalImageToTexture` throws `SecurityError` (WebGPU §3.9), and a 2D canvas becomes unreadable; with CORS both upload the exact texel. Same in both engines, WebGPU included (Gecko with `dom.webgpu.enabled`, `gfx.webgpu.ignore-blocklist`, `gfx.webgpu.force-enabled`).
- `postMessage` transfers a 1 MiB `ArrayBuffer`, an `ImageBitmap`, a `MessagePort` and an `OffscreenCanvas` (the sender's copy detaches; see the trap on row B6 for what full Chromium does when the other site draws into it), clones `Map`, `Date`, `Blob` and typed arrays, and refuses a function with `DataCloneError`.
- Each service frame is an out-of-process frame of its own site in Chromium (CDP `iframe` targets) and a `webIsolated=` process of its own in Gecko (Fission).
- In the Stereo Browser's flat WebXR mode the eyes were 7.6 mm apart with zero parallax near 2.2 m: −11.7 px at 1 m, −0.9 px at 2 m, +8.0 px at 12 m on a 1920-wide eye. A head-locked object at 1 m pops past a popped limit of 4 px; at `z0` it measured 0 px.

## Traps, symptom first

- **Symptom:** a conformance page completes every row in Chromium's headless shell, but in full Chromium (headed or headless, GPU or software) the driver reports `Page crashed` (CDP `Target.targetCrashed`, `"status":"killed"`) at the same row, and every later row is missing. **Cause (measured, Chromium 159.0.8154.6):** the request is valid (HTML §2.7 lists `OffscreenCanvas` as transferable) and the tab does not end. With site isolation, a frame of another site that calls `getContext()` and draws on an `OffscreenCanvas` transferred from the embedder makes the browser log `Terminating render process for bad Mojo message: Received bad user message: Invalid client ID` and end **that frame's process**, a few milliseconds after the frame has answered; the process also holds every other frame of that site, so the later rows, which post to the same frame, time out. Playwright takes the end of a frame's process for the page's and refuses every further call. One value at a time, a fresh browser each: `ArrayBuffer`, `ImageBitmap`, `MessagePort`, `Map`, `Date`, `Blob` and `Float32Array` all arrive; an `OffscreenCanvas` the other site does not draw on arrives; one it draws on ends that frame in 5 of 6 runs; the same draw from a frame of the page's own site never does; the headless shell (no site isolation) and Gecko (which reports `messageerror`) do not. **Fix:** run that row last, then ask the frame whether it still answers and report the browser's end of the frame as the row's measured result; in the driver, once the page is flagged, read it through the browser's own CDP session (`Target.attachToTarget` with `flatten: false`, then `Target.sendMessageToTarget` with `Runtime.evaluate`), which still answers. **Found by:** `KC_MEASURE_DIAGNOSE=1` (the browser's log has the bad-message line a few milliseconds before the flag), then the same values posted one at a time, then the page asked over raw CDP: `Target.getTargets` listed the page target alive and an iframe target with an empty URL.
- **Symptom:** a test page given to the browser with `route.fulfill()` cannot load its cross-site frame: `net::ERR_BLOCKED_BY_LOCAL_NETWORK_ACCESS_CHECKS`. **Cause:** a fulfilled document has no address space, so the browser treats its request to a loopback-resolved site as a public page reaching the local network. **Fix:** put the test page on the bench server's own document root (`docker cp`), not in a route.
- **Symptom:** the first message to a frame is lost though the frame's `load` fired. **Cause:** the frame's module script has not run yet. **Fix:** wait a moment, or have the frame announce itself.
- **Symptom:** every service frame shares the page's renderer; `Page.getFrameTree` says `NotIsolatedFeatureDisabled`. **Cause:** Playwright's default headless Chromium is the headless shell, which runs without site isolation. **Fix:** `chromium.launch({ channel: 'chromium' })`, the full binary in new headless mode. **Found by:** one renderer in `SystemInfo.getProcessInfo` with four services placed.
- **Symptom:** `SystemInfo.getProcessInfo is only supported on the browser target`, and `Target.getTargets` lists no frames. **Cause:** a page-level CDP session. **Fix:** `browser.newBrowserCDPSession()`.
- **Symptom:** a WebAuthn `get()` ends at once with `NotAllowedError` after `create()` worked. **Cause:** Chromium's virtual environment had a second virtual authenticator without the credential. **Fix:** remove the other authenticator first. **Found by:** the same calls passing with only the platform authenticator present.
- **Symptom:** a red WebAuthn row (no authenticator) never returns. **Cause:** without `WebAuthn.enable` Chromium waits for a real authenticator past the request's timeout. **Fix:** enable the virtual environment with no authenticator for the red row.
- **Symptom:** a screenshot of the WebGL page on SwiftShader takes a minute or times out. **Fix:** stop the animation loop after one more frame (`setAnimationLoop(null)`), capture, start it again.
- **Symptom:** a figure skinned with a procedural texture is black. **Cause:** a texture marked sRGB is decoded to linear when sampled; decoding it again in the shader crushes dark procedures to black. **Fix:** use the sampled value as linear. **Found by:** the same shader with a plain bright test texture.
- **Symptom:** the page placed over the view disappears in full screen. **Cause:** a `CSS3DObject` removes its element from the page when the object leaves the scene, so the iframe cannot be moved elsewhere. **Fix:** a second frame of the same page for full screen.
- **Symptom:** after a click in the full-screen page, Escape and Action do nothing. **Cause:** keys typed into a cross-origin frame belong to that frame; the world cannot hear them. **Fix:** a visible "Back to the world" button outside the frame.
- **Symptom:** a click at a button inside the tilted overlay (perspective `matrix3d`, cross-origin, out-of-process) does not reach it, while text typed there arrives and the same click on the flat full-screen frame works. Cause not determined; recorded as a finding (Chromium 159).
- **Symptom:** `getDisplayMedia()` rejects with `NotReadableError: Could not start video source` in headless Chromium, and a headful Chromium on a bare Xvfb display dies with `BadAtom` on `X_GetProperty`. The picker route could not be proved in a container; the page says why.
- **Symptom:** the VNC picture of a Chromium window on Xvfb is white. **Cause:** with no window manager the window is treated as occluded and draws nothing. **Fix:** `--disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-features=CalculateNativeWinOcclusion`. Keys forwarded over VNC reach the page only when that window is active: a window manager does it; the rig uses `Page.bringToFront` and focus emulation on that window.
- **Symptom:** x11vnc exits with "Wayland sessions are as of now only supported via -rawfb". **Cause:** it saw `WAYLAND_DISPLAY` of the compositor session. **Fix:** `env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE x11vnc -display :5 …`.
- **Symptom:** two `.test` services on the same parent name share a process. **Cause:** a site is scheme plus registrable domain; ports and subdomains do not separate sites. **Fix:** a different registrable name per service (`floor-map.test`, `catalogue.test`).
- **Symptom:** marks in an immersive capture are not found. **Cause:** the browser's immersive field is 21.6° high (row 876); points beyond ±18.8° horizontally fall outside. **Fix:** compute each mark's pixel from the session's own matrices before placing the person.

## Licences to read before a figure ships

A free figure is not a free licence. CGTrader's Royalty Free licence (section 20.5) belongs only to whoever downloaded the model and cannot be transferred; 21A.2 and 21A.3 allow a game or a virtual world to carry it in its own format with extraction prevented. Renderpeople's terms (4.2 b, 4.3 b) forbid passing on the 3D data or data based on it, and making it available as individual files. Keep such a figure out of the repository and let the publisher download it under their own licence ([reading a marketplace's licence](reading-an-asset-marketplace-licence.md)).

## Publishing under an Apache path

1. Keep one machine-readable list of full base URLs for the world, authorization provider, archive, WebAuthn, member door, services and intranet.
   The rig can keep its reserved `.test` names.
   A service on a Pages project has a path as part of its base address.
   Use that path to resolve its page and assets, and use the URL's origin alone for `postMessage`.
   Use one site per service, all distinct from the world's site, when demonstrating process isolation.
2. Allow the world origin in each service's receiver, and require the sender to be its parent frame.
   Read the same address file next to each service module.
   Install the message listener synchronously and let the handler await the address.
   This works even when the world sends its first message from the iframe's load handler.
3. Put the OAuth and WebAuthn endpoints behind an HTTPS reverse proxy scoped to the demo path.
   Use the full authorization provider base URL in discovery and ID token issuer validation.
   Use the world's HTTPS origin as WebAuthn's expected origin and its hostname as the relying party ID.
   Serve the provider and the archive on loopback and test the exact Node version the host uses.
   The test service holds the signing key and grants in memory and has no real accounts.
4. Put the client-certificate door on an optional, dedicated Apache TLS listener.
   Request the test client certificate in that listener's handshake.
   Leave the site's existing TLS policy in place.
   When the listener is disabled, describe the local test rig on the key and its help page.
   Use the site's existing server certificate and a dedicated CA for the shared test client identity.
   Keep the CA signing key out of the release.
   Test both the no-certificate refusal and accepted identity with default browser TLS.
   Run `apache2ctl configtest` before reloading and verify that undo closes the listener. [Apache mod_ssl](https://httpd.apache.org/docs/2.4/mod/mod_ssl.html).
5. Build the static release from a clean checkout with its nested imports, WebAssembly worker and every procedure the world fetches.
   Generate the lobby QR from the configured world address.
   Check the release hashes before installation and run the world against the public path in the fixture before publication.
   Keep the browser evidence gathered from a loopback copy distinct from evidence gathered from an internet deployment.

### Figures that can ship

- Start from [the CC0 MakeHuman and MPFB core assets](https://www.makehumancommunity.org/about/license.html).
  The [system asset pack](https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html) supplies the clothes, hair, skin and eyes as well.
  Change age, body proportions, build and outfit on the fitted model, rather than changing just the colour in the renderer.
  Give the helper a single figure used only by that character and apply its approved material in the renderer.
- Install MPFB as a local Blender extension, using `blender --command extension build --source-dir SOURCE` and `blender --command extension install-file -r user_default -e PACKAGE.zip`.
  MPFB provides the assembled mesh and weights.
  Evaluate the fitted mesh and the outfit's masks before drawing triangle-area weighted samples.
  Interpolate normals, UVs and bone weights at each point, sample the diffuse texture, drop the transparent samples and quantize the four greatest weights to a sum of 255.
- Download the individual original BVH files from [Ian Mason’s 100STYLE page](https://www.ianxmason.com/100style/), checked against the [dataset record](https://zenodo.org/records/8127870) for credit and CC BY 4.0.
  Keep the first and last T-poses out of the playable loops.
  Convert the BVH rotation order in source space, change to the rig's axes, apply the rotation to each target bone's rest transform, and recover parent-relative transforms per frame.
  Retarget independently to each skeleton.
  Keep raw root travel for the gait speed estimate and remove horizontal travel at playback.
  Convert only the new figures and their motions to SPLT and ANIM for redistribution.

### Deployment traps

- **Symptom:** the message probe times out and a service never connects. **Cause:** top-level await on address fetching lets the iframe fire load before its listener exists. **Fix:** register the listener first and await configuration in the callback. **Found by:** the first transfer before the fix timed out; all 21 rig rows passed after it.
- **Symptom:** a client can load the world, but the initial texture says HTTP 404. **Cause:** the worker was present in the release and the texture catalogue still pointed to a sibling demo for its four shared procedures. **Fix:** stage those procedures with the published worker and resolve them under the same demo path. **Found by:** the world's normal browser boot, after the HTTP route smoke passed.
- **Symptom:** the installer exits, then undo says another deployment is running. **Cause:** a locally launched daemon inherited the advisory lock file descriptor. **Fix:** close it when invoking service starts and reloads. **Found by:** the real Apache fixture with a foreground container supervisor.
- **Symptom:** MPFB raises "The package does not name an extension" when imported from a source checkout. **Cause:** its user storage uses Blender's extension repository API. **Fix:** build and install the source as a local extension and load its package from the extension repository. **Found by:** Blender 4.5 background builds.
- **Symptom:** a path-level client certificate gets an HTTP error or a TLS alert. **Cause:** the path is known after the first TLS handshake. **Evidence:** Apache 2.4 on Bookworm accepted the same test identity over TLS 1.2 and TLS 1.3 with curl and refused the request without a certificate. Default Chromium and Gecko sessions refused the imported certificate on the TLS 1.3 path (Apache AH10158).
  In separate TLS 1.2 test profiles both accepted it, with Chromium's `--ssl-version-max=tls1.2` and Gecko's `security.tls.version.max=3`.
  Keep both rows and tell visitors about the browser requirement.
- **Symptom:** an ImageBitmap or OffscreenCanvas transfer fires `messageerror` in the other site's Gecko process. **Fix:** show the error and send camera frames as bytes in an ArrayBuffer over the existing MessagePort. **Found by:** the echo probe and the camera frame counter.
- **Symptom:** a loopback HTTPS world opens in Chromium while Gecko reports an insecure certificate. **Cause:** the fixture presented its self-signed CA as the server certificate. **Fix:** trust a test CA and give Apache a separate signed leaf with every fixture host in its SAN. **Found by:** the same world opening immediately in Gecko with the leaf and the trusted CA.

### Constraining the service drawings in flat WebXR

The flat device supplies parallel eye transforms and horizontally shifted perspective matrices.
The edition's compositor sends the depth limits to the browser.
In the tested build a page can read the eye matrices, and the compositor's numeric limits are available to the rig through the Wayland trace.

1. In the shared eye coordinates, compute the zero-disparity distance from the eye baseline and the two projection offsets.
   With horizontal focal coefficient `fx`, baseline `b`, and horizontal offsets `left` and `right`, the distance is `fx * b / (left - right)`.
   Check for equal eye orientations and view sizes, a horizontal baseline, and a finite plane in front of the eyes.
2. Project every service primitive onto that plane along the midpoint eye's viewing rays.
   Apply the same vertex transform to the shell, label, panels, feeds, path lines and markers.
   For these parallel eye transforms the projection preserves homogeneous clip W.
   Keep the original clip depth for room occlusion and ordering, and keep the declared positions for proximity and input.
   The zero-disparity plane holds all the drawn pixels inside any nonnegative sunk and popped limits.
3. Capture both eyes and compare surface probes and the projected bounds of every declared vertex against the compositor's actual announced limits.
   Keep measurements for the original placements.
   Where the device supplies no shared plane, tell the person that the service drawings are available in 2D.

The recorded service markers matched the browser's geometry while exceeding the popped limit before this change.
Moving the same panels farther in a second placement still exceeded the limit because the browser's eye transforms could change.
Constrain the drawings from the current session matrices and leave separation and the screen-plane setting with the display system.

### Sending a certificate during the first handshake

A member door that succeeds with a TLS 1.2 test profile and fails with Apache AH10158 in default browser profiles is requesting the certificate too late for those TLS 1.3 clients.
The dedicated virtual host on a separate port moves the certificate request to the handshake.
Its proxy sends the verified result to the application and the regular API strips those headers.
Credentialed cross-origin responses name the exact world origin.
The same restore proof verifies both virtual-host configurations and the optional port.
If the dedicated door handshakes successfully but answers HTTP 404, check the proxy destination path.
The Debian 12 fixture returned 404 when a literal destination was used with ProxyPassMatch.
An anchored door expression and its full match `$0` produced the expected upstream path and restored HTTP 200.

Read the eyes for the service and tablet placement in the same scene render hook, after three.js updates its XR camera.
Refresh the tablet subtrees after changing their transforms in that hook.
When the browser changed its projection during a capture, updating the tablet before that hook could put one frame's tablet at the prior frame's plane.
Keep the WebXR frame loop running while capturing the compositor's pair. Stopping the loop stopped valid immersive submissions and produced a damaged capture.
Read the predicted probe positions on either side of the capture and verify they stayed within half a pixel.

### Aligning captured arms to the fitted rig

The released 100STYLE BVH skeleton extends its arms along X in the unrotated pose.
The fitted MPFB game-engine rig lowers the upper arms and already bends the forearms.
Applying the capture's world rotation directly to those fitted bind orientations bent the arms a second time.

Read the BVH child offsets and wrist endpoints.
After converting them to the target basis, find the shortest rotation from each fitted arm segment to its source rest direction.
Apply that rotation to the fitted bind orientation before the captured world rotation.
Recover local rotations relative to the new parent pose as before.
This transports the fitted roll and keeps its bone lengths.
Apply MPFB's bilateral hand-scale and finger length and diameter targets to the individual fitted body before adding the game rig and clothes.
For a regression check, decode every exported clip and measure the posed segment against the captured segment at every sample.
Keep front walk and idle stills from the same sampling fraction and camera for each figure.

### Giving the crowd the hall layout

Calculate ground footprints from the installed props, furniture and door assemblies after updating their scene transforms.
Expand the rectangles by a person’s clearance and connect corners with visible straight segments.
Choose a route to the current goal, then steer each step against the footprints and nearby people.
Use the measured movement to blend the walking animation.
When an agent makes no progress for three quarters of a second, release its queue slot and select another reachable goal.
Measure stalled movement only while the agent has a destination, because serving, pausing and conversations intentionally stand still.
Record every visitor’s trajectory and check that the same seed and inputs reproduce the same positions and states.

## On a phone, by touch, and a menu in the world

Added in ORDER 949 Addendum 6 (November 2026), after Daniel tried the live world on his phone and his desktop: the viewport did not fill the screen and the world changed size with it, held sideways the text covered the scene with no touch controls, and the inventory was a bar pasted on the screen.

### The shared screen plane, signed

`z0 = fx · b / (P8,left − P8,right)`, with `b` the right eye's position along the left eye's x axis, both eyes of the same orientation and only shifted sideways.
A flat stereo display (the Stereo Browser's flat device) gives a positive distance: that is its screen plane.
A headset's mirrored frusta give a negative one: there is no shared screen plane, so a menu or panel takes a comfortable distance instead.
Taking the absolute value (as a first version of the tablet's placement did) reads a headset as if it had a plane.

### Measured in this work (Chromium 159 with touch emulation, IWER 2.8.0's Meta Quest 3, the Stereo Browser on Stereo KWin)

- A fixed vertical field (64°) on a 412x915 phone gave a focal length of 697.6 CSS px upright, 652.8 with the address bar shown and 409.7 sideways: the world zoomed by 1.7 times on rotation. With the focal length from the screen it is 411.9 px in all four states, and on a desktop 864.4 px for windows of 1920x1080, 1280x720 and 1600x900.
- A play area with `min-height: 32rem` was 512 px tall in a 412 px sideways phone, so its lower controls were off the screen and the page scrolled.
- Held sideways, the earlier page covered 10.7 % of the screen with text that was not a control's label; the new layout covers 0 % and shows the stick, Action and the inventory button.
- With safe areas of 47 px on each side and 21 px below, every control stays inside them and the scene still fills the screen.
- In the Stereo Browser's 3D session (its flat WebXR display on Stereo KWin's 3D output, a screen plane of 6.553 m from the session's own matrices) the menu's items and hub measured 0.0 px of disparity (predicted 0.0) and its backing, 15 % of the distance behind, +1.0 px (predicted +1.28), with no vertical disparity, inside a sunk limit of 10 and a popped limit of 4.
- In the same browser's 2D page on a 3D output the browser makes the pair with its own camera: an opaque world object 1 m ahead measured -30.0 px against a popped limit of 4, and the menu's items -30.5 px, transparent or opaque alike (-13.5 px in another scene). The menu takes the disparity of any world object at its distance; the page cannot place that camera's screen plane, so this is the browser's to bound, not the page's.

### Traps, symptom first

- **Symptom:** a page that keeps its focal length from `screen` still zooms in a test when the window is resized or the address bar is simulated. **Cause:** Playwright's `setViewportSize()` resizes the emulated `screen` with the window, which no phone or monitor does. **Fix:** set the window with CDP `Emulation.setDeviceMetricsOverride` and give `screenWidth` and `screenHeight` the device's own size (swapped on a rotation, unchanged for the address bar or a window resize). **Found by:** the rows' measurements showed `screen` equal to the window in every state.
- **Symptom:** a test of "a desktop with a touch screen" gets the phone's layout. **Cause:** a context with `hasTouch` makes Chromium report the primary pointer as coarse, and `Emulation.setEmulatedMedia` with a `pointer` feature does not change `matchMedia('(pointer: coarse)')`. **Fix:** a mouse-first context, and the touch injected with `Input.dispatchTouchEvent` (it still produces pointer events of type `touch`). **Found by:** the row's own `pointer: coarse` reading, true with the override in place.
- **Symptom:** a coloured mark placed on a menu in the world is not found in either eye. **Cause:** the menu's materials are transparent, and three.js draws every opaque object before every transparent one whatever their `renderOrder`, so the menu covered the opaque mark. **Fix:** make the mark transparent too and give it a higher `renderOrder`. **Found by:** both eyes' centroids empty at the predicted pixel while the same marks on opaque service panels were found.
- **Symptom:** after a new block of proof rows, older immersive rows fail one after another (a mark not found, Action not filling the view, the menu not opening). **Cause:** the new block put away the held tablet and never gave it back; the menu then rightly refused to open over the tablet's full screen. A row of the form `wait_for(...) and state` could not fail and hid the cascade. **Fix:** a block that changes shared state restores it and checks that it did; every row reads its state after the wait. **Found by:** reading the rows in order from the first red one.
- **Symptom:** coloured marks are found in an immersive capture but not in the same page's 2D capture. **Cause:** the page's own gradient overlay (an `::after` over the canvas) dims the canvas in the 2D page, and an immersive session draws without the page's HTML. **Fix:** in the 2D page compare with a tolerance and choose colours far from the page's palette, or measure in the immersive frame. **Found by:** the marks' median colour in the 2D capture, (197, 6, 200) for a magenta of (255, 0, 255).
- **Symptom:** a camera that places the screen plane from the depth buffer (the Stereo Browser's camera for a 2D page) could push a menu drawn over the world past the person's popped limit. **Cause:** a menu drawn with `depthWrite: false` is not in the depth buffer the camera reads. **Fix:** draw it with `depthTest: false` and `depthWrite: true`, so the camera counts it where it floats.
- **Symptom:** a headed Chromium phase whose container starts `xvfb-run` as its entry point hangs with an empty log, while the same command run from `bash -c` passes. **Fix:** `docker run --init`, so an init process is PID 1 and `xvfb-run` runs as its child; the phase then passed in 22 s. The probable cause, not traced: a shell script as PID 1 does not reap Chromium's orphaned helper processes (Puppeteer's documentation gives the same reason for `--init`).
- **Symptom:** a long proof script stops with `unexpected EOF while looking for matching '"'` after a phase that passed. **Cause:** the script was edited while it ran, and bash reads a script as it goes. **Fix:** never edit a running script; wait, or run the edited copy afterwards.
