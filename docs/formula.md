# From a VR engine to a 3D display: the formula

A game with a VR mode already renders two eyes. A 3D television, projector or monitor can show those two eyes directly, side by side or top and bottom, with no headset. What stands in the way is everything the VR mode does *for a headset*: head tracking, lens distortion, a floating HUD panel, a cursor in a virtual screen. This file lists what has to change, learned by doing it on Half-Life 2 (2026-09-24, `sourcevr/`), whose own VR interface (`ISourceVirtualReality`) made it a good teacher: the structure below is what most VR games share.

Why games at all: "games and animated films use virtual rather than physical cameras and are therefore much easier to convert to 3D" (Linus Tech Tips, [*Was 3D TV actually poo?*, 2022, 19:02](https://www.youtube.com/watch?v=Dbjb2spwQVg&t=1142s)). An engine holds the scene as geometry, so the second eye is a second camera, not a guess.

wiz3D solves a different problem, stereo for games that never had a VR mode (a DirectX proxy; in iZ3D's tradition it renders each draw twice). Our work on it brings it to the same design as this formula: it takes the camera the game hands the API and renders that camera's view for each eye, keeping the per-draw shift inside as the fallback for draws that show no camera. This formula is for games that already have a VR mode.

## 1. The eyes: a window, not a headset

- **Projection.** Each eye gets an off-axis frustum: the two frustums share one window at the convergence distance (zero parallax, the screen plane), and each eye sits half the separation to its side. A headset's projection is symmetric per eye and centred on its lens; a display needs the shared window, or everything floats in front of the screen.
- **Field of view** comes from the game (its 2D setting), widened to the displayed aspect the way the game does it for widescreen, not from a lens.
- **Defaults that looked right on a 46-inch set:** separation 2.5 game units (about 64 mm in Source), screen plane at 120 units.
- **Packing:** each eye into its half of the frame (left eye first, as HDMI 1.4 packs it), the display told by its own 3D mode or by the signal.

## 2. The view: the game drives it, not a head

- Turn head tracking off and let the view follow the game: the mouse in play, the recorded angles in a demo. Half-Life 2 has the mode built in (`vr_moveaim_mode 7`, "HMD orientation is completely ignored"); its default left the view fixed while the demo's player looked around.
- Aim equals view. Anything that separates them (a cursor that moves inside the HUD, a torso that turns separately) is for a headset.

## 3. Composition: eyes into targets, targets into the frame

- Render each eye into its own target and copy it into its half of the frame. Rendering straight into the halves of the frame worked for the scene, but the HUD and the loading screen had nowhere to go.
- Lens distortion is replaced by that copy: nothing to undistort.
- **Engine-specific:** Half-Life 2 never asked the module to create its targets (it only does when VR is set up in its video settings at start), so the module creates them on first use, inside the engine's render-target allocation. A material used for the first time from the engine's render thread without a precache drew as the error texture (the purple-black checkerboard); precaching once fixed it.

## 4. The 2D layer: HUD and menus on the screen plane

- Text off the screen plane costs the viewer a refocus every time they read it: Killzone's subtitles on the PlayStation 3D Display, as Linus Tech Tips found ([2022, 8:52](https://www.youtube.com/watch?v=Dbjb2spwQVg&t=532s)). Keep all 2D at zero parallax.
- A VR mode paints the HUD into a small sheet (640x480 in Half-Life 2) and shows it as a panel floating in the world, sized for a headset. On a display, paste that sheet across the whole screen, **identical in both eyes**: zero parallax, so it sits exactly on the screen plane, where a flat HUD belongs.
- Rearrange for 3D where the 2D layout gets in the way: Half-Life 2's ammo panel sits over the gun, confusing in depth; its row moved to the top, the rest of the sheet shifted down whole (swapping bands cut the weapon selection in two). Messages that fade in and out stay where the game puts them.
- **Menus keep the game's layout.** Moving parts of the sheet while a menu is open moved its buttons away from where the cursor clicks. The engine tells the module when the cursor is visible.

## 5. The crosshair: 2D, centred, identical in both eyes

- A VR mode aims the crosshair through the weapon and projects it into the view. Half-Life 2 does that for a 640x480 screen and paints it into each eye unscaled, so at full eye resolution it lands off-centre.
- Two answers, both kept as modes: render each eye at the size the VR HUD assumes (the engine's own crosshair lands centred; the picture is softer, fine for low-resolution textures), or turn the engine's crosshair off and draw the game's own crosshair art on the 2D layer, once per eye, at the centre (sharp; for high-resolution textures).
- Use art that blends by its **alpha**. An additive crosshair (colour added to what is behind it) looks different in each eye, because the two eyes see different backgrounds; drawn into the transparent HUD sheet it became a black square.

## 6. The weapon and its effects

- Draw the first-person weapon model, not the third-person one a headset mode prefers (Valve's own Half-Life 2 VR setting).
- Effects placed by converting between the weapon's field of view and the world's (the muzzle flash sprite in Source) miss the gun once the weapon is drawn with the eye projection. Making the two fields of view agree puts them back (`viewmodel_fov 90` in Half-Life 2; a cheat-protected setting today).
- Effects that remember past frames keep that memory per eye. Half-Life 2's motion blur keeps one previous view for both eyes, so each eye blurs against the other eye's camera and the mouse movement smears; it is off in 3D until it keeps one per eye.

## 7. Input: one window, two eyes

- The system pointer moves across the whole window, both eyes, while the game's UI is one sheet shown in each eye. Find how the game maps the pointer onto its UI (log both: in Half-Life 2 the UI cursor is window pixels 1:1, and the sheet is the window's top-left 640x480) and confine the pointer to the part of the window the sheet shows.

## 8. Settings: apply on entry, restore on exit

- The per-game VR settings belong to the moment VR starts (Half-Life 2 meant to run `cfg/sourcevr_<game>.cfg`, and this build does not). Settings that also affect 2D play (the crosshair) must be restored when VR stops, and on the next start if the game quit while in VR.

## 9. What stayed the same

Shadows, lighting, level transitions, saves and loads needed nothing: the engine renders each eye itself, so everything it renders is right in both. That is the advantage of a VR engine over a stereo proxy, and why this formula starts from one.
