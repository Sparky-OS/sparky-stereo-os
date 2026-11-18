# An app center entry that is only a link to the vendor's store page (ORDER 10)

Written 2026-11-18 on sparky-aptus-stereo-appcenter 0.1.15+lc1, whose first row of this kind is CODESYS 4.

## When it is the right kind

The vendor allows exactly a link: the program stays theirs, registered and downloaded from their own store under their own licence, and nothing of theirs is fetched, installed, mirrored, packaged or hosted by the edition (the repository hosts only what the edition changes: [trying a vendor's closed program](trying-a-vendors-closed-program.md)).
If the vendor's licence lets the edition fetch the file on the person's machine, the kind is a download or a package entry ([adding a program to an app center](../../upstream-outreach/references/adding-a-program-to-an-app-center.md)), not this one.
A link needs nothing installed, so the app center's `Depends` do not change by one package (Daniel, 2026-11-14: "only when someone install vinci - same for anything that needs this sort of dependancy").

## The row and the card

`kind: store` in `stereo/catalogue.json` (a stereo section) or `stereo/main-entries.json` (a main page's entry, with `section: main`, `page`, `key`).
Fields: `vendor` (the maker, as its own pages name it), `store` (the store's name), `domain` (the vendor's own domain), `url` (https, on that domain or a subdomain), `note` (the key of one plain sentence on what the program is).
The page is the row's `section`: to move the entry change that one word among the five stereo sections; to put it on one of Paweł's pages move the row to `main-entries.json` and add the `aptus://KEY_ID` link to his page in both trees, as PJeOffice Pro's.
Daniel places the entry at the acceptance, by what the program is for the person; the lane proposes the page with its reasons.

The card says, before the button, in all ten languages (`stereo/lang/*.json`, keys `store_*` and the row's `note`):

1. what the program is, in one plain sentence taken from the vendor's own public pages;
2. who makes it, and that its names and trademarks are theirs and are used only to name the program;
3. that the button opens the store in the person's web browser, that the person registers there if it asks and downloads under the vendor's own licence agreement, and that the app center installs and downloads nothing;
4. the address, as text (never a link: a link in the page would be opened by another program, as another user, and says nothing before it is followed).

The button is `aptus://stereo_entry_ID_open` (or `aptus://storeopen_ID` on a main page); `catalogue.store_request(uri)` finds the row and `handler` runs `storelink.open_page`, with no pkexec and no route in `catalogue.route`.

## The click

`xdg-open ADDRESS`, as the person.
The app center starts through `pkexec`, so the handler is usually root: `storelink.command` drops to the user in `PKEXEC_UID` with `setpriv --reuid --regid --init-groups` and gives the child the person's `HOME`, `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS` and the session variables pkexec keeps (`DISPLAY`, `XAUTHORITY`, `LANG...`, plus `WAYLAND_DISPLAY` found as a socket in `/run/user/UID`).
It never opens a browser as root: with no usable `PKEXEC_UID` it opens nothing and says so.
Every failure is said in a window with the address to open by hand and "Nothing was installed": a refused address, no `xdg-open`, no known person, `xdg-open` exiting non-zero (its last line is the reason).
`xdg-open` is not a Depends of the app center; its absence is the message.

## The address test

`tests/store.py` checks the data (every `kind: store` row: scheme `https`, host equal to `domain` or under it, no credentials, port absent or 443) and `storelink.secure` checks the same at the click, with a table of look-alikes that must fail: `http://`, `evilcodesys.com`, `codesys.com.example.org`, the vendor's address inside a query string, credentials, a port, a space or newline, `javascript:`, `file:`, `aptus://`.
Mutation check: change the row's `url` to `http://`, its `domain` to another, drop `setpriv`, drop a sentence; each must turn the file red.

## Proof

Red before, green after: the new test file against the previous source (it stops at `import storelink`), then against the new one; the fork's whole set (`pjeoffice.py`, `entries.py`, `tools.py`, `displaycal.py`, `zram.py`, `store.py`) in a container with python3-apt.
The card as a person sees it: install the staged deb into a throwaway container (`dpkg-deb -x`), mount sparky-stereo-apt's reader and word catalogues where the package expects them, empty `/var/lib/apt/lists`, run `appcenter --render` in `en_US` and `pt_BR`, and print the card's text.
The click: a stub `xdg-open` that logs `id`, run through the real `handler` as root with `PKEXEC_UID=1000`, as uid 1000 directly, and as root without `PKEXEC_UID` (the log must stay empty); then a stub that exits 3, the real `xdg-open` with no browser installed (exit 3, "no method available"), and none at all.

## Traps, symptom first

- **Symptom:** the brief says the app center has no entry for the vendor, and the build adds a second card. **Cause:** a card was already there, hard-coded in the page script (`appcenter`) since 0.1.2, its address opened by Paweł's handler with `x-www-browser` as the administrator, and its one sentence ("Registration and the EULA are managed by CODESYS in its store.") in the language files. **Fix:** replace it by the row, in the same place of the same section; keep the old language key. **How found:** `grep -ril VENDOR` over the fork before writing anything.
- **Symptom:** `ModuleNotFoundError: No module named 'common'` when running the installed `handler` or `appcenter`. **Cause:** `python3 -I` drops the script's folder from `sys.path`; the scripts import their siblings. **Fix:** run them as their shebang does.
- **Symptom:** `appcenter --render` in the rig runs for minutes. **Cause:** `actions/entry status` reads the install-time download declaration of every package in apt's lists. **Fix:** empty `/var/lib/apt/lists` in the rig. **How found:** the command hit the tool's 120 s limit; the app center's README says the pass takes minutes.
- **Symptom:** the stub `xdg-open` logs nothing when run as the person, and the click still looks successful. **Cause:** the log file was created by root, mode 644; the stub's `echo >>` failed silently and it exited 0. **Fix:** `chmod 666` the log. The stub's behaviour must also not depend on an environment variable the dropped command never receives (the child's environment is a whitelist): read the stub's exit code from a file.
- **Symptom:** a real `xdg-open` with `XDG_CURRENT_DESKTOP=KDE` and `KDE_FULL_SESSION=true` set, in a system without KDE's tools, prints `kfmclient: not found` and exits 0: a success that opened nothing. **Cause:** its KDE branch trusts the variables. **Fix:** do not invent desktop variables that pkexec dropped; without them `xdg-open` takes its generic path (the person's default browser from the mime settings) and exits 3 with `no method available` when there is none, which is the message the person needs.
- **Symptom:** a test that the card has no external reference fails on the page's other, older raw link. **Cause:** the VR section's SteamVR card is the same kind of hard-coded `https://` link (to Valve's store) without sentences. **Fix:** assert on the card of the entry, not on the whole page; the SteamVR card is a candidate for the same kind (a suggestion, not done here).
- **Symptom:** `dpkg-genbuildinfo --build=binary` says "binary build with no binary artifacts found". **Cause:** an empty `debian/files` in the unpacked standalone source. **Fix:** rebuild once from the `.dsc` with `dpkg-buildpackage -us -uc -b -d` in a container that has the recipe's build dependency (`sparky-stereo-problems`); the two `.deb` files are byte for byte the same and the `.buildinfo` and `.changes` come with it.
- **Symptom:** `tests/entries.py` fails two cases after the new kind. **Cause:** the route test expects an install route for every row and the shape test lists the kinds. **Fix:** a store row has no changing route (assert `None`), and `store` joins the kinds; both say why in a comment.
- **Symptom:** the vendor's main site answers 429 and a "Vercel Security Checkpoint". **Cause:** a bot wall on `www.codesys.com`. **Fix:** say so, do not work around it; the store's own pages (`store.codesys.com/en/codesys-4.html`, `/en/imprint` for the trademark paragraph) were readable, and the product page and the imprint carried every fact the card needed.
