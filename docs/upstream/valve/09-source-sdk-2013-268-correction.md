A correction to my comment above, after testing it both ways (2026-09-26).
On Valve's shipped Half-Life 2 client, with no precache change, the in-world HUD panel (`vr_hud_never_overlay 1`) drew correctly, so I could not reproduce the checkerboard today, and the client change I suggested is not in my fork.
The checkerboard I saw was my own module's HUD material, which the module now precaches itself.
Details: https://github.com/ValveSoftware/Source-1-Games/issues/8297#issuecomment-5851255833
