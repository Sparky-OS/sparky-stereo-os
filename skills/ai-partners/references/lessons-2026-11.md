# ai-partners: lessons from the lanes of 25 October to 6 November 2026

Harvested by ORDER 429 from the accepted lane reports; each line names the lane it came from.
A trap gives its symptom, its cause, its fix and how the cause was found; a recipe gives the commands and the result to expect.

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: a hosted model returns an empty answer for a nine-language review in one request. Cause: request size. Fix: one language per request (glm-5.3 worked; mistral-large-4 for Polish). Same limit seen with `repo_files` above about 11 KB (files near 10 KB work). (lane dkms-unsigned-370)
- Symptom: iso.org returns 403 to the fetch tool, a spoofed-user-agent curl is refused by the permission classifier, IEC webstore prices load by JavaScript. Cause: bot walls. Fix: read the catalogue through committee.iso.org mirror pages and webstore.iec.ch, record the date, never use browser tools or a spoofed agent. Found by: the 403 and the classifier refusal. (lane paid-standards-396)
- Symptom: listings priced CHF 0 (14496-12, 23008-12, 23009-1) while an actual purchase shows a stamp. Cause: the tools read a JavaScript price as zero. Fix: have a person re-read in a normal browser once before quoting a price. Prices seen: 23000-11 CHF 135, 14496-15:2024 CHF 227, 13818-1:2025 CHF 227, 21496-1 CHF 100, CTA-861-I USD 405 (non-member), CTA-861.3-A USD 74. (lane paid-standards-396)
- Symptom: a subagent's write of REPORT.md is refused ("Subagents should return findings as text"). Cause: the harness. Fix: return the full hand-back as the final message and summarise it in the task list. Same in fable-vision-304 and milton lanes. (lane skills-gap-323)

## Perks of the part

- Review rule for a model-written essay: distinguish predictions about review capacity from established results; keep disputed claims with the evidence that would resolve them, since agreement among models is not a check; keep the allocation of reviewer attention visible beside contributor obligations. (lane astra-vision-300)

## Measured facts

- A national registered-engineer route to free standards may exclude ISO/IEC (Confea CP 26/2023 text); a national adoption price (ABNT NBR ISO/IEC) was on no static page, so no discount figure can be computed. State "not found" instead of computing from an assumed price. (lane paid-standards-396)
- Free substitutes when a spec is paid: HDMI 1.4a 3D extraction is not offered free (hdmi.org shows only 1.3a behind a form), so the kernel's drm_edid.c and hdmi.h carry the clause numbers; Debian Policy is no longer a forky package (take 4.7.4.1 from debian.org, 23 pages, one source_url per chapter); git.dpkg.org serves a bot check, use salsa main; man pages use manpages.debian.org/testing. 148 man pages ingested. (lane reference-corpora-324)
- `sparky-stereo-skills find` ranks words, not meaning; a symptom whose words appear in no description or task row is not found until the metadata names it; stemmer is English only. When new kind of work arrives, add its symptom to tools/tests/test-skills-find.py. The refusal test must not accept argparse's own "unrecognized arguments". A test that passes on the old helper guards a regression but does not prove the feature. (lane skills-gap-323)
- Measured: consult_skills searched only skills_general and returned no Sparky skill for six symptoms; an optional `skills_sparky-stereo` index built from the installed tree would fix it. Image_video_corpus has no ITU-T H.264 or H.265; qt6_corpus is Qt 6.6.3. (lane skills-gap-323)

