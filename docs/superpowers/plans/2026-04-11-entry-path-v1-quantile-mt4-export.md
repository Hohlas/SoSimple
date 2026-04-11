# Entry Path v1 Quantile MT4 Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить воспроизводимый CLI, который выпускает `ml_signals.csv` для MT4 из frozen `entry_path_v1_quantile` winner без re-fit и ручной фильтрации.

**Architecture:** Новый узкий exporter в `API/` читает `seed_dir`, frozen rule JSON и prediction CSV выбранного split, применяет уже замороженное правило к полному временному ряду и пишет `time;signal`. Логика применения frozen rule переиспользует совместимую формулу из quantile benchmark, но не запускает benchmark и не выбирает winner заново.

**Tech Stack:** Python 3.12, pandas, pathlib, pytest

---

## File Map

### Read First
- `AGENTS.md`
- `docs/superpowers/specs/2026-04-11-entry-path-v1-quantile-mt4-export-design.md`
- `docs/MT/trading_strategy.md`
- `docs/MT/ml_signal_integration.md`
- `ML/benchmark_entry_path_v1_quantile_filter.py`
- `tests/README.md`
- `API/README.md`

### Files To Create
- `API/export_entry_path_v1_quantile_signals.py`
- `tests/test_export_entry_path_v1_quantile_signals.py`

### Files To Modify
- `docs/MT/ml_signal_integration.md`
- `API/README.md`
- `MODULE_INDEX.md`

### Optional Docs Update
- `docs/MT/trading_strategy.md` only if real code findings require another nuance update

---

### Task 1: Add Frozen Rule Export Helpers

**Files:**
- Test: `tests/test_export_entry_path_v1_quantile_signals.py`
- Create: `API/export_entry_path_v1_quantile_signals.py`

- [ ] **Step 1: Write the failing unit test for full-series export**

Create a synthetic `seed_dir` fixture with:
- `entry_path_v1_quantile_filter_selected_rule.json`
- `entry_path_v1_quantile_test_predictions.csv`

Test behavior:
- exporter writes full `time;signal` series
- rows outside winner mask become `0`
- rows inside winner mask keep original `signal`

- [ ] **Step 2: Run the unit test and verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py::test_export_signals_writes_full_series_from_frozen_rule -q
```

Expected:
- FAIL with `ModuleNotFoundError` or missing function

- [ ] **Step 3: Implement minimal frozen-rule export logic**

Add:
- CSV/rule loading
- conformal `lb/ub/width` reconstruction
- baseline gate reconstruction from `baseline_threshold`
- frozen winner rule application
- `time;signal` export

- [ ] **Step 4: Re-run the same test and verify it passes**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py::test_export_signals_writes_full_series_from_frozen_rule -q
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add API/export_entry_path_v1_quantile_signals.py tests/test_export_entry_path_v1_quantile_signals.py
git commit -m "feat: add quantile MT4 signal exporter"
```

---

### Task 2: Cover Rule Variants And Error Paths

**Files:**
- Modify: `tests/test_export_entry_path_v1_quantile_signals.py`
- Modify: `API/export_entry_path_v1_quantile_signals.py`

- [ ] **Step 1: Write failing tests for baseline rule and unknown rule**

Add tests that verify:
- `baseline` rule uses only `signal != 0 && pred_ret_24_dir_atr >= baseline_threshold`
- unknown rule raises `ValueError`

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py -q
```

Expected:
- FAIL on missing rule handling or wrong output

- [ ] **Step 3: Implement the minimal rule dispatch**

Support:
- `baseline`
- `lb_gt_0`
- `lb_gt_m`
- `lb_gt_m_width_le_w`

Reject everything else explicitly.

- [ ] **Step 4: Re-run the full test file and verify it passes**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py -q
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add API/export_entry_path_v1_quantile_signals.py tests/test_export_entry_path_v1_quantile_signals.py
git commit -m "test: cover quantile export rule handling"
```

---

### Task 3: Add CLI And MT4 Copy Mode

**Files:**
- Modify: `tests/test_export_entry_path_v1_quantile_signals.py`
- Modify: `API/export_entry_path_v1_quantile_signals.py`

- [ ] **Step 1: Write failing CLI tests for split selection and copy mode**

Add tests that verify:
- `--split validation|test` selects the correct CSV
- `--copy-to-mt4` writes to:
  - `MT/tester/files/ml_signals.csv`
  - `MT/MQL4/Files/ml_signals.csv`

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py -q
```

Expected:
- FAIL on missing CLI/copy behavior

- [ ] **Step 3: Implement CLI parsing and copy mode**

Add CLI args:
- `--seed-dir`
- `--split`
- `--output`
- `--copy-to-mt4`

Default behavior:
- always write `--output`
- if `--copy-to-mt4` is set, duplicate the same CSV into both MT4 locations

- [ ] **Step 4: Re-run the test file and verify it passes**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py -q
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add API/export_entry_path_v1_quantile_signals.py tests/test_export_entry_path_v1_quantile_signals.py
git commit -m "feat: add MT4 copy mode for quantile export"
```

---

### Task 4: Sync Docs And Registry

**Files:**
- Modify: `docs/MT/ml_signal_integration.md`
- Modify: `API/README.md`
- Modify: `MODULE_INDEX.md`
- Optional: `docs/MT/trading_strategy.md`

- [ ] **Step 1: Update operational docs**

Document:
- how to export `ml_signals.csv` from frozen quantile seed-run
- why MT4 score-filter must not replace quantile winner logic
- when to use minimal `time;signal`

- [ ] **Step 2: Update module registry**

Add the new exporter CLI to:
- `API/README.md`
- `MODULE_INDEX.md`

- [ ] **Step 3: Verify docs paths and examples**

Check examples and file paths for:
- `seed_dir`
- `MT/tester/files/ml_signals.csv`
- `MT/MQL4/Files/ml_signals.csv`

- [ ] **Step 4: Commit**

```bash
git add docs/MT/ml_signal_integration.md API/README.md MODULE_INDEX.md docs/MT/trading_strategy.md
git commit -m "docs: document quantile MT4 export flow"
```

---

### Task 5: Final Verification

**Files:**
- Verify all touched files

- [ ] **Step 1: Run targeted tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py -q
```

Expected:
- PASS

- [ ] **Step 2: Run a smoke export from a real seed**

Run:

```bash
./.venv/bin/python -m API.export_entry_path_v1_quantile_signals \
  --seed-dir ML/reports/entry_path_v1_quantile_robustness/seed_123 \
  --split test \
  --output /tmp/entry_path_v1_quantile_mt4.csv
```

Expected:
- CSV written successfully
- header is `time;signal`

- [ ] **Step 3: Summarize output**

Check:
- row count
- active signal count
- output path

- [ ] **Step 4: Commit**

```bash
git add API/export_entry_path_v1_quantile_signals.py tests/test_export_entry_path_v1_quantile_signals.py docs/MT/ml_signal_integration.md API/README.md MODULE_INDEX.md
git commit -m "feat: export frozen quantile signals for MT4"
```
