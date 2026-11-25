#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Count competing code forms in a FreeCAD tree at one git revision.

Usage: count_idioms.py REPO REF SCOPE_NAME PATHSPEC [PATHSPEC ...]
Prints one line per form: the number of matching lines and of files with at least one.
Reads blobs with `git grep` at REF, so the working tree is not used.
"""
import subprocess
import sys

FORMS = [
    ("header guard #pragma once", r"^#pragma once"),
    ("header guard #ifndef X_H", r"^#ifndef [A-Z0-9_]+_H(PP)?_?$"),
    ("SPDX-License-Identifier", r"SPDX-License-Identifier"),
    ("SPDX-FileCopyrightText", r"SPDX-FileCopyrightText"),
    ("SPDX-FileNotice", r"SPDX-FileNotice"),
    ("old box 'Copyright (c)'", r"\*\s+Copyright \(c\)"),
    ("anonymous namespace", r"^namespace\s*\{?\s*$|^namespace \{"),
    ("named namespace (not Gui)", r"^namespace [A-Za-z_][A-Za-z0-9_:]*\s*\{?\s*$"),
    ("Base::Console().log/warning/error/message", r"Base::Console\(\)\.(log|warning|error|message|developerWarning|developerError|userWarning|userError|critical)\("),
    ("FC_LOG/FC_WARN/FC_ERR/FC_TRACE macros", r"\bFC_(LOG|WARN|ERR|TRACE|MSG)\("),
    ("fprintf(stderr / std::fprintf(stderr", r"fprintf\(stderr"),
    ("qDebug()/qWarning()", r"\bq(Debug|Warning|Critical)\(\)"),
    ("std::getenv", r"std::getenv\(|\bgetenv\("),
    ("std::unique_ptr / make_unique", r"std::(unique_ptr|make_unique)"),
    ("raw 'new ' (any)", r"=\s*new\s+[A-Z]"),
    ("CoinPtr<", r"CoinPtr<"),
    ("->ref() / ->unref()", r"->(ref|unref)\(\)"),
    ("freecad_cast<", r"freecad_cast<"),
    ("dynamic_cast<", r"dynamic_cast<"),
    ("isOfType( (Coin/Base types)", r"isOfType\(|isDerivedFrom\("),
    ("connect with &Class::member", r"connect\([^;]*&[A-Za-z_:]+::[a-zA-Z_]+"),
    ("connect with SIGNAL(/SLOT(", r"SIGNAL\(|SLOT\("),
    ("Q_EMIT", r"\bQ_EMIT\b"),
    ("bare emit", r"^\s*emit\s"),
    ("QT_TRANSLATE_NOOP", r"QT_TRANSLATE_NOOP\("),
    ("QT_TR_NOOP", r"QT_TR_NOOP\("),
    ("GetParameterGroupByPath", r"GetParameterGroupByPath\("),
    ("ViewParams::", r"ViewParams::"),
    ("std::format / fmt::format", r"std::format\(|fmt::format\("),
    ("std::ostringstream", r"std::ostringstream"),
    ("constexpr", r"\bconstexpr\b"),
    ("function-local static", r"^\s+static\s+(const\s+)?[A-Za-z_:<>]+\s+[a-z][A-Za-z0-9_]*\s*(=|;|\{)"),
    ("std::optional", r"std::optional<"),
    ("ZoneScoped (Tracy)", r"ZoneScoped"),
    ("PRIVATE(this) (Quarter)", r"PRIVATE\(this\)"),
    ("NOLINT", r"NOLINT"),
]


def count(repo, ref, pattern, specs):
    cmd = ["git", "-C", repo, "grep", "-P", "-c", "-I", "-e", pattern, ref, "--"] + specs
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode not in (0, 1):
        raise SystemExit(r.stderr.strip())
    lines = files = 0
    for row in r.stdout.splitlines():
        n = int(row.rsplit(":", 1)[1])
        lines += n
        files += 1
    return lines, files


def main():
    if len(sys.argv) < 5:
        raise SystemExit(__doc__)
    repo, ref, scope, specs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    r = subprocess.run(["git", "-C", repo, "ls-files", "--with-tree", ref, "--"] + specs,
                       capture_output=True, text=True, check=True)
    nfiles = len([x for x in r.stdout.splitlines() if x.endswith((".cpp", ".h", ".hpp", ".cxx"))])
    sha = subprocess.run(["git", "-C", repo, "rev-parse", "--short=10", ref],
                         capture_output=True, text=True, check=True).stdout.strip()
    print(f"## {scope} at {ref} {sha}: {nfiles} C++ files")
    for name, pattern in FORMS:
        lines, files = count(repo, ref, pattern, specs)
        print(f"{name:45s} {lines:6d} lines in {files:4d} files")


if __name__ == "__main__":
    main()
