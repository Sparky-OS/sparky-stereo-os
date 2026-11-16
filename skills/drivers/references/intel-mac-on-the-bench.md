# An Intel Mac on the bench

**For anyone who must put the edition on an Intel Mac of 2013 to 2017:** what Apple's firmware needs from a USB stick, which devices need more than the kernel and why, the readings to take first and the traps found.
Written 2026-11-16 from a desk study of an iMac 21.5-inch, Late 2013 (iMac14,1, Intel Iris Pro).
Nothing in it was run on the Mac: what only the real machine can show is listed at the end.

## Working recipe

1. **Read the ISO's layout before the stick is written.**
   `xorriso -indev FILE.iso -report_system_area plain` must print `Boot record : El Torito , MBR isohybrid cyl-align-on GPT APM`, an active MBR partition 1 (type 0x00, start 64), an MBR partition of type 0xef that is the EFI image, and `APM partition type : 1 Apple_HFS`.
   The packer's command is `xorriso -as mkisofs ... -isohybrid-mbr isohdpfx.bin -partition_offset 16 ... -eltorito-alt-boot -e boot/grub/efi.img -no-emul-boot -isohybrid-gpt-basdat -isohybrid-apm-hfsplus`.
   Write the stick with `dd`, never with a tool that copies files.
2. **Prove the part a rig can prove.**
   Build a small ISO with the packer's literal command (isolinux, shim-signed's `shimx64.efi.signed` as `EFI/boot/bootx64.efi`, `mmx64.efi.signed`, GRUB's `gcdx64.efi.signed` as `grubx64.efi`, a FAT `efi.img` that holds those three and a stub `grub.cfg`), attach it to QEMU with OVMF as a USB mass-storage disk (`-device qemu-xhci -device usb-storage,drive=stick,bootindex=1`, no keys enrolled, which is what a Mac without Secure Boot looks like), and read GRUB's serial output.
   A menu entry that prints and halts reaches the end of the chain.
3. **The picker.**
   Apple's firmware lists any EFI system partition that holds `/EFI/BOOT/BOOTX64.EFI` as "EFI Boot" (Arch Wiki, Mac).
   Hold Option (Alt) at power on; hold Ctrl while choosing to make a volume the default.
   A firmware password stops the picker: it belongs to the person whose Mac it is, never bypassed.
4. **Take the readings in this order, read only.**
   In macOS: `sysctl -n hw.model`, `sw_vers`, `diskutil list`, `diskutil cs list`, `diskutil apfs list`, `nvram boot-args`, `bless --getBoot`, `fdesetup status`.
   Live: `cat /sys/class/dmi/id/product_name`, `cat /sys/firmware/efi/fw_platform_size`, `mokutil --sb-state`, `lspci -nnk`, `lsusb`, `dmesg`, `rfkill list`, `ip -br link`, `aplay -l`, `ls /sys/class/backlight`, `sensors`, `lsblk -f`, `sgdisk -p`, `efibootmgr -v`.
   Never run `system_profiler SPHardwareDataType` (it prints the serial number); the model name answers from `hw.model` and DMI.
5. **Check every device against the kernel's source and the ISO's package list**, not against recall: the PCI or USB id in a public probe (linux-hardware.org, several machines of the model), the driver's id table in the kernel tree, the option in the published headers package's `.config`, the firmware's name in `MODULE_FIRMWARE` and in Debian's `Contents-all.gz` for each component (checked against the SHA-256 lines of `dists/testing/Release`).

## The devices of the 2013 iMac that need more than the kernel

- **Wi-Fi, Broadcom BCM4360 (PCI 14e4:43a0).** No driver of the kernel drives it.
  `bcma` claims the bus; `brcmfmac` knows chip 43602 only; `brcmsmac` binds 802.11 core revisions 17, 23 and 24; `b43` has an AC-PHY source file built by `CONFIG_B43_PHY_AC`, which no Kconfig defines.
  The driver is Broadcom's `wl`, Debian's `broadcom-sta-dkms` (non-free), which needs `dkms`, a compiler and the running kernel's headers.
  Its licence allows distribution "complete, unmodified and only for use with a Broadcom Product", with the agreement accompanying it and an indemnity (clause 2.3): carry Debian's unmodified package and install it only for a matching card, with the licence shown.
  Debian's 6.30.223.271-32 built `wl.ko` on kernel 7.3.1 headers with DKMS 3.4.4 (no hardware: it builds, it was not loaded).
- **Bluetooth, Apple (USB 05ac:828d).** `btusb` and `btbcm` bind it; the patch-RAM file is not in Debian, so the kernel logs "BCM: firmware Patch file not found, tried:" and continues.
- **Ethernet, BCM57766 (PCI 14e4:1686).** `tg3` needs `tigon/tg357766.bin` from `firmware-misc-nonfree`, redistributable "provided this copyright notice is accompanying it".
- **Audio.** `snd_hda_codec_cs420x` carries a quirk named for the machine (`SND_PCI_QUIRK(0x106b, 0x0600, "iMac 14,1", CS420X_IMAC27_122)`): nothing to add, nothing to prove without hearing it.
- **Graphics.** `i915` on Haswell loads no firmware (GuC, HuC and DMC begin at gen9).

## Traps

- **Symptom: the stick is not listed under Option.**
  Causes seen in the documentation: no `EFI/BOOT/BOOTX64.EFI` on an EFI partition the firmware reads; a layout without the Apple partition map that the stick's maker left out; the file-copy mode of a writing tool; a firmware password.
  Fix: read the layout (recipe step 1), write with `dd`, try another rear port, ask about the password.
  How it was found: `xorrisofs(1)` says the Apple partition map "is read by Macs for booting and for mounting", and a packer without the flag writes no such map, so read the layout instead of assuming it.
- **Symptom: no network and no Wi-Fi device on a Mac with a Broadcom 802.11ac chip.**
  Cause: `wl` is not on the ISO and the free drivers do not support the chip.
  Fix: a wire for Ethernet, then `apt install broadcom-sta-dkms`, restart (the package blacklists the free drivers); WPA3 networks may fail with `wl`, and power management off cures frequent disconnections (Debian wiki, wl).
  How it was found: `grep broadcom-sta` over the ISO's package list printed nothing.
- **Symptom: the installer's "install alongside" cannot make room next to macOS.**
  Cause: KPMcore supports no shrinking of APFS (`apfs.cpp` has Move, Copy and Backup only) and none of HFS+ (`hfsplus.cpp`: `m_Shrink = cmdSupportNone`); FileVault and Fusion (CoreStorage) volumes are not readable by it either.
  Fix: the person whose Mac it is makes the room in macOS first; manual partitioning reuses the existing EFI partition.
- **Symptom: after the install the Mac starts macOS again.**
  Cause: the firmware starts the volume its own default variable names; Linux boot entries in the NVRAM are not what decides it.
  Fix: choose the entry from the Option picker, hold Ctrl to keep it as the default.
- **Symptom: `sgdisk -v` on a hybrid ISO says the MBR partitions overlap.**
  Cause: by design, the same as Debian's own live images: xorriso marks the EFI image inside the ISO partition (`-isohybrid-gpt-basdat`, "an actually invalid GPT"); the MBR type 0xef partition is what EFI uses to boot from a stick.
  Fix: none; do not "repair" it.
- **Symptom: a container cannot install `hfsprogs` or `broadcom-sta-dkms`.**
  Cause: `hfsprogs` is not in Debian testing (the edition's repository carries it); `broadcom-sta-dkms` is in `non-free`, which a minimal container's sources may leave out.
  Fix: add `contrib non-free non-free-firmware` to the Components line inside the container, and drop a file-based repository whose Release file is missing.

## Perks

- No T2 chip exists on Macs before 2018, so an iMac of 2013 has no security chip between the firmware and the stick, and no Secure Boot: shim finds none enabled, and the kernel needs no signature for modules.
- Three public probes of one model already say which driver loads on a recent kernel; a model's probes are a cheap second opinion for the id table.
- The model's own kernel quirks can be read from the sound codec drivers, so "the kernel has a quirk for this machine" can be a verified sentence.

## Not proven here (the real machine only)

The Option picker with the stick, whether Apple's firmware accepts the Apple partition map entry that points at a FAT image, the panel, speakers and microphone, Bluetooth without the patch-RAM file, the camera, brightness, Thunderbolt, fan values, loading `wl` on the real chip, and the whole install.
