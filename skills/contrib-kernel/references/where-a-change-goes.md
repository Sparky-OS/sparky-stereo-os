# Where a kernel change goes in the cycle: the rules and their documents

**For** a person or an assistant about to send a kernel series or pull request: each rule about the merge window, the -rc weeks and the fixes and next branches, with the document and section it comes from, and where the documents say nothing.

Read on 2026-11-25 in the 7.4-rc2 tree (`7475ea8b58616b33c04afb976cf0fbaad9dd63fb`), and checked against mainline at `4dce97c6c265`: the only change there is a new `maintainer-kvm-arm64.rst`.
Every quoted phrase was found in its file by a script before this page was written; read them again in the tree you send to.

## The cycle

| Rule | Document | Section |
| --- | --- | --- |
| The bulk of a cycle's changes, and all the major ones, are merged in the merge window of about two weeks; they "have been collected, tested, and staged ahead of time" | `Documentation/process/2.Process.rst` | The big picture |
| -rc1 "is the signal that the time to merge new features has passed"; a feature that missed the window waits for the next cycle | `2.Process.rst` | The big picture |
| After -rc1 "only patches which fix problems should be submitted to the mainline" | `2.Process.rst` | The big picture |
| "Most of the patches at this point should fix a regression. Bugs that have always existed are not regressions, so only push these kinds of fixes if they are important." | `Documentation/process/howto.rst` | Mainline tree |
| "all patches merged during a given merge window should really have found their way into linux-next some time before the merge window opens" | `2.Process.rst` | Next trees |
| Most patches "need to be settled in soaking in linux-next in advance of the merge window opening"; after a profile's dates a change targets "the NEXT+1 merge window" | `Documentation/maintainer/maintainer-entry-profile.rst` | Key Cycle Dates |
| Find where the cycle stands from the newest tag in Linus's tree; a release tag without -rcN means "we are most likely in a merge window" | `Documentation/process/maintainer-netdev.rst` | Development cycle |
| A pull request with "new stuff after the merge window (or even bug-fixes, but ones that look scary)" explains "the _timing_" | `Documentation/maintainer/pull-requests.rst` | the quoted mail from Linus |
| A series reparented shortly before a pull request is "A frequent cause of merge-window trouble" | `Documentation/maintainer/rebasing-and-merging.rst` | Rebasing |
| Each logical change in its own patch | `Documentation/process/submitting-patches.rst` | Separate your changes |
| Give the base of the series with `git format-patch --base` | `submitting-patches.rst` | Providing base tree information |

## Regressions

| Rule | Document | Section |
| --- | --- | --- |
| A regression: an application or use case that ran fine with one kernel works worse or not at all with a newer one | `Documentation/admin-guide/reporting-regressions.rst` | What is a "regression" and what is the "no regressions" rule? |
| "Do not consider regressions from the current cycle as something that can wait till the end of the cycle" | `Documentation/process/handling-regressions.rst` | Expectations and best practices for fixing regressions |
| "strongly discouraged to delay mainlining regression fixes till the next merge window, except when the fix is extraordinarily risky or when the culprit was mainlined more than a year ago" | `handling-regressions.rst` | same |
| "Always consider reverting the culprit" | `handling-regressions.rst` | same, "On procedure" |
| A risky fix "just days before a new mainline release": ask Linus, who "can make the call" | `handling-regressions.rst` | same, "On procedure" |

## Stable

| Rule | Document | Section |
| --- | --- | --- |
| A stable patch "or an equivalent fix must already exist in Linux mainline"; the tag goes on the patch submitted for mainline | `Documentation/process/stable-kernel-rules.rst` | opening rules; Option 1 |
| A stable tag ending in `# after -rc3` delays the pick-up | `stable-kernel-rules.rst` | Option 1 |

So a fix for an old bug merged in the next merge window still reaches the stable trees, through its tag, once it is in mainline.

## The subsystems' own words

| Subsystem | Rule | Document | Section |
| --- | --- | --- | --- |
| KVM x86 | "fixes do not automatically warrant inclusion in the current release ... typically only fixes for bugs that are urgent, critical, and/or were introduced in the current release should target the current release"; everything else on `kvm-x86/next` | `Documentation/process/maintainer-kvm-x86.rst` | Base Tree/Branch |
| KVM x86 | fixes for the current cycle go to the main KVM tree, development for the next through the KVM x86 tree; soft close around rc5 for features, rc6 for fixes for the next release | `maintainer-kvm-x86.rst` | Trees; Lifecycle |
| netdev | `net` "is for fixes to existing code already in the mainline tree", `net-next` "is where the new code goes"; after -rc1 "only fixes to the rc1 content are expected"; nothing new to netdev while `net-next` is closed | `maintainer-netdev.rst` | Development cycle; git trees and patch flow |
| netdev | name the tree in the subject: `[PATCH net]` or `[PATCH net-next]` | `maintainer-netdev.rst` | Indicating target tree |
| tip | trees closed to all but urgent fixes in the merge window; "Large series should be submitted in mergeable state *at* *least* a week before the merge window opens"; `_urgent_` branches go in during stabilization | `Documentation/process/maintainer-tip.rst` | Merge window |
| SoC | send only small branches as the merge window gets closer; pull requests for bug fixes for the current release at any time | `Documentation/process/maintainer-soc.rst` | Branches and Pull Requests |
| DRM | feature work in linux-next by -rc6, in drm-next by -rc7; a blackout of about a month after; a -next tree that stays open | `Documentation/gpu/introduction.rst` | Feature Merge Deadlines |
| KVM arm64 (mainline after 7.4-rc2) | `next` for the next merge window, `fixes` for the release in its -rc phase; "the maintainers may defer a low-priority fix to the next merge window" | `Documentation/process/maintainer-kvm-arm64.rst` | Branches; Key Cycle Dates |

## Where the documents say nothing

- Where new tests go: only Linus's mail of 2026-11-24 says new test cases belong on a separate branch merged in the merge window.
- How large a change sent during the -rc weeks may be, and that lines not built by default or fixes for other bugs still add risk: only the same mail ("If you think that "41197 insertions" is ok and cannot introduce new problems just because most of it won't be compiled or becasue they were fixes for other things, you are full of crap.").
- That a fix for a subtle, long-standing bug can itself be buggy: only the same mail ("the fixes by definition are fixing something subtle and rare that nobody has noticed until now. And that makes the *fixes* possibly buggy.").
- `2.Process.rst`'s "only patches which fix problems" can be read as "any fix goes in -rc"; `howto.rst` and the KVM x86 profile say it is not so.
