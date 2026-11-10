#!/usr/bin/env python3
"""Read a werkkzeug3 project file (.k) and list its operators, page by page.

The layout follows WerkDoc::Read in fr_public/werkkzeug3/werkkzeug.cpp (file version 5 to 14):
a header, the pages, then every operator with its class, its place on the page grid
(x, y, width), its name, its links, its parameter words and its strings.
An operator takes as inputs the operators that sit in the row right above it and overlap
it sideways, from left to right (WerkPage::Connect1); Load takes a stored operator by name.

Usage: kdoc.py FILE.k            prints a summary
       import kdoc; kdoc.load(path) -> (pages, ops)
"""
import struct
import sys
from collections import Counter

MAGIC_BEGIN, CID = 0x3C3C3C3C, 0x01000100


class Reader:
    def __init__(self, data):
        self.w = struct.unpack("<%dI" % (len(data) // 4), data[:len(data) // 4 * 4])
        self.b = data
        self.p = 0

    def u(self):
        v = self.w[self.p]
        self.p += 1
        return v

    def s(self):
        n = self.u()
        t = self.b[self.p * 4:self.p * 4 + n].split(b"\0")[0].decode("latin-1")
        self.p += (n + 3) // 4
        return t


def load(path):
    data = open(path, "rb").read()
    r = Reader(data)
    while not (r.w[r.p] == MAGIC_BEGIN and r.w[r.p + 1] == CID):
        r.p += 1
    r.p += 2
    version = r.u()
    r.u()
    assert 5 <= version <= 14, version
    ec, pc, oc, ac = r.u(), r.u(), r.u(), r.u()
    r.p += 4
    pages = []
    for _ in range(pc):
        r.u(); r.u(); r.u(); r.u(); r.u()
        has_scratch, use_scratch = r.u(), r.u()
        r.u()
        pages.append(dict(name=r.s(), owner=r.s(), next=r.s(), use_scratch=bool(has_scratch and use_scratch)))
    ops = []
    for i in range(oc):
        cls, _, x, y, w, page, conv, scratch = [r.u() for _ in range(8)]
        bypass, strings, anims, hide = r.u(), r.u(), r.u(), r.u()
        blob = r.u() if version >= 12 else 0
        name = r.s()
        links = [r.s() for _ in range((conv >> 12) & 15)]
        n = conv & 255
        words = r.w[r.p:r.p + n]
        r.p += n
        strs = [r.s() for _ in range(strings)]
        splconv = (conv >> 20) & 7 if version >= 12 else (conv >> 20) & 15
        for _ in range(splconv):
            r.s()
        for _ in range(anims):
            px, py, ww, byte, para, uk, auto, _ = [r.u() for _ in range(8)]
            if uk == 1:      # AOU_VECTOR
                r.p += 4
            elif uk in (2, 3):  # AOU_COLOR, AOU_SCALAR
                r.p += 1
            elif uk == 4:    # AOU_NAME
                r.s()
            elif uk in (6, 7):  # AOU_EASE, AOU_TIMESHIFT
                r.p += 2
        ops.append(dict(i=i, cls=cls, x=x, y=y, w=w, page=page, conv=conv, scratch=scratch, bypass=bypass,
                        hide=hide, name=name, links=links, words=list(words), strings=strs, blob=blob))
    return pages, ops, r


if __name__ == "__main__":
    pages, ops, r = load(sys.argv[1])
    print(len(pages), "pages,", len(ops), "operators")
    c = Counter(o["cls"] for o in ops)
    print(sorted((hex(k), v) for k, v in c.items()))
