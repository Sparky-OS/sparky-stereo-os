#!/bin/sh
# Run once before prove-m2.sh m1: Calamares given a configuration folder with -c reads its qml/ and branding/ from that
# folder, so they are links to what the rig image has (the edition's branding is reached through the branding package's
# own link /etc/calamares/branding/sparky). Links to paths of the image, not of this host.
cd "$(dirname "$0")" && ln -sfn /usr/share/calamares/qml qml && ln -sfn /etc/calamares/branding branding
