# Cross-Instrument Robustness Check Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Отделить влияние смены провайдера котировок на `XAUUSD` от реального переноса системы на новые инструменты и получить каноническую таблицу робастности для `quality`, `frequency`, `original_plus_path`.

**Architecture:** Этап делится на две независимые проверки. Сначала выполняется `provider drift baseline`: те же frozen rules и тот же execution protocol прогоняются на `XAUUSD` от `Alpari`, а результат сравнивается с уже подтверждённым `XAUUSD` от `MetaQuotes`. Только после этого запускается `cross-instrument transfer`: те же frozen rules без перенастройки применяются к новым `Nero_XXX.csv` и `XXX_H1_OHLC.csv`, после чего строится единая матрица устойчивости с вердиктами `transfer_supported`, `transfer_inconclusive`, `transfer_failed`.

**Tech Stack:** Python 3, pandas, NumPy, pytest, существующие `API/export_take_skip_trailing_stop_v2_signals.py`, `ML/benchmark_execution_policy_v2.py`, frozen rules в `ML/reports/take_skip_trailing_stop_v2_*_selected_rule.json`, MT4 tester artifacts, docs/reports, wiki.

---

## Context

Текущий roadmap и `CONTEXT_HANDOFF.md` фиксируют `Cross-instrument robustness check` как следующий этап после `signal_export_parity`.

Свежий сравнительный анализ данных показал два разных эффекта:

- на всей истории `XAUUSD` от `MetaQuotes` и `Alpari` похожи умеренно;
- на окне `2023-01-01 .. 2025-12-31` расхождение уже заметное:
  - полное совпадение `OHLC` только на небольшой доле общих баров;
  - `Nero_XAUUSD_old.csv` и `Nero_XAUUSD.csv` на свежем окне не имеют полностью совпадающих строк.

Из этого следует жёсткое правило для этапа:

- сначала проверять `provider drift` на том же `XAUUSD`;
- только потом делать `cross-instrument transfer`;
- не смешивать оба эффекта в одном verdict.

Этот этап является **stress-test переноса**, а не заменой forward-validation на production-инструменте.

## Acceptance Rules

- Не менять frozen rules на `Alpari` и на новых инструментах.
- Не переобучать модели и не искать новые thresholds на transfer-данных.
- Не менять execution protocol между сравниваемыми системами.
- Для каждого system/dataset pair считать один и тот же набор метрик:
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
- В отчёте явно разделять:
  - `provider_drift`
  - `cross_instrument_transfer`
- Вердикты должны быть только из фиксированного словаря:
  - `provider_stable`
  - `provider_degraded`
  - `provider_failed`
  - `transfer_supported`
  - `transfer_inconclusive`
  - `transfer_failed`

## File Structure

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`
- `docs/reports/2026-04-19-execution-policy-v2.md`
- `docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md`
- `docs/reports/2026-04-22-signal-export-parity.md`
- `docs/superpowers/plans/2026-04-13-early-timeout-bar12.md`
- `API/export_take_skip_trailing_stop_v2_signals.py`
- `ML/benchmark_execution_policy_v2.py`
- `ML/benchmark_signal_export_parity.py`
- `MT/MQL4/Files/Nero_XAUUSD.csv`
- `MT/MQL4/Files/Nero_XAUUSD_old.csv`
- `MT/MQL4/Files/XAUUSD_H1_OHLC.csv`
- `DATA/XAUUSD_H1_OHLC.csv`

### Files To Create

- `ML/benchmark_cross_instrument_robustness.py`
- `tests/test_benchmark_cross_instrument_robustness.py`
- `docs/ML/benchmark_cross_instrument_robustness.py.md`
- `docs/reports/2026-04-23-cross-instrument-robustness-check.md`

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

### Existing Inputs To Reuse

- Frozen rules:
  - `ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json`
  - `ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json`
  - `ML/reports/take_skip_trailing_stop_v2_original_plus_path_selected_rule.json`
- Existing signal exports:
  - `MT/tester/files/ml_signals_quality.csv`
  - `MT/tester/files/ml_signals_frequency.csv`
  - `ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/ml_signals_original_plus_path.csv`

## Canonical Execution Protocol

Before any implementation, freeze the execution protocol that every compared system must use:

- `quality`: `TrailATR=8`, `TP=12`
- `frequency`: `TrailATR=8`, `TP=0`
- `original_plus_path`: `TrailATR=8`, `TP=0`

If a more conservative parallel table is wanted later, it must be reported as a second table, not mixed into the main verdict table.

## Task 1: Add Benchmark Skeleton and Dataset Manifest

**Files:**
- Create: `ML/benchmark_cross_instrument_robustness.py`
- Test: `tests/test_benchmark_cross_instrument_robustness.py`

- [ ] **Step 1: Write failing test for dataset manifest parsing**

Test behavior:

- benchmark accepts a manifest JSON with a list of datasets;
- each dataset entry contains:
  - `dataset_name`
  - `instrument`
  - `provider`
  - `kind` (`provider_drift_baseline` or `cross_instrument_transfer`)
  - `ohlc_path`
  - `signals` list with `system_name`, `signal_csv`, `policy_name`
- benchmark rejects duplicated `dataset_name`;
- benchmark rejects missing files;
- benchmark rejects unknown `kind`.

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_cross_instrument_robustness.py::test_manifest_validation_rejects_unknown_kind -q
```

Expected: fail with missing module/function.

- [ ] **Step 2: Implement manifest loader**

In `ML/benchmark_cross_instrument_robustness.py`, implement:

- `load_manifest(path)`
- `validate_manifest(payload)`
- dataclasses:
  - `RobustnessDataset`
  - `RobustnessSignalSpec`

Manifest rules:

- no implicit defaults for file paths;
- every dataset uses one OHLC source;
- every system explicitly points to its signal CSV;
- the same benchmark run may contain both `provider_drift_baseline` and `cross_instrument_transfer`, but they must remain distinguishable in output rows.

- [ ] **Step 3: Run green manifest tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_cross_instrument_robustness.py::test_manifest_validation_rejects_unknown_kind -q
```

Expected: pass.

## Task 2: Reuse Execution Engine and Produce Uniform Metrics

**Files:**
- Modify: `ML/benchmark_cross_instrument_robustness.py`
- Read: `ML/benchmark_execution_policy_v2.py`
- Test: `tests/test_benchmark_cross_instrument_robustness.py`

- [ ] **Step 1: Write failing test for policy-driven trade simulation**

Test behavior:

- benchmark reuses the same bar-by-bar execution semantics as `ML/benchmark_execution_policy_v2.py`;
- one synthetic signal file and one synthetic OHLC file produce:
  - deterministic trade count;
  - deterministic `pf`;
  - deterministic `max_drawdown_atr`.

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_cross_instrument_robustness.py::test_benchmark_reuses_execution_policy_metrics -q
```

Expected: fail until simulation is wired.

- [ ] **Step 2: Implement shared execution adapter**

Implementation rule:

- do not fork a second execution model;
- either import the existing helpers from `ML/benchmark_execution_policy_v2.py`, or extract minimal reusable helpers if duplication is unavoidable;
- benchmark output must preserve the same metric definitions already used in `execution_policy_v2`.

CLI should support:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_cross_instrument_robustness \
  --manifest ML/reports/cross_instrument_robustness/manifest.json \
  --output-dir ML/reports/cross_instrument_robustness
```

Required outputs:

- `summary.csv`
- `summary.json`
- `provider_drift.csv`
- `transfer_matrix.csv`
- `trades.csv`
- `run_metadata.json`

- [ ] **Step 3: Run green execution tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_cross_instrument_robustness.py::test_benchmark_reuses_execution_policy_metrics -q
```

Expected: pass.

## Task 3: Add Drift and Transfer Verdict Logic

**Files:**
- Modify: `ML/benchmark_cross_instrument_robustness.py`
- Test: `tests/test_benchmark_cross_instrument_robustness.py`

- [ ] **Step 1: Write failing tests for verdict rules**

Test behavior:

- `provider_stable` is allowed only when degradation is limited and trade activity remains in the same practical area;
- `provider_failed` fires when a previously confirmed system collapses materially on `XAUUSD` provider swap;
- `transfer_supported` is allowed only when the transferred system keeps `PF > 1`, reasonable activity, and no severe concentration blow-up;
- `transfer_inconclusive` is used for borderline cases instead of binary optimism.

Use explicit synthetic inputs to test verdict thresholds.

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_cross_instrument_robustness.py::test_verdict_logic_separates_provider_and_transfer_failures -q
```

Expected: fail until rules are implemented.

- [ ] **Step 2: Implement explicit verdict rules**

Start with conservative rules:

- `provider_stable`:
  - baseline system had confirmed historical MT4 result;
  - new run keeps `PF > 1`;
  - trade count does not collapse below `50%` of baseline;
  - `max_drawdown_atr` does not blow up more than `2x`;
  - `profit_concentration_top_1` does not rise into an obviously worse regime.
- `provider_degraded`:
  - still tradable, but one or more practical metrics deteriorate beyond the stable band.
- `provider_failed`:
  - `PF <= 1`, or trade activity collapses, or concentration/drawdown becomes non-practical.
- `transfer_supported`:
  - same frozen rule remains above practical minimum on the new instrument.
- `transfer_inconclusive`:
  - mixed evidence; no clear failure, no clear support.
- `transfer_failed`:
  - clear collapse under frozen transfer.

Implementation requirement:

- thresholds must live in one place;
- benchmark must emit reason fields, not only the verdict string.

- [ ] **Step 3: Run green verdict tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_cross_instrument_robustness.py::test_verdict_logic_separates_provider_and_transfer_failures -q
```

Expected: pass.

## Task 4: Prepare Canonical Manifest for XAUUSD Provider Drift

**Files:**
- Modify after implementation: `ML/reports/cross_instrument_robustness/manifest.json`
- Read: `MT/tester/files/ml_signals_quality.csv`
- Read: `MT/tester/files/ml_signals_frequency.csv`
- Read: `ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/ml_signals_original_plus_path.csv`

- [ ] **Step 1: Create provider-drift manifest**

Create one dataset entry for `XAUUSD_Alpari`:

- `instrument = XAUUSD`
- `provider = Alpari`
- `kind = provider_drift_baseline`
- `ohlc_path = MT/MQL4/Files/XAUUSD_H1_OHLC.csv`

Attach three systems:

- `quality` -> `MT/tester/files/ml_signals_quality.csv` -> `trail_x8_tp12`
- `frequency` -> `MT/tester/files/ml_signals_frequency.csv` -> `trail_x8`
- `original_plus_path` -> `ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/ml_signals_original_plus_path.csv` -> `trail_x8`

- [ ] **Step 2: Capture MetaQuotes baseline table**

Create a small baseline reference JSON or CSV inside `ML/reports/cross_instrument_robustness/` with already known confirmed metrics from reports:

- `quality`
- `frequency`
- `original_plus_path`

This reference is not re-optimized and not recomputed; it is the comparison anchor for provider drift.

- [ ] **Step 3: Run provider-drift benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_cross_instrument_robustness \
  --manifest ML/reports/cross_instrument_robustness/manifest.json \
  --baseline-reference ML/reports/cross_instrument_robustness/metaquotes_baseline_reference.json \
  --output-dir ML/reports/cross_instrument_robustness/provider_drift_xauusd
```

Expected:

- one row per `system × dataset`;
- populated `provider_drift.csv`;
- explicit verdict per system.

## Task 5: Harden Signal Preparation for New Instruments

**Files:**
- Modify: `ML/benchmark_cross_instrument_robustness.py`
- Read: `API/export_take_skip_trailing_stop_v2_signals.py`
- Test: `tests/test_benchmark_cross_instrument_robustness.py`

- [ ] **Step 1: Write failing test for signal/OHLC alignment guard**

Test behavior:

- benchmark fails fast when signal times are outside OHLC coverage;
- benchmark reports duplicated signal times separately from duplicated DATA rows;
- benchmark warns when signal CSV is sparse and needs explicit interpretation.

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_cross_instrument_robustness.py::test_alignment_guard_rejects_out_of_range_signals -q
```

Expected: fail until guard is implemented.

- [ ] **Step 2: Implement alignment diagnostics**

Reuse lessons from `ML/benchmark_signal_export_parity.py`:

- count raw rows;
- count non-zero rows;
- count unique timestamps;
- count missing timestamps in OHLC;
- report duplicate timestamps.

Add diagnostics to `run_metadata.json` and `summary.json`.

- [ ] **Step 3: Run green alignment tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_cross_instrument_robustness.py::test_alignment_guard_rejects_out_of_range_signals -q
```

Expected: pass.

## Task 6: Execute Cross-Instrument Transfer on New Symbols

**Files:**
- Read future inputs from `MT/MQL4/Files/Nero_XXX.csv`
- Read future inputs from `MT/MQL4/Files/XXX_H1_OHLC.csv`
- Modify after run: `ML/reports/cross_instrument_robustness/manifest.json`

- [ ] **Step 1: Add dataset entries for each new instrument**

For each `XXX`:

- create dataset entry with:
  - `instrument = XXX`
  - `provider = Alpari`
  - `kind = cross_instrument_transfer`
  - exact `ohlc_path`
- attach the same three systems and the same policy names as in the provider-drift stage.

Rule:

- no threshold retuning;
- no per-instrument policy change in the main table;
- if a system cannot be exported honestly for the new instrument, mark it as unavailable instead of improvising.

- [ ] **Step 2: Export frozen signals for each system/instrument pair**

Use existing exporter where needed:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions <prediction_csv> \
  --rule-path ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json \
  --output ML/reports/cross_instrument_robustness/signals/<instrument>_quality.csv
```

Repeat analogously for:

- `frequency`
- `original_plus_path`

If future new instruments require predictions to be generated first, that must be done in a separate preparatory task with no rule changes.

- [ ] **Step 3: Run transfer benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_cross_instrument_robustness \
  --manifest ML/reports/cross_instrument_robustness/manifest.json \
  --baseline-reference ML/reports/cross_instrument_robustness/metaquotes_baseline_reference.json \
  --output-dir ML/reports/cross_instrument_robustness/full_matrix
```

Expected:

- `transfer_matrix.csv` populated;
- one verdict per `system × instrument`;
- explicit reasons for failures and inconclusive cases.

## Task 7: Stage Report and Documentation Sync

**Files:**
- Create after run: `docs/reports/2026-04-23-cross-instrument-robustness-check.md`
- Modify: `docs/ML/benchmark_cross_instrument_robustness.py.md`
- Modify: `ML/README.md`
- Modify: `MODULE_INDEX.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/index.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify: `wiki/log.md`

- [ ] **Step 1: Document the benchmark module**

Create `docs/ML/benchmark_cross_instrument_robustness.py.md` with:

- purpose;
- CLI arguments;
- manifest format;
- output files;
- verdict definitions.

- [ ] **Step 2: Write canonical report**

Create `docs/reports/2026-04-23-cross-instrument-robustness-check.md` with sections:

- `Why Provider Drift Comes First`
- `Data Difference Snapshot`
- `Frozen Systems and Policies`
- `XAUUSD Provider Drift Results`
- `Cross-Instrument Transfer Results`
- `Key Failure Modes`
- `Operational Verdict`

- [ ] **Step 3: Sync project memory**

Update:

- `ML/README.md`
- `MODULE_INDEX.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`

Then sync wiki:

- add/update `wiki/research/execution-tracks.md`
- update `wiki/index.md`
- append entry to `wiki/log.md`
- regenerate `wiki/REPO_integrity.md`

## Suggested Commit Boundaries

- [ ] Commit 1: `test: add manifest and verdict tests for cross-instrument benchmark`
- [ ] Commit 2: `feat: add cross-instrument robustness benchmark`
- [ ] Commit 3: `docs: add cross-instrument benchmark docs`
- [ ] Commit 4: `report: record provider drift and transfer robustness verdicts`

## Final Validation Checklist

- [ ] Run focused tests:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_cross_instrument_robustness.py -q
```

- [ ] Run regression tests for reused interfaces:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_benchmark_execution_policy_v2.py \
  tests/test_export_take_skip_trailing_stop_v2_signals.py \
  tests/test_signal_export_parity.py -q
```

- [ ] Run provider-drift benchmark on `XAUUSD Alpari`.
- [ ] If provider-drift stage completes, run full transfer matrix on new instruments.
- [ ] Verify that the report uses frozen rules only and does not claim forward validation.
- [ ] Verify that every verdict row has a reason string and concrete metrics.

## Expected Outcome

После выполнения плана проект должен иметь:

- канонический benchmark для `provider drift` и `cross-instrument transfer`;
- отдельный verdict по смене провайдера на том же `XAUUSD`;
- отдельную матрицу переноса на новые инструменты;
- отчёт, который не смешивает transfer stress-test с production forward-validation.
