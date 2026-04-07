# Triple Barrier Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Довести текущий `Triple Barrier` трек до логического конца: исправить грубую разметку, откалибровать вероятности, честно подобрать пороги на `validation`, сверить `Python ↔ MT4` и решить, годится ли этот трек для отдельного EA-режима.

**Architecture:** Сохраняется уже существующий стек `label_triple_barrier -> train --task triple_barrier -> generate_signals --task triple_barrier -> lib_ML_Signal_TB.mqh`, но четыре слабых места устраняются последовательно: разметка по реальному первому касанию, учёт неоднозначных баров, калибровка вероятностей и полная сверка с MT4. Решение о пригодности трека принимается только после финального прогона по замороженному правилу.

**Tech Stack:** Python 3.11+, pandas, numpy, torch, pytest, MQL4

---

### Task 1: Переделать TB-разметку на реальное первое касание

**Files:**
- Modify: `processing/label_signals.py`
- Modify: `processing/label_main.py`
- Create: `tests/test_triple_barrier_first_touch.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_triple_barrier_first_touch.py
import pandas as pd
import processing.label_signals as ls


def test_first_touch_prefers_sl_when_low_hits_before_high():
    bars = pd.DataFrame([
        {'open': 100.0, 'high': 101.0, 'low': 98.0, 'close': 99.0},
        {'open': 99.0, 'high': 104.0, 'low': 97.0, 'close': 103.0},
    ])
    out = ls.first_touch_barrier_outcome(
        bars=bars,
        direction=1,
        entry_price=100.0,
        sl_price=98.0,
        tp_price=104.0,
    )
    assert out == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_triple_barrier_first_touch.py -q`
Expected: FAIL with `AttributeError`

- [ ] **Step 3: Add first-touch helper**

```python
# processing/label_signals.py
def first_touch_barrier_outcome(bars, direction, entry_price, sl_price, tp_price):
    for _, row in bars.iterrows():
        hit_sl = row['low'] <= sl_price if direction == 1 else row['high'] >= sl_price
        hit_tp = row['high'] >= tp_price if direction == 1 else row['low'] <= tp_price
        if hit_sl and not hit_tp:
            return 0
        if hit_tp and not hit_sl:
            return 1
        if hit_sl and hit_tp:
            return 0 if abs(row['open'] - sl_price) <= abs(tp_price - row['open']) else 1
    return -1
```

- [ ] **Step 4: Replace current “both hit -> 0” shortcut in TB labels**

```python
# processing/label_signals.py
outcomes = []
for row_idx, row in df.iterrows():
    bars = ohlc_window_map[row['time']]
    outcome = first_touch_barrier_outcome(
        bars=bars,
        direction=1 if target_col.startswith('buy_') else -1,
        entry_price=row['entry_close'],
        sl_price=row['entry_close'] - sl_atr * row['ATR'] if target_col.startswith('buy_') else row['entry_close'] + sl_atr * row['ATR'],
        tp_price=row['entry_close'] + tp_atr * row['ATR'] if target_col.startswith('buy_') else row['entry_close'] - tp_atr * row['ATR'],
    )
    outcomes.append(outcome)

outcome_series = pd.Series(outcomes, index=df.index)
df[target_col] = (outcome_series == 1).astype(int)
df[f'{target_col}_timeout'] = (outcome_series == -1).astype(int)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_triple_barrier_first_touch.py -q`
Expected: PASS


### Task 2: Добавить калибровку вероятностей и честный выбор порога

**Files:**
- Modify: `ML/train.py`
- Modify: `ML/evaluate_test.py`
- Modify: `ML/threshold_analysis.py`
- Create: `tests/test_triple_barrier_calibration.py`

- [ ] **Step 1: Write the failing calibration test**

```python
# tests/test_triple_barrier_calibration.py
import numpy as np
import ML.threshold_analysis as ta


def test_expected_value_uses_calibrated_probability():
    p = np.array([0.70])
    out = ta.expected_value_from_probability(p, sl=2, tp=6)
    assert float(out[0]) == 3.4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_triple_barrier_calibration.py -q`
Expected: FAIL with `AttributeError`

- [ ] **Step 3: Add EV helper and calibration hook**

```python
# ML/threshold_analysis.py
def expected_value_from_probability(p, sl, tp):
    return p * tp - (1.0 - p) * sl
```

- [ ] **Step 4: Fit calibration on validation only**

```python
# ML/train.py
if triple_barrier:
    val_logits_path = REPORTS_DIR / 'tb_validation_logits.npy'
    np.save(val_logits_path, val_logits)
    val_targets_path = REPORTS_DIR / 'tb_validation_targets.npy'
    np.save(val_targets_path, val_targets)
```

```python
# ML/evaluate_test.py
if task == 'triple_barrier':
    calibrator = joblib.load(REPORTS_DIR / 'tb_probability_calibrator.joblib')
    y_proba = calibrator.transform(y_proba.reshape(-1, 1)).reshape(y_proba.shape)
```

- [ ] **Step 5: Replace “max PF at any theta” with support-gated search**

```python
# ML/threshold_analysis.py
best = target_df[
    (target_df['trades'] >= 80) &
    (target_df['win_rate'] >= 0.35)
].sort_values(['pf', 'trades'], ascending=[False, False]).iloc[0]
```

- [ ] **Step 6: Run tests**

Run: `./.venv/bin/python -m pytest tests/test_triple_barrier_calibration.py -q`
Expected: PASS


### Task 3: Усилить выбор сделки и режим “не торговать”

**Files:**
- Modify: `API/generate_signals.py`
- Modify: `tests/test_generate_signals_research.py`
- Modify: `MT/MQL4/Include/lib_ML_Signal_TB.mqh`

- [ ] **Step 1: Add failing test for no-trade gate**

```python
def test_tb_preds_to_signals_returns_flat_when_ev_too_small():
    logits = [[0.1] * 12]
    out = gs.tb_preds_to_signals(np.array(logits), theta=0.5, min_ev=0.5)
    assert int(out['signal'].iloc[0]) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_generate_signals_research.py -q`
Expected: FAIL with unexpected keyword argument `min_ev`

- [ ] **Step 3: Add explicit no-trade threshold**

```python
# API/generate_signals.py
def tb_preds_to_signals(y_pred_logits, theta, min_ev=0.0):
    proba = 1.0 / (1.0 + np.exp(-y_pred_logits))
    n = len(proba)
    signals = np.zeros(n, dtype=int)
    sl_atrs = np.zeros(n, dtype=float)
    tp_atrs = np.zeros(n, dtype=float)
    probs = np.zeros(n, dtype=float)
    evs = np.zeros(n, dtype=float)
    for row_idx in range(n):
        best_ev = -np.inf
        best_signal = 0
        best_sl = 0.0
        best_tp = 0.0
        best_prob = 0.0
        for i, name in enumerate(TB_TARGET_NAMES):
            p = proba[row_idx, i]
            if p <= theta:
                continue
            parts = name.split('_')
            direction = 1 if parts[0] == 'buy' else -1
            sl = int(parts[1][2:])
            tp = int(parts[2][2:])
            ev = p * tp - (1 - p) * sl
            if ev > best_ev:
                best_ev = ev
                best_signal = direction
                best_sl = float(sl)
                best_tp = float(tp)
                best_prob = p
        if best_ev < min_ev:
            best_signal = 0
            best_sl = 0.0
            best_tp = 0.0
            best_prob = 0.0
```

- [ ] **Step 4: Carry `prob` and `ev` through to MT4 diagnostics**

```c
// MT/MQL4/Include/lib_ML_Signal_TB.mqh
Print(Mgc, ":: TB BUY prob=", DoubleToString(TB_Prob[idx],3),
      " ev=", DoubleToString(TB_EV[idx],2),
      " SL=", DoubleToString(TB_SL[idx],1), "ATR",
      " TP=", DoubleToString(TB_TP[idx],1), "ATR",
      " bar=", TimeToString(Time[bar]));
```

- [ ] **Step 5: Run the updated tests**

Run: `./.venv/bin/python -m pytest tests/test_generate_signals_research.py -q`
Expected: PASS


### Task 4: Полная сверка Python ↔ MT4 для TB-трека

**Files:**
- Modify: `statistics/signal_tracer.py`
- Create: `tests/test_signal_tracer_tb.py`
- Modify: `docs/statistics/signal_tracer.py.md`

- [ ] **Step 1: Write the failing test for TB log parsing**

```python
# tests/test_signal_tracer_tb.py
import statistics.signal_tracer as st


def test_parse_tb_log_line_extracts_sl_tp_prob():
    line = "TB BUY prob=0.731 ev=3.42 SL=2.0ATR TP=6.0ATR bar=2025.01.03 04:00"
    out = st.parse_tb_signal_line(line)
    assert out['prob'] == 0.731
    assert out['sl_atr'] == 2.0
    assert out['tp_atr'] == 6.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_signal_tracer_tb.py -q`
Expected: FAIL with `AttributeError`

- [ ] **Step 3: Add TB-specific tracer parsing**

```python
# statistics/signal_tracer.py
def parse_tb_signal_line(line: str) -> dict:
    return {
        'prob': float(re.search(r'prob=([0-9.]+)', line).group(1)),
        'ev': float(re.search(r'ev=([0-9.]+)', line).group(1)),
        'sl_atr': float(re.search(r'SL=([0-9.]+)ATR', line).group(1)),
        'tp_atr': float(re.search(r'TP=([0-9.]+)ATR', line).group(1)),
        'bar_time': re.search(r'bar=([0-9. :]+)$', line).group(1),
    }
```

- [ ] **Step 4: Add Python-vs-MT4 reconciliation report for TB**

Run: `./.venv/bin/python -m API.generate_signals --task triple_barrier --theta 0.6`
Expected: fresh `ml_signals_tb.csv`

Run: `./.venv/bin/python -m pytest tests/test_signal_tracer_tb.py -q`
Expected: PASS


### Task 5: Freeze the TB verdict

**Files:**
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `CHANGELOG.md`
- Create: `docs/reports/2026-04-07-triple-barrier-hardening.md`

- [ ] **Step 1: Train and select the hardened TB rule on validation**

Run: `./.venv/bin/python -m ML.train --model transformer --task triple_barrier --epochs 50 --seed 42 --encoder_ckpt ML/checkpoints/transformer_updn_best.pt`
Expected: new `transformer_tb_best.pt`

Run: `./.venv/bin/python -m ML.threshold_analysis --task triple_barrier --model transformer`
Expected: support-gated threshold report, not just raw max-PF rows

- [ ] **Step 2: Confirm only once on test**

Run: `./.venv/bin/python -m ML.evaluate_test --task triple_barrier --model transformer`
Expected: one final OOS TB report with calibrated probabilities

- [ ] **Step 3: Run MT4 verification**

Run: `grep -n "TB BUY" MT/MQL4/Include/lib_ML_Signal_TB.mqh`
Expected: TB diagnostics include `prob` and `ev`

- [ ] **Step 4: Write the decision**

```md
### Decision
- Keep `Triple Barrier` as a separate EA mode only if calibrated validation-selected rule stays profitable on final `test` and MT4 gap remains operationally small.
- Stop the branch if test profit disappears after first-touch relabeling or if Python-to-MT4 gap remains too wide for deployment confidence.
- Record the exact frozen threshold, the chosen `SL/TP` pair, and the final MT4/Python comparison table in the report.
```
