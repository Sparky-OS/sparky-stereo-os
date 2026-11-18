---
name: contrib-debian
description: >-
  Report a Debian packaging bug the way a maintainer can act on it the same day: reproduced in a clean testing
  container, the fix inline as a patch against Debian's own source (apt-get source, Tags: patch), composed with
  reportbug as a non-root user, the bug queried over the BTS SOAP interface, under Debian's Code of Conduct, Diversity
  Statement and its generative AI resolution; also a Salsa merge request. Load it when a Debian package fails to
  install, a dependency is missing from Debian's package, a maintainer script breaks, reportbug exits 1 as root, a tag
  the BTS drops, or the edition carries a fix Debian should have.
---

# Contributing to Debian

Written on 2026-11-02 from three sources read that day: Debian's [Code of Conduct](https://www.debian.org/code_of_conduct) (version 1.0, ratified 28 April 2014), its [Diversity Statement](https://www.debian.org/intro/diversity), and the General Resolution [LLM usage in Debian](https://www.debian.org/vote/2026/vote_002).
Also from the [Developer's Reference](https://www.debian.org/doc/manuals/developers-reference/) (sections 4.4 and 7.1) and the edition's first three reports.
The first, snmptt [#1152863](https://bugs.debian.org/1152863), was fixed by its maintainer in snmptt 1.5-4 about an hour after it was filed.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is Debian's own practice.
Check freshness: re-read the Code of Conduct and the resolution before a round.

## The rules that come first

- **Debian's Code of Conduct** covers its mailing lists, IRC and every other channel: be respectful, assume good faith, be collaborative, try to be concise, be open.
  - A bug report is read by many people: one problem, short, with what you add to the thread.
  - Public channels are preferred for Debian matters, as the Social Contract's third point says, unless the matter is sensitive.
  - Problems with someone's conduct go privately to the administrators of that channel.
- **The Diversity Statement:** Debian welcomes contributions from everyone who interacts constructively.
- **Generative AI (GR 2026/vote_002, "Responsible Use of Generative AI", voted 15 to 28 August 2026):**
  - Debian neither endorses nor bans the tools.
  - Every contribution meets the same standards of quality, correctness and legal compliance.
  - The contributor stays responsible: understand, review and test what you send; submitting generated material without human review is against Debian practice.
  - Disclosure is encouraged, not required. The edition discloses it once in each report: "I found this with AI assistance and checked it myself".
  - Mass bug filing, bulk patches and large changes need prior discussion on project channels.
  - Never paste non-public information (embargoed security details, keys) into a third-party AI service.
- **More than ten bugs on one topic:** the Developer's Reference (7.1.1) asks for a mail to the debian-devel list first, and for the reports to go to the BTS's maintonly address, which skips the bug list.

## A report a maintainer can apply the same day

Daniel, on the first drafts, which linked to our own build scripts: "tell them the fix or don't send".

1. **Search first:** the package's open and closed bugs, and its newer version in unstable or on Salsa (the `Vcs-Git` field of its source). A fix already there is carried, not reported.
   Search older and newer versions too: `https://sources.debian.org/api/src/SOURCE/` lists every version with its suites, and `https://sources.debian.org/data/main/PREFIX/SOURCE/VERSION/debian/control` gives each one's control file, so you can say in which release the fault entered and which releases carry it.
   Look at the sibling packages of the same team: the same fault may sit in another of them, and the fix the team already uses elsewhere is the form to follow.
   When the same fault is in several packages, each gets its own report with its own tested patch.
   **Find out what the maintainer intends** before calling a behaviour a bug: read `README.Debian`, the changelog and the closed bugs.
   A default in a configuration file that the administrator is meant to adapt is not a missing dependency.
2. **Reproduce in a clean container** of the suite you report against, with Debian's own package installed: the failure first, then your fix, both measured.
   Real hardware where the bug needs it (urfkill needed a laptop's radios; never pass a workstation's `/dev/rfkill` into a container, it switches the real radios).
3. **The fix as a patch against Debian's own source** (`apt-get source PACKAGE`), inline in the report, with `Tags: patch`.
   Never a link to your own repository or build script.
4. **Compose with reportbug**, Debian's own tool, as a non-root user in that container (as root it exits 1 and writes nothing):
   `reportbug --ui text -b --no-check-available -c --no-bug-script -x --no-cc-menu --mode standard --email ADDRESS --realname NAME -s SUBJECT -S SEVERITY -T patch --body-file BODY -o OUT.eml PACKAGE`
   Then send `OUT.eml` with your mail client.
5. **Severity** from Debian's list (critical, grave, serious, important, normal, minor, wishlist): a service that fails to start with its default configuration is `important`.
6. **Tags** only from Debian's list (patch, moreinfo, upstream, confirmed, l10n, ftbfs and the others in the BTS documentation).
   "regression" is Launchpad's, not Debian's; the BTS drops it.
7. **The body:** what fails and where (file and line), the exact message, why (the missing dependency, the lost build flag), the patch, and the one line on AI.

## After sending

- The BTS answers with the bug number by mail.
  Its web pages may sit behind a browser check; query it over SOAP instead: `https://bugs.debian.org/cgi-bin/soap.cgi`, with `get_bugs` (package, NAME), `get_status` and `get_bug_log`.
- Answer the maintainer in the bug itself (reply to the bug's own address), one point per mail.
- When Debian's fix reaches testing, retire the distribution's own build of that package, so people get Debian's.

## Packaging changes

- Many packaging teams take merge requests on [Salsa](https://salsa.debian.org), Debian's GitLab; the source's `Vcs-Git` names the repository, and Salsa CI runs the archive's tests on it.
- A report with the patch is still the route every maintainer reads; use a merge request where the package's team works that way.

## Lessons from the lanes, October to November 2026

From the lanes of 25 October to 6 November 2026; add the next lesson here as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).

- **A report closed as not a bug, and what it taught.** pkcs11-daemon [#1152864](https://bugs.debian.org/1152864), filed 2026-11-02 and closed by its maintainer on 2026-11-10: the report called the default `PKCS11_LIB` (which names libsofthsm2) a missing dependency and proposed a hard `Depends`. The maintainer's answer: `/etc/default/pkcs11-daemon` is a configuration file the administrator adapts, the default names the library most installations already have, and a hard dependency would be wrong. He was right. **Symptom:** a service fails with its shipped default on a system that lacks an optional backend. **Cause of the wrong report:** reading a configurable default as a requirement. **Fix:** the "find out what the maintainer intends" step above; such a case is at most a `Suggests`, and usually no report. **How found:** by reading the tracker again over SOAP eight days later; the closing mail had not been recorded. Read the tracker for every open report of yours whenever Debian work starts.
- **A missing dependency that is one (libusbmuxd-dev, 2026-11-18, not yet reported):** the development package's pkg-config file has `Requires.private: ... libimobiledevice-glue-1.0` and the package does not depend on `libimobiledevice-glue-dev`, so `pkg-config --cflags libusbmuxd-2.0` exits 1 with the package alone. The difference from the case above: nothing here is configurable, and the package cannot do its one job. The search found the release where it entered (2.1.0-1; 2.0.2-3 is right), no report anywhere, the same team's libimobiledevice-dev already carrying the dependency (the fix's form), and a second package with the same fault (libirecovery-1.0-dev). Nobody had met it because the only two sources in Debian that build against it name the glue library themselves: list the reverse build dependencies (`Build-Depends` in the suite's Sources index) to learn why a fault stayed hidden.
- contrib-debian already says "compose with reportbug as a non-root user in a clean container"; this lane adds a worked example: reproduce on Debian testing (dkms 3.2.2-1), add `openssl` to Depends in the source, rebuild, show the CMS signature plus both negative controls in the same container, then compose the patch-bearing report (reportbug 13.2.0+nmu1 as uid 1000). Installing the dependency does not repair modules already built unsigned; they need a rebuild. (lane debian-dkms-report-371)
