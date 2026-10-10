# AI provenance: every model that worked on Sparky Stereo OS

Sparky Stereo OS is directed and verified by Daniel Ramos.
AI partners from several labs did the legwork under his direction: code, packaging, tests, research and drafts.
Every one of them was key to the edition existing, and all of their use has been paid by Daniel personally; there is no sponsor so far.
This page lists them by lab, with where they ran and what they did, so the record is complete and anyone can check it.

## By lab

| Lab | Models | Where they ran | What they did | Commits naming them |
|---|---|---|---|---|
| **Anthropic** | Claude Opus 5.5, Claude Opus 5 (including its 1M-token context), Claude Opus 4.8, Claude Fable 5.1, Claude Sonnet 5.5 | Claude Code (Anthropic's command-line agent): the coordinating session, Claude lanes and subagents | Coordination, review and integration; kernel builds and Secure Boot signing; KWin, KScreen and Mesa work; packaging and the repository; the proof rigs and the stereo virtual machine; documents, skills and upstream drafts | about 7,580 |
| **OpenAI** | GPT-6.1 Sol, GPT-6 Astra, GPT-6 Luna, GPT reserve, GPT-5.6 Sol | Codex CLI (OpenAI's command-line agent) | Lanes for KWin and Mesa, KFileMetaData and KIO, the photo viewers (Gwenview, digiKam, KPhotoAlbum), KDE's game controller page, the Android stereo device, certificates for Brazil | about 960 |
| **Moonshot AI** | Kimi K3, Kimi K2.7 Code, Kimi K2.6 | Ollama's cloud, through Codex CLI and inside Claude Code | The first partner lanes: Marble, the website, deep colour studies, GIMP, the app center | about 115 |
| **Zhipu AI (Z.ai)** | GLM 5.3, GLM 5.3 Flash, GLM 5.2 | Ollama's cloud, through Codex CLI; GLM 5.3 also ran early main sessions | Lanes for the players, HandBrake, F3D, OpenSCAD, Octave, Netgen, Matplotlib, the wallpaper, locales, time and the Oxygen theme study | about 40 |
| **DeepSeek** | DeepSeek V4 Pro, DeepSeek V4.1 Flash | Ollama's cloud, through Codex CLI | Lane sessions on the GL stereo layer, KIO thumbnails, the KWin declaration, Marble, Octave, OpenSCAD, the players and Variety | recorded in the lane logs (66 sessions) |
| **Alibaba (Qwen)** | Qwen 3.5 397B | Ollama's cloud, through Codex CLI | Lane sessions on the same early work | recorded in the lane logs (2 sessions) |
| **Google** | Gemma 4 | Ollama's cloud, through Daniel's own model gateway | Reading images (screenshots and rendered pages) for sessions whose model had no vision, in September 2026 | none (no code) |

## How this was counted

- **Commits:** every commit authored under Daniel's identities since 2026-08-01, in the edition's repositories and our forks, counted by the AI trailer it carries (`Co-Authored-By:` or `Assisted-by:`). Trailer wording varied over time; each form was mapped to its model. Twelve commits name Claude Opus 5 and Kimi K3 together and are counted under Anthropic. Counted on 2026-10-10.
- **Lane logs:** each lane's agent log records the model of every session; models that left no trailers (DeepSeek, Qwen) are counted there.
- **The rule from here on:** every commit names the model that actually ran it, once, in the trailer its project expects. See the [ai-partners skill](../skills/ai-partners/SKILL.md).
