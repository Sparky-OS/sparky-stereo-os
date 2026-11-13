# A WebGL or WebXR control proven in stereo with a GPU, and what the browser does without one

Measured 2026-11-13 with a small WebGL control of our own (a glTF 2.0 model, one camera, an `immersive-vr` WebXR session on a button) in the edition's browser, builds +stereo3d9 (published), +12 and +14 (staged), under Stereo KWin +stereo3d46 in a container, on an NVIDIA card through CDI and with no card at all.
It continues [x3d-in-the-browser.md](x3d-in-the-browser.md) and [web3d-engines-in-the-browser.md](web3d-engines-in-the-browser.md): same two routes (the browser's second camera for a plain WebGL page, the session's own views for WebXR), one control instead of an engine matrix, and the case those pages did not run: a browser whose compositor is in software.

## The recipe

1. **An image of your own from the published repository.** Start from a Debian testing base pulled by digest and add three things before installing: the edition's source and its key, the deb-multimedia source for the same suite with its keyring (the edition's repository carries the keyring package), and the two pin files that the published `sparky-stereo-apt` package ships (`apt-get download sparky-stereo-apt`, `dpkg-deb -x`, copy `etc/apt/preferences.d/*`). Then `apt-get install --no-install-recommends` the browser, `kwin-wayland`, and for a whole-desktop picture `plasma-workspace`, `plasma-desktop`, `kinfocenter` and `sparky-stereo-info`.
2. **One fresh container and session per case**, as your own user with a passwd entry: `dbus-run-session`, a copy of `kwin_wayland` (the packaged file's capability is refused in a container), `--virtual --width 1920 --height 1080` with `KWIN_VIRTUAL_STEREO_MODES=1`.
3. **A virtual output that can show 3D.** Start KWin once so it writes `kwinoutputconfig.json`, stop it, set the output's `anaglyph` and `otherStereoFormats` to true and add `0x20000 | 0x200` to its mode's `flags` (clear bit 0), start it again. Without a stereo-capable output the flat WebXR display is not offered.
4. **The browser** with `--marionette -remote-allow-system-access --profile NEW --kiosk`, `WAYLAND_DEBUG=client` and `MOZ_LOG=sync,WebGLStereo:4`, the page served from 127.0.0.1 inside the container (`--network none`).
5. **Three cases on the GPU:** the plain page (the second camera), the same with `webgl.stereo-camera.enabled` false (the 2D control), and the page's own 3D button clicked with WebDriver pointer actions (`permissions.default.xr` 1).
6. **The same three with the compositor in software.** Two ways, and they are not the same test: no device given to the container at all (KWin and the browser both on llvmpipe; ScreenShot2 then answers `Screenshot got cancelled` often, so only the logs are evidence), and the card given with `gfx.webrender.software` true (KWin on the GPU, only the browser's compositor in software; captures work, so this is the one that shows what the person sees).
7. **Read four things per case:** the browser's own Wayland log (`kde_stereo_content_manager_v1.create(` and `set_content(3)`, counted, not the binds), `present two eyes` lines of the `WebGLStereo` log, the window's notification bars (`gNotificationBox.allNotifications` and `gBrowser.getNotificationBox()` from the chrome context), and the ScreenShot2 pair.
8. **Measure one marker.** Give the model a small part in a colour nothing else has (flat magenta), find its centroid in each eye, and compare left x minus right x with the prediction: for the second camera `s W (C / Z - 1)` with Z the marker's distance along the camera axis from the page's own matrices; for WebXR the marker projected through the session's recorded views and viewports.
9. **In each eye, look at both halves.** A marker that appears once in each half of the same eye, half as wide as it is high, is an undeclared pair painted flat: the test for "squeezed" that a colour check cannot give.

## What was found

| build | route | compositor | declared | what the capture holds |
|---|---|---|---|---|
| +9, +12 | plain page | GPU | 1 create, 1 `set_content(3)` | marker -31.98 px against -32.01 predicted (2 % of a 1904 px canvas, plane at 5 times the near distance), vertical 0.00 |
| +9, +12 | WebXR | GPU | yes | -6.70 px against -6.69 from the session's views |
| +14 | plain page | GPU | yes | +0.65 px against +0.64 (separation 0.00525 of the width from the person's limits, plane at 3.340 m from the scene's depth) |
| +14 | WebXR | GPU | yes | +10.25 px against +10.27 |
| +9 | 2D control | GPU | none | 0 of 2073600 pixels differ between the eyes |
| +9, +12, +14 | either | software | none | both eyes identical; the marker twice in each eye, 16 px wide where it is 31; `present two eyes` logged; notification bars empty |

So on a GPU a control needs nothing: draw one camera for the plain page and the session's views under WebXR, and the browser declares the pair.
In software the browser still drew two views and nothing carried the declaration, because the declaration travels on a layer of the browser's compositor and software WebRender makes no such layer.

## The fix, and how it was proved without a compile

Where a window's `windowUtils.layerManagerType` names a software compositor, the browser sets `webgl.stereo-camera.enabled` and `dom.vr.flat.enabled` false on the default branch and locks them for the session, and appends one notification to the window's bar with the compositor's name and the last log entry of the `WEBRENDER` feature of `nsIGfxInfo.getFeatureLog()` (its failure id and message, `FEATURE_FAILURE_SOFTWARE_GL, Blocklisted by gfxInfo` on llvmpipe).
The page then draws its own one picture, `isSessionSupported('immersive-vr')` answers false so a control hides its 3D button, and the person reads what failed and why.
After it: 0 `present two eyes` lines, one marker 28 px wide, the notice in the bar (also in a second language), and the GPU cases unchanged to the hundredth of a pixel.

A change that is only script and strings can be run without building the browser: both script files were byte-identical in the fork's source and in the built package's `browser/omni.ja` (assert it), so the patched files and the string appended to each packaged `localization/LOCALE/browser/browserContext.ftl` go into a copy of that archive (stored, not deflated), mounted over the package's in the same rig image.
Say in the report that the package itself was not built.

## Traps

- **Symptom:** `apt-get install` of the browser in a rig image ends with `Unable to satisfy dependencies. Reached two conflicting assignments`, hundreds of "but it is not going to be installed" lines. **Cause:** the edition's `librsvg2-2` depends on `libdav1d7 (>= 1:1.5.4)`, an epoch-1 version only deb-multimedia has, and the image had Debian and the edition only. **Fix:** add the deb-multimedia source. **Found by:** `apt-get -s install` of the browser alone and reading the numbered chain to its last line, `but none of the choices are installable: [no choices]`.
- **Symptom:** after that, the same error names `gtk-update-icon-cache`, whose `apt-cache policy` shows `Candidate: (none)` and the Debian version at `-1`. **Cause:** the only-ours pin file was taken from the build tree, which is ahead of the published repository and blocks Debian's build of a package the repository does not carry yet. **Fix:** take both pin files from the published `sparky-stereo-apt` package. **Found by:** the `-1` in `apt-cache policy`.
- **Symptom:** `sparky-stereo-apt` itself will not install in a container. **Cause:** it depends on a package of the parent distribution's own repository. **Fix:** unpack it and copy its pin files; do not add a third repository to a rig.
- **Symptom:** `Marionette:SetContext ... System access is required`. **Fix:** start the browser with `-remote-allow-system-access`.
- **Symptom:** `move target out of bounds` from a pointer action. **Cause:** the path to the button began outside the viewport, or the button is hidden and its rectangle is 0 by 0. **Fix:** start the move inside the page; treat a hidden 3D button as the result ("no immersive session offered"), not as a probe failure.
- **Symptom:** a preference set false still gives two views on one site. **Cause:** the per-site 3D Canvas permission set to On wins over the preference in `ClientWebGLContext::UpdateStereoCameraSite`. **Found by:** adding the permission from the chrome context (`Services.perms.addFromPrincipal(principal, 'stereo-camera', ALLOW_ACTION)`) and running the software case again. **Fix:** one condition there (`gfx::gfxVars::UseSoftwareWebRender()`), which needs a compile; script cannot close it without touching the person's saved choice.
- **Symptom:** a first compositor start has no 3D twin to restore. **Cause:** `kwinoutputconfig.json` does not exist before KWin has run once. **Fix:** the two-pass start of step 3.
- **A whole-desktop picture shows the machine.** About this System prints the host's processor, memory and graphics card, since a container has no hardware of its own; say so beside the picture, and let the person decide before it leaves the house.
- **Panel launchers are blank squares** in a rig image: the default panel names programs the image does not hold. It is the image, not the desktop.
- **The reason is the graphics layer's own English.** The failure id and message come from the browser's feature log untranslated; the sentence around them is translated.

## What a control should do

- One camera for the plain page, never a second view of its own; the session's `views` under WebXR, each with its own viewport, projection and inverse transform, unchanged.
- Show the 3D button only when `isSessionSupported('immersive-vr')` says yes, and offer nothing else for stereo but the render resolution per eye: separation, the screen plane, the eye order and every output format belong to the desktop.
- Say in its own status line where its values come from and what it could not draw.
