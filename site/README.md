# The front pages as a static site

**For** maintainers of the edition's front pages: one layout for each kind of page, with the words taken from each existing Markdown translation.
The Markdown remains the editorial source.
The generator uses only Python's standard library, and the resulting pages work with JavaScript disabled and use no outside resources or cookies.
An optional local WebGL drawing changes decoration only; the text and navigation are identical.

## Build and check

From the repository root:

```sh
python3 site/import_strings.py
python3 site/import_strings.py --check
python3 site/build.py
python3 site/check.py
python3 site/controls.py
python3 site/verify_text.py --control
```

The first command refreshes the catalogues and `missing.json`; review that diff whenever a source page changes.
The second refuses stale catalogues.
The build refuses a changed catalogue, an unknown link or an unlisted missing key.
The static check requires the offline `tidy` command; its raw output is retained with `--report-dir PATH`.
Tidy 5.8 warns about the standard `aria-current` and `decoding` attributes; those exact diagnostics are recognized, and other warnings fail.
The controls deliberately corrupt translations, links, anchors, resources and contrast, and must reject every corruption.
`check.py` compares each built page with the generator's own second rendering, so it cannot see a sentence the generator itself moves or drops.
`verify_text.py` is the check for that: it reads each Markdown source and its built page separately, with no code shared with the generator, and requires every word and punctuation mark in the source's order.
Two differences are named and allowed, the language row (the site's menu) and the home page's credit line at the foot of a detail or guide page; an element marked `data-added` is an addition the site makes on purpose and is counted, not compared.
With `--control` it also shows that a moved and a removed paragraph fail.

English is at the root; each other language has a folder named with its HTML language tag, such as `pt-BR/`.
Catalogue filenames use edition locale names such as `pt_BR.json`.
Only source pages that exist enter the language menu for that page kind.
German and Spanish have no detail page; six languages have no Windows quick start.
Their existing links to the English page remain explicit in their own source strings.

`strings/en.json` defines the source keys; each other JSON file contains only its language's own strings and the block structure that uses them.
Keys identify the page kind, English section name and paragraph or item; links, image sources and alternative texts are separate child keys.
The source file, its hash and each block's line are recorded alongside those keys.
English-only later additions to the detail page have their own semantic keys; absent translations are listed in `missing.json`, never silently filled.
Such an addition keeps its place: it records how many of its paragraph's own lines come before it, and the page draws it there, inside the one paragraph.
A source's different link placement is listed as an additional or missing key too.

The supported Markdown vocabulary is intentionally limited to these pages: headings, paragraphs, lists, quotes, the maintainer table, links, images, emphasis, code and a small set of inline HTML tags.
Unsupported syntax stops the import or build.
Do not treat this as a general Markdown converter.

## Address and output

The default output is `site/_build/`, which is ignored by Git.
The default canonical origin is the local preview address, not a selected public domain.
The base path is one argument:

```sh
python3 site/build.py --origin https://example.invalid --base-path /sparky-stereo-os/
python3 site/check.py
```

For a custom domain at its root use `--base-path /`.
The origin, canonical links, alternates, sitemap and local resource paths all follow these arguments.
The build marker identifies generated folders; the generator refuses to overwrite an unrelated folder.
A build keeps the output directory's inode so an already mounted static-server container can see a rebuild.

For local serving, export the authorized `DOCKER_HOST` first, then:

```sh
python3 site/preview.py
```

It builds for the loopback URL and runs a pinned Python image as a static server, with no host installation.
Open `http://localhost:8548/`; Ctrl+C stops its named container.
With `--open`, a person at the desktop gets the address opened in their own browser once it answers; an unattended run never passes it.
The source does not register a site, configure Pages or deploy anything.
GitHub branch publishing accepts a branch's root or `/docs`, not `site/_build` as an arbitrary folder.
Only the generated contents belong in a future publishing source.

## Browser checks

`browser_check.py` uses Python's standard library to speak the Chrome DevTools Protocol to an already running isolated headless browser.
Run it inside the same container network namespace as that browser, never against a person's desktop browser:

```sh
python3 site/browser_check.py --endpoint http://127.0.0.1:9222 --base-url http://127.0.0.1:8000 --output CAPTURES
```

It uses a fresh browser context for every capture: English, Portuguese, Japanese and Spanish, wide and phone widths, light and dark.
It checks real keyboard events on the language disclosure with scripts disabled, navigation, local resource requests, absent cookies, identical visible content with scripts enabled, and reflow at 320 CSS pixels.
All 22 content pages are also checked with enlarged text spacing, and each capture has a full-page companion.
`python3 site/depth_check.py --output CAPTURES` uses the same isolated browser to check the drawing with scripts off, reduced motion, missing WebGL and context loss, then that nothing is drawn or scheduled once it is hidden, off screen or at rest.

## The first screen

On a wide screen the home page's first screen is one group in two columns: what the edition is, its status and the next step on one side, the drawing with the four pictures and their caption on the other.
The blocks stay in the source's order in the document, so reading order and keyboard order are the README's; a narrow screen shows them one under another.
Running text keeps a measure: 66ch in the Latin-script languages and 38 characters in Japanese, Chinese and Korean, which also get their own line height, their own system fonts by name, upright emphasis and their own line breaking.
Each picture carries its real width and height, read from its file at build time, and only the first screen's picture loads at once.
Each page's description is its own first sentence, without its markup.

## The drawing

`depth.js` draws the desktop's three levels as one world: a window behind the screen, the window in use at the screen, its menu in front.
It is decoration (`aria-hidden`), carries no information the text lacks, and never covers the status or the next step.
It uses one perspective camera in two matrix uniforms, which the edition browser's 3D Canvas route recognises; the browser supplies the two parallel eye cameras and the desktop adapts the result to each screen.
The page makes no anaglyph and has no depth setting, eye swap or output format of its own.

The distances follow the browser's two rules for its screen plane, with D the camera's distance to the window in use: the near distance is D / 5, and the menu and the background window stand at D / 1.4 and D / 0.6, where the nearest and the farthest part balance at D.
The viewpoint moves sideways and comes to rest; nothing turns, so every plane keeps one distance in every frame.
`depth_check.py` applies those two rules to the page's own matrices and distances and requires the background window behind the screen, the window in use at it and the menu in front, inside the desktop's default limits, with the first version of the drawing as the control that must fail.
That is arithmetic on the page's numbers.
The proof that the edition's browser shows it that way is a capture of both eyes at the compositor, compared with the closed form; the recipe and the numbers are in the skill's [front pages as a site](../skills/writing-front-pages/references/front-pages-as-a-site.md#a-depth-drawing-proved-in-stereo) reference.

The drawing's place exists only while a drawing can run.
The stylesheet shows it under `(scripting: enabled) and (prefers-reduced-motion: no-preference)`, and `depth.js` marks it `depth-off` where WebGL is missing or its context is lost.
In every still form the page is the front page as written: its own picture, once, first in its column.
The motion ends after 4.8 seconds and stops while the page is hidden or the drawing is off screen.
The static checker reports the home page's weight without and with the script.

## A trial, on one commit

A row of counted figures under the first screen and a wordless strip over "How it works" are a trial that waits for a cold reading.
Each figure is counted at build time from the repository's own record (`counted_figures()` in `build.py` names the record and the unit) and stands beside a label that language's page already has, so no word is new.
Both are marked `data-added`; reverting their one commit removes them whole.

These scripts record measurements and captures; they belong outside the source repository.
These checks cover named accessibility criteria and are not a certificate of complete WCAG conformance or a substitute for assistive-technology review.

## Assets and credits

The wordmark is the edition's existing rendered artwork, unchanged: SPARKYOS / POWERED BY DEBIAN / STEREO 3D EDITION.
The colours use Oxygen's warm neutrals and blue links; the dark palette follows Sparky Stereo Oxygen Dark.
Brand and artwork provenance is in [ATTRIBUTIONS](../ATTRIBUTIONS.md).
No font file is included; typography uses system fonts.

The original screenshots and Windows guide pictures are copied byte for byte from this repository when building.
Their original alternative texts and the sentence about red-cyan glasses remain with them.
The two existing contributor avatars, DOI badge and SourceForge badge are stored locally, with origin and SHA-256 in `assets.json`.
Five unavailable Shields.io badge pictures are rendered as their existing alternative text within their original links; they do not make live requests or claim a live count.
The source's dark SourceForge variant is recorded alongside its light variant; the page uses the light badge on both themes, as an image with its own background.

Forms followed: Daniel's own site, for its native `<details class="lang">` disclosure and shared layout, and Dionatan Simioni's [KamLynk project pages](https://dionatansimioni.github.io/KamLynk/), for their static project-repository structure.
No third-party code is copied.
