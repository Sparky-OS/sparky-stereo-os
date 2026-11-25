#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Search a FreeCAD change for what FreeCAD's rules and reviewers refuse, rule by rule.

Usage: review-diff.py [--repo DIR] BASE HEAD

Walks the commits BASE..HEAD and the diff BASE HEAD. Prints one line per finding:
    RULE  where  what was found
and exits 1 when a rule marked "must" found something, 0 otherwise ("note" findings are places
to read, not faults). Each rule names its source in the skill's reference page
(viewer-code-as-its-maintainers-write-it.md), where the walk table says what to decide.
"""
import argparse
import re
import subprocess
import sys

CODE = re.compile(r"^(src|tests)/.*\.(c|cc|cpp|cxx|h|hh|hpp|hxx)$")
NEW_SOURCE = re.compile(r"^(src|tests)/.*\.(cpp|cxx|h|hpp|py)$")
THIRD_PARTY = ("src/Gui/Quarter/", "src/3rdParty/", "src/Gui/QSint/", "src/Gui/3Dconnexion/navlib/")
EDITION_WORDS = re.compile(r"Sparky|the edition|libstereo-declare|stereo-declare|kcm_kscreen|systemsettings|kcmshell6", re.I)
AI_COAUTHOR = re.compile(r"^(Co-Authored-By|Co-authored-by):.*(Claude|GPT|Gemini|Copilot|Anthropic|OpenAI|noreply@anthropic)", re.I | re.M)
GENERATED = re.compile(r"Generated with|🤖", re.I)
ASSISTED = re.compile(r"^Assisted-by:\s*(.+)$", re.M)
ASSISTED_FORM = re.compile(r"^[A-Za-z][\w.+ -]*\S \([^()]+\)$|^[A-Za-z][\w.+-]*-[\w.+-]+$")
SUBJECT = re.compile(r"^[A-Z][A-Za-z0-9 _/+.-]*: [A-Z]")
NOUN_START = re.compile(r"^[^:]+: (The|A|An|the|a|an) ")

MUST = {"R1", "R2", "R3", "R4", "R6", "R7", "R8", "R11", "R12", "R14", "R15", "R17", "R18", "R19"}


def git(repo, *args, binary=False):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def added_lines(repo, base, head):
    """{path: [(line number, text)]} for the lines HEAD adds over BASE."""
    out, path, line = {}, None, 0
    for row in git(repo, "diff", "-U0", "--no-color", "--diff-filter=ACMR", base, head).splitlines():
        if row.startswith("+++ "):
            path = row[6:] if row.startswith("+++ b/") else None
            out.setdefault(path, [])
            continue
        m = re.match(r"@@ -\S+ \+(\d+)", row)
        if m:
            line = int(m.group(1))
            continue
        if path and row.startswith("+"):
            out[path].append((line, row[1:].rstrip("\r")))
            line += 1
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("base")
    ap.add_argument("head")
    a = ap.parse_args()
    repo = a.repo
    findings = []

    def find(rule, where, what):
        findings.append((rule, where, what))

    new_files = git(repo, "diff", "--name-only", "--diff-filter=A", a.base, a.head).split()
    changed = git(repo, "diff", "--name-only", "--diff-filter=ACMR", a.base, a.head).split()
    lines = added_lines(repo, a.base, a.head)

    # R1 a new header uses #pragma once (All: Header Guards -> Pragma Once, #27154)
    # R2 a new source file opens with the three SPDX lines (handbook, Copyright: SPDX and Snippets)
    # R3 no address in a copyright line of a new file (handbook snippets: year and holder only)
    for path in new_files:
        if not NEW_SOURCE.match(path):
            continue
        text = git(repo, "show", f"{a.head}:{path}")
        head_lines = text.splitlines()[:8]
        if path.endswith((".h", ".hpp")):
            m = re.search(r"^#ifndef ([A-Z0-9_]+_H\w*)$", text, re.M)
            if m:
                find("R1", path, f"include guard {m.group(1)} instead of #pragma once")
            elif "#pragma once" not in text:
                find("R1", path, "new header without #pragma once")
        for tag in ("SPDX-License-Identifier", "SPDX-FileCopyrightText", "SPDX-FileNotice"):
            if not any(tag in l for l in head_lines):
                find("R2", path, f"no {tag} in the first lines")
        for n, l in enumerate(text.splitlines()[:30], 1):
            if re.search(r"(Copyright|SPDX-FileCopyrightText).*<[^>]+@[^>]+>", l):
                find("R3", f"{path}:{n}", l.strip()[:90])

    for path, added in lines.items():
        if path is None:
            continue
        code = bool(CODE.match(path))
        third = path.startswith(THIRD_PARTY)
        if third and added:
            # R10 third-party code changed (hyarion, #30634: keep changes in 3rd party code to the minimum;
            # pre-commit excludes src/Gui/Quarter)
            find("R10", path, f"{len(added)} lines added in third-party code")
        for n, l in added:
            where = f"{path}:{n}"
            if code:
                # R4 diagnostics through Base::Console / FC_LOG, never stderr or an env switch
                if re.search(r"fprintf\s*\(\s*stderr|std::cerr|std::cout|\bprintf\s*\(|getenv\s*\(", l):
                    find("R4", where, l.strip()[:90])
                # R5 Coin nodes are tested with isOfType, not dynamic_cast (viewer files 27 to 1)
                if re.search(r"dynamic_cast<\s*So", l):
                    find("R5", where, l.strip()[:90])
                # R6 no new macros (handbook code review, Design 6)
                if re.match(r"\s*#\s*define\s", l) and not third and not re.match(r"\s*#\s*define\s+\w+_H\w*\s*$", l):
                    find("R6", where, l.strip()[:90])
                # R13 Python API (CONTRIBUTING 5.10; list affected addons)
                if re.search(r"add_(varargs|noargs|keyword)_method\(", l):
                    find("R13", where, l.strip()[:90])
                # R16 string messages to views were migrated to methods (#32116, #30632, #30633)
                if re.search(r'strcmp\("[^"]+",\s*pMsg\)', l):
                    find("R16", where, l.strip()[:90])
                # R12 FEP-0007 (Active): an ellipsis only where the action asks for more input, and the single character, never three dots
                if re.search(r'(sMenuText|setText)\s*=?\s*\(?\s*QT_TR_NOOP\("[^"]*(\.\.\.|…)"', l) or \
                        re.search(r'sMenuText\s*=\s*QT_TR_NOOP\("[^"]*(\.\.\.|…)"', l):
                    find("R12", where, l.strip()[:90])
                # R18 debug leftovers (handbook code review, Common 9)
                if re.search(r"qDebug\(\)", l):
                    find("R18", where, l.strip()[:90])
                # R19 QT_NO_KEYWORDS: Q_EMIT, Q_SIGNALS, Q_SLOTS (writing-code.md)
                if re.search(r"^\s*emit\s|^\s*(signals|slots|public slots|private slots)\s*:", l):
                    find("R19", where, l.strip()[:90])
                # R21 note: anonymous namespace (handbook C++ practices asks to avoid; 5 of 15 newest files use one)
                if re.match(r"^namespace\s*\{?\s*$", l):
                    find("R21", where, "anonymous namespace")
                # R22 note: function-local static state (handbook code review: global state should be avoided)
                if path.endswith((".cpp", ".cxx", ".cc")) and \
                        re.match(r"^\s+static\s+(const\s+)?[\w:<>, *&]+?\s*[*&]?\s*\w+(\s*,\s*\w+)*\s*(=|\{|;)", l):
                    find("R22", where, l.strip()[:90])
            # R15 edition-only words in a change meant for FreeCAD (ours first, upstream second)
            if EDITION_WORDS.search(l) and not path.startswith("."):
                find("R15", where, l.strip()[:90])

    # R11 a file keeps its line endings (AGENTS.md; #28941)
    for path in changed:
        if path in new_files:
            continue
        try:
            before = git(repo, "show", f"{a.base}:{path}", binary=True)
            after = git(repo, "show", f"{a.head}:{path}", binary=True)
        except subprocess.CalledProcessError:
            continue
        b_cr, a_cr = before.count(b"\r\n"), after.count(b"\r\n")
        b_n, a_n = before.count(b"\n"), after.count(b"\n")
        if (b_cr == b_n) != (a_cr == a_n) or (0 < a_cr < a_n):
            find("R11", path, f"CRLF lines {b_cr}/{b_n} before, {a_cr}/{a_n} after")

    # R9 PR size (contributing-changes.md: roughly 400 to 500 changed lines)
    stat = git(repo, "diff", "--numstat", a.base, a.head)
    total = sum(int(x) + int(y) for x, y, *_ in (r.split("\t") for r in stat.splitlines()) if x != "-")
    if total > 500:
        find("R9", "whole change", f"{total} changed lines (split into coherent PRs, or say why not)")

    # Commits: R7 disclosure trailer form, R8 subject form, R14 no AI co-author or tool branding,
    # R17 each commit's message states no failing test
    for sha in git(repo, "rev-list", "--reverse", f"{a.base}..{a.head}").split():
        msg = git(repo, "log", "-1", "--format=%B", sha)
        subject = msg.splitlines()[0] if msg else ""
        short = sha[:10]
        for m in ASSISTED.finditer(msg):
            if not ASSISTED_FORM.match(m.group(1).strip()) or re.search(r"\((Anthropic|OpenAI|Google)\)", m.group(1)):
                find("R7", short, f"Assisted-by: {m.group(1).strip()} (form: Model-Family (Version/ID))")
        if not SUBJECT.match(subject) or NOUN_START.match(subject):
            find("R8", short, f"subject: {subject[:80]}")
        if AI_COAUTHOR.search(msg) or GENERATED.search(msg):
            find("R14", short, "AI co-author trailer or tool branding in the message")
        if re.search(r"\b(fail|fails|failing)\b.*\bon this commit\b|\bthis commit\b.*\bfail", msg, re.I):
            find("R17", short, "the message says a test fails on this commit")
        if re.search(r"^Forwarded:|^Origin:|^Last-Update:", msg, re.M):
            find("R15", short, "a Debian patch header (DEP-3) in the commit message")

    for rule, where, what in findings:
        level = "must" if rule in MUST else "note"
        print(f"{rule:4s} {level:4s} {where}  {what}")
    musts = sum(1 for r, _, _ in findings if r in MUST)
    print(f"review-diff: {len(findings)} findings, {musts} on must rules")
    sys.exit(1 if musts else 0)


if __name__ == "__main__":
    main()
