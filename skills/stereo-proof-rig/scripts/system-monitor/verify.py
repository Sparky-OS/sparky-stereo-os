#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""verify.py CASE_DIR MACHINE LANG red|old|green [LANG_DIR]: the rig row's verdict for System Monitor's Overview (row 182).
Expectations come from the machines read by hand (the recordings' sysfs, nvidia-smi on the station), not from the
probe's output. red, the published state: KDE's Overview opens with one GPU face for every card together. old, the
reviewed 0.1.0 build: its start page's title and its thread labels, as measured (the faults this build had). green:
the computer's preset opens, its title in LANG and whole in the sidebar (no ellipsis on screen), every card with the
sensors its driver reports (on the page, in ksystemstats' list, shown by name through AT-SPI), the note naming what it
does not report and no label for a sensor it lacks, one label per logical processor and no two threads under one
name, and every sensor of the page known to ksystemstats except the regular expressions the computer has nothing for
(then the missing-sensors banner shows, and only then)."""
import json
import re
import subprocess
import sys
from pathlib import Path

CASE, MACHINE, LANG, MODE = sys.argv[1:5]
LANG_DIR = Path(sys.argv[5]) if len(sys.argv) > 5 else Path("/pkg/lang")
HERE = Path(__file__).resolve().parent
# preset, what each card's driver reports (read from the recordings: gpu_busy_percent, mem_info_vram_*, the amdgpu
# hwmon's temp1_input and power1_input or power1_average; nvidia-smi dmon on the station), display devices
MACHINES = {
    "one-amd": ("one-gpu-many", {0: {"usage", "memory", "temperature", "power"}}, 1),
    "a10": ("every-gpu-many", {0: {"usage", "memory", "temperature"}, 1: {"memory", "temperature"}}, 2),
    "a10-real": ("every-gpu-few", {0: {"usage", "memory", "temperature"}, 1: {"memory", "temperature"}}, 2),
    "station": ("every-gpu-many", {0: {"usage", "memory", "temperature", "power"},
                                   1: {"usage", "memory", "temperature", "power"}}, 2),
}
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
preset, cards, devices = MACHINES[MACHINE]
atspi = json.loads((case / "start1/atspi.json").read_text())["objects"]
texts = [o.get("name") or "" for o in atspi if o.get("showing")]
frames = [o["name"] for o in atspi if o.get("role") == "frame"]
headings = [o["name"] for o in atspi if o.get("role") == "heading" and o.get("showing")]
banner = any(o.get("role") == "alert" and o.get("showing") for o in atspi)
listed = {}
for line in (case / "sensors.txt").read_text().splitlines():
    sid, _, name = line.partition(" ")
    listed[sid] = name
names = {i: listed.get("gpu/gpu%d" % i, "") for i in cards}
# the Name sensor's value, as System Monitor shows it (an NVIDIA card takes nvidia-smi's name over the udev one)
if (case / "start1/card-names.txt").exists():
    for line in (case / "start1/card-names.txt").read_text().splitlines():
        m = re.fullmatch(r"gpu/gpu([0-9]+)/name (.+)", line.strip())
        if m and int(m.group(1)) in names:
            names[int(m.group(1))] = m.group(2)
row(all(names.values()), "ksystemstats lists every card", json.dumps(names, ensure_ascii=False))
if (case / "start1/ksystemstats-ps.txt").exists():
    served = (case / "start1/ksystemstats-ps.txt").read_text()
    row(served.count("\npid ") + served.startswith("pid ") == 1, "one ksystemstats served the page", served.strip())
else:
    row(None, "one ksystemstats served the page (not recorded in this run)")

# the logical processors as ksystemstats lists them, and the labels a thread can carry on screen
processors = sorted(int(m) for m in re.findall(r"^cpu/cpu([0-9]+)/usage ", (case / "sensors.txt").read_text(), re.M))
ours = {n: s["LOCAL23"] % (n + 1) for n in processors}
kde = {n: listed.get("cpu/cpu%d/usage" % n, "") for n in processors}
thread_labels = [t.split("\x9c")[0] for t in texts if t.split("\x9c")[0] in set(ours.values()) | set(kde.values())]
dupes = sorted({t for t in thread_labels if thread_labels.count(t) > 1})


def measured():
    out = subprocess.run([sys.executable, "-I", str(HERE / "measure_sidebar.py"), str(case / "start1")],
                         capture_output=True, text=True)
    return [json.loads(line) for line in out.stdout.splitlines() if line.startswith("{")]


if MODE == "red":
    row(frames == [KDE_OVERVIEW[LANG] + " — System Monitor"] or frames[0].startswith(KDE_OVERVIEW[LANG]),
        "KDE's Overview opens", frames)
    row(sum(1 for h in headings if h == "GPU") == 1 and not any(re.fullmatch(r"GPU \d+", h) for h in headings),
        "one GPU face for every card together", headings)
elif MODE == "old":
    sidebar = [m for m in measured() if frames and m["title"] == frames[0]]
    row(sidebar and sidebar[0]["cut"] is False, "the start page's title is whole in the sidebar (measured on screen)", sidebar)
    row(not dupes, "no two threads under one name", "%s (threads shown %d of %d)" % (dupes, len(set(thread_labels)),
                                                                                    len(processors)))
else:
    part = s["LOCAL1"] if devices == 1 else s["LOCAL2"] % devices
    title = s["LOCAL3" if preset.endswith("few") else "LOCAL4"] % part
    row(frames and frames[0] == title, "the computer's preset opens, titled in %s (%s)" % (LANG, title), frames)
    sidebar_all = measured()
    sidebar = [m for m in sidebar_all if m["title"] == title]
    row(sidebar and sidebar[0]["cut"] is False, "its title is whole in the sidebar (measured: no ellipsis on screen)", sidebar)
    if (case / "post-hook.log").exists():
        # every preset shown in the sidebar (show-all-presets.sh): each of this computer's titles whole
        parts = [s["LOCAL1"]] + ([s["LOCAL2"] % devices] if devices > 1 else [])
        titles = [s[k] % part for part in parts for k in ("LOCAL3", "LOCAL4")]
        found = {m["title"]: m for m in sidebar_all}
        row(all(t in found and found[t]["cut"] is False for t in titles),
            "every preset's title is whole in the sidebar (%s)" % " | ".join(titles),
            [found.get(t, {"title": t, "found": False}) for t in titles])
    page = (case / "pages" / ("sparky-overview-%s-threads.page" % preset)).read_text(encoding="utf-8")
    ids = set()
    for m in re.finditer(r"^(?:highPrioritySensorIds|totalSensors)=(.*)$", page, re.M):
        ids |= set(json.loads(m.group(1).replace("\\\\", "\\")))
    known = [line.split(" ", 1)[0] for line in (case / "sensors-all.txt").read_text().splitlines()] \
        if (case / "sensors-all.txt").exists() else list(listed)
    unmatched = sorted(i for i in ids if not any(re.fullmatch(i, k) for k in known))
    row(all(re.match(r"(disk|network)/", i) for i in unmatched),
        "every sensor of the page is one ksystemstats has, but Disks' and Networks' expressions where it has none",
        unmatched)
    row(banner == bool(unmatched), "the missing-sensors banner shows only for those (%s)" % ("shown" if banner else
                                                                                          "not shown"), unmatched)
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
            shown = [t for t in texts for lab in lacks if lab != "?" and t.split("\x9c")[0] == lab]
            row(not shown, "gpu%d: no label for %s" % (i, ", ".join(missing)), shown)
        else:
            row(True, "gpu%d: every sensor reported" % i)
    shown_ours = [t for t in thread_labels if t in set(ours.values())]
    row(sorted(shown_ours) == sorted(ours.values()),
        "one label for each of the %d logical processors (%s)" % (len(processors), ", ".join(ours[n] for n in processors)),
        sorted(set(ours.values()) - set(shown_ours)))
    row(not dupes, "no two threads under one name", dupes)
    for key in ("LOCAL6", "LOCAL21") if preset.startswith("every") else ("LOCAL6",):
        row(s[key] in headings, "heading %r in %s" % (s[key], LANG), "")
failed = [r for r in rows if r["ok"] is False]
json.dump(rows, open(case / ("verdict-%s.json" % MODE), "w"), ensure_ascii=False, indent=1)
for r in rows:
    print("%s %s %s" % ({True: "PASS", False: "FAIL", None: "SKIP"}[r["ok"]], r["check"], "" if r["ok"] else r["detail"]))
print("%s %s %s %s: %d checks, %d failed, %d not recorded" % (MACHINE, LANG, MODE, CASE, len(rows), len(failed),
                                                               sum(1 for r in rows if r["ok"] is None)))
sys.exit(1 if failed else 0)
