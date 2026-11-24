# A closed Wi-Fi driver from the ISO

**For anyone who must make a vendor's closed Wi-Fi driver work on a machine that has no cable:** Broadcom's `wl` (Debian's `broadcom-sta-dkms`) is the worked case.
The licence is shown from the package file before anything is installed, the package comes from the ISO without the network, DKMS builds it on the edition's kernel, and every step is checked and every failure told and kept.
Written 2026-11-16 from ORDER 614; the loading of the module on a real BCM4360 was not proven (see the end).
Extended 2026-11-23 from row 728 (a MacBookPro9,2 whose BCM4331 dropped its Wi-Fi on `b43`): [a card two drivers drive](#a-card-two-drivers-drive), [the NetworkManager file matched on a driver](#the-networkmanager-file-matched-on-a-driver), [saved profiles after the interface is renamed](#saved-profiles-after-the-interface-is-renamed) and [the network applet's speed 0](#the-network-applets-speed-0-with-wl).

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

## A card two drivers drive

Some Broadcom chips run on a free driver of the kernel and on `wl` both: the BCM4331 (14e4:4331) is driven by `bcma` (the bus, on the PCI device) and `b43` (the 802.11 core, `CONFIG_B43_PHY_HT`), and Broadcom's own README lists it for `wl`.
Debian's `usr/share/broadcom-sta/broadcom-sta.ids` comments it out as "supported by b43", so nothing proposes `wl` for it by itself.
On that chip `b43` has no 5 GHz and no 802.11n features (linux-wireless documentation, b43, "Known issues").

1. **Find which ids both drive, from the published kernel's own modules.** `modinfo -F alias` of `bcma`, `ssb`, `b43`, `b43legacy`, `brcmsmac`, `brcmfmac` and `b44`, matched against each id of the package's list and of `share/network-ids.tsv`.
   A PCI claim by `bcma` or `ssb` is only the bus: the card is driven when a core driver binds its 802.11 core (`bcma:m04BFid0812rev1D` for the BCM4331's `b43`).
   Two rows of the table named a free driver that no module claims (14e4:432a and 14e4:432d): they take the `wl`-only route.
2. **Keep the kernel's driver; offer `wl`.** Detection prints `fact network-two-drivers ID FREE` and `action broadcom-wl-swap`; nothing is installed unasked.
   The plan window says which driver has the card and has a button for the other: `--broadcom-wl swap` and `--broadcom-wl back`.
3. **The swap is the `wl` route plus an undo.** Broadcom's licence from the package file, then install, DKMS, Secure Boot, unload the free modules in Debian's order (`b44 b43 b43legacy ssb brcmsmac bcma`), load `wl`, wait for an interface that `wl` drives.
   Record the free modules that were loaded first; when a step fails: unload `wl`, **purge** the package, load those modules again in reverse order (the bus first), wait for the free driver's interface, and say both the cause and the undo.
4. **The way back purges, then loads the card's own alias** (`/sys/bus/pci/devices/ADDRESS/modalias`), as the kernel does at the start: the bus driver comes, and udev loads the core's driver.
5. **Find the card's interface under its PCI device, not only on it.** `wl` binds the PCI device; `b43` binds the core below it, so the interface's `device` link points at `.../0000:03:00.0/bcma0:1`. Match the PCI address as a path component, and read the driver from the interface's own `device/driver`.

## The NetworkManager file matched on a driver

`/usr/lib/NetworkManager/conf.d/sparky-stereo-wl.conf`, one `[device-…]` and one `[connection-…]` section, both `match-device=driver:wl`:

| Key | Section | What it does (manual page) |
|---|---|---|
| `wifi.scan-rand-mac-address=no` | DEVICE | the card keeps its address while it scans (NetworkManager.conf(5), DEVICE SECTION) |
| `wifi.powersave=2` | CONNECTION | power saving off; the file takes the number, `disable` is 2 (nm-settings-nmcli(5), `802-11-wireless.powersave`; NetworkManager.conf(5): enum values "only can be configured via their numeric magic number") |
| `wifi.cloned-mac-address=permanent` | CONNECTION | the card's permanent hardware address while connected (nm-settings-nmcli(5), `802-11-wireless.cloned-mac-address`) |

- A connection default applies only when the profile asks for the default (`powersave` 0, `cloned-mac-address` unset): NetworkManager 1.58.1 reads it in `set_powersave()` (`src/core/devices/wifi/nm-device-wifi.c`) and in `nm-device.c` for the address. A person's own profile value wins.
- `/usr/lib/NetworkManager/conf.d` is read first; a file of the same name in `/etc/NetworkManager/conf.d` shadows it (NetworkManager.conf(5), DESCRIPTION), so an empty one switches it off.
- Debian's `wpasupplicant` (not `network-manager`) already ships `no-mac-addr-change.conf` with the scan setting for `wl` (Andrew Shadura, wpa 2:2.6-12, Debian #833507); nothing in Debian sets `wifi.powersave`.
- Debian's `broadcom-sta` carries Diego Escalante Urrelo's "wl: Make sure power_mgmt settings are honored" (since 6.30.223.271-16~exp1): `wl` turns power saving off as `PM_FORCE_OFF` when NetworkManager asks.

**Proving the form for real, without the card:** a QEMU guest with KVM, the edition's kernel, a Debian testing root with NetworkManager, wpa_supplicant, hostapd and iw, booted from an ext4 image (`docker export` of a prepared container, then `mke2fs -d`).
In the guest: `modprobe mac80211_hwsim radios=2`; `wlan1` is the access point under hostapd and unmanaged (`[keyfile] unmanaged-devices=interface-name:wlan1`); before NetworkManager starts, `wlan0` gets a non-permanent address and `iw dev wlan0 set power_save on`.
Three cases, each from a fresh radio: the file with `driver:wl` replaced by `driver:mac80211_hwsim` (the driver `nmcli -g GENERAL.DRIVER device show wlan0` reports), the file as shipped, and no file.
Read back while connected: `iw dev wlan0 get power_save`, `/sys/class/net/wlan0/address` against `ethtool -P wlan0`, the station hostapd saw (`iw dev wlan1 station dump`), and the addresses seen while it scanned.
Measured with NetworkManager 1.58.1 on 7.3.4-stereo3d18:

| Case | Address while scanning | Power save, connected | Address, connected |
|---|---|---|---|
| matched on `mac80211_hwsim` | unchanged | off | the permanent one |
| as shipped (`driver:wl`) | random | on | unchanged (not the permanent one) |
| no file | random | on | unchanged |

## Saved profiles after the interface is renamed

`b43` on a BCM4331 core names the card `wlp3s0b1` and `wl` on the PCI device names it `wlp3s0` (systemd.net-naming-scheme(7): "bnumber: Broadcom bus (BCMA) core number").
A profile with `connection.interface-name` set to the old name is refused on the new device: NetworkManager 1.58.1 says "No suitable device found for this connection (device wlrenamed not available because profile is not compatible with device (mismatching interface name))".
The swap and the way back list the Wi-Fi profiles tied to the old name before the person's yes, empty that one property (`nmcli connection modify UUID connection.interface-name ''`), read it back, and keep the old value with the date and both drivers in `/var/lib/sparky-stereo-hardware/broadcom-wl-profiles`.
Proved in the same guest with the package's own function: the bound profile failed, was freed, and came up.

## The network applet's speed 0 with wl

Plasma's network applet shows NetworkManager's `Bitrate`, which NetworkManager fills from an `NL80211_CMD_GET_STATION` dump without a MAC filter (`wifi_nl80211_get_station()`, `src/libnm-platform/wifi/nm-wifi-utils-nl80211.c`, since Andrew Zaborowski's 277e8eaa1fbc of 2020; before it, a non-dump request with the BSSID).
The kernel answers an unfiltered station dump only through the driver's `dump_station` (`nl80211_dump_station()`, `net/wireless/nl80211.c`, v7.3), and `wl`'s cfg80211 operations have `get_station` and no `dump_station` (`src/wl/sys/wl_cfg80211_hybrid.c`), so the dump fails with `EOPNOTSUPP` and `Bitrate` stays 0.
On the machine: `iw dev IF station dump` fails with "Operation not supported (-95)" and `iw dev IF link`, which asks with the MAC, shows the "tx bitrate". Nothing of ours is wrong; no fix exists upstream (searched 2026-11-23).

## Traps of the two-driver work, with how each was found

- **Symptom: after `apt-get remove broadcom-sta-dkms` the free driver does not come back at the next start.**
  Cause: `/etc/modprobe.d/broadcom-sta-dkms.conf` is a conffile; a removal keeps it (dpkg status `config-files`) and it still blacklists `b43`, `bcma` and `ssb`.
  Fix: purge. Found by the rig: `modprobe --showconfig` still listed `blacklist b43` after the removal.
- **Symptom: `modinfo -k KERNEL wl` says "Module wl not found" right after DKMS installed it, in a container.**
  Cause: a container with only the kernel's headers has no `modules.dep`, so a name finds nothing although `updates/dkms/wl.ko` is there.
  Fix: read the file (`modinfo -F vermagic FILE` must start with the kernel's release). Found by `find /lib/modules -name 'wl.ko*'`.
- **Symptom: in the guest every connection times out (`nmcli connection up` exit 3) and "after" reads show no change.**
  Cause: hostapd's network has no DHCP server, so activation waits for IPv4. Fix: `ipv4.method manual` and `ipv6.method disabled` in the test profile; read the values while connected, because NetworkManager puts the first address back when it gives up.
- **Symptom: after `ip link set wlan0 name X` a freed profile still fails at "authenticating".**
  Cause: renaming keeps the device and wpa_supplicant's old registration (its P2P device stays `p2p-dev-wlan0`). Fix: model a driver swap as it is, a new device: unload and load `mac80211_hwsim` again and rename the new interface before NetworkManager starts.
- **Symptom: the guest's container exits 125 at once with no output.**
  Cause: `timeout` as the container's first process (the [proof rig's](../../stereo-proof-rig/SKILL.md) trap); an attached `docker run` through the lane's socket kept exiting 125 after that too, for a reason not found. Fix: start the container detached, `docker wait` it, keep `docker logs`.
- **Symptom: an nmcli double finds no profile.** Cause: `${*##* }` removes the pattern from each argument, not from the joined line. Fix: `${!#}` for the last argument.
- **Symptom: `bash -n` says "unexpected EOF while looking for matching quote" far below the edit.** Cause: an apostrophe inside a double-quoted `"${var:-it's}"`. Fix: no quote characters in a default word.

## Not proven here

Loading `wl` on a real BCM4360, the card's scan and association, WPA3 (the Debian wiki says `wl` may fail with it), the power-management note for frequent disconnections, the first boot after the install with Debian's blacklist in the initramfs, and Secure Boot with the edition's first-boot enrolment of the DKMS key.
For the two-driver work: `wl` and `b43` on a real BCM4331 (the swap, the way back and the restart Debian's README.Debian asks for after the first installation; Debian #1088231 reports `wl` failing after `b43` was loaded and unloaded until a restart), `iw dev IF get power_save` reading `off` under `wl` with the file, and the `iw` readings of the speed 0 cause.
