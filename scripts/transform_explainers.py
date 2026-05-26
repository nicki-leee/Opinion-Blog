#!/usr/bin/env python3
"""
Transform Ready_To_Post explainer markdowns into Mintlify-grade MDX.

For each file:
  - parse the SEO metadata block (lines after H1 until first blank line)
  - extract `SEO title:` and `Meta description:`
  - replace the Obsidian-style `![[xx.excalidraw.md]]` embed with a Mintlify <Frame>
    pointing at /images/<basename>.svg
  - convert the trailing "## FAQ" section into <AccordionGroup>/<Accordion>
  - turn the leading "## Quick Answer" into a <Note> callout (kept as a content
    section, not stripped — beginners read it first)
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

SRC = Path("/Users/wyh/Documents/Codex/2026-05-24/Opinion/01_SEO_Content/English/Ready_To_Post")
OUT = Path("/Users/wyh/Documents/opinion-docs/learn")

# slug used in URL + filename
SLUGS = {
    "01_What_Is_a_Prediction_Market.md": "what-is-a-prediction-market",
    "02_Prediction_Markets_vs_Sports_Betting.md": "prediction-markets-vs-sports-betting",
    "03_You_Do_Not_Have_to_Wait_Until_Resolution.md": "trade-before-resolution",
    "04_Order_Book_Spread_and_Liquidity.md": "order-book-spread-liquidity",
    "05_World_Cup_Prediction_Markets_Multi_Choice.md": "world-cup-multi-choice-markets",
}

# short sidebar labels
SIDEBAR = {
    "what-is-a-prediction-market": "What Is a Prediction Market",
    "prediction-markets-vs-sports-betting": "vs Sports Betting",
    "trade-before-resolution": "Trade Before Resolution",
    "order-book-spread-liquidity": "Order Book & Liquidity",
    "world-cup-multi-choice-markets": "World Cup Multi-Choice",
}


@dataclass
class Parsed:
    title: str
    description: str
    body: str
    excalidraw_basename: str  # e.g. "01_prediction_market_flow"


EXCALIDRAW_RE = re.compile(r"!\[\[(\d+_[a-z_]+)\.excalidraw\.md\]\]")


def parse(path: Path) -> Parsed:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # H1 -> title
    assert lines[0].startswith("# "), f"{path} missing H1"
    title = lines[0][2:].strip()

    # find Meta description
    description = ""
    body_start = 1
    for i, line in enumerate(lines[1:], start=1):
        m = re.match(r"^Meta description:\s*(.*)$", line)
        if m:
            description = m.group(1).strip()
        # body starts at the excalidraw embed or first H2
        if EXCALIDRAW_RE.search(line) or line.startswith("## "):
            body_start = i
            break

    body = "\n".join(lines[body_start:])
    em = EXCALIDRAW_RE.search(body)
    basename = em.group(1) if em else ""
    return Parsed(title=title, description=description, body=body, excalidraw_basename=basename)


def replace_excalidraw(body: str, basename: str, caption: str) -> str:
    if not basename:
        return body
    repl = (
        f'<Frame caption="{caption}">\n'
        f'  <img src="/images/{basename}.svg" alt="{caption}" />\n'
        f'</Frame>'
    )
    return EXCALIDRAW_RE.sub(repl, body, count=1)


def transform_faq(body: str) -> str:
    """Convert the trailing '## FAQ' block (### Q / answer paragraphs) into AccordionGroup."""
    idx = body.find("\n## FAQ")
    if idx < 0:
        return body
    head = body[:idx]
    faq_block = body[idx + len("\n## FAQ") :]

    # split into Q/A pairs by '### '
    items = []
    current_q: str | None = None
    current_a: list[str] = []
    for line in faq_block.splitlines():
        if line.startswith("### "):
            if current_q is not None:
                items.append((current_q, "\n".join(current_a).strip()))
            current_q = line[4:].strip()
            current_a = []
        else:
            if current_q is not None:
                current_a.append(line)
    if current_q is not None:
        items.append((current_q, "\n".join(current_a).strip()))

    parts = ["\n## FAQ\n", "<AccordionGroup>"]
    for q, a in items:
        parts.append(f'  <Accordion title="{escape_attr(q)}">')
        # indent the answer 4 spaces
        for ln in a.splitlines():
            parts.append(f"    {ln}" if ln else "")
        parts.append("  </Accordion>")
    parts.append("</AccordionGroup>")
    return head + "\n".join(parts) + "\n"


def transform_quick_answer(body: str) -> str:
    """Wrap the 'Quick Answer' section in a <Note> callout (preserves content)."""
    # Match: ## Quick Answer\n\n<paragraphs until next ## >
    m = re.search(r"(^|\n)## Quick Answer\s*\n+(.*?)(?=\n## )", body, re.DOTALL)
    if not m:
        return body
    inner = m.group(2).strip()
    # Re-indent inner content lightly; <Note> renders MDX
    block = "\n## Quick Answer\n\n<Note>\n" + inner + "\n</Note>\n"
    return body[: m.start()] + block + body[m.end() :]


def escape_attr(s: str) -> str:
    return s.replace('"', '\\"')


def yaml_escape(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_mdx(src_name: str, parsed: Parsed) -> Path:
    slug = SLUGS[src_name]
    sidebar = SIDEBAR[slug]

    # mutate body
    body = parsed.body
    # caption: derive a friendlier name from basename
    caption = " ".join(parsed.excalidraw_basename.split("_")[1:]).strip().title() if parsed.excalidraw_basename else ""
    body = replace_excalidraw(body, parsed.excalidraw_basename, caption or "Diagram")
    body = transform_quick_answer(body)
    body = transform_faq(body)

    # build new frontmatter
    fm = [
        "---",
        f"title: {yaml_escape(parsed.title)}",
        f"sidebarTitle: {yaml_escape(sidebar)}",
        f"description: {yaml_escape(parsed.description)}",
        "---",
        "",
    ]
    out_path = OUT / f"{slug}.mdx"
    out_path.write_text("\n".join(fm) + body.lstrip("\n") + ("\n" if not body.endswith("\n") else ""), encoding="utf-8")
    return out_path


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in SLUGS:
        src = SRC / name
        parsed = parse(src)
        out = write_mdx(name, parsed)
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
