# A declared layer's state follows its declaration

Learned from ORDER 448 (November 2026), after ORDER 49's October picture: a packed frame, both views side by side in each eye, while the player said 3D.
The rule is the edition's no-silent-fallbacks design (nothing silently fails or falls back: it works, or the person is told) applied to the 3D area: the layer is active only once the compositor took its declaration, and a failed declaration is said and the video is drawn the ordinary way.

## The rule

- **Never commit a buffer of two views to a surface that is not declared.**
  Stereo KWin shows an undeclared surface as the 2D picture it is, so the person sees the packed frame flat.
  Declare the surface before the first buffer is attached (a desynchronised subsurface applies the declaration with its next commit, so nothing changes on the wire), and let nothing attach or commit while the declaration is refused, on every route that fills the surface (wl_shm, a driver's window surface, the layer's own DMA-BUF buffers).
- **"Active" is read after the declaration, never before.**
  A property such as `stereoLayerActive` that tells the player the video is in the layer must be false until the declaration was taken, and false again for good while it is refused.
  Derive it from "the layer exists and is declared", not from "3D was wanted and a presenter was started".
- **A refusal is said twice.**
  The log once (not once per frame: the first version of the fix logged 265 times in 8 seconds), and a read-only property with a change signal that the player reads and can show (`Video.stereoLayerFailure`, an empty string while all is well).
  A library cannot pop a dialog for its application: the property is how the failure reaches the person.
- **The video goes the ordinary way.**
  With the layer withdrawn the item draws the video through the scene graph, one view chosen by the person's view setting, never the packed frame.
- **Retry on a boundary the person can see.**
  The refusal is kept while the same 3D video plays (so the declaration is not asked for at every frame) and forgotten when that 3D video ends or the item changes window: the next 3D video declares again.
  `libstereo-declare` caches the compositor's global once per process, so a compositor that gains the global later is seen by a new process, not by a retry.

## Recipe: force a declaration failure and capture it

1. A rig image with the edition's Qt Multimedia, a QML player that prints `stereoVideo`, `stereoLayerActive` and (where the build has it) `stereoLayerFailure` (a 200 ms timer logging only changes: an undefined property reads `undefined` on a build without it, so the same player runs on the old and the new build), and the red/blue full side by side clip of the proof rig.
2. Build `../../stereo-proof-rig/scripts/refuse-shim.c` (`cc -shared -fPIC -o refuse-shim.so refuse-shim.c -ldl`) and preload it into the player: `LD_PRELOAD=refuse-shim.so STEREO_REFUSE=1` refuses every `stereo_declare_wayland` with `-ENOTSUP`, the value `libstereo-declare` returns when the compositor's global is gone; `STEREO_REFUSE_FILE=PATH` refuses while the file exists.
   Set the variables in the same `env` word list as the player (the container does not pass them on).
3. Start a fresh Stereo KWin (virtual backend, an anaglyph or side by side twin of the output), play, capture both eyes after 8 seconds, and name the 3D area with the proof rig's `check.py`.
4. Measured on Stereo KWin +stereo3d46 (virtual output, anaglyph twin, RTX 3060 through CDI) with Qt Multimedia +stereo3d14 and then +stereo3d15 (ORDER 448): before the fix FLAT (both eyes show red left of blue), `stereoLayerActive=true`, 0 `kde_stereo_content_manager_v1.create` and 0 `set_content` in KWin's `WAYLAND_DEBUG=server` log, one warning per frame in the player's log.
   After the fix: the left view in both eyes (one view, the ordinary picture), `stereoLayerActive=false`, `stereoLayerFailure` holding the reason, one warning, still 0 declarations on KWin's side.
5. Retry: a player that plays the 3D clip, a 2D clip and the 3D clip again, with `STEREO_REFUSE_FILE` removed during the 2D clip, shows the failure at the first 3D video, an empty `stereoLayerFailure` at the 2D clip, and STEREO with one declaration at the second 3D video.
6. The control that must still pass: the same run without the shim is STEREO (red left eye, blue right eye) with `stereoLayerActive=true`, `stereoLayerFailure=''`, 1 `create` and 1 `set_content(3)`.

## Traps

- Symptom: a compositor without the stereo global shows no problem, but a refused declaration does.
  Cause: `isSupported()` reads the globals once, so a compositor without `kde_stereo_content_manager_v1` never creates the layer (ordinary path, nothing to say); the failure is only reachable when the global is there and the declaration still fails (a library error, a global withdrawn between the check and the call, `-ENOMEM`).
  Found by: reading `stereo_declare_wayland` (`declare_wayland` returns `-ENOTSUP` only when the manager is gone) before building the case.
- Symptom: the first design added a callback from the presenter's thread to re-route the video when a declaration failed "late", and the late branch could never run.
  Cause: once the surface is declared at creation, `declared` stays true for the layer's life; a refusal can only happen at creation.
  Fix: no late path; the creation-time refusal is the only one, and the code for the other was removed.
  Found by: tracing which call can set the error after the layer is made (none), the review rule "read each changed branch for reachability".
- Symptom: after a refusal the presenter was made again at every timer tick (a thread per tick).
  Cause: the presenter is dropped when invalid and the output asks for it again while 3D is wanted.
  Fix: the output keeps the refusal (`m_stereoLayerFailure`) and asks again only after the 3D video ended.
- Symptom: a shim that refuses a declaration passes the other calls on with `dlsym(RTLD_NEXT, ...)` and every passed call fails with `-ENOTSUP`.
  Cause: `libstereo-declare` is a dependency of the QML plugin `libQt6MultimediaQuick`, which QML loads with dlopen after the player started, so the library is not in the global scope that RTLD_NEXT searches and `dlsym` returns NULL.
  Fix: look the real function up in the library asked for by name: `dlopen("libstereo-declare.so.1", RTLD_LAZY | RTLD_NOLOAD)` and `dlsym` on that handle (`../../stereo-proof-rig/scripts/refuse-shim.c`).
  Found by: printing the pointer the shim got ("the real stereo_declare_wayland is not found"), after a control run with the shim in pass-through mode failed where the run without the shim passed.
- Trap of the proof: `kde_stereo_content_manager_v1` appears in KWin's log at every client connection (`wl_registry.global` and `bind`), so count the `.create` request and `set_content(` on `kde_stereo_content_v1`, not the word `set_content`: `wp_content_type_v1.set_content_type` matches it too (a count of 2 for one declaration).
