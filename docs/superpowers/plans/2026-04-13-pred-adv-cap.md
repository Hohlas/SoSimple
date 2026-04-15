# pred_adv12 Cap Filter for entry_path_v1_quantile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить validation-first фильтр `pred_adv_12_atr <= Q75(validation)` поверх frozen `entry_path_v1_quantile`.

**Architecture:** Отдельный benchmark сначала воспроизводит frozen quantile-selected trades, затем фиксирует threshold только на validation filtered universe и применяет его к validation/test без retune. Test оценивается только если validation gate проходит; exporter и MT4 parity разрешены только после Python gate pass.

**Tech Stack:** Python 3.11, pandas/numpy, pytest, existing quantile artifacts, `ML.benchmark_entry_path_v1_quantile_filter`, `API/export_entry_path_v1_quantile_signals.py`.

---

## Decision Notes

- Discovery threshold `0.0313` был получен на test probe и не может быть production threshold.
- Canonical threshold для этого плана: `Q75(pred_adv_12_atr)` на validation quantile-selected trades.
- Фильтр не меняет signal, quantile rule, baseline threshold или hold policy.
- Этот track не зависит от закрытых `early_timeout` и `NY session` candidates.
- Идеи на будущее:
  - session filter standalone;
  - relaxed quantile + session composition.
  Они не входят в этот план, чтобы не смешивать вопросы.

## Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/reports/2026-04-13-pf-uplift-discovery.md`
- `docs/reports/2026-04-15-quantile-ny-session.md`
- `ML/reports/pf_uplift_discovery/probe_f_pred_adv12_le_Q75.json`
- `ML/reports/entry_path_v1_quantile_selected_rule.json`
- `ML/benchmark_quantile_ny_session.py`
- `API/export_entry_path_v1_quantile_signals.py`

## Files To Create

- `ML/benchmark_quantile_pred_adv_cap.py` — validation-first benchmark for `pred_adv_12_atr` cap.
- `tests/test_benchmark_quantile_pred_adv_cap.py` — threshold, selection, gate, CLI, artifact tests.
- `ML/reports/quantile_pred_adv_cap/validation_summary.json`
- `ML/reports/quantile_pred_adv_cap/test_summary.json`
- `ML/reports/quantile_pred_adv_cap/per_seed_summary.csv`
- `ML/reports/quantile_pred_adv_cap/yearly_breakdown.csv`
- `ML/reports/quantile_pred_adv_cap/run_metadata.json`
- `docs/reports/2026-04-15-quantile-pred-adv-cap.md`

## Files To Modify Only After Python Gate Passes

- `API/export_entry_path_v1_quantile_signals.py`
- `tests/test_export_entry_path_v1_quantile_signals.py`

## Files To Modify At Final Report Stage

- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`
- `wiki/research/execution-tracks.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Acceptance Rules

- No retraining.
- No quantile rule retuning.
- Threshold is computed on validation only.
- Test is evaluated only after validation gate pass.
- Validation gate:
  - `N_trades >= 30`
  - `PF > 2.0`
  - `negative_year_slices = 0`
  - filtered validation PF must be >= baseline validation PF
  - no seed-level validation PF collapse `<= 1.0`

## Task 1: Threshold And Gate Helpers

**Files:**
- Create: `ML/benchmark_quantile_pred_adv_cap.py`
- Create: `tests/test_benchmark_quantile_pred_adv_cap.py`

- [ ] **Step 1.1: Write failing helper tests**

Add tests for:

```python
import math

import pandas as pd

from ML.benchmark_quantile_pred_adv_cap import (
    compute_adv_threshold,
    filter_by_adv_cap,
    decide_adv_cap_gate,
)


def test_compute_adv_threshold_uses_validation_q75():
    frame = pd.DataFrame({"pred_adv_12_atr": [0.01, 0.02, 0.03, 0.04]})

    assert compute_adv_threshold(frame, quantile=0.75) == 0.0325


def test_filter_by_adv_cap_keeps_values_at_threshold():
    frame = pd.DataFrame({"pred_adv_12_atr": [0.01, 0.03, 0.04]})

    out = filter_by_adv_cap(frame, threshold=0.03)

    assert out["pred_adv_12_atr"].tolist() == [0.01, 0.03]


def test_decide_adv_cap_gate_rejects_support_and_seed_collapse():
    result = decide_adv_cap_gate(
        baseline_pf=8.0,
        filtered_pf=12.0,
        filtered_n_trades=29,
        filtered_negative_year_slices=0,
        seed_pf_values=[2.0, 0.9],
    )

    assert result["verdict"] == "gate_fail"
    assert "filtered_n_trades=29 < 30" in result["reasons"]
    assert "seed_pf_values_contain_pf<=1.0: [0.9]" in result["reasons"]
```

- [ ] **Step 1.2: Run tests and confirm failure**

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_pred_adv_cap.py -q
```

Expected: module missing.

- [ ] **Step 1.3: Implement helpers**

Implementation must:

- require `pred_adv_12_atr`;
- fail on null/NaN/non-finite threshold inputs;
- treat threshold as inclusive (`<=`);
- reject `None`, NaN, inf PF in gate.

- [ ] **Step 1.4: Run tests**

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_pred_adv_cap.py -q
```

- [ ] **Step 1.5: Commit**

```bash
git add ML/benchmark_quantile_pred_adv_cap.py tests/test_benchmark_quantile_pred_adv_cap.py
git commit -m "quantile: add pred-adv cap helpers"
```

## Task 2: Frozen Selection And Split Evaluation

**Files:**
- Modify: `ML/benchmark_quantile_pred_adv_cap.py`
- Modify: `tests/test_benchmark_quantile_pred_adv_cap.py`

- [ ] **Step 2.1: Add tests for frozen quantile selection plus adv cap**

Tests must prove:

- selected trades come from frozen quantile rule;
- `pred_adv_12_atr` is preserved from predictions;
- validation threshold is computed from selected validation trades;
- filtered trades apply inclusive cap.

- [ ] **Step 2.2: Implement selection path**

Reuse the existing frozen selection semantics from `ML.benchmark_quantile_ny_session.select_quantile_trades` or equivalent helpers. Do not copy unrelated session logic.

- [ ] **Step 2.3: Add yearly metrics and split evaluation**

Metrics:

- `n_trades`
- `wins`
- `losses`
- `gross_profit`
- `gross_loss`
- `pf`
- `win_rate`
- `mean_pnl_atr`
- `negative_year_slices`

- [ ] **Step 2.4: Run tests**

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_pred_adv_cap.py -q
```

- [ ] **Step 2.5: Commit**

```bash
git add ML/benchmark_quantile_pred_adv_cap.py tests/test_benchmark_quantile_pred_adv_cap.py
git commit -m "quantile: select pred-adv capped trades"
```

## Task 3: CLI Benchmark And Artifacts

**Files:**
- Modify: `ML/benchmark_quantile_pred_adv_cap.py`
- Modify: `tests/test_benchmark_quantile_pred_adv_cap.py`
- Create artifacts under `ML/reports/quantile_pred_adv_cap/`

- [ ] **Step 3.1: Add CLI tests**

Test requirements:

- CLI writes all artifacts;
- validation threshold appears in `run_metadata.json`;
- if validation gate fails, test summary is skipped;
- if validation gate passes in tiny fixture, test summary is evaluated.

- [ ] **Step 3.2: Implement `run_benchmark` and `main`**

CLI args:

```text
--validation-predictions
--test-predictions
--baseline-validation-predictions
--baseline-test-predictions
--selected-rule
--output-dir
--root-dir
--seeds
--quantile
```

Default quantile: `0.75`.

- [ ] **Step 3.3: Run tests**

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_pred_adv_cap.py -q
```

- [ ] **Step 3.4: Run canonical benchmark**

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_pred_adv_cap \
  --validation-predictions ML/reports/entry_path_v1_quantile_validation_predictions.csv \
  --test-predictions ML/reports/entry_path_v1_quantile_test_predictions.csv \
  --baseline-validation-predictions ML/reports/entry_path_v1_validation_predictions.csv \
  --baseline-test-predictions ML/reports/entry_path_test_predictions.csv \
  --selected-rule ML/reports/entry_path_v1_quantile_selected_rule.json \
  --output-dir ML/reports/quantile_pred_adv_cap \
  --root-dir /home/hohla/git/SoSimple/ML/reports/entry_path_v1_quantile_robustness \
  --seeds 7,17,42,77,123 \
  --quantile 0.75
```

- [ ] **Step 3.5: Commit**

```bash
git add ML/benchmark_quantile_pred_adv_cap.py tests/test_benchmark_quantile_pred_adv_cap.py
git add ML/reports/quantile_pred_adv_cap/validation_summary.json ML/reports/quantile_pred_adv_cap/test_summary.json ML/reports/quantile_pred_adv_cap/run_metadata.json
git add -f ML/reports/quantile_pred_adv_cap/per_seed_summary.csv ML/reports/quantile_pred_adv_cap/yearly_breakdown.csv
git commit -m "quantile: benchmark pred-adv cap filter"
```

## Task 4: Exporter Integration After Gate Pass Only

**Files:**
- Modify only if validation gate passes:
  - `API/export_entry_path_v1_quantile_signals.py`
  - `tests/test_export_entry_path_v1_quantile_signals.py`

- [ ] **Step 4.1: Stop if Python gate failed**

If validation gate failed, skip Task 4 and record that exporter/MT4 were not touched.

- [ ] **Step 4.2: Add optional exporter cap only if gate passed**

Default behavior must remain unchanged.

- [ ] **Step 4.3: Run exporter tests**

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py -q
```

- [ ] **Step 4.4: Commit**

```bash
git add API/export_entry_path_v1_quantile_signals.py tests/test_export_entry_path_v1_quantile_signals.py
git commit -m "quantile: add optional pred-adv export cap"
```

## Task 5: Report And Project Sync

**Files:**
- Create: `docs/reports/2026-04-15-quantile-pred-adv-cap.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

- [ ] **Step 5.1: Write final report**

Report must include:

- validation threshold;
- validation baseline vs filtered metrics;
- whether test ran or was skipped;
- multi-seed diagnostics;
- whether exporter/MT4 parity ran or was skipped;
- verdict.

- [ ] **Step 5.2: Sync changelog/handoff/roadmap/wiki**

Use report as source of truth.

- [ ] **Step 5.3: Run verification**

```bash
git diff --check
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_pred_adv_cap.py -q
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py generate
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py verify
```

- [ ] **Step 5.4: Commit**

```bash
git add CHANGELOG.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md docs/reports/2026-04-15-quantile-pred-adv-cap.md
git add wiki/index.md wiki/log.md wiki/research/execution-tracks.md wiki/REPO_integrity.md
git commit -m "docs: record quantile pred-adv cap verdict"
```

## Done Criteria

- Threshold was chosen only on validation.
- Test was evaluated only if validation gate passed.
- Report explicitly states accepted/rejected and why.
- Worktree is clean.
