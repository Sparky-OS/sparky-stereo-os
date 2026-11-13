# The front pages as a site

**For** a maintainer moving existing multilingual front pages into a static website: keep the words, links and anchors, use one layout, and prove the preview before changing the public front door.

Written on 2026-11-13 from the first pass that built the site, and extended the same day by a second pass that reviewed it, proved its drawing in stereo and set its type.

## Working recipe

1. Inventory the source pages by kind and language, including documents that will remain links to GitHub.
   Keep the Markdown as the editorial source, with its exact existing credit and flags.
   A missing page does not become an English page disguised as a translation.
2. Import one keyed catalogue per language, with English defining the shared keys.
   Keep paragraph text, destinations, picture sources and alternative texts as separate values.
   Record the source path, hash and line alongside each block.
   List missing and additional keys explicitly, including links placed differently by a translation.
   A line that only one language has gets its own key and keeps its place: record how many of its paragraph's own lines come before it, and draw it there.
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
   Write each picture's real width and height, read from its file, and let only the first screen's picture load at once.
7. Build both address forms: `--base-path /` and `--base-path /repository/`, with the chosen origin supplied separately.
   Check every local link and fragment, including images, language alternates and 404 navigation.
   The build directory is an artifact, not an automatically published website.
8. Run `python3 site/check.py` with offline HTML Tidy, then `python3 site/controls.py`, then `python3 site/verify_text.py --control`.
   The controls must reject missing translations, English substitutions, broken links, lost anchors, remote resources and insufficient contrast.
   The last command is the one that reads the Markdown and the built page separately and requires every word in the source's order.
   A check that only accepts good output has not established that it detects the fault.
9. Serve in an isolated static-server container and use a fresh browser context per case.
   [The browser checker](../../../site/browser_check.py) checks keyboard navigation with scripts off, local requests, cookies, language availability, wide and phone views, system light/dark, 320 CSS-pixel reflow and enlarged text spacing.
   Keep viewport and full-page PNGs outside the repository and inspect them.
   Record the browser, checker versions, page weight, measured criteria and untested assistive technologies.
10. Give a cold reader the first screen and the proposed additions without project context.
    Ask what it is, who it serves, the next step and what confused them.
    A refused service call is a recorded failure, not an endorsement; an addition gated on that verdict stays on a commit of its own until it is read.
11. Hand back a clean branch, reproducible commands, captures, source maps and the exact future switch steps.
    Leave the READMEs intact until the switch is approved.
    As checked in [GitHub's publishing-source documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) on 2026-11-13, branch publishing selects a branch's root or `/docs`, not any arbitrary nested folder.
    A generated output can later become the root of a dedicated publishing branch; saving that Pages setting is a deployment action.

## Reviewing a generated site as a second reader

The second pass is for what the first could not see in its own work.

1. Build from a clean checkout at the handed-over commit with the first pass's own commands, rerun every check its report names, and say which pass for you.
2. Read each check for what it compares with what.
   A check that compares the output with the generator's own second rendering proves the files were not edited afterwards; it cannot see a sentence the generator moves or drops.
   Prove the words with a reader that shares no code with the generator: the Markdown and the HTML read separately, compared as two sequences of words and punctuation marks, with the expected differences named (a language row that became a menu, a credit line added to a footer) and everything else a failure.
3. Prove "the sources are untouched" by git blob, not by trust: `git rev-parse BASE:FILE` beside `git hash-object FILE`, for every source.
4. Look at every language's first screen at a desktop and a phone width in a container browser, and measure before judging:
   where the status and the next step begin, the characters per line of each kind of text, the fonts the browser really used, which pictures say their size, and the layout shift on a slowed connection.
5. Write the findings as a table: what, where, how serious, fixed in which commit or left with the reason.
6. One change per commit, with a capture before and after and the measured numbers in the commit message.
   The approved wording is not yours to rewrite; a sentence you would change goes on a list with its reason.

What this found on the edition's site: one sentence of the English detail page built before the two it follows, a duplicate of the main picture in the still form, the status line 1,447 to 1,596 px down a 960 px screen, text 115 characters wide, every picture lazy and unsized, and a drawing whose three levels were all in front of the screen.

## A depth drawing, proved in stereo

Only add a drawing when the design asks for it.
It is decoration: `aria-hidden`, apart from the status and the next step, carrying no information the text lacks, with no anaglyph and no depth setting, eye swap or output format on the page.
Read [one world, two cameras](../../stereo-two-cameras/SKILL.md) and its [browser evidence](../../stereo-two-cameras/references/x3d-in-the-browser.md) first.

**Place the scene by the browser's rules, not by eye.**
The edition browser's 3D Canvas route recognises a perspective camera uploaded as a matrix uniform and draws the scene once more from a second, parallel camera.
A point at distance z along the camera axis then has the parallax `separation * (plane / z - 1)`, positive in front of the screen.
The published build takes 2 percent of the canvas's width as the separation and five times the camera's near distance as the plane.
The staged build takes the person's sunk limit, in the output's pixels, as the separation, and for the plane the distance where the nearest and the farthest part of the scene have equal and opposite parallax, `2nf / (n + f)`, no further than `n * (1 + popped / sunk)`.
So with D the camera's distance to the thing that must sit at the screen:
- the near distance is D / 5;
- what comes forward stands at D / (1 + R) and what goes back at D / (1 - R), which balance at D for any R;
- R is the desktop's default popped limit over its sunk limit, 0.4, so the nearest thing lands on the popped limit and nothing passes either limit.

**Nothing turns.**
A camera that turns tilts every plane, the nearest edge comes nearer, and the browser that reads the scene's depth fixes its plane from the first frames.
Move the viewpoint sideways instead, as a shear of x by z in the view matrix: each plane keeps one distance in every frame, and the thing at the screen stays where it is.

**Draw what the desktop does.**
On the stereo desktop windows sit at the screen or behind it, and what opens over a window comes forward: a background window, the window in use, its menu.

**The still form is the page as written.**
Where no drawing can run, the drawing's place should not exist, so the front page's own picture is first and appears once.
A stylesheet can decide that before the first paint: show the place under `@media (scripting: enabled) and (prefers-reduced-motion: no-preference)`, and let the script mark it off where WebGL is missing or its context is lost.

**Stop.**
End the motion (4.8 seconds here, inside the timing boundary of [WCAG 2.2 SC 2.2.2](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html)), stop while hidden or off screen, and leave no pending animation callback.

**Prove it at the compositor.**
Arithmetic on the page's own matrices shows the design; only a capture shows the picture.
Run the page in the edition's browser under a private Stereo KWin with a GPU, one fresh container and session per case, as [a WebGL control proven with a GPU](https://github.com/Sparky-OS/sparky-stereo-os/blob/main/skills/stereo-two-cameras/references/webgl-control-on-a-gpu-and-without.md) and [the proof rig](../../stereo-proof-rig/SKILL.md) describe.
1. Let the script write its scene's numbers on the canvas (`data-scene`: distances, near, each plane's colours) and a mark when it is at rest, so the measurement reads the page's values and waits for the right frame.
2. Per case keep four things: the declaration lines of the browser's Wayland log (one `create`, one `set_content(3)`), the count of its two-eye presents, its own log of separation, limits and plane (`MOZ_LOG=sync,WebGLStereo:4`), and the ScreenShot2 pair.
3. Measure each plane by the horizontal shift that lays the right eye's picture of its unoccluded part on the left eye's, searched in steps of 0.01 px with linear interpolation; keep an edge and a marker measure beside it and say when they disagree.
4. Compare with the closed form, using the plane the browser's log says is in use.
5. Controls: the camera switched off (`webgl.stereo-camera.enabled` false: nothing declared, eyes identical), each stereo eye against that control (differences inside the canvas only), scripts off (`javascript.enabled` false) and reduced motion (`ui.prefersReducedMotion` 1), and the earlier drawing as the case that must read wrongly.

Measured on 2026-11-13, a 456 px canvas on a 1920 px output, limits 10 and 4, an NVIDIA card:

| build | background window | window in use | menu | predicted |
|---|---|---|---|---|
| staged (+stereo3d14) | -4.00 px | 0.00 | +4.00 | -4.01, -0.02, +3.98 from its plane, 3.394 |
| published (+stereo3d9) | -3.74 px | 0.00 | +3.75 | -3.65, 0.00, +3.65 at 2 percent |
| either, camera off | 0 | 0 | 0 | nothing declared, 0 of 2,073,600 pixels differ |

The first version of the drawing, on the published build: 0.00, +1.50 and +3.75 px, all at or in front of the screen.
Not shown by this: a television, a headset, or the AMD and Mesa path.

## Type across scripts

1. Give running text a measure and count it, do not assume it: for each paragraph, its characters divided by its lines (a range's client rectangles give the lines).
   Under 80 characters a line for the Latin-script languages and about 38 for Japanese, Chinese and Korean, whose characters are as wide as they are high (WCAG 2.2, SC 1.4.8 names 80 and 40).
   Lists of links, pictures and grids keep the page's width.
2. Japanese, Chinese and Korean take a larger line height (1.8 on a desk screen, 1.6 on a phone), upright emphasis, since their scripts have no italic, strict line breaking for Japanese and `word-break: keep-all` for Korean, which breaks between words.
3. Name each language's own system fonts for its page and for any passage marked with that language, so the Simplified and the Traditional page, and the language menu's own entries, never borrow another language's forms of the shared Han characters.
   Nothing is fetched: these are local font names.
4. Hyphenate by the page's language on narrow screens, long words only (`hyphenate-limit-chars`).
5. Ask the browser which fonts it really used (`CSS.getPlatformFontsForNode` over the DevTools protocol) and say which machine that was; a container's fonts are not a reader's.
6. A script no page uses yet needs no rule: count its letters in the built pages first (no Cyrillic letter on this site on 2026-11-13).

## Traps and their evidence

| Symptom | Cause | Fix | How the cause was found |
|---|---|---|---|
| A translation seems complete although later English links are absent | Several new ideas were appended inside one existing paragraph | Split those source additions into semantic keys and list absent prose and URL keys | Compared per-language paragraph destinations with the English source |
| A page silently falls back to English | A generic translation lookup returns the source value when a key is absent | Refuse catalogue drift and enumerate omissions; render only the language's own blocks | Removing a Portuguese key and substituting its English value both made the gate fail |
| A sentence is built before the two it follows, and every check passes | The importer took the lines that only English has out of their paragraph and appended them after it | Each such line records how many of the paragraph's own lines precede it and is drawn there | A reader with no code shared with the generator compared the words as sequences and named the sentence |
| "Built text matches each language exactly" passes on a page with a moved sentence | The check compares the built page with the generator's own second rendering | Keep that check for edited output, and add the independent word comparison with a moved and a removed paragraph as controls | Reading the comparison line of the check |
| An independent word check reports hundreds of differences such as `maintainers ,` | It split on spaces, so a link's closing tag put a space before the comma | Tokens are words and single punctuation marks; inline tags vanish without a space, block tags break | Every difference was a punctuation mark after a link |
| Tidy rejects a screenshot's width | GitHub's Markdown HTML permits percentage dimensions that HTML `width` does not | Keep responsive sizing in CSS and integer dimensions only in HTML | Tidy's diagnostic identified `width="99%"` |
| An old checker warns about current standard attributes | Tidy 5.8 predates `aria-current` and `decoding` | Keep its version and raw output; recognize only those exact warnings, fail other diagnostics | Inspected every warning across all pages against current HTML/ARIA behavior |
| Tidy says `trimming empty <i>` for a drawing made of empty elements | It trims empty inline elements | Put a no-break space in each and give it `font-size: 0` | The static gate's ten failures quoted the warning |
| The browser requests a missing favicon despite no remote assets | The browser makes its own default `/favicon.ico` request | Declare the local wordmark as the icon | Network responses contained a 404 before the explicit icon was added |
| Rebuilt files exist on disk but the server serves an empty folder | Deleting and replacing the output directory leaves a bind mount attached to the old inode | Keep the generated output root and replace only its children; guard it with a build marker | Compared the host's rebuilt index with the container's mounted directory |
| Captures taken while another command rebuilt the same folder | The preview and the capture serve one build folder | Never rebuild while a capture runs; take the set again | The two commands' start times |
| Enter does not open a native language menu in the test | A synthetic keyDown omitted the text needed for the browser's keypress behavior | Send complete Enter key events, including carriage-return text; use Tab to reach the summary and links | Focus reached SUMMARY but `details.open` stayed false until the event was complete |
| The drawing test fails before any page code runs | A debugger hook declares a global name already provided by the browser | Keep instrumentation inside its own function scope | `Runtime.exceptionThrown` named the duplicate `location` identifier |
| The same picture twice on one screen with scripts off, the first cut to fit | The drawing's place held a cropped copy of the main picture as its still form | The place exists only while a drawing can run; the page's own picture follows the opening | The scripts-off capture |
| The status line is two screens down on a desktop | The pictures kept the README's full widths between the opening and the status | One group in two columns on a wide screen, in the source's order in the document | Measured top of the status block in every language |
| A picture is below a phone's first screen | The full source opening plus large type consumed the viewport; later, a larger line height for one script did it again | Measure its top edge in every language after every type change; tighten spacing, preserve all source words | Bounding rectangles at 390 by 844, per language |
| A phone rule for line height changes nothing | A later rule of the same weight in the stylesheet overrides it | Put the narrow-screen rule after the general one, or name `html` in it | The measured number did not move |
| 72ch gives 86 to 90 characters a line | `ch` is the width of the zero, wider than the average letter | 66ch gave 81 to 83 | Counting characters per line in the browser |
| Code is no longer monospace on the Japanese, Chinese and Korean pages | A font rule on `:lang(ja)` matches every element of the page, code included | Name the page and a marked passage: `:root:lang(ja), [lang="ja"]` | The computed font of the first `code` element |
| English breaks "every" as "ev-ery" on a phone | `hyphens: auto` with no lower limit | `hyphenate-limit-chars: 12 4 4` | A script that counts words under ten letters laid on two lines |
| Layout shift always measures 0 | The observer was injected while scripts were disabled, so it never ran | Measure with scripts on and the network slowed | The identical zero in every case |
| Text moves as each picture arrives | No picture said its size, and all were lazy | Width and height from the file; the first screen's picture loads at once | Layout-shift entries at the pictures' arrival times |
| A geometry test reports 561 points within 1e-16 while every plane is in front of the screen | It applied its own separation and plane to the page's matrices and compared a formula with itself | Apply the browser's two rules to the page's own numbers, with the earlier drawing as the control that must fail | A capture of both eyes in the real browser |
| The "sunk" plane measures 0 px and the "screen" plane +1.5 | The browser's plane is five times the near distance, in front of the whole scene | Near distance a fifth of the distance to the thing at the screen | The closed form matched the capture within 0.1 px |
| On the build that reads the scene's depth, the thing at the screen sits at -0.75 px | The camera turned, the first reads saw a tilted plane's near edge, and that plane stayed in use at rest | A sideways shear instead of a turn: constant distances in every frame | Its log: `nearest 2.219 ... in use 3.098`, later `-> 3.391 ..., in use 3.098` |
| One plane's marker reads +4.16 where its edge reads +3.50 | The centroid of an anti-aliased blob in two differently shifted eyes | Match the plane's unoccluded part between the eyes in 0.01 px steps; keep the others beside it | Three measures agreed on two planes and disagreed on one |
| A plane's measure has a vertical difference of 2 or 11 px | The measured part is covered by a nearer plane, differently in each eye | Measure only parts no plane covers in either eye | A vertical difference in a scene that has none |
| The canvas is slightly blurred | Columns in `fr` put it at a fraction of a pixel (x 1052.4, width 455.6) | Give its column a width in rem | The probe's `getBoundingClientRect` |
| A wordless strip is wider than a 320 px page | Its tiles had fixed sizes | Sizes in em and a smaller font size on narrow screens, with wrapping as the last resort | The reflow check named the element |
| A test's "Ctrl+C" leaves the preview container running | A shell's background job ignores the interrupt signal | Send it with `timeout -s INT` to a foreground process | The container was still listed |
| A figure typed by hand is one less than the table's rows | The table's rule row was subtracted although the count had never included it | Count at build time from the record, never type a number | The build's count beside the note |
| External badge images cannot be fetched | Their host refuses the request | Retain their existing alternative texts as links to the original destinations; record the choice | HTTP 403 from the badge endpoint, followed by an entirely local runtime request log |
| A purported one-click publish cannot serve the preview folder | Branch Pages sources are restricted to root and `/docs`; local ignored output is not online | Describe the preparation and the final Pages Save step separately | GitHub's current publishing-source documentation |
| A numerical row overstates accepted work | One source list entry may contain several PRs or collaborative testing, while other entries are still in review | Name the counted unit and exact source section; never call entry count a merge count | Counted only entries between the source's Merged and In review markers and read multi-PR entries |
| Both cold readers refuse (`429 Too Many Requests`, `bootstrap pending`) | The services' own limits | One call each, the refusals recorded word for word, the test left owed, the gated addition on a commit that one revert removes | The two error lines |

## What this saves

One source edit has one import, one layout change reaches every existing language, and a reviewer can trace each paragraph to its original line.
The menu needs no script, the public URL remains a deployment choice, and a preview can be reviewed without replacing the repository's front page.
A second reader starts from a checker that already compares the words independently, and a drawing starts from distances that are right in both builds of the browser.
The forms followed are Daniel's own site for the native language menu and Dionatan Simioni's [KamLynk project pages](https://dionatansimioni.github.io/KamLynk/) for a static site within its project repository.
No third-party code is required by this recipe.
