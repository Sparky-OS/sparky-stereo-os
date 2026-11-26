#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""kwin_received.py KWIN.log  ->  what KWin received about colour, format and stereo, from its own WAYLAND_DEBUG=server log.

Prints the requests of the colour management, colour representation, stereo content and linux-dmabuf protocols that
clients sent (each different request once, with how often it came), and under them the same facts in words: the buffer
formats as DRM fourcc codes, the named transfer function and primaries (wp_color_manager_v1 enums), the luminances and
the mastering data.
"""
import collections
import re
import sys

TF = {1: "bt1886", 2: "gamma22", 3: "gamma28", 4: "st240", 5: "ext_linear", 6: "log_100", 7: "log_316", 8: "xvycc",
      9: "srgb", 10: "ext_srgb", 11: "st2084_pq", 12: "st428", 13: "hlg", 14: "compound_power_2_4"}
PRIM = {1: "srgb", 2: "pal_m", 3: "pal", 4: "ntsc", 5: "generic_film", 6: "bt2020", 7: "cie1931_xyz", 8: "dci_p3",
        9: "display_p3", 10: "adobe_rgb"}
INTENT = {0: "perceptual", 1: "relative", 2: "saturation", 3: "absolute", 4: "relative_bpc", 5: "absolute_no_adaptation"}
WANT = re.compile(r"(wp_image_description_creator_params_v1|wp_image_description_creator_icc_v1|wp_color_management_surface_v1|"
                  r"wp_color_manager_v1|wp_color_representation_surface_v1|wp_color_representation_manager_v1|"
                  r"kde_stereo_content_surface_v1|kde_stereo_content_manager_v1|zwp_linux_buffer_params_v1)#\d+\.(\w+)\((.*)\)")


def fourcc(n):
    return "".join(chr((n >> s) & 0xFF) for s in (0, 8, 16, 24))


def main():
    seen = collections.Counter()
    words = collections.Counter()
    for line in open(sys.argv[1], errors="replace"):
        if " -> " in line:      # an event KWin sent, not a request it received
            continue
        m = WANT.search(line)
        if not m:
            continue
        iface, req, a = m.groups()
        a = re.sub(r"(new id [a-z_0-9]+|[a-z_0-9]+)#\d+", r"\1#N", a)
        a = re.sub(r"fd \d+", "fd N", a)
        if iface == "zwp_linux_buffer_params_v1" and req not in ("add", "create", "create_immed"):
            continue
        seen["%s.%s(%s)" % (iface, req, a)] += 1
        n = [int(x) for x in re.findall(r"(?<![#\w.])-?\d+", a)]
        try:
            if req in ("create", "create_immed"):
                w, h, f = n[-4], n[-3], n[-2]
                words["buffer %dx%d format %s (0x%08x)" % (w, h, fourcc(f), f)] += 1
            elif req == "add" and iface == "zwp_linux_buffer_params_v1":
                words["buffer plane %d stride %d modifier 0x%08x%08x" % (n[-5], n[-3], n[-2], n[-1])] += 1
            elif req == "set_tf_named":
                words["transfer function: %s (%d)" % (TF.get(n[0], "?"), n[0])] += 1
            elif req == "set_primaries_named":
                words["primaries: %s (%d)" % (PRIM.get(n[0], "?"), n[0])] += 1
            elif req == "set_luminances":
                words["luminances: minimum %.4f cd/m2, maximum %d cd/m2, reference white %d cd/m2" % (n[0] / 10000, n[1], n[2])] += 1
            elif req == "set_mastering_luminance":
                words["mastering luminance: minimum %.4f cd/m2, maximum %d cd/m2" % (n[0] / 10000, n[1])] += 1
            elif req == "set_mastering_display_primaries":
                words["mastering display primaries (x,y in 1e-6): %s" % n] += 1
            elif req == "set_max_cll":
                words["maximum content light level: %d cd/m2" % n[0]] += 1
            elif req == "set_max_fall":
                words["maximum frame average light level: %d cd/m2" % n[0]] += 1
            elif req == "set_image_description":
                words["image description set on a surface, rendering intent %s (%d)" % (INTENT.get(n[-1], "?"), n[-1])] += 1
            elif req == "set_content":
                words["stereo content declared: %d (3 is full side by side, left eye first)" % n[0]] += 1
            elif iface == "wp_color_representation_surface_v1":
                words["colour representation: %s(%s)" % (req, a)] += 1
        except IndexError:
            pass
    print("# requests KWin received (count, request)")
    for k, c in sorted(seen.items()):
        print("%6d %s" % (c, k))
    print("# in words")
    for k, c in sorted(words.items()):
        print("%6d %s" % (c, k))


main()
