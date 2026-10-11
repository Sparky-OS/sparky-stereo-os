# House formats: one format inside, conversions at the edges

Sparky Stereo OS treats every medium the same way.
Inside the system each medium has one format, the "house format".
Whatever comes in is converted to it once, where it enters; whatever goes out is converted from it once, where it leaves.
Nothing in the middle converts, guesses or reduces quality.
Broadcast and post-production work this way, and so does PipeWire for sound; this page applies it to every medium in the desktop.

**Status** says what is in the edition today and what is being built.

| Medium | House format (inside) | Converted where it enters | Converted where it leaves | Status |
|---|---|---|---|---|
| **Stereo pictures and video** | Full side by side, left eye first, both eyes complete, at the source's resolution; declared once to the compositor | In the program or its library: every packing in the standards (H.264, H.265 and H.274 frame packing; Matroska StereoMode; MPO; JPS; PNG `sTER`), and anaglyph pictures rebuilt into two eyes | In KWin's outputs only: HDMI 3D (frame packing, side by side, top and bottom), red and cyan on any screen, headsets through OpenXR; one conversion per screen, so mirrored screens and screens on different GPUs each get their own 3D output; glasses-free panels through DisplayXR (planned) | In the edition |
| **Depth of the desktop** | One value per element: sunk, screen or popped | Set by the window manager and the toolkit, from the element's role | Stereo screens: the two eyes' disparity. 2D screens: shadow and a small scale | KWin side done on our KWin branch, coming with the next KWin package; toolkit side being built |
| **Video colour** | The decoder's own bit depth, never reduced in the middle | In the decoder | At the screen: deep colour at 10, 12 or 16 bits per component when its EDID offers it | Being finished driver by driver |
| **Audio** | PCM at the source's own rate; the edition's floor is 24 bit at 48 kHz | In the decoder; the sound server follows the source's rate instead of resampling (44.1 to 192 kHz) | Per device: the best format the hardware takes; encoded formats passed through to the TV when its EDID says it accepts them; binaural on headphones for multichannel sound | Being built: rate following, device settings, passthrough and binaural |
| **Sound in XR** | The program's sound scene: its sources placed in its world, and that world anchored to the room | In the game or engine, which places the sources as it places its two cameras | Speakers: a mix that stays in room coordinates and never turns with the head. Headphones: binaural, following the head. HT mode and the Stereo Spectator keep the sound in the room | Planned: per-speaker setup, the headphone path, and the room-facing listener in our Half-Life 2 module |
| **Input devices** | Every button, axis and hat raw, as the device reports it | In the kernel driver and SDL, without dropping controls | In the game, Steam Input or the user's mapping | KDE's game controller page with every raw control done on our KDE fork; more than 80 buttons being built |

## The rules that follow from it

- **One declaration, not many options.** A program says what it hands over (for stereo: "full side by side") and nothing else. It never offers screen formats; the outputs own them.
- **Inputs are read in full.** Every format a standard defines is read, both eye orders included, so nothing upstream has to change before it works here.
- **Quality is never traded in the middle.** If something must give way on weak hardware, it happens at an edge, it is shown to the user, and the user can change it.
- **The hardware fills in the defaults.** EDID, ALSA and input descriptors say what a screen, a sound device or a controller can do, and the defaults start from that.

## Where each medium is explained

- Stereo pictures and video, and who does what between programs, toolkits, KWin and drivers: [stereo-labor-division.md](stereo-labor-division.md).
- Sound, and who does what between programs and the operating system: the [Sound](stereo-labor-division.md#sound-the-same-division) section of the same page.
- Developing for 3D and XR without the hardware on the desk: [develop-3d-on-an-ordinary-monitor.md](develop-3d-on-an-ordinary-monitor.md).
- Testing stereo without a 3D display: [test-stereo-without-a-3d-tv.md](test-stereo-without-a-3d-tv.md) and the stereo virtual machine: [stereo-vm.md](stereo-vm.md).
- Depth on the desktop: the "Depth on the desktop" section of the [README](../README.md).

## References

- **Stereo:** the specifications listed in [stereo-labor-division.md](stereo-labor-division.md#references) (HDMI 1.4b 3D structures; ITU-T H.264, H.265 and H.274 frame packing; RFC 9559 StereoMode; Vulkan, GLX, EGL and DXGI stereo).
- **Still stereo pictures:** CIPA DC-007 (Multi-Picture Format, MPO); PNG Extensions 1.4.0, the `sTER` chunk.
- **Video colour:** HDMI 1.3 and later, deep colour (30, 36 and 48 bits per pixel), signalled in the HDMI Vendor-Specific Data Block of the EDID.
- **Audio:** AES5 (preferred sampling frequencies for digital audio; 48 kHz for professional use); IEC 60958 and IEC 61937 (PCM and encoded audio over S/PDIF and HDMI); CTA-861, audio data blocks (the formats a display's EDID says it accepts); AES69 (SOFA files for head-related transfer functions).
- **Headsets:** [OpenXR 1.1](https://registry.khronos.org/OpenXR/specs/1.1/html/xrspec.html) (Khronos), the output to headsets beside the 3D televisions; [OpenVR](https://github.com/ValveSoftware/openvr) (Valve), for SteamVR.
- **Glasses-free panels:** DisplayXR's [window geometry specification](https://github.com/DisplayXR/displayxr-runtime/blob/main/docs/specs/runtime/wayland-window-geometry.md) and [ADR-033](https://github.com/DisplayXR/displayxr-runtime/blob/main/docs/adr/ADR-033-placement-reports-geometry-weaver-owns-phase.md): the compositor reports where a window is, and only the display vendor's weaver computes the lens phase.
- **Sound in XR:** AES69-2015 (SOFA) for the head-related transfer functions of binaural headphone sound, which PipeWire's [filter chain](https://docs.pipewire.org/page_module_filter_chain.html) takes; who places the sound and who routes it: the [Sound section](stereo-labor-division.md#sound-the-same-division) of the labor division.
- **Input devices:** the Linux input event codes (`include/uapi/linux/input-event-codes.h`); the USB HID Usage Tables.
