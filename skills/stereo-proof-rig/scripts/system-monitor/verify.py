#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""verify.py CASE_DIR MACHINE LANG red|green [LANG_DIR]: the rig row's verdict for System Monitor's Overview (row 182).
Expectations come from the recorded machines read by hand (sysfs and nvidia-smi), not from the probe's output:
red (the published state): KDE's Overview opens, one GPU face for every card together; green: the computer's preset
opens with its title in LANG, every card with the sensors its driver reports (on the page, in ksystemstats' list and
as labels read through AT-SPI), the note naming what it does not report, and no label for a sensor it lacks."""
import json
import re
import sys
from pathlib import Path

CASE, MACHINE, LANG, MODE = sys.argv[1:5]
LANG_DIR = Path(sys.argv[5]) if len(sys.argv) > 5 else Path("/pkg/lang")
# what each card's driver reports, read from the recordings (gpu_busy_percent, mem_info_vram_*, the amdgpu hwmon's
# temp1_input and power1_input or power1_average) and from nvidia-smi dmon on the station
MACHINES = {
    "one-amd": ("one-gpu-many", {0: {"usage", "memory", "temperature", "power"}}),
    "a10": ("every-gpu-many", {0: {"usage", "memory", "temperature"}, 1: {"memory", "temperature"}}),
    "a10-real": ("every-gpu-few", {0: {"usage", "memory", "temperature"}, 1: {"memory", "temperature"}}),
    "station": ("every-gpu-many", {0: {"usage", "memory", "temperature", "power"},
                                   1: {"usage", "memory", "temperature", "power"}}),
}
TITLE_KEY = {"one-gpu-few": "LOCAL1", "one-gpu-many": "LOCAL2", "every-gpu-few": "LOCAL3", "every-gpu-many": "LOCAL4"}
SENSOR_KEY = {"usage": "LOCAL9", "memory": "LOCAL10", "temperature": "LOCAL11", "power": "LOCAL12"}
KDE_OVERVIEW = {"en": "Overview", "pt_BR": "Visão geral", "de": "Übersicht"}

rows = []


def row(ok, what, detail=""):
    rows.append({"ok": None if ok is None else bool(ok), "check": what, "detail": detail})


def strings(lang):
    t = {}
    for line in (LANG_DIR / lang).read_text(encoding="utf-8").splitlines():
        m = re.fullmatch(r'(LOCAL[0-9]+)="([^"]*)"', line)
        if m:
            t[m.group(1)] = m.group(2)
    return t


case = Path(CASE)
s = strings(LANG)
preset, cards = MACHINES[MACHINE]
atspi = json.loads((case / "start1/atspi.json").read_text())["objects"]
texts = [o.get("name") or "" for o in atspi if o.get("showing")]
frames = [o["name"] for o in atspi if o.get("role") == "frame"]
headings = [o["name"] for o in atspi if o.get("role") == "heading" and o.get("showing")]
listed = {}
for line in (case / "sensors.txt").read_text().splitlines():
    sid, _, name = line.partition(" ")
    listed[sid] = name
names = {i: listed.get("gpu/gpu%d" % i, "") for i in cards}
row(all(names.values()), "ksystemstats lists every card", json.dumps(names, ensure_ascii=False))
if (case / "start1/ksystemstats-ps.txt").exists():
    served = (case / "start1/ksystemstats-ps.txt").read_text()
    row(served.count("\npid ") + served.startswith("pid ") == 1, "one ksystemstats served the page", served.strip())
else:
    row(None, "one ksystemstats served the page (not recorded in this run)")

if MODE == "red":
    row(frames == [KDE_OVERVIEW[LANG] + " — System Monitor"] or frames[0].startswith(KDE_OVERVIEW[LANG]),
        "KDE's Overview opens", frames)
    row(sum(1 for h in headings if h == "GPU") == 1 and not any(re.fullmatch(r"GPU \d+", h) for h in headings),
        "one GPU face for every card together", headings)
else:
    title = s[TITLE_KEY[preset]]
    row(frames and frames[0] == title, "the computer's preset opens, titled in %s" % LANG, frames)
    page = (case / "pages" / ("sparky-overview-%s-threads.page" % preset)).read_text(encoding="utf-8")
    ids = set()
    for m in re.finditer(r"^(?:highPrioritySensorIds|totalSensors)=(.*)$", page, re.M):
        ids |= set(json.loads(m.group(1).replace("\\\\", "\\")))
    explicit = sorted(i for i in ids if re.fullmatch(r"[A-Za-z0-9/]+", i))
    row(all(i in listed for i in explicit), "every explicit sensor of the page is one ksystemstats has",
        [i for i in explicit if i not in listed])
    for i, reported in cards.items():
        prefix = "gpu/gpu%d/" % i
        on_page = {i2[len(prefix):] for i2 in ids if i2.startswith(prefix)}
        want = {"name"} | {"usage"} & reported
        want |= {"usedVram", "totalVram"} if "memory" in reported else set()
        want |= {"temperature"} if "temperature" in reported else set()
        if "power" in reported:
            want |= {"power"} if "power" in on_page and "power1" not in on_page else {"power1"}
        row(on_page == want, "gpu%d: the page holds what its driver reports" % i, sorted(on_page))
        shown_name = [t for t in texts if t == names[i]]
        row(shown_name, "gpu%d: System Monitor shows the card ksystemstats listed (%s)" % (i, names[i]), "")
        heading = s["LOCAL7"] % (i + 1)
        row(heading in headings, "gpu%d: its card is on the page (%s)" % (i, heading), headings)
        missing = [k for k in ("usage", "memory", "temperature", "power") if k not in reported]
        if missing:
            note = s["LOCAL8"] % s["LOCAL13"].join(s[SENSOR_KEY[k]] for k in missing)
            row(note in headings, "gpu%d: the note names what is not reported" % i, note)
            # no label for a sensor the driver lacks (ksystemstats would show it as 0)
            lacks = []
            if "usage" in missing:
                lacks.append(listed.get(prefix + "usage", "?"))
            if "power" in missing:
                lacks += [listed.get(prefix + "power", "?"), listed.get(prefix + "power1", "?")]
            shown = [t for t in texts for l in lacks if l != "?" and t.split("\x9c")[0] == l]
            row(not shown, "gpu%d: no label for %s" % (i, ", ".join(missing)), shown)
        else:
            row(True, "gpu%d: every sensor reported" % i)
    for key in ("LOCAL6", "LOCAL21") if preset.startswith("every") else ("LOCAL6",):
        row(s[key] in headings, "heading %r in %s" % (s[key], LANG), "")
failed = [r for r in rows if r["ok"] is False]
json.dump(rows, open(case / ("verdict-%s.json" % MODE), "w"), ensure_ascii=False, indent=1)
for r in rows:
    print("%s %s %s" % ({True: "PASS", False: "FAIL", None: "SKIP"}[r["ok"]], r["check"], "" if r["ok"] else r["detail"]))
print("%s %s %s %s: %d checks, %d failed, %d not recorded" % (MACHINE, LANG, MODE, CASE, len(rows), len(failed),
                                                               sum(1 for r in rows if r["ok"] is None)))
sys.exit(1 if failed else 0)
