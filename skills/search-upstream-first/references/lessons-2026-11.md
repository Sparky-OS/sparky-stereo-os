# search-upstream-first: lessons from the lanes of 25 October to 6 November 2026

Harvested by ORDER 429 from the accepted lane reports; each line names the lane it came from.
A trap gives its symptom, its cause, its fix and how the cause was found; a recipe gives the commands and the result to expect.

## Recipes that worked

- Upstream search for a dpkg change: fetch dpkg main and deepen until the pinned release is an ancestor; list commits touching configure.c/unpack.c/archives.c since that release; search the dpkg bug list and the forge's merge requests (the Salsa mirror refused the API with HTTP 403, so say the MR search was not exhaustive); save evidence files (lane dpkg-lean-conffiles-376)
- Check the vendor's own packaging before inventing a lock: NVIDIA's Driver Installation Guide "Version locking" documents a pinning package per version; apt_preferences(5) says the first specific-form record matching decides the priority and preferences.d is read in lexicographic order; apt's changelog (2.9.3, 2.9.17) explained strict pinning (lane nvidia-dkms-link-gate-329)

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: "no upstream fix" claimed for DKMS re-signing. Cause: Debian's bug tracker pages are behind a browser challenge, and bts-link had tagged #1035707 fixed-upstream although the upstream issue was closed as stale without a fix. Fix: read the bug log over SOAP and the upstream issue itself; a "fixed-upstream" tag is not evidence. Found by: reading the bug log message that says the tag is misleading. (lane dkms-unsigned-370)
- Qdrant through the harness: queries of a few words return EMPTY, full sentence questions return hits. The same happened to lane 410 (a list shaped parameter returned EMPTY). Phrase corpus queries as a sentence and pass a string. (lane ffmpeg-six-fixes-377)
- Symptom: a brief says "the published package aborts and lacks fix X" and a lane is launched. Cause: the published source already carried the same three lines as patch 0052 (added with +stereo3d6); the report's premise came from reading the fork, not the packaged binary. Fix: before briefing a fix as missing, list the published source's debian/patches and changelog, grep for the function, and run the PR's reproducer against the packaged libraries (here exit 0, 48 frames). Found by: measuring with the packaged +stereo3d9 libraries. Existing skill talks about searching upstream first, not about checking our own published patches. (lane ffmpeg-hwaccel-carry-410)
- Symptom: a search of Qt's Jira returns no JSON. Cause: the REST search on `bugreports.qt.io` answers 301 to `qt-project.atlassian.net`, and there the version 2 search answers "The requested API has been removed". Fix: a plain GET of `https://qt-project.atlassian.net/rest/api/3/search/jql?jql=<JQL, URL-encoded>&fields=summary,status,created&maxResults=30`, the URL built in Python (a curl option that encodes form data reads as a write to the outreach guard); it returned 8 issues for QVulkanWindow and imageArrayLayers on 2026-11-15. Qt's Gerrit REST answers 403 to a script, so merged changes come from the GitHub mirror's history (`api.github.com/repos/qt/qtbase/commits?sha=dev&path=<file>&since=<date>`) and the report says open Gerrit changes were not searched. Found by: the 301 page and the API's own error message. (lanes qt-vulkan-rhi-two-views-556, vulkan-two-views-followups-573)

## Perks of the part

- lore.kernel.org answered plain curl with an honest user agent (try it before the Wayback Machine); searching by symbol finds in-flight patches that commit searches miss. The skill already names the shallow-clone route; add the symbol search. (lane amdgpu-devcoredump-deadlock-417)

