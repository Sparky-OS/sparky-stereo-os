# A library that shares the program's Wayland connection

**For** anyone who writes or changes a library that a program hands its `wl_display` (libstereo-declare, a toolkit plug-in, a video output, an EGL platform): what such a library may bind there, what the compositor then sends the program, why proxy tags do not save a program that does not check them, how a connection of the library's own replaces the binding, how to tell a surface made at a dead surface's address, and the matrix that proves a change on every program that loads the library.
Written from queue row 835 (November 2026): with libstereo-declare 1.12.1 the edition's mpv died at its first frame, on every file.

## What a library may bind on a program's connection

- **Objects the program never meets in its own listeners.** A global bound on the program's connection is a resource of the program's client in the compositor, and some events name every resource of that client.
  The one met here: `wl_surface.enter` and `leave` name a `wl_output`, and a compositor sends them for each `wl_output` resource the client holds for the output the surface is on (Stereo KWin's enter named the library's output first in the red trace; the test compositor of row 835 sends one per resource).
  So a library that binds `wl_output` on the program's connection makes the program's own surface listener receive an output proxy the program never created.
- **What the program then does with it is the program's code.** Qt looks the output up in its own list and ignores what it does not find (VLC Stereo, which initialises the library on Qt's display, met the library's output in five enter events with 1.12.1 and played on); mpv 0.41 set its current output to NULL and dereferenced it in a log line: SIGSEGV in `surface_handle_enter` (`video/out/wayland_common.c`) at the first frame, 2D files too.
- **Objects that carry no events naming other objects are safe** to make on the program's connection: the declaration (`kde_stereo_content_v1`), a depth follower (`kde_stereo_depth_v1`), a content type, on surfaces the program hands over.
- **Proxy tags are a guard, not a remedy.** `wl_proxy_set_tag()` and `wl_proxy_get_tag()` (libwayland 1.18 and later) let a program mark its own proxies and skip the others; SDL 3 does so for its outputs. A program that never reads tags (mpv 0.41) is not protected by the library's tags, and a library cannot tag the program's objects for it. So the repair belongs in the library: bind nothing there.

## A connection of the library's own

What the library needs from the outputs is not tied to the program's surfaces (a display-wide width), so it can come from a second connection to the same compositor:

1. The address: `getpeername(wl_display_get_fd(program_display))` gives the socket path the program is connected to (a `sockaddr_un`).
2. Connect a new `AF_UNIX` stream socket to that address and check with `SO_PEERCRED` that its peer is the same process as the program's peer; another process at that path is not the program's compositor.
3. `wl_display_connect_to_fd()` takes the descriptor (and closes it on failure); bind the outputs there, on its default queue.
4. Read it only inside the library's own call, with a bounded round trip: `wl_display_sync`, then `prepare_read`, `flush`, `poll` with the time left, `read_events`, `dispatch_pending`, until the callback is done; one more round when an output was bound in the last one (its first `mode` arrives before the next sync's `done`).
5. On a timeout destroy the sync callback (its listener points into the caller's frame), close the connection, and return an error; the next call connects again.
6. Close it where the program tells the library it is done (`stereo_declare_wayland_finish()`).

Limits, each an error to the caller, never a guess:

- A program connected through a socket pair (`WAYLAND_SOCKET`, as a compositor starts its own helpers) has no address to connect to again: `-ENOTCONN`.
- A compositor that does not answer in time: `-ETIMEDOUT`.
- An in-process test compositor deadlocks against a blocking round trip on the library's own connection: run the test compositor in a child process on a named socket (`wl_display_add_socket` under a temporary `XDG_RUNTIME_DIR`).

## A surface made at a dead surface's address

A library that keys its per-surface objects by the `wl_surface` pointer cannot see the program destroy that surface: no event on the declaration says so.
When the program destroys a declared surface without withdrawing it and makes a new one, the allocator often hands the new proxy the dead one's block, and the library then sends `set_content` on the dead surface's declaration: `kde_stereo_content_v1#N: error 0: wl_surface was destroyed before a set_content request`, and the connection ends.

- **Tell them apart by the protocol id** (`wl_proxy_get_id()`), recorded beside the pointer: libwayland frees a client id only when the compositor's `delete_id` arrives and gives a new object the id freed last, so the new surface nearly always has another id. Measured on row 835: the reused address came with a new id in every run (6 of 6 red runs: id 33, then 34).
- On a mismatch, drop the old entry: destroy the library's own objects for it (destructors are valid on an object whose surface is gone), leave alone an object the program lent (it may be gone with its surface), send nothing about the surface.
- Keep the withdrawal by pointer: the program may withdraw after the surface is gone, and reading the id of a dead proxy is a use after free.
- A new surface with the same address and the same id cannot be told from the same surface; the program's obligation to withdraw first stays in the API.

## The matrix recipe

1. **The red row first,** on the published library and the round's: start the program on a 2D and a 3D file with `WAYLAND_DEBUG=client` and read the binds and the enter events:
   ```sh
   grep -n -E 'bind\(.*"wl_output"|wl_surface#[0-9]+\.enter|kde_stereo_content_v1#[0-9]+\.set_content' wire.log
   ```
   Red is two `wl_output` binds on `{Default Queue}` (the program's and the library's) and an `enter` naming the library's.
2. **The backtrace** under gdb in the container (`gdb -batch -ex run -ex 'thread apply all bt 25' --args PROGRAM`) with the program's debug symbols installed.
3. **Find the programs that can meet it:** the binaries that import the library's Wayland entry point (`nm -D --undefined-only BINARY | grep stereo_declare_wayland_init`), minus those whose enter handler is a toolkit's that looks outputs up (Qt); read the rest's enter handler, or run them.
4. **Each such program to its first frame** with the old and the new library (the new one through `LD_LIBRARY_PATH` first, then installed), and the player with and without its own guard: {old library, new library} x {player without the guard, with it}, 2D and 3D, on each card.
5. **The answers that must not change:** a mapped window (an xdg toplevel with a buffer: a bare surface gets no limits) prints every depth function's answer, on one output, one output in its 3D mode and two outputs with one in 3D, with the old and the new library; the answers must be equal line for line.
6. **The library's own suite** gains a plain client with its own `wl_surface.enter` listener that aborts on an output it did not bind, against a compositor in another process; it must fail on the old library.

## Traps of row 835

- **Symptom:** mpv dies with SIGSEGV in `surface_handle_enter` at `video/out/wayland_common.c:1683` at its first frame, every file, with libstereo-declare 1.11.0 to 1.12.1; the wire's last line is `wl_surface#6.enter(wl_output#35)`, the library's output. **Cause:** the library bound `wl_output` on mpv's connection. **Fix:** libstereo-declare 1.12.2 binds no output there (the outputs come from its own connection), and mpv +stereo3d11 carries upstream's guard. **How found:** `WAYLAND_DEBUG=client` showed two binds on one queue and the enter naming the second; gdb showed thread `vo` in `surface_handle_enter` from `wl_display_dispatch_queue_pending`.
- **Symptom:** upstream mpv's f4d13e1c2c91 does not apply to 0.41.0 (`dpkg-source` patches at fuzz 0 and stops). **Cause:** it is built on an earlier upstream commit, 3847a8157f6e "wayland: handle all outputs disappearing without segfaulting", which removed the enter handler's early return and changed `update_output_geometry()`'s arguments. **Fix:** carry both, in order, each as it is (both apply at fuzz 0 on the edition's +stereo3d10 tree). **How found:** `git log -S` for the guard's text between the release tag and the commit, in a partial clone (`--filter=blob:none`).
- **Symptom:** a test of the reused address never reuses it ("no new surface was made at a destroyed surface's address"). **Cause:** a round trip between the destroy and the next create let libwayland's sync callback take the freed block. **Fix:** create the next surface at once, as a program does. **How found:** the test's own count of reuses, then the pointer and id log.
- **Symptom:** the Mesa lane's `never-withdrawn` order never fails under `WAYLAND_DEBUG`. **Cause:** the debug log's allocations move the heap, so no address is reused. **Fix:** log each declared surface's pointer and id from a small preloaded wrapper of the library's declare call instead.
- **Symptom:** a row "two outputs, one in a 3D mode" reads the same as the 2D row. **Cause:** the script took the first mode with `3D` in its name from all outputs, which belonged to the other output, and `kscreen-doctor` exits 0 on a mode id the output does not have. **Fix:** read only the named output's block of `kscreen-doctor -o`, and read back the current mode (`*`) before using the row.
- **Symptom:** a package build stops at `apt-get build-dep` with `Packages were downgraded and -y was used without --allow-downgrades` (Mesa). **Cause:** the builder image had been upgraded from the round's pool, and the recipe offers only the published tree. **Fix:** a builder image from the dated snapshot alone; the recipe adds the sources it builds against.
