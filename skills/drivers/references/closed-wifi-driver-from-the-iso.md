# A closed Wi-Fi driver from the ISO

**For anyone who must make a vendor's closed Wi-Fi driver work on a machine that has no cable:** Broadcom's `wl` (Debian's `broadcom-sta-dkms`) is the worked case.
The licence is shown from the package file before anything is installed, the package comes from the ISO without the network, DKMS builds it on the edition's kernel, and every step is checked and every failure told and kept.
Written 2026-11-16 from ORDER 614; the loading of the module on a real BCM4360 was not proven (see the end).
Extended 2026-11-23 from row 728 (a MacBookPro9,2 whose BCM4331 dropped its Wi-Fi on `b43`): [a card two drivers drive](#a-card-two-drivers-drive), [saved profiles after the interface is renamed](#saved-profiles-after-the-interface-is-renamed) and [the network applet's speed 0](#the-network-applets-speed-0-with-wl).
Corrected 2026-11-24 from row 728b: the NetworkManager settings are for every card `wl` can drive, whichever driver has it, so [the settings follow the card, not the driver](#the-settings-follow-the-card-not-the-driver) (row 728 had matched them on `driver:wl`).

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

## The settings follow the card, not the driver

<a id="the-networkmanager-file-matched-on-a-driver"></a>
Daniel, 2026-11-24, on a file "for cards on Broadcom's driver only": "the proper shape is "that are broadcom able" since we know these features tend to make it fail no matter the drive (we attempted both drivers with default settings)".
So Wi-Fi power saving off, no address change while scanning and the permanent address apply to every card that `wl` can drive (the `BROADCOM-WL` rows of `share/network-ids.tsv`), under the kernel's free driver or under `wl`, and to no other card: power saving off everywhere would cost every other laptop its battery.

### How NetworkManager can find a card

NetworkManager.conf(5) of 1.58.1, "Device List Format", has these forms, and its matcher (`match_device_eval()`, `src/core/nm-core-utils.c`) no others: `*`; a bare interface name or address; `interface-name:IFNAME` (with `~` for a glob and `=` for a literal name); `mac:HWADDR`, "the permanent MAC address of the device"; `s390-subchannels:`; `type:TYPE`; `driver:DRIVER`, optionally `/VERSION`; `dhcp-plugin:`; and `except:SPEC`, joined with `,` or `;`.
No form names a PCI id or a udev property, and forms are joined by "or", never "and".

| Form | What it catches wrongly | Measured |
|---|---|---|
| `driver:wl` (row 728) | nothing, but it misses the card under the free driver | guest: the card on the list under the free driver's stand-in scanned with a random address and connected with power saving on |
| `driver:wl,driver:b43,driver:b43legacy,driver:brcmsmac,driver:brcmfmac` | 82 device ids that are not `BROADCOM-WL` rows: 28 PCIe chips `brcmfmac` drives (BCM4350, BCM43602, BCM4364, BCM4377, BCM4378 and BCM4387 among them), 19 older PCI ids under `bcma` or `ssb` (`b43`, `b43legacy` or `brcmsmac` bind their 802.11 core by revision), 2 PC Cards, 24 SDIO and 9 USB ids | the module aliases of the published 7.3.4 kernel against the table; guest: a card not on the list, under the same driver, got power saving off and its permanent address |
| `interface-name:wlp3s0b1` | loses the card at the swap: `b43` names it `wlp3s0b1`, `wl` names it `wlp3s0` | guest: after the swap, power saving on and not the permanent address |
| `mac:` of every permanent address the card has shown | nothing: an address is one card's | guest: under both stand-ins, renamed, with a different permanent address under each |

### `mac:` needs the permanent address the kernel reports

- NetworkManager reads the kernel's `IFLA_PERM_ADDRESS` (`nm_platform_link_get_permanent_address()`), which rtnetlink sends only when `dev->perm_addr` is not all zero (`net/core/rtnetlink.c`, v7.3); `register_netdevice()` copies `dev_addr` into it when `addr_assign_type` is `NET_ADDR_PERM`, the default (`net/core/dev.c`).
- When NetworkManager cannot read one, it uses the current address as a "fake" permanent one, and the matcher gets none: `nm_match_spec_device_data_init_from_device()` passes `.hwaddr = is_fake ? NULL : hw_address` (`src/core/NetworkManagerUtils.c`), so `mac:` never matches such a device. The writer says so and keeps it as a failure.
- `wl` sets its `cur_etheraddr` with `eth_hw_addr_set()` before `register_netdev()` (Debian's patched `wl_linux.c`), so the kernel reports it as permanent. mac80211 drivers copy the wiphy's address into `perm_addr` (`net/mac80211/iface.c`); `b43` takes it from the SPROM, `et1mac` when it is valid, else `il0mac` (`b43/main.c`).
- `wl`'s address comes from Broadcom's closed core, so the two drivers may report different addresses for one card. Keep every address the card has shown, with the driver it showed it under.

### The recipe

1. `/usr/lib/sparky-stereo-hardware/broadcom-wl-settings write --reload` lists the PCI devices whose id is a `BROADCOM-WL` row, finds each wireless interface whose `device` is that card or a device under it, and asks the kernel for its permanent address (one `RTM_GETLINK` naming the interface, then `IFLA_PERM_ADDRESS`, attribute 54).
2. It keeps each address with its card and the drivers it was seen under in `/var/lib/sparky-stereo-hardware/broadcom-wl-cards`; a card no longer on the bus leaves the record.
3. It writes `/run/NetworkManager/conf.d/sparky-stereo-broadcom-wl.conf`, NetworkManager's per-boot folder ("Scripts can also put per-boot configuration into /run/NetworkManager/conf.d"): one device and one connection section, each `match-device=mac:A,mac:B`. With no such card it removes the file. A file of that name that does not start with the writer's own first line is left as it is, and that is kept as a failure.
4. When the file changed and NetworkManager is active (`systemctl show -p ActiveState --value NetworkManager.service`, waiting while it is `activating`), it runs `nmcli general reload conf`.
5. It runs before NetworkManager starts (a oneshot with `Before=NetworkManager.service`), from udev (`SUBSYSTEM=="net", ACTION=="add", ATTRS{vendor}=="0x14e4"` and `SUBSYSTEM=="pci", ACTION=="remove", ENV{PCI_ID}=="14E4:*"`, as `RUN`), after the swap, the way back and the `wl` route, and in the postinst. udev announces a device only after its `RUN` programs end, so NetworkManager reads the new address before it scans or connects on the new interface.
6. A failure (that foreign file, an interface with no permanent address, a refused reload) is kept by `sparky-stereo-problems` with the writer as its repair; a later run that works clears it.
7. A file of the same name in `/etc/NetworkManager/conf.d` is the person's: NetworkManager reads it instead ("The loading of a file /run/NetworkManager/conf.d/name.conf can be prevented by adding a file /etc/NetworkManager/conf.d/name.conf"), so an empty one switches ours off, and the writer never touches it. Sections in later files win (`/usr/lib` < `/run` < `/etc`), and a profile's own value wins over every default.

The three keys:

| Key | Section | What it does (manual page) |
|---|---|---|
| `wifi.scan-rand-mac-address=no` | DEVICE | the card keeps its address while it scans (NetworkManager.conf(5), DEVICE SECTION); read at each scan request (`_hw_addr_set_scanning()`, `nm-device-wifi.c`), so a reload counts at the next scan |
| `wifi.powersave=2` | CONNECTION | power saving off; the file takes the number, `disable` is 2 (nm-settings-nmcli(5), `802-11-wireless.powersave`; NetworkManager.conf(5): enum values "only can be configured via their numeric magic number"); set at activation, the one place `set_powersave()` is called |
| `wifi.cloned-mac-address=permanent` | CONNECTION | the card's permanent hardware address while connected (nm-settings-nmcli(5), `802-11-wireless.cloned-mac-address`) |

- A connection default applies only when the profile asks for the default (`powersave` 0, `cloned-mac-address` unset): NetworkManager 1.58.1 reads it in `set_powersave()` (`src/core/devices/wifi/nm-device-wifi.c`) and in `nm-device.c` for the address. A person's own profile value wins.
- Debian's `wpasupplicant` (not `network-manager`) already ships `no-mac-addr-change.conf` with the scan setting for `wl` (Andrew Shadura, wpa 2:2.6-12, Debian #833507); nothing in Debian sets `wifi.powersave`.
- Debian's `broadcom-sta` carries Diego Escalante Urrelo's "wl: Make sure power_mgmt settings are honored" (since 6.30.223.271-16~exp1): `wl` turns power saving off as `PM_FORCE_OFF` when NetworkManager asks.

### Proving it with simulated radios

The guest: QEMU with KVM, the edition's kernel, a Debian testing root with NetworkManager, wpa_supplicant, hostapd, iw and python3, booted from an ext4 image (`docker export` of a prepared container, then `mke2fs -d`). Everything that decides the result is real: the radios, the kernel's permanent address, udev, NetworkManager and its matching. Only the bus is a stand-in.
1. `modprobe mac80211_hwsim radios=0`, then make each radio through the driver's generic netlink family (`MAC80211_HWSIM`: `HWSIM_CMD_NEW_RADIO` with `HWSIM_ATTR_RADIO_NAME` and `HWSIM_ATTR_PERM_ADDR`, `HWSIM_CMD_DEL_RADIO` by name; `drivers/net/wireless/virtual/mac80211_hwsim.h`). A driver swap makes a new device, so "the same card under the other driver" is a new radio with another permanent address.
2. `.link` files matched on `PermanentMACAddress=` give each stand-in the name its driver gives the card (`wlp3s0b1`, `wlp3s0`) and a current address that is not the permanent one (`MACAddress=`), so the address in use while connected tells whether `cloned-mac-address=permanent` applied. The access point's radio is named `ap0` and unmanaged.
3. A guest rule after `80-net-setup-link.rules` runs `iw dev $name set power_save on` for each station radio, because a new hwsim radio starts with power saving off and "off" would prove nothing.
4. A small sysfs tree says which PCI card each name belongs to (`0000:03:00.0`, 14e4:4331, and a 14e4:4318 beside it), read by the writer through `SPARKY_STEREO_SYSFS`; a guest rule runs the writer with the same arguments on each new `wlan*` interface (a radio has no PCI parent for `ATTRS{vendor}`).
5. Read: `NetworkManager --print-config`, the addresses while it scans, then while connected `iw dev IF get power_save`, the address against `ethtool -P`, the station the access point saw, NetworkManager's PID, and its journal with monotonic times.

Measured with NetworkManager 1.58.1 on 7.3.4-stereo3d18 (row 728b):

| Case | Address while scanning | Power save, connected | Address, connected |
|---|---|---|---|
| 0.1.39 (`driver:wl`), the card under the free driver's stand-in | random | on | not the permanent one |
| 0.1.40, the card appears while NetworkManager is stopped | unchanged | off | the permanent one |
| 0.1.40, the swap while it runs: a new device, the other name, another permanent address, the profile's own autoconnect | unchanged | off | the new permanent one; NetworkManager not restarted |
| 0.1.40, the way back | not read | off | the first permanent one |
| 0.1.40, the next start from the record alone (the file exists before any interface) | unchanged | off | the permanent one |
| a card not on the list beside one on it, the same driver | random | on | not the permanent one |
| rejected: the list of driver names, a card not on the list | unchanged | off | the permanent one (caught wrongly) |
| rejected: `interface-name:wlp3s0b1`, after the swap | not read | on | not the permanent one |
| the person's file of the same name in `/etc` | random | on | not the permanent one (theirs wins; ours unchanged in `/run`) |

At the swap the writer ran from udev between 26.36 s and 26.41 s of the guest's uptime (the same clock as the journal's monotonic times in a guest that never sleeps), NetworkManager logged its configuration reload (`config: signal: CONF`, listing the file) at 26.406 s and took the new device (`unmanaged -> unavailable`) at 26.419 s.
When the card left, the file went and NetworkManager's reload listed no file of ours.
`udevadm verify` and `systemd-analyze verify` accept the rule and the unit, and the unit is ordered before `NetworkManager.service`.

The first form, `driver:wl` (row 728), measured the same way with the radio's own driver name put in its place:

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
- **Symptom: a guest rule `KERNEL=="wlp*"` never runs for an interface a `.link` file renames to `wlp3s0`.**
  Cause: while rules match, `KERNEL` is still the kernel's name (`wlan0`); the rename comes from `80-net-setup-link.rules` later in the same event.
  Fix: match the kernel's name or a parent's attribute (`ATTRS{vendor}`); the program still runs after the rename and sees the new name in sysfs.
  Found by: the writer's log stayed empty while the radio was up as `wlp3s0`.
- **Symptom: udevd says `Process '/usr/sbin/iw dev wlan0 set power_save on' failed with exit code 237` for a device now named `wlp3s0b1`.**
  Cause: udev expands `$name` in a `RUN` value when the rule matches; before `80-net-setup-link.rules` it is the kernel's name, though the program runs after the rename.
  Fix: put a rule that passes `$name` after the renaming rule (`81-…`); a program that reads sysfs itself needs no name.
  Found by: `journalctl -u systemd-udevd` in the guest.
- **Symptom: a radio helper reports an error although the radio is there.**
  Cause: the generic netlink acknowledgement carries the handler's return value, and `HWSIM_CMD_NEW_RADIO` returns the new radio's id.
  Fix: only a negative value is an errno. Found by: the radio's interface existed after each "ERROR radio" line.
- **Symptom: `iw dev IF get power_save` says off on a new hwsim radio before any setting.**
  Cause: hwsim does not turn power saving on by default; NetworkManager sets it only at activation (the one call of `set_powersave()`).
  Fix: switch it on before NetworkManager sees the device, or the "off" proves nothing.
- **Symptom: after `nmcli device disconnect IF`, the profile does not autoconnect on the device that replaces it.**
  Fix: delete the profile to let the card scan, and add it again before the next device appears.
- **Symptom: `nmcli` asked while NetworkManager is stopped: does it start it?**
  Measured with 1.58.1 (enabled, stopped): it stayed inactive. The writer still asks systemd first (`ActiveState`) and reloads only an active NetworkManager.
- **Symptom: in a test, `check 'x' bash -c "my_function"` fails though the function works.**
  Cause: a child shell does not inherit the test's functions. Fix: `check 'x' my_function`.
- **Symptom: a writer test reports the interface's driver as `none`.**
  Cause: the test double's `driver` link does not resolve, and the writer asked `os.path.exists`. Fix: read the link's name (`os.readlink`), as the shell library does.
- **Symptom: an nmcli double finds no profile.** Cause: `${*##* }` removes the pattern from each argument, not from the joined line. Fix: `${!#}` for the last argument.
- **Symptom: `bash -n` says "unexpected EOF while looking for matching quote" far below the edit.** Cause: an apostrophe inside a double-quoted `"${var:-it's}"`. Fix: no quote characters in a default word.

## Not proven here

Loading `wl` on a real BCM4360, the card's scan and association, WPA3 (the Debian wiki says `wl` may fail with it), the power-management note for frequent disconnections, the first boot after the install with Debian's blacklist in the initramfs, and Secure Boot with the edition's first-boot enrolment of the DKMS key.
For the two-driver work: `wl` and `b43` on a real BCM4331 (the swap, the way back and the restart Debian's README.Debian asks for after the first installation; Debian #1088231 reports `wl` failing after `b43` was loaded and unloaded until a restart), `iw dev IF get power_save` reading `off` under `wl` with the file, and the `iw` readings of the speed 0 cause.
For the settings that follow the card: whether `b43` and `wl` report the same permanent address on a real card (`ip -d link show IF` under each), the package's own udev rule on a real PCI card (the guest ran the same program from a rule matched on the name), a card's hot removal, and whether the settings end the drops.
