# AI provenance: every model that worked on Sparky Stereo OS

**For anyone who wants to check how AI was used here:** every model that worked on Sparky Stereo OS, by lab, with where it ran and what it did.
Sparky Stereo OS is directed and verified by Daniel Ramos.
AI partners from several labs did the legwork under that direction: code, packaging, tests, research and drafts.
Every one of them was key to the edition existing, and all of their use has been paid by Daniel personally; there is no sponsor so far.

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

## Before this edition: the earlier chain

| Lab | Models and tools | Where they ran | What they did | When | Commits naming them |
|---|---|---|---|---|---|
| **OpenAI** | ChatGPT | ChatGPT | Daniel's first AI | Late 2024 | n/a |
| **OpenAI / GitHub** | GitHub Copilot and Codex; GPT-5.1 | Copilot, Codex, GPT in the browser | PTX kernels and the ternary system in Knowledge3D; architecture advice, research and code checks | 2025-10-16 to 2025-11-24 in commits | about 12 (Codex 6, Codex/GPT-5.1 2, GPT-5.1 2, Codex (Implementation Partner) 2) |
| **Anthropic** | Claude Code (VS Code), Claude in the browser; Sonnet 4.5, Opus 4.5, 4.6, 4.7, Sonnet 4.6, Fable 5 (before this edition's models) | Claude Code, claude.ai | Repository work, planning, documents, W3C specifications | 2025-10-04 onward | 220 commits before 2026-07-19 (Knowledge3D 200, pm-kr 11, others 9); more after, counted in the table above |
| **xAI** | Grok | Browser | Fonts, curves, procedural typography, real-time research; opened the first Scaler Wizard chain | 2025-10-04 | 1 (Knowledge3D 11987798) |
| **Zhipu AI** | GLM-4.6 | Browser | Multilingual and cognitive-architecture views | 2025-10-04 | 1 (same commit) |
| **Moonshot AI** | Kimi K2 | Browser | RPN-Graph idea, long-context checks | 2025-10-04 | 1 (same commit) |
| **DeepSeek AI** | DeepSeek-OCR, DeepSeek-R1 | Browser, Ollama | OCR design, thinking tags for honesty training | October 2025 | none naming it |
| **Alibaba Cloud** | Qwen (Max, Coder, VL 30B) | Browser, Ollama | Vector drawing, CAD ideas, embeddings | October 2025 | none |
| **Google** | Gemini, NotebookLM, Jules | Browser; Jules in GitHub | Review and fact-checking; research space and audio; ms-swift integration (Scaler Wizard, AI-RLWHF) | Jules 2025-08-12 to 2026-04-01 | Jules authored 25 commits (see note), no trailers |
| **Perplexity AI** | Perplexity | Browser | Sourced research | not recorded | n/a |
| **Manus** | Manus.im | Browser | Second views on design | not recorded | n/a |
| **Mistral AI** | Mistral Large 3 (675B cloud) | Ollama's cloud | Model-diversity experiment (blind baseline, cumulative chain) | 2026-07-17 | n/a |
| **NVIDIA** | Nemotron | Ollama's cloud, in Daniel's own multi-model tooling | A partner in today's chain with Kimi, Qwen, GLM, DeepSeek and Gemini | 2026 | n/a |

Note on Jules: google-labs-jules[bot] authored 12 commits in Knowledge3D, 3 in AI-RLWHF (2025-10-09) and 10 in Scaler Wizard (2025-10-10, 2026-04-01). Counted with `git log --all --author=jules` on 2026-10-12; the Scaler Wizard figure is from the GitHub API.

## How this was counted

- **Commits:** every commit authored under Daniel's identities since 2026-08-01, in the edition's repositories and our forks, counted by the AI trailer it carries (`Co-Authored-By:` or `Assisted-by:`). Trailer wording varied over time; each form was mapped to its model. Twelve commits name Claude Opus 5 and Kimi K3 together and are counted under Anthropic. Counted on 2026-10-10.
- **Lane logs:** each lane's agent log records the model of every session; models that left no trailers (DeepSeek, Qwen) are counted there.
- **Earlier chain:** counted the same way in Daniel's other repositories on 2026-10-12; browser-only partners leave no commits, so their entry comes from Knowledge3D's ATTRIBUTIONS.md (section 0.4) and the Scaler Wizard chain record (Step1.md).
- **The rule from here on:** every commit names the model that actually ran it, once, in the trailer its project expects. See the [ai-partners skill](../skills/ai-partners/SKILL.md).
