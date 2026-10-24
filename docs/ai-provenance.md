# AI provenance: the partners in Sparky Stereo OS

**For anyone who wants to know how AI was used here:** which partners took part, from which lab, where they ran and what part of the work they carried.
Sparky Stereo OS is conceived, directed and verified by Daniel Ramos.
It is collective intelligence work, as Daniel's chain-written manifesto ["Information is Power, Shared"](https://github.com/danielcamposramos/Knowledge3D/blob/main/docs/SCIENTIFIC_MANIFESTO_COLLECTIVE_INTELLIGENCE_CHAIN.md) (Knowledge3D, 2025) sets out: partners from several labs worked with him and with each other, each one reading, checking and extending what the others did.
In Knowledge3D's terms the partners are Synthetic Users, and the technique carries that name; today it is prompt and context engineering, the briefs and skills each partner reads before it works.
All of their use has been paid by Daniel personally; there is no sponsor so far.

## Why there are no counts here

A commit records who wrote into the repository at that moment, not who made the work.
A GPT lane's finding lands in a Claude commit, a GLM review reshapes a Kimi plan, and Daniel's call decides between them.
So this page does not measure partners by commits or by lines.
It says who took part and in which roles, the way a scientific paper's contribution statement does, where nobody marks which line came from which researcher.
The roles are the 14 of CRediT, the [Contributor Roles Taxonomy](https://credit.niso.org/) (ANSI/NISO Z39.104-2022), which journals use for this.

## Contributions

| Contributor | Roles (CRediT) |
|---|---|
| **Daniel Ramos** | Conceptualization, Methodology (the MVCIC chain, the Synthetic User technique), Supervision, Project administration, Validation, Resources (the machines, the 3D televisions, the test media), Funding acquisition (he pays every partner himself), Writing (review and editing) |
| **Anthropic, Claude** | Software, Investigation, Validation, Formal analysis, Data curation, Project administration (coordinating the lanes under Daniel), Writing (original draft) |
| **OpenAI, GPT** | Software, Investigation, Validation, Visualization, Writing (original draft) |
| **Moonshot AI, Kimi** | Software, Investigation |
| **Zhipu AI, GLM** | Software, Investigation |
| **DeepSeek** | Software, Investigation |
| **Alibaba, Qwen** | Software, Investigation |
| **Google, Gemma, Gemini and NotebookLM** | Validation (reading screenshots and rendered pages for sessions without vision), Investigation (the research space), Visualization (the architecture infographic) |

## The partners, by lab

| Lab | Models | Where they ran | What they did |
|---|---|---|---|
| **Anthropic** | Claude Opus 5.5, Claude Opus 5 (including its 1M-token context), Claude Opus 4.8, Claude Fable 5.1, Claude Sonnet 5.5 | Claude Code (Anthropic's command-line agent): the coordinating session, Claude lanes and subagents | Coordination, review and integration; kernel builds and Secure Boot signing; KWin, KScreen and Mesa work; packaging and the repository; the proof rigs and the stereo virtual machine; documents, skills and upstream drafts |
| **OpenAI** | GPT-6.1 Sol, GPT-6 Astra, GPT-6 Luna, GPT reserve, GPT-5.6 Sol | Codex CLI (OpenAI's command-line agent) | Lanes for KWin and Mesa, KFileMetaData and KIO, the photo viewers (Gwenview, digiKam, KPhotoAlbum), FFmpeg, KDE's game controller page, the Android stereo device, certificates for Brazil; editing and fact-checking the architecture infographic |
| **Moonshot AI** | Kimi K3, Kimi K2.7 Code, Kimi K2.6 | Ollama's cloud, through Codex CLI and inside Claude Code | The first partner lanes: Marble, the website, deep colour studies, GIMP, the app center |
| **Zhipu AI (Z.ai)** | GLM 5.3, GLM 5.3 Flash, GLM 5.2 | Ollama's cloud, through Codex CLI; GLM 5.3 also ran early main sessions | Lanes for the players, HandBrake, F3D, OpenSCAD, Octave, Netgen, Matplotlib, the wallpaper, locales, time and the Oxygen theme study |
| **DeepSeek** | DeepSeek V4 Pro, DeepSeek V4.1 Flash | Ollama's cloud, through Codex CLI | Lane sessions on the GL stereo layer, KIO thumbnails, the KWin declaration, Marble, Octave, OpenSCAD, the players and Variety |
| **Alibaba (Qwen)** | Qwen 3.5 397B | Ollama's cloud, through Codex CLI | Lane sessions on the same early work |
| **Google** | Gemma 4; Gemini and NotebookLM | Ollama's cloud, through Daniel's own model gateway; the browser | Reading images (screenshots and rendered pages) for sessions whose model had no vision, from September 2026; the architecture research and the original infographic, October 2026 |

## Before this edition: the earlier chain

| Lab | Models and tools | Where they ran | What they did | When |
|---|---|---|---|---|
| **OpenAI** | ChatGPT | ChatGPT | Daniel's first AI | Late 2024 |
| **OpenAI / GitHub** | GitHub Copilot and Codex; GPT-5.1 | Copilot, Codex, GPT in the browser | PTX kernels and the ternary system in Knowledge3D; architecture advice, research and code checks | October and November 2025 |
| **Anthropic** | Claude Code (VS Code), Claude in the browser; Sonnet 4.5, Opus 4.5, 4.6, 4.7, Sonnet 4.6, Fable 5 (before this edition's models) | Claude Code, claude.ai | Repository work, planning, documents, W3C specifications | From October 2025 |
| **xAI** | Grok | Browser | Fonts, curves, procedural typography, real-time research; opened the first Scaler Wizard chain | October 2025 |
| **Zhipu AI** | GLM-4.6 | Browser | Multilingual and cognitive-architecture views | October 2025 |
| **Moonshot AI** | Kimi K2 | Browser | RPN-Graph idea, long-context checks | October 2025 |
| **DeepSeek AI** | DeepSeek-OCR, DeepSeek-R1 | Browser, Ollama | OCR design, thinking tags for honesty training | October 2025 |
| **Alibaba Cloud** | Qwen (Max, Coder, VL 30B) | Browser, Ollama | Vector drawing, CAD ideas, embeddings | October 2025 |
| **Google** | Gemini, NotebookLM, Jules | Browser; Jules in GitHub | Review and fact-checking; the research space and its audio overviews; Jules wrote the ms-swift integration (Scaler Wizard, AI-RLWHF) | From August 2025 |
| **Perplexity AI** | Perplexity | Browser | Sourced research | not recorded |
| **Manus** | Manus.im | Browser | Second views on design | not recorded |
| **Mistral AI** | Mistral Large 3 (675B cloud) | Ollama's cloud | Model-diversity experiment (blind baseline, cumulative chain) | July 2026 |
| **NVIDIA** | Nemotron | Ollama's cloud, in Daniel's own multi-model tooling | A partner in today's chain with Kimi, Qwen, GLM, DeepSeek and Gemini | 2026 |

## How this record is kept

- **From records only:** commit trailers, the lane files and session logs, Knowledge3D's ATTRIBUTIONS.md (section 0.4) and the Scaler Wizard chain record (`Multi-Vibe_Coding_Chains/Step1.md`). Partners who worked in the browser leave no commits, so their entries come from those records.
- **A role is listed only where a record shows it.** Anything no record confirms is left out.
- **Disclosure stays at the point of work:** every commit names the model that ran it, once, in the trailer its project expects. That is disclosure, not a score. See the [ai-partners skill](../skills/ai-partners/SKILL.md).
- **The method,** Multi-Vibe Code In Chain (MVCIC), and the chain in the order the partners joined: [ATTRIBUTIONS.md, section 10](../ATTRIBUTIONS.md#10-ai-partners).
