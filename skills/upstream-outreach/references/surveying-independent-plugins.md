# Surveying independent plugins before offering them a home

Written on 2026-11-20 from ORDER 52, a study of independent plugins for KDE programs that one person keeps alive, and extended the same day with section b, the pieces that attach to KDE Connect.
Nothing is built, downloaded or sent in a survey: it ends in a table, a list of what was set aside, and early-contact drafts that Daniel reads first.

## Recipe

1. **List what the edition already has,** before looking outside: the credits page (`ATTRIBUTIONS.md`), the list of merges (`docs/upstream-merges.md`) and the newest published round's pool.
   `apt-cache search -n NAME` on a machine that has the edition's repository tells whether a name is in Debian or the edition.
   A name a brief calls "already with us" that no source holds is written down as "not found", never assumed.
2. **Find candidates** by kind (widgets and wallpapers, KWin effects and scripts, service menus, KRunner, KIO, editor and creative-program plugins), from the KDE Store, KDE Discuss announcements and a web search; treat search summaries as leads, never as facts.
3. **Read each fact at the repository, and write the date and the address:**
   - last activity: `https://github.com/OWNER/REPO/commits.atom` (Codeberg: `/atom/branch/main`), the newest entry; it needs no login and no API quota;
   - licence: the head of `LICENSE`, `LICENSE.md` or `COPYING`, and the licence field of the metadata, since the two can differ;
   - Plasma 6 state: the package's `metadata.json` (`KPackageStructure`, `X-Plasma-API-Minimum-Version`) or the README's own requirements; a KWin effect has no such field and needs its build files;
   - translations: the repository tree (`https://api.github.com/repos/OWNER/REPO/git/trees/HEAD?recursive=1`, 60 unauthenticated calls an hour) counted against the edition's ten languages;
   - the AI rule: README, CONTRIBUTING, AGENTS.md, CLAUDE.md, the pull request template and every `.github` issue template, grepped for AI, LLM, Copilot, Claude, ChatGPT, generative and vibe; the author's own site is read separately.
4. **Rank** in one table by the request's criteria, one row per candidate, with a route (package only; package and offer changes back; use-only; not for us, with the reason). A fact not read stays "not read".
5. **Write early-contact drafts** only for projects whose rules allow it ([the message](../SKILL.md#the-message)): the offer first, one small ask, AI help said once, the venue named without any contact detail.
6. **Say what was set aside, one reason each.**

## Traps met

- **Symptom:** a count of "34 translations" for a repository whose only catalogue is English.
  **Cause:** the pattern for `.ts` files matched TypeScript sources, not Qt translation files.
  **Fix:** count `.po` files in a `po` or `translate` folder, and look at the Qt `.ts` hits by hand.
- **Symptom:** a repository's commit feed is empty or the page 404s.
  **Cause:** the project moved to an organisation (PlasmaZones) or the name in a search summary was a fork's.
  **Fix:** read the README's first lines and the package metadata for the author's own address before ranking it.
- **Symptom:** a repository named "...6" whose README opens "This is a Plasma 5 applet".
  **Cause:** a rename without a README edit.
  **Fix:** write the Plasma 6 state as not established; never rank it on the name.
- **Symptom:** the licence field says one licence and the LICENSE file is another.
  **Cause:** metadata and file written at different times.
  **Fix:** put both in the table and make the licence the one small question to the author.
- **Symptom:** a tree of hundreds of shaders, images or sounds under a single LICENSE file.
  **Cause:** the author collected them; each has its own origin.
  **Fix:** ask which may ship before any package is promised.
- **Symptom:** a first-person draft sentence such as "the first widget that does X".
  **Cause:** a search that found nothing earlier.
  **Fix:** drop it, or give the source beside it ([sparky-stereo, part three](../../sparky-stereo/SKILL.md)).
- **Symptom:** the repository's own AI file is an instruction file for an assistant, not a rule for contributors.
  **Cause:** the author uses an assistant (an `AGENTS.md` or `CLAUDE.md` for Claude Code).
  **Fix:** quote its first lines as what the author uses, never as a rule for or against us.
- **Symptom:** the project's licence file or a rule sits behind a login or a bot wall.
  **Fix:** write "not read"; never work around it ([sparky-stereo, part three](../../sparky-stereo/SKILL.md)).

## Perks

- A project that asks for translations in its README is the easiest first offer: the edition's ten languages are the offer, and the pull request is in the project's own format.
- A KDE project is not an independent author: the hold on contributions to KDE still applies to KIO S3, kio-gdrive and anything on KDE's own forge, so those rows say so and are set aside.

## KDE Connect: where a third-party piece attaches (ORDER 52b)

Read from the edition's clone of kdeconnect-kde (`plugins/README.txt`, `KDEConnectMacros.cmake`, `core/pluginloader.cpp`, `core/daemon.cpp`) and the published package's file list.
Sort every candidate into one of four doors before ranking it:

1. **In-tree desktop plug-in.** A `KdeConnectPlugin` subclass plus `kdeconnect_NAME.json` with its packet types, built by `kdeconnect_add_plugin` (`kcoreaddons_add_plugin ... INSTALL_NAMESPACE kdeconnect`), installed in `usr/lib/<triplet>/qt6/plugins/kdeconnect/`, found by `KPluginMetaData::findPlugins("kdeconnect")`.
   The published packages have no development package, so such a plug-in is a patch series against KDE Connect's tree, rebuilt into our own `kdeconnect`, never a separate package.
2. **The phone half.** A plug-in that sends or receives its own packet type needs a matching class in `kdeconnect-android`; carry it into the Android build the edition uses.
3. **D-Bus clients** (`org.kde.kdeconnect` on the session bus, `org.kde.kdeconnect.device.NAME` per plug-in) and `kdeconnect-cli`: widgets, KRunner pieces, pointer tools.
   They need no KDE Connect build; the package is a plasmoid or a script plus `Depends: kdeconnect`.
4. **A second implementation of the protocol** (GSConnect, Valent, kcd, handfast, COSMIC's): it replaces the daemon on the same port.
   Never co-install with `kdeconnectd`; at most an opt-in package for another kind of machine.

Phone-side programs that speak the protocol (Sailfish, macOS clients, a Switch, Google Glass) are use-only unless the edition ships that platform.

Where to find them: `https://github.com/topics/kdeconnect` and `/topics/kde-connect` (WebFetch shows 20 a page; `?page=2`, `?page=3`), then each repository's own files.
The KDE Store and web search summaries found almost none of these: a search for "KDE Connect widget" returned only a Plasma 5 applet and KDE's own plasmoid.

### Traps met in 52b

- **Symptom:** every row after the first twenty calls shows "API rate limit exceeded".
  **Cause:** the unauthenticated GitHub API allows 60 calls an hour, and `fetch` helpers spend one per repository.
  **Fix:** use the API once per repository for the licence and default branch, and everything else from `raw.githubusercontent.com` and `commits.atom`, which are not counted; wait for the reset (`/rate_limit`) before a tree listing.
- **Symptom:** a repository has no LICENSE file and the API licence is null.
  **Cause:** the licence is in SPDX headers, a `LICENSES` folder (REUSE) or `metadata.json`.
  **Fix:** read those, write the three sources in the table, and make a mismatch the "noticed, not asking you to act on" line of the draft.
- **Symptom:** a project's README says "for KDE Connect" and the code is another implementation.
  **Cause:** GSConnect, Valent, kcd and others speak the protocol.
  **Fix:** the four doors above; a daemon replacement is never "package only".
- **Symptom:** an installer that adds a button to KDE Connect's tray menu.
  **Cause:** it edits files of an installed plasmoid, which the package manager owns.
  **Fix:** not for us; ask for a D-Bus client or a patch instead.
- **Symptom:** `LC_ALL` unset gives `Candidato:` and a grep for `Candidate` finds nothing.
  **Cause:** `apt-cache policy` is translated.
  **Fix:** `LC_ALL=C apt-cache policy`.
- **Symptom:** an `issues.atom` feed with zero entries for every repository.
  **Cause:** GitHub has no public issue feed.
  **Fix:** read the Issues page (WebFetch) for the few rows that matter, and write "not read" for the rest.
- **Symptom:** an `AGENTS.md` at the root of a KDE Connect repository.
  **Cause:** the author works with assistants (one repository ships four skills under `.agents/`).
  **Fix:** quote it as what the author uses; it is not a rule for contributors.

## The adoption form of the contact text (Daniel, 2026-11-20)

The first contact does not ask permission.
It says, in this order: thanks for the work, with one true detail from their repository; who Daniel is ("my edition of SparkyLinux (by Paweł "pavroo" Pijanowski)", with KDE Plasma 6 on Debian testing, "in development and has no public release yet"); that the edition is adopting the work, as a Debian package built from the release tag with nothing changed, tested on Debian testing, with the author's name and repository on the credits page, and what the edition adds for the languages it lacks (as a pull request in the author's format, to take, change or leave); the invitation to take part as much or as little as they like, with Jeromy Streets as the example (his project lives in the edition's organisation with him as maintainer) and "credited either way"; one small ask ("tell me if you would like to take part, or if there is anything you want us to do differently"); a licence mismatch as "one thing I noticed and am not asking you to act on"; and, once, that AI partners help and Daniel reads and checks everything he sends.
One sentence per line; no dash in the middle of a sentence; the venue named in the file's header line (an issue on the repository, the store page), never a contact detail; a second language only where the author's own pages are in it (Fenestra's French).
Say what only the repository shows, never "the first" or "the only".
