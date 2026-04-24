# System Correlation And Portfolio Check Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Сравнить зрелые торговые системы по пересечению сделок, совпадению направления, синхронности прибыли и общим просадкам, чтобы понять, какие системы реально дополняют друг друга в портфеле.

**Architecture:** Этап делится на две части. Сначала строится канонический анализ на `XAUUSD`, потому что именно там все пять систем уже подтверждены в одном исследовательском контуре. Затем, только как дополнительное расширение, допускается отдельный анализ на новых инструментах, но лишь для тех систем, которые уже получили `transfer_supported`. Базовый вывод о портфеле должен приниматься по `XAUUSD`, а не по смешанной матрице из несовместимых режимов.

**Tech Stack:** Python 3.12, pandas, NumPy, pytest, существующие benchmark artifacts (`trades.csv`, `summary.csv/json`), `ML/benchmark_execution_policy_v2.py`, `ML/benchmark_cross_instrument_robustness.py`.

---

## Context

К этому моменту в проекте есть пять зрелых execution-систем:

- `quality`
- `frequency`
- `original_plus_path`
- `entry_path_v1`
- `entry_path_v1_quantile`

Для них уже закрыты два важных вопроса:

- provider drift на `XAUUSD MetaQuotes -> Alpari`;
- cross-instrument stress-test.

Следующий вопрос уже другой: не “какая система красивая сама по себе”, а “какие системы достаточно независимы, чтобы их имело смысл объединять”.

Критическое правило этапа:

- не подменять анализ портфеля сравнением итоговых `PF`;
- опираться на сделки и временные ряды прибыли, а не только на summary-метрики;
- не смешивать `transfer_failed` системы с `transfer_supported` при выводе о новых инструментах;
- финальное решение о совместимости принимать сначала на `XAUUSD`, где все системы сравнимы в одном и том же базовом контуре.

## File Map

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`
- `docs/reports/2026-04-24-cross-instrument-robustness-check.md`
- `docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md`
- `wiki/research/execution-tracks.md`
- `ML/benchmark_cross_instrument_robustness.py`
- `ML/benchmark_execution_policy_v2.py`

### Existing Inputs To Reuse

- `ML/reports/cross_instrument_robustness/metaquotes_baseline/trades.csv`
- `ML/reports/cross_instrument_robustness/metaquotes_baseline/summary.csv`
- `ML/reports/cross_instrument_robustness/xauusd_provider_drift/trades.csv`
- `ML/reports/cross_instrument_robustness/xauusd_provider_drift/summary.csv`
- `ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline/summary.json`
- `ML/reports/entry_path_cross_instrument_robustness/xauusd_provider_drift/summary.json`
- `ML/reports/entry_path_cross_instrument_robustness/verdict_overview.json`
- `ML/reports/execution_policy_v2/trades.csv`
- `ML/reports/signal_export_parity/original_plus_path_20260420/summary.json`

### Files To Create

- `ML/benchmark_system_correlation.py`
- `tests/test_benchmark_system_correlation.py`
- `docs/ML/benchmark_system_correlation.py.md`
- `ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json`
- `ML/reports/system_correlation_portfolio/xauusd_system_correlation/`
- `docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`

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

## Canonical Comparison Contract

### Systems Under Test

Mandatory `XAUUSD` set:

- `quality`
- `frequency`
- `original_plus_path`
- `entry_path_v1`
- `entry_path_v1_quantile`

Optional extension set on new instruments:

- only systems with prior `transfer_supported`;
- instrument by instrument, never pooled together without label.

### Primary Comparison Axes

For every system pair compute:

- `trade_overlap_ratio`
- `same_direction_ratio`
- `entry_time_jaccard`
- `trade_pnl_corr`
- `daily_pnl_corr`
- `weekly_pnl_corr`
- `drawdown_overlap_ratio`
- `co_loss_ratio`
- `staggered_gain_ratio`

Definitions:

- `trade_overlap_ratio`: доля сделок, открытых в одно и то же время;
- `same_direction_ratio`: доля совпадения направления на общих входах;
- `entry_time_jaccard`: пересечение времён входа / объединение времён входа;
- `trade_pnl_corr`: корреляция результата только на общих входах;
- `daily_pnl_corr`: корреляция дневной агрегированной прибыли;
- `weekly_pnl_corr`: корреляция недельной агрегированной прибыли;
- `drawdown_overlap_ratio`: как часто системы находятся в просадке одновременно;
- `co_loss_ratio`: как часто обе системы теряют в один и тот же день;
- `staggered_gain_ratio`: как часто одна система зарабатывает, пока другая нейтральна или теряет.

### Canonical Verdict Vocabulary

Для каждой пары систем:

- `portfolio_complementary`
- `portfolio_partially_overlapping`
- `portfolio_redundant`
- `portfolio_unclear`

Правила verdict должны быть явными и воспроизводимыми в коде, а не описаны “на глаз”.

## Task 1: Normalize Trade Inputs For All Systems

**Files:**
- Create: `ML/benchmark_system_correlation.py`
- Test: `tests/test_benchmark_system_correlation.py`
- Read: `ML/benchmark_cross_instrument_robustness.py`
- Read: `ML/benchmark_execution_policy_v2.py`

- [ ] **Step 1: Write failing tests for trade normalization**

Tests must prove:

- benchmark умеет загрузить `trades.csv` от `quality/frequency/original_plus_path`;
- benchmark умеет загрузить `entry_path` trade artifacts из их report directories;
- missing required columns cause explicit validation error;
- systems from different sources normalize to one contract.

Required normalized columns:

- `system_name`
- `instrument`
- `provider`
- `entry_time`
- `exit_time`
- `direction`
- `pnl_atr`
- `holding_bars`

- [ ] **Step 2: Run normalization tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_benchmark_system_correlation.py -q
```

Expected:
- FAIL because benchmark module does not exist yet.

- [ ] **Step 3: Implement minimal normalization layer**

Implement helper functions:

- `load_trade_frame(...)`
- `normalize_trade_frame(...)`
- `validate_trade_frame(...)`
- `load_manifest(...)`

Behavior:

- accept benchmark-produced `trades.csv`;
- accept entry-path report artifacts even if their source layout differs;
- coerce timestamps to canonical strings or pandas datetimes;
- derive `pnl_atr` from the canonical trade result column used by the source benchmark.

- [ ] **Step 4: Re-run normalization tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_benchmark_system_correlation.py -q
```

Expected:
- PASS.

## Task 2: Lock The XAUUSD Baseline Manifest

**Files:**
- Create: `ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json`
- Read: `ML/reports/cross_instrument_robustness/metaquotes_baseline/trades.csv`
- Read: `ML/reports/entry_path_cross_instrument_robustness/metaquotes_baseline/summary.json`

- [ ] **Step 1: Define the canonical source for each system**

Manifest must point each system to exactly one `XAUUSD` baseline artifact.

Rules:

- `quality/frequency/original_plus_path` should come from the same baseline family;
- `entry_path_v1/entry_path_v1_quantile` should come from the same provider baseline family;
- provider must be explicit in the manifest;
- if `entry_path` baseline lacks ready `trades.csv`, the plan executor must regenerate it in the same frozen benchmark contour before correlation analysis continues.

- [ ] **Step 2: Validate the manifest in code**

Run:

```bash
./.venv/bin/python -m ML.benchmark_system_correlation \
  --manifest ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json \
  --dry-run
```

Expected:
- manifest validates and prints resolved systems without running the full benchmark.

## Task 3: Compute Pairwise Correlation Metrics On XAUUSD

**Files:**
- Modify: `ML/benchmark_system_correlation.py`
- Test: `tests/test_benchmark_system_correlation.py`

- [ ] **Step 1: Write failing tests for pair metrics**

Tests must prove:

- exact same trades produce high overlap and high correlation;
- non-overlapping trades produce low overlap;
- opposite directions on the same timestamps reduce `same_direction_ratio`;
- daily aggregation works even when raw trades are sparse.

- [ ] **Step 2: Run the targeted tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_benchmark_system_correlation.py -q
```

Expected:
- FAIL on missing metric calculations.

- [ ] **Step 3: Implement pairwise metrics**

Implement:

- `compute_trade_overlap(...)`
- `compute_direction_agreement(...)`
- `compute_trade_pnl_corr(...)`
- `compute_period_pnl_corr(period="D" | "W")`
- `compute_drawdown_overlap(...)`
- `classify_pair_verdict(...)`

Verdict logic must be simple and explicit. Example shape:

- high overlap + high daily correlation + high drawdown overlap -> `portfolio_redundant`
- low overlap + low/negative daily correlation + low drawdown overlap -> `portfolio_complementary`
- middle zone -> `portfolio_partially_overlapping` or `portfolio_unclear`

- [ ] **Step 4: Re-run the full correlation tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_benchmark_system_correlation.py -q
```

Expected:
- PASS.

## Task 4: Run The XAUUSD Portfolio Benchmark

**Files:**
- Create: `ML/reports/system_correlation_portfolio/xauusd_system_correlation/`

- [ ] **Step 1: Run the benchmark on the XAUUSD manifest**

Run:

```bash
./.venv/bin/python -m ML.benchmark_system_correlation \
  --manifest ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json \
  --output-dir ML/reports/system_correlation_portfolio/xauusd_system_correlation
```

Expected artifacts:

- `pairwise_matrix.csv`
- `system_summary.csv`
- `daily_pnl_matrix.csv`
- `weekly_pnl_matrix.csv`
- `drawdown_overlap.csv`
- `run_metadata.json`
- `summary.json`

- [ ] **Step 2: Sanity-check the benchmark output**

Verify:

- all five systems are present;
- total pair count is `10`;
- no pair silently drops to empty due to column mismatch;
- verdicts exist for every pair.

## Task 5: Add Optional Supported-Transfer Extension

**Files:**
- Modify: `ML/benchmark_system_correlation.py`
- Test: `tests/test_benchmark_system_correlation.py`

- [ ] **Step 1: Add a manifest mode for instrument-specific extension**

The benchmark must support extra manifests like:

- `USDCHF supported systems`
- `XAGUSD supported systems`

But it must keep them separate from the `XAUUSD` baseline run.

- [ ] **Step 2: Add tests for instrument isolation**

Run:

```bash
./.venv/bin/python -m pytest tests/test_benchmark_system_correlation.py -q
```

Expected:
- PASS with clear error on pooled mixed-instrument manifests that omit instrument labels.

- [ ] **Step 3: Decide whether to execute extension now**

Rule:

- do not block stage closure on this extension;
- execute only if `XAUUSD` results are clean and time budget allows;
- if run, report them as supplementary, not as the primary portfolio verdict.

## Task 6: Documentation And Stage Close

**Files:**
- Create: `docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`
- Modify: `docs/ML/benchmark_system_correlation.py.md`
- Modify: `ML/README.md`
- Modify: `MODULE_INDEX.md`
- Update: `CHANGELOG.md`
- Update: `CONTEXT_HANDOFF.md`
- Update: `wiki/index.md`
- Update: `wiki/research/execution-tracks.md`
- Update: `wiki/log.md`
- Regenerate: `wiki/REPO_integrity.md`

- [ ] **Step 1: Write the canonical report**

The report must answer plainly:

- which systems overlap heavily;
- which pairs are genuinely complementary;
- whether `entry_path_v1_quantile` adds new risk profile or duplicates existing systems;
- which systems are candidates for the first portfolio layer.

- [ ] **Step 2: Sync project memory**

Update:

- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- wiki ingest pages

The handoff must point to the next rational step after portfolio analysis.

- [ ] **Step 3: Run final verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_benchmark_system_correlation.py -q
./.venv/bin/python -m compileall ML/benchmark_system_correlation.py
```

Expected:
- tests PASS;
- benchmark module compiles;
- stage artifacts and report paths are valid.

## Notes For Executor

- Не пытаться выводить портфельные решения только по `PF`; это отдельная ошибка интерпретации.
- Если для `entry_path` baseline не хватает `trades.csv`, не писать обходные выводы. Нужно честно досчитать trade-level artifact тем же frozen benchmark-контуром.
- Если корреляция по сделкам и по дням расходится, это не ошибка. Это отдельный диагностический факт, который надо явно показать в отчёте.
- Если одна система торгует заметно реже, не штрафовать её автоматически: overlap и correlation должны считаться с учётом sparsity, а не как “ноль полезности”.
- Не смешивать `XAUUSD` и новые инструменты в одном главном verdict.

## Success Criteria

Этап считается закрытым, если выполнены все условия:

- существует канонический benchmark-модуль для pairwise system correlation;
- есть воспроизводимый `XAUUSD` pairwise-matrix для пяти зрелых систем;
- в отчёте явно выделены `complementary` и `redundant` пары;
- проектная память синхронизирована и следующий этап после portfolio-check понятен без чтения всей истории.

