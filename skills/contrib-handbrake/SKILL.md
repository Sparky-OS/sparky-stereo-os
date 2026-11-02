---
name: contrib-handbrake
description: >-
  Contribute to HandBrake on GitHub with its issue-first template, AI disclosure
  rules and tested-platform declarations. Load with upstream-outreach before a
  HandBrake pull request.
metadata:
  requires-packages: handbrake-cli
---

# Contributing to HandBrake

Written on 2026-10-24 from HandBrake's own documents, read from the current tree and web.
The rules that come first were added on 2026-11-02 from `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md` and `.github/PULL_REQUEST_TEMPLATE.md` on master and from the [contribution guide](https://handbrake.fr/docs/en/latest/contributing/contribute.html), read that day.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is HandBrake's own practice.
Re-read `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md` and the contribution guide before every round.

## The rules that come first
- **HandBrake's Code of Conduct** (`CODE_OF_CONDUCT.md`, adapted from the Contributor Covenant 1.4).
  The guide begins with it: "First and foremost, familiarize yourself with the project's Code of Conduct."
  - Its standards: welcoming and inclusive language, respect for differing viewpoints, accepting constructive criticism gracefully, focusing on what is best for the community, empathy.
  - HandBrake adds to the unacceptable conduct: "Posting content which is illegal or of dubious legality. (This includes but is not limited to: illegally obtained copyrighted content, circumventing Digital Rights Management etc)".
  - It covers the project's spaces and public spaces where someone represents the project.
    Reports go to the project team through the Report page on handbrake.fr.
  - "This is a volunteer driven project": the team cannot read every post, and an answer is not always quick.
- **The route: talk first, then code.** The guide: "Please ask the HandBrake Team via one of the Community Support channels before making changes as this will increase the likely hood of a change being accepted", and "Failure to communicate what you are working on may lead to duplicated efforts or rejection of your contributions".
  Then an issue, its acceptance, and a pull request on GitHub, as the template below demands.
- **AI** (the guide's "Code" and "Translation" sections):
  - "If AI is used in the process of making a change, it must be disclosed in the Pull Request."
  - "Pull Requests may be rejected without further information if the change is not suitable for the project. For example, issues with: Code Quality / Style, Design, Security Issues, Inappropriate use of AI, Licenses / Copyright etc."
  - "Use of AI services to translate HandBrake is not permitted." Interface translations go through HandBrake on Transifex.
  - `CONTRIBUTING.md` itself: "contributions not meeting the project's goals or standards may be rejected".

## Where
- Pull requests are on https://github.com/HandBrake/HandBrake.
- The official contribution guide is https://handbrake.fr/docs/en/latest/contributing/contribute.html.

## The pull-request template
- The template demands an issue first: "Create an issue describing the change."
- It demands agreement before code: "Discuss the issue with the HandBrake team to ensure that the idea has been accepted." The template adds: "(An open enhancement request does not equal acceptance)."
- The template demands a "Tested on" checkbox for Windows, macOS or Ubuntu; the pull request must state which one.
- The guide also asks contributors to introduce themselves "on a ticket or one of our Community channels before working on a issue".
- Disclose AI assistance in the pull request, as the rules above say; the reviewer decides whether the result is accepted.

## Tests
- The template provides "Log file output (If relevant)" and "Screenshots (If relevant)" fields for project-specific evidence.
- Run the affected encoder path with a small input and preserve the input layout and output declaration.
- The template's log-file and screenshot sections exist for a reason; attach relevant evidence there.

## Public record
- Merged pull request [#8100](https://github.com/HandBrake/HandBrake/pull/8100), merged 2026-09-16, added an option so the x264 encoder writes the AVC frame-packing SEI from the input layout.
- The review in that pull request asked for the normal project evidence: the tested platform declaration and the log output.
