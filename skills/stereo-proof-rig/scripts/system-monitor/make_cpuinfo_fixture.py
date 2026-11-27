#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""make_cpuinfo_fixture.py OUT [CORE_IDS] [OFFLINE]: a /proc/cpuinfo for the rig made from this host's own blocks, so
every line ksystemstats reads is real: one socket (physical id 0), processors p and p+N sharing core id CORE_IDS[p % N]
(SMT siblings; default 0,1,2,4,5,6, a gap at 3 as many processors have), and the processors listed in OFFLINE left
out (default 5), as the kernel leaves out an offline processor. Mount it with run-case.sh CPUINFO=OUT."""
import re
import sys

out = sys.argv[1]
cores = [int(c) for c in (sys.argv[2] if len(sys.argv) > 2 else "0,1,2,4,5,6").split(",")]
offline = {int(c) for c in (sys.argv[3] if len(sys.argv) > 3 else "5").split(",") if c}
blocks = [b for b in open("/proc/cpuinfo").read().split("\n\n") if b.strip()]
kept = []
for b in blocks:
    p = int(re.search(r"^processor\s*:\s*(\d+)", b, re.M).group(1))
    if p in offline:
        continue
    b = re.sub(r"^physical id\s*:.*$", "physical id\t: 0", b, flags=re.M)
    b = re.sub(r"^core id\s*:.*$", "core id\t\t: %d" % cores[p % len(cores)], b, flags=re.M)
    kept.append(b)
open(out, "w").write("\n\n".join(kept) + "\n\n")
for b in kept:
    p = re.search(r"^processor\s*:\s*(\d+)", b, re.M).group(1)
    c = re.search(r"^core id\s*:\s*(\d+)", b, re.M).group(1)
    print("processor %s core %s" % (p, c))
