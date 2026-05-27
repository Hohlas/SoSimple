# Limit Order Entry Convention — Implementation Plan

> **For agentic workers:** REQUIRED: Use subagent-driven-development to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Реализовать Phase 1 (labeling + audit) и Phase 2 (RF/HGB baseline gate) для limit-order entry convention согласно spec.

**Architecture:** Новая функция `label_limit_order_barriers()` в `processing/label_signals.py` симулирует pending BUY/SELL LIMIT на уровне Close[row] с spread-adjusted fill и exit. Скрипт аудита сравнивает новые лейблы со старыми. RF/HGB baseline проверяет, есть ли edge до инвестиций в Transformer.

**Tech Stack:** Python 3.11+, pandas, numpy, sklearn (RandomForest, HistGradientBoosting), pytest, существующий OHLC-инфраструктура `processing/label_signals.py`

**Spec:** `docs/superpowers/specs/2026-05-27-limit-order-entry-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `processing/label_signals.py` | MODIFY | +`label_limit_order_barriers()` — новый лейблинг |
| `processing/label_main.py` | MODIFY | +флаг `--limit-order` для вызова новой функции |
| `processing/label_audit.py` | CREATE | Аудит: fill_lag, ambiguity, сравнение со старыми лейблами |
| `tests/processing/test_limit_order_barriers.py` | CREATE | Тесты на fill, NO_FILL, same-bar ambiguity, PnL |
| `ML/baseline/benchmark_limit_order_entry.py` | CREATE | RF/HGB baseline: train на fill-only, threshold sweep, gate |
| `DATA/Nero_{train,val,test}_limit_labeled.csv` | OUTPUT | Новые лейблы (output labeling pipeline) |
| `ML/baseline/reports/limit_order_baseline_*.md` | OUTPUT | Отчёт baseline (output скрипта) |

---

### Task 1: Write `label_limit_order_barriers()` in `label_signals.py`

**Files:** Modify `processing/label_signals.py` (добавить функцию после `label_first_barrier_hit`, около строки 1110)

- [ ] **Step 1: Прочитать текущий конец `label_signals.py`, чтобы знать точное место вставки**

```bash
wc -l processing/label_signals.py
tail -20 processing/label_signals.py
```

- [ ] **Step 2: Добавить константы и функцию**

Добавить перед функцией:

```python
# Limit-order label constants
LIMIT_FILL_WINDOW = 6
LIMIT_BARRIER_WINDOW = 24
LIMIT_NO_FILL_SENTINEL = -999.0
LIMIT_AMBIGUOUS_SENTINEL = -888.0
```

Добавить функцию:

```python
def label_limit_order_barriers(df, ohlc_path, fill_window=6, barrier_window=24,
                                spread=0.0, mode="conservative", debug=False):
    """
    Limit-order Triple Barrier labels: pending BUY/SELL LIMIT на Close[row_time].

    Симулирует pending order на уровне Close[row] с ожиданием fill до fill_window баров.
    Барьерный скан стартует от бара fill (fill_idx+1 .. fill_idx+barrier_window).

    Args:
        df:            DataFrame с колонками fractal0, ATR (до нормализации).
        ohlc_path:     Путь к DATA/XAUUSD_H1_OHLC.csv.
        fill_window:   Макс. баров ожидания fill (default 6).
        barrier_window: Баров барьерного скана после fill (default 24).
        spread:        Спред в ценовых единицах (default 0.0).
        mode:          "conservative" | "optimistic" | "ambiguous".
        debug:         Печатать статистику.

    Returns:
        DataFrame с колонками TB_TARGET_NAMES, buy_fill_lag, sell_fill_lag, _pnl_r, и ambiguous_flag_{target}.
    """
    from datetime import datetime, timezone

    ohlc, times, time_idx = load_ohlc_index(ohlc_path)

    for name in TB_TARGET_NAMES:
        df[name] = 0.5
        amb_col = f'ambiguous_flag_{name}'
        if amb_col not in df.columns:
            df[amb_col] = 0
        pnl_col = f'{name}_pnl_r'
        if pnl_col not in df.columns:
            df[pnl_col] = 0.0

    for side in ['buy', 'sell']:
        lag_col = f'{side}_fill_lag'
        if lag_col not in df.columns:
            df[lag_col] = -1

    found = skipped = no_fill = 0

    for i, row in df.iterrows():
        fractal0 = parse_fractal(row.get('fractal0'))
        if fractal0 is None:
            skipped += 1
            continue

        row_time = row.get('time')
        if pd.isna(row_time) or row_time == '':
            skipped += 1
            continue

        try:
            row_dt = datetime.strptime(str(row_time), "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            skipped += 1
            continue

        row_idx = time_idx.get(row_dt)
        if row_idx is None:
            skipped += 1
            continue

        # ВАЖНО: entry_exec_price = Bid-close из OHLC.
        # Для BUY это семантически Ask-entry (limit Ask = CloseBid).
        # Для SELL это Bid-entry.
        entry_exec_price = ohlc[row_dt][3]

        try:
            atr = float(row['ATR'])
        except (ValueError, KeyError):
            skipped += 1
            continue
        if atr <= 0:
            skipped += 1
            continue

        # effective_limit (Bid-уровень для проверки fill)
        buy_fill_bid_level = entry_exec_price - spread
        sell_fill_bid_level = entry_exec_price

        # Fill scan — раздельный для BUY и SELL
        buy_fill_idx = -1
        sell_fill_idx = -1
        for k in range(row_idx + 1, min(row_idx + 1 + fill_window, len(times))):
            o, h, l, c = ohlc[times[k]]
            if buy_fill_idx == -1 and l <= buy_fill_bid_level:
                buy_fill_idx = k
            if sell_fill_idx == -1 and h >= sell_fill_bid_level:
                sell_fill_idx = k
            if buy_fill_idx != -1 and sell_fill_idx != -1:
                break

        buy_fill_lag_val = buy_fill_idx - (row_idx + 1) if buy_fill_idx >= 0 else -1
        sell_fill_lag_val = sell_fill_idx - (row_idx + 1) if sell_fill_idx >= 0 else -1
        df.at[i, 'buy_fill_lag'] = buy_fill_lag_val
        df.at[i, 'sell_fill_lag'] = sell_fill_lag_val

        # Track NO_FILL per direction
        if buy_fill_idx == -1 and sell_fill_idx == -1:
            no_fill += 1
            for name in TB_TARGET_NAMES:
                df.at[i, name] = LIMIT_NO_FILL_SENTINEL
            found += 1
            continue

        # ========= BUY side (использует buy_fill_idx) =========
        if buy_fill_idx >= 0:
            buy_scan_end = min(buy_fill_idx + 1 + barrier_window, len(times))
            buy_bars = []
            for k in range(buy_fill_idx + 1, buy_scan_end):
                o, h, l, c = ohlc[times[k]]
                buy_bars.append({'open': o, 'high': h, 'low': l, 'close': c})
            buy_bars_df = pd.DataFrame(buy_bars, columns=['open', 'high', 'low', 'close'])
            fill_o_buy, fill_h_buy, fill_l_buy, fill_c_buy = ohlc[times[buy_fill_idx]]

            for sl in TB_SL_LEVELS:
                for tp in TB_TP_LEVELS:
                    buy_tp_price = entry_exec_price + tp * atr
                    buy_sl_price = entry_exec_price - sl * atr

                    buy_sl_hit_fill_bar = fill_l_buy <= buy_sl_price
                    buy_tp_hit_fill_bar = fill_h_buy >= buy_tp_price

                    buy_outcome = 0.5
                    for bi, bar in buy_bars_df.iterrows():
                        if bar['high'] >= buy_tp_price and bar['low'] <= buy_sl_price:
                            if mode == "conservative":
                                buy_outcome = 0.0
                            elif mode == "ambiguous":
                                buy_outcome = LIMIT_AMBIGUOUS_SENTINEL
                            break
                        elif bar['high'] >= buy_tp_price:
                            buy_outcome = 1.0
                            break
                        elif bar['low'] <= buy_sl_price:
                            buy_outcome = 0.0
                            break

                    if mode == "conservative" and buy_sl_hit_fill_bar:
                        buy_outcome = 0.0
                    elif mode == "ambiguous" and (buy_sl_hit_fill_bar or buy_tp_hit_fill_bar):
                        buy_outcome = LIMIT_AMBIGUOUS_SENTINEL

                    # BUY PnL
                    buy_pnl = 0.0
                    if buy_outcome == 1.0:
                        buy_pnl = +tp
                    elif buy_outcome == 0.0:
                        buy_pnl = -sl
                    elif buy_outcome == 0.5:
                        last_close = ohlc[times[buy_scan_end - 1]][3] if buy_scan_end > buy_fill_idx + 1 else fill_c_buy
                        buy_pnl = (last_close - entry_exec_price) / atr

                    buy_col = f'buy_sl{sl}_tp{tp}'
                    df.at[i, buy_col] = buy_outcome
                    buy_pnl_col = f'{buy_col}_pnl_r'
                    df.at[i, buy_pnl_col] = buy_pnl

                    # ambiguous flag for buy
                    amb_buy_col = f'ambiguous_flag_{buy_col}'
                    if buy_outcome == LIMIT_AMBIGUOUS_SENTINEL:
                        df.at[i, amb_buy_col] = (1 if buy_sl_hit_fill_bar
                                                 else 2 if buy_tp_hit_fill_bar else 4)
        else:
            # BUY NO_FILL: все buy-таргеты = NO_FILL
            for sl in TB_SL_LEVELS:
                for tp in TB_TP_LEVELS:
                    df.at[i, f'buy_sl{sl}_tp{tp}'] = LIMIT_NO_FILL_SENTINEL

        # ========= SELL side (использует sell_fill_idx) =========
        if sell_fill_idx >= 0:
            sell_scan_end = min(sell_fill_idx + 1 + barrier_window, len(times))
            sell_bars = []
            for k in range(sell_fill_idx + 1, sell_scan_end):
                o, h, l, c = ohlc[times[k]]
                sell_bars.append({'open': o, 'high': h, 'low': l, 'close': c})
            sell_bars_df = pd.DataFrame(sell_bars, columns=['open', 'high', 'low', 'close'])
            fill_o_sell, fill_h_sell, fill_l_sell, fill_c_sell = ohlc[times[sell_fill_idx]]

            for sl in TB_SL_LEVELS:
                for tp in TB_TP_LEVELS:
                    sell_tp_price = entry_exec_price - tp * atr
                    sell_sl_price = entry_exec_price + sl * atr

                    sell_sl_hit_fill_bar = fill_h_sell >= sell_sl_price
                    sell_tp_hit_fill_bar = fill_l_sell <= sell_tp_price

                    sell_outcome = 0.5
                    for bi, bar in sell_bars_df.iterrows():
                        bar_high_ask = bar['high'] + spread
                        bar_low_ask = bar['low'] + spread
                        if bar_high_ask >= sell_sl_price and bar_low_ask <= sell_tp_price:
                            if mode == "conservative":
                                sell_outcome = 0.0
                            elif mode == "ambiguous":
                                sell_outcome = LIMIT_AMBIGUOUS_SENTINEL
                            break
                        elif bar_low_ask <= sell_tp_price:
                            sell_outcome = 1.0
                            break
                        elif bar_high_ask >= sell_sl_price:
                            sell_outcome = 0.0
                            break

                    if mode == "conservative" and sell_sl_hit_fill_bar:
                        sell_outcome = 0.0
                    elif mode == "ambiguous" and (sell_sl_hit_fill_bar or sell_tp_hit_fill_bar):
                        sell_outcome = LIMIT_AMBIGUOUS_SENTINEL

                    # SELL PnL
                    sell_pnl = 0.0
                    if sell_outcome == 1.0:
                        sell_pnl = +tp
                    elif sell_outcome == 0.0:
                        sell_pnl = -sl
                    elif sell_outcome == 0.5:
                        last_close = ohlc[times[sell_scan_end - 1]][3] if sell_scan_end > sell_fill_idx + 1 else fill_c_sell
                        sell_pnl = (entry_exec_price - (last_close + spread)) / atr

                    sell_col = f'sell_sl{sl}_tp{tp}'
                    df.at[i, sell_col] = sell_outcome
                    sell_pnl_col = f'{sell_col}_pnl_r'
                    df.at[i, sell_pnl_col] = sell_pnl

                    amb_sell_col = f'ambiguous_flag_{sell_col}'
                    if sell_outcome == LIMIT_AMBIGUOUS_SENTINEL:
                        df.at[i, amb_sell_col] = (1 if sell_sl_hit_fill_bar
                                                  else 2 if sell_tp_hit_fill_bar else 4)
        else:
            # SELL NO_FILL: все sell-таргеты = NO_FILL
            for sl in TB_SL_LEVELS:
                for tp in TB_TP_LEVELS:
                    df.at[i, f'sell_sl{sl}_tp{tp}'] = LIMIT_NO_FILL_SENTINEL

        found += 1

    if debug:
        total = len(df)
        buy_fill = (df['buy_fill_lag'] >= 0).sum()
        sell_fill = (df['sell_fill_lag'] >= 0).sum()
        both_nofill = ((df['buy_fill_lag'] == -1) & (df['sell_fill_lag'] == -1)).sum()
        print(f"\n[LIMIT_ORDER_BARRIERS] Обработано: {found}, пропущено: {skipped}")
        print(f"  BUY fill={buy_fill} ({buy_fill/max(found,1)*100:.1f}%)  "
              f"SELL fill={sell_fill} ({sell_fill/max(found,1)*100:.1f}%)  "
              f"both NO_FILL={both_nofill}")
        for name in TB_TARGET_NAMES[:2]:
            vals = df[name].dropna()
            nf = (vals == LIMIT_NO_FILL_SENTINEL).sum()
            sl_c = (vals == 0.0).sum()
            tp_c = (vals == 1.0).sum()
            to_c = (vals == 0.5).sum()
            print(f"  {name}: TP={tp_c} SL={sl_c} TO={to_c} NO_FILL={nf}")

    return df
```

- [ ] **Step 3: Запустить линтер на изменённом файле**

```bash
.venv/bin/python -m flake8 processing/label_signals.py --max-line-length=120 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
git add processing/label_signals.py
git commit -m "feat: add label_limit_order_barriers() for limit-order entry convention"
```

---

### Task 2: Write tests for `label_limit_order_barriers()`

**Files:** Create `tests/processing/test_limit_order_barriers.py`

- [ ] **Step 1: Создать файл с синтетическим OHLC и тестами**

```python
# =============================================================================
# Файл: tests/processing/test_limit_order_barriers.py
# Назначение: Тесты для label_limit_order_barriers()
# =============================================================================

import os
import sys
import tempfile
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'processing'))
from label_signals import (
    label_limit_order_barriers,
    LIMIT_NO_FILL_SENTINEL,
    LIMIT_AMBIGUOUS_SENTINEL,
    TB_TARGET_NAMES,
)


def _make_ohlc_csv(path, rows):
    """Создать синтетический XAUUSD_H1_OHLC.csv."""
    df = pd.DataFrame(rows, columns=['time', 'open', 'high', 'low', 'close'])
    df.to_csv(path, index=False)
    return df


def _make_nero_df(times, atr_vals, fractal0_vals):
    """Создать DataFrame в формате Nero (до нормализации)."""
    return pd.DataFrame({
        'time': times,
        'fractal0': fractal0_vals,
        'ATR': atr_vals,
    })


def test_buy_fill_and_tp():
    """BUY LIMIT: fill на t+1, TP на t+2."""
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
        _make_ohlc_csv(ohlc_path, [
            ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),  # t: signal bar
            ('2020.01.01 01:00', 1501.0, 1503.0, 1499.0, 1501.0),  # t+1: Low=1499 <= 1500 → fill
            ('2020.01.01 02:00', 1501.0, 1510.0, 1500.0, 1508.0),  # t+2: High=1510 >= 1500+6=1506 → TP
        ])
        df = _make_nero_df(
            times=['2020.01.01 00:00'],
            atr_vals=[2.0],
            fractal0_vals=['123:2020.01.01 00:00:1501.0:0'],
        )

        result = label_limit_order_barriers(
            df, ohlc_path, fill_window=6, barrier_window=24,
            spread=0.0, mode="conservative", debug=False,
        )

        # buy_sl3_tp3: TP = 1500 + 3*2 = 1506, SL = 1500 - 3*2 = 1494
        assert result.at[0, 'buy_sl3_tp3'] == 1.0  # TP
        assert result.at[0, 'buy_fill_lag'] == 0


def test_buy_no_fill():
    """BUY LIMIT: цена уходит вверх, fill не происходит за 6 баров."""
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
        rows = [('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0)]
        # Все следующие бары: Low > 1500 → no fill
        for h in range(1, 8):
            rows.append((f'2020.01.01 {h:02d}:00', 1502.0, 1505.0, 1501.0, 1503.0))
        _make_ohlc_csv(ohlc_path, rows)

        df = _make_nero_df(
            times=['2020.01.01 00:00'],
            atr_vals=[2.0],
            fractal0_vals=['123:2020.01.01 00:00:1501.0:0'],
        )

        result = label_limit_order_barriers(df, ohlc_path, fill_window=6)
        assert result.at[0, 'buy_sl3_tp3'] == LIMIT_NO_FILL_SENTINEL
        assert result.at[0, 'buy_fill_lag'] == -1


def test_sell_fill_and_sl():
    """SELL LIMIT: fill на t+1, SL на t+2."""
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
        _make_ohlc_csv(ohlc_path, [
            ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
            ('2020.01.01 01:00', 1499.0, 1502.0, 1498.0, 1500.0),  # High=1502 >= 1500 → fill
            ('2020.01.01 02:00', 1500.0, 1510.0, 1499.0, 1509.0),  # High=1510 >= 1500+6=1506 → SL (SELL)
        ])
        df = _make_nero_df(
            times=['2020.01.01 00:00'],
            atr_vals=[2.0],
            fractal0_vals=['123:2020.01.01 00:00:1499.0:1'],
        )

        result = label_limit_order_barriers(df, ohlc_path, fill_window=6)
        # sell_sl3_tp3: TP = 1500-6=1494, SL = 1500+6=1506
        # Without spread: High=1510 >= 1506 → SL
        assert result.at[0, 'sell_sl3_tp3'] == 0.0  # SL
        assert result.at[0, 'sell_fill_lag'] == 0


def test_same_bar_fill_sl_conservative():
    """BUY: fill и SL на одном баре → conservative mode → SL."""
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
        _make_ohlc_csv(ohlc_path, [
            ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
            # t+1: Low=1490 → fill (1490 <= 1500) AND SL (1490 <= 1494)
            ('2020.01.01 01:00', 1495.0, 1496.0, 1490.0, 1492.0),
        ])
        df = _make_nero_df(
            times=['2020.01.01 00:00'],
            atr_vals=[2.0],
            fractal0_vals=['123:2020.01.01 00:00:1501.0:0'],
        )

        result_cons = label_limit_order_barriers(df, ohlc_path, mode="conservative")
        assert result_cons.at[0, 'buy_sl3_tp3'] == 0.0  # SL

        # same row, optimistic mode → fill first, no further bars → timeout
        result_opt = label_limit_order_barriers(
            _make_nero_df(['2020.01.01 00:00'], [2.0], ['123:2020.01.01 00:00:1501.0:0']),
            ohlc_path, mode="optimistic",
        )
        # Optimistic: fill counts, barrier scan from t+2 has no bars → timeout
        assert result_opt.at[0, 'buy_sl3_tp3'] == 0.5  # timeout (no bars after fill)


def test_spread_effect_buy_fill():
    """BUY LIMIT со spread: fill требует более низкого Bid."""
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
        _make_ohlc_csv(ohlc_path, [
            ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
            # t+1: Low=1499.5. Без spread: fill (1499.5 <= 1500).
            #       Со spread=0.5: effective_limit=1499.5, 1499.5 <= 1499.5 → fill.
            #       Со spread=1.0: effective_limit=1499.0, 1499.5 > 1499.0 → no fill.
            ('2020.01.01 01:00', 1500.0, 1502.0, 1499.5, 1500.5),
        ])
        df = _make_nero_df(
            times=['2020.01.01 00:00'],
            atr_vals=[2.0],
            fractal0_vals=['123:2020.01.01 00:00:1501.0:0'],
        )

        # spread=0.5: fill should happen
        r05 = label_limit_order_barriers(df, ohlc_path, spread=0.5)
        assert r05.at[0, 'buy_sl3_tp3'] != LIMIT_NO_FILL_SENTINEL

        # spread=1.0: no fill (1499.5 > 1499.0)
        r10 = label_limit_order_barriers(
            _make_nero_df(['2020.01.01 00:00'], [2.0], ['123:2020.01.01 00:00:1501.0:0']),
            ohlc_path, spread=1.0,
        )
        assert r10.at[0, 'buy_sl3_tp3'] == LIMIT_NO_FILL_SENTINEL


def test_fill_lag_values():
    """fill_lag: 0=t+1, 1=t+2, ..., 5=t+6."""
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
        # Signal at 00:00. Fill at 03:00 (t+3) → fill_lag=2
        rows = [('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0)]
        for h in range(1, 8):
            low = 1501.0 if h < 3 else 1499.0  # fill at h=3
            rows.append((f'2020.01.01 {h:02d}:00', 1501.0, 1503.0, low, 1502.0))
        _make_ohlc_csv(ohlc_path, rows)

        df = _make_nero_df(
            times=['2020.01.01 00:00'],
            atr_vals=[2.0],
            fractal0_vals=['123:2020.01.01 00:00:1501.0:0'],
        )

        result = label_limit_order_barriers(df, ohlc_path)
        assert result.at[0, 'buy_fill_lag'] == 2


def test_ambiguous_flag_columns_exist():
    """ambiguous_flag_{target} колонки создаются для всех 12 target-ов."""
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
        _make_ohlc_csv(ohlc_path, [
            ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
            ('2020.01.01 01:00', 1500.0, 1502.0, 1499.0, 1501.0),
        ])
        df = _make_nero_df(
            times=['2020.01.01 00:00'],
            atr_vals=[2.0],
            fractal0_vals=['123:2020.01.01 00:00:1501.0:0'],
        )
        result = label_limit_order_barriers(df, ohlc_path)
        for name in TB_TARGET_NAMES:
            assert f'ambiguous_flag_{name}' in result.columns
        assert 'buy_fill_lag' in result.columns
        assert 'sell_fill_lag' in result.columns


def test_sell_spread_tp_harder():
    """SELL со spread: TP труднее достичь (LowBid + spread <= TP)."""
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
        _make_ohlc_csv(ohlc_path, [
            ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
            # t+1: fill (High=1502>=1500). Затем t+2:
            # SELL TP = 1500 - 3*2 = 1494 (без spread)
            # С spread=0.5: LowBid + 0.5 <= 1494 → LowBid <= 1493.5
            # Low=1494.0: без spread → TP, со spread → timeout
            ('2020.01.01 01:00', 1499.0, 1502.0, 1498.0, 1500.0),
            ('2020.01.01 02:00', 1495.0, 1496.0, 1494.0, 1495.0),
            ('2020.01.01 03:00', 1495.0, 1496.0, 1493.0, 1494.0),
        ])
        df = _make_nero_df(
            times=['2020.01.01 00:00'],
            atr_vals=[2.0],
            fractal0_vals=['123:2020.01.01 00:00:1499.0:1'],
        )

        r0 = label_limit_order_barriers(
            _make_nero_df(['2020.01.01 00:00'], [2.0], ['123:2020.01.01 00:00:1499.0:1']),
            ohlc_path, spread=0.0,
        )
        # spread=0: Low=1494.0 <= 1494 → TP
        assert r0.at[0, 'sell_sl3_tp3'] == 1.0

        r05 = label_limit_order_barriers(
            _make_nero_df(['2020.01.01 00:00'], [2.0], ['123:2020.01.01 00:00:1499.0:1']),
            ohlc_path, spread=0.5,
        )
        # spread=0.5: LowBid=1494.0, LowAsk=1494.5 > TP=1494 → нет TP → timeout
        # (нет SL за 2 бара scan)
        assert r05.at[0, 'sell_sl3_tp3'] == 0.5  # timeout


def test_sell_spread_sl_easier():
    """SELL со spread: SL легче достичь (HighBid + spread >= SL)."""
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
        _make_ohlc_csv(ohlc_path, [
            ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
            ('2020.01.01 01:00', 1499.0, 1502.0, 1498.0, 1500.0),
            # SELL SL = 1500 + 3*2 = 1506 (без spread)
            # С spread=0.5: HighBid + 0.5 >= 1506 → HighBid >= 1505.5
            # High=1505.8: без spread → нет SL, со spread → SL
            ('2020.01.01 02:00', 1501.0, 1505.8, 1500.0, 1505.0),
            ('2020.01.01 03:00', 1506.0, 1510.0, 1504.0, 1507.0),
        ])
        df = _make_nero_df(
            times=['2020.01.01 00:00'],
            atr_vals=[2.0],
            fractal0_vals=['123:2020.01.01 00:00:1499.0:1'],
        )

        r0 = label_limit_order_barriers(
            _make_nero_df(['2020.01.01 00:00'], [2.0], ['123:2020.01.01 00:00:1499.0:1']),
            ohlc_path, spread=0.0,
        )
        # spread=0: High=1505.8 < SL=1506 → не SL → timeout (или TP позже)
        assert r0.at[0, 'sell_sl3_tp3'] != 0.0

        r05 = label_limit_order_barriers(
            _make_nero_df(['2020.01.01 00:00'], [2.0], ['123:2020.01.01 00:00:1499.0:1']),
            ohlc_path, spread=0.5,
        )
        # spread=0.5: HighBid=1505.8, HighAsk=1506.3 >= SL=1506 → SL
        assert r05.at[0, 'sell_sl3_tp3'] == 0.0


def test_sell_timeout_pnl_spread():
    """SELL timeout PnL уменьшается на spread."""
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
        _make_ohlc_csv(ohlc_path, [
            ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
            ('2020.01.01 01:00', 1499.0, 1502.0, 1498.0, 1500.0),
            ('2020.01.01 02:00', 1495.0, 1496.0, 1494.0, 1495.0),
        ])
        df = _make_nero_df(
            times=['2020.01.01 00:00'],
            atr_vals=[2.0],
            fractal0_vals=['123:2020.01.01 00:00:1499.0:1'],
        )

        r0 = label_limit_order_barriers(
            _make_nero_df(['2020.01.01 00:00'], [2.0], ['123:2020.01.01 00:00:1499.0:1']),
            ohlc_path, spread=0.0,
        )
        pnl0 = r0.at[0, 'sell_sl3_tp3_pnl_r']

        r05 = label_limit_order_barriers(
            _make_nero_df(['2020.01.01 00:00'], [2.0], ['123:2020.01.01 00:00:1499.0:1']),
            ohlc_path, spread=0.5,
        )
        pnl05 = r05.at[0, 'sell_sl3_tp3_pnl_r']

        # spread=0.5 должен дать PnL ниже на spread/ATR = 0.5/2.0 = 0.25
        assert abs((pnl0 - pnl05) - 0.25) < 0.001
```

- [ ] **Step 2: Запустить тесты — ожидаемый FAIL (функция ещё не протестирована в изоляции)**

```bash
.venv/bin/python -m pytest tests/processing/test_limit_order_barriers.py -v
```

- [ ] **Step 3: Если тесты падают не по причине багов, а из-за импортов — поправить импорты, перезапустить до PASS**

- [ ] **Step 4: Commit**

```bash
git add tests/processing/test_limit_order_barriers.py
git commit -m "test: add tests for label_limit_order_barriers()"
```

---

### Task 3: Add `--limit-order` flag to `label_main.py`

**Files:** Modify `processing/label_main.py`

- [ ] **Step 1: Найти место добавления аргумента и вызова**

```bash
grep -n "add_argument\|label_first_barrier_hit\|step 3d\|Triple Barrier" processing/label_main.py
```

- [ ] **Step 2: Добавить аргументы `--limit-order` и `--spread`**

```python
parser.add_argument('--limit-order', action='store_true',
                    help='Use limit-order entry labeling instead of immediate entry')
parser.add_argument('--spread', type=float, default=0.0,
                    help='Spread in price units for limit-order labeling (default 0.0)')
```

- [ ] **Step 3: Заменить вызов `label_first_barrier_hit` при `--limit-order`**

В секции Triple Barrier labels (строка ~283) заменить вызов:

```python
    if args.limit_order:
        from processing.label_signals import label_limit_order_barriers
        print(f"\nРазметка Limit-Order Triple Barrier (OHLC={args.ohlc}, spread={args.spread})...")
        labeled_df = label_limit_order_barriers(
            labeled_df, args.ohlc,
            fill_window=6, barrier_window=24,
            spread=args.spread, mode="conservative", debug=args.debug,
        )
    else:
        print(f"\nРазметка Triple Barrier таргетов (path-ordered, OHLC={args.ohlc})...")
        labeled_df = label_first_barrier_hit(labeled_df, args.ohlc, scan_bars=24, debug=args.debug)
```

ВАЖНО: новая функция ПЕРЕЗАПИСЫВАЕТ TB_TARGET_NAMES и `_pnl_r` колонки. Старый и новый протокол НЕ смешиваются — при `--limit-order` старый TB НЕ вызывается.

- [ ] **Step 4: Commit**

```bash
git add processing/label_main.py
git commit -m "feat: add --limit-order flag to label_main.py"
```

---

### Task 4: Run spread grid sweep

**Files:** None (CLI runs only)

- [ ] **Step 1: Запустить labeling для 4 уровней spread**

```bash
for spread in 0 0.20 0.40 0.80; do
  echo "=== Labeling with spread=$spread ==="
  .venv/bin/python processing/label_main.py \
    --input MT/MQL4/Files/Nero.csv \
    --ohlc DATA/XAUUSD_H1_OHLC.csv \
    --output-dir "DATA/spread_${spread}/" \
    --limit-order --spread $spread \
    --debug 2>&1 | tail -5
done
```

Примечание: Значения в ценовых единицах OHLC. Canonical baseline spread для XAUUSD ~0.20 (20 пунктов пятизнака) — уточнить по MT symbol metadata/tester logs перед запуском. spread=0 только lower-bound diagnostic.

- [ ] **Step 2: Сравнить fill rate и label distributions через audit**

```bash
for spread in 0 0.20 0.40 0.80; do
  echo "=== Audit spread=$spread ==="
  .venv/bin/python processing/label_audit.py \
    --new "DATA/spread_${spread}/Nero_train_labeled.csv" \
    --primary-target buy_sl3_tp3 2>&1 | head -20
done
```

Проверить: на каком spread fill rate падает ниже ~30%? Это определяет запас прочности гипотезы.

- [ ] **Step 3: Сохранить агрегированный отчёт spread grid**

```bash
mkdir -p ML/baseline/reports
for spread in 0 0.20 0.40 0.80; do
  echo "=== SPREAD=$spread ==="
  .venv/bin/python processing/label_audit.py \
    --new "DATA/spread_${spread}/Nero_train_labeled.csv" \
    --primary-target buy_sl3_tp3
done | tee ML/baseline/reports/limit_order_spread_audit.md
```

CSV-датасеты в `DATA/limit_order/` и `DATA/spread_*/` — generated artifacts, не коммитить. Коммитить только отчёты (*.md, *.json).

---

### Task 5: Run labeling pipeline and verify output

**Files:** None (run-only task)

- [ ] **Step 1: Запустить labeling с новым флагом (output в отдельную директорию)**

```bash
mkdir -p DATA/limit_order
.venv/bin/python processing/label_main.py \
  --input MT/MQL4/Files/Nero.csv \
  --ohlc DATA/XAUUSD_H1_OHLC.csv \
  --output-dir DATA/limit_order/ \
  --limit-order \
  --debug 2>&1 | tail -30
```

Проверить:
- Нет ошибок (KeyError, ValueError)
- Статистика NO_FILL, TP, SL, TO печатается
- Файлы `Nero_train_labeled.csv`, `Nero_validation_labeled.csv`, `Nero_test_labeled.csv` созданы

- [ ] **Step 2: Проверить колонки в выходном CSV**

```bash
head -1 DATA/limit_order/Nero_train_labeled.csv | tr ';' '\n' | grep -E "fill_lag|ambiguous_flag"
```

Должны быть: `buy_fill_lag`, `sell_fill_lag` + 12 колонок `ambiguous_flag_buy_sl*_tp*` + 12 `ambiguous_flag_sell_sl*_tp*` + 12 колонок `*_pnl_r`

- [ ] **Step 3: Проверить распределение fill_lag**

```bash
.venv/bin/python -c "
import pandas as pd
df = pd.read_csv('DATA/limit_order/Nero_train_labeled.csv', sep=';')
print('BUY fill_lag:')
print(df['buy_fill_lag'].value_counts().sort_index())
print(f'BUY fill_rate: {(df[\"buy_fill_lag\"] >= 0).mean():.2%}')
print()
print('SELL fill_lag:')
print(df['sell_fill_lag'].value_counts().sort_index())
print(f'SELL fill_rate: {(df[\"sell_fill_lag\"] >= 0).mean():.2%}')
"
```

- [ ] **Step 4: CSV-файлы — проверить .gitignore**

```bash
grep "Nero.*labeled" .gitignore || echo "DATA/Nero_*_labeled.csv" >> .gitignore
```

---

### Task 6: Apply 30-bar purge/embargo to train/val/test split

**Files:** Create `processing/purge_split.py` (вспомогательный скрипт)

Согласно spec: purge по времени — строки train, чей `row_time + 30h` заходит в val, исключаются из train loss. Аналогично val→test и test tail.

- [ ] **Step 1: Создать скрипт `processing/purge_split.py`**

```python
#!/usr/bin/env python3
"""
Применить 30-bar purge/embargo к train/val/test split.

Использование:
  .venv/bin/python processing/purge_split.py \
    --train DATA/Nero_train_labeled.csv \
    --val DATA/Nero_validation_labeled.csv \
    --test DATA/Nero_test_labeled.csv \
    --purge-hours 30
"""

import argparse
import pandas as pd
import os
import sys


def purge_boundary(df, next_df_min_time, purge_hours):
    """Удалить строки из df, чей row_time + purge_hours >= начало следующего сплита."""
    if next_df_min_time is None:
        return df, 0
    times = pd.to_datetime(df['time'])
    cutoff = next_df_min_time - pd.Timedelta(hours=purge_hours)
    keep = times < cutoff
    removed = (~keep).sum()
    return df[keep].copy(), removed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', required=True)
    parser.add_argument('--val', required=True)
    parser.add_argument('--test', required=True)
    parser.add_argument('--purge-hours', type=int, default=30)
    parser.add_argument('--output-dir', default=None)
    args = parser.parse_args()

    train = pd.read_csv(args.train, sep=';')
    val = pd.read_csv(args.val, sep=';')
    test = pd.read_csv(args.test, sep=';')

    val_min = pd.to_datetime(val['time']).min()
    test_min = pd.to_datetime(test['time']).min()
    train_max = pd.to_datetime(train['time']).max()
    val_max = pd.to_datetime(val['time']).max()

    print(f"Original sizes: train={len(train)} val={len(val)} test={len(test)}")
    print(f"Boundaries: train_end={train_max} val_start={val_min} val_end={val_max} test_start={test_min}")

    train_purged, n1 = purge_boundary(train, val_min, args.purge_hours)
    val_purged, n2 = purge_boundary(val, test_min, args.purge_hours)
    # Test tail: удаляем строки без 30h будущих баров
    test_times = pd.to_datetime(test['time'])
    test_cutoff = test_times.max() - pd.Timedelta(hours=args.purge_hours)
    test_keep = test_times < test_cutoff
    n3 = (~test_keep).sum()
    test_purged = test[test_keep].copy()

    print(f"Purged: train -{n1}, val -{n2}, test tail -{n3}")
    print(f"New sizes: train={len(train_purged)} val={len(val_purged)} test={len(test_purged)}")

    output_dir = args.output_dir or os.path.dirname(args.train)
    for name, df in [('train', train_purged), ('validation', val_purged), ('test', test_purged)]:
        path = os.path.join(output_dir, f'Nero_{name}_labeled.csv')
        df.to_csv(path, sep=';', index=False)
        print(f"Saved: {path}")


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Запустить purge на DATA/limit_order/ (НЕ на основном DATA/)**

```bash
.venv/bin/python processing/purge_split.py \
  --train DATA/limit_order/Nero_train_labeled.csv \
  --val DATA/limit_order/Nero_validation_labeled.csv \
  --test DATA/limit_order/Nero_test_labeled.csv \
  --output-dir DATA/limit_order/ \
  --purge-hours 30
```

Проверить: сколько строк удалено на каждой границе. Если 0 — проверить корректность временных меток.

- [ ] **Step 3: Commit**

```bash
git add processing/purge_split.py
git commit -m "feat: add 30-bar purge/embargo for limit-order split boundaries"
```

---

### Task 7: Write label_audit.py

**Files:** Create `processing/label_audit.py`

- [ ] **Step 1: Создать audit-скрипт**

```python
#!/usr/bin/env python3
"""
Аудит limit-order лейблов: сравнение со старыми, статистика fill_lag, ambiguity.
Использование:
  .venv/bin/python processing/label_audit.py --new DATA/Nero_train_labeled.csv \
      --old DATA/Nero_train_labeled_old.csv --primary-target buy_sl3_tp3
"""

import argparse
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'processing'))
from label_signals import TB_TARGET_NAMES, LIMIT_NO_FILL_SENTINEL, LIMIT_AMBIGUOUS_SENTINEL


def audit_fill_lag(df, primary_target):
    """Распределение fill_lag по сторонам (buy/sell)."""
    print("=" * 60)
    print("FILL_LAG AUDIT")
    print("=" * 60)
    total = len(df)
    for side in ['buy', 'sell']:
        lag_col = f'{side}_fill_lag'
        fill_lag = df[lag_col]
        no_fill = (fill_lag == -1).sum()
        filled = (fill_lag >= 0).sum()
        print(f"\n  {side.upper()} fill_lag:")
        print(f"  Filled:     {filled} ({filled/total*100:.1f}%)")
        print(f"  NO_FILL:    {no_fill} ({no_fill/total*100:.1f}%)")
        for lag in sorted(fill_lag[fill_lag >= 0].unique()):
            n = (fill_lag == lag).sum()
            print(f"    lag={int(lag)}: {n:5d} ({n/filled*100:5.1f}%)")
    print()


def audit_ambiguity(df, primary_target):
    """Статистика ambiguous_bar_flag для primary target."""
    print("=" * 60)
    print(f"AMBIGUITY AUDIT ({primary_target})")
    print("=" * 60)
    amb_col = f'ambiguous_flag_{primary_target}'
    if amb_col not in df.columns:
        print(f"WARNING: column {amb_col} not found")
        return
    amb = df[amb_col]
    target_side = 'buy' if primary_target.startswith('buy_') else 'sell'
    filled = df[f'{target_side}_fill_lag'] >= 0
    filled_amb = amb[filled]

    flags = {0: 'clean', 1: 'fill+SL (same bar)', 2: 'fill+TP (same bar)',
             3: 'fill+TP+SL (same bar)', 4: 'TP+SL (barrier bar)'}
    print("Ambiguous bar flags (filled rows):")
    for val, label in flags.items():
        n = (filled_amb == val).sum()
        if n > 0:
            print(f"  {val} ({label}): {n:5d} ({n/filled.sum()*100:5.1f}%)")
    print()


def audit_comparison(df_new, df_old, primary_target):
    """Сравнение старых и новых лейблов на пересекающихся строках."""
    print("=" * 60)
    print(f"COMPARISON: old vs new labels ({primary_target})")
    print("=" * 60)

    merged = df_new[['time', primary_target]].merge(
        df_old[['time', primary_target]], on='time', suffixes=('_new', '_old'),
        how='inner',
    )

    n = len(merged)
    if n == 0:
        print("No overlapping rows found.")
        return

    new_vals = merged[f'{primary_target}_new']
    old_vals = merged[f'{primary_target}_old']

    # Исключаем sentinel-ы из сравнения
    valid = (new_vals != LIMIT_NO_FILL_SENTINEL) & (new_vals != LIMIT_AMBIGUOUS_SENTINEL)
    new_v = new_vals[valid]
    old_v = old_vals[valid]

    agreement = (new_v == old_v).sum()
    print(f"Overlapping rows: {n}")
    print(f"Valid (non-sentinel): {len(new_v)}")
    print(f"Agreement: {agreement} ({agreement/len(new_v)*100:.1f}%)")

    # Confusion matrix
    for new_label in [0.0, 0.5, 1.0]:
        for old_label in [0.0, 0.5, 1.0]:
            cnt = ((new_v == new_label) & (old_v == old_label)).sum()
            if cnt > 0:
                print(f"  old={old_label} new={new_label}: {cnt}")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--new', required=True, help='Path to new labeled CSV')
    parser.add_argument('--old', default=None, help='Path to old labeled CSV for comparison')
    parser.add_argument('--primary-target', default='buy_sl3_tp3')
    args = parser.parse_args()

    df_new = pd.read_csv(args.new, sep=';')

    audit_fill_lag(df_new, args.primary_target)
    audit_ambiguity(df_new, args.primary_target)

    if args.old and os.path.exists(args.old):
        df_old = pd.read_csv(args.old, sep=';')
        audit_comparison(df_new, df_old, args.primary_target)


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Запустить аудит на train**

```bash
.venv/bin/python processing/label_audit.py \
  --new DATA/Nero_train_labeled.csv \
  --primary-target buy_sl3_tp3
```

Проверить:
- fill_rate (должен быть > 0% и < 100%)
- fill_lag распределение (сколько Instant/Quick/Slow/Tail)
- ambiguous_bar_flag статистика (особенно доля fill+SL same-bar)

- [ ] **Step 3: Commit**

```bash
git add processing/label_audit.py
git commit -m "feat: add label_audit.py for limit-order label diagnostics"
```

---

### Task 8: Write RF/HGB baseline for limit-order labels

**Files:** Create `ML/baseline/benchmark_limit_order_entry.py`

- [ ] **Step 1: Создать baseline-скрипт**

```python
#!/usr/bin/env python3
"""
RF/HGB Baseline для limit-order entry convention.
Проверяет, существует ли edge на уровне простых моделей перед инвестициями в Transformer.

Gate: PF >= 1.3 AND fill_rate >= 20% на validation.
Target: buy_sl3_tp3 (первичный). Дополнительно: buy_sl2_tp3, sell_sl3_tp3.

Использование:
  .venv/bin/python -m ML.baseline.benchmark_limit_order_entry \
    --train DATA/Nero_train_limit_labeled.csv \
    --val DATA/Nero_validation_limit_labeled.csv \
    --target buy_sl3_tp3
"""

import argparse
import os
import sys
import warnings
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from collections import defaultdict

warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'processing'))
from label_signals import (
    TB_TARGET_NAMES, LIMIT_NO_FILL_SENTINEL, LIMIT_AMBIGUOUS_SENTINEL,
)


def parse_fractal_to_features(df):
    """Извлечь плоские признаки из fractal0..fractal99 (как в baseline_experiments.py)."""
    features = []
    feature_names = []

    for level in range(100):
        col = f'fractal{level}'
        if col not in df.columns:
            break

        price_series = []
        dir_series = []
        time_series = []

        for val in df[col]:
            try:
                parts = str(val).split(':')
                if len(parts) >= 4:
                    time_series.append(pd.Timestamp(parts[1]))
                    price_series.append(float(parts[2]))
                    dir_series.append(int(parts[3]))
                else:
                    time_series.append(pd.NaT)
                    price_series.append(np.nan)
                    dir_series.append(np.nan)
            except (ValueError, IndexError):
                time_series.append(pd.NaT)
                price_series.append(np.nan)
                dir_series.append(np.nan)

        features.append(np.array(price_series, dtype=np.float64))
        feature_names.append(f'f{level}_price')

        if level == 0:
            features.append(np.array(dir_series, dtype=np.float64))
            feature_names.append('f0_dir')

    # ATR
    if 'ATR' in df.columns:
        features.append(df['ATR'].values.astype(np.float64))
        feature_names.append('ATR')

    X = np.column_stack([f for f in features if len(f) > 0])
    X = np.nan_to_num(X, nan=0.0)
    return X, feature_names


def compute_pf(pnl_values):
    """Profit Factor: gross_profit / gross_loss (R-multiples)."""
    pnl = np.asarray(pnl_values, dtype=np.float64)
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def evaluate_threshold(scores, pnl_values, fill_mask, time_col,
                       threshold=None, top_k=None):
    """
    Выбрать сигналы по threshold или top_k.
    PF считается по фактическим _pnl_r значениям (включая timeout PnL).
    """
    n = len(scores)
    if threshold is not None:
        selected = scores >= threshold
    elif top_k is not None:
        k = min(top_k, n)
        idx = np.argsort(scores)[::-1][:k]
        selected = np.zeros(n, dtype=bool)
        selected[idx] = True
    else:
        selected = np.ones(n, dtype=bool)

    n_selected = selected.sum()
    if n_selected == 0:
        return {'pf': 0, 'n_selected': 0, 'n_filled': 0, 'fill_rate': 0,
                'mean_r_per_signal': 0, 'mean_r_per_trade': 0, 'trades_per_year': 0}

    selected_fill = selected & fill_mask
    n_filled = selected_fill.sum()

    if n_filled > 0:
        filled_pnl = pnl_values[selected_fill]
        pf_val = compute_pf(filled_pnl)
        mean_r_trade = float(np.mean(filled_pnl))
    else:
        pf_val = 0.0
        mean_r_trade = 0.0

    mean_r_signal = pnl_values[selected_fill].sum() / n_selected if n_selected > 0 else 0.0
    fill_rate_val = n_filled / n_selected if n_selected > 0 else 0.0

    if time_col is not None:
        filled_times = time_col[selected_fill]
        if len(filled_times) > 0:
            years_series = filled_times.dt.year
            yearly_pnl = pd.Series(pnl_values[selected_fill]).groupby(years_series).sum()
            negative_years_val = int((yearly_pnl < 0).sum())
        else:
            negative_years_val = 0
        total_years = (time_col.max() - time_col.min()).days / 365.25
        tpy = n_filled / max(total_years, 0.5)
    else:
        negative_years_val = 0
        tpy = 0.0

    return {
        'pf': pf_val,
        'n_selected': int(n_selected),
        'n_filled': int(n_filled),
        'fill_rate': fill_rate_val,
        'mean_r_per_signal': mean_r_signal,
        'mean_r_per_trade': mean_r_trade,
        'trades_per_year': tpy,
        'negative_years': negative_years_val,
    }


def compute_pf(pnl_values):
    """Profit Factor: gross_profit / gross_loss (R-multiples)."""
    pnl = np.asarray(pnl_values, dtype=np.float64)
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def threshold_sweep(scores, pnl_values, fill_mask, time_col, n_thresholds=50):
    results = []
    unique_scores = np.sort(np.unique(scores))
    if len(unique_scores) <= n_thresholds:
        thresholds = unique_scores
    else:
        indices = np.linspace(0, len(unique_scores) - 1, n_thresholds, dtype=int)
        thresholds = unique_scores[indices]

    for thr in thresholds:
        metrics = evaluate_threshold(scores, pnl_values, fill_mask, time_col, threshold=thr)
        metrics['threshold'] = thr
        results.append(metrics)

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', default='DATA/limit_order/Nero_train_labeled.csv')
    parser.add_argument('--val', default='DATA/limit_order/Nero_validation_labeled.csv')
    parser.add_argument('--target', default='buy_sl3_tp3')
    parser.add_argument('--purge-hours', type=int, default=30)
    args = parser.parse_args()

    # Определить fill-сторону из имени target
    target_side = 'buy' if args.target.startswith('buy_') else 'sell'
    pnl_col = f'{args.target}_pnl_r'
    fill_lag_col = f'{target_side}_fill_lag'

    print(f"Loading data...")
    print(f"Target: {args.target}, side: {target_side}, PnL col: {pnl_col}")
    train_df = pd.read_csv(args.train, sep=';')
    val_df = pd.read_csv(args.val, sep=';')

    # Train: fill-only для target side
    train_fill_mask = train_df[fill_lag_col] >= 0
    train_df_fill = train_df[train_fill_mask].copy()

    # Val: все строки
    val_fill_mask = val_df[fill_lag_col] >= 0

    print(f"Train (fill-only for {target_side}): {len(train_df_fill)} rows")
    print(f"Val (all):                           {len(val_df)} rows")

    # Purge/embargo
    if 'time' in train_df_fill.columns:
        train_times = pd.to_datetime(train_df_fill['time'])
        val_min_time = pd.to_datetime(val_df['time']).min()
        purge_mask = train_times + pd.Timedelta(hours=args.purge_hours) < val_min_time
        train_df_fill = train_df_fill[purge_mask].copy()
        print(f"Train after purge ({args.purge_hours}h): {len(train_df_fill)} rows")

    # Признаки
    print("Building features...")
    X_train, feature_names = parse_fractal_to_features(train_df_fill)
    X_val, _ = parse_fractal_to_features(val_df)

    # Target and PnL
    y_train = train_df_fill[args.target].values.astype(np.float64)
    pnl_val = val_df[pnl_col].values.astype(np.float64)
    time_val = pd.to_datetime(val_df['time'])

    # NO_FILL маска для оценки (используется только для разделения filled/no_fill)
    # Сами NO_FILL строки УЧАСТВУЮТ в threshold sweep (модель выдаёт для них scores)

    from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor

    models = {
        'RF': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
        'HGB': HistGradientBoostingRegressor(max_iter=100, max_depth=6, random_state=42),
    }

    gate_pass = False
    best_result = None

    for name, model in models.items():
        print(f"\n{'='*60}")
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        scores = model.predict(X_val)

        results = threshold_sweep(scores, pnl_val, val_fill_mask.values, time_val)

        # Найти лучший threshold по PF (с gate constraints)
        valid = [r for r in results
                 if r['fill_rate'] >= 0.20
                 and r['trades_per_year'] >= 6
                 and r['negative_years'] == 0]
        if valid:
            best = max(valid, key=lambda r: r['pf'])
            best['model'] = name
            print(f"  Best threshold: {best['threshold']:.4f}")
            print(f"  PF={best['pf']:.3f}  fill_rate={best['fill_rate']:.1%}  "
                  f"trades/year={best['trades_per_year']:.1f}  "
                  f"selected={best['n_selected']}  filled={best['n_filled']}  "
                  f"neg_years={best['negative_years']}")
            if best['pf'] >= 1.3:
                gate_pass = True
                if best_result is None or best['pf'] > best_result['pf']:
                    best_result = best
        else:
            best_pf = max(results, key=lambda r: r['pf'])
            print(f"  Max PF={best_pf['pf']:.3f} (no threshold passes fill_rate>=20% gate)")
            print(f"  Best fill_rate: {max(r['fill_rate'] for r in results):.1%}")

    print(f"\n{'='*60}")
    if gate_pass and best_result:
        print(f"GATE PASS: {best_result['model']} PF={best_result['pf']:.3f} >= 1.3, "
              f"fill_rate={best_result['fill_rate']:.1%} >= 20%")
        print("→ Можно переходить к Phase 3 (Transformer).")
    else:
        print("GATE FAIL: ни одна модель не прошла PF>=1.3 и fill_rate>=20%")
        print("→ Гипотеза limit-order НЕ подтверждена на уровне baseline. Стоп.")


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Запустить baseline**

```bash
.venv/bin/python -m ML.baseline.benchmark_limit_order_entry \
  --target buy_sl3_tp3 2>&1
```

- [ ] **Step 3: Если GATE PASS — запустить на дополнительных target-ах**

```bash
.venv/bin/python -m ML.baseline.benchmark_limit_order_entry --target buy_sl2_tp3
.venv/bin/python -m ML.baseline.benchmark_limit_order_entry --target sell_sl3_tp3
```

- [ ] **Step 4: Commit**

```bash
git add ML/baseline/benchmark_limit_order_entry.py
git commit -m "feat: add RF/HGB baseline for limit-order entry convention"
```

---

### Task 9: Run Phase 2 baseline evaluation and document results

- [ ] **Step 1: Запустить полный baseline с Audit + Baseline**

```bash
.venv/bin/python processing/label_audit.py \
  --new DATA/Nero_train_labeled.csv \
  --primary-target buy_sl3_tp3

.venv/bin/python -m ML.baseline.benchmark_limit_order_entry --target buy_sl3_tp3
```

- [ ] **Step 2: Сохранить отчёт в `ML/baseline/reports/limit_order_baseline_*.md`**

```bash
mkdir -p ML/baseline/reports
```

Записать вывод baseline в файл отчёта с датой.

- [ ] **Step 3: Commit результаты**

```bash
git add ML/baseline/reports/
git commit -m "report: limit-order RF/HGB baseline results"
```

---

### Task 10: Sync docs and module index

- [ ] **Step 1: Обновить документацию methodology**

Загрузить skill update-docs-on-code-change и выполнить синхронизацию для затронутых файлов.

- [ ] **Step 2: Commit**

```bash
git add docs/methodology/
git commit -m "docs: update methodology for limit-order entry convention"
```
