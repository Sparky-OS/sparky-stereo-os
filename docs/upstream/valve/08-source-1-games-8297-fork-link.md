The in-game version is now on my fork of the SDK, as work in progress: https://github.com/danielcamposramos/source-sdk-2013/tree/stereo3d-sbs-native/src/sourcevr_display I am preparing it as a pull request to ValveSoftware/source-sdk-2013, one commit per fix.

**What it adds.**
A 3D section in the game's own options (GamepadUI, Video): Stereo 3D, 3D format, 3D output, Swap eyes, applied together on Apply with one reload.
Natively: half top and bottom (recommended) and half side by side, for 3D displays.
Through gamescope: the same formats as red/cyan anaglyph (CRT and modern screens), row-interleaved and checkerboard, switched from the menu with no relaunch.
The module is its own project (`src/sourcevr_display`), and the client finds it through a new additive interface (`SourceVirtualRealityDisplay001`, asked through the existing `QueryInterface`), so `SourceVirtualReality001` does not change.

**The six items, in code.**
1. The `sourcevr_<game>.cfg` exec does run in the SDK's client (seen on Half-Life 2: Deathmatch); it is Half-Life 2's shipped build that skips it, so the module still applies those settings.
2. Engine side, unchanged: the module creates its own render targets.
3. The module precaches its own HUD material. In an A/B on Valve's shipped client, the in-world HUD panel did not show the checkerboard, so I could not reproduce source-sdk-2013#268 today, and the client change I suggested there is not in the fork. 4 and 6. With a display module, the client lays the UI out at the window's size instead of 640x480: the crosshair is centred and the cursor stays on the menus.
5. `FormatViewModelAttachment()` skips the rescale for a display module, so the muzzle flash sits on the gun; `viewmodel_fov` stays a cheat. Also: the HUD overlay is allowed on displays, and the client no longer resets a video mode it did not change.

**Where it fails today.**
The README lists it plainly: the full-resolution formats inside gamescope (being fixed on the branch `stereo3d-full-res-wip`), frame packing (needs HDMI 3D modes the driver does not offer), native rows and checkerboard and the spectator mode (not built yet), and the OpenGL renderer (crashes in VR mode).
Half-Life 2's client is 32-bit and cannot be rebuilt from this SDK, so the client changes reach it only when Valve ships them; until then the module sizes the UI itself, and the muzzle flash needs `viewmodel_fov 90` with cheats.
The README also has the build, install and launch steps, including a 32-bit build script for Half-Life 2.
