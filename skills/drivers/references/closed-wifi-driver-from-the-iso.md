# A closed Wi-Fi driver from the ISO

**For anyone who must make a vendor's closed Wi-Fi driver work on a machine that has no cable:** Broadcom's `wl` (Debian's `broadcom-sta-dkms`) is the worked case.
The licence is shown from the package file before anything is installed, the package comes from the ISO without the network, DKMS builds it on the edition's kernel, and every step is checked and every failure told and kept.
Written 2026-11-16 from ORDER 614; the loading of the module on a real BCM4360 was not proven (see the end).

## Working recipe

1. **Say which chips need it, from the package's own list and the kernel's.**
   `share/network-ids.tsv` names `wl` in the driver column only for the chips no driver of the kernel drives (14e4:43a0, 14e4:43b1 and 14e4:4360: `brcmfmac` knows chip 43602, `brcmsmac` binds 802.11 core revisions 17, 23 and 24, `b43`'s AC-PHY file is built by `CONFIG_B43_PHY_AC`, which no Kconfig defines).
   The package's own `usr/share/broadcom-sta/broadcom-sta.ids` is the cross-check: its commented lines are the IDs a free driver supports.
   The detection (`lib/detect.py`) prints a `licence` line for every wl candidate and `fact network-no-kernel-driver` plus `action broadcom-wl` for a card with no kernel driver; it installs nothing, and a test asserts that no `package` line names the driver.
2. **Carry Debian's file, not a copy of it.**
   The packer (`iso-build/pack.sh`, the block "the driver pool") runs `apt-get download` for `lists/driver-pool.list` and the headers of every kernel in the image into `/usr/share/sparky-stereo/driver-debs`, then `dpkg-scanpackages -m` writes the index with each file's SHA-256.
   The folder is not the installer's offline folder: `offline-packages off` deletes that one after the installation, and the Wi-Fi driver is needed most on the installed system.
3. **Show the licence from the .deb, then install that .deb.**
   `dpkg-deb --fsys-tarfile PKG.deb | tar -xO ./usr/share/doc/broadcom-sta-dkms/copyright` is Broadcom's Software License Agreement, unchanged (its clauses 2.1: "complete, unmodified and only for use with a Broadcom Product", and 2.3: a copy of the agreement accompanies the distribution, and an indemnity).
   The person reads it in a window (`yad --text-info`, framing text in their language) or on the terminal; only "Install" installs; "Not now" is kept for the machine.
   From the pool the file's sum is checked against the index first and apt has the pool as its only source (`-o Dir::Etc::SourceList=FILE -o Dir::Etc::SourceParts=/dev/null -o Dir::State::Lists=DIR`, `deb [trusted=yes] file:POOL ./`): the network is neither needed nor touched.
   From the network the size is said first, the file is fetched with `apt-get download`, and the same file is installed.
4. **Verify each step, stop at the first that fails.**
   dpkg status `installed`; `dkms status -m broadcom-sta -v VERSION -k KERNEL` says `installed`; under Secure Boot (the last byte of `/sys/firmware/efi/efivars/SecureBoot-*` is 1) `modinfo -F signer wl` is not empty and `mokutil --test-key /var/lib/dkms/mok.pub` says the key is enrolled; the free modules that are loaded (`b44 b43 b43legacy ssb brcmsmac bcma`, README.Debian and the Debian wiki) are removed in that order; `modprobe wl`; a wireless interface whose `device` is that card's PCI address.
   Each failing step is an ERROR line, a message kept in `sparky-stereo-problems` (key `broadcom-wl`, Repair `sparky-stereo-hardware --broadcom-wl repair`) and the end-of-run list; success clears the key.
5. **Prove it with the network cut.**
   A container made from the rig image, with dkms, the running kernel's published headers and the real engine installed once, then committed and started with `--network none`: apt, dpkg, dkms, `modinfo` and `sparky-stereo-problems` are the real ones, only `modprobe` (a container cannot load a module) and the card's sysfs are doubles.
   `uname -r` in the container is the host's kernel, so DKMS builds against the published headers for real.

## Each failure and what is said (messages 73 to 83 of `lang/` and `problems-lang/`)

| Failure | How it is made in the rig | Message |
|---|---|---|
| the licence cannot be read from the package | a package with no copyright file | 73 |
| the package is not on the disk and cannot be fetched | no pool, apt knows no candidate, or the download fails | 74 |
| the pool file differs from the index | one byte appended | 75 |
| no headers for the running kernel | a kernel name the pool does not have | 76 |
| apt cannot install it | apt exits non-zero, package not on the machine | 77 |
| dkms cannot build | `/usr/bin/make` replaced by a script that exits 2: the real postinst fails and dpkg says `half-configured` | 78 |
| Secure Boot on, module unsigned | `/usr/bin/openssl` moved away before the build: dkms prints "openssl not found, can't generate key and certificate." and installs it unsigned | 79 |
| Secure Boot on, key not enrolled | `mokutil --test-key` says "is not enrolled" | 80 |
| key could not be checked | mokutil missing, or its own error (a container prints "EFI variables are not supported") | 83 |
| `modprobe wl` refused | the module's own message ("Key was rejected by service" is message 80) | 81 |
| no interface appears | the load double makes the driver link and no interface | 82 |

## Traps, with how each was found

- **Symptom: the driver pool lacks the edition's own packages when the image's source is a flat `file:/repo`.**
  Cause: apt's file method uses the file where it is and never copies it into `Dir::Cache::archives`, so `--download-only --reinstall install` leaves only the network downloads.
  Fix: `apt-get download PKG...` copies every file, whatever its source; the packer's own "missing from Packages" check fails loudly when a file is absent.
  Found by: running the packer's block, cut out of `pack.sh`, with the real apt in a container with `file:/repo`.
- **Symptom: the block says "could not list the image's kernels" on an image with none.**
  Cause: `dpkg-query -W 'linux-image-[0-9]*'` exits 1 with "no packages found", and a `grep -v` that filters out every line exits 1 as well, so both land in the first error branch.
  Fix: separate the two steps and say each failure in its own words; found by the unit test with no kernel.
- **Symptom: a patch of a desk study makes the tool stop with `FileNotFoundError: .../firmware-packages`.**
  Cause: `diff -ruN` writes no hunk for an empty file, so the three empty fixture files (`firmware-packages`, `hid-uevents`, `input-properties`) were lost.
  Fix: create them; a patch that carries fixtures should come as `git format-patch` or a folder.
- **Symptom: `mokutil --test-key` exits 1 in a container and the step says "not enrolled".**
  Cause: exit status 1 is also what mokutil returns for "EFI variables are not supported on this system", so the exit status alone invents a fact.
  Fix: read its words (`is already enrolled`, `is not enrolled`); anything else is its own error, said as it is (message 83).
- **Symptom: a test double's state change is not seen after the function under test returns.**
  Cause: bash's dynamic scope: the function declares `local pkg_status`, the double (called from inside it) sets that local, and it vanishes on return.
  Fix: name the double's state differently from the function's locals.
- **Symptom: faking a failing `make` with `PATH=/fake:$PATH function` has no effect on the DKMS build.**
  Cause: the environment of a function call does not reach the maintainer script's `dkms` through apt and dpkg the way a command prefix does.
  Fix: replace `/usr/bin/make` itself in the throwaway container and put it back.
- **Symptom: a window in Japanese comes up in English.**
  Cause: `load_strings` matches `ll_CC` (`ja_JP`); `ja.UTF-8` matches nothing.
  Fix: write the locale as the system writes it.
- **Symptom: `apt-get update` on the pool prints `W: Symlinking file  to .../partial/_pool_._Packages.bz2 failed`.**
  Cause: apt asks a `file:` source for each compressed form of `Packages` and the pool has only the plain one; the update still succeeds.
  Fix: none needed; read the exit status, not the warnings (the step does).
  Found by: the first run of the real-apt scenarios, whose output showed the warning above the `Setting up` lines of the install.

## Perks

- A licence window can be driven headless: `Xvfb :99`, `yad`, `xdotool getwindowgeometry --shell` and a click at the button row (`X+WIDTH-60`, `Y+HEIGHT-30`), a plain PNG with `import -window root`, and `fonts-noto-cjk` so Japanese is not boxes.
- The unit test (`tests/broadcom-wl.sh`) catches ten different broken versions of the step (a mutant that skips the checksum, the licence, the interface wait, the headers, the Secure Boot reading, the DKMS status, the engine's keep and clear, the modprobe error, the module unloading): keep that style for the next closed driver.
- The packer's block and the layout check are tested without an ISO build: `iso-build/tests/no-silent-failures.py` (stubbed commands) and `iso-build/tests/test-check-layout.sh` (small ISOs made with the packer's literal xorriso options).

## Not proven here

Loading `wl` on a real BCM4360, the card's scan and association, WPA3 (the Debian wiki says `wl` may fail with it), the power-management note for frequent disconnections, the first boot after the install with Debian's blacklist in the initramfs, and Secure Boot with the edition's first-boot enrolment of the DKMS key.
