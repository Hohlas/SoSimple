# Wiki Log — SoSimple
> Append-only chronological record of wiki operations.
> Format: `## [YYYY-MM-DD] operation | description`
> Parse last 5 entries: `grep "^## \[" wiki/log.md | tail -5`

## [2026-06-10] update | Fractal Stop Stage 2 oracle synced into wiki
- Updated `wiki/research/fractal-stop-research.md` after oracle diagnostics were added to `docs/reports/2026-06-10-fractal-stop-fav-stage2.md`.
- Recorded that RF Stage 2 remains FAIL, but oracle shows a high diagnostic ceiling for the mechanics.
- Reframed the next step from "stop research" to Stage 3: improve breach classifier and features.

## [2026-06-10] ingest | Fractal Stop Breach Stage 1 synced into wiki
- Added coverage for `docs/reports/2026-06-10-fractal-stop-breach-stage1.md`.
- Created `wiki/research/fractal-stop-research.md`.
- Recorded Stage 1 verdict: breach signal confirmed on validation and frozen test, but no trading PASS yet.
- Recorded Stage 2 caveat: trading layer must prove PnL/PF with costs and cannot use zero-spread as PASS.

## [2026-05-21] ingest | Direct direction improvement synced into wiki
- Added coverage for `docs/reports/2026-05-15-direct-direction-improvement.md`.
- Updated `wiki/research/execution-tracks-reconciliation-plus-audit.md` with §20 Direct Direction Improvement.
- Updated `wiki/research/execution-tracks-overview.md` from 39 to 40 reports and recorded the open SELL-side risk.
- Updated `wiki/index.md` report counts and coverage range for the reconciliation/candidate-source track.

## [2026-05-14] ingest | Entry path candidate-source audit
- Added `docs/reports/2026-05-14-entry-path-all-rows-ranking.md`.
- Updated `wiki/research/execution-tracks.md` with signal-only ablation and all-rows ranking result.
- Recorded verdict: all-rows ranking with `fractal0.direction` is rejected as a production path.
- Next research step: causal surrogate for `label_all().signal`.

## [2026-05-06] update | live-safe system tracker
- Added an Audit Tracker to `docs/reports/2026-05-05-live-safe-ml-audit.md`.
- Synced `wiki/research/execution-tracks.md` with the current follow-up order:
  focus `entry_path_v1_live_safe` first, then revisit quantile, keep take/skip
  paused unless a new live-safe hypothesis appears.
- Updated `entry_path_v1_live_safe` note after exporter support for `B` and
  `B_no_path6`; remaining question is rule-family stability, not export.
- Recorded decision: freeze `A` as the conservative live-safe baseline because
  it is simplest and repeated in `3 / 5` seeds.
- Recorded quantile follow-up after baseline `A`: n-boost remains
  `gate_fail` on stability, so quantile stays research-only.
- Added follow-up audit for `entry_path_v1_live_safe + A`: rule-family is
  robust with per-seed validation thresholds, but exact seed-42 threshold does
  not transfer across seed score scales.

## [2026-05-05] update | Take/skip live-safe baseline probe
- Added `live_safe_baseline_seq50` result to `wiki/research/execution-tracks.md`
- Recorded that direct take/skip rebuild without `predict`, `ret_dir_atr_lag1`,
  `ret_*`, `fav_*`, `adv_*` produced no validation winner
- Best observed validation PF was 1.5178 on only 3 trades; verdict `reject`
- Added follow-up note: MT-origin `Up/Dn` in `Nero.csv` are treated as live-safe
  accumulated `lib_PIC` state; `live_safe_path_seq50` is planned for remote
  server execution because local feature construction is too slow
- Added source-audit table to the canonical report: Python `predict`, `ret_*`,
  `fav_*`, `adv_*`, and `ret_dir_atr_lag1` are future-derived; MT-origin
  `Up/Dn` is treated separately
- Updated with server result: `live_safe_path_seq50` verdict `reject`, best
  validation PF 0.9893, no validation winner
- Updated with server result: `live_safe_geometry_seq50` verdict `reject`,
  best validation PF 0.5726, no validation winner
- Kept `wiki/index.md` coverage at 32 reports because the canonical report remained `2026-05-05-live-safe-ml-audit.md`

## [2026-05-05] update | Entry path v1 quantile over live-safe baseline
- Repeated `entry_path_v1_quantile` over the new `entry_path_v1_live_safe` baseline.
- Updated `wiki/research/execution-tracks.md`:
  - sequential PF > 2.0 for 4/5 seeds
  - one seed selected 0 sequential trades
  - n-boost `lb_gt_m_q40`: frozen test 35 trades, PF 32.4125
  - gate failed on stability: `same_winner_ratio=0.60 < 0.80`
- Kept `wiki/index.md` coverage at 32 reports because the canonical report remained `2026-05-05-live-safe-ml-audit.md`

## [2026-05-05] ingest | Entry path v1 live-safe retrain synced into wiki
- Extended report `docs/reports/2026-05-05-live-safe-ml-audit.md`
- Updated `wiki/research/execution-tracks.md` with `entry_path_v1_live_safe`:
  - removed `ret_dir_atr_lag1` from the new built-in profile
  - validation winner PF 2.8881
  - frozen test PF 3.6567
  - sequential test 25 trades, PF 2.3419
- Kept `wiki/index.md` coverage at 32 reports after merging the separate retrain report into the audit report

## [2026-05-05] update | Entry path v1 live-safe multi-seed follow-up
- Repeated retrain for seeds `7`, `17`, `42`, `77`, `123`
- Updated `wiki/research/execution-tracks.md`:
  - median sequential PF 2.3419
  - min sequential PF 1.5171, max 4.5985
  - PF > 2.0 for 3/5 seeds
  - PF <= 1.0 for 0/5 seeds
- Recorded exporter limitation: `A` supported, `B` / `B_no_path6` not yet supported

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

## [2026-04-18] ingest | Take/skip rule consumer synced into wiki
- Added report `docs/reports/2026-04-18-take-skip-rule-consumer.md`
- Updated `wiki/research/execution-tracks.md`:
  - added consumer-layer subsection for take/skip v2
  - recorded that frozen quality/frequency rules are now executable through a dedicated CLI
  - noted optional full-series expansion via `--base-csv`

## [2026-04-18] ingest | MT4 trailing-stop execution synced into wiki
- Added report `docs/reports/2026-04-18-mt4-trailing-stop-execution.md`
- Updated `wiki/research/execution-tracks.md`:
  - added MT4 direct trailing-stop execution subsection for `iSignal=3`
  - recorded new runtime parameters `ML_ExitMode` and `ML_TrailATR`
  - clarified that timeout path remains default, while trailing-stop is a separate explicit mode
- Updated `wiki/index.md` coverage from 19 to 20 reports

## [2026-04-19] ingest | Execution policy v2 synced into wiki
- Added report `docs/reports/2026-04-19-execution-policy-v2.md`
- Added benchmark `ML/benchmark_execution_policy_v2.py` and tests

## [2026-04-20] ingest | take_skip lib_PIC feature training synced into wiki
- Added report `docs/reports/2026-04-20-take-skip-lib-pic-feature-training.md`
- Updated `wiki/research/execution-tracks.md`:
  - added dual-stream `take_skip_v2` feature training verdict
  - recorded 9/9 rejects, `PF > 1` rows only at very low trade frequency
  - recorded next step: controlled ablation against the original baseline contract
- Updated `wiki/index.md` coverage from 22 to 23 reports
- Updated `wiki/research/execution-tracks.md`:
  - added Python + MT4 execution policy v2 subsection
  - recorded `ML_TakeProfitATR` as a broker-side TP parameter for direct ML mode
  - captured final frequent candidate: `ML_TrailATR=8`, `ML_TakeProfitATR=0`
  - captured cautious frequent alternative: `ML_TrailATR=6`, `ML_TakeProfitATR=0`
- Updated `wiki/index.md` coverage from 20 to 21 reports

## [2026-04-20] ingest | take_skip lib_PIC external selection synced into wiki
- Added report `docs/reports/2026-04-20-take-skip-lib-pic-selection.md`
- Added benchmark `ML/benchmark_take_skip_lib_pic_selection.py` and tests
- Updated `wiki/research/execution-tracks.md`:
  - recorded that `lib_PIC` filters did not replace the current quality/frequency rules
  - captured feature-frequency candidate: `pic_path_win_proxy24_share_w20 >= 0.25`, test `PF=5.30`, `trades_per_year=14.8`, `negative_year_slices=0`
  - clarified next step: use `lib_PIC` features inside a new training track rather than making a more complex external selector
- Updated `wiki/index.md` coverage from 21 to 22 reports

## [2026-04-20] ingest | take_skip original-contour feature ablation synced into wiki
- Added report `docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md`
- Added runner `ML/run_take_skip_original_contour_feature_matrix.py` and tests
- Updated `wiki/research/execution-tracks.md`:
  - recorded that the old single-tensor contour was reproduced with `input_features=539`
  - captured `original_plus_path_seq50` as practical candidate: `take_24_x8`, `prob>=0.60`, test `PF=38.78`, `trades_per_year=10.2`, negative years `0`
  - recorded that geometry candidates are not promoted because frozen test frequency falls to `4.8` trades/year
- Updated `wiki/index.md` coverage from 23 to 24 reports

## [2026-04-20] ingest | original_plus_path MT4 confirmation synced into wiki
- Updated report `docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md`
- Updated `wiki/research/execution-tracks.md`:
  - recorded MT4 confirmation for `original_plus_path_seq50`
  - captured `TrailATR=8, TP=0`: `29` trades, net `22294.65`, PF `23.79`, relative DD `14.74%`
  - captured cautious `TrailATR=8, TP=12`: `29` trades, net `15873.12`, PF `17.23`, relative DD `6.64%`
  - recorded parity caveat: exported rows can duplicate the same H1 timestamp, while MT4 consumes one direct ML signal per bar time

## [2026-04-22] ingest | signal export parity benchmark synced into wiki
- Added report `docs/reports/2026-04-22-signal-export-parity.md`
- Added benchmark `ML/benchmark_signal_export_parity.py` and tests
- Updated `wiki/research/execution-tracks.md`:
  - recorded that duplicate timestamps are expected because one H1 bar can form multiple different `lib_PIC` peaks/levels
  - captured `original_plus_path_20260420`: `51` nonzero rows, `37` unique `time+signal`, `29` MT4 opened trades
  - clarified that DATA should not be collapsed; runtime `time;signal` is coarser than DATA row identity
- Updated `wiki/index.md` coverage from 24 to 25 reports

## [2026-04-24] ingest | cross-instrument robustness check synced into wiki
- Added report `docs/reports/2026-04-24-cross-instrument-robustness-check.md`
- Updated `wiki/research/execution-tracks.md`:
  - recorded explicit split between `provider_drift_baseline` and `cross_instrument_transfer`
  - captured that `XAUUSD MetaQuotes -> Alpari` stayed `provider_stable` for all three systems
  - captured transfer matrix across `XAGUSD/EURUSD/GBPUSD/USDCHF`
  - recorded breadth conclusion: `frequency` is most robust by transfer width, `USDCHF` is strongest positive case, `EURUSD` is strongest negative case
- Updated `wiki/index.md` coverage from 25 to 26 reports

## [2026-04-24] ingest | entry_path cross-instrument robustness synced into wiki
- Added report `docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md`
- Updated `wiki/research/execution-tracks.md`:
  - added fixed-hold `entry_path` transfer subsection with `hold_24_backstop_50`
  - recorded `XAUUSD MetaQuotes -> Alpari` as `provider_stable` for both `entry_path_v1` and `entry_path_v1_quantile`
  - captured transfer matrix across `EURUSD/GBPUSD/USDCHF/XAGUSD`
  - recorded breadth conclusion: quantile variant is more robust than baseline `entry_path_v1`
- Updated `wiki/index.md` coverage from 26 to 27 reports

## [2026-04-24] ingest | system correlation and portfolio check synced into wiki
- Added report `docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`
- Added benchmark `ML/benchmark_system_correlation.py` and tests
- Updated `wiki/research/execution-tracks.md`:
  - added portfolio-level subsection for pairwise system correlation on `XAUUSD`
  - recorded explicit split between `redundant`, `complementary` and `partially_overlapping` pairs
  - captured main redundant pair: `frequency × original_plus_path`
  - captured main complementary line: `quality` / `original_plus_path` versus `entry_path` systems
- Updated `wiki/index.md` coverage from 27 to 28 reports

## [2026-04-27] docs | documentation architecture compacted
- Added `docs/README.md` as the documentation entry map.
- Added `docs/DOCS_ARCHITECTURE.md` as the source-of-truth matrix.
- Shortened `CONTEXT_HANDOFF.md` to current baton only.
- Converted `CLAUDE.md` into a thin Claude Code adapter to `AGENTS.md`.
- Updated `wiki/index.md` to point agents to the documentation architecture contract.

## [2026-04-27] docs | documentation map merged
- Merged `docs/DOCS_ARCHITECTURE.md` into `docs/README.md` to keep one documentation entrypoint.
- Updated agent and wiki references to use `docs/README.md`.

## [2026-04-27] docs | docs readme scoped to docs directory
- Scoped `docs/README.md` to artifacts inside `docs/`.
- Moved agent/navigation responsibility back to `AGENTS.md`.
- Added explicit `MODULE_INDEX.md` point-read rule to `AGENTS.md`.

## [2026-04-27] ingest | telemetry frequency demo launch synced into wiki
- Added report `docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`.
- Updated `wiki/research/execution-tracks.md`:
  - added `telemetry_frequency_v1` diagnostic launch section;
  - recorded frequency-first rule selection and ATR-sized SL/TP preset;
  - captured MQL reuse decision: extend `lib_ML_Signal.mqh::ML_TRADE()`, keep ticket-level helpers for multi-position, reuse `SERVICE.mqh` where compatible;
  - captured daily reconciliation CLI and required MLP log fields.
- Updated `wiki/index.md` coverage from 28 to 29 reports.

## [2026-04-27] ingest | telemetry frequency demo launch completed
- Updated report `docs/reports/2026-04-27-telemetry-frequency-demo-launch.md` to `Completed`.
- Updated `wiki/research/execution-tracks.md` with final tester proof:
  - `495` expected signals, `468` opened trades;
  - `critical_mismatch_count=0`;
  - broker-side `TakeProfit` / `StopLoss` closes logged via `source=broker_history`;
  - diagnostic contour ready for online demo launch.

## [2026-04-28] ingest | MQL runtime architecture snapshot
- Added report `docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`.
- Updated `wiki/research/execution-tracks.md`:
  - recorded `RECOUNT_HISTORY()` startup warmup for `PIC()` / `F[]`;
  - recorded `POC_SIMPLE()` as part of the atomic `PIC()` step;
  - recorded watcher runtime snapshot window (`--max-runtime-rows 12000`);
  - captured full-vs-12000 parity result (`signal_mismatch_rows=0`, `pred_* <= 3.37e-7`);
  - captured open finding: live `Nero.csv` has `signal=0` and `predict=0`, so diagnostic export cannot produce trades yet.
- Updated `wiki/index.md` coverage from 29 to 30 reports.

## [2026-04-29] save | online causal preprocessing contract
- Updated `wiki/research/execution-tracks.md` with the new online watcher contract:
  - raw `runtime_input_snapshot.csv` is no longer fed directly to inference;
  - `runtime_input_preprocessed.csv` applies fractal sorting and rowwise normalization;
  - diagnostic direction now refers to `fractal0.direction` after sorting.

## [2026-04-29] save | online inference contract guard
- Updated `wiki/research/execution-tracks.md` after audit of online/test parity:
  - recorded that legacy `original_baseline` used future-derived row features as model input;
  - recorded watcher contract guard and `--allow-unsafe-future-features` override;
  - clarified that unsafe override is only mechanical chain diagnostics, not ML-correct online validation.

## [2026-04-29] ingest | online inference contract hardening report
- Added `docs/reports/2026-04-29-online-inference-contract-hardening.md`.
- Updated `wiki/research/execution-tracks.md` and `wiki/index.md` coverage from 30 to 31 reports.

## [2026-05-05] ingest | live-safe ML audit
- Added `docs/reports/2026-05-05-live-safe-ml-audit.md`.
- Updated `wiki/research/execution-tracks.md`:
  - recorded legacy PF vs live-safe verdict for five profitable systems;
  - marked all five audited systems as `FAIL`;
  - recorded `ret_dir_atr_lag1` as future-derived after source/timing audit;
  - recorded live-safe `entry_path_v1` rebuild/retrain as the next blocker.
- Updated `wiki/index.md` coverage from 31 to 32 reports.

## [2026-05-07] ingest | entry path live-safe CPU baseline
- Added wiki coverage for:
  - `docs/reports/2026-05-07-cpu-gpu-reproducibility.md`;
  - `docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md`;
  - `docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md`.
- Updated `wiki/research/execution-tracks.md`:
  - recorded CPU-only production retrain decision;
  - recorded `entry_path_v1_live_safe + A @ 7.5%` as the main live-safe candidate;
  - recorded `entry_path_v1_quantile` as research-only over the CPU baseline;
  - recorded final take/skip `geometry_path` reject.
- Updated `wiki/index.md` coverage from 32 to 35 reports.

## [2026-05-11] save | online BackTest mode clarification
- Updated `wiki/research/execution-tracks.md` to record the operational split:
  - online/forward diagnostic uses `BackTest=0`;
  - Strategy Tester uses `BackTest=2` to select the current telemetry row.

## [2026-05-11] save | M5 online diagnostic event log
- Updated `wiki/research/execution-tracks.md`:
  - recorded `ML_MaxPositions=20` for the long-run M5 diagnostic;
  - recorded `MT/MQL4/Files/ml_trade_events.csv` as the detailed online/test
    trade-event log for price, spread, slippage, commission and swap analysis.

## [2026-05-13] ingest | online/tester execution reconciliation

- Ingested `docs/reports/2026-05-12-online-tester-execution-reconciliation.md`
  into `wiki/research/execution-tracks.md`.
- Updated `wiki/index.md` coverage from 36 to 37 execution-track reports.
- Linked `docs/ML/online_tester_reconciliation.py.md` as the canonical
  instruction for repeat online/tester reconciliation runs.

## [2026-05-14] ingest | entry path causal surrogate

- Added `docs/reports/2026-05-14-entry-path-causal-surrogate.md`.
- Updated `wiki/research/execution-tracks.md`:
  - recorded causal surrogate validation/test/sequential metrics;
  - recorded low active precision and high active recall;
  - marked the surrogate as research baseline, not production-rule.
- Updated `wiki/index.md` coverage for the new report.

## [2026-05-14] ingest | entry path direct bar model

- Added `docs/reports/2026-05-14-entry-path-direct-bar-model.md`.
- Updated `wiki/research/execution-tracks.md`:
  - recorded direct `BUY/SELL/SKIP` validation/test/sequential metrics;
  - recorded that offline `signal` is not used as gate;
  - marked direct score+direction as the best next research direction, not
    production-ready yet.
- Updated `wiki/index.md` coverage from 39 to 40 execution-track reports.

## 2026-05-18 - Ingest direct-direction audit
- Added `wiki/research/execution-tracks-direct-direction-audit.md` covering `docs/reports/2026-05-15-direct-direction-improvement.md` and `docs/audit/2026-05-18-codex-direct-direction-chain-audit.md`.
- Updated `wiki/index.md` and `wiki/research/execution-tracks-overview.md` coverage from 39/40 to 41 execution-track reports.
2026-05-21 23:00 — Ingest: added Direct Direction Rebuild (§22) to execution-tracks-direct-direction-audit.md; updated index (3 reports). Ran wiki.py generate.
[2026-05-23] Ingest: updated execution-tracks-take-skip-v2 (+v1 matrix, +v2 handoff, 04-17 reports), execution-tracks-direct-direction-audit (+transformer encoder direction, 05-21 report). Updated wiki/index.md, execution-tracks-overview.md.
### 2026-06-10: Stage 2 Ingest
- Updated wiki/research/fractal-stop-research.md: добавлены результаты Stage 2 (FAIL), статус changed from active to completed
- Updated wiki/index.md: sources count 1->2, status completed
### 2026-06-10: Save concept — folded-mov-channels
- Created wiki/concepts/folded-mov-channels.md: свёртка 10 up/dn → 5 mov_h, границы применимости (не для breach)
- Updated wiki/index.md: added to Concepts table
- Sources: EDA нормализации (2026-06-10), Stage 3 feature profiles
### 2026-06-11: Ingest Stage 3 feature profiles
- Updated `docs/reports/2026-06-10-feature-profiles-stage3.md`: clarified that `relative_geometry` is a profile-level winner, density/time are not isolated, `parse_fractal()` empty-fractal artifact does not affect Stage 3, and Stage 3.1 must precede XGBoost.
- Updated `CONTEXT_HANDOFF.md`: next step changed from immediate XGBoost to Stage 3.1 ablation.
- Updated `wiki/research/fractal-stop-research.md` and `wiki/index.md`: coverage Stage 1-3, 3 reports.
### 2026-06-11: Update concept — folded-mov-channels
- Updated `wiki/concepts/folded-mov-channels.md`: documented the decision to keep `Nero.csv` in the 23-field format, compute `mov_h` in Python only when needed, avoid `lib_PIC.mqh` re-export/relabel work, and keep current priority on `relative_geometry`.
