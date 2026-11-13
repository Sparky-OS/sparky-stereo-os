# The front pages as a site

**For** a maintainer moving existing multilingual front pages into a static website: keep the words, links and anchors, use one layout, and prove the preview before changing the public front door.

## Working recipe

1. Inventory the source pages by kind and language, including documents that will remain links to GitHub.
   Keep the Markdown as the editorial source, with its exact existing credit and flags.
   A missing page does not become an English page disguised as a translation.
2. Import one keyed catalogue per language, with English defining the shared keys.
   Keep paragraph text, destinations, picture sources and alternative texts as separate values.
   Record the source path, hash and line alongside each block.
   List missing and additional keys explicitly, including links placed differently by a translation.
3. Render a shared shell and one template per page kind with Python's standard library.
   The edition implementation is in [site](../../../site/README.md).
   From the repository root, `python3 site/import_strings.py --check` verifies source provenance; `python3 site/build.py` writes the ignored preview folder.
   No wording is translated or shortened by the generator.
4. Use Daniel's native `<details class="lang">` menu in the header: the current flag with 🌐🗣️ as its summary, native language names in links, and both `lang` and `hreflang` on each language link.
   Only languages that have that page and pass the checks appear there.
   Add matching alternate links, `x-default`, a canonical, a sitemap and an accessible 404 page.
5. Preserve every original heading fragment and explicit anchor as an `id` where its content now lives.
   Supplement translated fragments with English aliases; do not replace the translated ones.
   `python3 site/check.py --report-dir PATH` writes the full anchor and source-block maps outside the source tree.
6. Copy the approved pictures unchanged and serve every runtime asset locally.
   Ordinary outbound links remain links; a remote image, font or script is a runtime dependency.
   Keep image provenance and hashes, and inspect SVGs for active or external references.
7. Build both address forms: `--base-path /` and `--base-path /repository/`, with the chosen origin supplied separately.
   Check every local link and fragment, including images, language alternates and 404 navigation.
   The build directory is an artifact, not an automatically published website.
8. Run `python3 site/check.py` with offline HTML Tidy, then `python3 site/controls.py`.
   The latter must reject missing translations, English substitutions, broken links, lost anchors, remote resources and insufficient contrast.
   A check that only accepts good output has not established that it detects the fault.
9. Serve in an isolated static-server container and use a fresh browser context per case.
   [The browser checker](../../../site/browser_check.py) checks keyboard navigation with scripts off, local requests, cookies, language availability, wide and phone views, system light/dark, 320 CSS-pixel reflow and enlarged text spacing.
   Keep viewport and full-page PNGs outside the repository and inspect them.
   Record the browser, checker versions, page weight, measured criteria and untested assistive technologies.
10. Give a cold reader the first screen and the proposed additions without project context.
    Ask what it is, who it serves, the next step and what confused them.
    A refused service call is a recorded failure, not an endorsement; an addition gated on that verdict stays out until reviewed.
11. Hand back a clean branch, reproducible commands, captures, source maps and the exact future switch steps.
    Leave the READMEs intact until the switch is approved.
    As checked in [GitHub's publishing-source documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) on 2026-11-13, branch publishing selects a branch's root or `/docs`, not any arbitrary nested folder.
    A generated output can later become the root of a dedicated publishing branch; saving that Pages setting is a deployment action.

## Optional 3D decoration

Only add it when the design asks for it.
The scene is decoration, `aria-hidden`, separate from the status and next step, and cannot carry information absent from the text.
The original picture remains when scripts are disabled, reduced motion is requested, WebGL is unavailable or its context is lost.
No page-side red-cyan conversion is needed.

Use one world with real depth and a perspective camera supplied in matrix uniforms.
The edition browser's 3D Canvas route recognizes that camera and provides parallel per-eye views; do not draw a flattened picture twice or introduce page-level display settings.
Read [one world, two cameras](../../stereo-two-cameras/SKILL.md) and its [browser evidence](../../stereo-two-cameras/references/x3d-in-the-browser.md) first.
The example uses a depth buffer, opaque geometry and no screen-space effects or third-party library.
Camera-matrix arithmetic proves its geometry; it does not prove the browser-to-compositor transport or a physical display.
State that distinction in the evidence.

Stop animation while hidden or outside the viewport, and leave no pending animation callback after motion ends.
The example stops after 4.8 seconds rather than animating indefinitely beside reading material.
This fits the automatic-motion timing boundary of [WCAG 2.2 SC 2.2.2](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html); a longer animation needs an accessible pause, stop or hide mechanism with localized labels.
`python3 site/depth_check.py --output PATH` runs against the isolated CDP browser and checks the picture paths, context loss, idle callbacks, identical text, matrix geometry, swapped/flat-eye controls and local-only requests.
Report the page weight with and without its script.

## Traps and their evidence

| Symptom | Cause | Fix | How the cause was found |
|---|---|---|---|
| A translation seems complete although later English links are absent | Several new ideas were appended inside one existing paragraph | Split those source additions into semantic keys and list absent prose and URL keys | Compared per-language paragraph destinations with the English source |
| A page silently falls back to English | A generic translation lookup returns the source value when a key is absent | Refuse catalogue drift and enumerate omissions; render only the language's own blocks | Removing a Portuguese key and substituting its English value both made the gate fail |
| Tidy rejects a screenshot's width | GitHub's Markdown HTML permits percentage dimensions that HTML `width` does not | Keep responsive sizing in CSS and integer dimensions only in HTML | Tidy's diagnostic identified `width="99%"` |
| An old checker warns about current standard attributes | Tidy 5.8 predates `aria-current` and `decoding` | Keep its version and raw output; recognize only those exact warnings, fail other diagnostics | Inspected every warning across all pages against current HTML/ARIA behavior |
| The browser requests a missing favicon despite no remote assets | The browser makes its own default `/favicon.ico` request | Declare the local wordmark as the icon | Network responses contained a 404 before the explicit icon was added |
| Rebuilt files exist on disk but the server serves an empty folder | Deleting and replacing the output directory leaves a bind mount attached to the old inode | Keep the generated output root and replace only its children; guard it with a build marker | Compared the host's rebuilt index with the container's mounted directory |
| Enter does not open a native language menu in the test | A synthetic keyDown omitted the text needed for the browser's keypress behavior | Send complete Enter key events, including carriage-return text; use Tab to reach the summary and links | Focus reached SUMMARY but `details.open` stayed false until the event was complete |
| The drawing test fails before any page code runs | A debugger hook declares a global name already provided by the browser | Keep instrumentation inside its own function scope | `Runtime.exceptionThrown` named the duplicate `location` identifier |
| A picture is below a phone's first screen | The full source opening plus large type consumed the viewport | Measure its top edge, tighten spacing and typography, preserve all source words | Captures and bounding rectangles at 390 × 844 showed the picture enter the first screen |
| External badge images cannot be fetched | Their host refuses the request | Retain their existing alternative texts as links to the original destinations; record the choice | HTTP 403 from the badge endpoint, followed by an entirely local runtime request log |
| A purported one-click publish cannot serve the preview folder | Branch Pages sources are restricted to root and `/docs`; local ignored output is not online | Describe the preparation and the final Pages Save step separately | GitHub's current publishing-source documentation |
| A numerical row overstates accepted work | One source list entry may contain several PRs or collaborative testing, while other entries are still in review | Name the counted unit and exact source section; never call entry count a merge count | Counted only entries between the source's Merged and In review markers and read multi-PR entries |

## What this saves

One source edit has one import, one layout change reaches every existing language, and a reviewer can trace each paragraph to its original line.
The menu needs no script, the public URL remains a deployment choice, and a preview can be reviewed without replacing the repository's front page.
The forms followed are Daniel's own site for the native language menu and Dionatan Simioni's [KamLynk project pages](https://dionatansimioni.github.io/KamLynk/) for a static site within its project repository.
No third-party code is required by this recipe.
