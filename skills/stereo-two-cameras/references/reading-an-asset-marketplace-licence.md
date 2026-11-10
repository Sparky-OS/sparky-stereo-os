# Reading an asset marketplace's licence for a free operating system

Use this before 3D assets (scans, models, materials) go into a package, a theme or a stereo world that a free operating system ships.
The question is never "is it free to download": it is "may the whole system hand a copy to everyone, may people extract and change it, and may a script fetch it".

## Recipe

1. Read the binding text, not the summary page.
   A marketplace page often carries a short "You may / You may not" box that says it is "for your convenience only" and "not legally binding".
   The licence agreement is a separate document; find it and quote its section numbers.
2. If the licence page is a blank shell for curl, its text is loaded by the page's own script.
   List the page's `<script src>` files, grep them for the document key (here `eula.getContent` with `eulaKey`), then fetch the same address the page asks for, read only, anonymous, with an honest User-Agent.
   Fab: `curl -A "NAME (licence reading; no login)" -H 'Accept: application/json' https://www.fab.com/i/eula/fab_eula` returns `{"body": "<html>", "version", "key"}`; strip the tags.
3. Per asset, not per site: the listing's own JSON holds the licence names and the AI flags (Fab: `/i/listings/UID` has `licenses[]`, `isAiForbidden`, `isAiGenerated`; `/i/listings/search?seller=NAME` lists a seller's assets).
4. For each of the five questions quote the clause: ship whole or cut or converted or derived; fetch at install; attribution; engine-only; AI training.
5. A page behind a bot challenge (Cloudflare 403) is read from the Wayback Machine (`https://archive.org/wayback/available?url=...`, then the `id_` form of the snapshot, with `--compressed`), never with a spoofed browser agent; say the snapshot date, because it may predate a change.
6. Save every page with its sha256 and the date read.

## Clauses that decide for a free operating system

- A "do not redistribute on a stand-alone basis" clause: a package of the assets is a stand-alone copy, even free and even bundled with other assets.
- "Only as an inseparable part of a Project in object code; restrict end users from extracting": incompatible with files in /usr/share that anyone may copy (and with Debian's freedom rules).
- A non-compatible-licences clause naming GPL, LGPL and CC BY-SA: the system around the assets is GPL.
- "Do not make the content available in world- or level-editing tools": a home the person customises and exports.
- An account or an acceptance click before download: a package cannot do it for the person.
- A terms-of-service clause against automated access (Fab Terms of Service 1.8) decides the install-time fetch even when the licence allows the use.
- Versioning: which terms govern an asset already acquired (Fab EULA 7(a): the terms at acquisition).
- An AI clause that depends on a per-asset tag (Fab "NoAI"): read the tag of each asset.

## Traps

- Symptom: the FAQ says CC0 but the licence page says otherwise. Cause: the site changed its licence and left an old page (Quaternius: FAQ "All models are under the CC0 License", licence page "Quaternius Asset License (QAL) v1.0, last updated 8/28/2026", no redistribution as assets, "whether alone or bundled"). Fix: take the dated licence page and the file shipped in the pack; record both.
- Symptom: a library announced "free" is still not shippable. Cause: free of charge is not a free licence (Megascans on Fab are free and under the Standard Licence, no stand-alone redistribution).
- Symptom: the news post says "terms updated" but the agreement's "Last updated" is older. Cause: the change was in a per-asset flag or in another document (Fab EULA "Last updated: October 1st, 2024"; the AI change shows as `isAiForbidden: false` on the listing). Fix: read the flag on the assets you mean to use and say which document you could not read.
- Symptom: curl returns a 2 KB page. Cause: script-rendered. See step 2.
- CC0 pages can still bind the website: Poly Haven's Terms of Service forbid scraping without permission although the assets are CC0, so a fetch at install is a question to the site, while shipping the files is allowed.

## Found how

Fab EULA text from the page's own bundle (`eula.getContent`, `/eula/${eulaKey}`); listing flags from `/i/listings/UID`; Quixel's FAQ from the `FAQPage` JSON-LD in the page source; ORDER 484, 2026-11-10.
