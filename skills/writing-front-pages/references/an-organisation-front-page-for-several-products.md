# An organisation's front page for several products

**For** anyone who turns a GitHub organisation's profile page (`profile/README.md` in its `.github` repository) into one page for several products, some of them another maker's: one card per product in light and dark, the page in several languages, the proofs a reviewer can rerun.

Written on 2026-11-16 from ORDER 618, the Sparky-OS organisation page with three systems (SparkyOS onUSB, Sparky Stereo OS, Sparky Business) in ten languages, by Claude Opus 5.5.
The rules of [the skill](../SKILL.md#the-rules) come first; [adding a front-page language](adding-a-front-page-language.md) covers translations and [a repository as a small website](a-repository-as-a-small-website.md) a site outside GitHub's renderer.

## Working recipe

1. **Read every product's own home first, and the page as it is.**
   Fetch each product's pages (home, about, download, release notes) with `curl` into a new folder, keep their SHA-256, and write the claims table before the page: one row per sentence with the page and the words it rests on.
   A product that is another maker's gets only sentences its own site makes; a status ("available now") rests on its download page, not on a news item.
   Read the live organisation page's HTML too (`curl https://github.com/ORG`): its `id="user-content-…"` list is the set of anchors other pages may link to, and its `<source srcset>` shows how GitHub rewrote relative image paths.
   Search your own repositories for links into the page (`github.com/ORG#…`, `ORG/.github/blob/main/profile/…#…`) and keep each anchor.
2. **One structure, then the words.**
   Banner, language row, a two-line lead (what a person can do with the products, who makes them), one section per product (heading, card, three short lines, links), then the sections the page already had.
   What leaves the front goes to `profile/in-detail.md` whole, under its own `<a id>`.
3. **Cards as SVG files, one per product, language and theme,** shown through `<picture>` with `prefers-color-scheme` inside a link to the product's next step.
   Each card: a band with the product's mark on the ground that mark was made for, a status pill, one line of what a person does with it, a next-step button.
   Generate them from one strings table, never by hand: sixty cards for three products, ten languages and two themes.
4. **Text in the cards as glyph outlines.**
   An SVG shown through `<img>` loads no font and no outside file, and readers' fonts differ, so draw each word from an open font's outlines (fontTools' `SVGPathPen`), define each glyph once per file and place it with `<use href="#g12" x="…">` inside a group scaled from font units.
   Pick the font per language with a per-character fallback (Noto Sans CJK JP, KR, SC and TC for ja, ko, zh-CN and zh-TW; Noto Sans for Latin letters the CJK faces lack), wrap lines by measured width, and put the card's words in the `<img alt>` and the SVG's `<title>` word for word.
   Embed a raster mark as a `data:` URI; nothing else can load.
5. **Measure before you trust a layout.**
   Compute every pill and button width in every language and stop the build when one is wider than the card; check every text and button colour pair against WCAG 2.2 contrast 4.5:1 in both themes, by script.
   A 1200-unit card is drawn at about 0.7 on a 1280-pixel screen and about 0.27 on a 390-pixel phone: a 54-unit line is about 14 px there, a 40-unit pill about 11 px.
6. **The language files from the same generator.**
   `profile/README.md` is English and is what GitHub shows; each other language is `profile/README.LANG.md` with the same lines, the same pictures and one language row byte for byte the same in every file.
   Page links are absolute (`https://github.com/ORG/.github/blob/main/profile/README.LANG.md`; English goes to `https://github.com/ORG`), images relative (`./assets/…`), which GitHub serves from `/ORG/.github/raw/main/profile/` on the organisation's page and resolves next to the file in the repository view.
   Every translated heading gets the English anchor before it (`<a id="people"></a>`); a sentence the products' own pages already have in that language is copied from there, not translated again.
7. **Prove it the way GitHub renders it.**
   - Render each file: `gh api -X POST markdown --input req.json`, where `req.json` is `{"text": …, "mode": "gfm", "context": "ORG/.github"}`. Check by script that every `<picture>` holds its two `<source>` and one `<img>`, that no `<source>` is left outside, and that each card is inside its `<a>`.
   - Check links: map URLs into the organisation's repository to the branch, URLs into another repository to a fresh clone of it, fragments to GitHub's heading slugs and explicit ids, every other URL by HTTP status; compare each translation's headings, pictures and ids with the English file; run a broken copy that must fail.
   - Capture each file in a container with no network: the API's HTML inside `<article class="markdown-body">` with github-markdown-css (pinned version, its hash kept), remote pictures fetched once to files, Chromium at 1280 and 390 wide, light and dark; name each capture's theme from its pixels.
   - Move, never drop: look up every line of the old page in the new pair of files by script, and give every line that is not there word for word its new place in the claims table.
   - A cold reader on the English first screen, one change per round, every answer kept word for word.
8. **Another maker's mark is used as theirs.**
   Their file, unmodified and embedded byte for byte, on the colour their own site puts under it, only for their product, the card linked to their home page; a row in the assets list with its hash and "no licence stated" when none is; a courtesy list for whoever answers for the organisation (Daniel, for Sparky-OS) to tell the maker what is shown and how, with anything noticed on their site written as facts for them to decide.
   A product without a mark gets its name and a plain drawing marked as an illustration, never an invented logo.

## Traps

- **Symptom:** the card renders as an empty picture and the `<source>` lines appear as text under it.
  **Cause:** `<a href="…"><picture>` on one line is not an HTML block for CommonMark (an HTML block of type 7 needs the opening tag alone on its line), so it is inline HTML in a paragraph and the `<source>` lines fall outside the `<picture>`.
  **Fix:** `<a href="…">` alone on its line, the `<picture>` block, then `</a>` on its own line.
  **How it was found:** a test snippet through GitHub's markdown API returned `<themed-picture><picture></picture></themed-picture>` with the sources after it.
- **Symptom:** an anchor check finds no heading ids in the rendered HTML.
  **Cause:** the markdown API returns headings without ids (the page adds them) and turns explicit ids into `user-content-…`.
  **Fix:** check anchors against GitHub's slug rule on the Markdown, plus explicit `<a id>`.
- **Symptom:** a Polish name in a card stops the build ("no glyph for 'ł'").
  **Cause:** Noto Sans CJK has no ł, ę, ą, ś, ć, ż or ź, and the name appears in every language.
  **Fix:** a per-character fallback to Noto Sans. **How it was found:** a cmap check of each face for the ten languages' letters before the first card.
- **Symptom:** a translated button runs past the card's edge (Brazilian Portuguese 1316 units on a 1088-unit card).
  **Cause:** the English label fitted; four of the Latin-script translations did not.
  **Fix:** measure every label in every language first, shorten the label everywhere, and keep a guard that stops the build on overflow.
- **Symptom:** a Japanese line starts with a small kana ("ョン").
  **Cause:** breaking anywhere between CJK characters.
  **Fix:** small kana and the long-vowel mark in the no-line-start set, with the closing punctuation.
- **Symptom:** a cold reader takes the status "Live" on a system that runs from a USB drive for a Linux live session.
  **Fix:** "Available now". **How it was found:** the reader listed "Live" among the confusing words in round two.
- **Symptom:** sixty cards weigh several megabytes.
  **Cause:** a 2800-pixel wordmark resampled to twice its drawn size is still 107 KB, embedded in twenty cards.
  **Fix:** a 256-colour PNG (17.6 KB); measure its difference from the full-colour picture on the band colour (here at most 20 of 255, mean 0.3) and record it in the assets list.
- **Symptom:** a committed container image keeps `sh` as its entrypoint although `docker commit -c 'ENTRYPOINT []'` was given.
  **Cause:** the container was started with `--entrypoint sh`, and the commit kept it.
  **Fix:** commit with an explicit entrypoint (`-c 'ENTRYPOINT ["python3"]'`) or pass `--entrypoint` on every run.
- **Symptom:** a hook refuses `gh api -X POST markdown` as a write to another project.
  **Cause:** the render endpoint is a `POST`, though it changes nothing.
  **Fix:** do what the hook asks (read the skills it names) and say in the report that the call only renders.

## Perks

One strings table keeps ten languages and sixty cards in step: a reader's correction becomes one edit and one regeneration.
The products' own translated sentences make most of each translation a copy, not a new text.
The courtesy list turns "may we show your logo" into a short note the other maker can answer in a line.
