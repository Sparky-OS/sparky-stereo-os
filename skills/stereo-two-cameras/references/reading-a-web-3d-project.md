# Reading a web 3D project's real state and its stereo path

Use this before a project goes on a list of things a stereo browser can include.
Everything below is read from the project's own repository with read-only API calls (no clone needed), the registry for the published package, and the specification's own source.

## Recipe

1. Metadata: `gh api repos/OWNER/REPO --jq '{license:.license.spdx_id,pushed_at,archived,default_branch}'`.
   GitHub's SPDX field is a hint only: `NOASSERTION` appears for dual licences (X3DOM: MIT or GPL, in `LICENSE.md`), for W3C and Khronos repositories, and for repositories with several licence files.
   Read the licence file itself (`LICENSE*`, `COPYING*`, `LICENSES/`) and note its name.
2. Root listing: `gh api repos/OWNER/REPO/git/trees/BRANCH --jq '.tree[].path'`, then fetch with `curl -s https://raw.githubusercontent.com/OWNER/REPO/BRANCH/FILE`: `LICENSE*`, `CONTRIBUTING*`, `AGENTS.md`, `CLAUDE.md`, `.github/CONTRIBUTING.md`, `.github/pull_request_template.md`, `.github/copilot-instructions.md`, `README.md`.
3. AI position: grep those files for `\b(AI|LLM|copilot|claude|generative|Assisted-by)\b`, then read the section, not the hit.
   Three kinds exist and mean different things: a ban (Overte: "Contributions, issues and code reviews generated using Large Language Models are not allowed"), a disclosure or ownership clause (Khronos glTF and X_ITE "AI-Assisted Contributions", CesiumJS "AI acknowledgment" in the pull request template, Godot), and instructions written for agents that say nothing about contributors (PlayCanvas and WebSpatial `AGENTS.md`, Babylon.js `copilot-instructions.md`).
   Nothing found is recorded as "nothing found in these files", never as permission.
4. Published package: `curl -s https://registry.npmjs.org/PKG/latest | jq '{version,license,repository}'`; a `null` licence field and no licence file in the repository means the project cannot be built and shipped by us until its owner says what the licence is (Needle Engine, 2026-11-08).
5. Stereo path, in this order: does the code ask for a WebXR session (`src/**/webxr*`, `xr-manager`, `VRButton`); does it draw its own stereo outputs (three.js `examples/jsm/effects/AnaglyphEffect.js`, `StereoEffect.js`, `ParallaxBarrierEffect.js`, Babylon.js `Cameras/Stereoscopic/*`: these are the engine's own output modes and are not used in our build, only the camera maths is of interest); does it have a field for eye separation or a zero-parallax plane (three.js `StereoCamera.eyeSep` 0.064 and `focus`, Babylon.js `interaxialDistance`, X3DOM `interpupillaryDistance`, ANARI `interpupillaryDistance`, OpenUSD `UsdGeomCamera.stereoRole` mono|left|right with no separation field).
   WebXR itself: `XRView.eye` is `left`, `right` or `none`; an `inline` session gets two primary views only with the `inline-stereo` feature (WebXR Device API, session modes and feature descriptors).
   Then measure with the rig in `x3d-in-the-browser.md`: reading the code says what a project could do, only the capture says what it does.
6. Can a native program go inside: check that the browser has a mechanism at all before designing one. In the waterfox fork, `dom/plugins` holds only tests (no ipc or base code: the plugin interface is gone), so a tab cannot host a native window; what exists is a browser-owned surface with its own stereo declaration (`gfx/layers/NativeLayerWayland.*`).

## Traps

- Symptom: a GitHub code search for a word returns nothing for a project that surely has it. Cause: code search is a lagging, partial index. Fix: list the tree and fetch the file, or say "search found nothing" and do not write "absent".
- Symptom: a package ships a licence text nobody mentions (X_ITE `LICENSES/CC-BY-NC-4.0.txt`). Cause: the REUSE tool's bulk download (commit d11206a25, "Added more licenses.", 2026-08-02) put every licence text it knows in the folder; the only sidecars naming a non-commercial licence cover two HDR images in `docs/`, which the npm package does not contain. Fix: list every file that names the licence (`.license` sidecars, `REUSE.toml`, SPDX headers) before calling it a blocker; a text without a file that names it covers nothing.
- Symptom: GitHub says MIT, the README says something else. Cause: README, headers and LICENSE disagree (Halogen). Fix: take the LICENSE file, record the disagreement, ask the author before a pull request.
- Symptom: a spec repository has no licence file for its text. Fix: read the text's own licence page (3D Tiles `specification/LICENSE.adoc`: CC BY 4.0; AOUSD `specifications-public` `LICENSE`: CC BY-ND 4.0, so the text is not modified, implementing it is not restricted by it). A Khronos extension README header and the repository `COPYING.adoc` can differ (KHR_gaussian_splatting says CC-BY-4.0, COPYING says KHR extensions carry the Khronos specification copyright): record both.
- Symptom: a viewer is "open source" but not shippable. Cause: the licence is source-available (Needle `usd-viewer`: PolyForm Noncommercial 1.0.0). Fix: record "not ownable" and look for the upstream engine it wraps (OpenUSD itself builds for wasm32).
- Symptom: a contribution rule that needs an outside system (WebSpatial: a `ticket:` trailer with a Meego work item on every commit). Fix: record it as a barrier to contributing, not to using.
