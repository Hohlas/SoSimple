# Entry Path Cross-Instrument Robustness Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить перенос `entry_path_v1` и `entry_path_v1_quantile` на другого провайдера `XAUUSD` и на новые инструменты без ретюнинга правил.

**Architecture:** Этап повторяет правильную схему предыдущего robustness-check. Сначала сравнивается `XAUUSD MetaQuotes -> Alpari` на том же frozen execution contour, чтобы отделить эффект нового провайдера. Только после этого запускается `cross-instrument transfer` на новых инструментах. `entry_path_v1` и `entry_path_v1_quantile` считаются отдельно: это два разных слоя принятия решения, и их нельзя смешивать в одной таблице.

**Tech Stack:** Python 3.12, pandas, NumPy, pytest, существующие `entry_path_v1` / `entry_path_v1_quantile` export tools, `ML/benchmark_cross_instrument_robustness.py`, MT4-ready `time;signal` CSV.

---

## Context

После завершения `take_skip`-ветки и общего `Cross-instrument robustness check` в проекте остались ещё две зрелые execution-системы:

- `entry_path_v1`
- `entry_path_v1_quantile`

Обе линии уже имеют:

- зафиксированные правила;
- сохранённые prediction/export artifacts;
- подтверждение в MT4 или parity-режиме;
- канонические отчёты.

Но их перенос на другого провайдера и на новые инструменты ещё не проверялся в той же строгой схеме, что уже использовалась для `quality`, `frequency`, `original_plus_path`.

Критическое правило этапа:

- не переобучать модели;
- не менять thresholds;
- не менять execution logic;
- не смешивать provider drift и instrument transfer.

## File Map

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`
- `docs/reports/2026-04-09-entry-path-trade-filter.md`
- `docs/reports/2026-04-09-mt4-parity-check-winner.md`
- `docs/reports/2026-04-10-entry-path-v1-quantile.md`
- `docs/reports/2026-04-12-quantile-status-decision.md`
- `docs/reports/2026-04-24-cross-instrument-robustness-check.md`
- `ML/benchmark_cross_instrument_robustness.py`
- `API/export_entry_path_v1_quantile_signals.py`
- `ML/benchmark_entry_path_trade_filter.py`
- `ML/benchmark_entry_path_v1_quantile_filter.py`

### Existing Frozen Inputs To Reuse

- `ML/reports/entry_path_trade_filter_selected_rule.json`
- `ML/reports/entry_path_v1_quantile_selected_rule.json`
- `ML/reports/entry_path_v1_validation_predictions.csv`
- `ML/reports/entry_path_v1_test_predictions.csv`
- `ML/reports/entry_path_v1_quantile_validation_predictions.csv`
- `ML/reports/entry_path_v1_quantile_test_predictions.csv`
- `ML/reports/entry_path_v1_quantile_robustness/seed_007/`
- `MT/tester/files/ml_signals.csv`

### Files To Create

- `ML/export_entry_path_cross_instrument_signals.py`
- `tests/test_export_entry_path_cross_instrument_signals.py`
- `docs/ML/export_entry_path_cross_instrument_signals.py.md`
- `ML/reports/entry_path_cross_instrument_robustness/manifest_xauusd_provider_drift.json`
- `ML/reports/entry_path_cross_instrument_robustness/manifest_cross_instrument_transfer.json`
- `ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline_reference.json`
- `docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md`

### Files To Modify

- `ML/README.md`
- `MODULE_INDEX.md`

### Files To Update At Stage Close

- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/index.md`
- `wiki/research/execution-tracks.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Canonical Evaluation Contract

### Systems Under Test

Only these two systems belong to this stage:

- `entry_path_v1`
- `entry_path_v1_quantile`

### Execution Contract

Freeze one execution contract per system family:

- `entry_path_v1`: использовать уже зафиксированное правило `entry_path_trade_filter_selected_rule.json`
- `entry_path_v1_quantile`: использовать уже зафиксированное правило `entry_path_v1_quantile_selected_rule.json`

If export requires separate helper code for baseline and quantile, that is acceptable, but the final benchmark table must treat both as the same type of artifact: `time;signal`.

### Output Metrics

For every dataset/system pair compute:

- `trades`
- `trades_per_year`
- `pf`
- `net_atr`
- `max_drawdown_atr`
- `ulcer_index_atr`
- `equity_linearity_r2`
- `profit_concentration_top_1/3/10`
- `negative_months`
- `negative_years`

### Verdict Vocabulary

Provider drift:

- `provider_stable`
- `provider_degraded`
- `provider_failed`

Transfer:

- `transfer_supported`
- `transfer_inconclusive`
- `transfer_failed`

## Task 1: Define Frozen Export Contract For Entry-Path Systems

**Files:**
- Create: `ML/export_entry_path_cross_instrument_signals.py`
- Test: `tests/test_export_entry_path_cross_instrument_signals.py`
- Read: `API/export_entry_path_v1_quantile_signals.py`

- [ ] **Step 1: Write failing tests for export contract**

Tests must prove:

- one helper can build `time;signal` for `entry_path_v1`;
- the same helper can build `time;signal` for `entry_path_v1_quantile`;
- helper rejects unknown `system_name`;
- helper preserves frozen behavior and does not fit thresholds on new data.

Use synthetic prediction CSVs and rule JSONs in the tests.

- [ ] **Step 2: Run the new export tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_cross_instrument_signals.py -q
```

Expected:
- FAIL because helper module does not exist yet.

- [ ] **Step 3: Implement minimal export helper**

Implement:

- `export_entry_path_signals(...)`
- `load_frozen_rule(...)`
- `build_manifest_signal_spec(...)`

Behavior:

- for `entry_path_v1`, reuse frozen trade-filter rule and existing prediction CSV contract;
- for `entry_path_v1_quantile`, reuse production rule export path without recomputing or re-fitting correction;
- output must always be `time;signal`.

- [ ] **Step 4: Re-run export tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_cross_instrument_signals.py -q
```

Expected:
- PASS.

## Task 2: Build XAUUSD MetaQuotes Baseline Reference

**Files:**
- Create: `ML/reports/entry_path_cross_instrument_robustness/manifest_xauusd_provider_drift.json`
- Create: `ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline_reference.json`
- Read: `ML/benchmark_cross_instrument_robustness.py`

- [ ] **Step 1: Identify canonical MetaQuotes inputs**

Document exact baseline sources for:

- `entry_path_v1`
- `entry_path_v1_quantile`

They must point to the existing `MetaQuotes`-based XAUUSD artifacts, not to any newly generated Alpari exports.

- [ ] **Step 2: Write a small reproducibility note into the manifest**

Manifest must include one `XAUUSD MetaQuotes` baseline dataset for each system family using the same benchmark tool.

- [ ] **Step 3: Run MetaQuotes baseline benchmark**

Run:

```bash
./.venv/bin/python -m ML.benchmark_cross_instrument_robustness \
  --manifest ML/reports/entry_path_cross_instrument_robustness/manifest_xauusd_provider_drift.json \
  --output-dir ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline
```

Expected:
- `summary.csv/json`
- `trades.csv`

- [ ] **Step 4: Extract baseline reference file**

Write `metaquotes_baseline_reference.json` with the exact frozen baseline metrics needed for future provider/transfer verdicts.

## Task 3: Run XAUUSD Provider Drift Check

**Files:**
- Modify: `ML/reports/entry_path_cross_instrument_robustness/manifest_xauusd_provider_drift.json`
- Read: `MT/MQL4/Files/Nero_XAUUSD.csv`
- Read: `MT/MQL4/Files/XAUUSD_H1_OHLC.csv`

- [ ] **Step 1: Prepare Alpari-side XAUUSD exports**

Generate `time;signal` exports for:

- `entry_path_v1`
- `entry_path_v1_quantile`

using frozen rules only.

- [ ] **Step 2: Run provider drift benchmark**

Run:

```bash
./.venv/bin/python -m ML.benchmark_cross_instrument_robustness \
  --manifest ML/reports/entry_path_cross_instrument_robustness/manifest_xauusd_provider_drift.json \
  --baseline-reference ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline_reference.json \
  --output-dir ML/reports/entry_path_cross_instrument_robustness/xauusd_provider_drift
```

Expected:
- both systems get explicit provider verdicts;
- table is directly comparable to the old `take_skip` provider drift stage.

- [ ] **Step 3: Sanity-check the comparison**

Verify:

- same systems;
- same verdict logic;
- same benchmark metrics;
- no retraining hidden in the export path.

## Task 4: Build Cross-Instrument Transfer Inputs

**Files:**
- Create: `ML/reports/entry_path_cross_instrument_robustness/manifest_cross_instrument_transfer.json`
- Read: `processing/label_main.py`
- Read: `MT/MQL4/Files/Nero_EURUSD.csv`
- Read: `MT/MQL4/Files/Nero_GBPUSD.csv`
- Read: `MT/MQL4/Files/Nero_USDCHF.csv`
- Read: `MT/MQL4/Files/Nero_XAGUSD.csv`

- [ ] **Step 1: Freeze the instrument list**

Use the same comparison set as the completed `take_skip` robustness stage:

- `EURUSD`
- `GBPUSD`
- `USDCHF`
- `XAGUSD`

- [ ] **Step 2: Define preprocessing rule**

State clearly:

- use prepared `*_test_labeled.csv` if they already exist and match the needed contract;
- otherwise regenerate them through the standard labeling pipeline;
- do not invent a custom labeling path unless the standard path is broken and the workaround is fully documented.

- [ ] **Step 3: Generate frozen exports for both systems on all instruments**

For each instrument, produce:

- `entry_path_v1` signal CSV
- `entry_path_v1_quantile` signal CSV

Save outputs under:

- `ML/reports/entry_path_cross_instrument_robustness/generated/<INSTRUMENT>/`

## Task 5: Run Cross-Instrument Benchmark

**Files:**
- Modify: `ML/reports/entry_path_cross_instrument_robustness/manifest_cross_instrument_transfer.json`

- [ ] **Step 1: Run the benchmark on all instruments**

Run:

```bash
./.venv/bin/python -m ML.benchmark_cross_instrument_robustness \
  --manifest ML/reports/entry_path_cross_instrument_robustness/manifest_cross_instrument_transfer.json \
  --baseline-reference ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline_reference.json \
  --output-dir ML/reports/entry_path_cross_instrument_robustness/cross_instrument_transfer
```

Expected:
- `summary.csv/json`
- `transfer_matrix.csv`
- `trades.csv`

- [ ] **Step 2: Review verdict consistency**

Check that:

- `entry_path_v1` and `entry_path_v1_quantile` are not judged by different hidden standards;
- provider and transfer tables stay separate;
- there is no accidental leakage from validation artifacts into transfer verdicts.

## Task 6: Write Final Report And Sync Project Memory

**Files:**
- Create: `docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/index.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify: `wiki/log.md`

- [ ] **Step 1: Write canonical report**

Report must include:

- why `entry_path_v1` and `entry_path_v1_quantile` were selected;
- provider drift table;
- cross-instrument transfer matrix;
- interpretation of whether quantile layer is more or less transferable than baseline `entry_path_v1`.

- [ ] **Step 2: Update changelog and handoff**

Add:

- short changelog entry;
- new current stage summary in `CONTEXT_HANDOFF.md`;
- next step recommendation.

- [ ] **Step 3: Ingest into wiki and regenerate integrity map**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py verify
```

Expected:
- `REPO_integrity.md` refreshed
- wiki index remains consistent

## Acceptance Criteria

The stage is complete only if:

- `entry_path_v1` and `entry_path_v1_quantile` are both benchmarked on `XAUUSD MetaQuotes -> Alpari`;
- both are benchmarked on the same new instrument set;
- no retraining or threshold search is performed on new instruments;
- final report separates `provider drift` from `transfer`;
- all outputs are reproducible from frozen inputs and saved under one dedicated report directory.
