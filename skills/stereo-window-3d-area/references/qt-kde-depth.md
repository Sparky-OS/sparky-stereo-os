# Qt, KDE and depth: choosing the shared layer

Reviewed 2026-10-19 from implementation and the public Qt/KDE material below.
Use this for toolkit, effects or theme work; proposed integrations are not shipped features.

## Three different inputs

| Input | Produce the eye views | Keep coherent |
| --- | --- | --- |
| Stereo photo or video | Decode/unpack the real pair | Eye order, timing, metadata, colour and geometry |
| A 3D scene | Render one scene with coherent per-eye projections | Visibility, lighting, view-dependent history and poses |
| A 2D window or UI plane | Compose shared content twice with depth-dependent horizontal offsets | State, animation time, whole-control content, clipping and logical input |

The third route needs no application 3D engine. It still requires rendering/compositing work; measure its cost.
One shared interface produces two views, rather than two independently running applications.
In the edition's KWin, `WorkspaceScene::paintWindow` computes `StereoDepth::eyeShift`, passes the translation in `WindowPaintData`, and calls the existing effects paint path.
`drawStereoShadow` places a shadow at its receiving plane; ordinary surface content is reused per eye, while stereo surfaces select their actual eye image.
The pair has one frame time. See [desktop depth](../../../docs/depth-on-the-desktop.md) and [the shared representation](../../../docs/how-it-works.md).
Whole-window depth is implemented; a common Theme Editor and toolkit-level control-depth integration remain proposals.

## Shared intent, separate rendering paths

StyleKit describes a shared visual style for Quick and Widgets.
Its QWidget bridge reads QML properties and paints through QPainter; it does not run the Quick scene graph.
Check the selected release and [QStyleKitStyle limitations](https://doc.qt.io/qt-6.12/qstylekitstyle.html#known-limitations) before assuming a custom delegate or shadow works in both.
`Item.z` is sibling stacking order, not a complete binocular-depth contract.
Keep semantic depth separate from shadow blur, colour and stacking; high-contrast or shadowless themes still need coherent meaning.

[Canvas Painter](https://doc.qt.io/qt-6.12/qtcanvaspainter-index.html) provides GPU-oriented imperative 2D painting for Quick, Widgets and QRhi.
That fits coordinated per-eye 2D views; it does not supply this proposed integration automatically.
Do not assume a CPU backend or interchangeable QPainter behavior.
Measure copies, readbacks and damage before promising performance.

A button, its label, icon, focus ring and pressed animation belong to one logical control at its declared plane.
Test both eye bounds, clips, scrolling, overlap, popups and fractional scaling.
Keep hit testing in logical coordinates with an explicit transform; a drawn shift must not make the button unclickable.
Test focus/keyboard/controller activation, ordinary 2D fallback, reduced motion, contrast and text scaling.
The planned Theme Editor would author intent, shared toolkit code would consume it, and KWin would adapt the pair to each output.
Designer freedom does not remove the user's depth and accessibility limits.

## Effects API changes

Xaver Hugl's Vulkan talk motivates keeping semantic state separate from backend-specific drawing.
Before a KWin rebase, identify where the target version owns scene items, effect transforms, per-eye selection, damage and lifetime.
A Vulkan application's two-layer swapchain and KWin's compositor renderer are separate parts of the path.
Keep declarations and output conversion ownership stable while adapting rendering hooks.
Test normal 2D, overlays, resize, damage, direct-scanout eligibility and destruction as appropriate to the change.
The proposed Item effects API is a direction to verify against source, not a stable API promised by our outreach.

## Preview is a development loop, not the final proof

[Qt hot reload](https://www.qt.io/blog/hot-reload-in-qt-6.12) can retain useful application state during edits.
[QML Live Preview MCP](https://www.qt.io/blog/introducing-the-qml-live-preview-mcp-tool-for-agentic-development-of-embedded-devices) connects a running application to that workflow.
Record versions; test edits requiring rebuild, multiple engines/windows and replay limits explicitly.
Capture ordinary 2D and both eyes in a repeatable state; restart cleanly and repeat with installed artifacts.
A hot-reloaded preview can hide startup or initialization defects.
An offscreen QImage readback is useful for regressions, but is not a physical HDR or latency measurement.

## Further public context

- [Union/StyleKit discussion](https://discuss.kde.org/t/real-depth-for-oceans-elevation-a-design-question-for-union/50744/18): our contribution and question, not an acceptance record.
- [Theme design direction](../../../docs/for-theme-designers.md): authoring freedom and the proposed editor.
- [MEIG discussion, 13 October](https://www.w3.org/2026/10/13-me-minutes.html): stereo/HDR discussion, not W3C adoption.

Preserving meaning through presentation connects these topics, but eye layout, UI plane depth and HDR colour metadata each need their own consumer and tests.
