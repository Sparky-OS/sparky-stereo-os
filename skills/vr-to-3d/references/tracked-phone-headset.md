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

The receiver checks freshness even while no network event arrives. At 100 ms it pauses and invalidates; at 250 ms it reports unavailable. Recovery from stale input requires three fresh readings. Revocation or disconnect invalidates, releases held actions and unregisters the source. A new session must redo the peer/lease authorization, epoch negotiation and clock calibration; neither pairing alone nor a cached valid quaternion permits reuse of the old registration. Production reconnect through the OpenXR consumer remains a required integration test.

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
