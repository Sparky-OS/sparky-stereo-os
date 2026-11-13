# Trying a vendor's closed program on the edition

**For** a maintainer who was asked to test a closed program on the edition and report back to its vendor: the program stays the vendor's, the edition only links to it, and the result is a step list a person can follow plus two lists, what we do on our side and what we would suggest to them.

Written on 2026-11-13 from one such test: an industrial automation runtime with a web client, whose engineering tools run on Windows and whose runtime runs on Linux and in containers.
Nothing of the vendor's is packaged, mirrored, modified or decompiled; the edition's repository hosts only what the edition changes, so an unmodified program is a link in the app center.

## Working recipe

1. **Their terms first.**
   Read the licence agreement and the documentation pages on installation, editions and licensing before any download, and save each page with its version date.
   Look for four clauses: what "use" covers (copies, back-ups, separating components), reverse engineering, whether tests and evaluations by an end user are allowed, and what the installation consents to (transmitted data, automatic updates).
   Write down which clause allows each step you plan, and run the program only inside a container or a virtual machine without a route you do not need.
2. **Find what a person can get without filling a form.**
   A download page that asks for a name and an address, and a free edition whose serial number arrives by mail, are registrations: do not fill them from a test rig, record exactly what they ask, and go on with what the vendor publishes openly (a container image, a public repository, downloadable examples in the documentation).
   Say in the report which licence state the test ran in (for instance an evaluation mode with a session limit).
3. **Read the vendor's Linux route to its end before starting.**
   A "Linux deployment" page can end in a step done from a Windows program (installing the product files, uploading and starting a solution).
   Follow the route as far as a Linux-only person can and write down the first step that needs another operating system, with the page's own sentence.
4. **Install after the system, as a person would.**
   A fresh installation of the edition in a virtual machine (the installer, then the first full upgrade from the published repository), then the program by the vendor's own instructions.
   Record every command, every extra package (name, source, version, how it was checked with `apt-cache policy`), every message.
   Prefer what the edition already has: when a container engine is already installed, use it before adding another.
5. **Run a sample of theirs.**
   Prefer the vendor's own examples and templates over anything of ours, and test which of them the Linux build accepts: a loop that starts each example and reads the first line of the log sorts them in minutes.
   Read the program's own health and information endpoints and keep their answers.
6. **Timing on two kernel flavours.**
   Same virtual machine settings for both flavours; the program's own diagnostics by their own names (a task's run counter, last and peak duration, the interval between runs against its period) beside an independent measure under the same load (`cyclictest` from rt-tests, with `hackbench` as the load), several runs each, the spread reported, the host's load written beside every figure.
   A virtual machine shows that the flavour installs, boots and runs the program; its latency figures include the host's scheduling of the virtual processors and say little about a real machine. Say so in the same paragraph as the figures.
7. **The screenshot is the whole desktop.**
   The program beside the system information page (the edition's name, the kernel's name, the panel clock with the date), so the reader sees where it runs; a plain 2D screenshot is a PNG, and a stereo capture carries its format's own mark.
8. **The app center entry is a link.**
   A card with the vendor's own name for the product, one sentence in their own words, a note that the download, the licence and any registration are theirs, and their page's address; every language file the package carries gets the note, or the page fails in the languages left out.
9. **Two lists.**
   Ours: what the edition does or could do (a post-install step list, a package, a default).
   Theirs: what only the vendor can change, each as a measured fact with its message and the page it differs from, without a severity; anything that looks like a security matter goes through their private route only.
10. **Remove their files afterwards:** the image, the examples, the virtual disk; keep the page copies, the logs and the checksums.

## Traps

- **Symptom:** the page that describes the Linux installation ends with "install the product from the management program on Windows", and a Linux-only test stops there.
  **Cause:** the public Linux download is only a bootstrap service; the product files are copied by the Windows tool.
  **Fix:** the vendor's container image holds the whole Linux layout; use it as published, and report the bootstrap route as needing Windows.
  **How found:** reading the deployment page to its last step, then listing the public repository (it held the service's files and nothing of the runtime).
- **Symptom:** almost every downloadable example is refused at start with a message that it targets Windows.
  **Cause:** examples are saved for the Windows runtime, and the Linux runtime refuses them by design.
  **Fix:** start every example once and keep the ones that are accepted; say how many of how many.
  **How found:** the refusal is the first line of the start log, so a 40-second timeout per example is enough.
- **Symptom:** the vendor's headless authoring tool starts on Linux and writes its files, and its build step answers that a program "was not found" and asks for the Windows binaries.
  **Cause:** the builder it calls ships only for Windows.
  **Fix:** none on our side; it goes on the vendor's list with the exact message. Do not unpack the Windows installer to get it: the licence forbids separating components.
  **How found:** the tool's own error text names the file and the folders it searched.
- **Symptom:** a documented REST read of a tag answers "not found" although the tag is in the example.
  **Cause:** the interface serves only data marked public and hides the rest behind the same answer as a missing name; the examples' data is not public, and changing that needs the Windows designer.
  **Fix:** read what the anonymous user may read (run counters, durations, server information), and say plainly that the tags themselves were not reachable.
  **How found:** the same call succeeded for the runtime's own objects and failed for every tag, including names taken from the vendor's own example page.
- **Symptom:** a login that the documentation says needs a password succeeds for the built-in anonymous user with any text.
  **Cause:** the anonymous user has no password by design, and the interface only requires the field to be non-empty.
  **Fix:** treat it as their design unless their pages say otherwise; write the difference between the page and the behaviour on their list as a fact, never try it against a system that is not your own test instance.
  **How found:** a wrong password is refused for the administrator and accepted for the anonymous user on the same local instance.
- **Symptom:** the scratch folder passes its size limit during the installation.
  **Cause:** an installed desktop edition is larger than the limit by itself (16 GiB here), and the installer image sits beside it until the installation ends.
  **Fix:** remove the installer image the moment the installation finishes, run `fstrim` in the guest after the first upgrade, and say in the hand-back that the limit could not hold.
  **How found:** `du` on the scratch folder at 9 % of the installation.
- **Symptom:** a `docker exec` with a script on standard input prints nothing.
  **Cause:** `exec` without `-i` gives the process no input; and the vendor's image had no shell tools to probe with.
  **Fix:** probe from a second container that shares the first one's network (`--network container:NAME`) with an image that has Python.
- **Symptom:** a first full upgrade of a fresh installation takes most of an hour in a virtual machine while other work loads the host.
  **Cause:** hundreds of packages, kernel images and module builds, on four virtual processors.
  **Fix:** start it in the background with its log in the guest, and write the deliverables that do not need the guest meanwhile.

## What to hand back

The step list as run, the versions and checksums, which licence state the test ran in, the two lists, the screenshots' paths with which are from a virtual machine, and what was not proven (anything a real machine, the vendor's Windows tools or a registration would have been needed for).
