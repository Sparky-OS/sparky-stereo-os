# Works in stereo out of the box

**Open a program that already knows how to draw in stereo, turn its stereo on, and you see it in 3D on whatever screen you have.**
No driver to install, no special graphics card, no settings for your screen: the desktop turns the program's two pictures into what your screen needs.

## What works

| Program | Turn it on | What you get |
|---|---|---|
| [Blender](https://www.blender.org/) | Output properties, Stereoscopy | The whole window, viewport and panels, in both eyes; the display mode is Time Sequential, the one our build has |
| [OpenSceneGraph](https://openscenegraph.github.io/) viewers (`osgviewer`) | `--stereo QUAD_BUFFER` | Any model you open, in both eyes |
| The Mesa demos' `glxgears` | `-stereo` | The gears in both eyes, a quick way to see that your set-up shows 3D |

Each one draws what its authors call quad-buffer stereo, a left picture and a right picture of the same scene.
OpenSceneGraph's viewers and `glxgears` needed no change for this: Debian's own builds of them show the same pictures.
Blender's own stereo menu keeps its single mode here because the desktop gives every screen its format.

## On your screen

- **A 3D television or projector:** the desktop sends it the 3D mode its EDID declares, side by side, top and bottom or frame packing.
- **A VR headset:** the two pictures go to the headset as its two eyes.
- **A glasses-free 3D display or a lens monitor:** the desktop interleaves the two pictures for the panel.
- **Any ordinary monitor with red-cyan glasses:** pick anaglyph in Display Settings and the same program shows in 3D with no change.
- **A plain 2D monitor, no glasses:** you see the left picture, and the program looks as it does everywhere else.

If your glasses or screen show the eyes reversed, Display Settings has one swap for the output, so no program needs its own.

## How it was checked

Each program was run on both graphics cards of the test machine (an AMD Radeon and an NVIDIA GeForce RTX 3060) in an isolated copy of the desktop, and the picture the desktop hands to each eye was captured and compared:

- the left and right pictures differ in the 3D area and are identical everywhere else;
- the nearer object shifts one way and the farther object the other, as the scene's depth predicts, and reading the eyes the other way round fails the check;
- the same program with stereo off gives one picture and nothing is declared.

The details, the commands and the traps are in the [native Linux skill](../skills/native-linux/references/quad-buffer-programs.md).

## What comes next

Programs that draw stereo through the same door are welcome here, and [awesome-stereoscopy](https://github.com/danielcamposramos/awesome-stereoscopy) keeps the list of what we know.
Tell us the one you use.
