---
name: stereo-integrations
description: >-
  How to add the stereo integration of one more program to Sparky Stereo OS so that it is installed whenever the program is selected, switches itself on when the program is present, offers the program when it is missing, can be hidden or switched off without losing its options, leaves 2D exactly as it was, and hands Stereo KWin full side by side declared once. Load the general sparky-stereo skill first.
---

# One more program, integrated

**Check freshness first.**
Written on 2026-10-14 from a preliminary study and finished on 2026-10-24 from the first two real packs, `sparky-stereo-align` and `sparky-stereo-mkv-mark`, proved in a fresh Debian testing container with the edition's repository.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; [`edition-packaging`](../edition-packaging/SKILL.md) holds the tasks and the repository rules this builds on, and [`stereo-pictures`](../stereo-pictures/SKILL.md) and [`stereo-video`](../stereo-video/SKILL.md) hold the file marks the packs write.

## The principle

A program that is on the system gets its stereo integration with nothing for the person to switch on.
The edition leaves the integrator's job to itself, not to the person (Daniel, 2026-10-24): one default program per file type, set once in `sparky-stereo-look`'s `/etc/xdg/kde-mimeapps.list`, and every other program that can handle the file integrated through Open With and Dolphin's right click menu, with the integration arriving together with the program.
Every integration obeys these rules, and each has a mechanism behind it:

| Rule | Mechanism |
|---|---|
| Installed whenever the program is selected | its package is a row of `sparky-os/lists/integrations.tsv`; `make-meta.py` puts it in `sparky-stereo-integrations` (data packs) or in the Recommends of the role tasks (native packs); the APTus Stereo AppCenter installs the program and its packs in one call |
| On when the program is present, inert when it is not | the pack is data: files in the folder the program or the desktop scans at run time; nothing runs at install time |
| The program is missing | the action runs command-not-found and offers the package it names, with its own message, never a list of ours (Daniel, 2026-10-14, answer 6); hiding such actions is a secondary choice after Cancel |
| Can be turned off and keeps its options | the switch lives inside the program it serves, or is the `HideMissing` option; removing the package is the last resort and leaves the program as Debian ships it |
| A file is touched only when the person chose it | a data pack never writes to a file on its own; the action the person clicked is the choice, and a file that already has the value is left alone |
| 2D stays exactly as it was | the integration adds stereo paths and never changes a 2D default; the proof includes the 2D control |
| Full side by side, declared once | a program's 3D area is its own surface declared through `libstereo-declare1`; every input packing is converted to full side by side before it |

## The one list

`sparky-os/lists/integrations.tsv`, tab separated: the Debian package of the program, the pack, its kind, a note.

- `data`: inert files, no Depends on the program, `Enhances: <program>`. It joins `sparky-stereo-integrations`, which `sparky-stereo-desktop` depends on, so every installation carries it and a program installed years later by plain apt finds its integration in place.
- `native`: links against the program (an OBS module, a digiKam plug-in). `Depends: <program>`, `Enhances: <program>`. Recommended by every role task whose `roles.tsv` rows list the program, installed with it by the AppCenter, removed with it.

`make-meta.py` reads the list (`read_integrations()`), drops a pack the repository does not carry yet and says so, and `--list-integrations` prints each pack, its kind, its program, what carries it and whether the repository has it.
`make-appcenter-entries.py` writes the AppCenter's install sets from the same list; `sparky-stereo-integrations` ships them as `/usr/share/sparky-stereo/integrations.map`, and the fork's `aptus-package-install` adds the names to its apt call.
Debian's apt installs from Depends, Pre-Depends and Recommends only; `Enhances` is read by people and tools, not acted on, and `Supplements` is not a Debian field.

## The pack format

A pack is a Debian package `sparky-stereo-<thing>` in Paweł's formula ([`edition-packaging`](../edition-packaging/references/sparky-formula.md)), built with `lean.standalone`, with its definition in one `pack.json` that `sparky-os/packages/sparky-stereo-integration/make-pack.py` turns into the installed files:

```json
{
 "id": "mkv-mark",
 "program": "mkvpropedit",
 "worker": "/usr/lib/sparky-stereo/mkv-mark/mark",
 "menus": [
  {"file": "sparky-stereo-mkv-mark", "icon": "video-x-generic",
   "mime": ["video/x-matroska", "video/webm", "video/x-matroska-3d"],
   "urls": {"min": 1},
   "submenu": {"en": "Mark as 3D", "pl": "...", "pt_BR": "...", "fr": "...", "de": "...", "ja": "...", "ko": "...", "zh_CN": "...", "zh_TW": "..."},
   "actions": [{"id": "Mark1", "args": ["1"], "name": {"en": "Side by side, left eye first", "...": "..."}}]}
 ]
}
```

- `program` is the executable the actions need (the `TryExec`); the offer when it is missing is about this name.
- `worker` is the installed executable that does the work; it receives the action's `args`, then `--`, then the files.
- Each entry of `menus` becomes one ordinary Dolphin service menu, `/usr/share/kio/servicemenus/<file>.desktop`, with `MimeType`, `Actions`, `X-KDE-Submenu` and the `urls` limits (`required`, `min`, `max`, KIO's `X-KDE-RequiredNumberOfUrls`, `X-KDE-MinNumberOfUrls`, `X-KDE-MaxNumberOfUrls`); every action's `Exec` is `sparky-stereo-integration run <id> <args> -- %F`.
- The generator also writes `/usr/share/sparky-stereo/integrations.d/<id>.conf` (`program=`, `worker=`, `menus=`), which the runner reads.
- Every text exists in the nine required languages, en, pl, pt_BR, fr, de, ja, ko, zh_CN and zh_TW, or the generator stops. The worker's own messages live in `/usr/share/sparky/<package>/<code>` as `LOCAL1` to `LOCALn`, chosen as the other Sparky tools choose (the whole `LANG`, then the bare language, then English; Chinese keeps its territory).
- A pack gets its MIME list from the files it can really handle, never `image/*` or `video/*`: stereo actions must not show on plain files. A pair action on two pictures is the exception that the number of files makes (`urls.required: [2]`).
- Keep one table of words per pack (`gen.py` in the two first packs writes `pack.json` and the language files from it), so the menu and the worker say the same thing.

A program's own menu actions stay: a pack adds only what is missing.

## The runner and the missing program

`sparky-stereo-integration run <id> [args] -- files` is the only thing a service menu calls.
It checks for the pack's `program`; present, it runs the worker; missing, it runs command-not-found itself (`/usr/lib/command-not-found -- <program>`, a Depends of the runner) and shows its message as it is, which names the package that provides the program (Daniel, 2026-10-24: link it to command-not-found, and only then offer the window).
The dialog has two buttons, "Install <package>" and "Cancel".
Install is the edition's normal route with the person's consent: the AppCenter's own call, `pkexec apt-get install -- <package> <the packs listed for it in integrations.map>`, in a terminal where apt asks its question; never silent.
Only after Cancel, or when command-not-found names no package (its own words are shown in a message box first), a second, secondary dialog asks whether to hide the actions of programs that are not installed. It is never the first thing shown.
Without a desktop the message goes to the terminal and the exit status is 127, as for any missing command.
The pack itself never lists packages: the index is command-not-found's, and the edition's packages are in it because the published repository carries `Contents-<arch>` files (`repo/make-contents.py`, run by `publish-tree.sh`), which apt-file and command-not-found read.

The same message and the same install route are met in every place a missing program can be met:

| Place | How |
|---|---|
| bash, in Konsole and on a console | Debian's `/etc/bash.bashrc` defines `command_not_found_handle`; Konsole starts the user's shell as an ordinary shell, so it fires |
| fish | its own handler calls command-not-found on Debian |
| zsh | Debian's zshrc does not source `/etc/zsh_command_not_found`; `sparky-stereo-console` diverts `/etc/zsh/zshrc` to `zshrc.debian` and ships one that sources Debian's, then command-not-found's handler |
| KRunner | `sparky-stereo-integration` ships a D-Bus runner (`/usr/share/krunner/dbusplugins/sparky-stereo-missing-program.desktop`, activated as `org.sparky.stereo.MissingProgram`): a typed program that is not in `PATH` and that command-not-found places in exactly one package matches with command-not-found's first lines, and running the match calls `sparky-stereo-integration install <package>` |
| Dolphin's right click packs | the dialog above |

The database is filled where each system gets its packages: on an installed system by command-not-found's own hook after `apt update` (apt-file switches the Contents targets on), in the ISO's root file system at build time, and when `sparky-stereo-integration` is configured, from the package lists apt already has.

**The engine fact.** KIO 6.30 reads no `TryExec` in service menus (there is no `TryExec` in `kio/src`), and `kfileitemactions.cpp` decides what to show in `shouldDisplayServiceMenu()` and `checkTypesMatch()`. The edition's kf6-kio gains `TryExec` support as an engine patch. The default (offer the install) does not need it. The option that hides the entries must work on both:

- `HideMissing` is in `~/.config/sparky-stereo-integrationrc` (`[General]`, `HideMissing=true|false`), with the system default in `/etc/xdg/sparky-stereo-integrationrc` (`false`); the person's file wins.
- On, `sparky-stereo-integration hide-missing sync` writes a copy of each pack's menu into `~/.local/share/kio/servicemenus/` (KIO reads the user's folder first and keeps the first file of a name) carrying `TryExec=<program>`, for a KIO that reads it, and, while the program is missing, an empty `MimeType=`, so the published KIO shows nothing either. The copy has the marker `X-Sparky-Stereo-Override=true`; off removes only copies with the marker, and a file of the person's own with the same name is never touched.
- The sync runs when the option is switched, at every login (an autostart entry), and at each action; a program installed later reappears at the next sync, at once on a KIO that reads `TryExec`.

## Step 1: find the program's integration points

Read the program's own package before its source: `dpkg -L <program>` shows the folders it scans.
Look for plug-in, script and extension folders; presets and profiles; KDE's shared places (`/usr/share/kio/servicemenus/`, the `kf6/thumbcreator`, `kf6/kio` and `kf6/kfilemetadata` plug-in folders, `/usr/share/kwin/effects/` and `scripts/`, `/usr/share/mime/packages/`, `/etc/xdg/<app>rc`, `/usr/share/kconf_update/`); sound (`/usr/share/pipewire/pipewire.conf.d/`, `/usr/share/wireplumber/wireplumber.conf.d/`); and the program's own way of being told something is stereo (an encoder option, a stream property, a caps field, a file attribute).
Then read the code that scans the folder, so you know whether a file from another package is honoured: OBS auto-loads native modules and never auto-loads scripts, so anything that must be on by itself in OBS is a native module.
Audit the real commands before writing an action; do not invent flags. For Hugin, `align_image_stack` sorts images by exposure unless `--use-given-order` is given, which would swap a stereo pair silently.

## Step 2: choose the kind of package

- **Data pack** (above): scripts, presets, fragments, service menus, `/etc/xdg` defaults.
- **Native pack**: anything compiled against the program.
- **Inside our rebuild**: when the edition rebuilds the program anyway (`+stereo3dN`), the integration is a patch in that build and needs no discovery.
- **Settings only**: `/etc/xdg/<app>rc` for a default the person has not set; a `kconf_update` script only to move an existing key.

A dpkg file trigger (`interest-noawait <the program's folder>`) is for state that must follow the program's presence; it never installs anything, and the data packs of the first two rows need none, since the runner looks for the program each time.

## Step 3: package it

`sparky-stereo-<thing>`, `Maintainer: Daniel Ramos (Capitain Jack)`, `Homepage: https://sparkylinux.org`, `copyright` with every upstream credit kept, `lang/` in the nine languages, version `0.MINOR.PATCH+lc1`.
Add the row to `lists/integrations.tsv`; `make-meta.py` does the rest.
Build with the Lean Code toolkit (`lean.standalone`, then `check-debs` and `check-link`), stage with a `SHA256SUMS`; the main session signs and publishes.

## Step 4: prove it

In a fresh `debian:testing` container with the edition's repository, its pins and deb-multimedia, plus the staged packages as a second source with the repository's `Origin`:

1. every task and `sparky-stereo` resolve, nothing removed, `dpkg --audit` clean, and the plan of each carries the packs;
2. the program first, then the pack: the entries work; the pack first, then the program: they work the moment the program arrives, with nothing else done;
3. the program missing: the action exits 127 with command-not-found's message, and the dialog's answers do what they say (a fake `kdialog` and a fake terminal record the calls): Install runs the AppCenter's call, Cancel then Keep them changes nothing, Cancel then Hide them sets the option, and the hide offer is never the first dialog;
4. the program purged: the pack stays, `dpkg --audit` is clean, `apt-get -s autoremove` removes none of ours; purge the pack with and without the program and no file of it is left;
5. `Enhances` shows in `apt-cache show` and `rdepends`, and `apt-get install <program>` alone installs nothing else;
6. the menus listed and clicked by the real KIO, not by a script that imitates it: a small program built on `KFileItemActions` (`setItemListProperties`, `addActionsTo`, then `QAction::trigger()`), run offscreen as an ordinary user, in more than one language;
7. the outputs read back by an independent reader: KFileMetaData's `stereo3dLayout` through its extractor plug-ins for pictures and Matroska, `mkvinfo` and `mkvmerge -J` for `StereoMode`, `exiftool` for MPO, a measurement of vertical disparity (phase correlation of textured blocks) before and after an alignment, with an injected misalignment as the known truth;
8. the negative controls: the other eye order gives the other mark and the other left view; a file that already has the value is byte for byte unchanged; a sibling file in the same folder is never touched; two pictures that share no points write nothing and say so;
9. the option: `HideMissing` on and off against the real KIO, a program present and missing, a person's own file of the same name untouched;
10. the other places a missing program is met: a pty session of bash, zsh and fish, Konsole offscreen with a probe in place of the shell, and the real KRunner library (`KRunner::RunnerManager`) against the runner, each red first where the edition changed it.

Then the stereo proof of the general skill for anything that changes what a person sees.

## What the first packs fixed in the details

- **JPS.** A `_JPSJPS_` block in an APP3 segment: the descriptor is `type | layout << 8 | flags << 16`, type 1 stereo, layout 2 side by side, flag bit 18 left eye first (`0x40201`); without the block a `.jps` is right eye first, the convention KFileMetaData reads as well.
- **MPO.** An MP Index IFD with the number of images, the MP Entry records and an attribute IFD whose MP Individual Number (tag `0xB101`) is 1 for the left view and 2 for the right; the first image carries the index, the second its own MPF with its number; offsets are relative to the TIFF header of the first image's MPF.
- **PNS.** The `sTER` chunk, mode 1 (left eye on the left), before the first `IDAT`, with the padding of the PNG extensions specification, section 3.6: `padding = 7 - ((w - 1) mod 8)`, the right view starting on a column divisible by eight; a reader strips it with `padding = 15 - ((W - 1) mod 16)`.
- **Matroska.** `StereoMode` is a property of the video track, values 0 to 14 of RFC 9559 (5.1.4.1.28.3), written with `mkvpropedit --edit track:v1 --set stereo-mode=N` and removed with `--delete stereo-mode`; the names come from `mkvmerge --list-stereo-modes`.
- **Eye order of two loose pictures** is the order of the selection, the first picture being the left eye; the swapped actions are the per-file input correction ("Swap left and right eyes" in the player's words), never an output setting.

## Step 5: upstream, never cold

Check the project's stance on AI before anything (OBS discourages it, Krita has a moratorium, Blender has a published policy, KDE had none adopted in October 2026); find who owns the code in its own records; draft the heads-up as [`upstream-outreach`](../upstream-outreach/SKILL.md) says; the main session and Daniel send it.
A pack that only calls a program's command line, as these two do, needs no message to its authors.
