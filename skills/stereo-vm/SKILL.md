---
name: stereo-vm
description: >-
  Testing a virtual machine's stereo display on Sparky Stereo OS: the viewers (QEMU's own window, virt-viewer, virt-manager, Karton), the pointer in a 3D mode, resizing, a mode change while the pointer moves, the controls that must fail, and the traps that fooled us. Load the general sparky-stereo skill first, then stereo-proof-rig for the capture rig and vkms-stereo for the virtual 3D display.
---

# A virtual machine in stereo

**Check freshness first.** Written on 2026-10-10. The guide [A virtual machine with a 3D display](../../docs/stereo-vm.md) says how the VM works; this skill says how to prove a change to it.

## The design every viewer follows

- The viewer's ordinary window is the guest's display at its own size (one view) and takes the input.
- Both views go side by side to a surface of their own on top of it, declared once as full side by side.
- The pointer: the viewer sends its position in the guest's display. With a stereo layout set, the server tells the tablet the display is one view, so the host's tablet mapping stays as upstream has it. Nothing remaps the pointer in QEMU.

## The checks

1. **Colour test:** both views in the right eye, the same frame number in both, one declaration, the window's 2D part identical in both eyes.
2. **Pointer:** the host moves the pointer to four fractions of the view in 2D and in every 3D mode; the guest's own kernel prints what its tablet gets (read the evdev node before any compositor maps it); each report must be the fraction of the range, within 4 %.
3. **Resize:** the same after the window is made smaller and larger.
4. **A mode change while the pointer moves:** the pointer circles around the view's centre while the guest changes mode; every report must stay at the centre of the range. A report at the instant of the switch can be off (the viewer's layout, the server's tablet size and the surface arrive on their own, as for a plain 2D resolution change): count those, allow at most two per transition in the first half second, and none later.
5. **Controls that must fail:** a stock client (Debian's spice-gtk, stock Karton), a QEMU that sends no layout. Say which modes the control fails in: a stock widget over this server points right in the modes whose left view sits at the frame's origin at full size.

## Traps that fooled us

- **`fake-click move`, one process per move, gives a GTK client only pointer enters:** the device comes and goes, and QEMU's GTK display and virt-manager hear no motion. Keep one `fake-click follow` session and write positions to it.
- **A libvirt domain's monitor socket path is limited to 107 bytes:** a long run name fails the start with "UNIX socket path too long"; keep run names short.
- **A repository with the edition's spice-gtk wins over Debian's:** a "stock client" image must pin Debian's version (`=0.42-4+b1`), for the library, the introspection package and virt-manager's.
- **virt-viewer opens at the size of the whole frame** (twice the view in a 3D mode): give the host's virtual output room, and a test that holds the pointer still will find it outside the window after a mode change.
- **WAYLAND_DEBUG prints `wl_pointer#12.enter`, not `@12`:** filters written for the old format match nothing.
- **A resize test must put the window back:** the next steps are measured at its size.
- **`pgrep -f` or `pkill -f` on a pattern in your own command line** matches itself.
