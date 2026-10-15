# GPU vendors' repositories on Sparky Stereo OS: compute updates, the display driver stays ours

Sparky Stereo OS drives the screen with its own display drivers, because they carry HDMI 3D and deep colour: our build of NVIDIA's open kernel modules, and the amdgpu driver in our kernel.
NVIDIA and AMD publish their own display drivers in the same repositories as CUDA and ROCm.
If one of those repositories is given a high priority, an ordinary upgrade replaces our driver with the vendor's, which has no HDMI 3D.
The files below let CUDA and ROCm update as usual and keep the display driver ours.
A pin for a repository that is not configured does nothing, so every install carries them.

## How apt chooses, in short

From [apt_preferences(5)](https://manpages.debian.org/testing/apt/apt_preferences.5.en.html):

- A record that names packages (`Package: some-name`) decides the priority of the versions it matches; the first such record that matches wins, and it beats any record for `Package: *`, whatever the numbers.
- Files in `/etc/apt/preferences.d` are read in lexical order, so a file whose name starts with `10` is read before `nvidia-driver-pin`.
- A priority of 1000 or more installs a version even as a downgrade; a negative priority never installs it.
- `Pin: version 615.71.09-2*` is a prefix match.
  A pattern with a leading `*` is not a glob as one would expect: apt drops the trailing `*` first, so `*~rc*` matches only versions that end in `~rc`.
  A regular expression between slashes, `/~rc/`, matches anywhere.

## NVIDIA

| File | Ships in | What it does |
|---|---|---|
| `/etc/apt/preferences.d/10sparky-stereo-nvidia-driver-lock` | `sparky-stereo-nvidia-driver-lock`, built with our module `nvidia-kernel-open-dkms-stereo3d` from the same source and version, and required by it | NVIDIA's and Debian's own NVIDIA kernel module packages: never (-1). Every NVIDIA driver package at the version our module is built for (today 615.71.09-2): 1005. The same packages at any other version: 100. The lock package itself follows our repository (1001). |
| `/etc/apt/preferences.d/sparky-stereo-gpu-nvidia` | `sparky-stereo-hardware` | NVIDIA's container toolkit at 990 from both NVIDIA repositories, so the two copies NVIDIA publishes of each version stop swapping at every upgrade ([NVIDIA/nvidia-container-toolkit#2137](https://github.com/NVIDIA/nvidia-container-toolkit/issues/2137)); its release candidates at 100. Our `libnvidia-egl-wayland1` over the copy in NVIDIA's CUDA repository. |

The set of driver packages is the one NVIDIA's own `nvidia-driver-pinning-<version>` package pins, by source package, so a new library NVIDIA adds to the driver is covered without a change here.
The version includes NVIDIA's Debian revision (`615.71.09-2`, not `615.71.09`), because our module provides `nvidia-kernel-open-dkms` at exactly that revision and NVIDIA's `nvidia-driver` depends on exactly that revision.
CUDA packages are not in the lock and keep updating.
Some CUDA meta packages name a minimum driver (`cuda` 13.1 to 13.3 depend on `nvidia-open (>= ...)`; 13.4 does not); one that needs a newer driver than ours waits until our module moves (measured with a test package).

**Measured** in a Debian testing container with NVIDIA's real repositories at Daniel's priorities (1002 and 1003) and a newer driver 620.10.01 published beside them (test packages built from NVIDIA's own control fields):

| Without the lock | With the lock |
|---|---|
| `apt-get install nvidia-open` or `cuda-drivers` removes our module and installs NVIDIA's 620 | Both install at 615.71.09-2; nothing removed |
| `apt-get full-upgrade` with the classic solver (`--solver internal`) does the same | No change, with either solver |
| apt 3.3's default solver keeps 37 packages back at every upgrade | No change |

The edition's hardware setup adds NVIDIA's CUDA repository at 1002, so this applies to every NVIDIA install of the edition, not only to developers' machines.

### Moving the driver to a new version

1. Rebuild our module first: rebase the patches on NVIDIA's new tree and add a changelog entry with NVIDIA's new version (for example `620.10.01-1+stereo3d1`).
   The control fields and the lock are generated from it.
2. Nothing to change in `sparky-stereo-hardware`: since 0.1.6 its NVIDIA setup reads the version from the module in the repository (its version without the `+stereo3d` suffix), so the two cannot drift.
3. Publish.
   The first upgrade on each machine installs only the new lock, because the old one still holds the driver.
4. The next upgrade moves our module and NVIDIA's userspace together, with nothing removed (measured with both of apt's solvers).

The lock is a package of its own because a lock inside the module could never move: the old lock holds `firmware-nvidia-gsp` at the old version, the new module needs it at exactly the new version, and apt keeps the new module back for ever (measured).

To leave our module for NVIDIA's own driver, purge both packages: `apt purge nvidia-kernel-open-dkms-stereo3d sparky-stereo-nvidia-driver-lock`.
Removing without purging keeps the configuration file, and with it the lock.

## AMD

| File | Ships in | What it does |
|---|---|---|
| `/etc/apt/preferences.d/sparky-stereo-gpu-amd` | `sparky-stereo-hardware` | AMD's out-of-tree kernel driver, from any source: never. Every package whose name contains `amdgpu`, and AMDVLK, from AMD's repositories (Release origin `repo.radeon.com`): never. `amdgpu-install` and `amdgpu-insecure-instinct-udev-rules`: available as usual. |

What AMD publishes, from AMD's own pages and package indexes:

- **The kernel driver.** AMD's [Debian installation page](https://instinct.docs.amd.com/projects/amdgpu-docs/en/docs-31.60.0/install/detailed-install/package-manager/package-manager-debian.html) adds `https://repo.radeon.com/amdgpu/31.60/ubuntu noble` and installs `amdgpu-dkms`, which depends on `amdgpu-dkms-firmware`; both replace the former `rock-dkms` and `rock-dkms-firmware`.
  Our kernel's amdgpu carries the HDMI 3D changes, so these never install, and the `amdgpu` meta package, which depends on `amdgpu-dkms`, cannot pull them in.
- **Graphics.** `repo.radeon.com/graphics` (the `graphics` use case of [amdgpu-install](https://rocm.docs.amd.com/en/latest/install/rocm.html)) publishes AMD's own Mesa, libdrm, Wayland and LLVM builds as `*-amdgpu` packages under `/opt/amdgpu`: `amdgpu-lib`, `libgbm1-amdgpu`, `libegl1-amdgpu-mesa`, `libgl1-amdgpu-mesa-glx`, `libdrm2-amdgpu`, `libdrm-amdgpu-amdgpu1`, `mesa-amdgpu-vulkan-drivers` and the rest.
  Every one of them depends on `amdgpu-core`, whose install script writes `/etc/ld.so.conf.d/20-amdgpu.conf` and puts `/opt/amdgpu/lib` ahead of the system's libraries for every program.
  **Measured:** with three of them installed, our own Mesa loads AMD's `libgbm`, `libdrm` and `libdrm_amdgpu`.
  `mesa-amdgpu-vulkan-drivers` also ships `/etc/environment.d/10-mesa-amdgpu.conf` with `VK_LOADER_DRIVERS_DISABLE=radeon_icd.*`, which turns off the distribution's Vulkan driver in the whole session.
- **ROCm**, untouched and updating as usual.
  AMD's ROCm for Debian 13 (`https://stable.repo.amd.com/rocm/core/packages/debian13/`, [install page](https://rocm.docs.amd.com/en/latest/install/rocm.html)) and the ROCm that `amdgpu-install` sets up (`repo.radeon.com/rocmradeon`) depend on none of the packages above.
  In the older ROCm 7.2 repository only `rocdecode` and `rocjpeg` need AMD's graphics Mesa, so those two do not install here.

**Measured** with every AMD repository AMD documents for Debian 13 configured at 1002: `amdgpu-dkms`, the `amdgpu` meta package, `amdgpu-lib` and `amdgpu-core` are refused, the i386 copies too; our Mesa stays the candidate; Debian's `libdrm-amdgpu1` and `xserver-xorg-video-amdgpu` are untouched; the full ROCm meta package resolves without any of them, a ROCm package installs and would upgrade from 10.0 to 10.1, and no `/opt/amdgpu` appears.

## Intel

Not guarded.
i915 has allowed HDMI stereo modes upstream since 2013 (`connector->stereo_allowed = true` in [`intel_hdmi.c`](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/i915/display/intel_hdmi.c)), so the edition has no Intel display driver of its own to protect.
