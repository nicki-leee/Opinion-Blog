# opinion-docs

Mintlify-powered docs site for Opinion's prediction-market learn hub.

## Local preview

```bash
npm i -g mintlify
mintlify dev
```

Then open http://localhost:3000.

## Project layout

```
.
├── docs.json              # Mintlify config + navigation
├── index.mdx              # Landing page
├── learn/                 # All articles (one .mdx per slug)
├── logo/                  # logo/light.svg, logo/dark.svg (TODO)
├── images/                # Inline article images
└── scripts/transform.py   # Re-generates learn/*.mdx from upstream SEO source
```

## Adding a new article

1. Drop a new MDX file under `learn/` (or re-run `scripts/transform.py` if you maintain the upstream source).
2. Add its path to the appropriate group in `docs.json` → `navigation.tabs[].groups[].pages`.
3. Commit & push — Mintlify auto-deploys.

## Source of truth

The English source articles live in
`/Users/wyh/Documents/Opinion-WorldCup-Growth-Plan/01_SEO_长尾阵地/EN/`.
`scripts/transform.py` converts them into Mintlify-compatible MDX in `learn/`.
