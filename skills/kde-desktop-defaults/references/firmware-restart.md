# One-time restarts: UEFI setup, and the anti-cheat start

Check the package's exact base first.
In Plasma Workspace 6.7.4, Breeze's `lookandfeel/org.kde.breeze/contents/logout/Logout.qml` owns the Leave controls, the `logout-greeter` exposes their bindings, and `applets/kicker/systemmodel.cpp` supplies Kickoff's power actions.
The session runner is in `runners/sessions`.
Later upstream moved the Leave QML to Plasma Desktop's `desktoppackage/contents/logout`.
The separate Desktop Session checkbox belongs to Plasma Desktop's `kcms/ksmserver`.
[Upstream move](https://invent.kde.org/plasma/plasma-workspace/-/commit/3729037a418e016f4d5974e006b03e161035a318).

## Capability and dispatch

- Query `org.freedesktop.login1.Manager.CanRebootToFirmwareSetup` on the system bus as the active desktop user. Check for a UEFI boot, the exact reply `yes` and the user's ability to restart. Keep ordinary Restart and its offline update handling on the existing code path.
- Reuse the existing Leave greeter and session shutdown service. A launcher opens an explicit firmware confirmation with the countdown stopped. Entering the choice calls `SetRebootToFirmwareSetup(true)` before the session closes. Use the caller's existing authorization and display a translated reason on a refusal.
- Read the previous flag before changing it. The shutdown service rolls back a flag it set if logout is cancelled. Preserve a flag that was already set by Desktop Session.
- Build the code and separate translation patches on the highest staged successor. Check the nine compiled gettext catalogues in the installed package. Check the English source and render two additional languages in a real session.

[login1 manager methods and properties](https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html).

## Proof

1. Boot QEMU through a bootable UEFI disk or ISO with OVMF code read only and a copy of the writable variable template. Use the edition's Plasma packages and a real login on seat0. Record the capability, boot ID and initial bit. Select Leave's firmware action, capture the set bit before shutdown and observe OVMF's firmware boot manager through QMP. This OVMF build selects **EFI Firmware Setup** in its boot manager. Press Enter there to capture the setup page. Use a separate SeaBIOS boot for the unavailable choice.
2. For real polkit denial, record the visible choice and `yes` first. Add a temporary rule returning `NO` for `org.freedesktop.login1.set-reboot-to-firmware-setup` in that guest. Verify the rule is live, select the choice, and check the denial message, the unchanged boot ID, the running session and the unset bit. Remove the rule before reusing that guest.
3. For a hardware bench where the current boot must stay running, confine the candidate applications to a private session bus and keep the real system bus for login1. Put a controlled KSMServer responder on the private bus that reads the bit after the setter and declines `closeSession`. The candidate daemon's rollback then clears the bit through logind. Check the boot ID and the original flag afterwards. Use the desktop user's session environment so the capability and authorization apply to the same user as in a normal login.
4. Read the EFI variable as a little-endian bit mask. Efivarfs prepends four attribute bytes. `EFI_OS_INDICATIONS_BOOT_TO_FW_UI` is bit zero of the following eight bytes. Check it alongside the D-Bus property; confirm that the other bits remain stable.

## Traps

| Symptom | Cause | Fix | How to find it |
|---|---|---|---|
| The firmware option is hidden even on a UEFI bench | The probe ran in an inactive SSH session and got `challenge` | Run the capability probe through the active desktop user's systemd user manager | Compare `busctl` from SSH and the probe unit, and read the seat's active session |
| Installing a denial rule makes the action disappear | The setter and the capability share a polkit action | Let the real greeter receive `yes` and open the menu before changing the rule | Compare the capability replies before and after the policy change |
| The notice is present on the red package | The old greeter already reads the scheduled reboot property | Assert the distinct action and setter behavior, and keep the existing notice as a control | Search the expanded source and both ASCII and UTF-16LE strings in the shipped binary |
| An older custom theme shows a plain restart countdown from a launcher | Its QML lacks the explicit firmware confirmation controls | Use the firmware-aware Breeze confirmation for launcher requests | Start the firmware prompt with a theme from before the patch and check its buttons and timer |
| QEMU restarts and loads Linux again after the firmware action | The proof fixture supplies the kernel through QEMU's direct-boot path | Boot through EFI GRUB on a bootable ISO or disk | Compare serial logs after the two boots, and record the EFI variable and the firmware's BootManagerMenuApp invocation |
| The isolated X11 greeter closes before it paints | The fullscreen greeter's three-second focus timer expires in a slow TCG session | Use the packaged greeter's `--windowed` proof mode to exercise the Leave controls | Compare the greeter's focus log with the QMP captures and a windowed run |

[EDK II firmware UI dispatch](https://github.com/tianocore/edk2/blob/master/MdeModulePkg/Universal/BdsDxe/BdsEntry.c), [OVMF setup application registration](https://github.com/tianocore/edk2/blob/master/OvmfPkg/Library/PlatformBootManagerLib/BdsPlatform.c).

## The second choice: Restart for anti-cheat games (row 190)

Restart Options is a list (`restartActions` in `Logout.qml`), and the anti-cheat start is its second entry, from plasma-workspace 4:6.7.4-2+stereo3d14 (fork branch order190).
The button shows when either choice is available (`hasRestartActions`), so a computer without logind's firmware capability still gets the menu for the anti-cheat start.

- **Offered when:** `/sys/firmware/efi` is a folder, `/var/lib/sparky-stereo-boot/anticheat.entry` exists (sparky-stereo-boot writes it at update-grub only when GRUB's menu has the entry and GRUB can keep a one-time request) and `/usr/lib/sparky-stereo-boot/anticheat-restart` is executable (`LogindSessionBackend::canRebootForAntiCheat()`).
- **Every path asks first:** the Leave menu item sets `antiCheatChosen`; Kickoff (`reboot-for-anti-cheat`) and KRunner (`anti-cheat`, `anticheat`, the translated name) call `promptRebootForAntiCheat` on `org.kde.LogoutPrompt`, which opens the same confirmation (`antiCheatOnly`). It says what the start does and lists what `sparky-stereo-boot anticheat-check --json` reports as not met or unknown, read when the confirmation opens (`readAntiCheatCheck`, never at every Leave). Rows the checker marks `settledByAntiCheatStart` (lockdown off, kexec closed only after the start: the anti-cheat start's own kernel line changes them) are left out. When the rows would push the buttons past the screen's bottom, the column moves up and the avatar steps aside (`column.tooTall`).
- **Scheduling:** `org.kde.Shutdown.logoutAndRebootForAntiCheat` runs `pkexec /usr/lib/sparky-stereo-boot/anticheat-restart set` before the session closes (polkit allows it for the active session, as logind allows a restart; pkexec's 126 and 127 become `org.freedesktop.PolicyKit1.Error.NotAuthorized`, the helper's 3 `org.freedesktop.DBus.Error.NotSupported`); the greeter waits up to 300 s for an authentication dialog. A cancelled logout runs `unset`, which removes only a request of ours.
- **Strings:** the menu item in `libkicker`, `plasma_runner_sessions` and `plasma_lookandfeel_org.kde.lookandfeel`, the confirmation and the three error texts in the last; `A session shutdown is already in progress.` already exists there and is reused (a second `msgid` of it would break `msgfmt`). The checker's rows come translated from sparky-stereo-boot's own language files.
- **New symbols** of `libkworkspace6-6`: `SessionManagement::canRebootForAntiCheat`, `requestRebootForAntiCheat`, `canRebootForAntiCheatChanged`, `SessionBackend::canRebootForAntiCheat` (read with `nm -D` on a build of the changed targets before the package build).

| Symptom | Cause | Fix | How it was found |
| --- | --- | --- | --- |
| The anti-cheat restart from the Leave menu starts at once | the firmware entry triggers directly, and the second entry copied it | the item opens the confirmation; only its button schedules the restart | reading the first draft against the design (nothing hidden from the person) |
| Restart Options missing where only the anti-cheat start is available | the button's visibility read the firmware capability alone | `hasRestartActions` | the QML visibility bindings |
| At 1280x800 the confirmation's Restart and Cancel are below the screen | the column starts below the middle of the screen (upstream's layout) and four wrapped rows filled the rest | leave out the rows the start settles, widen the rows' column, move the column up when it still does not fit | the confirmation captured in the virtual machine; tested by putting the edited `Logout.qml` over the installed one before the package build |
| `Logout.qml:67: TypeError: Cannot read property 'canRebootToFirmwareSetup' of null` in the journal at every prompt | the greeter sets the `leaveSession` context property after the QML is first evaluated | `leaveSession ? leaveSession.x : false` | the session's journal during the proof |
| An edited `Logout.qml` copied into the guest changes nothing | the copy failed: the 9p share was not mounted after the restart, and the output was cut to its last line | mount the share in every step and check the file (`grep` a new word) before prompting | the file's date was still the package's |
| A long patch fails the hundred-minute package build at its end | compile errors found late | compile only the changed targets first (`ninja kworkspace ksmserver-logout-greeter plasma-shutdown krunner_sessions kickerplugin`) on the staged source with its build dependencies, in a container | the first compile check (two minutes after the build dependencies) |

