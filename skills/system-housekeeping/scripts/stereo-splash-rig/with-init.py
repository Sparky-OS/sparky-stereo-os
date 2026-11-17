#!/usr/bin/python3 -I
# with-init.py BASE.img OUT.img [NAME=PATH ...]: BASE.img followed by a newc cpio holding this folder's init (and any
# other NAME=PATH files); the kernel unpacks concatenated archives in order, so these files replace the image's own.
import os, sys

here = os.path.dirname(os.path.abspath(__file__))
base, out = sys.argv[1:3]
files = [('init', os.path.join(here, 'init'), 0o100755)]
for arg in sys.argv[3:]:
    name, path = arg.split('=', 1)
    files.append((name, path, 0o100755 if os.access(path, os.X_OK) else 0o100644))


def entry(name, data, mode, ino):
    nb = name.encode() + b'\0'
    h = b'070701' + b''.join(b'%08X' % v for v in (ino, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(nb), 0))
    rec = h + nb
    rec += b'\0' * (-len(rec) % 4)
    rec += data + b'\0' * (-len(data) % 4)
    return rec


arch = b''
for i, (name, path, mode) in enumerate(files):
    arch += entry(name, open(path, 'rb').read(), mode, 900000 + i)
arch += entry('TRAILER!!!', b'', 0, 0)
arch += b'\0' * (-len(arch) % 512)
with open(out, 'wb') as f:
    data = open(base, 'rb').read()
    f.write(data)
    f.write(b'\0' * (-len(data) % 512))   # the kernel takes a following archive only at an aligned offset
    f.write(arch)
