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

## Measured in this work (Chromium 159, Stereo Browser 6.7.5-0+stereo3d16 on Stereo KWin +stereo3d64)

- A cross-origin picture without CORS is shown in a page, but `texImage2D` throws `SecurityError` (WebGL "Origin Restrictions"), `copyExternalImageToTexture` throws `SecurityError` (WebGPU §3.9), and a 2D canvas becomes unreadable; with CORS both upload the exact texel. Same in both engines, WebGPU included (Gecko with `dom.webgpu.enabled`, `gfx.webgpu.ignore-blocklist`, `gfx.webgpu.force-enabled`).
- `postMessage` transfers a 1 MiB `ArrayBuffer`, an `ImageBitmap`, a `MessagePort` and an `OffscreenCanvas` (the sender's copy detaches), clones `Map`, `Date`, `Blob` and typed arrays, and refuses a function with `DataCloneError`.
- Each service frame is an out-of-process frame of its own site in Chromium (CDP `iframe` targets) and a `webIsolated=` process of its own in Gecko (Fission).
- In the Stereo Browser's flat WebXR mode the eyes were 7.6 mm apart with zero parallax near 2.2 m: −11.7 px at 1 m, −0.9 px at 2 m, +8.0 px at 12 m on a 1920-wide eye. A head-locked object at 1 m pops past a popped limit of 4 px; at `z0` it measured 0 px.

## Traps, symptom first

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
4. Make Apache authorize the member door's path before forwarding the client status.
   Install a dedicated test CA for this demonstration and offer a shared PKCS#12 client identity to visitors.
   Keep its signing key out of the release.
   Run `apache2ctl configtest` before reloading, then test the static site, both client-certificate controls and the undo.
   Location-level client authentication depends on TLS renegotiation or, in TLS 1.3, post-handshake authentication. [Apache mod_ssl](https://httpd.apache.org/docs/2.4/mod/mod_ssl.html).
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
- **Symptom:** a path-level client certificate gets an HTTP error or a TLS alert. **Cause:** the path is known after the first TLS handshake. **Evidence:** Apache 2.4 on Bookworm accepted the same test identity over TLS 1.2 and TLS 1.3 with curl and refused the request without a certificate. Use a browser-specific positive control before giving the route to visitors.
- **Symptom:** an ImageBitmap or OffscreenCanvas transfer fires `messageerror` in the other site's Gecko process. **Fix:** show the error and send camera frames as bytes in an ArrayBuffer over the existing MessagePort. **Found by:** the echo probe and the camera frame counter.
