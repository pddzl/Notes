#!/usr/bin/env python3
"""Regenerate README.md (the vault catalog) from the file tree.

Rules:
- Every top-level folder (English, IT, ...) becomes a <details> section.
- Inside IT, each category folder also becomes a nested <details>.
- Every other folder becomes a plain nested list.
- README.md files are cataloged as 概述.md; the vault-root README.md is skipped.
- Junk files such as README.md.md are skipped.
- Entries are sorted alphabetically (Unicode order for Chinese), files first, then folders.

Usage:
    python3 scripts/gen_catalog.py           # regenerate README.md
    python3 scripts/gen_catalog.py --check   # exit 1 if README.md is out of date
"""

import os
import sys
import urllib.parse

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(VAULT, "README.md")
SKIP_DIRS = {".obsidian", ".git", ".trae", ".trash", "scripts"}
NESTED_DETAILS_SECTIONS = {"IT"}

# Characters that must be percent-encoded inside markdown link URLs.
ENCODING = [
    ("%", "%25"),
    (" ", "%20"),
    ("&", "%26"),
    ("(", "%28"),
    (")", "%29"),
    ("[", "%5B"),
    ("]", "%5D"),
    ("#", "%23"),
    ("?", "%3F"),
]


def collect(folder):
    """Return (files, folders) sorted alphabetically, files first."""
    files, folders = [], []
    for name in sorted(os.listdir(folder), key=str.lower):
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            if name in SKIP_DIRS or name.startswith("."):
                continue
            folders.append(name)
        elif name.endswith(".md"):
            if name == "README.md.md":
                continue  # junk double-extension file
            if folder == VAULT and name == "README.md":
                continue  # the catalog itself
            files.append(name)
    return files, folders


def label(name):
    """Display label for a file, escaping markdown-sensitive characters."""
    if name == "README.md":
        name = "概述.md"
    return name.replace("[", "\\[").replace("]", "\\]")


def encode(rel):
    """Percent-encode special characters, keeping CJK characters readable."""
    for char, enc in ENCODING:
        rel = rel.replace(char, enc)
    return rel


def emit_list(folder, rel_base, depth, out):
    """Emit a nested markdown list for one folder."""
    files, folders = collect(folder)
    indent = "  " * depth
    for name in files:
        rel = os.path.join(rel_base, name)
        out.append(f"{indent}- [{label(name)}]({encode(rel)})")
    for name in folders:
        out.append(f"{indent}- {name}")
        emit_list(os.path.join(folder, name), os.path.join(rel_base, name), depth + 1, out)


def build():
    lines = ["## Catalog", ""]
    root_files, top_folders = collect(VAULT)

    for name in root_files:
        lines.append(f"- [{label(name)}]({encode(name)})")
    if root_files and top_folders:
        lines.append("")

    for name in top_folders:
        lines.append("<details>")
        lines.append(f"<summary>{name}</summary>")
        lines.append("")
        files, folders = collect(os.path.join(VAULT, name))
        for f in files:
            lines.append(f"- [{label(f)}]({encode(os.path.join(name, f))})")
        if files and folders:
            lines.append("")
        for d in folders:
            rel_d = os.path.join(name, d)
            if name in NESTED_DETAILS_SECTIONS:
                lines.append("<details>")
                lines.append(f"<summary>{d}</summary>")
                lines.append("")
                emit_list(os.path.join(VAULT, name, d), rel_d, 0, lines)
                lines.append("")
                lines.append("</details>")
            else:
                lines.append(f"- {d}")
                emit_list(os.path.join(VAULT, name, d), rel_d, 1, lines)
        lines.append("")
        lines.append("</details>")
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


def main():
    content = build()
    if "--check" in sys.argv:
        current = open(OUT, encoding="utf-8").read()
        if current == content:
            print("README.md is up to date")
            sys.exit(0)
        print("README.md is out of date — run: python3 scripts/gen_catalog.py")
        sys.exit(1)

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(content)
    links = content.count("](")
    print(f"README.md regenerated: {links} links")


if __name__ == "__main__":
    main()
