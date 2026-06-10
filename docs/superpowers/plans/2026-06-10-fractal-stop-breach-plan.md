# Fractal Stop Breach (Stage 1) — Implementation Plan

> **For agentic workers:** REQUIRED: Use subagent-driven-development to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, предсказывают ли фрактальные признаки будущий пробой уровня `fractal0` за горизонт H ∈ {6,12} баров.

**Architecture:** Добавить разметку breach-таргетов в `label_signals.py`, подключить в `label_main.py`, покрыть тестами. Обучить dummy baseline и RF-классификатор на 10 базовых каналах × 100 фракталов. Оценить AUC/PR-AUC/lift на train + validation; test заморожен до явного freeze-решения.

**Tech Stack:** Python 3.11+, pandas, numpy, scikit-learn (RandomForestClassifier, DummyClassifier), pytest.

**Spec:** `docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md`

---

## Split Manifest

| Сплит | Доля | Приблизительные даты | Purge |
|-------|------|---------------------|-------|
| train | 70% | ~2004 – ~2020 | H баров с хвоста (пересечение с val) |
| validation | 15% | ~2020 – ~2023 | H баров с хвоста (пересечение с test) |
| test | 15% | ~2023 – ~2026 | FROZEN — не использовать до freeze |

**Правило purge:** если окно целевой переменной `H` пересекает границу train→val или val→test, строка исключается из train/val соответственно. При `H=12` удаляются последние 12 строк каждого сплита. Purge применяется при загрузке в baseline-скрипте, не модифицирует CSV.

**Файлы данных:** `DATA/Nero_XAUUSD_train_labeled.csv`, `DATA/Nero_XAUUSD_validation_labeled.csv`, `DATA/Nero_XAUUSD_test_labeled.csv`.

---

## Feature Contract

### Allowlist (10 каналов × 100 фракталов + ATR)

Из каждого фрактала `fractal0`..`fractal99` извлекаются поля (имена из `parse_fractal()`):

| Индекс в строке | Ключ словаря | Смысл | Live-safe? |
|---|---|---|---:|
| 1 | `price` | Цена пика/впадины | ✅ стабильный |
| 2 | `direction` | Направление (±1) | ✅ стабильный |
| 3 | `front` | Движение до фрактала | ✅ стабильный |
| 4 | `back` | Движение после фрактала | ⚠️ эволюционирует; на момент строки — текущее значение |
| 5 | `strong` | Признак разворота тренда | ⚠️ всегда 0 для fractal0, эволюционирует |
| 6 | `break` | Счётчик пробитий | ⚠️ эволюционирует; на момент строки — текущее значение |
| 7 | `reverse` | Сила пробитого уровня | ✅ стабильный |
| 8 | `power` | Сумма сил совпадающих фракталов | ⚠️ эволюционирует |
| 9 | `count` | Количество совпадений по уровню | ⚠️ эволюционирует |
| 10 | `impulse` | Импульс цены | ✅ стабильный |

Плюс `ATR` (строка) — волатильность на момент строки.

Итого: 10 × 100 + 1 = 1001 признак.

**Обоснование live-safe для эволюционирующих полей (`back`, `strong`, `break`, `power`, `count`):** они записаны в `Nero.csv` в состоянии на момент строки. `fractal0` имеет те же начальные значения, что и новый фрактал в реальной торговле. Train/inference mismatch отсутствует. См. `docs/dataset_description.md:82-90`.

### Denylist (запрещены во вход модели)

- `signal` — строится оффлайн по будущему `strong=1` fractal0
- `predict` — строится оффлайн по будущему `back`
- Все колонки `up_3`..`dn_48` строки — таргеты regression_updn
- Все колонки `buy_sl*_tp*`, `sell_sl*_tp*` — таргеты Triple Barrier
- Все колонки `ret_*`, `fav_*`, `adv_*` — entry path таргеты
- Все колонки `trail_*` — trailing stop таргеты
- Все колонки `trade_*`, `archetype_*`, `path_*_class` — diagnostic
- Все колонки `buy_fill_lag`, `sell_fill_lag` — limit-order fill
- Все колонки `session_hour`, `weekday` — контекстные (разрешены, но не извлекаются в этом baseline)
- Все колонки `buy_stop_broken_*`, `sell_stop_broken_*` — breach таргеты (этого этапа)
- `fractal_time` (поле 0) — не используется (только для time-фич, не в этом baseline)
- `shift` (поле 22) — не используется
- `fractal_atr` (поле 21) — не используется (есть row-level ATR)
- Поля `up_3`..`dn_6` (17–20) — не извлекаются (являются короткими горизонтами up/dn)

Сборщик признаков использует явный allowlist (`BASE_CHANNEL_KEYS`), а не схему «всё, кроме denylist».

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `processing/label_signals.py` | MODIFY | + константы `BR_*` и `label_fractal_stop_breach()` |
| `processing/label_main.py` | MODIFY | + флаг `--fractal-stop-breach`, вызов функции |
| `tests/processing/test_fractal_stop_breach_labels.py` | CREATE | 11 тестов: BUY/SELL breach, no-breach, offset/H sensitivity, edge cases |
| `ML/baseline/benchmark_fractal_stop_breach.py` | CREATE | Dummy + RF baseline: обучение на train, оценка на val; test FROZEN (отдельный Task 7) |
| `statistics/data_contract_smoke_check.py` | MODIFY | + проверка breach-колонок и их значений |
| `docs/superpowers/plans/2026-06-10-fractal-stop-breach-plan.md` | OUTPUT | Этот план |

---

### Task 1: Константы и функция разметки в `label_signals.py`

**Files:** Modify `processing/label_signals.py`

- [ ] **Step 1: Добавить константы breach-таргетов**

Вставить после существующих TB-констант (после `TB_TARGET_NAMES`, около строки 548):

```python
# Fractal Stop Breach — константы (Stage 1: только пробой уровня)
BR_BREACH_HORIZONS = (6, 12)
BR_BREACH_OFFSETS = (0.0, 0.2, 0.5)        # 0.0 = diagnostic only
BR_BREACH_OFFSETS_PRIMARY = (0.2, 0.5)       # для отчётов (без diagnostic 0.0)

BR_BREACH_COLUMNS = []
for h in BR_BREACH_HORIZONS:
    for off in BR_BREACH_OFFSETS:
        off_str = f'{int(off * 10):02d}'     # 0.0→00, 0.2→02, 0.5→05
        BR_BREACH_COLUMNS.append(f'buy_stop_broken_H{h}_off{off_str}_flag')
        BR_BREACH_COLUMNS.append(f'sell_stop_broken_H{h}_off{off_str}_flag')
# Итого 12 колонок: buy_stop_broken_H6_off00_flag, ... sell_stop_broken_H12_off05_flag
```

- [ ] **Step 2: Написать `label_fractal_stop_breach()`**

Сигнатура:

```python
def label_fractal_stop_breach(df, ohlc_path, debug=False):
    """
    Разметка пробоя уровня fractal0 за H баров (Stage 1).

    Для каждой строки с валидным fractal0['direction'] вычисляется:
      - stop_price = fractal0['price'] ± stop_offset_val * ATR
      - breach_flag = any(Low/High[row+1 : row+H] touches stop_price)

    Если для заданного H недостаточно будущих баров — значение NaN.
    Противоположная сторона (напр. BUY для SELL-строки) — NaN.

    Колонки: buy_stop_broken_H{h}_off{off}_flag / sell_stop_broken_H{h}_off{off}_flag
    Значения: 0.0 (нет пробоя), 1.0 (пробой), NaN (неприменимо/недостаточно данных).

    Возвращает df с новыми колонками.
    """
```

Логика построчно (псевдокод, отражающий все edge cases):

```python
    ohlc, times, time_idx = load_ohlc_index(ohlc_path)

    for i, row in df.iterrows():
        fractal0 = parse_fractal(row.get('fractal0'))
        if fractal0 is None:
            continue  # все breach колонки остаются NaN

        fractal_dir = fractal0['direction']
        if fractal_dir == 0:
            continue  # нет стороны

        fractal_price = fractal0['price']

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

        for h in BR_BREACH_HORIZONS:
            # Проверка: хватает ли будущих баров
            if idx0 + h >= len(times):
                continue  # H-колонки для этого горизонта остаются NaN

            for off in BR_BREACH_OFFSETS:
                off_str = f'{int(off * 10):02d}'
                stop_offset_price = off * atr

                if fractal_dir == -1:  # BUY: стоп ниже впадины
                    stop_price = fractal_price - stop_offset_price
                    col = f'buy_stop_broken_H{h}_off{off_str}_flag'
                    breach = any(
                        ohlc[times[k]][2] <= stop_price  # low
                        for k in range(idx0 + 1, idx0 + 1 + h)
                    )
                    df.at[i, col] = 1.0 if breach else 0.0
                    # sell-колонка остаётся NaN

                elif fractal_dir == 1:  # SELL: стоп выше пика
                    stop_price = fractal_price + stop_offset_price
                    col = f'sell_stop_broken_H{h}_off{off_str}_flag'
                    breach = any(
                        ohlc[times[k]][1] >= stop_price  # high
                        for k in range(idx0 + 1, idx0 + 1 + h)
                    )
                    df.at[i, col] = 1.0 if breach else 0.0
                    # buy-колонка остаётся NaN

    if debug:
        print(f"\n[FRACTAL_STOP_BREACH]")
        for col in BR_BREACH_COLUMNS:
            vals = df[col]
            n_total = len(vals)
            n_valid = vals.notna().sum()
            n_breach = (vals == 1.0).sum()
            n_no_breach = (vals == 0.0).sum()
            rate = n_breach / n_valid if n_valid > 0 else 0.0
            print(f"  {col}: valid={n_valid}/{n_total}, breach={n_breach} ({rate:.1%})")

    return df
```

**Ключевые точки:**
- `parse_fractal()` возвращает словарь, доступ по ключам `['direction']`, `['price']`.
- Явная проверка `idx0 + h >= len(times)` — если будущих баров меньше H, колонка остаётся NaN.
- Противоположная сторона никогда не заполняется — остаётся NaN.
- Не используется `signal`, `strong`, или любое другое future-derived поле.

- [ ] **Step 3: Проверить diff**

```bash
git diff processing/label_signals.py
```

---

### Task 2: Подключение в `label_main.py`

**Files:** Modify `processing/label_main.py`

- [ ] **Step 1: Добавить CLI-флаг**

В секцию `parser.add_argument` (рядом с `--limit-order`):

```python
parser.add_argument('--fractal-stop-breach', action='store_true',
                    help='Разметить breach target для fractal stop (Stage 1)')
```

- [ ] **Step 2: Импортировать функцию и константы**

В секцию импортов:

```python
from label_signals import label_fractal_stop_breach, BR_BREACH_COLUMNS
```

- [ ] **Step 3: Вызвать в пайплайне**

После блока `label_first_barrier_hit` / `label_limit_order_barriers`, перед нормализацией:

```python
if args.fractal_stop_breach:
    labeled_df = label_fractal_stop_breach(labeled_df, ohlc_path=args.ohlc, debug=args.debug)
```

- [ ] **Step 4: Проверить diff**

```bash
git diff processing/label_main.py
```

---

### Task 3: Тесты разметки

**Files:** Create `tests/processing/test_fractal_stop_breach_labels.py`

Паттерн: `test_limit_order_barriers.py` — синтетические OHLC/DataFrame, `tempfile.TemporaryDirectory`.

- [ ] **Step 1: Базовая структура и хелперы**

```python
import os, sys, tempfile
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, 'processing')
import label_signals as ls

LABEL_FN = ls.label_fractal_stop_breach
BR_BREACH_COLUMNS = ls.BR_BREACH_COLUMNS

def _make_ohlc_csv(path, rows):
    """rows: list of (time, open, high, low, close)."""
    df = pd.DataFrame(rows, columns=['time', 'open', 'high', 'low', 'close'])
    df.to_csv(path, sep=';', index=False)

def _make_nero_df(times, atr_vals, fractal0_vals):
    return pd.DataFrame({
        'time': times,
        'fractal0': fractal0_vals,
        'ATR': atr_vals,
    })

def _fractal_str(price, direction):
    """23 поля: T:P:Dir:Frnt:Back:Strong:Brk:Rev:Pwr:Cnt:Imp:Up12:..."""
    return f'123:{price}:{direction}:1.0:2.0:0:0:0.0:0.0:0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0:0'
```

- [ ] **Step 2: Тест — BUY breach**

```python
class TestBuyBreach:
    def test_buy_breach_H6_off02(self):
        """BUY: valley=1500, off=0.2×ATR=4 → stop=1496, low touches 1495 → breach=1."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1502.0, 1503.0, 1501.0, 1502.0),
                ('2020.01.01 01:00', 1501.0, 1502.0, 1495.0, 1498.0),  # breach
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'buy_stop_broken_H6_off02_flag'] == 1.0
            assert pd.isna(result.at[0, 'sell_stop_broken_H6_off02_flag'])
```

- [ ] **Step 3: Тест — BUY no breach**

```python
    def test_buy_no_breach_H6_off02(self):
        """BUY: цена остаётся выше стопа."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1502.0, 1503.0, 1501.0, 1502.0),
                ('2020.01.01 01:00', 1503.0, 1505.0, 1502.0, 1504.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'buy_stop_broken_H6_off02_flag'] == 0.0
```

- [ ] **Step 4: Тест — SELL breach**

```python
class TestSellBreach:
    def test_sell_breach_H6_off02(self):
        """SELL: peak=1500, off=0.2×ATR=4 → stop=1504, high touches 1505 → breach=1."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1498.0, 1499.0, 1497.0, 1498.0),
                ('2020.01.01 01:00', 1499.0, 1505.0, 1498.0, 1502.0),  # breach
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, 1)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'sell_stop_broken_H6_off02_flag'] == 1.0
            assert pd.isna(result.at[0, 'buy_stop_broken_H6_off02_flag'])
```

- [ ] **Step 5: Тест — offset sensitivity**

```python
    def test_sell_offset_sensitivity(self):
        """Больший offset → дальше стоп → меньше breach.
        off=0.2: stop=1504, high=1505 → breach=1.0
        off=0.5: stop=1510, high=1505 → breach=0.0
        """
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1498.0, 1499.0, 1497.0, 1498.0),
                ('2020.01.01 01:00', 1499.0, 1505.0, 1498.0, 1502.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, 1)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'sell_stop_broken_H6_off02_flag'] == 1.0
            assert result.at[0, 'sell_stop_broken_H6_off05_flag'] == 0.0
```

- [ ] **Step 6: Тест — H12 даёт больше breach чем H6**

```python
    def test_longer_horizon_more_breaches(self):
        """H=12 захватывает breach на 8-м баре, H=6 — нет."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            rows = [('2020.01.01 00:00', 1498.0, 1499.0, 1497.0, 1498.0)]
            for k in range(1, 13):
                rows.append((f'2020.01.01 {k:02d}:00', 1499.0, 1500.0, 1498.0, 1499.0))
            rows[8] = (f'2020.01.01 08:00', 1499.0, 1505.0, 1498.0, 1502.0)  # breach at bar 8
            _make_ohlc_csv(ohlc_path, rows)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, 1)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'sell_stop_broken_H6_off02_flag'] == 0.0
            assert result.at[0, 'sell_stop_broken_H12_off02_flag'] == 1.0
```

- [ ] **Step 7: Тест — нехватка будущих баров → NaN**

```python
    def test_insufficient_future_bars(self):
        """7 будущих баров: H6 — ok, H12 — NaN."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            rows = [('2020.01.01 00:00', 1498.0, 1499.0, 1497.0, 1498.0)]
            for k in range(1, 8):  # 7 bars total = 7 future
                rows.append((f'2020.01.01 {k:02d}:00', 1499.0, 1500.0, 1498.0, 1499.0))
            _make_ohlc_csv(ohlc_path, rows)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, 1)],
            )
            result = LABEL_FN(df, ohlc_path)
            # H6: 6 баров ≤ 7 → ok
            assert result.at[0, 'sell_stop_broken_H6_off02_flag'] in (0.0, 1.0)
            # H12: 12 баров > 7 → NaN
            assert pd.isna(result.at[0, 'sell_stop_broken_H12_off02_flag'])
```

- [ ] **Step 8: Тест — все колонки присутствуют**

```python
class TestColumns:
    def test_all_breach_columns_exist(self):
        """Все 12 колонок созданы в выходном DataFrame."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1502.0, 1503.0, 1501.0, 1502.0),
                ('2020.01.01 01:00', 1502.0, 1503.0, 1501.0, 1502.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],
            )
            result = LABEL_FN(df, ohlc_path)
            for col in BR_BREACH_COLUMNS:
                assert col in result.columns, f'{col} not found'
```

- [ ] **Step 9: Edge cases — плохие данные → NaN**

```python
class TestEdgeCases:
    def test_missing_fractal0(self):
        """Пустой fractal0 → все breach колонки NaN."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1502.0, 1503.0, 1501.0, 1502.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[''],
            )
            result = LABEL_FN(df, ohlc_path)
            for col in BR_BREACH_COLUMNS:
                assert pd.isna(result.at[0, col])

    def test_zero_atr(self):
        """ATR=0 → все breach колонки NaN."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1502.0, 1503.0, 1501.0, 1502.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[0.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],
            )
            result = LABEL_FN(df, ohlc_path)
            for col in BR_BREACH_COLUMNS:
                assert pd.isna(result.at[0, col])

    def test_fractal_dir_zero(self):
        """dir=0 → нет стороны → NaN."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1502.0, 1503.0, 1501.0, 1502.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, 0)],
            )
            result = LABEL_FN(df, ohlc_path)
            for col in BR_BREACH_COLUMNS:
                assert pd.isna(result.at[0, col])
```

- [ ] **Step 10: Запустить тесты — должны упасть**

```bash
source ~/git/SoSimple/.venv/bin/activate
python -m pytest tests/processing/test_fractal_stop_breach_labels.py -v
```
Expected: FAIL (функция ещё не реализована).

- [ ] **Step 11: Реализовать `label_fractal_stop_breach()` до зелёных тестов**

Импорты внутри функции:
```python
from datetime import datetime, timezone
# load_ohlc_index уже определена выше в label_signals.py
```

- [ ] **Step 12: Запустить тесты — должны пройти**

```bash
python -m pytest tests/processing/test_fractal_stop_breach_labels.py -v
```
Expected: все 11 тестов PASS.

- [ ] **Step 13: Проверить diff**

```bash
git diff --stat
git diff processing/label_signals.py tests/processing/test_fractal_stop_breach_labels.py
```

---

### Task 4: Разметка реальных данных и smoke check

**Files:** Modify `statistics/data_contract_smoke_check.py`

- [ ] **Step 1: Разметить breach на существующих сплитах**

```bash
source ~/git/SoSimple/.venv/bin/activate
python -c "
from processing.label_signals import label_fractal_stop_breach
import pandas as pd
for split in ['train', 'validation', 'test']:
    path = f'DATA/Nero_XAUUSD_{split}_labeled.csv'
    df = pd.read_csv(path, sep=';')
    df = label_fractal_stop_breach(df, 'DATA/XAUUSD_H1_OHLC.csv', debug=True)
    df.to_csv(path, sep=';', index=False)
    print(f'{split}: {len(df)} rows saved')
"
```

Проверить вывод `debug=True`: доля breach по каждой колонке, число valid/skipped, BUY/SELL split.

- [ ] **Step 2: Дополнить smoke check**

В `statistics/data_contract_smoke_check.py` добавить после существующих проверок TB-колонок:

```python
    # Проверка breach-колонок (fractal stop Stage 1) — внутри цикла for name, path in files.items()
    from processing.label_signals import BR_BREACH_COLUMNS, BR_BREACH_OFFSETS_PRIMARY, BR_BREACH_HORIZONS

    for col in BR_BREACH_COLUMNS:
        check(f'{name}: колонка {col} существует', col in df.columns)
    for col in BR_BREACH_COLUMNS:
        if col in df.columns:
            vals = df[col].dropna()
            if len(vals) > 0:
                check(f'{name}: {col} ∈ {{0,1}}',
                      set(vals.unique()).issubset({0.0, 1.0}))
                rate = vals.mean()
                check(f'{name}: {col} breach_rate={rate:.1%} ∈ (0%, 100%)',
                      0.0 < rate < 1.0)
    for h in BR_BREACH_HORIZONS:
        for off in BR_BREACH_OFFSETS_PRIMARY:
            off_str = f'{int(off * 10):02d}'
            buy_col = f'buy_stop_broken_H{h}_off{off_str}_flag'
            sell_col = f'sell_stop_broken_H{h}_off{off_str}_flag'
            if buy_col in df.columns and sell_col in df.columns:
                buy_rate = df[buy_col].dropna().mean()
                sell_rate = df[sell_col].dropna().mean()
                print(f'  {name} {buy_col}: breach={buy_rate:.1%}, '
                      f'{sell_col}: breach={sell_rate:.1%}')
```

- [ ] **Step 3: Запустить smoke check**

```bash
python statistics/data_contract_smoke_check.py
```
Expected: PASS или явный отчёт о breach-распределениях (асимметрия BUY/SELL ожидаема).

---

### Task 5: Baseline (dummy + RF)

**Files:** Create `ML/baseline/benchmark_fractal_stop_breach.py`

Образец структуры: `ML/baseline/benchmark_limit_order_entry.py`.

- [ ] **Step 1: Создать файл с заголовком и импортами**

```python
# =============================================================================
# Файл: ML/baseline/benchmark_fractal_stop_breach.py
# Назначение: Dummy + RF baseline — предсказание пробоя уровня fractal0 (Stage 1)
# Язык: Python 3.10+
# Обновлён: 2026-06-10
# Зависимости: numpy, pandas, scikit-learn
#   Входные данные: DATA/Nero_XAUUSD_train_labeled.csv, ...validation_labeled.csv
#   Выходные данные: ML/reports/fractal_stop_breach_baseline.json
#   Примечание: test не открывается в Stage 1 (заморожен до freeze-решения)
# Использование:
#   source ~/git/SoSimple/.venv/bin/activate
#   python -m ML.baseline.benchmark_fractal_stop_breach
# =============================================================================

import argparse, json, os, sys
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'processing'))
from label_signals import (
    BR_BREACH_COLUMNS, BR_BREACH_HORIZONS, BR_BREACH_OFFSETS,
    BR_BREACH_OFFSETS_PRIMARY,
)
```

- [ ] **Step 2: Извлечение признаков — allowlist из 10 ключей**

```python
# Feature contract: 10 live-safe каналов × 100 фракталов + ATR
BASE_CHANNEL_KEYS = [
    'price', 'direction', 'front', 'back', 'strong',
    'break', 'reverse', 'power', 'count', 'impulse',
]

def extract_flat_base_features(df, n_fractals=100):
    """Извлечь BASE_CHANNEL_KEYS × n_fractals как плоские float64 признаки + ATR."""
    features = []
    feature_names = []
    for level in range(n_fractals):
        col = f'fractal{level}'
        if col not in df.columns:
            break
        parts = df[col].astype(str).str.split(':', expand=True)
        # Индексы полей в строке: price=1, direction=2, ..., impulse=10
        key_to_idx = {
            'price': 1, 'direction': 2, 'front': 3, 'back': 4,
            'strong': 5, 'break': 6, 'reverse': 7, 'power': 8,
            'count': 9, 'impulse': 10,
        }
        for key in BASE_CHANNEL_KEYS:
            idx = key_to_idx[key]
            vals = pd.to_numeric(parts[idx], errors='coerce').fillna(0.0).values
            features.append(vals.astype(np.float64))
            feature_names.append(f'f{level}_{key}')
    if 'ATR' in df.columns:
        features.append(df['ATR'].values.astype(np.float64))
        feature_names.append('ATR')
    X = np.column_stack(features)
    return X, feature_names
```

- [ ] **Step 3: Загрузка данных с purge и year**

```python
def load_split(path, purge_bars=12):
    """Загрузить сплит, column year, purge H баров с хвоста."""
    df = pd.read_csv(path, sep=';')
    if purge_bars > 0 and len(df) > purge_bars:
        df = df.iloc[:-purge_bars]
    df['_year'] = pd.to_datetime(
        df['time'], format='%Y.%m.%d %H:%M', errors='coerce'
    ).dt.year
    return df
```

- [ ] **Step 4: Метрики — AUC, PR-AUC, lift@20%, годовые срезы**

```python
def compute_metrics(y_true, y_pred_proba, years=None):
    """AUC, PR-AUC, breach_rate, lift@20%. При years — годовые срезы."""
    mask = ~np.isnan(y_true)
    y_true = y_true[mask]
    y_pred_proba = y_pred_proba[mask]
    if years is not None:
        years = years[mask]
    if len(y_true) < 10:
        return None

    # Только один класс — AUC не определён
    unique_classes = np.unique(y_true)
    if len(unique_classes) < 2:
        return {
            'auc': None, 'pr_auc': None,
            'breach_rate': round(float(y_true.mean()), 4),
            'n': int(len(y_true)),
            'note': 'single_class',
        }

    auc = roc_auc_score(y_true, y_pred_proba)
    pr_auc = average_precision_score(y_true, y_pred_proba)
    overall_rate = float(y_true.mean())

    # Lift: bottom 20% по predict → breach rate vs overall
    cutoff = np.quantile(y_pred_proba, 0.20)
    low_risk_mask = y_pred_proba <= cutoff
    low_risk_rate = float(y_true[low_risk_mask].mean()) if low_risk_mask.sum() > 0 else 0.0
    lift = overall_rate / low_risk_rate if low_risk_rate > 0 else float('inf')

    metrics = {
        'auc': round(auc, 4),
        'pr_auc': round(pr_auc, 4),
        'breach_rate': round(overall_rate, 4),
        'low_risk_breach_rate': round(low_risk_rate, 4),
        'lift': round(lift, 2),
        'n': int(len(y_true)),
    }

    if years is not None:
        yearly = {}
        for yr in sorted(set(years)):
            ym = years == yr
            if ym.sum() >= 5:
                yr_unique = np.unique(y_true[ym])
                if len(yr_unique) >= 2:
                    try:
                        yr_auc = roc_auc_score(y_true[ym], y_pred_proba[ym])
                    except ValueError:
                        yr_auc = None
                else:
                    yr_auc = None
                yearly[int(yr)] = {
                    'auc': round(yr_auc, 4) if yr_auc is not None else None,
                    'n': int(ym.sum()),
                    'breach_rate': round(float(y_true[ym].mean()), 4),
                }
        metrics['yearly'] = yearly
    return metrics
```

- [ ] **Step 5: Основной цикл — dummy + RF, только train/val (test не открывается)**

```python
def main():
    parser = argparse.ArgumentParser(description='Baseline: fractal stop breach (Stage 1)')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--target', default=None,
                        help='Конкретная колонка (default: все primary-колонки)')
    parser.add_argument('--purge-bars', type=int, default=12)
    parser.add_argument('--output-json', default='ML/reports/fractal_stop_breach_baseline.json')
    parser.add_argument('--n-estimators', type=int, default=200)
    parser.add_argument('--max-depth', type=int, default=12)
    parser.add_argument('--min-samples-leaf', type=int, default=50)
    parser.add_argument('--include-diagnostic-offsets', action='store_true',
                        help='Включить off00 (diagnostic only) в отчёт')
    args = parser.parse_args()

    train_df = load_split(args.train, args.purge_bars)
    val_df = load_split(args.val, args.purge_bars)

    X_train, feature_names = extract_flat_base_features(train_df)
    X_val, _ = extract_flat_base_features(val_df)

    # Выбор колонок для отчёта
    if args.target:
        targets = [args.target]
    else:
        # Только primary offset (0.2, 0.5); off00 — diagnostic
        targets = []
        for h in BR_BREACH_HORIZONS:
            for off in (BR_BREACH_OFFSETS_PRIMARY if not args.include_diagnostic_offsets
                        else BR_BREACH_OFFSETS):
                off_str = f'{int(off * 10):02d}'
                targets.append(f'buy_stop_broken_H{h}_off{off_str}_flag')
                targets.append(f'sell_stop_broken_H{h}_off{off_str}_flag')

    results = {}

    for target_col in targets:
        y_train = train_df[target_col].values
        y_val = val_df[target_col].values

        train_mask = ~np.isnan(y_train)
        val_mask = ~np.isnan(y_val)

        n_train = train_mask.sum()
        n_val = val_mask.sum()

        if n_train < 50:
            print(f'{target_col}: SKIP (train n={n_train})')
            results[target_col] = {'status': 'SKIP', 'reason': f'train n={n_train}'}
            continue

        train_breach_rate = float(y_train[train_mask].mean())
        print(f'\n--- {target_col} ---')
        print(f'  Train: n={n_train}, breach_rate={train_breach_rate:.3f}')
        print(f'  Val:   n={n_val}')

        X_tr = X_train[train_mask]
        y_tr = y_train[train_mask]
        X_v = X_val[val_mask]
        y_v = y_val[val_mask]

        # --- Dummy baselines ---
        dummy_results = {}
        for strategy in ['most_frequent', 'stratified', 'uniform']:
            dummy = DummyClassifier(strategy=strategy, random_state=42)
            dummy.fit(X_tr, y_tr)
            pred_dummy = dummy.predict_proba(X_v)[:, 1]
            dummy_results[strategy] = compute_metrics(y_v, pred_dummy)
            print(f'  Dummy/{strategy}: AUC={dummy_results[strategy].get("auc", "N/A")}')

        # --- Random Forest ---
        rf = RandomForestClassifier(
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            min_samples_leaf=args.min_samples_leaf,
            random_state=42,
            n_jobs=-1,
        )
        rf.fit(X_tr, y_tr)

        pred_val = rf.predict_proba(X_v)[:, 1]
        val_metrics = compute_metrics(y_v, pred_val, val_df['_year'].values[val_mask])

        results[target_col] = {
            'train_n': int(n_train),
            'train_breach_rate': round(train_breach_rate, 4),
            'val_n': int(n_val),
            'test_not_run': True,
            'dummy': dummy_results,
            'rf_val': val_metrics,
        }

        if val_metrics:
            print(f'  RF val:  AUC={val_metrics.get("auc", "N/A"):.3f} '
                  f'PR-AUC={val_metrics.get("pr_auc", "N/A"):.3f} '
                  f'lift={val_metrics.get("lift", "N/A")}')

    # Сохранить отчёт
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    report = {
        'config': {
            'purge_bars': args.purge_bars,
            'n_estimators': args.n_estimators,
            'max_depth': args.max_depth,
            'min_samples_leaf': args.min_samples_leaf,
            'feature_keys': BASE_CHANNEL_KEYS,
            'n_features': X_train.shape[1],
            'targets': targets,
        },
        'test_not_run': True,
        'results': results,
    }
    with open(args.output_json, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f'\nSaved: {args.output_json}')

if __name__ == '__main__':
    main()
```

- [ ] **Step 6: Запустить baseline (только train + val)**

```bash
source ~/git/SoSimple/.venv/bin/activate
python -m ML.baseline.benchmark_fractal_stop_breach
```

Expected: таблица с Dummy AUC, RF AUC/PR-AUC/lift по 8 primary колонкам на val. Test не открывается. JSON содержит `"test_not_run": true`. Файл: `ML/reports/fractal_stop_breach_baseline.json`.

- [ ] **Step 7: Проверить diff**

```bash
git diff --stat
```

---

### Task 6: Финальная валидация

- [ ] **Step 1: Полный прогон тестов breach-разметки**

```bash
source ~/git/SoSimple/.venv/bin/activate
python -m pytest tests/processing/test_fractal_stop_breach_labels.py -v
```
Expected: все 11 тестов PASS.

- [ ] **Step 2: Smoke check**

```bash
python statistics/data_contract_smoke_check.py
```
Expected: PASS, breach-колонки присутствуют, значения ∈ {0,1}, breach_rate в разумных пределах.

- [ ] **Step 3: Сверить baseline-результаты с критериями спецификации**

| Метрика (на val) | Критерий | Где проверять |
|---|---|---|
| RF AUC > Dummy AUC | Минимум для продолжения | `rf_val.auc` vs `dummy.most_frequent.auc` |
| PR-AUC > случайный | Качество при дисбалансе | `rf_val.pr_auc` > breach_rate |
| Lift > 1.0 в low-risk группе | Практическая полезность | `rf_val.lift` |
| Нет годов с AUC ≈ 0.5 среди >20 сделок | Устойчивость | `rf_val.yearly.*.auc` |
| BUY/SELL показаны раздельно | Нет скрытого провала | Отдельные строки `buy_*` / `sell_*` |

- [ ] **Step 4: Проверить итоговый diff/status**

```bash
git diff --stat
git status
```

Commit не делать без явной команды пользователя.

---

### Task 7: Frozen test (только после freeze-решения)

**Когда запускать:** после того как по результатам val выбраны:
- горизонт H (6 или 12),
- `stop_offset_val` (0.2 или 0.5),
- пороговые критерии (минимальный AUC, lift для Этапа 2),
- гиперпараметры RF.

Параметры заморожены — test открывается **один раз**.

- [ ] **Step 1: Запустить frozen test**

```bash
source ~/git/SoSimple/.venv/bin/activate
python -m ML.baseline.benchmark_fractal_stop_breach \
  --train DATA/Nero_XAUUSD_train_labeled.csv \
  --val DATA/Nero_XAUUSD_validation_labeled.csv \
  --target buy_stop_broken_H6_off02_flag \
  --output-json ML/reports/fractal_stop_breach_frozen_test.json
```

Код frozen-теста: отдельный скрипт или флаг `--test` в том же baseline (добавить на этом шаге). Загружает train + val для обучения, test для однократной оценки. Сохраняет `rf_test` метрики.

- [ ] **Step 2: Сверить test-метрики с ожиданиями**

| Метрика (на test) | Критерий |
|---|---|
| RF AUC > Dummy AUC | Подтверждение сигнала |
| Lift > 1.0 | Практическая полезность на OOS |
| Нет годов с AUC ≈ 0.5 | Устойчивость |

---

## Критерии перехода к Этапу 2 (Торговый слой)

Решение по результатам val (test — только после freeze, см. Task 7):

| Результат Stage 1 | Действие |
|---|---|
| RF AUC > Dummy AUC + lift > 1.5 на ≥2 primary колонках, нет провала по годам | ✅ Пишем план Этапа 2, test-метрики — контрольные |
| RF AUC > Dummy AUC, но lift < 1.2 или провал по годам | ⚠️ Анализируем причину, ablation признаков |
| RF AUC ≈ Dummy AUC на всех колонках | ❌ Этап 2 не начинаем — фрактальные признаки не несут сигнала о пробое |

---

## Открытые вопросы (не блокируют Этап 1)

1. **BUY/SELL: одна модель или две?** Сейчас разметка раздельная — модель для BUY учится только на BUY-строках. Имеет смысл сравнить оба подхода в ablation Этапа 1.
2. **`off00` diagnostic.** `stop_offset_val = 0.0` даёт много breach (стоп на уровне). Включать в основной отчёт только с `--include-diagnostic-offsets`.
3. **Transformer.** Если RF показывает сигнал — проверять ли Transformer? По опыту direction-экспериментов RF работает, Transformer на фракталах — нет. Вопрос для Этапа 2.
