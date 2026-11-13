# writing-front-pages: lessons from the lanes of 25 October to 6 November 2026

Harvested by ORDER 429 from the accepted lane reports; each line names the lane it came from.
A trap gives its symptom, its cause, its fix and how the cause was found; a recipe gives the commands and the result to expect.

## Recipes that worked

- Guide to HTML and PDF without Docker or a display: python-markdown with the earlier guide's CSS and inlined images, then headless Chrome print to PDF; check first pages visually; checks per file: no mid-sentence dash, no download token, no private name. (lane crash-course-231)
- Link audit for public pages: `curl -L`, save bodies, record final status, effective URL, content type, title; 87 distinct URLs gave 85 HTTP 200 and 2 HTTP 403 (bot walls, listed as exceptions); inspect titles of the 200s for the expected destination; an authentication redirect is not evidence, replace it with the public index; check each `#fragment` in the returned HTML. Style check script covers prohibited markers, no sentence-separating dash, adjacent duplicate lines. (lane tpac-public-pages-264c)
- Registered marks: brand link on the first mention outside any link or code, or in the closing notice when every prose mention is linked; the exact closing notice line as supplied by the licensor. Skill already has the HDMI example and notice (line 105). (lane hdmi-marks-357)
- README translation checks that passed: the URL set of source and translation compared in both directions (101 targets; 105 in zh-CN), 21 headings in the same order and levels, language selector byte-identical, HTML `src/href/srcset` identical, relative targets exist, English anchors (`<a id>`) before translated headings so fragment links still resolve, the source hash enforced so a source change fails the check, `publish-check: clean`. Skill already says explicit anchors. Add: KDE terms taken from KDE's own catalogs (`msgid "System Settings"` in systemsettings.mo) rather than invented. (lane readme-ja / readme-zh-tw / readme-zh-cn / readme-ptbr-pl)
- Name-collision check for a new term: exact-phrase queries on the web, an IETF datatracker search, arXiv and OpenAlex; record zero results and repeat them independently; state that the check covers stated indexes, not trademark registers; use the full name at first mention when the acronym is already used. Reader review by a second model is task-aware, so it does not replace a cold reader. A Markdown-only change is not validated by ReSpec CI. (lane srn-name-276)
- Publish the document that defines a term before, or together with, the pages that link to it; the only HTTP 404 in a pre-publish link check should be that intended URL. Keep a pre-edit copy of each file (`evidence/before/N.md`) and a patch per repository for review. (lane dpfr-term-267)

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: public text still says "both eyes at full size" or half formats "converted and upscaled to full SBS". Cause: an older wording survived in a ledger row and ATTRIBUTIONS. Fix: use "full side by side, two separate pictures, left eye first, each at its own resolution, declared once". Found by: grepping the old phrase after the rule changed. (lane helpers-update-220)
- Symptom: a mark-adding edit changed or split an existing link and the verifier accepted it. Cause: the verifier allowed reconstruction of split links. Fix: a verifier with no file-specific rules: remove only the added brand-link wrapper, the marks and the added notice, then require every original line and the whole byte sequence to equal the base, and compare each rendered hyperlink in order. Result 48 files, 7,773 lines, 132 lines with marks, PASS. Found by: the reviewer spotting the defect. (lane hdmi-marks-357)

## Perks of the part

- Offline anchor check against the pushed ref: slug rule lowercase, strip punctuation, spaces to hyphens, suffix duplicates; a public text that states a project fact links the page that proves it. (lane fable-vision-304)

## Measured facts

- External link audit of 608 URLs: 592 OK, 10 HTTP_ERROR, 1 URLError; a 403, 418, 999, TLS error or timeout is an unverified destination, not proof a page is gone. Pre-existing: 26 of 178 fragment links point to missing headings in translated READMEs, with identical heading ids before and after. (lane hdmi-marks-357)
- A creator-facing message in a non-English language needs a page in that language (every link in the draft was English); the programs page has no line on depth as a 3D source (libstereo-dibr, the FFmpeg `dibr` filter). Phone VR viewers cost R$ 28.79 to R$ 86.04 in a country-agnostic search, checked 2026-10-23. (lane friends-fabio-216)


## A demo page with a control panel (ORDER 540, 13 November 2026)

**Before:** the page asked someone to pick a connection speed and press Restart with these settings.
At 1280 pixels the always-open measurements panel occupied about 38 percent of the content width; at 360 × 800 it began just below the viewport.
Some controls changed the active run, some waited for restart, and changing language discarded pending fields.
The scene's photograph count existed only in its screen-reader description.

**After:** the scene has a visible state line and seven named surface states, speed choices replay immediately, and Play again stays in view.
The full former panel remains in Details and measurements, closed initially, with a pending note next to each deferred setting.
Three small pictures explain recipe, computed surface and photograph takeover; the longer About remains below.
At the end, hold and split comparison use saved drawings while the procedure player remains stopped.
These are presentation choices for showing the same process, not new claims about the rendering technique.

**Recipe:** inventory controls by when they act; put the changing result before its instrument; move details as a whole; preserve pending state while translating and preserve the query when replaying.
Measure which elements are initially visible as well as checking reflow, and give an independent reader only the resulting first-screen block.
A source-aware self-review is not that reading.

- Symptom: a control changes a number but the finished picture stays the same.
  Cause: changing a limiter after download cannot repeat the event being demonstrated.
  Fix: the main speed choice restarts the demonstration, with that behavior stated before use; detailed deferred settings explicitly say how to apply them.
  Found by: the before-page control audit and unchanged firstFrame/timeOrigin after a speed change.
- Symptom: the short lead passes a word count, but the first screen still reads like a technical instrument.
  Cause: the adjacent panel dominates attention and repeats implementation detail before the person sees the outcome.
  Fix: show the scene's changing state, retain each measurement behind one disclosure, and use three concrete illustrated steps.
  Found by: inspecting the desktop and phone captures, not by counting the header alone.
- Symptom: shrinking a demo removes its controls, diagnostics or credits.
  Cause: treating simplification as deletion.
  Fix: inventory first, move the whole panel and keep its fields, component bars, timeline/table, player figures, notices and camera control reachable.
  Found by: comparing every old control and document link with the new DOM and preserved source.
