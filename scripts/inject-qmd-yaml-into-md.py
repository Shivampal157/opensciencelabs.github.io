"""Inject YAML front matter from index.qmd into Quarto-generated index.md.

Quarto's GFM output sometimes omits or rewrites the YAML block. This script
ensures each blog index.md has the exact front matter from the source index.qmd,
so the blogging plugin and RSS get correct metadata (title, slug, date, etc.).

Run from repo root after 'quarto render' in the pre-build step.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BLOG_ROOT = REPO_ROOT / "pages" / "blog"


def extract_yaml_from_qmd(path: Path) -> str:
    """Return the YAML block (including --- fences) from a .qmd file.
    Drops 'format:' so the .md has only blog metadata for mkdocs."""
    text = path.read_text(encoding="utf-8")
    if not text.strip().startswith("---"):
        return ""
    rest = text.split("\n", 1)[1]
    match = re.search(r"^---\s*$", rest, re.MULTILINE)
    if not match:
        return ""
    raw = rest[: match.start()].rstrip()
    # Drop format: / gfm: / variant: lines (Quarto-only)
    lines = []
    skip = 0
    for line in raw.split("\n"):
        if skip > 0:
            skip -= 1
            continue
        if line.strip().startswith("format:"):
            skip = 2
            continue
        lines.append(line)
    yaml_body = "\n".join(lines).rstrip()
    return "---\n" + yaml_body + "\n---"


def extract_body_from_quartos_md(text: str) -> str:
    """Return the body of the doc (from first ## heading to end). Quarto GFM
    outputs: # Title\nAuthor\nDate\n\n## First section..."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("##"):
            return "\n".join(lines[i:])
    return "\n".join(lines)


def process_post_dir(dir_path: Path) -> None:
    """Inject YAML from index.qmd into index.md in the given blog post dir."""
    qmd_path = dir_path / "index.qmd"
    md_path = dir_path / "index.md"
    if not qmd_path.exists() or not md_path.exists():
        return
    yaml_block = extract_yaml_from_qmd(qmd_path)
    if not yaml_block:
        return
    md_content = md_path.read_text(encoding="utf-8")
    body = extract_body_from_quartos_md(md_content)
    new_md = yaml_block + "\n\n" + body
    md_path.write_text(new_md, encoding="utf-8")


def main() -> None:
    if not BLOG_ROOT.exists():
        print(f"[EE] Blog root not found: {BLOG_ROOT}", file=sys.stderr)
        sys.exit(1)
    for dir_path in BLOG_ROOT.iterdir():
        if dir_path.is_dir():
            process_post_dir(dir_path)
    print("[II] Injected YAML from .qmd into generated .md files.")


if __name__ == "__main__":
    main()
