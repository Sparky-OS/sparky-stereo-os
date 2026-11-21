# Tracked phone headset: owners and proof boundaries

Reconciled 2026-11-20. StereoDroidVR is the tracked Android program; iStereoVR is the later tracked iPhone program. Flat Headset is the static desktop/movie program. Renaming the product does not rename wire identifiers, repository URLs or Android application identifiers.

## Working recipe

1. Pin the accepted phone, KRdp, FreeRDP and runtime sources and inspect the edition's published package index. A staged package and an installed test prefix are not a published package.
2. Retain KDE Connect pairing as the entry condition. Picture and pose belong to the same authenticated RDP session; camera frames use RDP camera redirection. ALVR and WiVRn are use-only references, not a parallel transport.
3. Join the peer-bound pose consumer to the PC OpenXR headset provider. The provider must preserve source identity, capture time, uncertainty, origin and validity. A synthetic input grant proves an interface, not desktop authority.
4. Prove the resulting views in an isolated Android/PC rig, including wrong-axis, stale-pose, revocation and reconnect controls. OpenVR through xrizer is a separate positive row. Running that application does not prove the SteamVR runtime.
5. Leave optical fit, real sensor behavior, hardware decode, motion-to-photon latency and real audio listening to a bench run with the person present.

## Clause map

| Clause | Owner and boundary | Evidence available; open part |
| --- | --- | --- |
| Pair and virtual output | KDE Connect trust, KRdp control lease, KWin output | Flat Headset 13513 and KRdp +11 have staged pairing-dialog, revocation and HEVC guest proof. Apply that trust to tracking; do not replace it with the sensor fixture's synthetic grant. |
| Pose leaving Android | Android fused sensor, bounded latest-sample mailbox, FreeRDP DVC | Sensor work at Flat Headset `a627bbe528cf` delivered 338 framework-fused readings in an emulator. The production tracked program still needs integration. |
| Pose on PC | KRdp `6bdb9ac036da`, `StereoPoseConsumer` | Validated message, clock, geometry and lifecycle; synthetic peer-bound consumer accepted. No production OpenXR adapter established by that result. |
| PC headset | Active OpenXR runtime, its headset pose provider and two view cameras | First open integration boundary. OpenVR reaches it through xrizer. Existing DisplayXR/xrizer two-eye proofs are flat-display proofs, not phone headset acceptance. |
| SteamVR itself | Separate runtime qualification | Not demonstrated by xrizer translating an OpenVR client. Never infer it from an OpenVR SDK sample. |
| Camera and hands | Android Camera2 → FreeRDP RDPECAM → PC tracking worker | FreeRDP `c39d13c47306` and a matching 3.33.1 server delivered twelve raw NV12 640×480 frames. Camera delivery is accepted; hand inference, calibrated pose and timing integration remain open. |
| Lens presentation | Phone viewer with calibrated optics and frame-pose history | Earlier PhoneVR/Cardboard ALVR proof includes retained-frame reprojection and pause/resume. It must be requalified on the RDP viewer with tracking enabled. |
| Room audio | PC multichannel audio and the same head-pose origin | Isolated yaw-control and impulse-rotation probes exist. A continuously tracked room-anchored 5.1/7.1 result is not established. |

Accepted predecessor reports are evidence for those scopes only. The Android-to-desktop xrtransport work is a different direction from a phone receiving PC VR over RDP.

## Existing pose message

Source of this description: KRdp `6bdb9ac036da`, `src/stereotracking/Protocol.{h,cpp}`, `Geometry.cpp`, `Session.cpp`, `PoseState.cpp` and `src/StereoPose.h`. These are prototype semantics already implemented, not a new protocol proposal.

The dynamic virtual channel is `Sparky.StereoDroid.Pose.1`. Keep its spelling when changing the displayed name. Integers are little endian. The envelope is 32 bytes; maximum complete message size is 4096 bytes.

| Offset | Field |
| --- | --- |
| 0 | Four-byte magic `SDP1` |
| 4 | uint16 version 1 |
| 6 | uint16 type: HELLO=1, SELECT=2, POSE=3, CLOCK_REQUEST=4, CLOCK_RESPONSE=5, STATUS=6 |
| 8 | uint32 total length including envelope |
| 12 | uint32 session epoch |
| 16 | uint64 sequence |
| 24 | uint64 time in nanoseconds; POSE uses original sensor capture time |

POSE has a 32-byte payload: four float32 quaternion components at offsets 0/4/8/12 in **xyzw** order, uint16 sensor at 16, int16 Android accuracy at 18, uint32 flags at 20, uint32 source epoch at 24 and uint32 mounting at 28. Sensors are 15 (game rotation vector) or 11 (rotation vector). Flag bit 0 says orientation valid; bit 1 says yaw may drift. Accuracy is -1 through 3, not a calibrated confidence value. Quaternion norm must be within 1% of one, then is normalized. Position is not carried.

The wire quaternion is Android device-to-world. Android's quaternion helper returns wxyz, so the adapter reorders it. KRdp applies the negotiated mounting and recentered reference and yields canonical head orientation: look along -Z, up +Y, xyzw quaternion. Mounting values 0–3 correspond to quarter-turns about device Z; the accepted independent ray checks cover both landscape mountings 1 and 3. Do not apply a display rotation again in the runtime. The consumer's optional position is metres; the orientation-only result leaves position and confidence unknown and position validity false. A neck model is modeled translation, never measured six-degree-of-freedom tracking.

HELLO advertises the available fused sensor/rate; SELECT chooses 30, 60, 90 or 120 Hz explicitly, and repeats the chosen nonzero epoch. Unavailable rate/source must fail explicitly. Before accepting pose, the session waits for eight real clock exchanges. It retains source capture time, mapped PC time and uncertainty, refreshing clock samples every 250 ms after startup. It must not substitute receipt time for capture time.

## Recentering, loss and reconnect

Registration binds source, session, lease, output, seat and peer token to an active input grant. The interface alone does not mint this grant. The first acceptable reading establishes the reference. A recenter request invalidates the old result, resets geometry/capture history and advances the origin; the next acceptable reading establishes the new reference. A changed sensor source epoch pauses delivery until recentered. Stale old-source packets are rejected before changing source-epoch state.

The receiver checks freshness even while no network event arrives. At 100 ms it pauses and invalidates; at 250 ms it reports unavailable. Recovery from stale input requires three fresh readings. Revocation or disconnect invalidates, releases held actions and unregisters the source. A new session must redo the peer/lease authorization, epoch negotiation and clock calibration; neither pairing alone nor a cached valid quaternion permits reuse of the old registration. Installed-package reconnect through the OpenXR consumer is qualified separately by the paired lifecycle controls below.

## Rendering and future seams

The PC renders the world, with OpenXR as the common boundary and xrizer translating OpenVR applications. Every source gives KWin full side by side, left eye first, at any render resolution per eye. KWin owns output conversion; the phone link keeps half side by side for latency. Apply the person's existing headset depth limits once. Do not add a runtime factor on top of limits already resolved for that headset output.

Automatic switching later selects the static or tracked program against the shared paired-session lifecycle; it must not create a second trust route or duplicate monitor lease. The future iPhone implementation can supply the same message, coordinate and lifecycle contract from its sensor adapter after its static receiver works. Neither seam requires implementing those products during Android reconciliation.

## Traps found in reconciliation

| Symptom | Cause | Fix and how found |
| --- | --- | --- |
| README says there is a headset, but no APK target exists | The named stereodroid repository contains seven documentation/licence files; earlier executable work is in PhoneVR and Flat Headset | Inspect the tree and branch histories before choosing a build owner. `git ls-tree` at `1123824` exposed the boundary; a documentation rename does not rename the APK. |
| Accepted sensor result is described as a production HMD | A synthetic-grant `StereoPoseConsumer` was mistaken for a runtime provider | Require the peer/lease permission adapter and measured OpenXR views. Found by comparing the accepted sensor report with `StereoPose.h`. |
| A lane reports a missing edition component from its container | The lane image differs from the published pool and from staged candidates | Read the published Packages index and retain version/hash/filename. The 2026-11-20 amd64 index listed KRdp/KPipeWire +8 while later +11/+9 candidates were staged. |
| Renaming breaks channel negotiation | Branding was applied to a protocol identifier | Keep `Sparky.StereoDroid.Pose.1` and application IDs; rename human-facing text only. Found by separating source identifiers from repository prose. |
| An old ALVR proof is called the paired RDP route | Earlier plans used a different transport | Retain historical attribution and proof scope, and use the same-session RDP design for integration. Found by comparing the earlier report and current brief. |

For established source-time, mounting, mailbox, status-drain and emulator traps, use [RDP sensors and emulator preflight](../../3d-to-vr/references/rdp-sensors-preflight.md). No new executable result is claimed by this reconciliation.

## Paired orientation adapter implementation

The earlier standalone tracked Android target lived in PhoneVR's `code/mobile/android/StereoDroidVR`, with application identifier `viritualisres.phonevr` and held versionCode 20002 after the recenter-touch correction. It carries the paired KDE Connect/FreeRDP receiver foundation. The tracked entry always asks for a virtual output and the fixed half-SBS link; the static receiver's descriptor helper remains separate so its format and no-echo controls stay meaningful. The tracked APK builds for ARM64 and x86_64 and passes all 94 offline controls without changing its prepared hash. A complete headset remains unqualified.

KRdp's `PairedPanelSessionService` binds tracking to the actual paired peer, control lease, session and output. It does not take the sensor fixture's synthetic grant. Revoking the panel lease clears the shared active-grant state. `HeadsetPoseConsumer` sends validated orientation to a same-user local Unix socket; this is a PC-internal boundary, not another phone transport.

The runtime creates `$XDG_RUNTIME_DIR/stereodroidvr/pose` as `AF_UNIX/SOCK_SEQPACKET`, in an owner-checked 0700 directory with a 0600 socket. Both ends check `SO_PEERCRED`. `STEREODROIDVR=1` selects this provider explicitly for the integration rig. It fails closed if the endpoint cannot be created; it does not silently use keyboard tracking. Automatic product/runtime selection is still open.

The local ABI is 160 bytes, all integers little endian, with no native structure layout:

| Byte offset | Field |
| --- | --- |
| 0, 4, 6 | `SDVR`, uint16 version 1, uint16 kind: register 0, pose 1, invalidate 2, end 3 |
| 8, 24, 40, 56 | Four 16-byte identities: source, RDP session, control lease, output |
| 72, 80, 88, 96 | uint64 PC BOOTTIME capture, original source capture, uncertainty, origin; time fields in ns |
| 104 | Four IEEE-754 float64 values, quaternion xyzw, canonical -Z forward/+Y up |
| 136, 140, 144 | uint32 source epoch, mounting, validity flags (bit 0 orientation valid) |
| 148, 150 | uint16 reason, ten reserved zero bytes |

The runtime accepts registration before pose, requires all four identities and preserves their equality. It bounds a poll to sixteen messages, rejects malformed size/version/reserved fields and nonfinite/nonunit quaternions, invalidates on stale or nonmonotonic capture times, and clears validity at 100 ms even without another message. Uncertainty over 50 ms is rejected. EOF, end and invalidation remove tracking validity. A fresh connection requires a fresh registration. It advertises only measured orientation, never tracked position or invented angular velocity. The held runtime retains origin but emits no OpenXR reference-space-change event. A successor implements capture-timed LOCAL, LOCAL_FLOOR and STAGE notifications and bounded queries on either side of the change; its two direct provider tests pass 70 assertions. The successor passes its clean package suite and archive gates. With XR_EXT_local_floor enabled, the paired client observes all three spaces. The qualified socket successor has paired denial/approval, both signed-axis mountings, stale/invalid clocks, changed epochs/replay, pause/recenter, revoke/unpair and killed-runtime reconnect controls. These establish transport and orientation state, not rendered eyes or physical sensor behavior. The installed-plugin build-image trap described below must be kept separate from an event regression.

An isolated prototype used actual KDE Connect pairing and consent, an Android framework-fused sensor, the RDP DVC, this local adapter and real `xrLocateViews`. Rotation changed the reported orientation and pausing the receiver cleared validity. This proves the prototype boundary, not a final installed-package pair, eye rendering, lens reprojection, xrizer, SteamVR, hands or audio. The inherited viewer-pose-page stress test needs its reader attached before its writer starts; its corrected package proof is separate from qualification of a complete headset.

## Traps found while building the adapter

| Symptom | Cause | Fix or remaining action; how found |
| --- | --- | --- |
| Paused source still reports a runtime available after its socket closes | Availability only tested whether the descriptor existed | Poll HUP/ERR/NVAL; the consumer red test fails before and passes after the change. |
| Missing runtime becomes an Android epoch-mismatch message | Rejection before SELECT used the newly allocated nonzero epoch | Send epoch zero until SELECT and report TrackerUnavailable; the handshake red/green tests cover the actual state transition. |
| Paired panel cannot create its virtual stream although the edition has the protocol | Apt picked newer stock plasma-wayland-protocols, then generated headers outlived the corrected XML | Build against the edition XML and regenerate the affected cached headers; reproduced in the isolated rig. A container dependency error is not absence from the edition. |
| KDE Connect appears unpaired despite the expected name | Stock Debian packages were selected instead of the edition's paired-headset extension | Inspect installed versions and use the published edition packages; actual UI pairing plus PC acceptance then produced a reachable paired device. |
| Loopback-only Android guest never discovers the PC | KDE Connect filters loopback broadcasts and the emulator NAT did not forward the discovery packet | A rig-only helper sends the installed library's public identity packet; adb reverse carries the guest's normal TLS connection. Pairing and consent still happen normally. Never ship this fixture as a connection route. |
| Two static descriptor controls fail after adding the tracked target | A global change forced half-SBS even for static tests | Keep static `measure()` semantics and add a separate fixed-format `tracked()` entry. All 94 controls passed in a network-none verification container, with the prepared APK hash unchanged. |
| APK rebuild stops while projecting OpenSSL | Disk exhaustion interrupted the projection and left an in-progress marker | Discard the disposable projection and rebuild from authored sources on a disk with room; never reuse partial projection as authored input. A fresh projection then built and passed all 94 offline controls; the interrupted tree was never reused. |
| Viewer-pose stress gate loses samples from its total on a loaded machine | The writer can lap the reader before its first drain; that drain intentionally starts at the oldest retained sample, while the test counts from sample one | With the test correction approved, attach the reader on the empty page before starting the writer. `u_vpp_read_new` then sets `started=true` and `next=0`. Keep every assertion, retry count and the product reader unchanged. Prove the old precondition deterministically by letting the writer finish before the first read, then require 200 loaded consecutive passes and the original package suite. The negative control got 16 of 200000; 200 loaded runs passed, followed by all 215 enabled suite tests through the unchanged invocation. |
| A higher versionCode and the same application ID still cannot upgrade the old debug APK | The carried receiver and old PhoneVR APK use different debug signing certificates | Compare certificate SHA-256 values as well as ID/code. The new APK uses the receiver’s public debug fixture; it is an emulation artifact, not an in-place upgrade of the accepted PhoneVR predecessor. Do not read or replace a release key to hide the difference. |
| Bubblewrap fails in Docker, then also fails inside a guest chroot | Docker namespace restrictions, followed by the kernel's chroot restriction on user namespaces | Use the authorized KVM guest with a private mount namespace and a real pivot_root, then run the unchanged gate. No extra host capability or passthrough device is needed. |

The older clause table above records the accepted predecessor boundaries. The adapter and tracked target are new implementation work with prototype evidence, not accepted replacements for those records.

The compile-only proof must retain debhelper’s build-system context. Calling the configure override directly without `DH_OPTIONS` selected Makefiles while the package uses Ninja; modern debhelper also rejects the former `--until` option. Invoke the existing source-projection hook, configure with the package’s build-system and build-directory options, and compile with those same options. Run the normal package build and its original test invocation after the dedicated stress proof.

## Installed-pair follow-up: limits found before rendered-eye qualification

The held APK 20001, KRdp +12 and runtime +4 were exercised together through actual KDE Connect pairing and consent. Denial produced the phone's denial message; approval delivered orientation through the DVC and into `xrLocateViews`. A diagnostic two-second reduction of sensor capture timestamps stopped valid delivery, then normal timestamps restored it. These observations do not qualify the complete lifecycle or independently calibrate signed axes.

| Symptom | Cause | Fix or remaining action; how found |
| --- | --- | --- |
| Tapping the displayed recenter control leaves the local origin unchanged | `HeadsetActivity` installs a click listener on `PoseStatusView`, but its activity-level `dispatchTouchEvent` returns true unconditionally, before child dispatch | Route a gesture starting inside the visible recenter control directly to that control, in local coordinates, through UP/CANCEL; continue consuming all other Activity touches. The old installed tap retained origin 1. The corrected APK tap advanced origin to 2 and delivered Pending/CalibrationRequired then Active through the DVC; an outside tap left origin unchanged and delivered no remote mouse event. This also establishes a valid negative control for the held runtime: origin changed but no reference-space event arrived. It does not establish the successor event green. |
| A fault-injection rig crashes an otherwise working installed KRdp | The WTS read interposer dereferenced an optional count/output pointer | Guard the pointers before inspecting a successful read. Uninstrumented connection succeeded, then the corrected interposer delivered the same valid pose path. Do not count fixture crashes as product red controls. |
| A retained runtime stress build links as root but fails from an unprivileged reviewer launcher | Ninja's original link writes its dependency file in the root-owned compiled tree; CTest also writes build metadata | Run the review in the same isolated build-user context, or redirect all such outputs and arrange permissions explicitly. The corrected launcher reproduced deterministic red and 200 loaded greens. Retain the exact package image and compiled tree when the reviewer requires them; keep pairing credentials and guest disks out of that retained set. |
| Restarted rig starts Qt clients before its Wayland server is ready | A stale socket from the stopped session satisfied a socket-exists check | Check a real connection/readiness, not just the old path. The restarted KDE Connect process connected after KWin was actually accepting clients. |
| A 1920-wide headset measurement actually measures a 960-wide logical view | The virtual-output request describes the packed panel while VirtualStereo creates two views | Request a 3840-wide packed panel for two 1920-wide views and record the configured logical dimensions. Measure physical-size inputs separately; pixel width alone does not determine output depth. |

For a legacy-depth audit, keep three boundaries separate: published KWin's actual event, the exact runtime resolver's arithmetic, and a production caller supplying that resolver. The inspected +4 source has tests calling `u_depth_limits_publish` but no production caller. A headless pose probe does not start the legacy camera resolver. A direct resolver call therefore cannot establish live compositor-to-runtime depth delivery. Record this source observation without choosing a replacement policy.


### Package and source-boundary traps

| Symptom | Cause | Fix or remaining action; how found |
| --- | --- | --- |
| Three `tests_oxr_view_space_mode_*` registrations fail although a prior package suite passed | They require quad/four-view modes, but discover the installed edition SimDisplay plugin, built with `XRT_SIM_DISPLAY_FULL_SBS_ONLY=ON`. It offers only 2D and full SBS and explicitly rejects `SIM_DISPLAY_OUTPUT=quad`. | Use a build-dependency image without the package under build installed, and record verbose test output. The contaminated candidate suite passed 213 of 216; the same three tests failed with the held runtime library. In a clean image, CTest reports all three registrations passed, but all five cases explicitly skip because no display processor is registered: no plugin loads and the quad assertions are not reached. Do not remove assertions, change retries, exclude tests or call skipped cases installed-plugin qualification. Keep the installed paired rig separate from the build environment. |
| A KDE fork branch cannot be pushed because commits touch `po/` | Catalogue changes are in fork history instead of the edition package recipe | Preserve translations in the recipe, rewrite onto a new branch without catalogue changes in any commit (including merge-parent comparisons), and compare the resulting compiled MO files with the held package. Nine translated catalogues byte-matched; English remains in source. |
| A recipe stores upstream uploader addresses in our authored overlay | It copies a complete Debian control file merely to change dependencies | Apply targeted dependency edits to the extracted upstream control. Reconstruct and byte-compare the result before deciding whether binary control changed or a rebuild is needed. |
| A new label and unchanged Android package name are mistaken for an upgrade path | Android package identity also requires compatible signing; the new receiver does not preserve the legacy Activity classes | Record certificates and component boundaries. The debug successor can update its own same-signer predecessor, but it cannot update the differently signed legacy PhoneVR package in place. Source placement and application identifiers are separate decisions. |

The direct event fixture uses the local adapter, not KDE Connect consent. An actual paired tap is required for the end-to-end event proof. At a change, use the mapped capture time in the OpenXR monotonic clock domain; a receive timestamp is not a substitute. If the old-to-new reference transform is unknown, report `poseValid=false` rather than invent it. Test queries immediately before and at `changeTime`, reconnect with a reused origin serial, and invalidation after stale input. The successor's direct tests cover these boundaries; paired qualification remains open.


Linux plugin discovery walks explicit `XRT_PLUGIN_SEARCH_PATH` roots first, then the user's DisplayProcessors directory and installed system roots. The first usable component ID wins. The runtime's build directory is not automatically a Linux discovery root; an explicit development root would take precedence over `/usr/lib`. Therefore a clean build test may load no plugin rather than the tree's plugin. Inspect the verbose test log, including Catch2 `SKIPPED` cases, before describing a CTest pass as executed behavior.

When reconstructing a build image, compare detected features as well as package absence. Only the declared runtime dependencies left EGL/OpenGL/OpenGL ES disabled in the clean reconstruction; restoring the development libraries brought those features back to the held build's values. CMake cached a failed `HAVE_EGL` probe from the earlier image, so the generated cache had to be removed before reconfiguration could detect the installed headers/library. No feature flag or test definition was changed to work around this.


A completion callback can submit the next desktop capture. The upstream worker originally cleared `cap_in_flight` only after `run_capture` returned, so a callback or a recorder awakened by it could receive LIMIT_REACHED after completion. Search upstream before changing this: at the checked main revision the code was unchanged, introduced by David in the common capture worker. The flag's only reader is the mutex-protected submission guard; scheduling, teardown and retention use separate fields. The carried correction clears the flag under the existing mutex before both success and failure notifications and removes the worker's later clear, which otherwise could erase a newly submitted request. A new callback-submission case fails deterministically with -10 on both original paths and passes 22 assertions after the correction. Existing test bytes, retries and exclusions remain unchanged. Stability repetition selects the callback-submission, capture_limits and capture_audit cases by exact name for 200 consecutive loaded runs. The whole package suite retains its existing ctest invocation and until-pass:3 policy. These and paired qualification are separate proofs; a direct regression green does not complete them.

A loaded desktop-control repetition can also fail an existing kill-switch control: it submits five actions with a 100 ms fake delay, waits for at least one completion, then suspends policy and expects at least three refusals. The recorder does not pause the worker, so scheduling can let more actions finish before suspension; the failure alone does not measure that interleaving. The capture correction passed 21 complete loaded runs before this separate assertion failed with two refusals. The gate author separated that unrelated finding from capture stability: retain it as an unsent factual draft, do not change or investigate the control further. No correction to that control is carried. A failure in the three selected capture cases remains a stop; the full unchanged suite is qualified by its existing recipe, not by 200 whole-binary loaded runs.


## Application functions, identities and launcher entries

The flat receiver already is the remotedesktop function of the KDE Connect Android application. A second tracked function in that same application would share its stored device UUID, certificate and pairing. A separate application built from the same source has separate private storage and runtime identity even when the APK signer is the same. In the isolated guest, existing Flat debug 13513 and held tracked 20002 appeared as two PC devices: pairing the first did not pair the second. This is evidence about those existing IDs, not a build of a proposed new ID.

Two function icons can be activity aliases with separate labels/icons targeting an entry in one application; the entry must route the selected function on cold launch and task reuse. Android App info still describes one application. Alias entries alone do not guarantee two Recents cards: target affinity, launch mode, flags and task descriptions matter. Separate applications have separate App info and default task affinities, but still need a direct-function entry. This was the pre-decision comparison. Daniel subsequently selected one application with two functions; the implementation boundary is recorded below.

Today's active receiver is not a live flat/tracked handoff. Its per-application session guard rejects a second session; KRdp rejects a different descriptor or tracking flag under an active entry for the same certificate identity. The current lifecycle ends the old session and leases, closes decoding, and starts a new session/output/channel with fresh clock/origin state. Shared source does not transfer a decoder, pairing or profile between two app sandboxes. Preserve the common implementations when a shape is chosen; do not mistake this boundary description for an implemented handoff.

The corrected capture stability gate passed all 200 consecutive selected runs under four load workers, zero failures. The unchanged recipe suite then passed all 216 registrations in the clean image, including tests_desktop_control; the unchanged archive gate also passed all three payload packages and the final check verified all six packages. These do not complete the paired lifecycle controls.


| Symptom in the paired runtime-loss control | Cause read from our local provider | Current disposition and discovery |
| --- | --- | --- |
| After terminating the runtime, a replacement cannot create the phone pose provider | Normal destruction unlinks the same-user Unix socket, but SIGTERM bypasses that destructor. Creation refuses to bind over the retained socket, including a stale one. | The real paired run reported TrackerUnavailable correctly, then replacement xrCreateInstance failed. The retained 0600 same-user socket refused connections and returned EADDRINUSE on bind. The local-provider correction serializes startup with a lock on its private directory, probes the occupied socket, and removes it only after ECONNREFUSED, matching user, type and unchanged inode. Live owners, other users and regular files are refused with explicit diagnostics. Shutdown removes only its own recorded socket identity. Direct red controls reproduce stale recovery failure and missing refusal explanations; green covers recovery and continued first-owner pose, with a root-only foreign-owner fixture. The +6 clean suite and archive gates pass. In the paired rig a killed runtime is replaced without manual unlink, the receiver reconnects with fresh session/lease and clock calibration, and a simultaneous second runtime leaves the first tracking. The runtime logs the exact conflict; the existing OpenXR API returns XR_ERROR_INITIALIZATION_FAILED (-6), not a new ownership-specific result code. |

The paired +5 recenter produced LOCAL and STAGE events with poseValid=false and the mapped capture time; queries on either side of changeTime returned their respective orientations. LOCAL_FLOOR requires enabling XR_EXT_local_floor in the observation client; upstream deliberately filters that event otherwise. The socket successor completes its paired observation and the lifecycle/axis matrix, including runtime-loss recovery. Earlier +5 evidence remains limited to the run that stopped at the stale socket. No rendered-eye qualification or depth change follows from these orientation/event observations.


### Paired lifecycle proof boundaries

The decoder and RDP session can remain visible after tracking becomes unavailable: judge the pose state and the actual OpenXR orientation-valid bit, not the presence of video. In the isolated checks, a changed sensor epoch and foreground resume require an explicit recenter before tracking resumes. Revoke and unpair invalidate and unregister the source; a new grant requires actual permission, and unpair additionally requires a new pairing.

Use both landscape mountings with literal signed-axis fixtures, and negative opposite-sign, w-first and wrong-mount inputs. A decoded-channel fixture tests the PC coordinate mapping; it does not qualify Android hardware sensor signs. Independently recompute capture time and uncertainty from the eight real clock exchanges and the exact poll clock; corrupt receipt-time/uncertainty copies must fail that checker. Impossible timing and dropped responses must fail the live channel separately.

A headless observer must enable XR_EXT_local_floor before expecting LOCAL_FLOOR events. Record LOCAL, LOCAL_FLOOR and STAGE at the same mapped capture time, poseValid=false when no old/new transform is supplied, and queries on both sides of the boundary. This is not rendered-eye qualification. An ordinary output's depth resolver remains a separate design decision.

| Symptom | Cause | Fix / how found |
| --- | --- | --- |
| A fixture cannot activate KDE Connect on an otherwise live private session bus | The fixture runs as root while the owned session runs as uid 1000 | Run the D-Bus action as the session user. The real unpair then removes trust and invalidates pose; no trust store is seeded. |
| An Android restart briefly shows the paired PC as unreachable in a network-none emulator | The one-shot public-identity packet arrived before the restarted receiver listened | Send the same public identity once the receiver is ready, then use the real pairing and grant paths. This is emulator discovery plumbing, not permission or a second pose transport. |
| A packaging retry reports an already marked Lean payload | A failed gate left its disposable binary staging | Recreate binary staging from the compiled outputs and rerun the unchanged gate. Do not remove a marker to reproject already projected bytes. |


### A headset conflict reaches the person

The local provider keeps the specification's XR_ERROR_INITIALIZATION_FAILED result when another runtime owns the headset. The person receives the reason through the edition's one failure engine, not through a new OpenXR result or a common mapper change. The provider reads SO_PEERCRED from the connected same-user owner socket and calls the absolute sparky-stereo-problems command with literal arguments, never a shell. The person-scoped package/key is displayxr-runtime / paired-headset-in-use; data.owner_pid and data.owner_uid identify the kernel-reported process, and text_en retains the complete English explanation. The successor reads the live same-user owner’s /proc/PID/comm and includes that name plus the process number; if the name is unreadable, the existing PID-only sentence remains. No program-name table or guess is used.

Successful local headset acquisition clears that key. Dismiss is the engine's hide operation: the evidence stays retained but hidden until resolution or a changed message; it is not a second provider-owned store. The package requires sparky-stereo-problems as a Depends and carries LOCAL7 (title) and LOCAL8 (PID-only body) and LOCAL9 (body with program name and PID) in its own lang catalog. English and Brazilian Portuguese are authored; the other eight message translations remain explicitly pending. Catalog shape is not translation proof. The common runtime interface and mapper remain unchanged.

For qualification, use the installed package and engine in the same isolated paired session. On the previous package, a second runtime must be refused while the engine remains empty. On the successor, check one record in English and Brazilian Portuguese naming the actual first process, the unchanged -6 result, and the first listener's inode and fresh orientation. Check hide separately from clear on later successful acquisition. No rendered frame is needed for this ownership test.

| Symptom | Cause | Fix / how found |
| --- | --- | --- |
| A fresh successor passes the suite but packaging reports a missing Lean manifest | Replacing the entire inherited debian/rules file removed its projection and package hooks | Preserve the held rules/control and patch only the new catalog subject and dependency. Discard the invalid build and project fresh; rerun the unchanged suite and archive gate. |
| The private daemon is running, but kdeconnect-cli -a shows no device before pairing | -a lists paired reachable devices, not unpaired discovery | Use -l to inspect the one owned stand-in, then request and accept actual pairing. This supplies no trust. |
| A reconstructed rig lacks the edition's headset plugin after generic dependency installation | An unpinned dependency step selected a newer upstream KDE Connect | Install the exact recorded edition package and verify the package version before pairing. |

Throw and Catch remain the feature names in every language. At first encounter use the desktop catalogue's parenthesized everyday meaning; Brazilian Portuguese is Throw (jogar) and Catch (receber), while the landing notification stays Receba!. English is unchanged. The earlier source-only update changed headset_direct_waiting and headset_direct_connected in nine locales. The later selected one-application implementation also applies the first-contact versus running-session distinction below.


The installed failure-engine successor passes the unchanged clean suite and archive gate. Its paired red/green preserves the first listener and orientation and keeps -6; English and Brazilian Portuguese name the measured owner process, dismissal hides, and later acquisition clears. The paired successor also passes both signed-axis mountings, invalid clock/epoch/replay, stale capture, recenter/pause, denial/approval, revoke/unpair and killed-runtime reconnect. Its clock checker recomputes 11,938 samples and rejects receipt-time and uncertainty mutations; fifteen events of each world reference-space kind have at most 20 ns capture mapping error. These are orientation and lifecycle observations, never rendered-eye acceptance.

A fixture that tries `am start` on the private HeadsetActivity is correctly refused by Android. Do not export it for a test. The existing task can be brought forward for an onResume lifecycle observation; in the owned API-28 guest the fixture briefly used `am task lock TASK` then immediately `am task lock stop`, preserving the existing Activity and requiring a real recenter tap. Starting a new MainActivity can instead add another page above the session, so its later Back actions do not prove resume. Record and exclude that wrong-page fixture evidence from positive claims.


## Live owner name and failure-engine argument parsing

The same-user SO_PEERCRED check precedes the comm read. Keep owner_pid and owner_uid in data; add owner_name only when a nonempty complete read succeeds. The English record remains complete even when another locale is selected. LOCAL9 is “The headset is already in use by %s (process %s). Close that program's headset session and try again.” Brazilian Portuguese uses “O visor já está em uso por %s (processo %s). Feche a sessão do visor nesse programa e tente de novo.” Unreadable names retain LOCAL8, not a placeholder program name.

The engine parses `--` as a command boundary, not an end-of-options marker. A live program name can contain option-like text. The local provider therefore serializes message substitutions in details.args using the existing cJSON dependency, and supplies only fixed strings in literal posix_spawn argv. It does not invoke a shell. Source inspection caught this parser boundary before qualification; the first projection was discarded and the corrected source rebuilt fresh.

Owner-name proof: use a named live first instance, then a refused second instance on the held PID-only package and on the successor. Check the actual engine records in English and Brazilian Portuguese, unchanged OpenXR -6, unchanged listener inode and fresh paired orientation. A test-only fopen interposer denies exactly the owner's comm path with EACCES to prove the old sentence remains. Separately check hide/show and clearing on later acquisition.

## One application, two function entries

Daniel selected the tracked function inside the Flat Headset application. Keep its base identifier org.kde.kdeconnect_tp, existing debug suffix, version stream and application label. Both functions use the same certificate, trusted devices, viewer profile, decoder and session implementation. A real tracked launcher activity can own a separate task affinity; an activity alias cannot set its own affinity. Keep the existing Flat Headset launcher and USB service. Select the tracked descriptor, orientation controller and hidden static-mode choices per entry; never write the tracked selection into the flat function's orientation preference.

An explicit switch ends the previous function's session; it is not row 780's seamless handoff. A qualification must observe both cold entries, warm task reuse, one PC device and one pairing across both entries, flat requests without tracking and tracked requests with tracking=orientation. Inspect the complete APK comparison and the unchanged flat defaults as well as the new entry.

Throw and Catch are feature names. First-contact titles and offering labels include the everyday translation in parentheses. Running status, stop actions and session messages use the bare name. Brazilian Portuguese uses Throw (jogar), Catch (receber), Parar o Throw and visor; the landing exclamation stays Receba!. The other pairs are es lanzar/atrapar, fr envoyer/recevoir, de senden/empfangen, pl przerzucić/odebrać, ja 送る/受け取る, ko 보내다/받다, zh_CN 发送/接收 and zh_TW 傳送/接收. Do not change link or depth policy while updating wording.


For a source join, identify the actual APK baseline as well as the branch. The staged Flat 13513 came from 0b9f230; the accepted 74f0793 source adds the optional sensor preview without an intervening staged APK. An APK built from 74f0793 is therefore a private pre-join comparison fixture, not a claim about the version on a person's phone. Compare the joined APK against both the staged artifact and that source baseline, and name inherited differences separately.

Cold and warm launch are separate controls. A secondary real launcher that shares KDE Connect's default task affinity can return to the warm KDE Connect activity even when the intent names the Flat activity. A separate function affinity fixes that routing while retaining the existing component, icon, label and service. Check the actual resumed component; the substring HeadsetActivity also matches StandaloneHeadsetActivity and is not a sufficient assertion.


The joined candidate passes 94 offline controls and both cold/warm function entries. Actual acquisition calls for tracked → flat → tracked contain orientation / no tracking / orientation and the same paired certificate. Each old RDP listener closes before the next session starts. The previous two-application fixture required two identities and pairings; ordinary update to the joined function preserves the existing application's identity and trusted peer. The flat launcher's task affinity is an explicit routing correction, in addition to the shared touch correction, not an unreported unchanged byte.

The joined paired controls repeat both signed-axis mountings, stale/epoch/replay/clock rejection, pause/recenter, consent/revoke/unpair, killed-owner recovery and all three reference-space events. Fourteen thousand seven hundred six accepted samples independently recompute capture time and uncertainty; all differ from receipt time. Sixteen events per reference-space kind map to captured origin transitions with at most 30 ns error. These numbers describe the measured run, not a device performance requirement.

| Symptom | Cause | Fix / how found |
| --- | --- | --- |
| A current-state observer reports no fresh rows despite a live orientation stream | Parsing its complete growing JSON log consumes the 300 ms observation window | Bound the observer to the recent tail; retain the freshness assertion and explicitly wait for calibrated readiness. The recorded failed check had an empty row set, while subsequent raw records showed valid orientation. |
| Revoke followed by a fixture Back leaves no Connect button | Product revocation already ended the viewer and returned to its controller; Back then left that page | Navigate from the named function entry after revoke; do not treat the wrong-page UI attempt as a product failure. |
| Non-root emulator or adb fails after copying an SDK into a retained image | Docker COPY made a group-only directory root-owned | Preserve uid 1000 ownership for SDK/JDK and emulator files in the image. Prove the fresh no-network rerun rather than relying on a manually repaired container. |

The optional flat preview's touch proof uses a private pre-join source build, with its existing preference on. A real tap yields zero production requestRecenter method entries before the correction and one after; an outside tap yields zero and no remote mouse event. Returning the preference to its default off hides the local status control and retains the same flat descriptor without a tracking field. The tracked paired test separately proves origin/status delivery; a local callback observation alone does not establish a pose channel in flat mode.

Retain compiled binaries, exact package/APK hashes and a fresh factory-userdata launcher for independent review. The no-build replay pairs through actual UI and daemon acceptance, checks the held owner-message red and successor name/fallback/clear, both cold/warm function entries and stop/start with one pairing. Never retain a seeded pairing as proof. A completed fresh-image replay checks the tool permissions and bootstrap as well as the product; a manually repaired running container does not qualify the saved image.


## Depth from the engine

The edition's runtime must use the session window output's final KWin limits without a class multiplier, strength or absolute-depth override.
KWin already tailors those numbers to the screen; multiplying a headset announcement by 2.5 again applies the headset adjustment twice.
Use libstereo-declare's conversion, not a copied formula.
In 1.12.1, `stereo_depth_wayland_get_buffer_limits` uses the selected surface's output width when protocol version 6 supplies it; the older display-wide helper is ambiguous on multiple outputs.
Watch the window's actual output and settings changes, and retain no guessed announcement when either is unavailable.
The held +8 legacy resolver retains its current camera rig when no announcement exists; its first rig is the existing default.
That is not proof of flat rendering or of current limits, and the person must be told through the edition's failure engine.

| Symptom | Cause | Fix or required action; how found |
| --- | --- | --- |
| Linking the required declaration library fails the runtime's soname gate | DisplayXR's `scripts/package_deb_linux.sh` permits only a list of dependencies whose package names it qualifies across Ubuntu releases; `libstereo-declare.so.1` is not on that list | Report the gate conflict before changing its policy. A compiled call to staged 1.12.1 returned 10/4 unchanged, while the verbatim soname subgate rejected its ELF with exit 1. The held +8 runtime passed that subgate. No package or rendered-eye qualification follows from this dependency probe. |
| An older skill says the runtime publishes X11 limits, but the held package has no publisher | The skill described an earlier prototype whose reader is absent from the source used for the held package | Search the exact applied source and trace the production caller; a decoder test or a standalone publisher does not establish session-window delivery. |

The dependency blocker remains unresolved in this record.
No static copy, runtime lookup or gate exemption was introduced to make the check pass.


### Edition depth successor

The native Linux compositor owns one observer per session window. Its worker owns the library's Wayland queue state or X11 connection and stops before the window is destroyed. `stereo_depth_*_get_buffer_limits` converts to the solver's 1920-wide coordinates using the displayed width of one eye. No second output-class factor or strength is applied. Output movement and live settings must be tested on the window, not against a fabricated process-global announcement.

A missing announcement retains the current camera rig and creates a per-window problem through sparky-stereo-problems; recovery and session destruction clear it. Do not describe this as necessarily flat: a previous camera rig can remain. Native sample checks and a direct held-resolver comparison are distinct evidence; the held +8 package had no production announcement publisher.

| Symptom | Cause | Fix and how found |
| --- | --- | --- |
| Required edition library is rejected by upstream's archive soname gate | The upstream list qualifies Ubuntu dependencies, while this edition links libstereo-declare | Carry one edition-only patch adding libstereo-declare.so.1, a versioned Depends, and the unchanged edition archive link/start gate. The old gate rejects a linked ELF, the new list accepts it, and an unrelated soname is still rejected. |
| A fullscreen test window appears not to follow output limits | XMoveWindow did not move the managed fullscreen window | Use the standard fullscreen-monitor request and verify actual coordinates. Only then compare per-window announcements. |
| Incremental build refuses an edited source after projection | Lean records the authored inputs of its projection | Commit the correction, refresh the carried patch and recipe pin, and build a fresh projection. Never edit projected source to evade the check. |
| Vulkan sample headers do not match the sample's extension names | The standalone sample pins a newer displayxr-common than the runtime source component | Build the sample against its own declared dependency tag; leave the runtime's component intact. The sample's CMake pin and upstream tag identify the matching header. |
