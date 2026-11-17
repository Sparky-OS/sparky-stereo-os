# Draft 04: comment on ValveSoftware/source-sdk-2013 #268 ("VR Support / HUD Broken again?", 2014, open)

Status: **POSTED 2026-09-24 as https://github.com/ValveSoftware/source-sdk-2013/issues/268#issuecomment-5822876523** (approved by Daniel, posted verbatim).
Target: https://github.com/ValveSoftware/source-sdk-2013/issues/268

---

The black and pink checkerbox is the HUD material drawing as the error material, and I think I found why.

With the threaded material system, a material that is first used from the render thread without a precache on the main thread draws as the error pattern, whatever texture it points at.

In current Half-Life 2 I hit the same checkerbox in VR mode, and it stayed even with the texture swapped for the engine's own `_rt_FullFrameFB`.

Holding a reference to the material and calling `CacheUsedMaterials()` once, before its first draw, fixed it (`IsPrecached()` went from 0 to 1).

For the SDK's VR client that would probably mean precaching `vgui/inworldui` and `vgui/inworldui_opaque` when VR activates; I have not built that in the SDK yet.

Details and the rest of the VR-on-a-3D-display work: ValveSoftware/Source-1-Games#8297
