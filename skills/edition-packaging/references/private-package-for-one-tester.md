# A private package for one tester

**For** a maintainer who must let one person try a program the edition may not publish: a local `.deb`, proof that it installs and runs in stereo from the live image the tester will start, and one page of steps a Windows user can follow alone.

Written on 2026-11-13 from one such delivery.
The program was a stereo 3D viewer whose authors have not published a licence, built from a private clone, for a tester who works on Windows and does not program.
Nothing of it enters a repository, an index or a public page; the package goes to the tester by a private link.

## Working recipe

1. **Reconcile first.**
   List what exists: the private clone and its build notes, the image the tester will start (its date, its package list, its boot menu), the guides already written for a reader coming from Windows.
   Write down what is missing between those and "the tester can run it alone".
2. **Name and version that cannot collide.**
   Check that the package name has no candidate in any configured archive (`apt-cache policy NAME` in the build container prints no candidate).
   Use a version that sorts below every real release and says what it is: `0+private1`.
   A later real package replaces it by an ordinary upgrade.
3. **Packaging beside the authors' files, never in them.**
   Add a `debian/` folder on a local branch of the private clone, commit there, push nothing.
   `debian/copyright` says the truth: the authors as copyright holders, `License: none` with one sentence saying that no licence has been published, that the build is private and that it must not be passed on.
   The package description says the same in its last paragraph.
   No `Bugs:` field pointing at a public tracker.
   Leave out anything the authors' tree carries under a third party's agreement (a vendor's device kit): check the built package with `dpkg-deb -c` and `strings` on the binary.
4. **A launcher when the program reads from its working directory.**
   A program that opens `assets/` by relative path and writes its preferences beside them cannot run from `/usr/share`.
   Install the data under `/usr/share/NAME`, the binary under `/usr/lib/NAME`, and a small `/usr/bin/NAME` script that makes `${XDG_DATA_HOME:-$HOME/.local/share}/NAME`, links the read-only folders into it, copies the writable defaults once and starts the program there.
   The desktop entry runs the launcher.
5. **Dependencies as `Depends`, the stereo ones versioned.**
   `${shlibs:Depends}` gives the library names.
   Add by hand what the linker cannot know: the compositor and the graphics library at the versions the proof ran on, the stereo build of the windowing library at its own version, and the dialog program the file dialogs call.
   Look every name up first, as [the skill](../SKILL.md#names-and-sources-are-checked-before-they-are-written-down) says.
6. **Build in a container against the published repository,** with no network during the build, as the lane user.
   Read Lintian's report and list its findings; a private package of somebody else's tree will have some (a font in a non-font package, a file that is not UTF-8, no manual page), and none of them is corrected in the authors' files.
7. **Prove it the way the tester will do it,** in a virtual machine started from the same image file, as a USB disk, under UEFI with Secure Boot on and the edition's key not enrolled.
   Drive the guest through QEMU's QMP socket only (`screendump`, `send-key`, `input-send-event`); the build repository's `sparky-os/iso-build/boot-matrix/vmctl.py` and `typede.py` do it.
   Hand the file to the guest the way the download place will: a small web server on the host's loopback address, which the guest reaches at `10.0.2.2` through QEMU's user networking, opened in the guest's own browser.
   Type the page's command exactly as printed, start the program from the application menu, choose the screen's 3D mode in Display Configuration, and read the scanout with `screendump`.
8. **Measure, do not look.**
   With the output in side by side full, the scanout is twice as wide and holds both eyes, left first.
   Give the program a scene with objects at known distances and compare each object's disparity with the closed form of its cameras ([stereo-two-cameras](../../stereo-two-cameras/SKILL.md)).
   Controls that must fail: the same capture in a 2D mode (one picture), and the output's own "Swap left and right eyes", which must reverse every sign.
   The interface (menu bar, panels) must be the same picture in both eyes.
9. **Write the one page from the run, not from memory.**
   Every label on the page is copied from a capture of the run, every command is the one that was typed, every picture is a crop of a capture.
   Say on the page what was tested and what was not (a real notebook, the tester's own screens).
10. **Hand over three things:** the `.deb`, the page as a PDF, and a checksum file; with them, the sentences for the message that carries the one link.
    Check with `cmp` that the file handed over is the file the run installed.

## What the one page must carry

- One sentence saying what the program is and that nothing is written to the computer's disk.
- What the reader needs, in one line: the computer, the internet, a stick, the time, the files; and the screens the reader has, named, with nothing to buy.
- **Step 1, before anything else: the BitLocker recovery key,** with why, Microsoft's own page, and a check ("you can read the key on paper or on your phone"). Then: change nothing in the firmware settings, leave Secure Boot on. See [writing-front-pages](../../writing-front-pages/SKILL.md).
- The stick, the start from the stick, the key enrolment when the image needs it, the menu entry to choose.
- The download, the install, the start, the 3D mode for each of the reader's screens, how to stop and return to Windows.
- What the reader sees when a step fails, and what to do: no internet, no stereo window, eyes reversed, a device the build does not support.
- That the live session keeps nothing, in the step where it matters, and which steps are repeated next time.
- How to tell the maker what happened, in three lines.
- Five to ten steps, a picture for each step that shows a screen, plain words, no code names, no marks of a text format, one link.

## Traps met, each with symptom, cause, fix and how the cause was found

- **Symptom:** the packaged program starts, loads its scene and stops before its first frame with `Assertion ... failed` from its interface library, while the same source built by hand runs.
  **Cause:** debhelper's CMake build leaves the build type empty, so `NDEBUG` is not defined and every `assert()` is compiled in; the authors only ever build Release, and one assertion does not hold in their own main loop.
  **Fix:** `override_dh_auto_configure: dh_auto_configure -- -DCMAKE_BUILD_TYPE=Release`, with a comment saying why.
  **Found by:** starting the program from a terminal in the guest with its output in a file, and sending the file back to the host; the last line named the assertion.
- **Symptom:** in the live session `sudo apt install ./FILE.deb` answers that four dependencies are "not installable" and installs nothing.
  **Cause:** the image ships without apt's package lists, so apt knows no package that is not already installed.
  **Fix:** the page gives two lines, `sudo apt update` and then the install; say that the internet is needed, and what the reader sees without it.
  **Found by:** `ls /var/lib/apt/lists` in the guest (empty but for `partial`), then the same install after `apt update`.
- **Symptom:** the install needs the network although the `.deb` is local.
  **Cause:** some of its libraries are not on the image.
  **Fix:** before writing the page, compare the package's `Depends` with the image's published package list; either accept the download and say so, or hand over the missing `.deb` files too.
  **Found by:** `grep` of the dependency names in the package list published beside the image.
- **Symptom:** `${shlibs:Depends}` asks only for `libglfw3 (>= 3.3)`, which any archive's build satisfies.
  **Cause:** the library's symbols file knows nothing of the edition's stereo window.
  **Fix:** a second, explicit entry with the edition's version (`libglfw3 (>= 3.5.1-1+stereo3d3~)`); dpkg merges the two.
  **Found by:** reading `dpkg-deb -f FILE.deb Depends`.
- **Symptom:** the build image fails with `Unable to satisfy dependencies ... libavcodec ... libaom3 ... [no choices]` when a runtime-only dependency (a dialog program) is added to its package list.
  **Cause:** that program pulls the media stack, which the edition's repository builds on another archive that the image does not have as a source.
  **Fix:** check a runtime-only name with `apt-cache policy` and do not install it in the build image.
  **Found by:** apt's own explanation of the conflict.
- **Symptom:** the packaging commit carries hundreds of megabytes.
  **Cause:** `debian/.debhelper`, `debian/files`, the staging folder `debian/NAME` and the build folder were left by the build and added with `git add debian`.
  **Fix:** remove them, add a `debian/.gitignore`, amend; check with `git show --stat`.
- **Symptom:** with Secure Boot on, the image shows a text in ten languages and returns to its menu instead of starting.
  **Cause:** an image that carries only the edition's kernel cannot start under Secure Boot until the edition's key is enrolled; there is no second kernel to fall back on.
  **Fix:** the page has a step for the enrolment with the choices in order, as the image's own text lists them, and says that it is done once per computer.
  In the rig: the distribution's OVMF with Secure Boot and Microsoft's keys (`OVMF_CODE_4M.secboot.fd`, a private copy of `OVMF_VARS_4M.ms.fd`, `-machine q35,smm=on`, `-global driver=cfi.pflash01,property=secure,value=on`), no `-no-reboot`, so the guest restarts into the stick after the enrolment.
  **Found by:** the first `screendump` after choosing the live entry.
- **Symptom:** the command typed into the guest comes out with other characters (`-` for `/`, `z` for `y`).
  **Cause:** QMP's `send-key` presses physical keys; a live entry in another language has another keyboard layout.
  **Fix:** type with a layout-aware helper (`typede.py` for the German layout), and tell the reader to choose the live entry of the keyboard they own, because the command must be typed.
- **Symptom:** text typed while apt is still running ends up inside apt's answer or in the log file.
  **Cause:** the terminal reads ahead.
  **Fix:** wait for the prompt (a capture shows it) before typing the next line.
- **Symptom:** typing the first word of a settings page in the application menu and pressing Enter opens another program.
  **Cause:** the menu ranks applications before settings pages.
  **Fix:** the page prints the full name of the settings page and says to click the line with that name; prove it with a capture of the search result.
- **Symptom:** after "Apply" on a 3D mode, a click on the "keep" button does nothing and the mode goes back.
  **Cause:** in the rig, the pointer position sent through QMP did not land on the button while the output was in the 3D mode (not investigated further); for a person, the dialog simply times out.
  **Fix:** in the rig use the button's keyboard shortcut; on the page say that the screen goes back by itself when the button is not clicked at once.
- **Symptom:** the prediction is off by a few percent.
  **Cause:** the program's viewport is not what the capture suggests: its window was 1080 high under a title bar on a 1080 high screen, so part of it was below the screen, and the cameras use the window's own size.
  **Fix:** take the viewport height from an object of known angular size in the capture (a square of side `s` at distance `Z` is `s / Z * vh / (2 tan(fovy / 2))` pixels high), then predict the disparity with that height.
- **Symptom:** nothing of the first session is there after a restart.
  **Cause:** a live session without a persistence entry in its boot menu keeps its changes in memory.
  **Fix:** prove it (reset the guest, `dpkg -l NAME` says the package is not found) and say on the page which steps are repeated.
- **Symptom:** the one command on the PDF is broken over two lines.
  **Cause:** the column is narrower than the command in a fixed-width font.
  **Fix:** print two short commands instead of one joined with `&&`, each on a line of its own, and look at the rendered page; a reader types a line break as it shows.
- **Symptom:** the PDF's text is smaller than the style sheet says.
  **Cause:** PyMuPDF's `insert_htmlbox` shrinks text to fit its rectangle and only reports it in its return value.
  **Fix:** measure each block first (a tall scratch rectangle, the returned spare height), lay the blocks out from the measured heights, and fail the build when the returned scale is below 1.

## Perks

- The image's package list, published beside the image, answers "is this library already there?" without starting anything.
- A red and cyan output needs no second proof run of the geometry: in the anaglyph mode the left eye's objects sit in the red channel and the right eye's in green and blue, at the positions the side by side capture showed.
- The guest can hand files back with `curl -T FILE http://10.0.2.2:PORT/NAME` when the host's small server accepts PUT into an inbox folder; versions, apt's history and the program's log arrive as text, not as pictures of text.
- A virtual machine has no graphics card, so the program runs on the software renderer at about one frame a second; that is enough for geometry and says nothing about a real card.

## What this proof does not show

A real notebook's firmware and its one-time start menu, a wireless network, a real graphics card, the tester's own screens and glasses, and any device the build leaves out.
Say so on the page and in the hand-back.
