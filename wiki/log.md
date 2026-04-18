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

## [2026-04-13] audit | TB float-label convention audit completed
- Added report `docs/reports/2026-04-13-label-convention-audit.md`
- Added audit artifacts:
  - `ML/reports/label_convention_audit.md`
  - `ML/reports/label_convention_audit_inventory.csv`
- Fixed two post-verdict TB analytics bugs:
  - `ML/tb_signal_logic.py`: timeout no longer counted as loss via `~win_mask`
  - `ML/threshold_analysis.py`: timeout no longer counted as loss via `n_trades - wins`
- Added permanent guards: `tests/test_tb_label_invariants.py`
- Additional frozen rerun against canonical main-tree artifacts matched `2026-04-12` exactly:
  - validation: `28 / 16 / 4 / 2`, `PF=4.333333333333333`
  - test: `69 / 29 / 23 / 5`, `PF=1.2777777777777777`
- Conclusion: audit fixes did not change historical TB verdict

## [2026-04-13] ingest | Quantile × fav composition verdict synced into wiki
- Added report `docs/reports/2026-04-13-quantile-fav-composition.md`
- Updated `wiki/research/execution-tracks.md`:
  - new section for composition verdict
  - updated comparison table with `quantile × fav_3_vs_12`
  - final verdict corrected from initial source-mismatch `INCONCLUSIVE` to honest `gate_fail`
  - added note about rebuilt aligned `updn` source and 2023 negative yearly slice
- Updated `wiki/index.md` coverage from 13 to 14 reports
- Header `execution-tracks.md`: `last_updated: 2026-04-13`, `sources: 14`

## [2026-04-13] ingest | Fav 3 vs 12 standalone verdict synced into wiki
- Added report `docs/reports/2026-04-13-fav-3-vs-12-standalone.md`
- Updated `wiki/research/execution-tracks.md`:
  - corrected composition subsection header to final closed status
  - added standalone `fav_3_vs_12` verdict section
  - updated comparison table with standalone rejection
- Updated `wiki/index.md` coverage from 14 to 15 reports
- Header `execution-tracks.md`: `last_updated: 2026-04-13`, `sources: 15`

## [2026-04-13] ingest | PF uplift discovery synced into wiki
- Added report `docs/reports/2026-04-13-pf-uplift-discovery.md`
- Added 3 skeleton plans: `docs/superpowers/plans/2026-04-13-{ny-session-filter,early-timeout-bar12,pred-adv-cap}.md`
- Added artifacts: `ML/reports/pf_uplift_discovery/` (trade_enriched.csv, 6 probe JSON, regime_crosstab.csv, baseline_numbers.json)
- Updated `wiki/research/execution-tracks.md`:
  - added "PF Uplift Discovery (04-13)" section with probe results table and path-dep findings
  - updated open questions with PF uplift реализация item
- Updated `wiki/index.md` coverage from 16 to 17 reports
- Header `execution-tracks.md`: `last_updated: 2026-04-13`, `sources: 17`
- Verdict: 3 STRONG hypotheses shortlisted (NY session +12.1 PF, early timeout bar=12 +5.55 PF, pred_adv12 cap +4.57 PF)

## [2026-04-13] ingest | Quantile forward validation scaffold synced into wiki
- Added report `docs/reports/2026-04-13-quantile-forward-validation.md`
- Added benchmark `ML/benchmark_quantile_forward_validation.py`
- Current operational verdict: `watch / no_forward_data`
- Updated `wiki/research/execution-tracks.md`:
  - added forward validation scaffold section
  - clarified that historical test was not reused as forward data
  - updated comparison table and open question for strictly-forward prediction CSV
- Updated `wiki/index.md` coverage from 15 to 16 reports
- Header `execution-tracks.md`: `last_updated: 2026-04-13`, `sources: 16`

## [2026-04-18] ingest | Take/skip frequency follow-up synced into wiki
- Added report `docs/reports/2026-04-18-take-skip-frequency-followup.md`
- Updated `wiki/research/execution-tracks.md`:
  - added take/skip v2 frequency follow-up section
  - captured split between `quality-first` and `frequency-first`
  - recorded practical trade-off: `8.2 -> 19.2` trades/year on test at the cost of one negative year slice
- Updated `wiki/index.md` coverage from 17 to 18 reports
- Header `execution-tracks.md`: `last_updated: 2026-04-18`, `sources: 18`

## [2026-04-18] ingest | Anchored frequency refinement synced into wiki
- Re-read `docs/reports/2026-04-18-take-skip-frequency-followup.md` after follow-up refinement
- Updated `wiki/research/execution-tracks.md`:
  - added `anchor-expansion` as the main frequent candidate
  - corrected frequent-mode conclusion: raw `frequency-first` is exploratory, anchored mode is the better frozen candidate
- No new report added; synthesis updated in place

## [2026-04-18] ingest | Anchored sweet-spot refinement synced into wiki
- Re-read `docs/reports/2026-04-18-take-skip-frequency-followup.md` after narrow `16%–20%` frozen sweep
- Updated `wiki/research/execution-tracks.md`:
  - added `top_k 17%` as current best anchored sweet spot
  - recorded improved frequent compromise: `test PF=13.12`, `trades_per_year=16.4`, `negative_year_slices=0`

## [2026-04-18] ingest | Take/skip v2 rule artifacts synced into wiki
- Re-read `docs/reports/2026-04-18-take-skip-frequency-followup.md` after packaging frozen rule artifacts
- Updated `wiki/research/execution-tracks.md`:
  - added canonical paths for quality and frequent frozen rules
  - clarified that `take_24_x8 + top_k 17%` is the current packaged frequent candidate
