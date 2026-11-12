#!/usr/bin/env python3
"""List a WebAssembly module's imports and exports (the binary format's sections 2 and 7): wasm_sections.py FILE.wasm"""
import sys


def leb(b, p):
    r = s = 0
    while True:
        x = b[p]; p += 1
        r |= (x & 0x7f) << s; s += 7
        if not x & 0x80:
            return r, p


def name(b, p):
    n, p = leb(b, p)
    return b[p:p + n].decode(), p + n


b = open(sys.argv[1], 'rb').read()
assert b[:8] == b'\0asm\x01\0\0\0', 'not a WebAssembly module'
p = 8
kinds = ['func', 'table', 'memory', 'global', 'tag']
while p < len(b):
    sid = b[p]; p += 1
    size, p = leb(b, p)
    end = p + size
    if sid == 2:
        n, q = leb(b, p)
        for _ in range(n):
            mod, q = name(b, q); fld, q = name(b, q)
            k = b[q]; q += 1
            print('import %s.%s (%s)' % (mod, fld, kinds[k]))
            if k == 0:
                _, q = leb(b, q)
            elif k == 1:
                q += 1; fl = b[q]; q += 1; _, q = leb(b, q)
                if fl & 1: _, q = leb(b, q)
            elif k == 2:
                fl = b[q]; q += 1; _, q = leb(b, q)
                if fl & 1: _, q = leb(b, q)
            elif k == 3:
                q += 2
        if n == 0:
            print('imports: none')
    if sid == 7:
        n, q = leb(b, p)
        for _ in range(n):
            nm, q = name(b, q)
            k = b[q]; q += 1
            _, q = leb(b, q)
            print('export %s (%s)' % (nm, kinds[k]))
    p = end
print('%d bytes' % len(b))
