# MT4-Execution Trade Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить точную оффлайн-модель сделки под правила MT4 и поверх уже замороженного базового варианта `A @ 7.5%` сделать новый слой `торговать / не торговать`, который выбирается только на `validation` и идёт на `test` только после заморозки победителя.

**Architecture:** План не заменяет текущий `entry_path_v1` и не отменяет уже замороженный базовый вариант `A @ 7.5%`. Сначала строится точная модель сделки по тем же правилам, что и в MT4: вход на следующем баре, одна открытая позиция, удержание, блокировка новых сигналов и причины закрытия. Затем поверх уже отобранных `A`-сигналов строится простой слой `торговать / не торговать`, который сравнивает несколько простых правил и простую линейную модель. Победитель замораживается на `validation`, один раз проверяется на `test`, а затем из него выпускается рабочий CSV для MT4.

**Tech Stack:** Python 3.11+, pandas, numpy, scikit-learn, pytest

**File Map:**
- Create: `API/trade_simulator.py` — оффлайн-модель сделки по правилам MT4
- Modify: `statistics/signal_tracer.py` — сверка журнала Python и MT4
- Create: `ML/execution_trade_filter.py` — слой `торговать / не торговать` поверх замороженного `A`
- Create: `ML/benchmark_execution_trade_filter.py` — выбор победителя только на `validation`
- Create: `API/export_execution_filtered_signals.py` — выпуск финального CSV для MT4 по замороженному правилу
- Create: `tests/test_trade_simulator.py`
- Create: `tests/test_trade_simulator_reconcile.py`
- Create: `tests/test_execution_trade_filter.py`
- Create: `tests/test_export_execution_filtered_signals.py`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Create: `docs/reports/2026-04-09-mt4-execution-trade-selection.md`

---

### Task 1: Собрать точную оффлайн-модель сделки под правила MT4

**Files:**
- Create: `API/trade_simulator.py`
- Create: `tests/test_trade_simulator.py`

- [ ] **Step 1: Write the failing test for next-bar entry and one-open-position**

```python
# tests/test_trade_simulator.py
import pandas as pd
import API.trade_simulator as ts


def test_simulate_signal_frame_opens_on_next_bar_and_blocks_new_signals():
    frame = pd.DataFrame({
        'time': pd.to_datetime([
            '2025-01-01 00:00',
            '2025-01-01 01:00',
            '2025-01-01 02:00',
            '2025-01-01 03:00',
            '2025-01-01 04:00',
        ]),
        'signal': [1, 1, 0, -1, 0],
        'open': [100.0, 101.0, 103.0, 102.0, 99.0],
        'high': [101.0, 104.0, 104.0, 103.0, 100.0],
        'low': [99.0, 100.0, 101.0, 98.0, 97.0],
        'close': [100.0, 103.0, 102.0, 99.0, 98.0],
        'atr14': [1.0, 1.0, 1.0, 1.0, 1.0],
    })

    config = ts.TradeSimConfig(max_hold_bars=2, spread_points=0.0, allow_reversal=False)
    out = ts.simulate_signal_frame(frame, config)

    assert len(out) == 2
    assert out.loc[0, 'signal_time'] == pd.Timestamp('2025-01-01 00:00')
    assert out.loc[0, 'entry_time'] == pd.Timestamp('2025-01-01 01:00')
    assert out.loc[0, 'blocked_signals'] == 1
    assert out.loc[0, 'exit_reason'] == 'timeout'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_trade_simulator.py -q`
Expected: FAIL with `ModuleNotFoundError` or `AttributeError`

- [ ] **Step 3: Add the minimal trade simulator core**

```python
# API/trade_simulator.py
from dataclasses import dataclass

import pandas as pd


@dataclass
class TradeSimConfig:
    max_hold_bars: int = 12
    spread_points: float = 0.0
    allow_reversal: bool = False


def simulate_signal_frame(frame: pd.DataFrame, config: TradeSimConfig) -> pd.DataFrame:
    ordered = frame.sort_values('time').reset_index(drop=True).copy()
    trades = []
    idx = 0

    while idx < len(ordered) - 1:
        signal = int(ordered.loc[idx, 'signal'])
        if signal == 0:
            idx += 1
            continue

        entry_idx = idx + 1
        exit_idx = min(entry_idx + config.max_hold_bars - 1, len(ordered) - 1)
        atr = float(ordered.loc[idx, 'atr14']) or 1.0
        entry_price = float(ordered.loc[entry_idx, 'open'])
        exit_price = float(ordered.loc[exit_idx, 'close'])
        pnl_atr = (exit_price - entry_price) / atr if signal == 1 else (entry_price - exit_price) / atr

        trades.append({
            'signal_time': ordered.loc[idx, 'time'],
            'entry_time': ordered.loc[entry_idx, 'time'],
            'exit_time': ordered.loc[exit_idx, 'time'],
            'signal': signal,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'exit_reason': 'timeout',
            'blocked_signals': int((ordered.loc[idx + 1:exit_idx, 'signal'] != 0).sum()),
            'pnl_atr': pnl_atr,
        })
        idx = exit_idx + 1

    return pd.DataFrame(trades)
```

- [ ] **Step 4: Add a second failing test for reversal closing**

```python
def test_simulate_signal_frame_closes_on_opposite_signal_when_reversal_is_allowed():
    frame = pd.DataFrame({
        'time': pd.to_datetime([
            '2025-01-01 00:00',
            '2025-01-01 01:00',
            '2025-01-01 02:00',
            '2025-01-01 03:00',
        ]),
        'signal': [1, 0, -1, 0],
        'open': [100.0, 101.0, 102.0, 99.0],
        'high': [101.0, 103.0, 103.0, 100.0],
        'low': [99.0, 100.0, 98.0, 97.0],
        'close': [100.0, 102.0, 99.0, 98.0],
        'atr14': [1.0, 1.0, 1.0, 1.0],
    })

    config = ts.TradeSimConfig(max_hold_bars=5, spread_points=0.0, allow_reversal=True)
    out = ts.simulate_signal_frame(frame, config)

    assert out.loc[0, 'exit_reason'] == 'reverse_signal'
    assert out.loc[0, 'exit_time'] == pd.Timestamp('2025-01-01 02:00')
```

- [ ] **Step 5: Extend the simulator with reversal close**

```python
def _find_reverse_exit(ordered: pd.DataFrame, start_idx: int, stop_idx: int, signal: int) -> int | None:
    reverse_rows = ordered.index[
        (ordered.index >= start_idx)
        & (ordered.index <= stop_idx)
        & (ordered['signal'].astype(int) == -signal)
    ]
    return int(reverse_rows[0]) if len(reverse_rows) > 0 else None


def simulate_signal_frame(frame: pd.DataFrame, config: TradeSimConfig) -> pd.DataFrame:
    ordered = frame.sort_values('time').reset_index(drop=True).copy()
    trades = []
    idx = 0

    while idx < len(ordered) - 1:
        signal = int(ordered.loc[idx, 'signal'])
        if signal == 0:
            idx += 1
            continue

        entry_idx = idx + 1
        exit_limit = min(entry_idx + config.max_hold_bars - 1, len(ordered) - 1)
        exit_idx = exit_limit
        exit_reason = 'timeout'

        if config.allow_reversal:
            reverse_idx = _find_reverse_exit(ordered, entry_idx, exit_limit, signal)
            if reverse_idx is not None:
                exit_idx = reverse_idx
                exit_reason = 'reverse_signal'

        atr = float(ordered.loc[idx, 'atr14']) or 1.0
        entry_price = float(ordered.loc[entry_idx, 'open'])
        exit_price = float(ordered.loc[exit_idx, 'close'])
        pnl_atr = (exit_price - entry_price) / atr if signal == 1 else (entry_price - exit_price) / atr

        trades.append({
            'signal_time': ordered.loc[idx, 'time'],
            'entry_time': ordered.loc[entry_idx, 'time'],
            'exit_time': ordered.loc[exit_idx, 'time'],
            'signal': signal,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'blocked_signals': int((ordered.loc[idx + 1:exit_idx, 'signal'] != 0).sum()),
            'pnl_atr': pnl_atr,
        })
        idx = exit_idx + 1

    return pd.DataFrame(trades)
```

- [ ] **Step 6: Run tests to verify the simulator passes**

Run: `./.venv/bin/python -m pytest tests/test_trade_simulator.py -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add API/trade_simulator.py tests/test_trade_simulator.py
git commit -m "feat: add MT4-style trade simulator core"
```


### Task 2: Сверить Python-журнал и MT4-журнал по одним и тем же правилам

**Files:**
- Modify: `API/trade_simulator.py`
- Modify: `statistics/signal_tracer.py`
- Create: `tests/test_trade_simulator_reconcile.py`

- [ ] **Step 1: Write the failing reconciliation test**

```python
# tests/test_trade_simulator_reconcile.py
import pandas as pd
import statistics.signal_tracer as st


def test_compare_execution_ledgers_counts_entry_matches_and_misses():
    sim = pd.DataFrame([
        {'entry_time': pd.Timestamp('2025-01-01 01:00'), 'signal': 1, 'exit_reason': 'timeout'},
        {'entry_time': pd.Timestamp('2025-01-01 05:00'), 'signal': -1, 'exit_reason': 'reverse_signal'},
    ])
    mt4 = pd.DataFrame([
        {'open_time': pd.Timestamp('2025-01-01 01:00'), 'signal': 1},
        {'open_time': pd.Timestamp('2025-01-01 06:00'), 'signal': -1},
    ])

    out = st.compare_execution_ledgers(sim, mt4)

    assert out['matched_entries'] == 1
    assert out['python_only'] == 1
    assert out['mt4_only'] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_trade_simulator_reconcile.py -q`
Expected: FAIL with `AttributeError`

- [ ] **Step 3: Add ledger comparison in `statistics/signal_tracer.py`**

```python
# statistics/signal_tracer.py
def compare_execution_ledgers(sim_trades: pd.DataFrame, mt4_trades: pd.DataFrame) -> dict:
    sim_keys = set(zip(pd.to_datetime(sim_trades['entry_time']), sim_trades['signal'].astype(int)))
    mt4_keys = set(zip(pd.to_datetime(mt4_trades['open_time']), mt4_trades['signal'].astype(int)))
    return {
        'matched_entries': len(sim_keys & mt4_keys),
        'python_only': len(sim_keys - mt4_keys),
        'mt4_only': len(mt4_keys - sim_keys),
    }
```

- [ ] **Step 4: Add CLI export to the simulator**

```python
# API/trade_simulator.py
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='MT4-style offline trade simulator')
    parser.add_argument('--signals', required=True)
    parser.add_argument('--ohlc', required=True)
    parser.add_argument('--csv-out', required=True)
    parser.add_argument('--max-hold-bars', type=int, default=12)
    parser.add_argument('--allow-reversal', action='store_true')
    args = parser.parse_args()

    signals = pd.read_csv(args.signals, sep=';')
    ohlc = pd.read_csv(args.ohlc, sep=';')
    frame = signals.merge(ohlc[['time', 'open', 'high', 'low', 'close', 'atr14']], on='time', how='inner')
    out = simulate_signal_frame(
        frame,
        TradeSimConfig(max_hold_bars=args.max_hold_bars, allow_reversal=args.allow_reversal),
    )
    Path(args.csv_out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.csv_out, sep=';', index=False)
```

- [ ] **Step 5: Run tests to verify the comparison passes**

Run: `./.venv/bin/python -m pytest tests/test_trade_simulator.py tests/test_trade_simulator_reconcile.py -q`
Expected: PASS

- [ ] **Step 6: Run the first parity smoke command**

Run: `./.venv/bin/python -m API.trade_simulator --signals MT/MQL4/Files/ml_signals.csv --ohlc DATA/XAUUSD_H1_OHLC.csv --csv-out ML/reports/trade_simulator_legacy.csv --max-hold-bars 12 --allow-reversal`
Expected: writes `ML/reports/trade_simulator_legacy.csv` with `signal_time`, `entry_time`, `exit_time`, `exit_reason`, `pnl_atr`

- [ ] **Step 7: Commit**

```bash
git add API/trade_simulator.py statistics/signal_tracer.py tests/test_trade_simulator.py tests/test_trade_simulator_reconcile.py
git commit -m "feat: add simulator parity and ledger comparison"
```


### Task 3: Построить таблицу сделок поверх замороженного `A @ 7.5%`

**Files:**
- Create: `ML/execution_trade_filter.py`
- Create: `tests/test_execution_trade_filter.py`

- [ ] **Step 1: Write the failing test for joining `A`-сигналы и журнал сделок**

```python
# tests/test_execution_trade_filter.py
import pandas as pd
import ML.execution_trade_filter as etf


def test_build_trade_frame_from_a_selector_keeps_only_closed_a_trades():
    predictions = pd.DataFrame({
        'time': pd.to_datetime(['2025-01-01 00:00', '2025-01-01 01:00']),
        'signal': [1, -1],
        'pred_ret_24_dir_atr': [0.40, 0.10],
        'pred_ret_12_dir_atr': [0.20, -0.05],
        'pred_fav_12_atr': [1.6, 0.8],
        'pred_adv_12_atr': [0.4, 0.9],
        'pred_fav_24_atr': [2.1, 1.0],
        'pred_adv_24_atr': [0.6, 1.1],
        'pred_path_6_prob_pos': [0.7, 0.2],
        'pred_path_6_prob_neg': [0.1, 0.5],
    })
    trades = pd.DataFrame({
        'signal_time': pd.to_datetime(['2025-01-01 00:00']),
        'pnl_atr': [1.25],
        'exit_reason': ['timeout'],
        'blocked_signals': [0],
    })

    out = etf.build_trade_research_frame(predictions, trades)

    assert len(out) == 1
    assert out.loc[0, 'take_label'] == 1
    assert out.loc[0, 'edge_12'] == 1.2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_execution_trade_filter.py -q`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Add the research-table builder**

```python
# ML/execution_trade_filter.py
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

FEATURE_COLUMNS = [
    'pred_ret_24_dir_atr',
    'pred_ret_12_dir_atr',
    'pred_fav_12_atr',
    'pred_adv_12_atr',
    'pred_fav_24_atr',
    'pred_adv_24_atr',
    'pred_path_6_prob_pos',
    'pred_path_6_prob_neg',
]


def build_trade_research_frame(predictions: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    keep = predictions[['time', 'signal', *FEATURE_COLUMNS]].copy()
    merged = keep.merge(trades[['signal_time', 'pnl_atr', 'exit_reason', 'blocked_signals']], left_on='time', right_on='signal_time', how='inner')
    merged['take_label'] = (merged['pnl_atr'] > 0).astype(int)
    merged['edge_12'] = merged['pred_fav_12_atr'] - merged['pred_adv_12_atr']
    merged['edge_24'] = merged['pred_fav_24_atr'] - merged['pred_adv_24_atr']
    merged['path_edge_6'] = merged['pred_path_6_prob_pos'] - merged['pred_path_6_prob_neg']
    return merged
```

- [ ] **Step 4: Add a second failing test for the simple linear selector**

```python
def test_apply_linear_selector_score_uses_validation_fit_only():
    validation = pd.DataFrame({
        'pred_ret_24_dir_atr': [0.9, 0.8, -0.3, -0.4],
        'pred_ret_12_dir_atr': [0.6, 0.7, -0.1, -0.2],
        'edge_12': [1.5, 1.2, -0.4, -0.6],
        'edge_24': [2.0, 1.8, -0.5, -0.7],
        'path_edge_6': [0.5, 0.4, -0.2, -0.1],
        'take_label': [1, 1, 0, 0],
    })
    apply_frame = validation.iloc[[0, 2]].copy()

    model = etf.fit_linear_selector(validation)
    score = etf.apply_linear_selector(apply_frame, model)

    assert score[0] > score[1]
```

- [ ] **Step 5: Add the simple linear selector**

```python
LINEAR_FEATURES = ['pred_ret_24_dir_atr', 'pred_ret_12_dir_atr', 'edge_12', 'edge_24', 'path_edge_6']


def fit_linear_selector(frame: pd.DataFrame) -> dict:
    model = LogisticRegression(max_iter=2000, class_weight='balanced', random_state=42)
    X = frame[LINEAR_FEATURES].to_numpy(dtype=np.float64)
    y = frame['take_label'].to_numpy(dtype=np.int64)
    model.fit(X, y)
    return {
        'feature_columns': LINEAR_FEATURES,
        'coef': model.coef_[0].astype(float).tolist(),
        'intercept': float(model.intercept_[0]),
    }


def apply_linear_selector(frame: pd.DataFrame, fitted: dict) -> np.ndarray:
    X = frame[fitted['feature_columns']].to_numpy(dtype=np.float64)
    raw = X @ np.asarray(fitted['coef'], dtype=np.float64) + fitted['intercept']
    return 1.0 / (1.0 + np.exp(-raw))
```

- [ ] **Step 6: Run tests to verify the trade table and selector pass**

Run: `./.venv/bin/python -m pytest tests/test_execution_trade_filter.py -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add ML/execution_trade_filter.py tests/test_execution_trade_filter.py
git commit -m "feat: add execution-aware trade filter research frame"
```


### Task 4: Выбрать победителя только на `validation` и только потом один раз проверить на `test`

**Files:**
- Create: `ML/benchmark_execution_trade_filter.py`
- Modify: `ML/execution_trade_filter.py`
- Modify: `tests/test_execution_trade_filter.py`

- [ ] **Step 1: Write the failing benchmark test**

```python
def test_pick_working_selector_prefers_stable_variant_over_tiny_tail():
    table = pd.DataFrame([
        {'candidate': 'tiny', 'pf': 4.5, 'trades': 8, 'stability_ratio': 0.0},
        {'candidate': 'stable', 'pf': 1.8, 'trades': 34, 'stability_ratio': 1.0},
    ])

    best = etf.pick_working_selector(table, min_trades=30, min_stability_ratio=0.75)

    assert best['candidate'] == 'stable'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_execution_trade_filter.py -q`
Expected: FAIL with `AttributeError`

- [ ] **Step 3: Add selector ranking and frozen-policy serialization**

```python
# ML/execution_trade_filter.py
def pick_working_selector(table: pd.DataFrame, min_trades: int = 30, min_stability_ratio: float = 0.75) -> pd.Series:
    live = table[(table['trades'] >= min_trades) & (table['stability_ratio'] >= min_stability_ratio)].copy()
    live = live.sort_values(['pf', 'stability_ratio', 'trades'], ascending=[False, False, False]).reset_index(drop=True)
    if live.empty:
        raise ValueError('No selector passed the shared trade floor and stability rule.')
    return live.iloc[0]
```

- [ ] **Step 4: Build the validation-only benchmark CLI**

```python
# ML/benchmark_execution_trade_filter.py
parser.add_argument('--mode', choices=['validation_research', 'test_final'], default='validation_research')
parser.add_argument('--validation-pred', required=True)
parser.add_argument('--validation-trades', required=True)
parser.add_argument('--test-pred', required=True)
parser.add_argument('--test-trades', required=True)
parser.add_argument('--policy', default='')
parser.add_argument('--output-dir', default='ML/reports')
parser.add_argument('--min-trades', type=int, default=30)
parser.add_argument('--min-stability-ratio', type=float, default=0.75)
```

- [ ] **Step 5: Implement the four candidate families**

```python
# ML/benchmark_execution_trade_filter.py
from ML.entry_path_trade_filter import apply_candidate_b_score, build_candidate_a_score, fit_candidate_b_score
from ML.execution_trade_filter import apply_linear_selector, build_trade_research_frame, fit_linear_selector

# candidates on validation trades:
# 1. keep_all_a        -> score = 1 for every A-trade
# 2. a_score           -> score = pred_ret_24_dir_atr
# 3. b_score           -> score from existing composite B
# 4. linear_full       -> score from validation-fitted linear selector
```

- [ ] **Step 6: Rebuild fresh prediction CSVs for the base layer**

Run: `./.venv/bin/python -m API.generate_signals --task entry_path_v1 --research-out-prefix ML/reports/trade_execution_base`
Expected: writes `ML/reports/trade_execution_base_validation_predictions.csv` and `ML/reports/trade_execution_base_test_predictions.csv`

- [ ] **Step 7: Run simulator on the frozen `A @ 7.5%` base layer**

Run: `./.venv/bin/python -m API.trade_simulator --signals MT/MQL4/Files/ml_signals.csv --ohlc DATA/XAUUSD_H1_OHLC.csv --csv-out ML/reports/trade_simulator_legacy.csv --max-hold-bars 12 --allow-reversal`
Expected: smoke pass for the simulator CLI before it is reused in the new benchmark

- [ ] **Step 8: Run the new validation-only benchmark**

Run: `./.venv/bin/python -m ML.benchmark_execution_trade_filter --mode validation_research --validation-pred ML/reports/trade_execution_base_validation_predictions.csv --validation-trades ML/reports/trade_simulator_validation.csv --test-pred ML/reports/trade_execution_base_test_predictions.csv --test-trades ML/reports/trade_simulator_test.csv --output-dir ML/reports`
Expected: writes `ML/reports/execution_trade_filter_validation_summary.csv`, `ML/reports/execution_trade_filter_report.md`, and `ML/reports/frozen_execution_trade_filter.json` only if a winner exists

- [ ] **Step 9: Run exactly one final test check**

Run: `./.venv/bin/python -m ML.benchmark_execution_trade_filter --mode test_final --policy ML/reports/frozen_execution_trade_filter.json --validation-pred ML/reports/trade_execution_base_validation_predictions.csv --validation-trades ML/reports/trade_simulator_validation.csv --test-pred ML/reports/trade_execution_base_test_predictions.csv --test-trades ML/reports/trade_simulator_test.csv --output-dir ML/reports`
Expected: writes one final `ML/reports/execution_trade_filter_test.md`; if frozen JSON is missing, STOP and do not search on `test`

- [ ] **Step 10: Run tests to verify the benchmark logic passes**

Run: `./.venv/bin/python -m pytest tests/test_execution_trade_filter.py -q`
Expected: PASS

- [ ] **Step 11: Commit**

```bash
git add ML/execution_trade_filter.py ML/benchmark_execution_trade_filter.py tests/test_execution_trade_filter.py
git commit -m "feat: add validation-first execution trade filter benchmark"
```


### Task 5: Выпустить финальный CSV для MT4 и обновить handoff

**Files:**
- Create: `API/export_execution_filtered_signals.py`
- Create: `tests/test_export_execution_filtered_signals.py`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Create: `docs/reports/2026-04-09-mt4-execution-trade-selection.md`

- [ ] **Step 1: Write the failing export test**

```python
# tests/test_export_execution_filtered_signals.py
import pandas as pd
import API.export_execution_filtered_signals as exf


def test_apply_frozen_selector_sets_signal_to_zero_below_threshold():
    frame = pd.DataFrame({
        'time': ['2025.01.01 00:00', '2025.01.01 01:00'],
        'signal': [1, -1],
        'pred_ret_24_dir_atr': [0.6, -0.1],
        'pred_ret_12_dir_atr': [0.4, -0.1],
        'pred_fav_12_atr': [1.0, 0.5],
        'pred_adv_12_atr': [0.2, 0.8],
        'pred_fav_24_atr': [1.5, 0.6],
        'pred_adv_24_atr': [0.3, 0.9],
        'pred_path_6_prob_pos': [0.7, 0.2],
        'pred_path_6_prob_neg': [0.1, 0.4],
    })
    policy = {
        'winner': {
            'candidate': 'a_score',
            'score_threshold': 0.0,
        }
    }

    out = exf.apply_frozen_selector(frame, policy)

    assert out['signal'].tolist() == [1, 0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_export_execution_filtered_signals.py -q`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Add the export tool**

```python
# API/export_execution_filtered_signals.py
import json
from pathlib import Path

import pandas as pd

from ML.entry_path_trade_filter import build_candidate_a_score, apply_candidate_b_score
from ML.execution_trade_filter import apply_linear_selector, build_trade_research_frame


def apply_frozen_selector(frame: pd.DataFrame, policy: dict) -> pd.DataFrame:
    winner = policy['winner']
    candidate = winner['candidate']
    threshold = float(winner['score_threshold'])

    if candidate == 'keep_all_a':
        score = pd.Series(1.0, index=frame.index)
    elif candidate == 'a_score':
        score = pd.Series(build_candidate_a_score(frame), index=frame.index)
    elif candidate == 'b_score':
        score = pd.Series(apply_candidate_b_score(frame, policy['b_fit']), index=frame.index)
    else:
        score = pd.Series(apply_linear_selector(frame, policy['linear_fit']), index=frame.index)

    out = frame.copy()
    out.loc[score < threshold, 'signal'] = 0
    return out
```

- [ ] **Step 4: Add the CLI for the final MT4 CSV**

```python
# API/export_execution_filtered_signals.py
def main():
    parser = argparse.ArgumentParser(description='Apply frozen execution trade filter to prediction CSV')
    parser.add_argument('--predictions', required=True)
    parser.add_argument('--policy', required=True)
    parser.add_argument('--csv-out', required=True)
    args = parser.parse_args()

    frame = pd.read_csv(args.predictions, sep=';')
    policy = json.loads(Path(args.policy).read_text(encoding='utf-8'))
    out = apply_frozen_selector(frame, policy)
    Path(args.csv_out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.csv_out, sep=';', index=False)
```

- [ ] **Step 5: Run tests to verify the export path passes**

Run: `./.venv/bin/python -m pytest tests/test_export_execution_filtered_signals.py -q`
Expected: PASS

- [ ] **Step 6: Build the final MT4 CSV only from the frozen winner**

Run: `./.venv/bin/python -m API.export_execution_filtered_signals --predictions ML/reports/trade_execution_base_test_predictions.csv --policy ML/reports/frozen_execution_trade_filter.json --csv-out MT/MQL4/Files/ml_signals_execution_filter.csv`
Expected: writes one final filtered CSV for MT4; do not emit multiple variants

- [ ] **Step 7: Update report, changelog and handoff**

```md
## Winner
- Base layer: frozen `A @ 7.5%`
- New layer: exactly one selector from `ML/reports/frozen_execution_trade_filter.json`
- Reason: best validation PF after the same trade floor and period stability rule

## If no winner
- No `frozen_execution_trade_filter.json`
- No final test report
- No MT4 CSV export
```

- [ ] **Step 8: Run final verification**

Run: `./.venv/bin/python -m pytest tests/test_trade_simulator.py tests/test_trade_simulator_reconcile.py tests/test_execution_trade_filter.py tests/test_export_execution_filtered_signals.py -q`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add API/export_execution_filtered_signals.py tests/test_export_execution_filtered_signals.py CHANGELOG.md CONTEXT_HANDOFF.md docs/reports/2026-04-09-mt4-execution-trade-selection.md
git commit -m "feat: add execution-aware trade selection export"
```
