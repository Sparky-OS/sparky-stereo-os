# A 3D mouse in a stereo program on Linux: libspnav, spacenavd, and a simulated device for a test

Measured on 2026-11-13 with the edition's build of KDAB's Stereo Demonstrator (`stereo3ddemo` 0.3.1+git20250303.4f99a5d+dfsg+stereo3d3), Debian testing's `libspnav0` 1.2-2 and `spacenavd` 1.3.1-1, under Stereo KWin in a container on an NVIDIA card and in a virtual machine started from the edition's live image.
No real 3D mouse was connected at any point: everything below was proved with a simulated device, and the last section says what that leaves open.

## The parts, and who wrote them

- **The device** is a six-axis controller (three translations, three rotations) with buttons. On Linux the kernel shows a USB one as an ordinary input device under `/dev/input`.
- **spacenavd** (John Tsiombikas, GPL-3.0-or-later per Debian's copyright file) is the daemon. It reads the device, applies its own sensitivity, dead zone and axis map, and serves events on the socket `/var/run/spnav.sock`. Its systemd unit is `spacenavd.service`.
- **libspnav** (John Tsiombikas, BSD-3-Clause per Debian's copyright file) is the client library. `spnav_open()` connects to that socket, `spnav_wait_event()` and `spnav_poll_event()` return motion and button events, `spnav_fd()` gives the descriptor for an event loop.
- **A vendor kit on other systems.** On Windows and macOS a program usually links the device maker's own kit (3Dconnexion's 3DxWare SDK with its Navlib component), which talks to the maker's driver. That kit is handed out through the maker's developer program and is not free software. A program can carry both routes behind a build switch, as the demonstrator does: `WITH_NAVLIB` on Windows and macOS, `WITH_SPNAV` when CMake finds libspnav on Linux.
  A free package leaves the kit's folder out of its source (`Files-Excluded` in `debian/copyright`, `+dfsg` in the version) and builds the libspnav route only.

## The recipe

1. **Read which route the build takes.** `ldd PROGRAM | grep spnav` must show `libspnav.so.0`; `strings PROGRAM | grep -i -c navlib` must be 0 in a free build; `dpkg-deb -c` must list no file of the vendor kit.
2. **Check the package's relations.** `libspnav0` comes as a `Depends` through the shared library; the daemon does not. `apt install PROGRAM` then only lists `spacenavd` under suggested packages, and a person with a 3D mouse has no daemon until they install it.
3. **Prove the program's own code with a stand-in for the daemon**, in the proof rig's container on a GPU ([stereo-proof-rig](../../stereo-proof-rig/SKILL.md)).
   Give the container a writable `/run` (`--tmpfs /run:rw,mode=1777`), start [`scripts/fake-spnavd.py`](../scripts/fake-spnavd.py) on `/var/run/spnav.sock` before the program, and drop a file `go-1` holding `count x y z rx ry rz` into its trigger folder.
   Read the program's own camera values before and after, and compare with what its code predicts (the demonstrator adds 0.001 per unit of translation and 0.0001 rad per unit of rotation: 40 events of x = 25 moved the camera by 1.000, 50 events of ry = 100 turned it by 0.5 rad).
4. **Capture both eyes after each move** and measure them against the same closed-form prediction as before the move ([stereo-two-cameras](../../stereo-two-cameras/SKILL.md)), with the camera position read from the program's log at that moment. A square cut by the edge of the 3D area is not a valid reading: skip it and say so.
5. **Prove the daemon and the kernel side in a virtual machine**, never in a container (see the first trap).
   Install `spacenavd`, check `systemctl is-active spacenavd` and the socket, then create a device with [`scripts/uinput-spacemouse.py`](../scripts/uinput-spacemouse.py): it uses only Python's standard library and the kernel's uinput, and gives the device a SpaceNavigator's USB identity (046d:c626), six relative axes and two buttons.
   `/proc/bus/input/devices` must show it, and a libspnav client ([`scripts/spnav-listen.c`](../scripts/spnav-listen.c), built with `gcc spnav-listen.c /lib/libspnav.so.0`) must name it and print the events.
   Run the client once before the device exists: it must print "(none)", or the test cannot fail.
6. **Then the program itself in that machine**, started after the daemon, with one move from the device and the camera read from its log.
7. **Say what a simulated device does not show** (the last section), in the report and to the person who will plug a real one in.

## Traps

- **Symptom:** a simulated input device made inside a container appears on the desktop of the machine that runs the containers.
  **Cause:** `/dev/uinput` is the host's kernel; a container has no input stack of its own.
  **Fix:** make the device in a virtual machine, whose kernel is its own. In a container use the stand-in daemon instead, which touches nothing but a socket.
  **Found by:** reading what `--device /dev/uinput` would hand over, before running it.
- **Symptom:** the program closes by itself while the view moves under the 3D mouse, with `terminate called after throwing an instance of 'std::runtime_error'` and `Signal is already emitting, nested emits are not supported!`.
  **Cause:** the program polls `spnav_wait_event()` in a thread of its own and writes the camera's properties from that thread, while the window's thread is emitting on the same properties (autofocus answering the camera's move). KDBindings' signals refuse a second emit while one runs (`kdbindings/signal.h`).
  **Fix:** deliver device events on the thread that owns the camera: watch `spnav_fd()` with the toolkit's own notifier (Qt: `QSocketNotifier`) and read with `spnav_poll_event()`, or post each event to that thread (`QMetaObject::invokeMethod` with a queued connection). No fix was built here.
  **Found by:** the message, then the code of the poll thread; and by counting: with autofocus on the program ended in 2 of 4 runs, with autofocus off in 0 of 2, which is how a race looks. One clean run proves nothing about a thread fault: repeat, and vary what the other thread is doing.
- **Symptom:** no 3D mouse is found, and the program says nothing at all.
  **Cause:** `spnav_open()` returned -1 (no daemon on the socket) and the program's only message was a commented-out debug line.
  **Fix:** tell the person in the window that no 3D mouse service was found and which package provides it; nothing fails silently.
  **Found by:** a run without the daemon and an empty log.
- **Symptom:** the daemon is started (or installed) after the program, and the 3D mouse still does nothing.
  **Cause:** the program calls `spnav_open()` once, in a constructor at start.
  **Fix:** start the program after the daemon, and in the program retry the connection or watch for the socket. Found by reading the constructor; not run as a case.
- **Symptom:** a simulated move along one axis keeps moving after the script went on to the next axis; x still grows while only z is sent.
  **Cause:** the device was made with relative axes, the kernel drops a relative event whose value is 0, and spacenavd keeps each axis's last value and sends it again with every report. The script can never say "x is back at rest".
  **Fix:** one device per move (a new device starts at rest), or a device with absolute axes, which can report 0.
  **Found by:** the test client's running sums: x rose by the same step during the z and the rotation moves.
- **Symptom:** the kernel's Z arrives in the client as -y, and RY as -rz.
  **Cause:** spacenavd's default axis map swaps Y and Z and inverts them, for the device's own orientation.
  **Fix:** none needed; predict the program's motion from what the client receives, not from what the script sent. Found by the same sums.
- **Symptom:** the daemon's journal says `Authorization required, but no authorization protocol specified`.
  **Cause:** as root it also tries to reach an X server for its older X11 protocol.
  **Fix:** none; socket clients are served. Do not read it as the reason for a missing device.
- **Symptom:** a stand-in daemon receives 4 bytes (`01 55 aa 7f`) right after the client connects, and 4 more about 300 ms later.
  **Cause:** libspnav 1.x asks the daemon which protocol it speaks and waits for an answer.
  **Fix:** a stand-in that never answers keeps the client on the plain protocol: eight 32-bit integers per event, the first 0 for motion (then x, y, z, rx, ry, rz and the period in milliseconds), 1 for a button press and 2 for a release (then the button's number). A real `spacenavd` 1.3.1 answers, and the client reports protocol 1.
- **Symptom:** the stand-in cannot create its socket.
  **Cause:** the path is fixed (`/var/run/spnav.sock`) and `/run` belongs to root.
  **Fix:** a tmpfs on `/run` in the test container; never change the library's path for a test, or the test no longer runs the shipped code.
- **Symptom:** a control that the design removes still sits in the menu and seems dead.
  A saved "Flipped" (the program's own eye swap) changed nothing in the first picture of the Qt Quick 3D renderer, though the code reads it.
  **Fix:** remove the control in the edition's build (a program that renders its own scene offers no swap; the desktop swaps per output); do not spend a run on why it is dead.

## Perks

- The program logs its camera on every change (`QT_LOGGING_RULES=stereo3ddemo.*=true`), so a move is checked to the last digit without reading a pixel.
- The stand-in daemon and the uinput device need no package beyond Python 3; the test client needs `gcc` and the library the program already depends on.
- `spnav-listen` asks the daemon for the device's name, so one line tells "no daemon", "daemon without a device" and "device seen" apart.

## Found on the way, not about the mouse

- **Symptom:** the program's status line says its two eyes go out through the two-layer swapchain ("Quad buffer: the display stack packs the two eyes"), and both halves of a 3D mode's scanout are pixel-identical.
  Seen in a virtual machine without a graphics card, on a live image with KWin +stereo3d38; the same program on the software Vulkan driver under KWin +stereo3d46 measured right within 0.06 px, and bringing the image's Qt and Qt Quick to the published versions changed nothing.
  **What was proved:** Mesa's software Vulkan hands the compositor a buffer two eyes wide with the declaration, and the program's other route ("Two views side by side (declared)") shows two different eyes in the same session.
  **Not found:** the cause; it is narrowed to that KWin on a real 3D output with the buffers the Vulkan route declares.
  **For the person:** choose the side-by-side route under Advanced. A status line that says 3D is not proof of two eyes: compare the halves.
- **A scanout of a 3D mode is a pair too.** Keep it as a marked picture (PNG with `sTER`, `.pns`) like every other stereo capture, and count the pixels that differ between its halves before trusting any label.

## What a simulated device leaves open

- A real device's USB reports, its buttons beyond two, its LED and its wireless receiver.
- Whether spacenavd's list of known devices covers the model at hand; a device it does not know is not a 3Dconnexion one and needs its own route.
- The feel: sensitivity, dead zone and axis directions as a hand expects them.
- Hot-plug while the program runs.
