# First kernel messages after GRUB

On the installed machine, record the running kernel, boot ID, command line, console threshold and kernel messages before changing the boot.
Read the full-priority journal as well as warnings and errors.

```sh
uname -r
cat /proc/sys/kernel/random/boot_id /proc/cmdline /proc/sys/kernel/printk
sudo journalctl -b -k -p warning --no-pager
sudo journalctl -b -k --no-pager
sudo journalctl --list-boots --no-pager
```

Compare the installed versions with the signed round before assigning a result to that round.
Unpack the published binaries with `dpkg-deb -R` and inspect the boot defaults, module configuration and maintainer scripts.
Read `/boot/config-RELEASE` from each published image and inspect the source named by the corresponding `.dsc`.
A repository checkout can contain later fixes.

| Symptom | Cause, check and correction |
| --- | --- |
| `Driver 'pcspkr' is already registered` | Both `snd_pcsp` and `pcspkr` advertise `platform:pcspkr` and register a platform driver named `pcspkr`. Read both aliases with `modinfo -F alias MODULE` and check `modprobe -n -v -b platform:pcspkr` for a pending load. An already loaded module may be absent from dry-run output, so also read `/proc/modules`. For the edition's PC Speaker, blacklist the `snd_pcsp` alias and keep `pcspkr` available. Verify alias handling and the PC Speaker device after boot. |
| `ima: Can not allocate sha384 (reason: -2)` | IMA can request a crypto transform for its configured digest and for hashes in the TPM's allocated PCR banks. Check that `CONFIG_CRYPTO_SHA512=y` makes SHA-384 available during IMA initialization, read `CONFIG_IMA_DEFAULT_HASH` from the running and published configurations, and check `/proc/crypto` and the IMA journal lines. With a visible TPM 2.0 device and the tool installed, use `sudo tpm2_getcap pcrs` to check the banks. Build 18 ships SHA-512 built in and SHA-256 as the IMA default. A boot reporting TPM bypass can show the default hash works while leaving PCR bank coverage untested. |
| `Failed to setup vendor infoframe on connector DP-1: -22` | The DRM HDMI helper can return `-EINVAL` when the connector lacks HDMI InfoFrame support. Inspect the caller in the published `amdgpu_dm_connector.c`. Build 18's `fill_stream_properties_from_drm_display_mode()` already gates construction on `stream->signal` being HDMI Type A or FRL. Check the negotiated signal because a connector named `DP-1` can feed HDMI through a dual-mode adapter. Prove a change with native DisplayPort and a working HDMI control. |
| `VMX not supported by CPU` on an AMD machine | This message comes from the Intel KVM driver's VMX check. Determine who requested the load. Resolve the current CPU modalias with `modprobe -R "$(cat /sys/devices/system/cpu/modalias)"` and compare the result with the aliases of both KVM modules. Check the initramfs and `modules-load.d` before tracing requests from userspace. A supported AMD CPU should resolve to `kvm_amd`. An old message outside the retained journal cannot identify the caller. Fix a confirmed requester at its source so Intel hosts can still load their driver. |
| Errors spill onto the console after GRUB | Compare `/proc/cmdline` with the generated entry and read the first value of `/proc/sys/kernel/printk`. Linux's `quiet` handler sets the quiet console threshold, so an edition default of `loglevel=3` belongs after `quiet` for the normal entry. Respect explicit administrator settings. Compare serial console output with the same messages read from the kernel log in the guest. The console threshold controls printing to the console. Journald retention follows its own configuration. |

The speaker fix in `sparky-stereo-kernel-settings` ships `/usr/lib/modprobe.d/sparky-stereo-pcspkr.conf` and activates the `update-initramfs` trigger.
Check the rebuilt initramfs with `lsinitramfs` for that exact path and check `/sys/bus/platform/devices/pcspkr/driver` and the input device named `PC Speaker` after boot.
Inside a minimal guest, invoke the full path to kmod's modprobe to avoid a BusyBox shell selecting its own applet.
Use the merged-usr layout so the guest reads the same vendor configuration as the installed system.

The boot package's late GRUB drop-in adds the threshold only to quiet normal entries and preserves a loglevel given in either GRUB command-line variable.
A guest boot with `quiet` reaches printk threshold 4 and the new default reaches 3.
Verify that a priority-3 marker drops from the serial console and is still read from the ring buffer.
Use a priority-2 marker as the serial control and an explicit `loglevel=7` as the override control.

When the warning and the HDMI signal are both confirmed, check whether the sink advertises HDMI InfoFrames.
Paul Menzel corrected the diagnostic for HDMI sinks that omit that capability in [Linux commit 2b784f5e7869](https://github.com/torvalds/linux/commit/2b784f5e78694d4d852053b3eef3de3f0ff1d02e).

Use [the system housekeeping boot-chain recipe](../../system-housekeeping/SKILL.md#boot-chain) after changing boot defaults or initramfs contents.
