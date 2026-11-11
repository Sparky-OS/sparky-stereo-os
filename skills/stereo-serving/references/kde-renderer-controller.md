# A KDE controller for UMS renderers

## Working recipe

1. Reconcile the published settings package with its exact source archive before adding a controller.
2. Keep UMS's sharing and service enablement choices unchanged.
   Resolve the selected local file only inside its existing active shared folders.
3. Use UMS's renderer-specific browse and media-selection API with the chosen renderer ID.
   Discover that renderer's AVTransport and RenderingControl service versions, endpoints and actions through SSDP and its SCPDs.
4. Publish the explicitly selected renderer on MPRIS2.
   Remove the old service before refreshing or changing targets.
   Propagate SOAP faults to both the visible window and D-Bus callers.
5. Exercise the actual Purpose alternatives model and jobs, KIO's service-menu engine, and a private Dolphin window.
   Compile and capture all required languages.
6. Run a real UMS instance and an emulated renderer on an internal container network.
   Check the received bytes, decoded raster and both views, alongside Play, Pause, Seek and volume.
   A successful SOAP call alone is not playback proof.

The controller is a control point, not another media server or a local stereo player.
UMS keeps the renderer's profile, permissions and edge conversion.
No desktop stereo-output selector belongs here.
The initial controller supports instance 0 only; it does not allocate multi-instance connections or claim DLNA certification.

## Traps found by running it

- **Symptom:** the desktop sees a generic renderer's library or media URL.
  **Cause:** UMS's ContentDirectory browse identifies the requester by its IP address.
  **Fix:** use `/v1/api/renderers/browse` and `/v1/api/renderers/control` with the selected renderer ID for media selection.
  **How found:** compared UMS's SOAP browse path with RendererItem's remote-control browse and media selection code, then played a real selected-renderer conversion through the API.
- **Symptom:** the UMS API refuses an apparently local request.
  **Cause:** authentication is enabled by default, while localhost administrator access is disabled by default in the inspected UMS source.
  **Fix:** honor the authentication requirement and offer explicit sign-in; never modify a person's authentication setting to make a controller work.
  An isolated fixture may explicitly enable localhost administration in its own disposable profile.
  **How found:** the real server returned a permission error; checked the defaults in UmsConfiguration rather than assuming localhost was trusted.
- **Symptom:** SSDP discovery works on a normal network but fails on an internal test network.
  **Cause:** the internal network has no default multicast route.
  **Fix:** send M-SEARCH on each up multicast-capable interface, then verify the returned description's UDN against the selected UUID.
  **How found:** the fixture received no search until the outgoing interface was set explicitly.
- **Symptom:** a real UMS remote player cannot control an emulator that accepted earlier manual SOAP calls.
  **Cause:** its SCPDs contained no action descriptions.
  **Fix:** advertise complete action arguments and state variables for the actions the emulator actually implements.
  **How found:** jUPnP discovers and validates the service description before invoking its actions.
- **Symptom:** Seek fails on a strict renderer even though argument names look correct.
  **Cause:** a sorted map changed the SOAP argument order.
  **Fix:** preserve the service schema's argument sequence, including InstanceID, Unit and Target.
  **How found:** a strict wire fixture checked namespaces, argument order, instance and channel instead of accepting arbitrary XML fields.
- **Symptom:** a SOAP fault is visible in the window but the MPRIS caller receives success.
  **Cause:** QDBusContext on the abstract adaptor did not provide the expected call context.
  **Fix:** export the Player interface from a QObject with QDBusContext; keep the root interface as its adaptor.
  **How found:** a separate-process D-Bus regression expected a SOAP fault to be an error reply.
- **Symptom:** a D-Bus volume command fails intermittently in a real compositor session.
  **Cause:** the periodic synchronous status poll is still running when the method arrives.
  **Fix:** delay the D-Bus reply and queue the action behind the poll, with a deadline and an explicit error on failure.
  Preserve action errors across successful periodic polls.
  **How found:** private-KWin tests exposed the race that offscreen tests had missed.
- **Symptom:** D-Bus registration warns about QWidget's grab method.
  **Cause:** ExportAllSlots exported inherited widget methods.
  **Fix:** mark the intended Open entry point Q_SCRIPTABLE and use ExportScriptableSlots.
  **How found:** the Purpose job handed off correctly but registration emitted an unsupported QPixmap return-type warning.
- **Symptom:** private-KWin windows work but ScreenShot2 cancels every capture.
  **Cause:** the compositor is using QPainter; the inspected ScreenShotManager implementation needs an EglBackend.
  **Fix:** give the isolated compositor an authorized GPU or a working software EGL backend, then use CaptureWorkspace and verify the returned dimensions.
  **How found:** read ScreenShotManager::takeScreenShot and compared its backend condition with the compositor log.
- **Symptom:** a capture shows an input-permission dialog instead of Dolphin's menu.
  **Cause:** newer Xwayland routes XTEST through libei and requests permission.
  **Fix:** preauthorize only the test input client in the disposable compositor's XwaylandEisNoPromptApps setting.
  Never alter the person's KWin configuration.
  **How found:** inspected the captured dialog and KWin's matching configuration implementation.
- **Symptom:** a seek request succeeds but its received body is empty.
  **Cause:** the seek was exactly at the end of a one-second fixture.
  **Fix:** use a longer fixture and seek inside its duration; record response headers and byte counts as well as control results.
  **How found:** the HTTP record showed playback bytes but no bytes for the end-of-file seek.

## Proof boundaries

Translated captures prove that catalogues load, not that native speakers reviewed the wording.
Ordinary private-KWin UI captures do not prove stereo identity or depth.
An emulator proves the control path and received stream, not a physical phone or television's decoder or panel.
A local package candidate is not a published release or a full release-cohort qualification.
