# A diagnostic build with sanitizers of a program that draws through Stereo KWin

Written on 2026-11-21 from queue row 762c: an OpenXR sample on the edition's DisplayXR runtime aborted now and then at start with glibc's `malloc(): unaligned tcache chunk detected`.
The cause turned out to be in a system library the sanitizers do not instrument, so this page says what a sanitizer build can and cannot show, and which tool found the write when it could not.
The fault itself, with its fix, is in [vr-to-3d: the runtime's start-up heap fault](../../vr-to-3d/references/openxr-runtime-startup-heap-fault.md).

## Working recipe

1. **Reduce the route, keep the fault.** Start the rig's compositor once (`kwin_wayland --virtual --xwayland --output-count 2 --width 1920 --height 1080`; the second output stands in for a phone's or a projector's panel where the program puts its window) and start the program many times inside it with the route's exact environment, each held a few seconds and ended with SIGTERM as the route ends it.
   The reduced case is the same fault when the program prints the same message at the same place (the same last log line).
   Keep each start's log and exit status: 124 from `timeout` is a normal end, 134 is SIGABRT, 139 is SIGSEGV.
2. **Count under the load that shows it.** A race needs the right preemption.
   Busy loops inside the container's own CPU quota (`--cpus 4` plus four `while :` loops) showed 0 aborts in 22 starts, because the quota throttles every thread of the container together.
   Pinning the container to two CPUs (`--cpuset-cpus 10,11`, nothing else added) showed 2 to 4 in 40, and so did unrelated work elsewhere on the machine.
   Record what else ran beside each count (a build, an apt install, another lane's rig): it changes the rate.
3. **Build the sanitizer variant of everything of ours that runs in the process,** from the authored source (not a Lean Code projection, so reports name real lines) with the package's own CMake options plus `-fsanitize=address,undefined -fno-omit-frame-pointer -g` and `-O1`:
   - the program;
   - the in-process runtime library, its plug-ins (found next to the library) and its Vulkan layer (found through its installed JSON): lay the sanitizer files over the installed ones in an image of your own made from the rig image, never on the base itself;
   - the sample's helper library at the tag the sample pins (DisplayXR's cube needs `displayxr-common` v2.29.0, not the runtime's own older component).
4. **Run it with the sanitizer runtime first.** When the rig preloads an observer library, put `libasan.so.8` before it in `LD_PRELOAD`, or ASan stops with "runtime does not come first".
   `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:malloc_context_size=40:verify_asan_link_order=0` and `UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=0` (a driver's own leaks and benign UB reports otherwise stop the run).
5. **When the sanitizers stay silent, change tools, not the counts:**
   - `gdb -batch -ex run -ex 'thread apply all bt 40'` on each start prints every thread at the fatal signal. It is slow at thread creation and library loading, so it hides some races; it caught one abort in 20 starts with two CPUs pinned, and that one showed which other thread was active.
   - A crash-trace preload (a SIGSEGV/SIGABRT handler on an alternate stack that writes the thread id, registers, `backtrace_symbols_fd()` and `/proc/self/maps`, with `backtrace()` called once in the constructor so the handler never allocates) disturbs the timing less than gdb.
   - Valgrind's memcheck instruments every library, also the ones the compiler did not; with `--undef-value-errors=no --fair-sched=yes` the GPU driver's noise stays out. Install the matching `-dbgsym` packages from Debian's debug archive (`deb https://deb.debian.org/debian-debug testing-debug main`, pinned to the installed versions) to get function names and lines in the system libraries.
6. **Prove a library cause outside the program.** A small program that does only what the stacks show (here: threads that each open an X display, query RandR and close it) gives a red that needs no compositor patience; build the library's source twice (unchanged, and with the fix) and run both through `LD_LIBRARY_PATH` in the same rig.

## What the sanitizers cannot show

- **A write into freed memory by a library that is not instrumented.** ASan replaces glibc's allocator and keeps freed blocks in quarantine, so such a write lands in a quarantined block, corrupts nothing and is reported by nobody. Measured: 0 aborts and 0 reports in 60 starts of the ASan build, while the plain build aborted in 2 to 4 of 40 under the same load.
- **A race where one side is not instrumented.** TSan sees only instrumented accesses; in three starts it reported one race, a flag read without the lock as a hint and re-checked under it, and nothing about the real fault.
- So the silence of both is a measurement, not a verdict: it says the damaging write is probably in code the compiler did not build, which points to Valgrind.

## Traps

- **Symptom:** a run's script stops with a syntax error, or repeats a line, after a script was edited.
  **Cause:** bash reads a script as it goes; an editor that rewrites the file in place changes the bytes under a run that reads it through a bind mount.
  **Fix:** each run copies the rig scripts into its own folder and mounts that copy; change scripts by writing a new file and renaming it over the old one.
  **Found by:** the proof-rig rule "Never edit a script while it runs", broken once here.
- **Symptom:** `kwin_wayland: Operation not permitted` (exit 126) in the container.
  **Cause:** the packaged binary carries a file capability the container does not grant.
  **Fix:** run a plain copy of the same binary (`cmp` shows it is the same file).
- **Symptom:** DisplayXR's `package_deb_linux.sh --no-build` stops with "DT_NEEDED on system libraries not known to share a package name ... libasan.so.8 libubsan.so.1".
  **Cause:** its portability check refuses the sanitizer runtimes.
  **Fix:** expected for a diagnostic build: the tree is already laid out under the dist folder when it stops; take the libraries, plug-ins and layer JSON from there and accept only that one refusal.
- **Symptom:** gdb prints "Error disabling address space randomization: Operation not permitted".
  **Cause:** Docker's seccomp profile refuses the personality call.
  **Fix:** none needed for a backtrace; the run keeps its normal randomisation.
- **Symptom:** a busy-loop load in the container never brings the fault out, while unrelated work on the machine does.
  **Cause:** the CFS quota throttles the whole container together instead of preempting threads one at a time.
  **Fix:** pin the container to fewer CPUs (`--cpuset-cpus`) and record what ran beside it.
- **Symptom:** `coredumpctl list` on the host shows `memcheck-amd64-linux` SIGSEGV records from a container started with `--ulimit core=1`.
  **Cause:** when the program under Valgrind dies of a signal, Valgrind sets its own core limit to 0 before raising the signal again, and the kernel ignores a limit of 0 for a piped core handler, so the host's handler runs (and can notify the desktop).
  **Fix:** a test program that is expected to crash calls `prctl(PR_SET_DUMPABLE, 0)` first; under Valgrind that covers Valgrind too, since they are one process.
  **Found by:** reading `coredumpctl list --since` before the hand-back, then `coredumpctl info PID` for the container's cgroup.
- **Symptom:** the launcher printed no summary, and stopped containers of the lane piled up, their IDs never recorded.
  **Cause:** under `set -e`, `kill "$sampler"; wait "$sampler"` returns the killed job's status (143) and ends the script before `docker inspect` and `docker rm`.
  **Fix:** `wait "$sampler" || true`; list `docker ps -a --filter name=PREFIX` after every series, not only running containers.
  **Found by:** a crash record whose container ID was missing from the lane's ID list.
