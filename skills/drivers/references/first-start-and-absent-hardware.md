# The first start, and hardware that is not there

**For anyone who changes what an installed system does at its first start, or what it installs for hardware:** how to decide Secure Boot from the firmware, a signing step that does nothing where nothing needs a signature, a vendor driver only where its card is, a known machine's firmware table and masked event as table entries, and how each was proved without the machine.
Written 2026-11-25 from five breakage rows found on two installed Intel Macs (a MacBookPro9,2 and an iMac14,1).
Nothing in it was run on those machines: what only they can show is listed at the end.

## Working recipe

1. **Ask the firmware, not your own files.**
   Secure Boot is on when the `SecureBoot` variable of the EFI global GUID holds 1: `/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c`, whose fifth byte is the value (efivarfs puts four attribute bytes first).
   Five answers, and what each means for work that exists only to satisfy Secure Boot:

   | What is read | `mokutil --sb-state` says | State | A signature is needed |
   |---|---|---|---|
   | no `/sys/firmware/efi` | EFI variables are not supported on this system | `bios` | no |
   | variables readable, none named `SecureBoot` | This system doesn't support Secure Boot | `unsupported` | no |
   | value 0 | SecureBoot disabled | `off` | no |
   | value 1 | SecureBoot enabled | `on` | yes |
   | EFI, but the variables cannot be read | (not supported) | `unknown` | yes |

   A state that cannot be read counts as needed: a failed read never weakens the signed path.
   The kernel has its own answer too: `/sys/module/module/parameters/sig_enforce` says `Y` when it refuses unsigned modules, under Secure Boot (`security/integrity/ima/ima_efi.c`, `arch_get_ima_policy`) or because the person set `module.sig_enforce=1`; treat `Y` as needed whatever the firmware says.
   Never decide from the presence of a key file or of a boot entry: both exist on machines that have no Secure Boot.
2. **A step that only signs does nothing where nothing needs a signature.**
   `dkms-sign-unsigned` (the edition's dkms) asks first, says which state it found in its own journal line, builds nothing, and writes no "done" mark, so the first start after Secure Boot is turned on signs.
   It clears what it kept earlier for a module without a signature.
   The build itself is never capped: the cure for a 13 minute build at the first start is no build.
3. **Offer a Secure Boot action only where it can be used.**
   GRUB's enrolment entries are written at `update-grub` only when the firmware has Secure Boot (state `on` or `off`); state `unsupported` gets none and says so; `unknown` (a chroot, a BIOS start) writes them as before.
   Record what the menu was written for, and let a boot-time check write it again when the firmware no longer matches (a disk moved to another computer).
4. **A vendor's driver only where its card is, settled once.**
   The image carries the driver so a machine with the card works at once; a machine without it is settled at its first start, not in the installer (one step then also serves machines already installed, and a disk started on another computer).
   - Read the bus from sysfs: a PCI device with `vendor` 0x10de and `class` 0x03xxxx. The HDMI audio function of a card (class 0x0403) is not a card. A bus that cannot be read is not "no card".
   - Purge the driver's own packages by name (the driver, its modules, its locks and repository package), reading apt's plan first: a plan that would take anything that is not the vendor's, or a vendor package the person installed by name, removes nothing and is kept as a problem that names the package.
   - Then purge what is left of the driver: installed, the vendor's by name, installed automatically, and removable alone. Do not count on `apt autoremove`'s list (see the traps). Never run an autoremove.
   - Keep the firmware the free driver needs, so a card that appears has a picture at once.
   - Do it once (a mark), record the cards seen, and after that remove nothing: a card that leaves takes nothing with it.
   - A card present with no driver at that first settling is left alone, and that is right only because the image always installs the driver: its absence is then the person's doing. An image that did not carry the driver would have to install it there.
   - A card the machine has not shown before gets the driver through the hardware setup, kept and said by the problems engine; nothing is downloaded on a metered connection; the person's earlier choice of the free driver is kept in a file and respected.
   - Every helper of the driver (32-bit libraries, services) asks for a card before it keeps a problem or installs anything.
5. **A known machine's correction is a table entry of a reviewed kind, never a command.**
   - `acpi-table`: the ASL source ships in the package, `iasl` compiles it at build time, an initramfs hook the package owns puts the tables that are on for this model into the boot image's early archive (`kernel/firmware/acpi/`, `prepend_earlyinitramfs`), and records per kernel what it put in. The kernel logs `ACPI: Table Upgrade: install [SSDT-OEMID-TABLEID]` (Documentation/admin-guide/acpi/initrd_table_override.rst).
   - `kernel-option`: one `name=value`, added by a file of the package in `/etc/default/grub.d/` that asks the table at `update-grub` time.
   - Match on the DMI product name only, apply only when not yet in place (`update-initramfs -u -k all`, `update-grub`), tell the session that it takes effect at the next restart, list each correction with what it does, and give the person a switch.
   - Search the kernel first: `grep -rn 'MODEL' drivers/acpi drivers/platform arch` in the tree you ship and in mainline. A quirk in the engine comes first; the table carries what cannot be fixed there.
6. **Do not hold the start, anywhere in the chain.**
   A target waits for every unit it wants that has default dependencies. A oneshot that purges packages or writes boot images at the first start gets `DefaultDependencies=no` (with `After=basic.target`, `Conflicts=` and `Before=shutdown.target` written out).
   A unit ordered `After=` that oneshot waits for it to finish, which is how the signing step runs after the driver's removal; so every unit ordered after it needs `DefaultDependencies=no` too, `Type=exec` or not, or the target waits for the whole chain through it.
   Prove it with `systemd-analyze critical-chain multi-user.target` on a first start, never by reading the unit files.
7. **Name the boot option file so it is read last.**
   `grub-mkconfig` reads `/etc/default/grub.d/*.cfg` in the shell's order. A file that adds an option only when it is not on the line yet must come after any file a person made by hand, which appends without looking: `zz-NAME.cfg`, not `40-NAME.cfg`.

## Proving it without the machine

- **The firmware's state:** start the kernel you ship directly in QEMU (`-kernel`, TCG is enough, about ten seconds) with a small boot image that holds bash, the step, `mokutil` and the efivarfs module, under each firmware, and print the step's answer beside `mokutil --sb-state` and `sig_enforce`:
  - SeaBIOS: `bios`.
  - `OVMF_CODE_4M.fd` (built without Secure Boot): `unsupported`. This is what an Intel Mac before the T2 chip looks like.
  - `OVMF_CODE_4M.secboot.fd` with the empty variables file, `-machine q35,smm=on -global driver=cfi.pflash01,property=secure,value=on`: `off` (setup mode).
  - `OVMF_CODE_4M.ms.fd` with `OVMF_VARS_4M.ms.fd` and your own certificate added to `db` (`virt-fw-vars --input ... --output ... --add-db GUID CERT.pem`): `on`, and OVMF accepts your signed kernel through `-kernel`.
- **Module loading:** in the same guests, `insmod` a module DKMS signed with its own key and the same module with its signature cut off (the trailer is `~Module signature appended~\n`, the 4 bytes before it hold the signature's length, 12 bytes of header precede those). Without Secure Boot the unsigned one loads. With it both are refused until the DKMS certificate is in the variables (`--add-db` again stands for the enrolment), then the signed one loads.
- **What the first start costs:** an image with the real dkms, the shipped kernel's headers and two small DKMS modules, every signature cut off and DKMS's key removed (how an ISO built in a chroot leaves them); run the step in a fresh container per case under `/usr/bin/time`, with a firmware tree in each state. Only the firmware is a fixture there.
- **A card that is not there:** a sysfs fixture folder, passed by an environment variable, for the detection; an image with the published driver set as the image build installs it, for the real apt. Judge on apt's `Inst`, `Remv` and `Purg` lines and on the difference of the installed list: nothing that is not the vendor's leaves, nothing comes in, `apt-get check` passes. Run one case on the real `/sys` too.
- **The start itself, under a real systemd, without privileges:** install the published set into a container (systemd as init, the shipped kernel, initramfs-tools, GRUB's menu tools), `docker export` it into `mke2fs -t ext4 -d ROOT disk.raw` inside another container, and start QEMU with `-kernel`, the boot image the guest itself wrote last, `root=/dev/vda rw` and the disk behind a qcow2 layer. A second small ext4 disk carries each start's script in and its results out (`mke2fs -d` to make it, `debugfs -R "rdump /out DIR"` to read it); the guest copies its boot image and `grub.cfg` there, so the next start uses what `update-initramfs` and `update-grub` really wrote. Nothing is mounted on the host.
  Drive the guest from a timer and a `Type=exec` service that waits until `systemd-analyze time` answers: `blame` and `critical-chain` refuse until the start has finished, and a oneshot in the start's own jobs would keep it from finishing.
  Measure a start by when `multi-user.target` was reached (`systemctl show -p ActiveEnterTimestampMonotonic`), in pairs, published against new, alternated, with the host's load written at each; "Startup finished" also counts background jobs and is not what a person waits for.
- **A firmware table:** `-smbios type=1,product=MODEL` gives the DMI name (double a comma: `MacBookPro9,,2`), and `-acpitable file=X.aml` adds a table that does what the faulty method does. A device with a method `_INI` that does the `Notify` to the missing name gives the same two lines the real machine logs, `ACPI BIOS Error (bug): Could not resolve symbol [...], AE_NOT_FOUND` and `ACPI Error: Aborting method ... due to previous error`; with the package's table in the early archive (built exactly as the hook builds it) both are gone and the upgrade line is there.
- **A window and its button, in the guest:** Xvfb, the program started as a person starts it (root, the language from a locale file), a wait for the drawn dialog and not for the first window of its class (see the traps), a picture before the click and one after, the click at the place an earlier picture of the same screen size and language shows; the same switch from a person's account through polkit, refused without an authorization and done with a rule that answers yes for that one action and that one account, standing for the agent. Look at the pictures: a long sentence cut at the window's edge shows only there.
- **A masked event:** `acpi_mask_gpe=0x06` gives `ACPI: Masking GPE 0x6.` and `/sys/firmware/acpi/interrupts/gpe06` ending in `masked`. The storm itself needs the machine.
- **A one-line kernel fix without a kernel build:** take the function's own text (from its definition line to the first line that is exactly `}`), include it in a user-space file whose `snprintf` has the kernel's check (`vsnprintf()` warns and returns 0 for a size above `INT_MAX`), and compare what the measuring pass counts with what is printed.

## Traps

- **Symptom:** in a UEFI guest the step says `unknown`, `mokutil` says "EFI variables are not supported".
  **Cause:** efivarfs is a module in Debian's kernel configuration and nothing loaded it; BusyBox `insmod` reads no compressed module.
  **Fix:** decompress the module into the boot image, `insmod` it, `mount -t efivarfs efivarfs /sys/firmware/efi/efivars`.
  **Found by:** printing the number of files in `efivars` (0) beside the state.
- **Symptom:** libraries of the vendor's driver stay after the driver is purged, although nothing depends on them.
  **Cause:** apt does not call them unneeded: `nvidia-vulkan-icd` provides `vulkan-icd`, which other packages name as an alternative, and it holds the rest.
  **Fix:** list what is left by name, automatic mark and a plan of its own, as above.
  **Found by:** `apt-mark showauto` and `apt-cache rdepends --installed` on the leftovers, then `Provides` of the one nothing depended on.
- **Symptom:** removing the vendor's packages installs the distribution's `nvidia-detect`.
  **Cause:** NVIDIA's `nvidia-kernel-support` conflicts with and stands in for `nvidia-detect`; a package that depends on it gets Debian's edition once NVIDIA's is gone.
  **Fix:** depend on it only when its answer is read; the edition's plan comes from NVIDIA's own tables.
  **Found by:** apt's refusal to install both in one transaction, and the `Inst` line of the removal's plan.
- **Symptom:** removing a driver lock brings the other branch's lock in.
  **Cause:** the repository package depends on `lock-a | lock-b`.
  **Fix:** the repository package leaves with the driver and comes back first with it, so nothing forces a lock on a machine without the card.
- **Symptom:** in a proof container the step refuses: "apt cannot plan the removal".
  **Cause:** the new package was installed with `dpkg --force-depends` because one dependency is a staged package that is not published; apt then has a broken system.
  **Fix:** a stand-in package of that name and version for the unrelated dependency, said in the proof. The refusal itself is right and stays.
- **Symptom:** a test "passes" on the published side.
  **Cause:** it counted language names from a list that lacked a language, so two wrong numbers agreed.
  **Fix:** when a required language is added, the list of names in a test gains it and the counts change.
- **Symptom:** the first start reaches `multi-user.target` only when the driver's removal has ended (20 minutes in an emulated guest), although the removal's own unit has `DefaultDependencies=no`.
  **Cause:** two `Type=exec` units wanted by the target were ordered after the removal; the target waits for every wanted unit with default dependencies to start, and they could not start before the removal ended.
  **Fix:** `DefaultDependencies=no` on every unit of the chain (recipe step 6). After it the target was reached 34 s into user space while the removal ran on for 25 minutes.
  **Found by:** `systemd-analyze critical-chain multi-user.target` in the guest: the target hung under `sparky-stereo-known-machines.service @20min 5.474s`.
- **Symptom:** a guest assembled in a container gets no kernel option from the table, and the tool says nothing is behind.
  **Cause:** there is no `/boot/grub/grub.cfg`: no installer ever ran `update-grub`, and the tool writes no menu where there is none.
  **Fix:** one start of each guest runs the real `update-grub` first, as an installed machine has it.
- **Symptom:** an older test of the table starts writing boot images in its container.
  **Cause:** it called `--apply` on a fixture of a machine that now has a correction.
  **Fix:** matching tests ask with `--list`; `--apply` is tested with doubles and in the guest.
- **Symptom:** at an early start a new card's driver would be downloaded on a metered connection.
  **Cause:** NetworkManager has not said yet what the connection is; its `Metered` property is still unknown.
  **Fix:** `nm-online -q -t 60` before the question.
- **Symptom:** the image list's test or reader shows one package more than the list has.
  **Cause:** the generator writes the count into the list's first line; a hand edit left the old number.
  **Fix:** run the generator on a copy and take its file for the list you changed.
- **Symptom:** a harness refuses `docker run ... sh -c '... rm -rf ...'`.
  **Cause:** it cannot read a removal inside a quoted script.
  **Fix:** give the removal as the container's own command with a literal path (`docker run ... IMAGE rm -rf /d/NAME`).
- **Symptom:** a kernel option appears twice on the kernel line, or other scripts of `/etc/grub.d` slow down.
  **Cause:** files of `/etc/default/grub.d` are sourced more than once (the memory tester's script sources them for every value it reads).
  **Fix:** add an option only when it is not on the line yet.
- **Symptom:** the list archive's search answers 403.
  **Cause:** a bot wall.
  **Fix:** the author's page on a list mirror, and mainline's raw files for "is it merged"; the lists' git mirrors for a search by function name.
- **Symptom:** the Lean Code link gate cannot resolve a dependency on a package of the edition.
  **Cause:** its archive list holds only the public archives.
  **Fix:** add the published edition repository as a `file:` archive with its public key. A native script package is rebuilt from its retained source in an image that has its build dependencies.
- **Symptom:** a step started by a unit fails, the kept problem says "its output says why", and the run's log holds one line.
  **Cause:** the setup's `ERR` trap printed to wherever the failing command's output was pointed, and the facts are gathered as `run COMMAND >FILE`; the error text went into the facts file.
  **Fix:** keep the run's own output on a descriptor of its own (`exec 8>&1`, again after the `tee` redirection) and let the trap write there (`exec >&8 2>&8` first).
  **Found by:** making one fact-gathering command fail in the guest (a stand-in `lsusb` that exits 1) and counting the log's lines and its `ERROR` lines.
- **Symptom:** in the guest `lsusb` exits 1 and a service that lists USB devices fails, in the published set too.
  **Cause:** the guest has no USB controller at all, which no real computer of the last twenty years is.
  **Fix:** `-device qemu-xhci`. A unit that fails only for that is the rig's, not a finding; say it once.
- **Symptom:** apt in the guest says `Failed to fetch file:/repo/pool/... File not found`, although the files were copied into the guest.
  **Cause:** the guest got the repository's index only (its packages are gigabytes), and `/repo` in the exported root is the empty folder the container's mount point left, not the copy.
  **Fix:** carry the few packages a step installs in on the second disk, at their pool path, and make `/repo` a link to the guest's copy before the step runs.
- **Symptom:** in the picture of the plan's window the sentence about the correction ends at the window's right edge.
  **Cause:** `yad --text-info` does not wrap unless told; the package's other windows had `--wrap`, the plan's did not.
  **Fix:** `--wrap`. A picture of the window is the only test that shows this: the log has the whole sentence.
- **Symptom:** `xdotool getwindowgeometry` of the window found by class gives 10x10.
  **Cause:** the first window of yad's class is GTK's leader window, which exists before the dialog is drawn; `xdotool search --class yad` returns it at once.
  **Fix:** wait for a visible window as wide as the dialog (`xdotool search --onlyvisible --class yad`, then `getwindowgeometry --shell` and its `WIDTH`), twenty minutes at most, and only then take the picture or click; the button's place comes from a picture of the same screen size and language.
- **Symptom:** a start that presses a window's button never ends; the guest idles at about 5 % of a core and its results disk stops changing.
  **Cause:** the click was sent four seconds after the leader window appeared, while the plan was still being worked out (under emulation at a host load of 50 the plan came about ten minutes later), so it hit an empty screen. When the wait ran out the scenario sent Return, and Return answers the plan window's default button, which is "install" (yad's answer 0): the setup started a terminal for an installation the guest cannot download, and `wait $pid` had no bound.
  **Fix:** the wait above; a picture before the click; the click sent again (three times at most) when nothing happens; never a key to the plan's window (Escape where it must close, which is Cancel's 252); every wait for the program bounded (`ended PID SECONDS`, which stops it and says so). Prove the waiting with a real yad window in Xvfb started 25 s late: the old way took the 10x10 window at 6 s and its click did nothing, the new one took the 760x500 dialog at 26 s and the click gave the button's code.
  **Found by:** reading the guest's second disk while it ran (see the perks), whose button log had no `--off` line and ended with `GdkWindow ... unexpectedly destroyed` at the wait's 600 s mark; qemu's CPU time over ten minutes (idle); the program's own table of yad's answers (`plan_answer`).
- **Symptom:** the scenario's own line says `The name org.freedesktop.NetworkManager was not provided by any .service files`, yet the step then says the connection is metered.
  **Cause:** the Python stand-in for NetworkManager takes its name more than four seconds after it starts under emulation; the scenario asked after a fixed sleep, the unit asked later.
  **Fix:** wait for the name itself (`busctl status NAME` in a loop) before anything asks.
- **Symptom:** the dependency table says a tool the new scripts call is NOT INSTALLED (`nm-online` in a guest without NetworkManager).
  **Cause:** the step calls it only when it is there (`command -v nm-online`); without NetworkManager there is no metered state to ask about, and the step goes on as before.
  **Fix:** report a guarded tool as such, not as a missing Depends; a Depends is owed only for a tool called without a guard.
- **Symptom:** in a plain container of the guest image Xvfb aborts at start, `double free or corruption (out)`, whatever its options; in the emulated guest the same image's Xvfb works.
  **Cause:** not found here. It happens only while Xvfb loads Mesa's GLX on the host's processor (`-extension GLX` makes it run).
  **Fix for a test that only needs a display:** `Xvfb ... -extension GLX`; the scenarios in the guest keep GLX. Start every such container with `--ulimit core=1`, so the abort does not reach the host's crash handler.
- **Symptom:** a harness refuses a test script that removes `"$T/sys"`.
  **Cause:** an empty variable would make it `/sys`.
  **Fix:** `"${T:?}/sys"`, in tests too.

## Perks

- "The memory tests twice" in GRUB's menu is Debian's `memtest86+`: one entry for the screen and one for a serial console (`GRUB_MEMTEST_DISABLE_SERIAL=true` hides the second).
- A file in `/etc/sudoers.d` with mode 0644 works but `visudo -c` calls it out; the mode sudoers(5) asks for is 0440. Check who owns the file before changing it.
- The firmware of an Intel Mac before the T2 chip has EFI variables and no `SecureBoot` among them: state `unsupported`, never `off`.
- A guest's second disk can be read while the guest runs, without mounting and without stopping it: `debugfs -c -R 'ls -l /out' io.raw` and `debugfs -c -R 'cat /out/FILE' io.raw` (`-c` opens it read only, in catastrophic mode). This is how a start that seems slow is told from one that hangs: compare the files' times with qemu's CPU time (`ps -o time -p PID`) a few minutes apart.
- A stopped start-path job: `docker stop` on the job's own container by name ends `docker run`, and the script's own trap then records the container and removes it. A signal to the waiting script runs its trap only after `docker run` returns.

## Not proven here (the real machines only)

That the MacBookPro9,2's `_Q80` stops logging with the table as the package places it, that the iMac14,1's processor load falls with the option as the package sets it, a real NVIDIA card appearing (the kernel's own udev event, the download, the restart), MokManager's own enrolment of the DKMS key, GRUB itself reading the menu it was given (the guests take the kernel line from the written `grub.cfg`), and the time of the removal on a real disk (about a minute in a container, 25 minutes emulated).
