# The zram and zswap gate: what it refuses, what it lets through, and a retiring unit it can read

**For the person who writes or reviews a package of the edition that touches zram or zswap, and for whoever reads the gate's verdict.**
Written on 2026-11-14 from the work that made the gate exact, after it refused the edition's own package that only retires an unchosen zram.
The gate is `sparky-os/iso-build/zram-check.py` in the build repository; its tests are `sparky-os/iso-build/tests/test-zram-check.py`.
It runs on every publication (`publish-tree.sh`, before anything is copied or signed) and on every image (`rootfs.sh`, `pack.sh`, `check-iso.sh`).

The rule it guards is Daniel's: zram and zswap are never set up by the edition, and the person's own choice is never capped.
Daniel, 2026-11-02: "do not compress or put anything to run from the RAM regarding swap"; 2026-11-03: "we don't cape user choice".
So two things must both pass through it: nothing of ours sets zram up, and a package of ours may still retire the zram an older edition left.

## The short recipe

1. Run the gate on your package before you stage it: `python3 sparky-os/iso-build/zram-check.py --debs YOUR.deb`.
   Exit 0 prints `zram/zswap gate: passed` and then one `note:` line for each tear-down it let through; exit 1 prints each finding with its file and line.
2. Read every note: each must be something you meant to ship.
   A note is not a warning; it is the record of what was let through and why.
3. On a refusal, change the package, never the gate.
   If you believe the gate is wrong, add a failing test for the form first, then make the gate read it.

## What it refuses

Each of these refuses wherever it is found: a package's files, its maintainer scripts, an image's trees, an ISO's boot menus.

| Form | Source |
|---|---|
| A relation that pulls a zram package in (`Depends`, `Pre-Depends`, `Recommends`, `Provides`) or keeps the person from one (`Conflicts`, `Breaks`) | Debian Policy 7.2 to 7.5 |
| A zram-generator configuration (`zram-generator.conf`, `zram-generator.conf.d`), a generator named after zram, zram-tools' `zramswap` files | zram-generator.conf(5) |
| `zramctl` with `--find`, `--size`, `--algorithm`, `--streams` or `--algorithm-params` | zramctl(8) |
| A write to `disksize`, `comp_algorithm`, `max_comp_streams`, `mem_limit`, `backing_dev` or `algorithm_params` of a zram device | the kernel's `Documentation/admin-guide/blockdev/zram.rst` |
| Any read or write of `/sys/class/zram-control/hot_add` | zram.rst: "In order to add a new /dev/zramX device, perform a read operation on the hot_add attribute" |
| `mkswap` or `swapon` on `/dev/zram*`, an fstab line or a `What=/dev/zram*` | swapon(8), systemd.swap(5) |
| `modprobe zram`, `zram` in `modules-load.d`, `options zram` in `modprobe.d` | modprobe(8) |
| A udev rule that sets an attribute of, or runs a program for, `KERNEL=="zram*"` | udev(7) |
| `zswap.enabled` true or `systemd.zram` true on a kernel command line, `CONFIG_ZSWAP_DEFAULT_ON=y`, a true value written to `/sys/module/zswap/parameters/enabled` | the kernel's `Documentation/admin-guide/mm/zswap.rst` |
| A preset that enables a zram unit | systemd.preset(5) |
| A compiled file that carries `zram-generator.conf`, the edition's former switch or `zswap.enabled=1` | the gate's own token list |

Inside a zram unit, a drop-in of one, or the script either runs, these refuse too:

- `systemctl start`, `restart`, `enable`, `preset`, `unmask` or `isolate` of a zram unit the package does not ship;
- `apt-get install` of a zram package, or of a package the line does not name;
- `zram-generator --setup-device` (what Debian's `systemd-zram-setup@.service` runs) and `zramswap start`;
- a set-up attribute written through a path the line does not spell (`echo 4G > $d/disksize`);
- a setting that pulls a zram unit of another package in (`Wants=`, `Requires=`, `Upholds=`, `OnSuccess=`, `Also=`);
- a mask of a zram unit, and `ExecCondition=/bin/false` on one: both keep the person's zram from starting, which caps their choice.

## What it lets through, with a note

A tear-down stops, resets or removes zram, or reports; it sets nothing up.

| Form | Source |
|---|---|
| `echo 1 > /sys/block/zramN/reset` (any positive number) | zram.rst, "Reset": "Write any positive value to 'reset' sysfs node" |
| A write to `/sys/class/zram-control/hot_remove` | zram.rst, "Add/remove zram devices" |
| `swapoff /dev/zramN` | swapoff(8) |
| `systemctl stop`, `disable` or `kill` of a zram unit | systemctl(1) |
| `modprobe -r zram`, `rmmod zram` | modprobe(8), rmmod(8) |
| `zramctl --reset`, `zram-generator --reset-device`, `zramswap stop` | zramctl(8), zram-generator(8) |
| `apt-get purge`, `remove` or `autoremove` of a zram package | apt-get(8) |
| A false value written to `/sys/module/zswap/parameters/enabled` | zswap.rst |
| A drop-in for another package's zram unit that only adds a condition, a limit, an order, a description or a failure handler | systemd.unit(5) |
| A link that starts a unit of the same package which itself passes | systemd.unit(5) |
| A `/dev/null` link that masks one drop-in of a zram unit | systemd.unit(5): it takes a setting away and adds none |

Reading is free and gets no note: a file test, a comparison, `cat`, `awk`, `grep`, `zramctl` with no set-up option, `systemctl is-active`.

## How the gate reads a unit

A file below systemd's `system` or `user` folder is read as a zram unit when zram or zswap is named on its way (its own name, the drop-in folder it sits in), in what a link points to, or in one of its settings.
A comment does not make it one.
The gate then reads, never the name alone:

1. every `Exec` setting, as a command line of its own;
2. the program that line runs, when the package ships it: the whole script, every line, and every other script of the package that it names;
3. the units of the same package that the settings name (`OnFailure=`, a `.wants` link, a timer's service).

A unit passes only when all of that passes.
A unit that carries a tear-down and anything refused gets one more finding, `does both`, so the tear-down is not read as the reason.

## A retiring unit the gate can read

Write it so that every act on zram is spelled on its own line, in a file the package ships.

```ini
[Unit]
Description=Remove the compressed swap generator an older edition left installed (once)
ConditionPathExists=/var/lib/PACKAGE/leftover-zram-generator

[Service]
Type=simple
ExecStart=/usr/libexec/PACKAGE/retire --purge-leftover

[Install]
WantedBy=multi-user.target
```

```sh
if awk '$1 == "/dev/zram0" { f=1 } END { exit !f }' /proc/swaps; then
    systemctl stop dev-zram0.swap || true
    swapoff /dev/zram0
fi
if [ -r /sys/block/zram0/disksize ] && [ "$(cat /sys/block/zram0/disksize)" != 0 ]; then
    echo 1 >/sys/block/zram0/reset
fi
```

- **Ship the script.** A program the package does not ship, a compiled one, or a link that leaves the package cannot be followed and is refused. Programs whose command line says all they do (`systemctl`, `swapoff`, `apt-get`, `modprobe`, a shell with `-c`) are judged by that line.
- **Spell the device.** Write `/dev/zram0` and `/sys/block/zram0/reset` where they are used. A path kept in a variable (`d=/sys/block/zram0`) is refused in a unit's script, because the next line can write anything through it.
- **Write the reset with its number.** `echo 1 >…/reset` passes; `echo $n >…/reset` does not.
- **Hold a unit of another package with a drop-in, not a mask.** `ExecCondition=` on your own shipped script, `ConditionPathExists=`, `StartLimitIntervalSec=` and `OnFailure=` are what a drop-in may add. To report a failure, name a unit of your own in `OnFailure=`; `ExecStartPre=`, `ExecStopPost=`, `Environment=` and any other setting in such a drop-in are refused.
- **No text made at run time.** `eval`, a download piped to a shell, `exec()` and decoded text are refused: the gate cannot read what they run.
- **Shell text inside a Python script is read line by line** like any other line, so keep each command of that text on one source line.
- **Prose is read as code.** In a unit's script every line that is not a `#` comment is judged, a docstring too. A sentence such as "systemctl restart of the zram unit" in a docstring reads as a start; put it in a `#` comment.

## The verdict's lines

```
zram/zswap gate: passed, nothing of zram or zswap of ours in N package(s), 0 refused (...).
zram/zswap gate: K tear-down(s) let through, each read to its end. A tear-down stops, resets or removes zram, or reports; it sets nothing up:
  note: PACKAGE.deb: /path:LINE: the line (what it is: a tear-down)
  note: PACKAGE.deb: /path/unit.service: a zram unit that only stops, resets, removes or reports: runs /path/script, read to the end; K tear-down line(s) in what it runs, no set-up
```

```
zram/zswap gate: refused, N finding(s) and M unreadable in ...:
  PACKAGE.deb: /path:LINE: the line (what it is)
```

Exit 0 is a pass, 1 a refusal (a finding, or a file that could not be read), 2 a wrong call.
The notes go to standard output on a pass and to standard error, after the findings, on a refusal.

## Proving a retiring package in a virtual machine

No zram device is made on a build machine: the proof runs in a guest.
The guest that proved the retiring package (2026-11-14): QEMU 11.1.2 without KVM (`-accel tcg,thread=multi -cpu max`, under two minutes for a case of two boots), the edition's own kernel (zram is a module there, `CONFIG_ZRAM=m` from Debian's configuration), Debian's `systemd-zram-generator` 1.2.1 with its own `/usr/lib/systemd/zram-generator.conf`.

1. Make the root file system in a throwaway container (`apt-get install systemd-sysv udev kmod python3 apt initramfs-tools systemd-zram-generator`, then the packages under test and the kernel with `dpkg -i`), `docker export` it, and turn the tar into a disk with `mke2fs -t ext4 -d root.tar disk.img 1500M` (e2fsprogs 1.47.4 read the tar here; no root and no loop device needed).
2. Make the state of an upgraded edition the way the package's own test does: `apt-mark auto systemd-zram-generator` and the marker its old `preinst` wrote. For the chosen case, `apt-mark manual` before the zram unit is judged (a unit with `DefaultDependencies=no`, `Before=systemd-zram-setup@zram0.service`).
3. A unit after `multi-user.target` prints the facts, installs the new package with `apt-get install ./FILE.deb`, prints them again and restarts; on the second boot it prints them once more and powers off.
   The facts: the package versions, `apt-mark showauto` and `showmanual`, `/proc/modules`, `/sys/block/zram0/disksize`, `/proc/swaps`, `systemctl --failed`, the units' `Result` and their journal.
4. Boot with `-kernel`, `-initrd`, `-append 'root=/dev/vda rw console=ttyS0'`, `-serial file:LOG`, `-nic none`, and read the facts from the log.

What a pass looks like: unchosen, after the purge and a restart, no zram module, no `/sys/block/zram0`, no swap, no failed unit; chosen, `/dev/zram0` in `/proc/swaps` before the upgrade, after it and after the restart.
In the boot in which Debian's generator still ran, the zram module is loaded and an empty `zram0` node exists (`disksize` 0): the generator loads the module itself; that node is not a set-up device and is gone at the next boot.

## Traps met

- **Symptom:** the gate refuses a package whose units only retire zram, with `a zram unit` on each unit's name and `a zram device set up through sysfs` on a line that writes `1` to `reset`.
  **Cause:** before 2026-11-14 the gate judged a unit by `zram` in its file name, and took any write on a line that also named `disksize` for a write to it; the line read `disksize` and wrote `reset`.
  **Fix:** the gate reads what the unit and its script do, and a sysfs set-up is the attribute that is written.
  **Found by:** reading each of the five findings against the file: none could make or grow a device.
- **Symptom:** the same gate passed two drop-ins of the same package in `systemd-zram-setup@zram0.service.d/` for weeks.
  **Cause:** their file names (`50-…-migration.conf`) had no `zram`; only the folder did.
  **Fix:** a drop-in is read by the folder it sits in.
  **Found by:** listing the published package beside the refused one.
- **Symptom:** a guest built from `docker export` boots, but swap units are `not-found` and nothing of zram is ever tried.
  **Cause:** the export carries `/.dockerenv`, so the guest's systemd believes it is in a container, where swap units do not exist.
  **Fix:** `tar --delete -f root.tar .dockerenv` before making the disk; check with `systemd-detect-virt`, which must say `qemu`.
  **Found by:** printing `systemd-detect-virt` among the facts: it said `docker`.
- **Symptom:** the proof unit runs, the guest restarts as scripted, and none of its lines are in the serial log.
  **Cause:** the script had opened `/dev/ttyS0` itself; the serial getty started next and hung up every earlier opener of the line.
  **Fix:** let the unit write (`StandardOutput=journal+console`), never the script.
  **Found by:** the log showed the unit's `Started` and `Stopped` lines and the restart, with nothing between.
- **Symptom:** a test expects a failed zram unit on the old package and the guest shows none.
  **Cause:** the failure on real machines was a start limit hit by several starts within seconds; a small guest starts the unit once, and the guard's skip (`Result=exec-condition`) is not a failure.
  **Fix:** none needed for the retiring proof; say that the guest did not reproduce the start limit, and keep the package's own test for it.

## Credits

zram-generator is by Zbigniew Jędrzejewski-Szmek, Igor Raits and наб, at [systemd/zram-generator](https://github.com/systemd/zram-generator); Debian's `systemd-zram-generator` is packaged by the Debian Rust Maintainers (Arnaud Ferraris, Ben Westover, Clay Stan).
zram-tools is by Jonathan Carter, who also maintains it in Debian.
The kernel's zram driver and its documentation are maintained by Minchan Kim and Sergey Senozhatsky.
