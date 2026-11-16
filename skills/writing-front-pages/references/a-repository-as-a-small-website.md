# A project's repository as a small website

**For** a maintainer who turns a public repository (README, provenance, releases, a citation file) into a few static pages, with a brand folder's logo and colours, and must prove the pages before anyone switches publishing on.

Written on 2026-11-16 from ORDER 613 (a four-page site for a patched compiler's repository), by Claude Sonnet 5.5.
The general rules are in [writing front pages](../SKILL.md); the multilingual case is [the front pages as a site](front-pages-as-a-site.md).

## Working recipe

1. **Claims table first.**
   Clone the repository into scratch, read the README, the provenance and contribution files, the citation file, the release notes (`gh release view TAG --json body,assets`) and the build guide, then write one row per sentence the site will say: page, sentence, file and line (or release page).
   Write the table before the pages; a sentence with no row does not go on the site.
   Leave out, by name in the table, what the repository's own text says about other people or projects: the site gives results, never labels.
2. **Brand folder.**
   Read its README, specifications, palette JSON and manifest.
   Copy only the files the site uses, under neutral names.
   Write down which usage rules the folder states and which it does not; where it states none (clear space, backgrounds), use the logo only as approved, on its own light ground, also in dark mode.
   A second brand whose text must not appear gives colour values and non-textual graphics only: strip `<title>`, `aria-label` and any `<text>` from copied SVGs, rename the files neutrally, and mark the graphic `aria-hidden` with an empty `alt`.
3. **Plain files.**
   `index.html` plus at most three pages, one `style.css` with colours as custom properties, light and dark by `prefers-color-scheme`, no script, no outside font or script, system font stack, fixed 16 px gutter, tables that stack on a phone (`td::before { content: attr(data-label) }`).
   Write the shared header and footer once in a scratch generator if you like, but publish only the generated files and edit those afterwards.
4. **First screen.**
   About 100 words: what a person can do, the single most telling measured fact, an honest status line, two buttons.
   Show before telling: a figure drawn from the recorded numbers on one stated scale, with the numbers also in text.
5. **Proofs, each kept as a file in the evidence folder.**
   - Link check: every `href`, `src` and `srcset`, local files and `#fragments` offline, external URLs by HTTP status, and anchors into the repository's README against GitHub's heading slugs (lowercase, backticks and punctuation dropped, spaces to hyphens), because GitHub answers 200 for any anchor.
   - Contrast: read the colour pairs from `style.css` and compute WCAG 2.2 ratios, 4.5:1 for text (SC 1.4.3) and 3:1 for graphics that carry information (SC 1.4.11), in both themes.
   - Captures: serve `site/` with `python3 -m http.server` inside a container and capture each page at 1920x1080 and 390x844, light and dark, plus one tall capture per page and size to read the whole page; look at them.
   - Run what the page tells the reader to run, as written, in a container: the download, the checksum, the install lines, the first command.
   - Cold reader: the first screen as Markdown to one model through ACIG, answers recorded word for word, then one change and one more round.
6. **PUBLISH.md** for the person who will switch it on: the exact steps, the address forms the links must survive, and what is checked after.

## Traps

- Symptom: the capture named "light" is dark.
  Cause: in Chromium 156 `--blink-settings=preferredColorScheme=0` is dark and `1` is light.
  Fix: name the capture from its pixels.
  Found by: reading one background pixel of each PNG.
- Symptom: the container image has no browser, and `apt-get update` fails on `file:/repo`.
  Cause: the rig image carries its own local repository and a vendor repository whose key is missing; its Qt WebEngine has libraries but no headers.
  Fix: in a throwaway container remove the two extra source files and the pin, run the https-only helper, install `chromium` from Debian, commit the image under the lane's name and list it in `.artifacts`.
  Found by: `docker run ... which chromium` and the apt errors.
- Symptom: the install command in the release notes fails on a clean machine with "error while loading shared libraries: libclang-cpp.so.21.1".
  Cause: the released compiler is dynamically linked to the system's LLVM and Clang, and the notes only said so for the other build.
  Fix: run the released binary in a bare container before writing install steps, add the prerequisite and the package that provides it, and run `zig version` again.
  Found by: running the downloaded binary read-only in a container.
- Symptom: `curl -O` saves the archive as `...%2B...`.
  Cause: `-O` keeps the URL's last segment as written; the folder needs `%2B`, the file name a literal `+`.
  Fix: write the file name with a literal `+` in the command and run the page's own block, extracted from the HTML.
- Symptom: a logo set to `width: min(320px, 100%)` inside an inline-block tile stays at its full size.
  Cause: a percentage inside a shrink-to-fit box has nothing to resolve against.
  Fix: `width: 320px; max-width: 100%`.
- Symptom: the contrast check fails on a brand colour used for a bar.
  Cause: the brand's teal is 2.78:1 on the light track, below 3:1.
  Fix: use the brand's deep indigo for informational graphics in the light theme and keep the teal for decoration.
- Symptom: a shell `rm -f *` in a scratch folder is refused by the safety check.
  Fix: make a new empty folder for each download instead of clearing one.
- Symptom: `ask_cloud` with a named model answers "bootstrap pending".
  Fix: record the refusal and ask once with the default model.

## Perks

The release notes are often the best source for install steps and sizes; the README's tables are the best source for measured facts, each with its commit; a status table of "not yet measured" rows is a feature of the page, not a hole in it.

## The visuals

When the page's words have already been reviewed, freeze the exact source revision before changing the look.
A picture states a fact that the page already has; it does not introduce a new performance claim.
Keep the difference between a measured value and a bound: “under” and “more than” are not exact bar endpoints.
Use the existing sentence for its alternative text and keep the source and caveat beside the picture.
A decorative mark does not replace a picture of the result.

Use the brand folder's approved files as they are, with their original proportions.
Check the copied files byte for byte against that folder; do not redraw, recolour or crop a mark.
If a folder says nothing about clear space or backgrounds, record the placement choice and its reason rather than inventing a brand rule.
Padding outside the artwork and a light tile in both themes can preserve the approved appearance.
Keep the brand's credits as its own records give them.

Assign colours by role in each theme: paper, surface, text, secondary text, link, focus, meaningful graphic and decoration.
A palette value that passes on a dark surface may fail on a light one.
Measure the actual adjacent pairs, including code, status labels and focus outlines, against WCAG 2.2 SC 1.4.3 and 1.4.11.
Use `prefers-color-scheme` for the reader's setting and respect `prefers-reduced-motion` if anything moves.
Keep typography and spacing in a small shared system; let prose have a readable measure while a table uses the available width.

The proofs travel with the change:
- Serve the base and changed files over HTTP inside an isolated container with core dumps disabled.
- Use a fresh headless browser profile for every page, size and theme; save both viewport and full-page captures at desktop and phone dimensions.
- Verify the viewport size and the computed theme, image loading, document overflow, and keyboard access to the skip link.
- Look at the captures, including the lower parts of long pages, before calling them proof.
- Compare text, numbers, URLs and anchors against the frozen base; when the change is CSS only, require every HTML file to remain byte-identical.
- Check local files, fragments, CSS image URLs and external links; record blocked or failed external requests as unverified.
- Search SVG source, filenames and decoded image metadata for forbidden words; compressed pixel bytes are not text.

Traps met during a visual-system pass:
- **Headless Chromium exits with `chrome_crashpad_handler: --database is required`.** A non-root container process had no writable configuration directory. Give each fresh profile its own `XDG_CONFIG_HOME` and `XDG_CACHE_HOME`; retain the failing log and rerun without a desktop connection.
- **A forbidden-word scan flags an approved PNG.** A case-insensitive search matched random compressed pixel bytes. Inspect the PNG chunk table and any `tEXt`, `zTXt` or `iTXt` payloads, scan text sources separately, and verify approved asset identity by hash. Do not edit a logo to remove a random binary match.
- **A phone page has a horizontal scrollbar although the text fits.** Long unbroken links or fixed-width artwork can exceed the available inline size. Inspect which element exceeds the document client width; allow long links to wrap and constrain the outer tile as well as its proportional image. Compare document scroll width with client width, not `innerWidth`, because the latter includes the scrollbar.
