# Wiki Log — SoSimple
> Append-only chronological record of wiki operations.
> Format: `## [YYYY-MM-DD] operation | description`
> Parse last 5 entries: `grep "^## \[" wiki/log.md | tail -5`

## [2026-04-09] bootstrap | Initial wiki structure created
- Created wiki/wiki.py (generate/verify tool)
- Created wiki/WIKI_index.md (552 files tracked)
- Created wiki/index.md (catalog of wiki pages)
- Created wiki/log.md (this file)

## [2026-04-09] ingest | First bootstrap ingest: all 14 reports from docs/reports/
- Ingested 14 reports (2026-04-01 — 2026-04-09)
- Created wiki/research/signal-quality-research.md (synthesis of 7 signal quality reports)
- Created wiki/research/execution-tracks.md (synthesis of 7 execution track reports)
- Created wiki/concepts/signal-archetypes.md (key concept: bimodal 64/36 structure)
- Updated wiki/index.md with new pages
- Deleted wiki/LLM Wiki_method.md and wiki/wiki_index_method.md (design inputs, no longer needed)
- Updated MODULE_INDEX.md (+31 modules)

## [2026-04-10] ingest | Refresh execution tracks with latest reports
- Re-read all execution-track reports from 2026-04-08 onward
- Updated wiki/research/execution-tracks.md to include:
  - MT4 confirmation of frozen entry_path winner (2026-04-09)
  - quantile layer for entry_path_v1 (2026-04-10)
- Updated wiki/index.md coverage from 7 to 9 reports
- Regenerated wiki/REPO_integrity.md
