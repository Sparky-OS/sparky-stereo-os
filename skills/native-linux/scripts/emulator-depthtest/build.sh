#!/bin/sh
# SPDX-License-Identifier: MIT
# build.sh: depthtest.dol from source/depthtest.c with devkitPPC (run inside the pinned devkitpro/devkitppc image)
set -eu
export DEVKITPRO=/opt/devkitpro DEVKITPPC=/opt/devkitpro/devkitPPC
PATH=$DEVKITPPC/bin:$DEVKITPRO/tools/bin:$PATH
mkdir -p /tmp/b && cd /tmp/b
powerpc-eabi-gcc -O2 -Wall -mrvl -mcpu=750 -meabi -mhard-float -I$DEVKITPRO/libogc/include -c /src/depthtest.c -o depthtest.o
powerpc-eabi-gcc -mrvl -mcpu=750 -meabi -mhard-float depthtest.o -L$DEVKITPRO/libogc/lib/wii -lwiiuse -lbte -logc -lm -o depthtest.elf
elf2dol depthtest.elf /out/depthtest.dol
sha256sum /out/depthtest.dol
