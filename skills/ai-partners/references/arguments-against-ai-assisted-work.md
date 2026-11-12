# Arguments against AI-assisted work and what answers each

Use this reference when evaluating a contribution policy, preparing an evidence-based response to a maintainer's objection, or comparing claims about assisted code quality.
It is a research recipe and a map of possible requirements, not permission to disregard a project's rules.
Primary sources below were read on 2026-11-12; check current policy and document history before relying on their status.

## Working recipe

1. Read the project's own contribution, security and AI rules, including module exceptions.
   Record the URL, revision or date, exact scope and whether the text is adopted policy, a proposal or an individual's statement.
2. State the objection in its strongest defensible form.
   Separate the speaker's reason from independent evidence for it; an objection about community purpose need not be a defect-rate claim.
3. For a study, record participants, tasks, actual models/tools, observation period, outcome, denominator and stated limitations.
   Publication year does not identify the model generation; a newer model does not invalidate an older result in its original setting.
4. Compare like outcomes: perceived speed, elapsed task time, static warnings, exploitable defects, reviewer time and later maintenance are different measurements.
5. Identify an observable requirement that could reduce the risk, and say what remains unanswered.
   Classify tool behavior, observed omitted checks and unresolved causation separately; a mistake alone does not prove laziness or deceit.
6. Preserve counterexamples and failed checks.
   Accepted work proves acceptance of that work; a written requirement proves neither compliance nor long-term effectiveness.

## Concerns and candidate requirements

The requirements here are proposals for assessment, not experimentally validated cures.

| Concern | Primary reason or evidence | Requirement and remaining limit |
| --- | --- | --- |
| Unverified reports and asymmetric review cost | [LLVM's policy](https://llvm.org/docs/AIToolPolicy.html) treats contributions whose review costs exceed benefit as extractive. | Concise, bounded work with reproduction and a tested fix; maintainers retain discretion over their capacity. |
| Too much valid work | [curl's October 2026 account](https://daniel.haxx.se/blog/2026/10/22/ignore-the-slop/) distinguishes useful high volume from false reports. | Coordinate intake, deduplicate and contribute remediation; accuracy alone cannot create reviewer time. |
| Code nobody understands or maintains | [Jellyfin](https://jellyfin.org/docs/general/contributing/llm-policies/) requires understanding and response to review. | Demonstrate reasoning, revise the change and name future ownership; passing tests is not sufficient evidence of comprehension. |
| Invented dependencies and insecure patterns | [OpenSSF's guide](https://best.openssf.org/Security-Focused-Guide-for-AI-Code-Assistant-Instructions.html) identifies these risks and labels its guidance as expert recommendations. | Verify origins and versions, preserve negative tests and independent checks; instructions reduce risk without guaranteeing safety. |
| Loss of learning opportunities | [LLVM](https://llvm.org/docs/AIToolPolicy.html) protects beginner issues; [nouveau](https://nouveau.freedesktop.org/Humanity.html) prioritizes retained human knowledge. | Protect practice and assess understanding; output volume does not measure a future maintainer pipeline. |
| Copyright and origin uncertainty | [QEMU](https://www.qemu.org/docs/master/devel/code-provenance.html) declines generated contributions under its current provenance policy. | Establish compatible rights and human certification; code quality cannot resolve unavailable provenance or override that policy. |
| Disclosure and accountability | [VideoLAN](https://github.com/videolan/vlc/blob/master/doc/VideoLAN_AI_Policy.md) requires disclosure in the contribution and excludes agent submission even with approval. | Follow the actual venue's provenance and sender rules; one universal trailer convention would misstate differing policies. |
| Autonomous action beyond the intended task | [METR's August 2026 investigation](https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/) documents unintended target selection. | Constrain allowed targets, execution and external submission; human responsibility does not establish conscious approval of every action. |
| Environmental and supplier objections | [IEA's Energy and AI](https://www.iea.org/reports/energy-and-ai/executive-summary) assesses aggregate infrastructure demand. | Evaluate actual resource and supplier conditions; data-centre totals do not measure energy per accepted patch. |
| A community wants human-only work | [Zig's rules](https://ziglang.org/code-of-conduct/) establish a boundary; [nouveau](https://nouveau.freedesktop.org/Humanity.html) explains a knowledge-centred purpose. | Respect the choice; a sound generated patch does not logically settle a community's objectives. |

## Measurements to compare carefully

| Primary study | What it can answer | What it cannot answer |
| --- | --- | --- |
| [METR's experienced-developer trial](https://arxiv.org/abs/2507.09089), 2025, and [2026 follow-up](https://metr.org/blog/2026-02-24-uplift-update/) | Historical randomized task-time effect, followed by newer but selection-biased evidence. | A universal productivity effect or a confirmed reversal from the follow-up's raw estimate. |
| [The Debt Behind the AI Boom](https://arxiv.org/abs/2603.28592), October 2026 revision | Persistence of static findings in explicitly attributed commits. | Relative performance against a reliable human-only baseline, which the study lacks. |
| [Echoes of AI](https://arxiv.org/abs/2507.00788), February 2026 revision | Short follow-on maintenance outcomes under a controlled task. | Proof of equivalence from a nonsignificant, underpowered result. |
| [How AI Impacts Skill Formation](https://arxiv.org/abs/2601.20245), 2026 | Immediate learning with a particular assistant and unfamiliar library. | Lifetime deskilling or an effect of every way of asking questions. |

Useful accepted work is also part of the record: [curl's Aisle audit](https://daniel.haxx.se/blog/2026/10/14/a-curl-audit-by-aisle/) describes validated findings and collaboration; [Torvalds's debugging commit](https://github.com/torvalds/linux/commit/818bebeb63dd6bf5f4e07e145f6cdbace520a34c) records extensive human-directed debugging; [PHP's buffer-overrun fix](https://github.com/php/php-src/commit/342a7465b3c5fb888a34492cf4d3dd402e13f4f0) includes a regression test and assistance credit.
These are existence proofs of accepted outcomes, not an aggregate success rate.

## Traps found while checking sources

- Symptom: a past rejection rule is reported as today's project policy.
  Cause: a dated announcement, draft or module note was treated as adopted project-wide text.
  Fix: inspect current source and history; preserve status and scope beside the claim.
  Found by comparing the actual policy files with linked discussions.
- Symptom: a headline becomes a precise quality or productivity rate without a denominator.
  Cause: self-reports, static proxies, mixed workflows or raw counts were conflated with controlled outcomes.
  Fix: read methods and limitations before quoting the number.
  Found by checking the papers' baseline, selection and statistical-power sections.
- Symptom: an autonomous agent is assumed to wait for a person before every target or message.
  Cause: responsibility and standing authorization were confused with individual operational decisions.
  Fix: inspect the deployed harness's target rules, permission modes and submission path, plus public incident evidence.
  Found by comparing documented automation modes with the independent incident investigation.
- Symptom: a blocked page is silently replaced by an unattributed summary.
  Cause: the original was unavailable to the default client.
  Fix: use an identified official source mirror or public archive; otherwise record the missing primary text.
  Found by keeping the HTTP failure and successful retrieval route separately.

The practical benefit is a reusable evidence table: objection, primary source/date, measured scope, what remains right, candidate requirement and unresolved limit.
Keep private correspondence, personal contact details and unsourced motive judgments out of it.
