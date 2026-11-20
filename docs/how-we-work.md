# How we work here

**For people who build Sparky Stereo OS, and for the AI partners who help them:** the decisions behind every package, each with the skill that carries its recipe.
These are settled. A change that goes against one of them starts with a conversation, not with a patch.

- **One system, one copy of each library.** A program the edition ships links the edition's own libraries: its FFmpeg, its Mesa, its Qt. A program that brings private copies is rebuilt to use ours, and what its makers patched in their copy is imported into our library with their credit, so every program gains it. When a program's own build cannot do that, we keep a stereo fork of it. Skill: [edition-packaging](../skills/edition-packaging/SKILL.md).
- **Fix the engine, not each program.** A fault that many programs meet is fixed where it lives: the kernel, Mesa, Stereo KWin, the stereo layer. A program gets a patch only for what is its own. Skills: [sparky-stereo](../skills/sparky-stereo/SKILL.md), [native-linux](../skills/native-linux/SKILL.md).
- **One format inside.** Every source hands Stereo KWin full side by side, left eye first, at any resolution, and KWin turns it into what each screen needs. Programs decode any input and offer no output formats. Skill: [sparky-stereo](../skills/sparky-stereo/SKILL.md).
- **One depth setting, in one place.** The person sets the depth limits once, for the screen. No program rescales them by a window, a picture or an icon. Skill: native-linux, [One separation, one place](../skills/native-linux/references/one-separation-one-place.md).
- **Search upstream first, and carry their commit.** Before any fix we read the default branch, the merge requests, the issues and our own published patches. A fix that exists is carried with its author's name. Skill: [search-upstream-first](../skills/search-upstream-first/SKILL.md).
- **Our forks ship.** Work is pushed to our fork the same day and published from it. What upstream accepts retires our patch. Skill: [forks-and-online](../skills/forks-and-online/SKILL.md).
- **Decided defaults, nothing removed.** The system works out of the box. Where two paths give a person different results, both are options with one default. No capability is removed to make a default work. Skill: [kde-desktop-defaults](../skills/kde-desktop-defaults/SKILL.md).
- **It works, or the person is told.** Nothing falls back in silence. Skill: [sparky-stereo](../skills/sparky-stereo/SKILL.md).
- **Proof before words.** A failing run before the fix and a passing one after, both eyes captured, a 2D control, numbers against a prediction. A rebuilt package is compared file by file with the one it replaces, and a reviewer runs it again. Skills: [stereo-proof-rig](../skills/stereo-proof-rig/SKILL.md), [edition-packaging](../skills/edition-packaging/SKILL.md).
- **The test machine first.** Every update goes onto the old test laptop and through a restart before it reaches a working machine. Skill: [test-bench](../skills/test-bench/SKILL.md).
- **Every language, old hardware.** Each sentence a person can meet exists in the ten languages, and the system runs on a 64-bit machine of ten years ago. Skill: [edition-packaging](../skills/edition-packaging/SKILL.md); page: [the machines it runs on](hardware.md).
- **Skills as we go, credits by name.** Each piece of work leaves its recipe and its traps in a skill, and names the people it builds on. Skill: [making-skills](../skills/making-skills/SKILL.md); page: [ATTRIBUTIONS](../ATTRIBUTIONS.md).
- **Never cold.** A heads-up comes before a merge request, AI assistance is said once, a report carries its fix and its test, one finding at a time. Skill: [upstream-outreach](../skills/upstream-outreach/SKILL.md).
- **People and AI partners, the same rules.** The same instructions and the same checks, and a person answers for every line. Skill: [ai-partners](../skills/ai-partners/SKILL.md); page: [how AI help is credited](ai-provenance.md).

**Where to go next:** [AGENTS.md](../AGENTS.md) to start a task, the [maintainer workflow](maintainer-workflow.md) for one change from source to package, and the [skills index](../skills/README.md) for the recipe.
