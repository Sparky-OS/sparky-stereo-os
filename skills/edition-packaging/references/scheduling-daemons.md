# ananicy-cpp, its rules and the sched_ext schedulers: recipes, defaults and traps

Packages of ORDER 108's processor-governance clause: `ananicy-cpp`, `cachyos-ananicy-rules`, `scx-scheds` and `scx-tools`. Part of the [`edition-packaging`](../SKILL.md) skill.

## The default state of a service follows what the gaming distributions ship, read at their primary files

Daniel's rule (2026-11-02, kernel tunings): a value a main gaming distribution ships is his design, each naming the distribution and file; a value none ships needs his word. A service's enablement is such a value. Read on 2026-11-16:

| Service | CachyOS | Bazzite | The edition |
| --- | --- | --- | --- |
| `ananicy-cpp` | enabled: `cachyos-settings.install` (CachyOS-PKGBUILDS) `SERVICES=("ananicy-cpp" …)` and `post_install` runs `systemctl enable`; the package Depends on `ananicy-cpp` and `cachyos-ananicy-rules` | not shipped (no hit in `build_files/` or `system_files/` at main 69db4d1cf118) | the two differ: unit installed and off until Daniel answers |
| `scx` schedulers and loader | packages `scx-scheds` and `scx-tools` enable nothing (their PKGBUILDs have no `install=`) | installed, then `systemctl disable scx_loader.service` (`build_files/bazzite/12-finalize.sh:161`); the Steam Deck image lets steamos-manager switch it (`platform.toml`) | both ship it off: off |

Look in the installer's service list too (`cachyos-calamares`'s `services-systemd.conf` lists none of these) and in the image's finalize scripts, not only in the package.

## ananicy-cpp

- Source: the upstream tag `v1.2.0` (2026-03-26) plus its three later commits; the build tree's `upstream/ananicy-cpp` is at them (3554447c). The Fedora spec in the tree still says 1.1.1: read the tags, not the spec. Built as Arch builds it for CachyOS (gitlab.archlinux.org `packages/ananicy-cpp` PKGBUILD): `-DUSE_BPF_PROC_IMPL=ON -DBPF_BUILD_LIBBPF=OFF -DENABLE_REGEX_SUPPORT=ON`, the system fmt, spdlog and nlohmann_json.
- **What the BPF listener costs:** build dependencies (clang, libbpf-dev, libelf-dev, bpftool, libpcre2-dev), run-time libbpf1 and pcre2, a kernel with BTF and BPF permission for the daemon, and a failure mode: where the BPF object cannot be loaded (an unprivileged container) the daemon prints `failed to load BPF object: -1`, dies of SEGV, and leaves its shared-memory singleton (`/dev/shm/AnanicyCppMutex`), so systemd's restarts say "Ananicy Cpp is already running!" (upstream issues 88 and 90 are open). It does not fall back to scanning.
- **Proof under systemd** (no `--privileged`): an image with `systemd`, `systemd-sysv` and `dbus`, run with `--cgroupns=private --security-opt writable-cgroups=true --tmpfs /run --tmpfs /run/lock --tmpfs /tmp` and **`--cap-add SYS_NICE`** (without it the daemon cannot set an I/O priority and reports "Insufficient permission to set io-priority" for every process, and then sets nothing). Install the two packages with apt, read `systemctl is-enabled` (disabled) and `is-active` (inactive), write one rule in `/etc/ananicy.d/`, start two copies of `sleep` under different names, `systemctl start ananicy-cpp`, and read the nice value and `ionice -p` back. The packaged BPF build was not exercised: loading a BPF program needs host privileges that a test should not grant; the proof ran the same source built without BPF.
- `cachyos-ananicy-rules`: the repository's files into `/etc/ananicy.d` less README.md, sort-games.sh, the two schemas, lint.py and Makefile, as CachyOS's PKGBUILD does. The tag is a plain tag; the licence file is the GPL-3 text and no rule file carries a notice. 361 rule files are conffiles. `ananicy-cpp` Depends on it (a designed feature's dependency is a Depends).

## A package that Depends on a sibling not yet published

The archive link and start gate refuses `Depends: cachyos-ananicy-rules` ("none of the choices are installable") until the sibling is in the tree. Build the sibling first and name it in `SPARKY_LC_SIBLINGS_FILE` (a file listing its `.deb` paths); the gate then takes it as authoritative.

## scx-scheds and scx-tools (Rust, vendored)

- Sources: `scx` at the signed tag `v1.1.4` (Tejun Heo; the build tree's copy is 149 commits older and is not used) and `scx-loader` at `v1.1.3` (CachyOS's `scx-tools`; its tag signer's key has no user ID on keys.openpgp.org, so the signature cannot be checked: said in the recipe). The loader is a separate repository; the units for the schedulers are `services/scx.service` and `services/scx` in `scx`, and the loader's units, D-Bus file, polkit policy and configuration are installed by its own `xtask install --destdir`.
- **The network-free source:** `cargo vendor --locked vendor` and its `.cargo/config.toml` go in the orig archive (`make-orig.sh` of each recipe, run where cargo is). Measured: scx 1045 MiB and 762 crates unpacked, about 95 MiB as `orig.tar.xz`; the loader 405 MiB and 285 crates, about 27 MiB. The orig archives go to the pool, not to GitHub.
- The workspace is built as CachyOS builds it (`cargo build --release --frozen --workspace` less scx_rlfifo, scx_mitosis, scx_characterize, xtask, vmlinux_docify and the two arena self-test crates); one scheduler alone (`-p scx_lavd`, 190 crates) took 6 minutes at 2 CPUs.
- Lean Code: `debian/sparky-lean-languages.json` is `["c", "rust"]`, and `lean.debian_prepare` gets `--preserve-source 'vendor/*'`, so cargo's `.cargo-checksum.json` check still passes (a `'.cargo/*'` pattern matches no file and is refused). Two more files are needed: `debian/sparky-lean-rust-readers.json` (the one procedural macro that asks for the caller's file, `linktime-proc-macro`, reviewed: it uses the path only) and, for the C check, an unversioned `clang` beside `clang-22` in Build-Depends.
- **Measured, 2026-11-17 (2 CPUs, container):** the whole workspace builds 21 scheduler binaries plus `scxtop` in about 35 minutes (432 crates, then the schedulers one after another); `scx-scheds` is 24.9 MB installed as one deb, `scx-tools` 2.3 MB. The loader's `default_sched` is none, and its D-Bus file names `SystemdService=scx_loader.service`, so a call to `org.scx.Loader` starts the loader even though the unit is disabled; it loads no scheduler until asked.
- **BPF needs clang 22.** `scx_nitosis` refuses clang 21 at build time: set `BPF_CLANG=clang-22` in `debian/rules` (Build-Depends `clang-22`, `llvm-22`).
- `dh_auto_test` runs `scx_lavd --version`: a scheduler binary starts far enough to print its version without loading anything into the kernel. Never start a scheduler on a machine in use.

## Traps

- **`dh` runs its test step before the install.** A recipe that checks the installed tree in `override_dh_auto_test` sees nothing; put the checks at the end of the install override.
- **`set -e` and a command substitution hide a failing build.** `runuser … build.sh; echo "exit=$?"` under `set -e` ends the script silently: use `cmd && echo ok || echo FAILED`.
- **The CachyOS kernel is no longer a patch.** `compaction_proactiveness` and the read-ahead are in `CachyOS/linux` (`mm/compaction.c`, `include/linux/pagemap.h` at the tag `cachyos-7.3.4-1`), under `CONFIG_CACHY`; `CachyOS/kernel-patches` has only `misc` and `sched` for 7.3.
