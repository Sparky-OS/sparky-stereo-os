# Sparky Stereo OS 9 beta 1: try it, then install it beside Windows

This guide takes you from the download to a 3D desktop, first from a USB stick and then installed next to Windows on the same disk.
It is written for a reader who knows Linux the classic way, with one partition for each system folder, and it starts from there.

Sparky Stereo OS, Daniel Ramos's edition of SparkyLinux (by Paweł "pavroo" Pijanowski).
It is Debian 14 "Forky" with SparkyLinux and KDE Plasma, plus a stereo 3D stack: the whole desktop, not only films and games, can be shown in 3D on the screens you have.

![The boot menu of the stick](images/beta1/boot-menu-uefi.jpg)

This is beta 1.
Everything in this guide was run on the beta 1 image in virtual machines, as described in each section.
What could not be run there is marked as not tested.
The known issues of beta 1 are listed near the end.

## Contents

1. [Download and check the image](#1-download-and-check-the-image)
2. [The live USB: what it is for](#2-the-live-usb-what-it-is-for)
3. [Writing the stick](#3-writing-the-stick)
4. [Booting the stick](#4-booting-the-stick)
5. [The 3D desktop in the live session](#5-the-3d-desktop-in-the-live-session)
6. [From one partition per folder to one partition](#6-from-one-partition-per-folder-to-one-partition)
7. [Installing beside Windows](#7-installing-beside-windows)
8. [After the installation](#8-after-the-installation)
9. [Known issues of beta 1](#9-known-issues-of-beta-1)
10. [Reporting what you find](#10-reporting-what-you-find)

## 1. Download and check the image

The download link goes to beta testers: ask for it in the [beta tester thread](https://github.com/Sparky-OS/sparky-stereo-os/issues/26).

| File | sparky-stereo-os-9-mashtabba-beta1-x86_64.iso |
|---|---|
| Size | 5,166,120,960 bytes |
| SHA-256 | `3564fc23315117bb552543235e889e5a398c9cf13e41ec0cceb6086ff43a25ab` |
| SHA-512 | `cd7c3da5ae699b951471a4c9d6e7443f5a8944fd7eb3a0f2f7d311c96275689be1e056c0ea96296f4ffd75ba4c3b21a5d79c499bb8a34e43b7d89784a35bd377` |

Check the file before you write it to a stick.

On Windows, in a Command Prompt in the download folder:

```
certutil -hashfile sparky-stereo-os-9-mashtabba-beta1-x86_64.iso SHA256
certutil -hashfile sparky-stereo-os-9-mashtabba-beta1-x86_64.iso SHA512
```

In PowerShell, `Get-FileHash .\sparky-stereo-os-9-mashtabba-beta1-x86_64.iso -Algorithm SHA256` gives the same.
Windows prints the sum in lower or upper case; the letters are the same.

On Linux:

```
sha256sum sparky-stereo-os-9-mashtabba-beta1-x86_64.iso
sha512sum sparky-stereo-os-9-mashtabba-beta1-x86_64.iso
```

If a sum differs, download the file again.

## 2. The live USB: what it is for

The stick is a complete system that runs from the USB stick and from memory, and changes nothing on your disks until you start the installer.
It is there to test your hardware, to show the 3D desktop, and to install.

A live session is slower than an installed system.
Every program is read from a compressed image on the stick and unpacked as it runs, so starting programs takes longer, and the first start of the desktop takes a few minutes.
Judge the speed of Sparky Stereo OS only once it is installed.

Nothing you change in the live session is kept after a restart.
The live user is `live`, with the password `live`.

What to try in the live session:

- the 3D desktop on your screens, in the format each screen understands (section 5);
- 3D photos in Gwenview, 3D videos in mpv and Bino, and the 3D screensavers and wallpapers;
- your graphics cards and screens: which card drives which screen, and whether the 3D formats reach them as expected.

## 3. Writing the stick

You need a USB stick of at least 8 GB.
Everything on it is erased.

Three ways were considered: Rufus and Ventoy on Windows, Ventoy and dd on Linux.

| Tool | Mode | Status in beta 1 |
|---|---|---|
| dd (Linux) | raw copy | Tested: the image boots as a USB disk on every firmware in the test set |
| Rufus (Windows) | DD Image mode | A raw copy like dd, so the same result is expected; Rufus itself was not run |
| Rufus (Windows) | ISO Image mode | Not tested; not recommended for beta 1 |
| Ventoy (Linux) | Ventoy 1.1.18 with Secure Boot support | Tested: BIOS, UEFI, and UEFI with Secure Boot |
| Ventoy (Windows) | the same Ventoy, written from Windows | Same stick as above, so the same result is expected; not run on Windows |

### Rufus, in DD Image mode

1. Start Rufus and choose your stick under Device.
2. Under Boot selection, click SELECT and choose the image.
3. Click START.
4. Rufus says that the image is an ISOHybrid image and asks how to write it.
   Choose "Write in DD Image mode" and confirm with OK.
5. Confirm that the stick will be erased.

In DD Image mode Rufus ignores its partition scheme and file system choices: the stick becomes an exact copy of the image, which boots in BIOS and in UEFI mode, with and without Secure Boot.

ISO Image mode copies the files onto a FAT32 or NTFS stick instead.
The image holds a file larger than 4 GB, so Rufus would have to use NTFS with its own UEFI:NTFS loader.
That path was not tested for beta 1, so use DD Image mode.

### Ventoy

Ventoy puts a small boot menu on the stick, and you copy image files onto it like onto any other stick.

On Windows, start `Ventoy2Disk.exe`, open the Option menu and tick Secure Boot Support, choose your stick and click Install.
On Linux, from the unpacked Ventoy folder, as root:

```
sh Ventoy2Disk.sh -i -s /dev/sdX
```

Here `-s` adds the Secure Boot support and `/dev/sdX` is your stick (check it with `lsblk` first).
Then copy the image file onto the stick's big partition, and check it with `sha256sum` again if you want to be sure.

With Secure Boot on, Ventoy needs its own one-time enrolment, separate from the Sparky Stereo OS key of section 4.
On the first start the firmware stops with "Verification failed: (0x1A) Security Violation".

![Ventoy's first start under Secure Boot](images/beta1/ventoy-sb-violation.png)

Press Enter, choose "Enroll key from disk", open the stick's VTOYEFI volume and choose `ENROLL_THIS_KEY_IN_MOKMANAGER.cer`.

![Ventoy's key in MokManager](images/beta1/ventoy-enrol-key.png)

Choose Continue, then Yes, then Reboot.
After that, Ventoy's menu lists the image; choose it, then "Boot in normal mode", and the stick's own menu follows.

### dd, on Linux

```
lsblk
sudo dd if=sparky-stereo-os-9-mashtabba-beta1-x86_64.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

Replace `/dev/sdX` with the whole stick (not a partition such as `/dev/sdX1`), and check it twice with `lsblk`: dd writes to whatever device you give it.

## 4. Booting the stick

### Choosing the stick

Most firmware opens a one-time boot menu with a key at power on: F8 on ASUS boards, F11 or F12 on many others, sometimes Esc.
Choose the stick there.
If the stick is listed twice, once with "UEFI:" in front, choose the UEFI entry: it is the one to use for an installation beside a UEFI Windows.

The stick's menu says which mode it started in, "(UEFI mode)" or "(BIOS mode)" in its title.
For a live session both work.
For the installation beside Windows it must be UEFI mode, because Windows on a GPT disk starts in UEFI mode and both systems share its EFI system partition.

The menu offers:

| Entry | What it does |
|---|---|
| Sparky Stereo OS (live) | The live session in English, with the edition's kernel |
| Sparky Stereo OS (live, Deutsch) | The same, in German with a German keyboard |
| Sparky Stereo OS with Debian's signed kernel | The live session with Debian's own kernel, which needs no key; the edition's stereo kernel features are missing |
| Enrol the Sparky Stereo OS key | Opens MokManager to enrol the edition's key from the stick (below) |
| Safe graphics (nomodeset) | For a screen that stays black with the normal entry |
| Copy ToRAM | Copies the whole image to memory first, then runs without the stick |

### Boards with their own management controller

Server and workstation boards with a management controller (BMC) have a small VGA chip of their own.
The firmware screens, the stick's menu and the boot splash may appear on that VGA port and not on your graphics card.
In the firmware setup, a setting usually called "VGA Priority" (Advanced, PCI Subsystem Settings, on AMI firmware) chooses which one comes first; set it to the add-in card ("Offboard Device").
Some boards also have a jumper to turn the onboard VGA off.

On such boards the factory settings often start USB sticks in legacy (CSM) mode only.
Look for the CSM settings: "Boot Option filter" should allow UEFI ("UEFI and Legacy" or "UEFI only"), and the video option ROM policy should be UEFI if you want the firmware screens on the add-in card in UEFI mode.

Once the desktop runs, Sparky Stereo OS puts the desktop on the graphics card that has screens connected, also when the firmware chose the management controller's VGA first.
This was tested with simulated card layouts, not on a board with a management controller.

### Graphics cards

The live session chooses the graphics driver by itself and says so in a notification:

- NVIDIA cards of the Turing generation and newer (GeForce RTX, Quadro RTX, RTX A-series and later) get the edition's NVIDIA driver, version 615 with open kernel modules.
- Older NVIDIA cards (Pascal and before, such as GeForce 10 and Quadro P) get the open nouveau driver.
  The closed NVIDIA legacy drivers do not build for beta 1's kernel.
- With Secure Boot on and the edition's key not enrolled, the live session starts with Debian's kernel, which has no NVIDIA modules, so it uses nouveau too.

To choose by hand, edit the menu entry with `e` and add `sparky.gpu=nvidia` or `sparky.gpu=nouveau` to the line that starts with `linux`, then start it with F10.

### Secure Boot and the Sparky Stereo OS key

With Secure Boot on, the stick starts through Debian's signed shim and Debian's signed GRUB, which every Secure Boot computer accepts.
The edition's own kernel is signed with the edition's key.
Your firmware does not know that key until you enrol it once, as a Machine Owner Key (MOK).

```mermaid
flowchart LR
  FW[Firmware with Secure Boot] --> SHIM[shim, signed for Microsoft's UEFI CA]
  SHIM --> GRUB[GRUB, signed by Debian]
  GRUB -->|key enrolled| SK[Sparky Stereo OS kernel, signed with the edition's key]
  GRUB -->|key not enrolled| DK[Debian's kernel, signed by Debian]
```

Without the key, nothing breaks.
The stick shows "error: bad shim loader signature." and "The Sparky Stereo OS key is not enrolled: starting Debian's signed kernel instead.", waits up to 10 seconds, and starts Debian's kernel.
With the key enrolled, the edition's kernel starts, with its stereo features and the NVIDIA driver.

The key's certificate is "Sparky Stereo OS Secure Boot 2026", valid until October 2036.
MokManager shows its fingerprint as `02 56 F3 3B 33 F4 68 9A 31 27 0E 8A AF 9F 13 B4 4D 8B 46 D7`; compare it before you enrol.

There are two ways to enrol it.
Both were tested under Secure Boot with Microsoft's keys.

Before you start: MokManager first shows "Press any key to perform MOK management" and waits only about 10 seconds.
Press a key at once.
If you miss it, MokManager closes and the computer may show an error or go back to the firmware menu; start the stick again and repeat.

![If no key is pressed in time](images/beta1/mok-timeout.png)

#### Way 1: from the live session, with mokutil

Start the live session (with Secure Boot on it runs Debian's kernel at this point), open Konsole and run:

```
sudo mokutil --import /usr/lib/sparkybackup/stereo/secureboot/sparky-stereo-secureboot-2026.der
```

mokutil asks for a one-time password twice; choose something short, you need it once.
Restart the computer and boot the stick again.
MokManager appears before the stick's menu.

| | |
|---|---|
| ![Press any key](images/beta1/mok-mokutil-1-press-key.png) | Press a key at once. |
| ![MokManager menu](images/beta1/mok-mokutil-2-menu.png) | Choose "Enroll MOK". |
| ![Enroll MOK](images/beta1/mok-mokutil-3-enroll.png) | Choose "View key 0" to check it, or Continue. |
| ![The key](images/beta1/mok-mokutil-4-view-key.png) | Compare the fingerprint, press a key to return, then choose Continue. |
| ![Enroll the key?](images/beta1/mok-mokutil-5-question.png) | Choose Yes. |
| ![Password](images/beta1/mok-mokutil-6-password.png) | Type the one-time password from mokutil. |
| ![Reboot](images/beta1/mok-mokutil-7-reboot.png) | Choose Reboot. |

#### Way 2: from the stick's menu

Choose "Enrol the Sparky Stereo OS key (MokManager, Secure Boot)" in the stick's menu.
No password is needed on this way.

| | |
|---|---|
| ![Press any key](images/beta1/mok-disk-1-press-key.png) | Press a key at once. |
| ![MokManager menu](images/beta1/mok-disk-2-menu.png) | Choose "Enroll key from disk". |
| ![Select the volume](images/beta1/mok-disk-3-volume.png) | Choose the first volume, the stick's EFI image. |
| ![Folders](images/beta1/mok-disk-4-folders.png) | Open `EFI/`, then `boot/`. |
| ![The certificate file](images/beta1/mok-disk-5-file.png) | Choose `sparky-stereo-secureboot-2026.der`. |
| ![The key](images/beta1/mok-disk-6-view-key.png) | Check the fingerprint, then Continue. |
| ![Enroll the key?](images/beta1/mok-disk-7-question.png) | Choose Yes. |
| ![Reboot](images/beta1/mok-disk-8-reboot.png) | Choose Reboot. |

After either way, the stick's first entry starts the edition's kernel under Secure Boot.
In the live session, `mokutil --sb-state` says "SecureBoot enabled" and `uname -r` shows `7.3.0-rc6-stereo3d8`.

The key stays enrolled in the computer's firmware.
An installed Sparky Stereo OS uses the same key, so you enrol it once per computer.

#### Secure Boot off

With Secure Boot off, the stick starts the edition's kernel directly, and nothing needs to be enrolled.
That is also the case when the stick starts in BIOS (CSM) mode.

## 5. The 3D desktop in the live session

![The live session](images/beta1/live-desktop.jpg)

The desktop starts with the Sparky Welcome window and KDE's Welcome Center.
Close them when you have read them.

![The boot splash](images/beta1/splash.jpg)

### Where the 3D formats are

Open System Settings, Display Configuration (or right-click the desktop and choose Configure Display Settings).
Each screen has two switches, both off by default:

- Anaglyph: red and cyan, for any screen and a pair of anaglyph glasses.
- Other stereo formats: the formats of 3D monitors, projectors and televisions that are switched to 3D by hand, and of passive and glasses-free screens.

![Display Configuration with the two switches](images/beta1/display-settings.jpg)

Tick a switch and click Apply.
The new choices then appear in the lists below.

With Anaglyph on, every resolution is listed twice more, "(anaglyph, modern screens)" and "(anaglyph, CRT)", in the Resolution list.

![Anaglyph in the Resolution list](images/beta1/anaglyph-under-resolution.jpg)

![The desktop in anaglyph](images/beta1/anaglyph-desktop.jpg)

With Other stereo formats on, the Refresh rate list offers, for the chosen resolution:

- side by side and top and bottom, for a display you switch to 3D with its own remote or menu;
- rows, for passive screens with polarised lines;
- columns, for parallax-barrier and lenticular screens;
- checkerboard, for 3D-ready DLP projectors and televisions;
- frame sequential, for gear with its own glasses sync, when the screen runs at 100 or 120 Hz.

Rows, columns and checkerboard come in both eye orders, "left eye first" and "right eye first"; if the depth looks inside out, choose the other order.

![Other stereo formats in the Refresh rate list](images/beta1/other-formats-under-refresh-rate.jpg)

A display that announces its own HDMI 3D modes (frame packing, side by side, top and bottom) gets them in the Refresh rate list too, labelled "3D frame packing" and so on.
They are never chosen automatically; choosing one switches the display to 3D by itself.
The virtual machines of the tests have no such display, so these entries are not in the screenshots.

Every change asks "Keep display configuration?" and goes back by itself after 10 seconds unless you click Keep.

### Two screens as one 3D pair

Dual projectors, mirror rigs and two-panel beam-splitter monitors show each eye on its own screen.
With Other stereo formats on and two screens enabled, Display Configuration offers a stereo pair for each screen:

- Stereo pair: the other screen of the pair.
- Pair type: Dual projection, Mirror rig, or iZ3D monitor.
- This output: Left eye or Right eye.
- Reflection (for a mirror rig): None, Horizontal or Vertical.

![The stereo pair settings](images/beta1/stereo-pair-settings.jpg)

For a beam-splitter monitor with two panels, choose Mirror rig, set one panel to Left eye and the other to Right eye, and look through the glasses.
If the picture seen through the mirror is upside down, set its reflection to Vertical; if it is mirrored left to right, to Horizontal.
If the monitor already turns the mirrored panel's picture around by itself, keep None.

Both screens of a pair must be connected to the same graphics card, with the same resolution, refresh rate and scale.
In beta 1 the stereo pair was not tested on real hardware.
In the test virtual machine the two screens were on two separate virtual cards, and the pair was refused, as expected; please report how it works with your gear.

### Depth on the desktop

System Settings, 3D Depth, sets how far popped elements (menus, tooltips) come out of the screen and how far the background goes behind it.

## 6. From one partition per folder to one partition

The classic layout gave each system folder its own partition:

```mermaid
flowchart TB
  subgraph classic["The classic layout"]
    B["/boot"] --- R["/"] --- U["/usr"] --- V["/var"] --- T["/tmp"] --- H["/home"] --- S["swap"]
  end
  subgraph today["Sparky Stereo OS beside Windows"]
    E["EFI system partition (shared with Windows)"] --- W["Windows (C:)"] --- L["Sparky Stereo OS: one ext4 partition for /"]
  end
```

Each partition had its reasons, and each reason has a newer answer:

| Old reason | Today |
|---|---|
| `/boot` low on the disk, where the BIOS could read it | UEFI reads the EFI system partition anywhere on a GPT disk, and GRUB reads `/boot` from the root file system. |
| `/usr` read-only, or shared over the network | Debian has merged `/bin`, `/sbin` and `/lib` into `/usr`; a separate `/usr` must be mounted by the initramfs and gains nothing on a desktop. |
| `/var` so logs cannot fill the root | The systemd journal limits itself (by default to 10 % of the file system, at most 4 GB), and log rotation does the rest. |
| `/tmp` with its own size limit | In beta 1, `/tmp` is a folder on the root file system; `sudo systemctl enable tmp.mount` makes it a memory file system (tmpfs) from the next start, limited to half the RAM and empty at every start. |
| `/home` kept across reinstalls | Still a valid choice; the installer's manual partitioning creates it (below). |
| Quotas per folder | ext4 project quotas limit a folder tree without its own partition. |
| swap partition | Optional; Sparky Stereo OS sets up compressed swap in memory (zram) by itself where it helps: with 8 GB of RAM or less, or on slow storage. |

Windows does it the same way: one C: partition for the system, the programs and the users, next to a few small hidden partitions (the EFI system partition, the Microsoft reserved partition, the recovery partition).
Sparky Stereo OS joins that layout with one partition of its own and shares the EFI system partition with Windows.

One partition also means one free space: no partition runs full while another stays empty.

If you want a separate `/home` anyway, choose Manual partitioning in the installer, create the root partition and the `/home` partition in the free space, and set the existing EFI system partition's mount point to `/boot/efi` without formatting it.

![Manual partitioning](images/beta1/installer-manual-partitioning.jpg)

## 7. Installing beside Windows

### In Windows, first

1. Make room: in Disk Management (right-click the Start button), right-click the C: partition, choose Shrink Volume, and leave at least 30 GB free, more if you can.
2. Turn off Fast Startup: Control Panel, Power Options, "Choose what the power buttons do", untick "Turn on fast startup".
   Fast Startup leaves the Windows partition half closed, and changes from Linux could be lost.
3. If BitLocker is on, write down the recovery key.
   Starting Windows through a different boot path can make BitLocker ask for it.
4. Back up what matters, as before any change to partitions.

The free space stays unformatted; the installer uses it.

### The installer

Start the live session in UEFI mode, close the welcome windows, and double-click Sparky Installer on the desktop.
The installer needs no network connection.
Without a network it says that the system is not connected to the Internet; that is only a note.

| | |
|---|---|
| ![Welcome](images/beta1/installer-welcome.jpg) | Choose the language. |
| ![Location](images/beta1/installer-location.jpg) | Choose region and zone. |
| ![Keyboard](images/beta1/installer-keyboard.jpg) | Choose the keyboard layout and test it in the field below. |

On Partitions, the installer shows the disk as it is: Windows Boot Manager (the EFI system partition), the reserved partition, Windows, the free space and the recovery partition.

![The disk before](images/beta1/installer-partitions.jpg)

Choose "Replace a partition" and click the free space in the "Current" bar.
The "After" bar shows one new ext4 partition for Sparky Stereo OS in the free space, and the line below says that the existing EFI system partition will be used for starting it.
Nothing else is changed.

![Replace the free space](images/beta1/installer-replace-free-space.jpg)

"Install alongside" would shrink a partition from the installer; shrinking Windows from Windows, as above, is safer and was the tested path.
"Erase disk" removes Windows; do not choose it on a shared disk.

| | |
|---|---|
| ![Users](images/beta1/installer-users.jpg) | Your name, login name, computer name and password. |
| ![Summary](images/beta1/installer-summary.jpg) | Check the summary: one new partition, the EFI system partition kept. Then click Install. |

While it installs, the installer shows slides about the edition.
In the test virtual machines the installation took about 20 minutes.

![Installing](images/beta1/installer-slide.jpg)

When it says it is done, restart and remove the stick.

### What the installer sets up for dual boot

- The boot menu lists Sparky Stereo OS first, then its advanced options and two memory tests, then Windows Boot Manager, with a 5 second timeout.
- Windows' own boot manager and its fallback loader on the EFI system partition are left as they are.
- The hardware clock stays in local time, as Windows keeps it, so both systems show the right time.

![The boot menu of the installed system](images/beta1/grub-menu-installed.jpg)

The screenshot is from a German installation, which is why the help text under the menu is German.

The tests used a disk laid out the way Windows 10 and 11 install themselves, with a small stand-in for the Windows boot manager.
The Windows entry started that stand-in; how it starts a real Windows is something to confirm on your machine.

If you prefer the hardware clock in UTC, as Linux usually keeps it, tell Windows to read it as UTC, in a Command Prompt run as administrator:

```
reg add "HKLM\System\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal /t REG_DWORD /d 1 /f
```

and in Sparky Stereo OS:

```
sudo timedatectl set-local-rtc 0
```

## 8. After the installation

![The first start](images/beta1/first-start.jpg)

The installed system starts the same edition kernel as the stick, and under Secure Boot it uses the key you enrolled.
On a computer where the key is not enrolled, enrol it as in section 4.

The edition's package source, `repo.sparkyos.org`, is not public yet.
Updates from Debian, SparkyLinux and deb-multimedia work as usual.
Until the edition's repository goes online, `apt update` reports that source as unreachable; that message can be ignored for now.

## 9. Known issues of beta 1

- 32-bit UEFI (ia32 firmware, mostly older tablets and small laptops) does not start the image.
- The installer's slides are in English, also when the installer runs in German or another language.
- MokManager's "Press any key" screen waits only about 10 seconds (section 4).
- The edition's package repository, `repo.sparkyos.org`, is not online yet (section 8).
- The stereo pair of two screens was not tested on real hardware (section 5).
- KDE's Welcome Center opens next to Sparky Welcome at the first login.
- The GRUB menus still show SparkyLinux's blue background picture.
- Older NVIDIA cards (Pascal and before) run with nouveau (section 4).

## 10. Reporting what you find

Report on the edition's tracker: https://github.com/Sparky-OS/sparky-stereo-os/issues

Please say what you did, what you expected, and what happened, and attach what fits:

```
cat /etc/os-release
uname -r
mokutil --sb-state
inxi -Fxz
stereo-display-info
kscreen-doctor -o
journalctl -b -p warning --no-pager > journal.txt
```

`stereo-display-info` lists what each connected screen can do in 3D and deep colour, read from its EDID, and what it is doing now.

For an installation problem, copy the installer's log before you restart the live session, because the live session forgets it:

```
sudo cp /root/.cache/calamares/session.log ~/installer.log
```

and save it to another stick.

A photo of the screen helps for anything that happens before the desktop: the firmware, the stick's menu, MokManager.
