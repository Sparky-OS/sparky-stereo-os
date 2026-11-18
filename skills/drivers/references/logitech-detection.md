# Offer OpenLogi when Logitech hardware is present

**For Hardware Setup maintainers:** identify the hardware from existing metadata and offer the vendor-signed app center entry; do not install an unmodified vendor application behind the person's back.
Read with [drivers](../SKILL.md) and [the signed-download entry](../../edition-packaging/references/vendor-signed-download-entry.md).

Checked on 2026-11-18 against OpenLogi v0.9.0, commit `a5b507ec8802e0ecb7ef3de61ce7868609c9b533`, and Linux commit `4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd`.
The edition's hardware candidate is 0.1.37, following source 0.1.36; compare actual source, stage and published archive versions rather than relying on a brief's remembered version.

## Working recipe

1. In `sparky-stereo-hardware`, keep the sourced numeric identities in `share/peripherals/openlogi.ids`; regenerate with `tools/make-logitech-ids.py` from separately fetched source files, never copied vendor code.
2. Read the existing `lsusb` and separated `hid-uevents` facts. Match known receivers, Litra lights and USB HID++ IDs; for HID_ID accept only Logitech vendor 046d and USB bus 3 or Bluetooth bus 5, using the known product list or an explicit `DRIVER=logitech-hidpp` binding.
3. For UVC, read USB interface `bInterfaceClass=0e` and its parent's `idVendor`/`idProduct` through `logitech.usb_video`. A Logitech vendor ID alone is insufficient. Do not open a camera, hidraw or input node to classify it.
4. Emit `offer\topenlogi\tIDENTIFIERS`, never `package\topenlogi`. If the program is already present, suppress the install offer.
5. Present the localized note and button in the existing Hardware Setup plan. The button opens the app center entry, releases the hardware lock and re-enters the hardware plan afterward; it does not install the application itself. If the app center is absent, say so visibly.
6. Prefer this offer to automatically selecting Solaar for these devices. Keep Solaar installable and preserve existing installations and autostart preferences. The entry advises quitting Solaar before starting OpenLogi, as upstream recommends.
7. Run `python3 tests/logitech.py` in the package test container: eight cases must pass, including unrelated hardware, separated HID devices and the already-installed control. Run the existing detection, peripherals and NVIDIA-branch suites too.
8. Use umockdev metadata for a receiver `046d:c52b`, Bluetooth device `046d:b023`, UVC interface `046d:082d`, Litra `046d:c900` and unrelated vendor control. Feed the actual installed dry-run classifier and assert the offer is present only for the four Logitech classes; assert no automatic OpenLogi/Solaar package selection.

The note/button presentation is an implemented proposal awaiting the edition maintainer's design review; the recorded requirement specifies an offer but does not prescribe its appearance.

## Detection table

Each row below is numeric metadata with its primary source, not a claim that every listed model was physically tested.
The wildcard UVC row requires USB video class 0e, and HID++ driver binding is an additional explicit positive fact.

| Identifier | Family/transport | Source at the inspected commit |
| --- | --- | --- |
| `046d:*` | uvc | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-camera/src/linux.rs) |
| `046d:0a87` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4915) |
| `046d:b008` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4930) |
| `046d:b00c` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4829) |
| `046d:b012` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4932) |
| `046d:b015` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4934) |
| `046d:b019` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4936) |
| `046d:b01d` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4938) |
| `046d:b01e` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4939) |
| `046d:b020` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4941) |
| `046d:b023` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4947) |
| `046d:b025` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4949) |
| `046d:b034` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4951) |
| `046d:b037` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4953) |
| `046d:b038` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4955) |
| `046d:b042` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4959) |
| `046d:b305` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4919) |
| `046d:b309` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4922) |
| `046d:b30b` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4925) |
| `046d:b35f` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4928) |
| `046d:b369` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4987) |
| `046d:b36e` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4989) |
| `046d:b36f` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4961) |
| `046d:b370` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4963) |
| `046d:b371` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4967) |
| `046d:b374` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4969) |
| `046d:b377` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4965) |
| `046d:b378` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4979) |
| `046d:b380` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4981) |
| `046d:b383` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4971) |
| `046d:b384` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4973) |
| `046d:b386` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4975) |
| `046d:b388` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4977) |
| `046d:b38c` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4983) |
| `046d:b38f` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4985) |
| `046d:b391` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4957) |
| `046d:b394` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4991) |
| `046d:b397` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4993) |
| `046d:b39c` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4995) |
| `046d:b39d` | bluetooth | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4997) |
| `046d:c081` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4890) |
| `046d:c082` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4878) |
| `046d:c086` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4892) |
| `046d:c087` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4886) |
| `046d:c088` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4894) |
| `046d:c08a` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4896) |
| `046d:c08d` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4880) |
| `046d:c090` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4888) |
| `046d:c091` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4898) |
| `046d:c094` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4908) |
| `046d:c095` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4882) |
| `046d:c098` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4884) |
| `046d:c09a` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4912) |
| `046d:c09b` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4910) |
| `046d:c262` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4902) |
| `046d:c26e` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4905) |
| `046d:c343` | usb | [source](https://github.com/torvalds/linux/blob/4405c18c95d2d0f99f6c581ef0ee8591a1aa6ccd/drivers/hid/hid-logitech-hidpp.c#L4900) |
| `046d:c52b` | receiver | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/receiver.rs#L58) |
| `046d:c532` | receiver | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/receiver.rs#L59) |
| `046d:c534` | receiver | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/receiver.rs#L63) |
| `046d:c537` | receiver | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/receiver.rs#L65) |
| `046d:c539` | receiver | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/receiver.rs#L71) |
| `046d:c53a` | receiver | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/receiver.rs#L77) |
| `046d:c53e` | receiver | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/receiver.rs#L68) |
| `046d:c53f` | receiver | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/receiver.rs#L83) |
| `046d:c541` | receiver | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/receiver.rs#L89) |
| `046d:c547` | receiver | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/receiver.rs#L95) |
| `046d:c548` | receiver | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/receiver.rs#L100) |
| `046d:c54d` | receiver | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/receiver.rs#L102) |
| `046d:c900` | litra | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/litra.rs#L8) |
| `046d:c901` | litra | [source](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/crates/openlogi-device-registry/src/litra.rs#L10) |

## Trap: a descriptor-only device disappears after probing

**Symptom:** OpenLogi sees the fake hidraw node, tries a channel probe, then retires it and reports no device.
**Cause:** a HID report descriptor describes reports but does not answer HID++ ping, feature discovery or configuration requests.
**Fix:** distinguish metadata/descriptor proof from protocol proof. For the latter, combine the kernel's `hidpp_descriptor` in `drivers/hid/hid-logitech-dj.c` with the upstream fixture exchanges under `fixtures/devices/mx-master-3-001/cases`, using UMockdev's private PTY and ioctl descriptor support.
**How found:** the descriptor-only control failed its HID++ handshake; a responder using the recorded exchanges enumerated the logical mouse in CLI and GUI. Missing discovery metadata was explicitly synthesized and logged, not described as recorded hardware behavior.

## Trap: a shared PTY invents a coexistence failure

**Symptom:** two clients steal each other's fake responses or time out, unlike normal hidraw opens.
**Cause:** two processes reading the same PTY share a consumptive queue; real hidraw provides a report queue per open.
**Fix:** give each simulated client its own private node and broadcast each model response to both queues, retaining request software IDs. Inspect what each actual client read and its exit status.
**How found:** checking the testbed's queue model against hidraw semantics led to separate UMockdev testbeds. OpenLogi `list` and Solaar `config "MX Master 3" dpi` then completed, with Solaar reporting DPI 1000.
This establishes concurrent read behavior only. OpenLogi's per-node software-ID leases do not coordinate another application's settings; neither recorded descriptors nor a response model prove safe simultaneous writes, live event delivery, reconnects or physical button behavior.

## Trap: a full Solaar query exceeds the recorded fixture

**Symptom:** `solaar show` raises FeatureCallError while inspecting a wheel capability.
**Cause:** the recording lacks that request; the harness returns an explicit unsupported-function response.
**Fix:** report the fixture gap; exercise a common recorded operation for coexistence and keep the failed exploratory log. Do not call it a Solaar/OpenLogi conflict or invent successful hardware values.
**How found:** the failing request mapped to HIRES_WHEEL capability discovery, while the recorded DPI query succeeded in both clients' scope.

A real-device bench remains necessary for active-seat ACLs, receiver pairing, concurrent configuration, event diversion, SmartShift, cameras and lights. It needs explicit authorization and a recoverable baseline; this metadata/protocol test touches no physical peripheral.
