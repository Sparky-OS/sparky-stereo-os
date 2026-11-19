# An HDMI sound device that "could not be read"

**Check freshness first.**
Written on 2026-11-19 by Claude Sonnet 5.5 (ORDER 757), against sparky-stereo-audio 0.1.0 to 0.3.1, the kernel's sound/hda/common/proc.c and sound/hda/codecs/hdmi/hdmi.c at v7.3, and PipeWire 1.6.9-2.

## Symptom

The problems list says "The sound devices NVidia, Generic could not be read, so the standard rates are kept for them and PipeWire decides what each device takes" (sparky-stereo-audio 0.1.0 to 0.3.0), with the displays connected and lit.
On a laptop with no display connected the same sentence names "HDMI".

## Cause

`parse_codec` took an HDA output only when its `[Audio Output]` node carried a `Device: name="...", type="..."` line.
The kernel prints that line from `print_nid_pcms()` (sound/hda/common/proc.c):

```c
list_for_each_entry(cpcm, &codec->pcm_list_head, list) {
	for (type = 0; type < 2; type++) {
		if (cpcm->stream[type].nid != nid || cpcm->pcm == NULL)
			continue;
		snd_iprintf(buffer, "  Device: name=\"%s\", "
			    "type=\"%s\", device=%i\n", ...
```

For an HDMI or DisplayPort codec `stream[type].nid` is set when a stream is opened (`hdmi_pcm_open()`: `hinfo->nid = per_cvt->cvt_nid`) and cleared when it closes (`hdmi_pcm_close()`: `hinfo->nid = 0`).
So the line exists only while a PCM holds the converter.
At boot, when the service runs, and whenever the sink is idle, a graphics card's codec file has no Device line at all, and the old reader found no output on it and called the card unreadable.
The `PCM:` rate lines are a second trap: a converter prints them only when it has a format override (`AC_WCAP_FORMAT_OVRD`), so an AMD codec lists its rates once, under `Default PCM:`, and none under its nodes.

## How it was found

The installed script was read for the condition that makes a card readable; the `/proc/asound/card*/codec#0` files of a machine with two graphics cards, copied with both displays lit and nothing playing, had 4 and 6 `Audio Output` nodes and no `Device:` line (`grep -c 'Device:'` gives 0), while valid `eld#` files named the televisions.
The recipe's older fixtures had passed because they were copied while PipeWire held the sinks open: a read made while a stream plays has the Device line and looks fine.
**Always take a fixture twice, playing and idle.**

## Fix (sparky-stereo-audio 0.3.1)

- A card with `eld#` files, or whose codec has a Pin Complex whose `Pincap` lists `HDMI` or `DP`, is a graphics card's audio whatever its Device lines.
- Its outputs are the displays connected now: one per valid ELD (`monitor_present 1`, `eld_valid 1`), with the ELD's LPCM rates inside the converters' rates (the `PCM:` lines, else `Default PCM:`), and the ELD's alone where the converters list none.
- No display connected: the card is read, has no output, and raises no problem. A card whose codec file is missing or empty is still said.
- What a display told is kept in `/var/lib/sparky-stereo-audio/displays.json` by the ELD's `manufacture_id`, `product_id` and `monitor_name` and used while it is away, marked "remembered" in `sparky-stereo-audio show`. The name alone is not an identity: two televisions of one model name were two different ELDs.

## Which events cover a display being connected

- `SUBSYSTEM=="sound", KERNEL=="card[0-9]*", ACTION=="add|remove|change"` (already there): a sound card appears or goes (a GPU, a USB DAC), and boot.
- The sound card raises no event when a display is plugged: `hdmi.c` reports the jack with `snd_jack_report()`, an input event, and sends no `kobject_uevent` (`grep -n 'uevent' sound/hda/codecs/hdmi/hdmi.c` finds nothing).
- The graphics driver does: a DRM `change` event with `HOTPLUG=1`. Rule added: `SUBSYSTEM=="drm", KERNEL=="card[0-9]*", ACTION=="change", ENV{HOTPLUG}=="1"` starts the same service.
- The ELD follows the hotplug event by a moment, so the service runs `detect --write --settle`: it reads the graphics cards again every half second until two readings agree (at most four seconds).

## Rig

`/proc/asound` is masked in a container; point `SPARKY_STEREO_AUDIO_PROC` at a fixture tree.
Make the trees from one real copy of `card*/{id,codec#*,eld#*}`: idle (as copied), nothing connected (each `eld#` replaced by `monitor_present 0`, `eld_valid 0`), no `eld#` files, a PCM open (a `Device:` line inserted after the converter's `Node` line), a card with only an `id` file, a card with an empty `codec#0`, an analog codec alone.
Red is the old reader on the idle and nothing-connected trees (card unreadable) and green on the PCM-open tree (the trap); green is the new reader on all of them, the analog and USB trees unchanged.
Install the package by apt in a container and run the unit's own `ExecStart` for each stage: displays, displays away, displays back, a fresh machine without a display, an empty codec file.

## Traps (symptom, cause, fix, how found)

- **A fixture that passes the old reader.** Cause: copied while a stream played. Fix: copy idle. Found by comparing the `Device:` count of two copies of one card.
- **`monitor_present 0` files exist for every pin.** An idle Nvidia codec has sixteen `eld#0.N` files and one is valid; read `monitor_present` and `eld_valid`, never the file's existence.
- **Two televisions named alike.** Both were "SONY TV" with different `product_id`: key remembered values by the ELD's three fields.
- **A new reader that writes a state file in a read-only command.** `detect` without `--write` and `show` write nothing; only `detect --write` keeps displays.
- **Credits.** The code that prints these files is by Takashi Iwai (the codec proc interface), Wu Fengguang and Anssi Hannula (the ELD and HDMI codec code), from their copyright and author lines in the kernel source.
