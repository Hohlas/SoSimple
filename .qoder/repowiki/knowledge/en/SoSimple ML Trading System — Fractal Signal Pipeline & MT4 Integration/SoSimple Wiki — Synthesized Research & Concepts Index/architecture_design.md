The module is a documentation/knowledge layer organized around three content directories plus a CLI tool:
- `index.md` is the canonical entry point for agents, linking to synthesized pages in `research/` (cross-report synthesis) and `concepts/` (stable domain knowledge).
- `research/*.md` files aggregate findings across multiple dated reports under `docs/reports/`, forming narrative arcs (e.g. execution-tracks, signal-quality, fractal-stop).
- `concepts/*.md` captures enduring architectural decisions extracted from those reports.
- `wiki.py` is a self-contained CLI (`generate`, `verify`, `status`, `search`) that scans the repo, parses `MODULE_INDEX.md` for per-file descriptions/status emojis, computes blake2b hashes, and writes `REPO_integrity.md` — an auto-generated integrity map used by agents as a project map.
- `.archive/execution-tracks-monolith-deprecated.md` holds deprecated material kept for reference.
Dependency direction is one-way: wiki pages reference upstream artifacts (`docs/reports/*`, code, MODULE_INDEX); the CLI reads filesystem state but is never imported by application code.