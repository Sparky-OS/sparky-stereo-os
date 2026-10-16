# Skills

**For contributors and the AI assistants they work with:** instructions for working on Sparky Stereo OS and on the programs it changes for stereo 3D and deep colour.
Each folder holds one skill in the open `SKILL.md` format: plain Markdown with a short header, readable by a person and loadable by any assistant that supports skills.

Start with [`sparky-stereo`](sparky-stereo/SKILL.md): the contract, what counts as proof, and how to work with upstream projects.
It ends with the list of the skills for each kind of work.

The same approach is used for awesome-stereoscopy's [contribution skill](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/ai-skill/SKILL.md).

**On Sparky Stereo OS** the package `sparky-stereo-skills` (in both developer tasks) installs them in `/usr/share/sparky-stereo-os/skills`.
Run `sparky-stereo-skills` as yourself to link them where your AI assistants read skills (Claude Code, Codex, Gemini CLI, OpenCode, GitHub Copilot, Cursor, goose, Cline), or `sparky-stereo-skills export skills.zip` for Open WebUI.
