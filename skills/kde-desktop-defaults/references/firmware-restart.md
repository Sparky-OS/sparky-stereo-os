# One-time restart to UEFI setup

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

1. Boot QEMU with OVMF code read only and a copy of the writable variable template for each case. Use the edition's Plasma packages and a real login on seat0. Check the firmware directory, capability, boot ID and initial bit. Select the Leave option, observe the firmware setup screen through the QEMU monitor, and keep the screen capture. Use a separate SeaBIOS boot for the unavailable choice.
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
