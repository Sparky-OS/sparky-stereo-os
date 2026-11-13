# The front pages as a static site

**For** maintainers of the edition's front pages: one layout for each kind of page, with the words taken from each existing Markdown translation.
The Markdown remains the editorial source.
The generator uses only Python's standard library, and the resulting pages use no JavaScript, outside resources or cookies.

## Build and check

From the repository root:

```sh
python3 site/import_strings.py
python3 site/import_strings.py --check
python3 site/build.py
python3 site/check.py
python3 site/controls.py
```

The first command refreshes the catalogues and `missing.json`; review that diff whenever a source page changes.
The second refuses stale catalogues.
The build refuses a changed catalogue, an unknown link or an unlisted missing key.
The static check requires the offline `tidy` command; its raw output is retained with `--report-dir PATH`.
Tidy 5.8 warns about the standard `aria-current` and `decoding` attributes; those exact diagnostics are recognized, and other warnings fail.
The controls deliberately corrupt translations, links, anchors, resources and contrast, and must reject every corruption.

English is at the root; each other language has a folder named with its HTML language tag, such as `pt-BR/`.
Catalogue filenames use edition locale names such as `pt_BR.json`.
Only source pages that exist enter the language menu for that page kind.
German and Spanish have no detail page; six languages have no Windows quick start.
Their existing links to the English page remain explicit in their own source strings.

`strings/en.json` defines the source keys; each other JSON file contains only its language's own strings and the block structure that uses them.
Keys identify the page kind, English section name and paragraph or item; links, image sources and alternative texts are separate child keys.
The source file, its hash and each block's line are recorded alongside those keys.
English-only later additions to the detail page have their own semantic keys; absent translations are listed in `missing.json`, never silently filled.
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
It records measurements and captures; they belong outside the source repository.
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
