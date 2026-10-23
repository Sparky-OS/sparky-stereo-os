---
name: user-groups
description: >-
  Give every desktop user the Unix groups the edition's hardware and programs need, however the account is made, and add a group when a feature needs one; never a root-equivalent group.
---

# User groups for desktop users

## Working recipe

1. Before adding a feature that sits behind a Unix group, find where the group is checked: a udev rule, a polkit rule, a daemon's configuration, or the package's postinst.
2. Add the group to the one list, with that reason, and run the package's tests, the control that must fail included.
3. Never change an existing account; print what it would need instead.

**Check freshness first.**
Written on 2026-10-14 for `sparky-stereo-user-groups` 0.1.0; published on 2026-10-23.
The package's own README in [the build tree](https://github.com/Sparky-OS/sparky-stereo-os-build/tree/main/sparky-os/packages/sparky-stereo-user-groups) holds the current list and the reason for each group; it wins over this page.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

## Why

Daniel, 2026-10-10: "this is a pain all the time for users coming from windows, where they don't even know this type of thing exists".
People coming from Windows do not know Unix groups exist, so "permission denied" on a wheel, a serial board, a printer or a virtual machine is the edition failing them.

## The rule

- **One list:** `/etc/sparky-stereo/user-groups`, a conffile of the `sparky-stereo-user-groups` package, one group per line, each with a comment saying what needs it.
- **The groups (0.1.0):** games, dialout, plugdev, audio, video, bluetooth, netdev, lpadmin, scanner, kvm, render and sambashare.
- **Add a group only** when a package the edition installs or recommends needs it, and cite where the group is checked.
- **Never a group that equals root, reads every keystroke, the password hashes or every log:** root, adm, admin, disk, docker, input, kmem, lxd, operator, podman, shadow, staff, sudo, sys, systemd-journal, tty, wheel, or any group whose gid is 0. `sparky-stereo-user-groups apply` and `check` refuse such a list.
- **libvirt stays out** (Daniel, 2026-10-14): its members can act as root through system VMs. kvm stays, for user-session VMs.
- **Administration stays sudo** for the administrator account (the installer's first user, which gets Sparky's own sudo and wheel from the calamares package, or an administrator made in System Settings).
- **Existing users never change**, on install or later. `sparky-stereo-user-groups propose` prints the `usermod -aG` line each local user would need and runs nothing.

## One mechanism for the three ways an account is made

| Way | Where the groups go | Why it works |
|---|---|---|
| adduser | `EXTRA_GROUPS` and `ADD_EXTRA_GROUPS=1` in a marked block at the end of `/etc/adduser.conf` | adduser reads one file, and the last assignment wins ([adduser.conf(5)](https://manpages.debian.org/testing/adduser/adduser.conf.5.en.html)) |
| System Settings, Users page | the same block | Debian's AccountsService (23.13.9-8) creates accounts with `/usr/sbin/adduser --add-extra-groups`, not useradd; measured in a container. Measure before assuming |
| The installer (Calamares) | `/etc/calamares/modules/users.conf`, generated from the calamares package's `/usr/share/calamares/modules/users.conf` with the groups added to `defaultGroups` (`must_exist: false`, `system: true`) | Calamares reads the `/etc` file first. The generated file is marked, a dpkg trigger regenerates it when the calamares package changes the shipped one, and an administrator's own `users.conf` is never overwritten |

- `sparky-stereo-user-groups apply` writes all of it, `remove` takes it out (the package does this on removal), and `status` shows it.
- Plain `useradd` from a root shell is not covered: it is the low-level tool, and the person using it chooses.
- A group that exists only when its package is installed (sambashare, scanner, bluetooth, lpadmin) is given when it exists; adduser warns about a missing group and goes on.

## Membership, not pam_group

pam_group (`/etc/security/group.conf`) would give the groups only to logins on the seat.
polkit's `isInGroup`, CUPS's `SystemGroup` and Samba's usershare directory read the account's membership in `/etc/group`, not a login process's groups, so lpadmin, netdev and sambashare would still fail on a seat login.
The cost is that an SSH login of the same account has the same groups (tested), as a Debian installer's first user does.

## Testing

`tests/run-tests.sh` in the package runs in a throwaway container with accountsservice, polkit, sshd and the calamares package.
- It creates a user each way and checks the exact group sets, leaves an existing user alone, and checks that `remove` restores `adduser.conf` byte for byte.
- The control plants docker in the list and in `adduser.conf` (`PLANT=docker`) and must fail.
- Not covered by it: a real display-manager login and Calamares' exec phase; the installer's user is reproduced with Calamares' own commands.
