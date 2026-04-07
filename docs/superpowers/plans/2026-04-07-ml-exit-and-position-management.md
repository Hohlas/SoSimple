# ML-Guided Exit And Position Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Усилить текущий `regression_updn` трек за счёт ML-логики выхода и аккуратного управления позицией, не меняя пока саму модель.

**Architecture:** Сначала строится Python-симулятор выходов на `validation`, который работает на уже существующих `up_3..dn_48` предсказаниях и сравнивает несколько политик закрытия. Только после этого лучший вариант переносится в `lib_ML_Signal.mqh` и в набор `extern`-параметров эксперта. Формат `ml_signals.csv` сохраняется: нужные отношения вычисляются в MQL4 “на лету”.

**Tech Stack:** Python 3.11+, pandas, numpy, pytest, MQL4

---

### Task 1: Offline-симулятор ML-выходов на validation

**Files:**
- Create: `API/exit_policy_research.py`
- Create: `tests/test_exit_policy_research.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_exit_policy_research.py
import pandas as pd
import API.exit_policy_research as epr


def test_close_on_reverse_signal_triggers_when_opposite_ratio_crosses_threshold():
    trade = pd.DataFrame({
        'bar': [0, 1, 2],
        'signal': [1, 1, 1],
        'ratio_up': [4.0, 2.8, 1.5],
        'ratio_dn': [0.2, 0.8, 2.6],
        'net_atr': [0.2, 0.6, 0.4],
    })

    policy = {'name': 'reverse_close', 'reverse_ratio': 2.5}
    out = epr.simulate_trade_exit(trade, policy)
    assert out['exit_bar'] == 2
    assert out['reason'] == 'reverse_ratio'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_exit_policy_research.py -q`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Add simulator primitives**

```python
# API/exit_policy_research.py
def simulate_trade_exit(trade_frame: pd.DataFrame, policy: dict) -> dict:
    for _, row in trade_frame.iterrows():
        if row['ratio_dn'] >= policy['reverse_ratio']:
            return {'exit_bar': int(row['bar']), 'reason': 'reverse_ratio'}
    return {'exit_bar': int(trade_frame['bar'].iloc[-1]), 'reason': 'timeout'}
```

- [ ] **Step 4: Add the first three candidate exit policies**

```python
POLICIES = [
    {'name': 'reverse_close', 'reverse_ratio': 2.0},
    {'name': 'weak_edge_close', 'keep_ratio_min': 1.6, 'min_hold_bars': 2},
    {'name': 'profit_guard_close', 'profit_start_atr': 1.0, 'keep_ratio_min': 1.8},
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_exit_policy_research.py -q`
Expected: PASS


### Task 2: Сравнение политик выхода на validation и жёсткие условия отбора

**Files:**
- Modify: `API/exit_policy_research.py`
- Modify: `tests/test_exit_policy_research.py`

- [ ] **Step 1: Add failing test for policy ranking**

```python
def test_rank_policies_sorts_by_pf_then_keeps_trade_floor():
    table = pd.DataFrame([
        {'policy': 'a', 'pf': 1.4, 'trades': 120},
        {'policy': 'b', 'pf': 1.6, 'trades': 18},
        {'policy': 'c', 'pf': 1.5, 'trades': 90},
    ])
    out = epr.rank_policies(table, min_trades=50)
    assert out.iloc[0]['policy'] == 'c'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_exit_policy_research.py -q`
Expected: FAIL with `AttributeError: module 'API.exit_policy_research' has no attribute 'rank_policies'`

- [ ] **Step 3: Implement policy ranking with support gates**

```python
def rank_policies(table: pd.DataFrame, min_trades: int = 50) -> pd.DataFrame:
    out = table[table['trades'] >= min_trades].copy()
    out = out.sort_values(['pf', 'trades'], ascending=[False, False]).reset_index(drop=True)
    return out
```

- [ ] **Step 4: Add validation-only CLI output**

```python
parser.add_argument('--split-profile', choices=['validation_research', 'test_final'], default='validation_research')
parser.add_argument('--min-trades', type=int, default=80)
```

- [ ] **Step 5: Run the research smoke command**

Run: `./.venv/bin/python -m API.exit_policy_research --split-profile validation_research`
Expected: prints ranked exit policies with `trades`, `PF`, `win_rate`, `avg_hold_bars`


### Task 3: Port the validated exit rule to MQL4

**Files:**
- Modify: `MT/MQL4/Include/lib_ML_Signal.mqh`
- Modify: `MT/MQL4/Experts/$o$imple.mq4`

- [ ] **Step 1: Add failing test for rule serialization**

```python
# tests/test_exit_policy_research.py
def test_render_mql_thresholds_returns_expected_names():
    cfg = epr.render_mql_thresholds({
        'reverse_ratio': 2.2,
        'keep_ratio_min': 1.7,
        'profit_start_atr': 1.0,
    })
    assert 'ML_ExitReverseRatio' in cfg
    assert 'ML_ExitKeepRatio' in cfg
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_exit_policy_research.py -q`
Expected: FAIL with `AttributeError`

- [ ] **Step 3: Add new expert inputs**

```c
// MT/MQL4/Experts/$o$imple.mq4
extern double ML_ExitReverseRatio = 2.0;
extern double ML_ExitKeepRatio    = 1.6;
extern double ML_ExitProfitATR    = 1.0;
extern int    ML_ExitMinHoldBars  = 2;
```

- [ ] **Step 4: Extend ML exit logic in MQL4**

```c
// MT/MQL4/Include/lib_ML_Signal.mqh
if (BUY.Typ == MARKET) {
   bool reverse_exit = (ratio_dn >= ML_ExitReverseRatio);
   bool weak_edge_exit = (BUY.Bars >= ML_ExitMinHoldBars && ratio_up < ML_ExitKeepRatio);
   bool profit_guard_exit = (BUY.Max - BUY.Val >= ML_ExitProfitATR * ATR && ratio_up < ML_ExitKeepRatio);
   if (reverse_exit || weak_edge_exit || profit_guard_exit) {
      CLOSE_BUY(1, "ML_Exit");
   }
}
```

- [ ] **Step 5: Keep reversal behavior only when opposite edge is truly strong**

```c
if (sig == -1 && BUY.Typ != NONE && ratio_dn >= ML_ExitReverseRatio) {
   CLOSE_BUY(1, "ML_Reversal");
}
```

- [ ] **Step 6: Validate the Python side**

Run: `./.venv/bin/python -m pytest tests/test_exit_policy_research.py -q`
Expected: PASS


### Task 4: Final confirmation and MT4 handoff

**Files:**
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Freeze the chosen exit policy from validation**

Run: `./.venv/bin/python -m API.exit_policy_research --split-profile validation_research --save-best ML/reports/frozen_exit_policy.json`
Expected: writes JSON with one chosen policy and its thresholds

- [ ] **Step 2: Run final Python confirmation on test**

Run: `./.venv/bin/python -m API.exit_policy_research --split-profile test_final --policy ML/reports/frozen_exit_policy.json`
Expected: one final summary table, no search loop

- [ ] **Step 3: Run MT4 test with the frozen inputs**

Run: `grep -n "ML_ExitReverseRatio" MT/MQL4/Experts/'$o$imple.mq4'`
Expected: new extern exists and is ready for tester optimization or fixed run
