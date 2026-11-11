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
Whole-window depth is implemented, and so is control-level depth for windows styled by Stereo Union; a common Theme Editor remains a proposal.

## Control-level depth: the pair contract (built, 23 October 2026)

Stereo Union, Qt and Stereo KWin share four window properties and one protocol object; read [Depth inside every window](../../../docs/depth-inside-windows.md) for the values and their roles.
- Stereo KWin tells a surface whether its elements may show depth now and which of its edges lie on the output's edge (`kde_stereo_depth_v1.depth_state`, version 3 of `kde_stereo_content_v1`); libstereo-declare 1.5 wraps it.
- The style sets the window's `_q_stereo_depth` and each element's `_q_stereo_parallax` (qreal, device pixels, positive when nearer).
- Qt sets `_q_stereo_views` to 2 for the platform, `_q_stereo_pair` while it draws the pair, and `_q_stereo_eye` (1 left, 2 right, 0 between frames); the style moves nothing itself while `_q_stereo_pair` is set.
- Each element moves by `eyeShift(p) - eyeShift(p_ref)`, `p_ref` being its nearest ancestor with a parallax or the window; the right eye takes `-trunc(p/2)` and the left the rest, as `StereoDepth::eyeShift()` splits it. A deeper element is clipped to its 2D rectangle. Only matrices and clip nodes change; geometry and input stay 2D.
- The pair is marked `set_desktop_depth`, so Stereo KWin draws it per eye but does not count it as stereo content.
- Built paths: Qt Quick on the OpenGL RHI on Wayland (both render loops, one QRhi frame per eye, the left ended with `SkipPresent`), and Qt Widgets painted on Wayland's shared memory backing store. Still flat, each with its plan in the page above: the Vulkan RHI, the software backend, `QQuickWidget` and `QQuickRenderControl`, client-side decorated windows, X11.
- Proof: element disparity against a prediction worked out from the theme's CSS, at the shipped limits and at `ElementLimit` 12, Debian's Qt Quick as the negative control, 2D output at 0 differing pixels; see [the proof rig](../../stereo-proof-rig/SKILL.md#element-depth-inside-a-window).

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

## How Stereo KWin picks a surface's depth level

The whole rule is in KWin's `src/scene/stereodepth.{h,cpp}`; read `roleOf()` and `level()` before changing a level.

1. `roleOf(window)` gives one role: `Fixed` (full screen, lock screen, panels, the pointer's drag icon), `Desktop`, `Active`, `Popped`, `Sunk`, `Above` or `Below` (the two pinned ones).
   Anything `isPopup()` (menus, tooltips, notifications, on-screen displays, applet popups) is `Popped`, and so is whatever is transient for a window that is not sunk.
2. `level(window)` turns the role into a number from -1 to 1: `Fixed` and `Active` 0, `Desktop` and `Below` -1, `Above` 1, `Sunk` shared out over the sunk range, `Popped` shared out over the popped range.
3. `levelDepth()` multiplies it by the output's own limit (`SunkLimit` or `PoppedLimit` of kwinrc `[StereoDepth]`, built on the display), and `parallax()` is `round(depth * viewWidth / 1920)` device pixels: 10 or 4 px at 1920 wide by default, 3 px at 1280.
4. A popped surface that touches the output's edge is flattened to level 0 (the edge rule), because something in front of the screen cut by the screen's edge breaks the picture.
   Stereo KWin keeps popups 10 logical pixels inside every edge of a 3D output (`PopupBorder`) so the rule never fires for them; it still fires for panels and window content.
5. `Popped` surfaces share the range: the topmost is at the limit and each one below it is `rank / count` of it.
   Notifications and on-screen displays (`isNotification()`, `isCriticalNotification()`, `isOnScreenDisplay()`) are not part of that share and always sit at the limit, the nearest thing on the output; before it, a stack of three notifications had 1, 2 and 3 px, though they never overlap.
   The limit bounds everything except what opens over a window pinned above (point 6).
6. **The pinned stack (Daniel, 2026-11-07: "keep the poped max for pinned, anything inside it stacks even more far from the screen"; kwin +stereo3d46):** a window kept above others (`Role::Above`) stays at the person's `PoppedLimit`.
   What opens over it stacks further out, one step per layer: its menus, sub-menus and popups (transients of the pinned window, found by `mainWindow()`), and a notification or an on-screen display shown over it (`pinnedBase()`: the topmost pinned window below it in the stacking order whose frame it overlaps).
   The layers over one pinned window share one more popped limit (`s_pinnedStackSpan`, 1 limit): layer `rank` of `count`, in stacking order, sits at level `1 + span * rank / count`, so the topmost layer is at two limits and each layer is a step of `span / count` nearer than the one under it, the spacing the popped share had before notifications were put at the limit.
   Depth follows stacking, so a normal notification (stacked under the popups) is a lower layer than an open menu; a critical notification and an on-screen display are stacked over them.
   Numbers at the default limit of 4 px (parallax `round(level * 4 * width / 1920)`): one menu 8 px at 1920 (5 at 1280, pinned 3); a menu and a sub-menu 6 and 8 (4 and 5); a menu, a sub-menu and a critical notification 5, 7, 8 (4, 4, 5), the pinned window staying at 4 (3).
   Nowhere else: menus of an unpinned window still share the range inside the limit, a notification away from the pinned window is at the limit, a pinned window touching the output's edge is at the screen (the edge rule) and what opens over it follows the ordinary rules, a declared place (`kde_stereo_depth_v1.set_place`) is untouched, and 2D outputs change nothing.
   `maxEyeShift()` (damage margins and the pointer's bounds) counts the extra span, or the farthest layer's shifted pixels are never repainted.

To change a level: add the case to `level()`, give `StereoDepth` no new state, and write the test in `autotests/integration/stereo_depth_notifications_test.cpp` style (the pinned stack is `stereo_depth_pinned_stack_test.cpp`, with xdg popups made by `createMenu()`): a 320x240 output with `SunkLimit` 96 and `PoppedLimit` 60 (10 px at 320 wide), surfaces from `Test::createXdgToplevelSurface` plus a `PlasmaShellSurface` with the role and a position, a solid colour each, and the parallax read from ScreenShot2 as the left eye's first x of the colour minus the right eye's.
Cover one surface alone (a control that passes before the change), several surfaces together (the case that shares), the pinned window, the person's own `PoppedLimit`, and a 2D output (nothing moves).

Plasma's own notifications and on-screen displays are `plasmashell` windows with the panel-shell roles Notification, CriticalNotification and OnScreenDisplay at a position it asks for (36 px from the edges for notifications; the OSD low and centred).
Traps met with the pinned stack:

- **A notification over the menus read below them.** Symptom: with a pinned window, a menu, a sub-menu and a notification, the menu read 17 px where 13 was expected. Cause: a normal notification lies in the notification layer, under the popup layer, so it is the first layer in stacking order and the menus are further out; the test had assumed the order it was created in. Found by printing `workspace()->stackingOrder()` positions. Fix: depth follows the stacking order (a critical notification and an on-screen display are over the popups), and the test asserts the order it relies on.
- **A menu jumps when a sub-menu opens.** One layer over a pinned window is at two limits; with a second layer the first falls to 1.5, the second takes two limits. It is the share of old, eased by the 80 ms rise and 150 ms sink; a fixed step (limit / 3) would keep a lone menu still but grow without bound with deeper stacks, so the step is a decision for the maintainers of the design, not a detail of the code.
- **A uniform window gives no disparity to match.** Symptom: block matching on a white Qt window read the same error for every shift. Cause: nothing to match inside the frame. Fix: match the title bar strip where nothing opens over it, and the popups on their own text.
- **A kept test build saves a copy.** The earlier build tree was reused in place: the new test was added to the source with the old code, built and run (red), then the code was changed and everything rebuilt (green), so the old library stayed as `libkwin-sNN.so` for the plasmashell red run and no second build tree was needed on a nearly full disk.

A real plasmashell sees more than a unit test does: several notifications at once (they stack), an on-screen display over a notification, a menu open beside one.
Test those in the proof rig (`stereo-proof-rig`, "Plasma in the rig"), not only one surface at a time.

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
