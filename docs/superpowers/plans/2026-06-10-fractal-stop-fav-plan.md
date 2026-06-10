# Fractal Stop + Fav Target (Stage 2) — Implementation Plan

> **For agentic workers:** REQUIRED: Use subagent-driven-development to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить торговый слой поверх breach-сигнала: entry_price, стоп за уровнем, TP от предсказанного благоприятного хода, оценка по фактическому PnL (первое касание OHLC).

**Architecture:** Добавить разметку fav-таргетов (`target_buy_H6_val`, `target_buy_H12_val`, `target_sell_H6_val`, `target_sell_H12_val`) в `label_signals.py`, написать торговый симулятор (first-touch SL/TP/TIMEOUT по спецификации), обучить RF-регрессор для fav_val, объединить с breach-классификатором через торговое правило. Grid search порогов на val (только canonical spread 0.20), frozen test через `--frozen-rule` JSON.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn (RandomForestClassifier, RandomForestRegressor), pytest.

**Spec:** `docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md` (стр. 173–333)

---

## Пререквизиты

Stage 1 завершён. Данные размечены breach-таргетами. Frozen test подтвердил сигнал.

- `DATA/Nero_XAUUSD_train_labeled.csv` — breach колонки присутствуют
- `DATA/Nero_XAUUSD_validation_labeled.csv` — breach колонки присутствуют
- `DATA/Nero_XAUUSD_test_labeled.csv` — breach колонки присутствуют
- `DATA/XAUUSD_H1_OHLC.csv` — H1 бары для first-touch оценки

---

## Feature Contract (расширение Stage 1)

### Новые regression таргеты (fav) — разделены по H

| Колонка | Формула | Значение |
|---------|---------|----------|
| `target_buy_H6_val` | `max(High[row+1:row+6] - Open[row+1]) / ATR` | Благоприятный ход BUY за 6 баров, ATR |
| `target_buy_H12_val` | `max(High[row+1:row+12] - Open[row+1]) / ATR` | Благоприятный ход BUY за 12 баров, ATR |
| `target_sell_H6_val` | `max(Open[row+1] - Low[row+1:row+6]) / ATR` | Благоприятный ход SELL за 6 баров, ATR |
| `target_sell_H12_val` | `max(Open[row+1] - Low[row+1:row+12]) / ATR` | Благоприятный ход SELL за 12 баров, ATR |

- Не заполняются для противоположной стороны (NaN)
- `Open[row+1]` ищется в OHLC по времени строки
- При нехватке будущих баров для данного H — NaN для этой колонки
- Итого 4 колонки: `target_buy_H6_val`, `target_buy_H12_val`, `target_sell_H6_val`, `target_sell_H12_val`

### Новые торговые колонки (для оценки)

| Колонка | Тип | Значение |
|---------|-----|----------|
| `entry_price` | float | `Open[row+1]` |
| `stop_buy_price` | float | `min(fractal_price, entry_price) - stop_offset_val * ATR` |
| `stop_sell_price` | float | `max(fractal_price, entry_price) + stop_offset_val * ATR` |
| `stop_buy_val` | float | `(entry_price - stop_buy_price) / ATR` |
| `stop_sell_val` | float | `(stop_sell_price - entry_price) / ATR` |
| `tp_buy_price` | float | `entry_price + tp_val * ATR` (только при enter_buy) |
| `tp_sell_price` | float | `entry_price - tp_val * ATR` (только при enter_sell) |
| `outcome_pnl_H_val` | float | PnL сделки в ATR |
| `outcome_pnl_H_r` | float | PnL сделки в единицах риска |
| `outcome_exit_H` | str | `TP`, `SL`, `TIMEOUT` |
| `ambiguous_flag` | int | `1` если в одном баре задеты и TP и SL |

Торговые колонки не являются таргетами для обучения. Они вычисляются trading evaluator на лету во время оценки модели.

### Denylist (расширение)

Добавить к denylist Stage 1:
- `target_buy_H6_val`, `target_buy_H12_val`, `target_sell_H6_val`, `target_sell_H12_val`
- `entry_price`
- Все колонки `stop_*`, `tp_*`, `outcome_*`, `ambiguous_flag`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `processing/label_signals.py` | MODIFY | + `label_fractal_stop_fav_targets()`, + `evaluate_fractal_stop_trade()` |
| `processing/label_main.py` | MODIFY | + `--fractal-stop-fav` флаг, вызов fav labeling |
| `tests/processing/test_fractal_stop_fav.py` | CREATE | Тесты: fav labeling (4 теста), trade evaluation (5 тестов) |
| `statistics/data_contract_smoke_check.py` | MODIFY | + проверка fav колонок и значений |
| `ML/baseline/benchmark_fractal_stop_fav.py` | CREATE | RF regressor + breach classifier + trade evaluation + grid search |
| `docs/superpowers/plans/2026-06-10-fractal-stop-fav-plan.md` | OUTPUT | Этот план |

---

## Решения по открытым вопросам спецификации

| Вопрос | Решение | Обоснование |
|--------|---------|-------------|
| stop_offset_val | 0.2, 0.5 | Stage 1: оба дают lift > 1.5. 1.0 — ablation |
| BUY/SELL: одна или две модели | Отдельные breach-классификаторы + отдельные fav-регрессоры, как в Stage 1 | Проще, позволяет видеть асимметрию |
| Минимум lift для перехода | Неприменимо к Stage 2 — здесь PF > 1.0 на val | |
| Spread для XAUUSD H1 | 0.20 (canonical) | Из limit-order эксперимента |
| Минимум сделок для допуска | ≥ 30/год на val | Статистическая значимость |

---

### Task 1: Fav-таргеты + торговый симулятор в `label_signals.py`

**Files:** Modify `processing/label_signals.py`

- [ ] **Step 1: Добавить `label_fractal_stop_fav_targets()`**

После `label_fractal_stop_breach()` (около строки 1544), добавить:

```python
def label_fractal_stop_fav_targets(df, ohlc_path, debug=False):
    """
    Разметка благоприятного хода (fav) для торгового слоя Stage 2.

    Для каждой строки с валидным fractal0.dir вычисляется:
      target_<side>_H<h>_val = max(|благоприятный_ход|) / ATR  за h баров от Open[row+1]

    Колонки: target_buy_H6_val, target_buy_H12_val, target_sell_H6_val, target_sell_H12_val.
    NaN для неприменимых строк (противоположная сторона, нет данных).

    Возвращает df с новыми колонками.
    """
    from datetime import datetime, timezone

    ohlc, times, time_idx = load_ohlc_index(ohlc_path)

    FAV_COLUMNS = [
        'target_buy_H6_val', 'target_buy_H12_val',
        'target_sell_H6_val', 'target_sell_H12_val',
    ]
    for col in FAV_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    for i, row in df.iterrows():
        fractal0 = parse_fractal(row.get('fractal0'))
        if fractal0 is None:
            continue

        fractal_dir = fractal0['direction']
        if fractal_dir == 0:
            continue

        row_time = row.get('time')
        if pd.isna(row_time) or row_time == '':
            continue
        try:
            row_dt = datetime.strptime(str(row_time), "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        idx0 = time_idx.get(row_dt)
        if idx0 is None:
            continue

        try:
            atr = float(row['ATR'])
        except (ValueError, KeyError):
            continue
        if atr <= 0:
            continue

        # entry_price = Open[row+1]
        if idx0 + 1 >= len(times):
            continue
        entry_dt = times[idx0 + 1]
        entry_price = ohlc[entry_dt][0]  # open

        for h in (6, 12):
            if idx0 + h >= len(times):
                continue

            # Собрать High/Low за окно [row+1 : row+h]
            highs = []
            lows = []
            for k in range(idx0 + 1, idx0 + 1 + h):
                _, high, low, _ = ohlc[times[k]]
                highs.append(high)
                lows.append(low)

            # BUY: благоприятный ход вверх (fractal_dir == -1 → direction == 1 = buy)
            if fractal_dir == -1:
                fav = (max(highs) - entry_price) / atr
                df.at[i, f'target_buy_H{h}_val'] = max(0.0, fav)
            # SELL: благоприятный ход вниз (fractal_dir == 1 → direction == -1 = sell)
            elif fractal_dir == 1:
                fav = (entry_price - min(lows)) / atr
                df.at[i, f'target_sell_H{h}_val'] = max(0.0, fav)

    if debug:
        for col in FAV_COLUMNS:
            vals = df[col].dropna()
            if len(vals) > 0:
                print(f'  {col}: n={len(vals)}, mean={vals.mean():.3f}, '
                      f'median={vals.median():.3f}, max={vals.max():.3f}')

    return df
```

- [ ] **Step 2: Добавить `evaluate_fractal_stop_trade()`**

После `label_fractal_stop_fav_targets()`:

```python
def evaluate_fractal_stop_trade(bars_h, direction, entry_price, sl_price, tp_price, atr):
    """
    First-touch оценка сделки по OHLC барам за окно H.

    Правило одного бара (по спецификации):
      если в одном H1-баре задеты и TP, и SL — SL первым, ambiguous_flag = 1.

    ВСЕ PnL возвращаются в ATR-единицах (_val per terminology convention).

    Args:
        bars_h: list of (open, high, low, close) tuples за окно [row+1 : row+H]
        direction: -1 (BUY) или 1 (SELL)
        entry_price: float (цена входа, уже со spread)
        sl_price: float
        tp_price: float (уже со spread)
        atr: float (для нормировки PnL)

    Returns:
        dict: {
            'exit': 'TP' | 'SL' | 'TIMEOUT',
            'pnl_val': float  (PnL в ATR),
            'ambiguous': 0 | 1,
        }
    """
    for o, h, l, c in bars_h:
        if direction == -1:  # BUY
            hit_sl = l <= sl_price
            hit_tp = h >= tp_price
        else:  # SELL
            hit_sl = h >= sl_price
            hit_tp = l <= tp_price

        if hit_sl and hit_tp:
            # ambiguous bar: SL first per spec
            if direction == -1:
                return {'exit': 'SL', 'pnl_val': -(entry_price - sl_price) / atr, 'ambiguous': 1}
            else:
                return {'exit': 'SL', 'pnl_val': -(sl_price - entry_price) / atr, 'ambiguous': 1}
        if hit_tp:
            if direction == -1:
                return {'exit': 'TP', 'pnl_val': (tp_price - entry_price) / atr, 'ambiguous': 0}
            else:
                return {'exit': 'TP', 'pnl_val': (entry_price - tp_price) / atr, 'ambiguous': 0}
        if hit_sl:
            if direction == -1:
                return {'exit': 'SL', 'pnl_val': -(entry_price - sl_price) / atr, 'ambiguous': 0}
            else:
                return {'exit': 'SL', 'pnl_val': -(sl_price - entry_price) / atr, 'ambiguous': 0}

    # TIMEOUT: закрытие по последнему Close
    close_h = bars_h[-1][3]
    if direction == -1:
        timeout_pnl = (close_h - entry_price) / atr
    else:
        timeout_pnl = (entry_price - close_h) / atr
    return {'exit': 'TIMEOUT', 'pnl_val': timeout_pnl, 'ambiguous': 0}
```

### Task 2: Подключение в `label_main.py`

**Files:** Modify `processing/label_main.py`

- [ ] **Step 1: Добавить CLI-флаг**

```python
parser.add_argument('--fractal-stop-fav', action='store_true',
                    help='Разметить fav target для fractal stop (Stage 2)')
```

- [ ] **Step 2: Импортировать**

```python
from label_signals import label_fractal_stop_fav_targets
```

- [ ] **Step 3: Вызвать в пайплайне**

После блока `--fractal-stop-breach`:

```python
if args.fractal_stop_fav:
    labeled_df = label_fractal_stop_fav_targets(labeled_df, ohlc_path=args.ohlc, debug=args.debug)
```

---

### Task 3: Тесты fav-разметки и торгового симулятора

**Files:** Create `tests/processing/test_fractal_stop_fav.py`

Паттерн: `test_fractal_stop_breach_labels.py` — синтетические OHLC/DataFrame, `tempfile.TemporaryDirectory`.

- [ ] **Step 1: Базовая структура**

```python
import os, sys, tempfile
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, 'processing')
import label_signals as ls

LABEL_FAV = ls.label_fractal_stop_fav_targets
EVAL_TRADE = ls.evaluate_fractal_stop_trade

def _make_ohlc_csv(path, rows):
    df = pd.DataFrame(rows, columns=['time', 'open', 'high', 'low', 'close'])
    df.to_csv(path, sep=';', index=False)

def _make_nero_df(times, atr_vals, fractal0_vals):
    return pd.DataFrame({
        'time': times,
        'fractal0': fractal0_vals,
        'ATR': atr_vals,
    })

def _fractal_str(price, direction):
    return f'123:{price}:{direction}:1.0:2.0:0:0:0.0:0.0:0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0:0'
```

- [ ] **Step 2: Тесты fav-разметки** (колонки H-specific)

```python
class TestFavTargets:
    def test_buy_fav_H6_val(self):
        """BUY: entry=1502, high reaches 1510 → fav = 8/20 = 0.4."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1501.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1502.0, 1510.0, 1501.0, 1508.0),
                ('2020.01.01 02:00', 1508.0, 1509.0, 1506.0, 1507.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],  # BUY
            )
            result = LABEL_FAV(df, ohlc_path)
            assert result.at[0, 'target_buy_H6_val'] == pytest.approx(0.4, abs=0.01)
            assert pd.isna(result.at[0, 'target_sell_H6_val'])

    def test_sell_fav_H6_val(self):
        """SELL: entry=1498, low reaches 1490 → fav = 8/20 = 0.4."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1501.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1498.0, 1499.0, 1490.0, 1492.0),
                ('2020.01.01 02:00', 1492.0, 1495.0, 1491.0, 1493.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, 1)],  # SELL
            )
            result = LABEL_FAV(df, ohlc_path)
            assert result.at[0, 'target_sell_H6_val'] == pytest.approx(0.4, abs=0.01)
            assert pd.isna(result.at[0, 'target_buy_H6_val'])

    def test_fav_H_differ(self):
        """H12 > H6 строго: максимум High находится после 6-го бара."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            rows = [('2020.01.01 00:00', 1500.0, 1501.0, 1499.0, 1500.0)]
            rows.append(('2020.01.01 01:00', 1502.0, 1502.0, 1501.0, 1502.0))  # entry=1502
            # Бары 2–6: High не выше 1505
            for k in range(2, 7):
                rows.append((f'2020.01.01 {k:02d}:00', 1502.0, 1505.0, 1501.0, 1503.0))
            # Бар 7: High=1520 — только в H12
            rows.append(('2020.01.01 07:00', 1503.0, 1520.0, 1502.0, 1515.0))
            for k in range(8, 14):
                rows.append((f'2020.01.01 {k:02d}:00', 1510.0, 1512.0, 1508.0, 1510.0))
            _make_ohlc_csv(ohlc_path, rows)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],
            )
            result = LABEL_FAV(df, ohlc_path)
            h6 = result.at[0, 'target_buy_H6_val']
            h12 = result.at[0, 'target_buy_H12_val']
            # H6: entry=1502, max_high в окне idx+1..idx+6 = 1505 → (1505-1502)/20 = 0.15
            # H12: max_high в окне idx+1..idx+12 = 1520 → (1520-1502)/20 = 0.9
            assert h12 > h6, f'H12={h12} должно быть строго больше H6={h6}'
            assert h6 == pytest.approx(0.15, abs=0.01)
            assert h12 == pytest.approx(0.9, abs=0.01)

    def test_fav_no_entry_bar(self):
        """Нет Open[row+1] → NaN."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1501.0, 1499.0, 1500.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],
            )
            result = LABEL_FAV(df, ohlc_path)
            assert pd.isna(result.at[0, 'target_buy_H6_val'])
            assert pd.isna(result.at[0, 'target_sell_H6_val'])
```

- [ ] **Step 3: Тесты торгового симулятора** (pnl_val в ATR, передан atr)

```python
class TestTradeEvaluator:
    ATR = 20.0

    def test_buy_tp_hit(self):
        """BUY: entry=1500, SL=1490, TP=1520. High=1525 → TP first. PnL=(1520-1500)/20=1.0."""
        bars = [
            (1501.0, 1510.0, 1500.0, 1505.0),
            (1505.0, 1525.0, 1504.0, 1520.0),
        ]
        result = EVAL_TRADE(bars, direction=-1, entry_price=1500.0,
                           sl_price=1490.0, tp_price=1520.0, atr=self.ATR)
        assert result['exit'] == 'TP'
        assert result['pnl_val'] == pytest.approx(1.0, abs=0.01)
        assert result['ambiguous'] == 0

    def test_buy_sl_hit(self):
        """BUY: entry=1500, SL=1490. Low=1485 → SL. PnL=-(1500-1490)/20=-0.5."""
        bars = [
            (1501.0, 1502.0, 1485.0, 1490.0),
        ]
        result = EVAL_TRADE(bars, direction=-1, entry_price=1500.0,
                           sl_price=1490.0, tp_price=1520.0, atr=self.ATR)
        assert result['exit'] == 'SL'
        assert result['pnl_val'] == pytest.approx(-0.5, abs=0.01)
        assert result['ambiguous'] == 0

    def test_buy_ambiguous(self):
        """BUY: в одном баре и TP и SL → SL first, ambiguous=1."""
        bars = [
            (1490.0, 1525.0, 1480.0, 1505.0),
        ]
        result = EVAL_TRADE(bars, direction=-1, entry_price=1500.0,
                           sl_price=1490.0, tp_price=1520.0, atr=self.ATR)
        assert result['exit'] == 'SL'
        assert result['ambiguous'] == 1

    def test_buy_timeout(self):
        """BUY: ни SL ни TP. Close[H]=1510. PnL=(1510-1500)/20=0.5."""
        bars = [
            (1501.0, 1505.0, 1495.0, 1503.0),
            (1503.0, 1508.0, 1501.0, 1510.0),
        ]
        result = EVAL_TRADE(bars, direction=-1, entry_price=1500.0,
                           sl_price=1480.0, tp_price=1530.0, atr=self.ATR)
        assert result['exit'] == 'TIMEOUT'
        assert result['pnl_val'] == pytest.approx(0.5, abs=0.01)
        assert result['ambiguous'] == 0

    def test_sell_tp_hit(self):
        """SELL: entry=1500, SL=1510, TP=1480. Low=1475 → TP. PnL=(1500-1480)/20=1.0."""
        bars = [
            (1499.0, 1501.0, 1475.0, 1485.0),
        ]
        result = EVAL_TRADE(bars, direction=1, entry_price=1500.0,
                           sl_price=1510.0, tp_price=1480.0, atr=self.ATR)
        assert result['exit'] == 'TP'
        assert result['pnl_val'] == pytest.approx(1.0, abs=0.01)
        assert result['ambiguous'] == 0
```

- [ ] **Step 4: Запустить тесты — должны упасть**

```bash
source ~/git/SoSimple/.venv/bin/activate
python -m pytest tests/processing/test_fractal_stop_fav.py -v
```
Expected: FAIL (функции ещё не реализованы полностью — реализовать до зелёных).

---

### Task 4: Разметка реальных данных и smoke check

**Files:** Modify `statistics/data_contract_smoke_check.py`

- [ ] **Step 1: Разметить fav на существующих сплитах**

```bash
source ~/git/SoSimple/.venv/bin/activate
python -c "
from processing.label_signals import label_fractal_stop_fav_targets
import pandas as pd
for split in ['train', 'validation', 'test']:
    path = f'DATA/Nero_XAUUSD_{split}_labeled.csv'
    df = pd.read_csv(path, sep=';')
    df = label_fractal_stop_fav_targets(df, 'DATA/XAUUSD_H1_OHLC.csv', debug=True)
    df.to_csv(path, sep=';', index=False)
    print(f'{split}: {len(df)} rows saved')
"
```

- [ ] **Step 2: Дополнить smoke check**

После breach-проверок добавить:

```python
    # Проверка fav-колонок (fractal stop Stage 2) — H-specific
    FAV_COLUMNS = [
        'target_buy_H6_val', 'target_buy_H12_val',
        'target_sell_H6_val', 'target_sell_H12_val',
    ]
    for col in FAV_COLUMNS:
        check(f'{name}: колонка {col} существует', col in df.columns)
        if col in df.columns:
            vals = df[col].dropna()
            if len(vals) > 0:
                check(f'{name}: {col} >= 0', (vals >= 0).all())
                check(f'{name}: {col} mean ∈ (0, 5) ATR',
                      0 < vals.mean() < 5.0)
```

- [ ] **Step 3: Запустить smoke check**

```bash
python statistics/data_contract_smoke_check.py
```

---

### Task 5: RF baseline с торговым слоем

**Files:** Create `ML/baseline/benchmark_fractal_stop_fav.py`

Образец: `ML/baseline/benchmark_fractal_stop_breach.py`.

Скрипт делает:

1. Загружает train + val (purge H=12 баров)
2. Извлекает 1001 признак (как в Stage 1)
3. Для каждого H ∈ {6, 12} и off ∈ {0.2, 0.5}:
   a. Обучает RF-классификатор для breach (как в Stage 1)
   b. Обучает RF-регрессор для fav_val
   c. На val: применяет торговое правило с grid search порогов
   d. Вычисляет PnL через `evaluate_fractal_stop_trade()`
   e. Считает метрики: PF, сделок/год, убыточные годы, BUY/SELL split, timeout%, ambiguous%

- [ ] **Step 1: Импорты и конфигурация**

```python
# =============================================================================
# Файл: ML/baseline/benchmark_fractal_stop_fav.py
# Назначение: RF breach + fav → торговый слой → PnL (Stage 2)
# ...
# =============================================================================

import argparse, json, os, sys, csv
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import roc_auc_score, average_precision_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'processing'))
from label_signals import (
    load_ohlc_index,
    evaluate_fractal_stop_trade,
    parse_fractal,
)

# Feature contract: same as Stage 1
BASE_CHANNEL_KEYS = [
    'price', 'direction', 'front', 'back', 'strong',
    'break', 'reverse', 'power', 'count', 'impulse',
]
```

- [ ] **Step 2: Извлечение признаков** — идентично Stage 1 (`extract_flat_base_features`)

- [ ] **Step 3: Загрузка данных** — `load_split()` с year и purge, идентично Stage 1

- [ ] **Step 4: Entry price lookup**

```python
def lookup_entry_prices(df, ohlc_path):
    """Добавить колонку entry_price = Open[row+1]."""
    ohlc, times, time_idx = load_ohlc_index(ohlc_path)
    entries = []
    for _, row in df.iterrows():
        try:
            row_dt = datetime.strptime(str(row['time']), "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            entries.append(np.nan)
            continue
        idx0 = time_idx.get(row_dt)
        if idx0 is None or idx0 + 1 >= len(times):
            entries.append(np.nan)
        else:
            entries.append(ohlc[times[idx0 + 1]][0])  # open
    return np.array(entries, dtype=np.float64)
```

- [ ] **Step 5: Trading simulator**

```python
def simulate_trades(df, entry_prices, breach_proba, fav_pred, ohlc_path,
                    side, h, stop_offset, atr_col='ATR',
                    p=0.5, min_fav_val=0.5, min_rr=1.5, tp_fraction=0.5, cap=5.0,
                    spread=0.0):
    """
    Применить торговое правило к val/test данным.

    Для каждой строки с валидным fractal0.dir и достаточным OHLC-окном:
    1. Вычислить stop_price, stop_val
    2. Проверить enter_buy/enter_sell условие
    3. Вычислить tp_price
    4. Запустить evaluate_fractal_stop_trade() для first-touch PnL

    Returns:
        list of dicts: [{exit, pnl_val, stop_val, ambiguous, year}, ...]
    """
    from datetime import datetime, timezone

    ohlc, times, time_idx = load_ohlc_index(ohlc_path)

    trade_direction = -1 if side == 'buy' else 1   # -1=BUY, 1=SELL (spec convention)
    expected_fractal_dir = -1 if side == 'buy' else 1  # BUY: впадина dir==-1, SELL: пик dir==1
    trades = []

    for i, row in df.iterrows():
        # --- Parse fractal: BUY берёт fractal0.dir == -1 (впадина), SELL == 1 (пик) ---
        fractal0 = parse_fractal(row.get('fractal0'))
        if fractal0 is None:
            continue
        if fractal0['direction'] != expected_fractal_dir:
            continue
        if fractal0['direction'] == 0:
            continue
        fractal_price = fractal0['price']

        # --- Time lookup ---
        try:
            row_dt = datetime.strptime(str(row['time']), "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        idx0 = time_idx.get(row_dt)
        if idx0 is None or idx0 + h >= len(times):
            continue

        # --- Entry and stop ---
        entry_price_val = entry_prices[i]
        if np.isnan(entry_price_val):
            continue
        atr_val = float(row[atr_col])
        if atr_val <= 0:
            continue

        pred_break = breach_proba[i]
        pred_fav = fav_pred[i]
        if np.isnan(pred_break) or np.isnan(pred_fav):
            continue

        if trade_direction == -1:  # BUY
            stop_price = min(fractal_price, entry_price_val) - stop_offset * atr_val
            stop_val = (entry_price_val - stop_price) / atr_val
        else:  # SELL
            stop_price = max(fractal_price, entry_price_val) + stop_offset * atr_val
            stop_val = (stop_price - entry_price_val) / atr_val

        if stop_val <= 0:
            continue

        # --- TP (pred_fav * tp_fraction, capped) ---
        tp_val_atr = min(pred_fav * tp_fraction, cap)
        if trade_direction == -1:
            tp_price = entry_price_val + tp_val_atr * atr_val
        else:
            tp_price = entry_price_val - tp_val_atr * atr_val

        # --- Apply spread ---
        if trade_direction == -1:
            entry_spread = entry_price_val + spread
            tp_price_spread = tp_price - spread
            stop_val_actual = (entry_spread - stop_price) / atr_val
        else:
            entry_spread = entry_price_val - spread
            tp_price_spread = tp_price + spread
            stop_val_actual = (stop_price - entry_spread) / atr_val

        if stop_val_actual <= 0:
            continue

        # --- Trading rule (на фактическом риске после spread) ---
        if pred_break >= p:
            continue
        if pred_fav < min_fav_val:
            continue
        if pred_fav / stop_val_actual < min_rr:
            continue

        # --- First-touch evaluation (uses spread-adjusted prices) ---
        bars_h = []
        for k in range(idx0 + 1, idx0 + 1 + h):
            o, hi, lo, c = ohlc[times[k]]
            bars_h.append((o, hi, lo, c))

        outcome = evaluate_fractal_stop_trade(
            bars_h, trade_direction, entry_spread, stop_price, tp_price_spread, atr_val
        )

        year = row.get('_year', np.nan)
        trades.append({
            'exit': outcome['exit'],
            'pnl_val': outcome['pnl_val'],
            'stop_val': stop_val_actual,
            'pnl_r': outcome['pnl_val'] / stop_val_actual if stop_val_actual > 0 else outcome['pnl_val'],
            'ambiguous': outcome['ambiguous'],
            'year': int(year) if not pd.isna(year) else None,
            'side': side,
        })

    return trades
```

- [ ] **Step 6: Метрики торгового слоя**

```python
def compute_trade_metrics(trades):
    """PF, сделок/год, убыточные годы, timeout%, ambiguous%."""
    if len(trades) == 0:
        return {'n_trades': 0, 'status': 'no_trades'}

    df_t = pd.DataFrame(trades)
    gross_profit = df_t[df_t['pnl_val'] > 0]['pnl_val'].sum()
    gross_loss = abs(df_t[df_t['pnl_val'] < 0]['pnl_val'].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    yearly = df_t.groupby('year').agg(
        n=('pnl_val', 'count'),
        pf=('pnl_val', lambda x: x[x > 0].sum() / abs(x[x < 0].sum()) if (x < 0).any() else float('inf')),
        total_pnl=('pnl_val', 'sum'),
    ).to_dict('index')

    negative_years = sum(1 for y in yearly.values()
                         if y['pf'] < 1.0 and y['n'] >= 5)

    buy_side = df_t[df_t['side'] == 'buy']
    sell_side = df_t[df_t['side'] == 'sell']

    return {
        'n_trades': len(trades),
        'pf': round(pf, 3),
        'timeout_pct': round((df_t['exit'] == 'TIMEOUT').mean(), 3),
        'ambiguous_pct': round(df_t['ambiguous'].mean(), 3),
        'trades_per_year': round(len(trades) / len(yearly), 1) if yearly else 0,
        'negative_years': negative_years,
        'n_years': len(yearly),
        'yearly': yearly,
        'buy': {
            'n': len(buy_side),
            'pf': round(buy_side[buy_side['pnl_val'] > 0]['pnl_val'].sum() /
                       abs(buy_side[buy_side['pnl_val'] < 0]['pnl_val'].sum()), 3)
                   if (buy_side['pnl_val'] < 0).any() and len(buy_side) > 0 else None,
        } if len(buy_side) > 0 else None,
        'sell': {
            'n': len(sell_side),
            'pf': round(sell_side[sell_side['pnl_val'] > 0]['pnl_val'].sum() /
                       abs(sell_side[sell_side['pnl_val'] < 0]['pnl_val'].sum()), 3)
                   if (sell_side['pnl_val'] < 0).any() and len(sell_side) > 0 else None,
        } if len(sell_side) > 0 else None,
    }
```

- [ ] **Step 7: Основной цикл — обучение + grid search**

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--test', default=None, help='Frozen test (только после freeze)')
    parser.add_argument('--frozen-rule', default=None,
                        help='JSON с замороженными параметрами (H, off, side, p, min_fav_val, '
                             'min_rr, tp_fraction, cap, hyperparams). Только с --test. '
                             'Запрещает grid search.')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--purge-bars', type=int, default=12)
    parser.add_argument('--output-json', default='ML/reports/fractal_stop_fav.json')
    parser.add_argument('--n-estimators', type=int, default=200)
    parser.add_argument('--max-depth', type=int, default=12)
    parser.add_argument('--spread', type=float, default=0.20,
                        help='Spread для ордера (canonical XAUUSD H1)')
    parser.add_argument('--spread-stress', type=float, default=0.40,
                        help='2x spread stress test')
    args = parser.parse_args()
    # ... реализация ...
```

Grid search параметров на val:

```python
P_GRID = [0.3, 0.4, 0.5]           # макс допустимая P(пробой)
MIN_FAV_GRID = [0.3, 0.5, 0.7]     # мин ожидаемый fav ход (ATR)
MIN_RR_GRID = [1.0, 1.5, 2.0]      # мин отношение fav/stop
TP_FRACTION_GRID = [0.3, 0.5, 0.7]  # доля от pred_fav для TP
CAP = 5.0                            # верхнее ограничение TP
```

Для каждого H ∈ {6, 12}, off ∈ {0.2, 0.5}:
- Обучаем breach classifier на train
- Обучаем fav regressor на train (колонка `target_<side>_H<h>_val`)
- Предсказываем на val
- **Grid search порогов только на canonical spread = 0.20:**
  - Перебираем все комбинации `P_GRID × MIN_FAV_GRID × MIN_RR_GRID × TP_FRACTION_GRID`
  - Лучшая комбинация: max PF при ≥30 сделок/год
- **Spread diagnostic (использует те же пороги, что и canonical):**
  - spread = 0.0 (zero-spread diagnostic — не участвует в выборе победителя)
  - spread = 0.40 (2x stress test — не участвует в выборе победителя)
- Сохраняем frozen rule JSON: `ML/reports/fractal_stop_fav_frozen_rule.json`

**Frozen rule JSON format:**

```json
{
  "h": 12,
  "stop_offset_val": 0.2,
  "side": "sell",
  "p": 0.4,
  "min_fav_val": 0.5,
  "min_rr": 1.5,
  "tp_fraction": 0.5,
  "cap": 5.0,
  "n_estimators": 200,
  "max_depth": 12,
  "min_samples_leaf": 50,
  "selected_on": "val_canonical_spread_0.20",
  "val_pf": 1.35,
  "val_trades_per_year": 42.0
}
```

- [ ] **Step 8: Запустить baseline — только val (test заморожен)**

```bash
source ~/git/SoSimple/.venv/bin/activate
python -m ML.baseline.benchmark_fractal_stop_fav
```

Expected: таблица PF, сделок/год, убыточных годов для каждой комбинации H×off×spread. Лучший порог выбран на val. Test не открывается. JSON содержит `"test_not_run": true`.

---

### Task 6: Фикс тестов + регрессия Stage 1

- [ ] **Step 1: Убедиться, что Stage 1 тесты всё ещё PASS**

```bash
python -m pytest tests/processing/test_fractal_stop_breach_labels.py -v
```

- [ ] **Step 2: Убедиться, что Stage 2 тесты PASS**

```bash
python -m pytest tests/processing/test_fractal_stop_fav.py -v
```

- [ ] **Step 3: Smoke check**

```bash
python statistics/data_contract_smoke_check.py
```

---

### Task 7: Frozen test (только после freeze-решения)

**Когда запускать:** после того как frozen rule JSON зафиксирован по результатам val на canonical spread=0.20. **Запрещено:** повторный grid search, перебор параметров, выбор победителя на test.

**Статус test:** test уже использовался в Stage 1 frozen test для решения «переходить ли к Этапу 2». Поэтому Stage 2 frozen test допустим только как OOS-контроль в рамках данного цикла. Результат: **research candidate**, не допуск в рабочий контур. Для рабочего допуска нужен новый forward-период или MT4/tester-подтверждение.

- [ ] **Step 1: Запустить frozen test — читает frozen rule JSON**

```bash
python -m ML.baseline.benchmark_fractal_stop_fav \
  --frozen-rule ML/reports/fractal_stop_fav_frozen_rule.json \
  --test DATA/Nero_XAUUSD_test_labeled.csv \
  --output-json ML/reports/fractal_stop_fav_frozen_test.json
```

**Режим `--frozen-rule`:**
- Читает JSON с замороженными параметрами
- Обучает breach classifier + fav regressor на train+val (purge H баров)
- Оценивает на test с замороженными порогами
- Вычисляет метрики на canonical spread (0.20), stress (0.40), diagnostic (0.0)
- **НИКАКОГО grid search. НИКАКОГО выбора параметров на test.**

- [ ] **Step 2: Сверить test-метрики**

| Метрика (на test) | Критерий |
|---|---|
| RF PF > 1.0 | Сигнал воспроизводится OOS (research candidate) |
| ≥ 30 сделок/год | Статистическая значимость |
| Нет годов с PF < 1.0 и ≥5 сделок | Устойчивость |

---

## Критерии перехода

| Результат Stage 2 | Действие |
|---|---|
| PF > 1.0 на val (canonical spread) + PF > 1.0 на frozen test + ≥30 сделок/год | ✅ Research candidate: план Stage 3 (feature engineering + ablation). НЕ допуск в рабочий контур — нужен новый forward-период или MT4/tester. |
| PF > 1.0 на val, но PF ≤ 1.0 на frozen test | ⚠️ Анализ OOS деградации, проверка на новых данных |
| PF < 1.0 на val при всех порогах | ❌ Торговая постановка не работает на текущих признаках |

## Статус test

Test `2022–2026` вскрыт дважды в рамках одного исследовательского цикла:
1. Stage 1 frozen test: решение «переходить ли к Этапу 2» (AUC breach)
2. Stage 2 frozen test: OOS-контроль торгового слоя (PF)

Оба вскрытия — один цикл спецификации. Результат Stage 2 frozen test не является допуском в рабочий контур. Для допуска требуется:
- Новый forward-период (после 2026), не использованный ни в одном эксперименте
- ИЛИ подтверждение через MT4 Strategy Tester с посекундным моделированием
