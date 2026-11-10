#!/usr/bin/env python3
"""Make a copy of werkkzeug4's wz3_bitmap_code.cpp that compiles without the rest of werkkzeug4.

Usage: patch_wz3.py SOURCE.cpp TARGET.cpp
Whole functions are removed (the ones that need fonts, image files, the atlas or the
vector operator), and one line of Paste; no other line of a texture operator is changed.
"""
import re
import sys

src = open(sys.argv[1], encoding="latin-1").read().replace("\r\n", "\n")


def drop(text, head):
    """Remove the function whose definition starts with `head`, up to its closing brace."""
    i = text.index(head)
    j = text.index("{", i)
    depth, k = 0, j
    while True:
        if text[k] == "{":
            depth += 1
        elif text[k] == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    return text[:i] + "// (left out of this copy: " + head.split("(")[0].strip() + ")\n" + text[k + 1:]


for head in ("void GenBitmap::CopyTo(sImage *img)",
             "void GenBitmap::CopyTo(sImageI16 *dest)", "void GenBitmap::Init(const sImage *img)",
             "void GenBitmap::Text(", "void CalcGenBitmapVectorLoop(", "void GenBitmap::Vector(",
             "sInt LoadAtlas("):
    src = drop(src, head)
# Paste works on the copy its caller hands it; the "is this bitmap shared" test belongs to werkkzeug3's cache
i = src.index("GenBitmap * __stdcall Bitmap_Paste(")
src = src[:i] + src[i:].replace("  if(CheckBitmap(bm)) return 0;\n", "", 1)
open(sys.argv[2], "w", encoding="latin-1").write(src)
