# Surveying independent plugins before offering them a home

Written on 2026-11-20 from ORDER 52, a study of independent plugins for KDE programs that one person keeps alive.
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
