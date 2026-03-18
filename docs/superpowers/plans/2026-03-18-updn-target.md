# Up/Dn Target Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flawed variable-horizon `predict` target with direction-independent fixed-horizon `up_N` / `dn_N` targets, computed incrementally in MQL4 and extracted in Python.

**Architecture:** Up[3]/Dn[3] arrays are added to the PICS struct and accumulated on every bar in `LEVELS_FIND_AROUND()`. The values are written as part of each fractal's data (18 fields instead of 11). Row-level ATR in the CSV is Atr.Slow (baseline volatility); each fractal carries its own F[f].Atr (Atr.Fast at formation). Python computes `ATR_ratio = F[f].Atr / Atr.Slow` per fractal as a model feature. Python `label_updn()` extracts the 6 target columns (up_12, dn_12, up_24, dn_24, up_48, dn_48) by tracking the newest fractal through future rows until its Up/Dn values converge. The predict column is preserved for backward compatibility.

**Tech Stack:** MQL4 (MT4 EA), Python 3.11, pandas

---

## File Map

| File | Change |
|------|--------|
| `MT/MQL4/Include/head_PIC.mqh` | Add `#define H12/H24/H48` + `float Up[3], Dn[3]` to PICS struct |
| `MT/MQL4/Include/lib_PIC.mqh` | 4 edits: init in NEW_LEVEL(), accumulate in LEVELS_FIND_AROUND(), export in NERO_CSV_CREATE() (18 fields, Atr.Slow as row ATR, F[f].Atr per fractal) |
| `processing/label_signals.py` | Extend `parse_fractal()` (18 fields, adds `fractal_atr`), add `label_updn()` |
| `processing/label_main.py` | Import and call `label_updn()` after `label_all()` |
| `ML/data_loader.py` | Update `N_RAW_FEATURES=18`, `N_FRACTAL_FEATURES=17`, replace ATR broadcast with ATR_ratio computation |
| `tests/test_label_updn.py` | New unit test file for Python changes |

---

## Task 1: head_PIC.mqh — Add Up/Dn fields to PICS struct

**Files:**
- Modify: `MT/MQL4/Include/head_PIC.mqh`

> Note: head_PIC.mqh is UTF-16LE encoded. Edit in MT4 editor or use tools that preserve encoding.

- [ ] **Step 1: Add horizon defines before the PICS class**

Find the line `class PICS{  //  C Т Р У К Т У Р А   P I C` and insert BEFORE it:

```cpp
// Горизонты для накопления Up/Dn (индексы массива)
#define H12 0  // 12 баров
#define H24 1  // 24 бара
#define H48 2  // 48 баров
```

- [ ] **Step 2: Add Up/Dn arrays to PICS class**

Find the last field before `};` in PICS class (`TRIANGLE TRG;`) and add AFTER it:

```cpp
float Up[3];   // max(High[i] - P) за горизонт: [H12], [H24], [H48]
float Dn[3];   // max(P - Low[i]) за горизонт: [H12], [H24], [H48]
```

- [ ] **Step 3: Verify the EA compiles in MT4**

Open MT4 → MetaEditor → compile `$o$imple.mq4`. Expected: 0 errors.

---

## Task 2: lib_PIC.mqh — Zero-initialize Up/Dn in NEW_LEVEL()

**Files:**
- Modify: `MT/MQL4/Include/lib_PIC.mqh` (around line 262, after `F[n].PwrSum=PwrSum;`)

- [ ] **Step 1: Find the initialization block in NEW_LEVEL()**

The block around line 262–305 sets `F[n].P`, `F[n].T`, `F[n].Dir`, etc. Find the line:
```cpp
F[n].PwrSum=PwrSum;  // Сумма сил пиков, совпадающих с этим по уровню
```

- [ ] **Step 2: Add Up/Dn initialization after PwrSum**

```cpp
F[n].Up[H12]=0.0f; F[n].Up[H24]=0.0f; F[n].Up[H48]=0.0f;
F[n].Dn[H12]=0.0f; F[n].Dn[H24]=0.0f; F[n].Dn[H48]=0.0f;
```

- [ ] **Step 3: Compile. Expected: 0 errors.**

---

## Task 3: lib_PIC.mqh — Accumulate Up/Dn in LEVELS_FIND_AROUND()

**Files:**
- Modify: `MT/MQL4/Include/lib_PIC.mqh` (around line 368)

- [ ] **Step 1: Add accumulation loop at the START of LEVELS_FIND_AROUND()**

Find line `void EXPERT::LEVELS_FIND_AROUND(){` (line 368) and the first `for (uchar f=1;` loop inside it (line 373). Insert BEFORE that loop:

```cpp
// ─── Up/Dn accumulation — все фракталы, без фильтров ──────────────────────
for (uchar f = 1; f < LevelsAmount; f++) {
   if (F[f].P == 0) continue;
   int dist = SHIFT(F[f].T) - bar;
   if (dist < 0 || dist > 48) continue;  // вне горизонта — пропускаем
   float hmp = H - F[f].P;   // upward excursion from fractal price
   float pml = F[f].P - L;   // downward excursion from fractal price
   if (dist <= 48) {
      if (hmp > F[f].Up[H48]) F[f].Up[H48] = hmp;
      if (pml > F[f].Dn[H48]) F[f].Dn[H48] = pml;
   }
   if (dist <= 24) {
      if (hmp > F[f].Up[H24]) F[f].Up[H24] = hmp;
      if (pml > F[f].Dn[H24]) F[f].Dn[H24] = pml;
   }
   if (dist <= 12) {
      if (hmp > F[f].Up[H12]) F[f].Up[H12] = hmp;
      if (pml > F[f].Dn[H12]) F[f].Dn[H12] = pml;
   }
}
// ─── end Up/Dn accumulation ───────────────────────────────────────────────
```

> **Пояснение**: `SHIFT(F[f].T)` = `iBarShift(NULL, 0, T, false)` (определено в `iGRAPH.mqh`) = bar index фрактала относительно последнего бара. `bar` — это **переменная-член класса EXPERT** (не параметр функции), доступна напрямую. `dist = SHIFT(F[f].T) - bar` = кол-во баров с момента формирования фрактала. Накапливаем пока dist <= 48.

- [ ] **Step 2: Compile. Expected: 0 errors.**

- [ ] **Step 3: Run EA on 100-bar history, spot-check manually**

In MT4 Strategy Tester, run on 200 bars. Open Nero.csv (in `MT/MQL4/Files/`). Find a fractal that formed 50+ bars ago. Its Up[H48] should be > 0. Find a fractal that formed 5 bars ago — its Up[H48] should be small or 0.

---

## Task 4: lib_PIC.mqh — Export Up/Dn in NERO_CSV_CREATE(int cur_bar)

**Files:**
- Modify: `MT/MQL4/Include/lib_PIC.mqh` (around lines 856–880)

- [ ] **Step 1: Change row-level ATR from Atr.Fast to Atr.Slow**

Find line 773:
```cpp
string NeroInfo = BTIME(cur_bar) + ";0;0;" + S4(Atr.Fast);
```
Replace `S4(Atr.Fast)` with `S4(Atr.Slow)`.

- [ ] **Step 2: Extend non-normalized output branch**

Find the non-normalized fractal string block (the `else` branch, around line 884):

```cpp
NeroInfo = NeroInfo + ";" +
           S0(F[f].T) + ":" +
           S4(F[f].P) + ":" +
           S0(F[f].Dir) + ":" +
           S4(F[f].FrntVal) + ":" +
           S4(F[f].BackVal) + ":" +
           S0(F[f].Strong) + ":" +
           S0(F[f].Brk) + ":" +
           S4(F[f].Rev) + ":" +
           S4(F[f].PwrSum) + ":" +
           S0(F[f].Cnt) + ":" +
           S4(F[f].Imp);
```

Replace `S4(F[f].Imp);` with:

```cpp
           S4(F[f].Imp) + ":" +
           S4(F[f].Up[H12]) + ":" + S4(F[f].Dn[H12]) + ":" +
           S4(F[f].Up[H24]) + ":" + S4(F[f].Dn[H24]) + ":" +
           S4(F[f].Up[H48]) + ":" + S4(F[f].Dn[H48]) + ":" +
           S4(F[f].Atr);
```

- [ ] **Step 3: Extend normalized output branch**

Find the normalized fractal string block (the `if (USE_NORMALIZED_OUTPUT)` branch, around line 856). It also ends with `S4(F[f].Dn[H48]);`. Replace:

```cpp
                    S4(F[f].Up[H48]) + ":" + S4(F[f].Dn[H48]);
```
with:
```cpp
                    S4(F[f].Up[H48]) + ":" + S4(F[f].Dn[H48]) + ":" +
                    S4(F[f].Atr);
```

> Note: Up/Dn and fractal_atr exported raw (not normalized) in both branches — Python handles them.

- [ ] **Step 4: Compile. Expected: 0 errors.**

- [ ] **Step 5: Run EA on full history, verify Nero.csv format**

```bash
head -3 MT/MQL4/Files/Nero.csv
```

Each fractal field should have 18 colon-separated values (instead of 11). Example non-zero row:
```
2026.01.15 10:00;0;0;0.00085;1705312800:1.28450:1:0.0034:0.0021:1:0:0.0:0.0025:3:0.0018:0.0015:0.0010:0.0028:0.0019:0.0040:0.0031:0.00092;...
```
(last field = F[f].Atr, 4th field in row header = Atr.Slow)

- [ ] **Step 6: Commit MQL4 changes**

```bash
git add MT/MQL4/Include/head_PIC.mqh MT/MQL4/Include/lib_PIC.mqh
git commit -m "feat(mql4): add Up/Dn targets + fractal_atr to NERO_CSV, row ATR → Atr.Slow"
```

---

## Task 5: Python — Extend parse_fractal() in label_signals.py

**Files:**
- Modify: `processing/label_signals.py:39-88`
- Test: `tests/test_label_updn.py` (create)

- [ ] **Step 1: Write failing test**

Create `tests/test_label_updn.py`:

```python
import sys
import pytest
import pandas as pd
sys.path.insert(0, 'processing')
from label_signals import parse_fractal


FRACTAL_11 = "1705312800:1.28450:1:0.0034:0.0021:1:0:0.0:0.0025:3:0.0018"
FRACTAL_18 = "1705312800:1.28450:1:0.0034:0.0021:1:0:0.0:0.0025:3:0.0018:0.0015:0.0010:0.0028:0.0019:0.0040:0.0031:0.00092"


def test_parse_fractal_11_fields_backward_compat():
    result = parse_fractal(FRACTAL_11)
    assert result is not None
    assert result['up_12'] == 0.0
    assert result['dn_12'] == 0.0
    assert result['up_48'] == 0.0
    assert result['fractal_atr'] == 0.0


def test_parse_fractal_18_fields():
    result = parse_fractal(FRACTAL_18)
    assert result is not None
    assert result['up_12'] == 0.0015
    assert result['dn_12'] == 0.0010
    assert result['up_24'] == 0.0028
    assert result['dn_24'] == 0.0019
    assert result['up_48'] == 0.0040
    assert result['dn_48'] == 0.0031
    assert result['fractal_atr'] == pytest.approx(0.00092, abs=1e-6)


def test_parse_fractal_none_input():
    assert parse_fractal(None) is None
    assert parse_fractal('') is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/hohla/git/SoSimple && source .venv/bin/activate
pytest tests/test_label_updn.py -v
```

Expected: FAIL with `KeyError: 'up_12'`

- [ ] **Step 3: Extend parse_fractal() in label_signals.py**

In `processing/label_signals.py`, find the `return {` block (line 74) and add 7 new keys after `'impulse'`:

```python
        'up_12':      float(parts[11]) if len(parts) > 11 else 0.0,
        'dn_12':      float(parts[12]) if len(parts) > 12 else 0.0,
        'up_24':      float(parts[13]) if len(parts) > 13 else 0.0,
        'dn_24':      float(parts[14]) if len(parts) > 14 else 0.0,
        'up_48':      float(parts[15]) if len(parts) > 15 else 0.0,
        'dn_48':      float(parts[16]) if len(parts) > 16 else 0.0,
        'fractal_atr': float(parts[17]) if len(parts) > 17 else 0.0,
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_label_updn.py::test_parse_fractal_11_fields_backward_compat \
       tests/test_label_updn.py::test_parse_fractal_18_fields \
       tests/test_label_updn.py::test_parse_fractal_none_input -v
```

Expected: 3 PASSED

---

## Task 6: Python — Add label_updn() to label_signals.py

**Files:**
- Modify: `processing/label_signals.py`
- Test: `tests/test_label_updn.py`

- [ ] **Step 1: Write failing test for label_updn()**

Add to `tests/test_label_updn.py` (add these imports/functions to the existing file from Task 5):

```python
# (label_updn will be importable after Task 6 Step 3)
from label_signals import label_updn


def _make_fractal(t, price, up12, dn12, up24, dn24, up48, dn48, strong=0, brk=0, atr=0.001):
    """Helper: build a fractal string with 18 fields."""
    return f"{t}:{price:.5f}:1:0.001:0.001:{strong}:{brk}:0.0:0.001:1:0.001:{up12:.5f}:{dn12:.5f}:{up24:.5f}:{dn24:.5f}:{up48:.5f}:{dn48:.5f}:{atr:.5f}"


def test_label_updn_basic():
    """Fractal0 appears in 3 subsequent rows, last row has final Up/Dn."""
    T0 = 1705312800  # fractal0 time
    T1 = 1705316400  # another fractal (different time)

    # Row 0: fractal0 just formed (Up/Dn = 0)
    # Row 1: fractal0 still present, Up/Dn partially accumulated
    # Row 2: fractal0 still present, Up/Dn fully accumulated
    # Row 3: fractal0 evicted (no longer present)
    rows = [
        {"time": "2026.01.15 10:00", "fractal0": _make_fractal(T0, 1.28, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
         "fractal1": _make_fractal(T1, 1.27, 0.005, 0.003, 0.008, 0.005, 0.012, 0.008)},
        {"time": "2026.01.15 11:00", "fractal0": _make_fractal(T1, 1.27, 0.005, 0.003, 0.008, 0.005, 0.012, 0.008),
         "fractal1": _make_fractal(T0, 1.28, 0.002, 0.001, 0.004, 0.002, 0.0, 0.0)},
        {"time": "2026.01.15 12:00", "fractal0": _make_fractal(T1, 1.27, 0.005, 0.003, 0.008, 0.005, 0.012, 0.008),
         "fractal1": _make_fractal(T0, 1.28, 0.003, 0.002, 0.006, 0.004, 0.010, 0.007)},
        {"time": "2026.01.15 13:00", "fractal0": _make_fractal(T1, 1.27, 0.005, 0.003, 0.008, 0.005, 0.012, 0.008),
         "fractal1": ""},  # T0 evicted
    ]
    df = pd.DataFrame(rows)

    result = label_updn(df)

    # Row 0: target = last found values for T0 = row 2's values
    assert result.at[0, 'up_12'] == pytest.approx(0.003, abs=1e-5)
    assert result.at[0, 'dn_12'] == pytest.approx(0.002, abs=1e-5)
    assert result.at[0, 'up_48'] == pytest.approx(0.010, abs=1e-5)
    # Row 1 (fractal0 is T1, not T0): T1 is in all rows → uses its last appearance
    # (not testing row 1 here — T1 survives till end)


def test_label_updn_fractal0_missing():
    """Row with no fractal0 gets zeros."""
    df = pd.DataFrame([{"time": "2026.01.15 10:00", "fractal0": ""}])
    result = label_updn(df)
    assert result.at[0, 'up_12'] == 0.0
    assert result.at[0, 'up_48'] == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_label_updn.py::test_label_updn_basic tests/test_label_updn.py::test_label_updn_fractal0_missing -v
```

Expected: FAIL with `ImportError: cannot import name 'label_updn'`

- [ ] **Step 3: Implement label_updn() in label_signals.py**

Add after `label_predict_only()` (around line 303):

```python
def label_updn(df, debug=False):
    """
    Извлекает up/dn таргеты для каждой строки из накопленных значений фрактала.

    Алгоритм: для каждой строки i берёт fractal0 (новейший фрактал).
    Сканирует вперёд до тех пор, пока фрактал существует в массиве.
    Берёт последние найденные значения Up/Dn (самые накопленные).
    Записывает в колонки up_12, dn_12, up_24, dn_24, up_48, dn_48.

    Args:
        df (pd.DataFrame): DataFrame с колонками fractalN.
        debug (bool): Флаг отладки.

    Returns:
        pd.DataFrame: DataFrame с добавленными колонками up/dn.
    """
    HORIZONS = [12, 24, 48]
    for h in HORIZONS:
        df[f'up_{h}'] = 0.0
        df[f'dn_{h}'] = 0.0

    fractal_columns = [col for col in df.columns if col.startswith('fractal')]
    rows_list = list(df.itertuples(index=False))
    total_rows = len(rows_list)

    found_count = 0
    for i, row_i in enumerate(rows_list):
        fractal0 = parse_fractal(getattr(row_i, 'fractal0', None))
        if fractal0 is None:
            continue

        target_time = fractal0['time']
        best = fractal0  # Start with row i's own values (Up/Dn = 0 for newest)

        for j in range(i + 1, total_rows):
            found = find_fractal_by_time(rows_list[j], fractal_columns, target_time)
            if found is None:
                break  # Fractal evicted — use best so far
            best = found  # Keep updating until eviction

        for h in HORIZONS:
            df.at[i, f'up_{h}'] = best.get(f'up_{h}', 0.0)
            df.at[i, f'dn_{h}'] = best.get(f'dn_{h}', 0.0)
        found_count += 1

    if debug:
        print(f"[UPDN] Размечено строк: {found_count} / {total_rows}")

    return df
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_label_updn.py -v
```

Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
git add processing/label_signals.py tests/test_label_updn.py
git commit -m "feat(python): extend parse_fractal to 18 fields (+fractal_atr), add label_updn()"
```

---

## Task 7: Python — Add label_updn to pipeline in label_main.py

**Files:**
- Modify: `processing/label_main.py:55` (import), `processing/label_main.py:327` (pipeline)

- [ ] **Step 1: Update import in label_main.py**

Find line 55:
```python
from label_signals import label_all
```
Replace with:
```python
from label_signals import label_all, label_updn
```

- [ ] **Step 2: Add label_updn step to pipeline**

Find step 3 in `main()` (around line 325–327):
```python
    labeled_df = label_all(temp_sorted_path, temp_labeled_path, debug=args.debug)
```
Add immediately after:
```python
    # 3b. Разметка Up/Dn таргетов
    print(f"\nРазметка Up/Dn таргетов...")
    labeled_df = label_updn(labeled_df, debug=args.debug)
```

- [ ] **Step 3: Update summary print at the end**

Find:
```python
    print(f"Метки: signal, predict")
```
Replace with:
```python
    print(f"Метки: signal, predict, up_12, dn_12, up_24, dn_24, up_48, dn_48")
```

- [ ] **Step 4: Run pipeline on real data (requires updated Nero.csv from MQL4)**

```bash
cd /home/hohla/git/SoSimple && source .venv/bin/activate
python processing/label_main.py --no-normalize
```

Expected output includes: `Разметка Up/Dn таргетов...` and `Метки: signal, predict, up_12, dn_12, up_24, dn_24, up_48, dn_48`

Verify new columns exist in output:
```bash
python -c "
import pandas as pd
df = pd.read_csv('DATA/Nero_train_labeled.csv', sep=';', nrows=5)
print(df[['up_12','dn_12','up_24','dn_24','up_48','dn_48']].describe())
"
```

Expected: non-zero values for most rows (not all zeros).

> **Note on normalization**: `normalize_rowwise()` normalizes per-fractal numeric fields (price, front, back, etc.) but does NOT touch the up_12..dn_48 target columns. These columns remain in raw price units — acceptable since they are regression **targets**, not input features. If/when ML training uses them as targets, they should be normalized together with ATR (same RobustScaler used for `predict`). That step is outside scope of this plan.

- [ ] **Step 5: Commit**

```bash
git add processing/label_main.py
git commit -m "feat(pipeline): add label_updn step to label_main.py pipeline"
```

---

## Task 8: Python — Update data_loader.py for 17-field fractals

**Files:**
- Modify: `ML/data_loader.py:43-44` (constants), `ML/data_loader.py:53` (REGRESSION_TARGET)

- [ ] **Step 1: Update constants**

Find:
```python
N_RAW_FEATURES = 11   # Всего полей в строке фрактала (включая fractal_time)
N_FRACTAL_FEATURES = 10  # Без fractal_time → price..impulse
```
Replace with:
```python
N_RAW_FEATURES = 18   # T:P:Dir:FrntVal:BackVal:Strong:Brk:Rev:PwrSum:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:FractalAtr
N_FRACTAL_FEATURES = 17  # Без fractal_time → 17 features per fractal (fields 1-17)
```

- [ ] **Step 2: Replace ATR broadcast with ATR_ratio computation**

Find the ATR broadcast block:
```python
# ATR как 11-й признак (индекс 10), broadcast на все позиции
atr_values = pd.to_numeric(df['ATR'], errors='coerce').fillna(0).values.astype(np.float32)
X[:, :, N_FRACTAL_FEATURES] = atr_values[:, np.newaxis]
```
Replace with:
```python
# ATR_ratio = F[f].Atr (Atr.Fast при формировании) / Atr.Slow (текущий бар, row-level)
# fractal_atr уже в X[:,:,16] (последнее поле из CSV, feat_idx = 17-1 = 16)
atr_slow = pd.to_numeric(df['ATR'], errors='coerce').fillna(1.0).values.astype(np.float32)
denom = np.where(atr_slow > 0, atr_slow, 1.0)
X[:, :, N_FRACTAL_FEATURES - 1] = X[:, :, N_FRACTAL_FEATURES - 1] / denom[:, np.newaxis]
```

Also update the docstring comment above the function (`n_features = N_FRACTAL_FEATURES + 1` becomes `n_features = N_FRACTAL_FEATURES`):

Find:
```python
    # 10 фрактальных features (без fractal_time) + 1 ATR = 11
    n_features = N_FRACTAL_FEATURES + 1
```
Replace with:
```python
    # 17 фрактальных features (без fractal_time); поле 17 (fractal_atr) → ATR_ratio in-place
    n_features = N_FRACTAL_FEATURES
```

- [ ] **Step 3: Update REGRESSION_TARGET and add new target names**

Find:
```python
# Имя колонки для регрессионного таргета
REGRESSION_TARGET = 'predict'
```
Replace with:
```python
# Имя колонки для регрессионного таргета
REGRESSION_TARGET = 'predict'  # backward compat default

# Доступные up/dn таргеты
UPDN_TARGETS = ['up_12', 'dn_12', 'up_24', 'dn_24', 'up_48', 'dn_48']
```

- [ ] **Step 4: Verify data loads without error**

```bash
cd /home/hohla/git/SoSimple && source .venv/bin/activate
python -c "
from ML.data_loader import create_data_loaders
train_loader, val_loader, _ = create_data_loaders(target='predict', seq_len=20)
X, y, mask = next(iter(train_loader))
print('X shape:', X.shape)   # Expected: (batch, 20, 17)
print('y shape:', y.shape)
"
```

Expected: `X shape: (batch_size, 20, 17)` — 17 features per fractal position (price..Dn48 + ATR_ratio).

> Note: `create_data_loaders` signature uses `target=` (not `task=`). Available values: `'signal'`, `'predict'`.

- [ ] **Step 5: Commit**

```bash
git add ML/data_loader.py
git commit -m "feat(ml): update data_loader for 18-field fractals, replace ATR broadcast with ATR_ratio"
```

---

## Task 9: Update documentation

**Files:**
- Modify: `docs/dataset_description.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update fractal structure in dataset_description.md**

Find:
```
fractal_time : price : direction : front : back : strong : break : reverse : power : count : impulse
```
Replace with:
```
fractal_time : price : direction : front : back : strong : break : reverse : power : count : impulse : up_12 : dn_12 : up_24 : dn_24 : up_48 : dn_48
```

Add explanation after the existing field descriptions:

```markdown
### Up/Dn таргеты (накопленные в MQL4):
- up_12 / dn_12 (float) – max(High - P) / max(P - Low) за 12 баров H1 после формирования
- up_24 / dn_24 (float) – то же за 24 бара
- up_48 / dn_48 (float) – то же за 48 баров
- Для новейшего фрактала в момент записи строки = 0; финальные значения читаются из более поздних строк Python'ом
```

- [ ] **Step 2: Add entry to CHANGELOG.md**

Add at the top of CHANGELOG.md:

```markdown
## [2026-03-18] — ME-6: Up/Dn Fixed-Horizon Targets
### Добавлено
- `head_PIC.mqh`: `float Up[3], Dn[3]` в структуру PICS + `#define H12/H24/H48`
- `lib_PIC.mqh`: инкрементальное накопление Up/Dn в `LEVELS_FIND_AROUND()` для всех фракталов
- `lib_PIC.mqh`: row-level ATR заменён на Atr.Slow; экспорт Up/Dn + F[f].Atr как полей 12–18 в `NERO_CSV_CREATE()`
- `label_signals.py`: `parse_fractal()` расширен до 18 полей (+ fractal_atr), новая функция `label_updn()`
- `label_main.py`: шаг `label_updn` добавлен в pipeline
- `data_loader.py`: `N_RAW_FEATURES=18`, `N_FRACTAL_FEATURES=17`, ATR broadcast → ATR_ratio, `UPDN_TARGETS`
### Суть
Заменяем шумный таргет `predict` (переменный горизонт) на direction-independent up/dn с фиксированными горизонтами 12/24/48 баров. Для входа берётся `F[f].P` (цена фрактала).
```

- [ ] **Step 3: Commit docs**

```bash
git add docs/dataset_description.md CHANGELOG.md
git commit -m "docs: update dataset description and changelog for up/dn targets (ME-6)"
```

---

## Execution Notes

### Порядок выполнения
Tasks 1–4 — MQL4 side, requires MT4 editor. Must be done before Task 7 Step 4 (running full pipeline).
Tasks 5–6 — Python unit tests, can be run immediately (no new CSV needed).
Tasks 7–8 — require updated Nero.csv from MQL4 changes.
Task 9 — documentation, do last.

### Проверка корректности Up/Dn
Для spot-check после генерации нового Nero.csv:
```python
import pandas as pd
df = pd.read_csv('DATA/Nero_train_labeled.csv', sep=';')
# Новые таргеты должны быть >0 для большинства строк
print((df['up_48'] > 0).mean())   # ожидаем > 0.9
print((df['dn_48'] > 0).mean())   # ожидаем > 0.9
# up_48 >= up_24 >= up_12 (монотонность по горизонту)
assert (df['up_48'] >= df['up_24']).all()
assert (df['up_24'] >= df['up_12']).all()
```
