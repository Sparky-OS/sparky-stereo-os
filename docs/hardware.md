# The hardware behind it

Sparky Stereo OS is built and tested on two ordinary machines, the ones Daniel already had: a home PC and a 2016 laptop.
There is no workstation graphics card and no special 3D monitor.
The 3D screens are two Sony TVs from 2011 and 2012, and any monitor with red-cyan glasses.

Stereo programs used to need all of that: a workstation graphics card, its vendor's driver and a stereo monitor.
Here the 3D comes from the open software every Linux desktop already runs, the graphics drivers and the desktop itself, so the computer you have is the computer that shows 3D.

## The desktop

Daniel's home PC, where the edition is built and used every day.

| Part | Model |
|---|---|
| Processor | AMD Ryzen 5 5600G, 6 cores, with its own Radeon graphics |
| Graphics | the processor's Radeon graphics, and an NVIDIA GeForce RTX 3060 (12 GB) |
| Board | ASUS TUF Gaming X570-Plus |
| Memory | 96 GB |
| Storage | two NVMe SSDs, SATA SSDs, and hard disks for files |
| 3D screens | Sony BRAVIA KDL-46EX725 (2011) and KDL-46HX855 (2012), both 3D TVs |

The screens run from both graphics chips at once: the processor's own Radeon and the RTX 3060.
The large memory and the many disks are for building the whole system from its source code, again and again: the core, the graphics drivers, the desktop and the video libraries.
Using the desktop needs far less, as the laptop below shows.

## The laptop

Daniel's field machine, an entry-level laptop from 2016.

| Part | Model |
|---|---|
| Laptop | Lenovo ideapad 310-15ABR |
| Processor | AMD A10-9600P, 4 cores (2016), with Radeon R5 graphics |
| Graphics | the processor's Radeon R5, and a small second Radeon (R5 M330 class, 2 GB) |
| Memory | 12 GB, the most it takes |
| Storage | two SATA SSDs, one in the old DVD drive's bay |
| Screens | its own 1366x768 screen, and HDMI out to the KDL-46HX855 3D TV, on the TV's second input |

It runs the same edition, installed from the same packages as the desktop: our stereo core, desktop and graphics drivers.
On the KDL-46HX855 it runs the 3D desktop by itself, with its own screen off, in full HD for each eye (the TV's frame packing mode).
Red-cyan 3D works on it too, tested by Daniel.

## Your hardware

If your machine runs a current Linux desktop, it is the kind of machine this is made for.
Tell us what you have: sign up in your language on [the front page](../README.md) and list your 3D gear.
