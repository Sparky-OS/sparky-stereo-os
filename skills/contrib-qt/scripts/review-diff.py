#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Print review questions with changed-line locations. Run from the Qt module's Git tree."""
import argparse
import re
import subprocess
from pathlib import PurePosixPath


def git(*args):
    return subprocess.check_output(["git", *args], text=True)


def changed_files(parent, tip):
    fields = git("diff", "--name-status", "-z", "-M", parent, tip, "--", "src", "tests")
    entries = iter(fields.rstrip("\0").split("\0")) if fields else iter(())
    for status in entries:
        old = next(entries)
        new = next(entries) if status.startswith(("R", "C")) else old
        yield status, old, new


def changed_lines(parent, tip, old_path, path):
    if old_path == path:
        revisions = (parent, tip, "--", path)
    else:
        revisions = (parent + ":" + old_path, tip + ":" + path)
    diff = git("diff", "--no-color", "--no-ext-diff", "-U0", *revisions)
    old = new = 0
    for line in diff.splitlines():
        hunk = re.match(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if hunk:
            old, new = map(int, hunk.groups())
        elif line.startswith(("@", "+++", "---")):
            continue
        elif line.startswith("-"):
            yield "-", old, line[1:]
            old += 1
        elif line.startswith("+"):
            yield "+", new, line[1:]
            new += 1


def enclosing_handler(lines, index):
    for i in range(index, -1, -1):
        if lines[i] == "}":
            break
        if re.match(r"^int \w+::\w+\(", lines[i]):
            end = lines.index("}", index) if "}" in lines[index:] else len(lines)
            if set(re.findall(r"\breturn ([^;]+);", "\n".join(lines[i:end]))) == {"0"}:
                return i
    return None


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("base")
    args.add_argument("tip")
    args.add_argument("--module-dir", required=True, help="production folder whose idioms were counted")
    args = args.parse_args()
    base, tip = args.base, args.tip
    found = set()

    def ask(rule, path, line, value):
        mark = (rule, path, line)
        if mark not in found:
            print(rule, path, line, value.strip().replace("\t", " "), sep="\t")
            found.add(mark)

    body = git("log", "-1", "--format=%B", tip).rstrip()
    for n, line in enumerate(body.splitlines(), 1):
        if re.match(r"^[\w-]+: |^\(cherry picked from ", line):
            continue
        if re.search(r"[a-z]\(\)|m_[a-z]|operator==", line):
            ask(1, "MESSAGE", n, line)
        if len(line) > 72:
            ask(2, "MESSAGE", n, line)
    if not re.search(r"^Change-Id: I[0-9a-f]{40}$", body, re.M):
        ask(2, "MESSAGE", 1, "missing Change-Id")
    for status, old_path, path in changed_files(base, tip):
        filename = PurePosixPath(path)
        header = filename.suffix in (".h", ".hpp")
        if not header and filename.suffix not in (".cpp", ".cxx", ".cc"):
            continue
        production = path.startswith(args.module_dir.rstrip("/") + "/")
        lines = [] if status == "D" else git("show", tip + ":" + path).splitlines()
        for side, n, value in changed_lines(base, tip, old_path, path):
            if side == "-":
                if re.search(r"\w*(?:Cache|Changed|Listener|[Ll]ock|[Ss]ync)\s*\(", value):
                    ask(19, old_path, n, value)
                continue
            i = n - 1
            near = "\n".join(lines[max(0, i-1):i+5])
            above = "\n".join(lines[max(0, i-5):i+1])
            if header and re.fullmatch(r"\s+const char \*\w+;", value):
                ask(4, path, n, value)
            if ("return -1;" in value and "empty()" in above
                    or re.search(r"\[\s*(?:size_t|qsizetype)\(\w+(?:Index|Offset)\(", value)):
                ask(5, path, n, value)
            if value.strip() == "return 0;":
                start = enclosing_handler(lines, i)
                if start is not None:
                    ask(6, path, start+1, lines[start])
            if "std::variant<" in value and not header and re.search(r"\)\s*(?:const)?\s*\{", near):
                ask(7, path, n, value)
            if re.search(r"\bif\s*\(\s*!?\w+\.has_value\(\)\s*\)", value):
                ask(8, path, n, value)
            if (production and re.search(r"std::(find|find_if|equal|sort|all_of|any_of|none_of|copy|transform|for_each)\(", value)
                    and ".begin()" in near and ".end()" in near):
                ask(9, path, n, value)
            if production and re.search(r"^\s+for \(.*:", value) and re.search(r"\n\s+if \([^\n]+\)\s*\n\s+(?:return|continue)\b", near):
                ask(10, path, n, value)
            if header and re.search(r"\bm_\w*(?:[Rr]eported|[Ww]arned|[Ll]ogged)\w*\s*[;{=]", value):
                ask(11, path, n, value)
            if production and "qCInfo(" in value:
                ask(12, path, n, value)
            if re.search(r"qC?(?:Warning|Critical|Fatal)", value) and "UNLIKELY" in "\n".join(lines[max(0,i-2):i+1]):
                ask(13, path, n, value)
            if re.search(r"^\s*(emit |(?:signals|public slots|private slots):)", value) and "QT_NO_KEYWORDS" in "\n".join(lines):
                ask(14, path, n, value)
            if value.lstrip().startswith("//") and re.search(r"operator==|[Cc]ompare\b", value) and "equal(" in "\n".join(lines[n:n+6]):
                ask(15, path, n, value)
            if header and re.search(r"\bm_\w*(?:Source|Sink)Name\s*;", value):
                ask(16, path, n, value)
            if "camera" in filename.name.lower() and re.search(r"^#\s*include\s+.*audio", value, re.I):
                ask(17, path, n, value)
            if "syncRegistry(" in value and value.strip() in [s.strip() for s in (lines[max(0,i-1):i]+lines[i+1:i+2])]:
                ask(22, path, n, value)
            if "spa_dict_lookup(" in value and "PW_KEY_METADATA_NAME" in value:
                ask(24, path, n, value)


if __name__ == "__main__":
    main()
