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

## [2026-04-11] ingest | Quantile robustness stage synced into wiki
- Added report `docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md`
- Updated `wiki/research/execution-tracks.md` with multi-seed robustness verdict:
  - `same_rule_count = 5`
  - `negative_year_slices = 0`
  - final verdict `go_mt4`
- Updated `wiki/index.md` coverage from 9 to 10 reports
- Regenerated `wiki/REPO_integrity.md`

## [2026-04-11] ingest | Quantile MT4 parity stage synced into wiki
- Added report `docs/reports/2026-04-11-entry-path-v1-quantile-mt4-parity.md`
- Updated `wiki/research/execution-tracks.md` with quantile MT4 parity verdict:
  - exporter dedupe fix `keep='last'`
  - canonical export `8872` rows / `8` active signals
  - MT4 result `PF=58.88`, `7W/1L`, `DD=2.85%`
  - reconciliation artifact `ML/reports/entry_path_v1_quantile_mt4_reconciliation.csv`
- Updated `wiki/index.md` coverage from 10 to 11 reports
- Regenerated `wiki/REPO_integrity.md`

## [2026-04-12] ingest | Quantile status decision + TB verdict synced into wiki
- Added report `docs/reports/2026-04-12-quantile-status-decision.md` (production parallel mode verdict для quantile-layer)
- Added report `docs/reports/2026-04-12-tb-verdict.md` (TB gate_fail, не production)
- Updated `wiki/research/execution-tracks.md`:
  - new section "Quantile Status Decision (04-12)" с details про n-boost gate (PF=8.18, win_rate=0.8125), MT4 parity 20/20, 4 устранённых бага pipeline
  - new section "MT4 Verdict (04-12)" под TB-трек: fixed simulator bug (`int(outcome)` на float-лейблах), honest test PF=1.28, gate fail по PF и negative years 2023/2026
  - обновлена сравнительная таблица треков: quantile → production parallel mode, TB → gate fail
  - обновлены открытые вопросы (composition, forward validation, TB regime shift)
- Updated `wiki/index.md` coverage from 11 to 13 reports
- Header `execution-tracks.md`: `last_updated: 2026-04-12`, `sources: 13`
- Regenerated `wiki/REPO_integrity.md`
