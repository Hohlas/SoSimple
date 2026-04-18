# Take/Skip Frequency Follow-Up Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Расширить follow-up benchmark вокруг уже найденного winner-а `take_skip_trailing_stop_v2` без нового обучения: проверить более широкий trailing-stop `X = 10 / 12` и найти область с большим числом сделок при `PF > 1`.

**Architecture:** План не запускает новый training cycle. Сначала расширяются continuous labels и binary targets для `X=10/12`, затем строится отдельный follow-up benchmark на уже готовых prediction CSV из `take_skip_trailing_stop_v2_matrix`. Отбор делается в двух режимах: quality-first и frequency-first, а итог выбирается по validation с frozen check на test.

**Tech Stack:** Python 3, pandas, NumPy, pytest, существующие `processing/label_signals.py`, `ML/take_skip_trailing_stop_v2_task.py`, `ML/benchmark_take_skip_trailing_stop_v2.py`, артефакты `ML/reports/take_skip_trailing_stop_v2_matrix/`.

---

## File Structure

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/reports/2026-04-18-multi-horizon-take-skip-feature-track.md`
- `ML/take_skip_trailing_stop_v2_task.py`
- `ML/benchmark_take_skip_trailing_stop_v2.py`
- `processing/label_signals.py`

### Files To Create

- `ML/benchmark_take_skip_trailing_stop_v2_followup.py`
- `tests/test_benchmark_take_skip_trailing_stop_v2_followup.py`
- `docs/reports/2026-04-18-take-skip-frequency-followup.md`

### Files To Modify

- `processing/label_signals.py`
- `tests/test_trailing_stop_target_labels.py`
- `ML/take_skip_trailing_stop_v2_task.py`
- `tests/test_take_skip_trailing_stop_v2_task.py`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`

### Files To Update At Stage Close

- `docs/reports/2026-04-18-take-skip-frequency-followup.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/execution-tracks.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

---

## Acceptance Rules

- Новый train не запускается.
- Новые prediction CSV не генерируются.
- Расширение labels ограничено `X = 10 / 12`.
- Follow-up benchmark обязан использовать уже готовые exports из `ML/reports/take_skip_trailing_stop_v2_matrix/`.
- Success criterion follow-up:
  - найти область с большим `trades_per_year`, чем у текущего winner-а;
  - при этом сохранить `PF > 1`;
  - и не получить явный развал по годам.

---

### Task 1: Extend Trailing-Stop Labels to X=10/12

**Files:**
- Modify: `processing/label_signals.py`
- Modify: `tests/test_trailing_stop_target_labels.py`

- [ ] **Step 1: Write the failing label test**

Extend expected columns with:

```python
'trail_12_pnl_atr_x10', 'trail_12_pnl_atr_x12',
'trail_24_pnl_atr_x10', 'trail_24_pnl_atr_x12',
'trail_48_pnl_atr_x10', 'trail_48_pnl_atr_x12',
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trailing_stop_target_labels.py -q
```

Expected: FAIL because `x10/x12` columns do not exist yet.

- [ ] **Step 3: Implement minimal label extension**

Update trailing-stop ATR grid so multi-horizon labels also compute:

```python
TRAILING_STOP_ATR_MULTIPLIERS_V2 = (2, 4, 8, 10, 12)
```

- [ ] **Step 4: Re-run test**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trailing_stop_target_labels.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add processing/label_signals.py tests/test_trailing_stop_target_labels.py
git commit -m "labels: extend trailing-stop grid to x10 x12"
```

---

### Task 2: Extend Take/Skip V2 Target Contract

**Files:**
- Modify: `ML/take_skip_trailing_stop_v2_task.py`
- Modify: `tests/test_take_skip_trailing_stop_v2_task.py`

- [ ] **Step 1: Write the failing task test**

Extend target expectations so `TAKE_SKIP_TRAILING_STOP_V2_COLUMNS` also includes:

```python
'take_12_x10', 'take_12_x12',
'take_24_x10', 'take_24_x12',
'take_48_x10', 'take_48_x12',
```

and the matching `TAKE_SKIP_TRUE_PNL_V2_COLUMNS`.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_trailing_stop_v2_task.py -q
```

Expected: FAIL because task contract still stops at `x8`.

- [ ] **Step 3: Implement minimal target extension**

Update the task constants and keep threshold logic unchanged:

```python
take = 1 if trail_pnl >= 0.5 else 0
```

- [ ] **Step 4: Re-run test**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_trailing_stop_v2_task.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/take_skip_trailing_stop_v2_task.py tests/test_take_skip_trailing_stop_v2_task.py
git commit -m "ml: extend take-skip v2 targets to x10 x12"
```

---

### Task 3: Build Follow-Up Benchmark for Frequency-First Search

**Files:**
- Create: `ML/benchmark_take_skip_trailing_stop_v2_followup.py`
- Create: `tests/test_benchmark_take_skip_trailing_stop_v2_followup.py`

- [ ] **Step 1: Write the failing benchmark tests**

Cover three contracts:

1. benchmark can load existing prediction CSV and score target columns `x8/x10/x12`;
2. benchmark emits both:
   - `quality_first`
   - `frequency_first`
3. `frequency_first` prefers higher `trades_per_year` among rows with `PF > 1` and `negative_year_slices = 0`.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_take_skip_trailing_stop_v2_followup.py -q
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement the benchmark**

Implement a small read-only benchmark over existing exports:

- input: ready-made `validation_predictions.csv` and `test_predictions.csv`
- candidate families:
  - `prob_ge_threshold`
  - `top_k_probability`
- threshold sweep should be denser in the lower-probability area than before, for example:

```python
prob_thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75]
top_k = [0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20]
```

- produce two picks on validation:
  - `quality_first`: sort by `PF`, then by stability
  - `frequency_first`: among rows with `PF > 1` and `negative_year_slices = 0`, maximize `trades_per_year`, then `PF`

- [ ] **Step 4: Re-run test**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_take_skip_trailing_stop_v2_followup.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/benchmark_take_skip_trailing_stop_v2_followup.py tests/test_benchmark_take_skip_trailing_stop_v2_followup.py
git commit -m "ml: add take-skip v2 frequency followup benchmark"
```

---

### Task 4: Run Read-Only Follow-Up on Existing Matrix Artifacts

**Files:**
- Use: `ML/reports/take_skip_trailing_stop_v2_matrix/`

- [ ] **Step 1: Regenerate labeled CSV locally if needed**

Only if the local split CSV do not yet contain `trail_*_x10/x12`.

- [ ] **Step 2: Run the follow-up benchmark**

Run the new module against the current best base family:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_take_skip_trailing_stop_v2_followup \
  --input-dir ML/reports/take_skip_trailing_stop_v2_matrix \
  --output-dir ML/reports/take_skip_trailing_stop_v2_followup
```

Expected: writes summary plus per-config follow-up tables.

- [ ] **Step 3: Inspect outputs**

Required questions:

- does `x10` or `x12` beat `x8` on frequency-first?
- can we get materially more trades while keeping `PF > 1`?
- does yearly stability survive?
- is profit concentration still acceptable?

- [ ] **Step 4: Commit artifacts if they are stage-worthy**

```bash
git add ML/reports/take_skip_trailing_stop_v2_followup
git commit -m "reports: add take-skip v2 frequency followup"
```

---

### Task 5: Close Stage If Follow-Up Gives a Useful Answer

**Files:**
- Create: `docs/reports/2026-04-18-take-skip-frequency-followup.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`

- [ ] **Step 1: Write the stage report**

Document:

- whether `x10/x12` improved anything;
- whether a lower-threshold or top-k region gave more trades with `PF > 1`;
- whether `seq50 + take_24_x8` remains the winner;
- whether the new best choice is “higher PF” or “more trades”.

- [ ] **Step 2: Update changelog and handoff**

Keep changelog short; handoff should name the new preferred candidate and next action.

- [ ] **Step 3: Update wiki ingest**

Update `wiki/research/execution-tracks.md`, `wiki/index.md`, `wiki/log.md`, then regenerate integrity:

```bash
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py generate
```

- [ ] **Step 4: Commit stage close**

```bash
git add docs/reports/2026-04-18-take-skip-frequency-followup.md CHANGELOG.md CONTEXT_HANDOFF.md wiki/research/execution-tracks.md wiki/index.md wiki/log.md wiki/REPO_integrity.md
git commit -m "docs: record take-skip frequency followup"
```

