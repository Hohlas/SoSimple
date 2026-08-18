# Pair-Spread Kill-Тест (idea-01) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Исполнить пункт 1 роэдмэпа `docs/audit/best_ideas.md`: предрегистрированный двухступенчатый kill-тест парного статистического арбитража (скрининг 7 кандидатов на train ≤ 2022, z-score mean-reversion на test 2023+), без ML.

**Architecture:** Код в `statistics/pair_spread/` — четыре плоских модуля без `__init__.py` (каталог `statistics/` конфликтует со stdlib): `pair_data.py` (загрузка OHLC, кроссы, спреды, сплит), `screening.py` (метрики ступени 1), `backtest.py` (симулятор ступени 2 + stationary bootstrap), `run_pair_spread.py` (оркестратор, JSON-артефакты, таблица вердиктов). Данные — экспорт M5/H1 из MT5 через MQL5-скрипт. Тесты загружают модули через `importlib` по пути к файлу (паттерн `tests/test_mi_upper_bound.py`).

**Tech Stack:** Python (.venv, numpy, pandas, statsmodels — доустанавливается), MQL5 (экспорт истории и спецификаций), pytest.

**Импорт:** `statistics/pair_spread/` не является пакетом. Runner запускается как `.venv/bin/python statistics/pair_spread/run_pair_spread.py` (sys.path[0] = каталог скрипта, импорт `from pair_data import ...`). Тесты — через `importlib.util.spec_from_file_location`.

```text
depends_on: спецификация docs/superpowers/specs/2026-08-17-pair-spread-design.md (коммит 93278c6); данные M5/H1 в MT/MQL4/Files/{M5,H1}
blocks: ничего (следующие идеи роэдмэпа независимы; их очерёдность — по результатам)
supersedes: нет
exit_decisions: все пары убиты → тема закрыта, переход к идее 2 (OCO-стрэддл); есть SURVIVED с N ≥ 100 и BS_p05 > 1.0 → отдельный план production-контура; только DIAGNOSTIC_ONLY (N < 100) → decision memo «мощность недостаточна», опционально тиковая диагностика по разделу 3.3 спеки
locked_test_policy: не используется — этап RESEARCH_ONLY/DIAGNOSTIC_ONLY
```

## Global Constraints

- Python: только `./.venv/bin/python`; тесты: `./.venv/bin/python -m pytest <файл> -q`.
- Все числа из спеки (пороги, окна, правила) заморожены; изменение после первого запуска — только документированным решением.
- Сплит: train 2005-01-01…2022-12-31, test 2023-01-01…конец данных. Ни одна строка test не участвует в оценке β, μ, σ, порогов и издержек.
- Сигналы считаются по close-спреду, исполнение — по open-спреду следующего бара (секция 4 спеки).
- В формуле издержек используется `abs(β)` (уточнение реализации: спека подразумевает β>0, но у mul-кроссов OLS может дать отрицательный β).
- Комиссия = 0; своп для XAUXAG вычитается за ночь удержания до вердикта (раздел 7 спеки). Своп берётся по стороне сделки: side=+1 (long A / short B) платит `swap_long_A + swap_short_B`, side=−1 — `swap_short_A + swap_long_B` (уточнение по аудиту В-6: симметричное приближение отклонено).
- Нормировка издержек в лог-единицы спреда — по последним ценам TRAIN-окна, не по концу ряда (уточнение по аудиту В-5: снимок спецификаций «сегодня» остаётся вне обоих окон как источник самих величин).
- Ожидаемая длина блока bootstrap = медианная длительность эпизодов TRAIN (замораживается в screening.json); test-данные для выбора длины блока не используются (уточнение по аудиту В-1).
- `statistics/pair_spread/` — без `__init__.py`.
- Вердикты: SURVIVED только при PF ≥ 1.3, BS_p05 > 1.0, N ≥ 100 и ≥ 30 на сторону, EG-p на test ≤ 0.10; иначе KILLED или DIAGNOSTIC_ONLY.
- Приоритет вердиктов (конвенция по аудиту Q-1): EG-p(test) > 0.10 → KILLED независимо от числа сделок (мощность EG-теста определяется числом баров, не сделок); гейт N < 100 / < 30 на сторону ограничивает только SURVIVED → DIAGNOSTIC_ONLY. Конвенция фиксируется в отчёте.

---

### Task 0: Регистрация трека в roadmap.md (по аудиту Q-2)

**Files:**
- Modify: `docs/superpowers/roadmap.md`

**Interfaces:**
- Produces: единственный ACTIVE-трек «pair-spread kill-test» в `docs/superpowers/roadmap.md`; прежний ACTIVE-трек «MT5 entry mechanics» перенесён в PARKED с сохранением текущих фактов (правило 1 роэдмэпа — один ACTIVE-трек).

- [ ] **Step 1: Обновить roadmap.md**

В `docs/superpowers/roadmap.md`:
1. Секцию `## ACTIVE` заменить блоком:

```markdown
## ACTIVE

### Pair-spread kill-test (idea-01)

Status: план исполняется (`docs/superpowers/plans/2026-08-17-pair-spread.md`).
Предрегистрированный двухступенчатый kill-тест парного статистического
арбитража, RESEARCH_ONLY/DIAGNOSTIC_ONLY, без `locked_test`.

Next action: исполнение плана по задачам; вердикты — по спеке
`docs/superpowers/specs/2026-08-17-pair-spread-design.md`.
```

2. Текущий блок «MT5 entry mechanics / trade-count frozen probe» целиком
   перенести в `## PARKED Research Directions` в конец секции, сменив статус
   на `PARKED` и добавив условия возврата:

```markdown
### `MT5 entry mechanics / trade-count frozen probe`

[текущие факты блока ACTIVE сохранить дословно]

Условия возврата:

- создан frozen probe plan по entry mechanics / trade-count consolidation;
- `locked_test` не используется для нового выбора.

Статус: `PARKED` (вытеснен ACTIVE-треком pair-spread kill-test).
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/roadmap.md
git commit -m "Register pair-spread kill-test as ACTIVE track, park MT5 entry mechanics"
```

---

### Task 1: Зависимость statsmodels

**Files:**
- Modify: `requirements.txt`

**Interfaces:**
- Produces: `statsmodels` в `.venv` (нужен Task 4: `statsmodels.tsa.stattools.coint`).

Примечание (по итогам аудита): на момент доработки плана statsmodels 0.14.6 уже
установлен в `.venv` аудитором; задача сводится к фиксации в `requirements.txt`.

- [ ] **Step 1: Проверить текущее состояние**

Run: `./.venv/bin/python -c "import statsmodels" ; cat requirements.txt | head -20`
Expected: импорт проходит (или ModuleNotFoundError — тогда установка на шаге 2); statsmodels в requirements.txt может отсутствовать.

- [ ] **Step 2: Установить (если нет) и добавить в requirements**

Run:
```bash
./.venv/bin/pip install statsmodels
grep -q '^statsmodels$' requirements.txt || echo "statsmodels" >> requirements.txt
./.venv/bin/python -c "from statsmodels.tsa.stattools import coint; print('ok')"
```
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "Add statsmodels dependency for pair-spread screening"
```

---

### Task 2: Экспорт данных из MT5 (ручной шаг пользователя + валидация)

**Files:**
- Create: `MT/MQL5/Scripts/ExportOHLC.mq5`
- Create: `MT/MQL5/Scripts/ExportSymbolSpecs.mq5`
- Create: `statistics/pair_spread/check_data.py`
- Данные (результат экспорта): `MT/MQL4/Files/M5/*.csv`, `MT/MQL4/Files/H1/*.csv`, `MT/MQL4/Files/pair_spread_costs_snapshot.csv`

**Interfaces:**
- Consumes: MT5-терминал пользователя с открытой историей символов.
- Produces: CSV вида `time;open;high;low;close;volume` (время серверное, формат `YYYY.MM.DD HH:MM`) для 8 символов × 2 таймфрейма; снимок спецификаций (спред/своп/point). Эти файлы читают Task 3 и Task 6.

- [ ] **Step 1: Написать ExportOHLC.mq5**

```mql5
//+------------------------------------------------------------------+
//| ExportOHLC.mq5 — экспорт OHLC в CSV для этапа pair-spread        |
//| Запускать дважды: PERIOD_M5/InpSubdir=M5 и PERIOD_H1/InpSubdir=H1|
//+------------------------------------------------------------------+
#property script_show_inputs
input string        InpSymbols = "AUDUSD,NZDUSD,USDCAD,EURUSD,GBPUSD,USDCHF,XAUUSD,XAGUSD";
input ENUM_TIMEFRAMES InpTF    = PERIOD_M5;
input datetime      InpFrom    = D'2004.01.01 00:00';
input string        InpSubdir  = "M5";

void OnStart()
{
   string parts[];
   int cnt = StringSplit(InpSymbols, ',', parts);
   for(int k = 0; k < cnt; k++)
   {
      string sym = parts[k];
      if(!SymbolSelect(sym, true)) { Print("SymbolSelect failed: ", sym); continue; }
      int dig = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
      MqlRates rates[];
      ArraySetAsSeries(rates, false);
      int copied = CopyRates(sym, InpTF, InpFrom, TimeCurrent(), rates);
      if(copied <= 0) { Print("CopyRates failed: ", sym, " err=", GetLastError()); continue; }
      string fname = InpSubdir + "\\" + sym + "_OHLC.csv";
      int h = FileOpen(fname, FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
      if(h == INVALID_HANDLE) { Print("FileOpen failed: ", fname); continue; }
      FileWrite(h, "time", "open", "high", "low", "close", "volume");
      for(int i = 0; i < copied; i++)
      {
         FileWrite(h, TimeToString(rates[i].time, TIME_DATE | TIME_MINUTES),
                   DoubleToString(rates[i].open, dig),
                   DoubleToString(rates[i].high, dig),
                   DoubleToString(rates[i].low, dig),
                   DoubleToString(rates[i].close, dig),
                   IntegerToString((long)rates[i].tick_volume));
      }
      FileClose(h);
      Print("Exported ", sym, " ", copied, " bars -> ", fname);
   }
}
```

- [ ] **Step 2: Написать ExportSymbolSpecs.mq5**

```mql5
//+------------------------------------------------------------------+
//| ExportSymbolSpecs.mq5 — снимок спредов/свопов для cost model     |
//+------------------------------------------------------------------+
void OnStart()
{
   string syms[8] = {"AUDUSD","NZDUSD","USDCAD","EURUSD","GBPUSD","USDCHF","XAUUSD","XAGUSD"};
   int h = FileOpen("pair_spread_costs_snapshot.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(h == INVALID_HANDLE) { Print("FileOpen failed"); return; }
   FileWrite(h, "symbol", "point", "spread_points", "spread_price", "swap_long", "swap_short", "digits");
   for(int k = 0; k < 8; k++)
   {
      string sym = syms[k];
      if(!SymbolSelect(sym, true)) continue;
      double pt = SymbolInfoDouble(sym, SYMBOL_POINT);
      long   sp = SymbolInfoInteger(sym, SYMBOL_SPREAD);
      FileWrite(h, sym,
                DoubleToString(pt, 8),
                IntegerToString(sp),
                DoubleToString(sp * pt, 8),
                DoubleToString(SymbolInfoDouble(sym, SYMBOL_SWAP_LONG), 2),
                DoubleToString(SymbolInfoDouble(sym, SYMBOL_SWAP_SHORT), 2),
                IntegerToString(SymbolInfoInteger(sym, SYMBOL_DIGITS)));
   }
   FileClose(h);
   Print("Specs exported");
}
```

- [ ] **Step 3: Коммит скриптов; инструкция пользователю**

```bash
git add MT/MQL5/Scripts/ExportOHLC.mq5 MT/MQL5/Scripts/ExportSymbolSpecs.mq5
git commit -m "Add MT5 export scripts for pair-spread data and cost snapshot"
```

Дальше — ручные действия пользователя (зафиксировать в отчёте этапа):
1. В MT5 открыть History Center и запросить полную историю 8 символов на M5 и H1.
2. Скомпилировать и запустить `ExportOHLC.mq5` дважды: (M5, InpSubdir=M5) и (H1, InpSubdir=H1).
3. Запустить `ExportSymbolSpecs.mq5`.
4. Скопировать из `MT/MQL5/Files/`: `M5/` и `H1/` → в `MT/MQL4/Files/M5/` и `MT/MQL4/Files/H1/`; `pair_spread_costs_snapshot.csv` → в `MT/MQL4/Files/`.
5. XAUUSD M5: сравнить экспорт с существующим `MT/MQL4/Files/XAUUSD_M5_OHLC.csv` (раздел 3.1 спеки): при совпадении цен на пересечении дат оставить экспорт MT5 как единый источник (старый файл не удалять, он вне каталога M5/).

- [ ] **Step 4: Написать check_data.py (валидатор)**

```python
# =============================================================================
# Файл: statistics/pair_spread/check_data.py
# Назначение: проверка полноты экспорта M5/H1 перед запуском этапа
# Использование: ./.venv/bin/python statistics/pair_spread/check_data.py
# =============================================================================
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SYMBOLS = ['AUDUSD', 'NZDUSD', 'USDCAD', 'EURUSD', 'GBPUSD', 'USDCHF', 'XAUUSD', 'XAGUSD']
ROOT = Path(__file__).resolve().parents[2]
M5_DIR = ROOT / 'MT' / 'MQL4' / 'Files' / 'M5'
H1_DIR = ROOT / 'MT' / 'MQL4' / 'Files' / 'H1'
MIN_START = pd.Timestamp('2006-01-01')  # запас на глубокие бары брокера; train стартует 2005
MIN_END = pd.Timestamp('2026-01-01')
MIN_TRAIN_YEARS = 10


def check(tf_dir: Path, tf: str) -> list[str]:
    problems = []
    for sym in SYMBOLS:
        path = tf_dir / f'{sym}_OHLC.csv'
        if not path.exists():
            problems.append(f'{tf} {sym}: файл отсутствует')
            continue
        df = pd.read_csv(path, sep=';')
        t = pd.to_datetime(df['time'], format='%Y.%m.%d %H:%M')
        start, end = t.min(), t.max()
        if start > MIN_START:
            problems.append(f'{tf} {sym}: старт {start} позже {MIN_START}')
        if end < MIN_END:
            problems.append(f'{tf} {sym}: конец {end} раньше {MIN_END}')
        if (df['close'] <= 0).any():
            problems.append(f'{tf} {sym}: есть close <= 0')
        years_train = (pd.Timestamp('2022-12-31') - max(start, pd.Timestamp('2005-01-01'))).days / 365.25
        if years_train < MIN_TRAIN_YEARS:
            problems.append(f'{tf} {sym}: train-окно {years_train:.1f} лет < {MIN_TRAIN_YEARS}')
    return problems


def main() -> int:
    problems = check(M5_DIR, 'M5') + check(H1_DIR, 'H1')
    costs = ROOT / 'MT' / 'MQL4' / 'Files' / 'pair_spread_costs_snapshot.csv'
    if not costs.exists():
        problems.append('pair_spread_costs_snapshot.csv отсутствует')
    if problems:
        print('FAIL:')
        for p in problems:
            print(' -', p)
        return 1
    print('PASS: все 8 символов × M5/H1 на месте, снимок издержек найден')
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 5: Запустить валидацию**

Run: `./.venv/bin/python statistics/pair_spread/check_data.py`
Expected: `PASS: все 8 символов × M5/H1 на месте, снимок издержек найден` (только после ручного экспорта; до него — FAIL со списком отсутствующих файлов, это нормально как TDD-проверка самого валидатора).

- [ ] **Step 6: Commit**

```bash
git add statistics/pair_spread/check_data.py
git commit -m "Add data completeness checker for pair-spread stage"
```

---

### Task 3: Модуль данных pair_data.py

**Files:**
- Create: `statistics/pair_spread/pair_data.py`
- Test: `tests/test_pair_spread_data.py`

**Interfaces:**
- Consumes: CSV из Task 2 (`time;open;high;low;close;volume`).
- Produces: `load_ohlc_csv(path) -> pd.DataFrame` (DatetimeIndex `time`, float-колонки open/high/low/close, без дублей времени и close ≤ 0); `resample_to_h1(m5) -> pd.DataFrame`; `CANDIDATES` — dict имя кандидата → `{'legs': (symA, symB)}`; `build_log_spreads(closes_a, closes_b, beta) -> pd.Series` (s = lnA − β·lnB по inner-джойну времени); `TRAIN_END = pd.Timestamp('2022-12-31 23:59')`, `TEST_START = pd.Timestamp('2023-01-01 00:00')`.

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_pair_spread_data.py
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_MODULE_PATH = Path(__file__).resolve().parents[1] / 'statistics' / 'pair_spread' / 'pair_data.py'
_spec = importlib.util.spec_from_file_location('pair_data', _MODULE_PATH)
pair_data = importlib.util.module_from_spec(_spec)
sys.modules['pair_data'] = pair_data
_spec.loader.exec_module(pair_data)


def _write_csv(path, rows):
    lines = ['time;open;high;low;close;volume']
    lines += rows
    path.write_text('\n'.join(lines) + '\n')


def test_load_ohlc_csv_parses_and_cleans(tmp_path):
    p = tmp_path / 'SYM_OHLC.csv'
    _write_csv(p, [
        '2020.01.01 00:00;1.0;1.1;0.9;1.05;100',
        '2020.01.01 00:00;1.0;1.1;0.9;1.06;100',   # дубль времени
        '2020.01.01 00:05;1.06;1.2;1.0;1.10;50',
        '2020.01.01 00:10;0.0;0.0;0.0;0.0;0',      # close <= 0
    ])
    df = pair_data.load_ohlc_csv(p)
    assert len(df) == 2
    assert df.index[0] == pd.Timestamp('2020-01-01 00:00')
    assert df.loc[pd.Timestamp('2020-01-01 00:00'), 'close'] == 1.06  # keep='last'
    assert list(df.columns) == ['open', 'high', 'low', 'close']


def test_resample_to_h1_ohlc(tmp_path):
    rows = []
    closes = [1.0, 1.1, 1.2, 1.15, 1.3, 1.25, 1.2, 1.22, 1.18, 1.19, 1.21, 1.20]
    for i, c in enumerate(closes):
        rows.append(f'2020.01.01 00:{i*5:02d};{c};{c+0.01};{c-0.01};{c};10')
    p = tmp_path / 'SYM_OHLC.csv'
    _write_csv(p, rows)
    h1 = pair_data.resample_to_h1(pair_data.load_ohlc_csv(p))
    assert len(h1) == 1
    bar = h1.iloc[0]
    assert bar['open'] == 1.0
    assert bar['close'] == 1.20
    assert bar['high'] == 1.3 + 0.01
    assert bar['low'] == 1.0 - 0.01


def test_build_log_spreads_beta():
    t = pd.date_range('2020-01-01', periods=3, freq='5min')
    a = pd.Series([2.0, 4.0, 8.0], index=t)
    b = pd.Series([1.0, 2.0, 4.0], index=t)
    s = pair_data.build_log_spreads(a, b, beta=1.0)
    assert np.allclose(s, np.log(2.0))
    # a = b^2: ln a - 2*ln b = 0 тождественно (исправлено по аудиту К-2.1)
    a2 = pd.Series([1.0, 4.0, 16.0], index=t)
    s2 = pair_data.build_log_spreads(a2, b, beta=2.0)
    assert np.allclose(s2, 0.0)


def test_build_log_spreads_inner_join():
    t1 = pd.date_range('2020-01-01', periods=3, freq='5min')
    t2 = t1[1:]
    a = pd.Series([2.0, 2.0, 2.0], index=t1)
    b = pd.Series([1.0, 1.0], index=t2)
    s = pair_data.build_log_spreads(a, b, beta=1.0)
    assert len(s) == 2
    assert s.index[0] == t1[1]


def test_split_constants():
    assert pair_data.TRAIN_END == pd.Timestamp('2022-12-31 23:59')
    assert pair_data.TEST_START == pd.Timestamp('2023-01-01 00:00')
```

- [ ] **Step 2: Запустить, убедиться что падают**

Run: `./.venv/bin/python -m pytest tests/test_pair_spread_data.py -q`
Expected: FAIL (нет модуля pair_data.py).

- [ ] **Step 3: Реализовать pair_data.py**

```python
# =============================================================================
# Файл: statistics/pair_spread/pair_data.py
# Назначение: загрузка OHLC CSV (экспорт MT), сборка лог-спредов кандидатов,
#             константы сплита. Без __init__.py (конфликт statistics/ со stdlib)
# Обновлён: 2026-08-17
# Зависимости:
#   Входные данные: MT/MQL4/Files/{M5,H1}/*_OHLC.csv (откуда: MT5-экспорт, Task 2)
#   Выходные данные: pd.Series/pd.DataFrame в памяти (куда: screening.py, backtest.py, run_pair_spread.py)
# Использование: импорт из каталога скрипта (sys.path[0]) или importlib в тестах
# =============================================================================
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TIME_FORMAT = '%Y.%m.%d %H:%M'

TRAIN_END = pd.Timestamp('2022-12-31 23:59')
TEST_START = pd.Timestamp('2023-01-01 00:00')

# Кандидаты спеки (раздел 3.2): legs = (нога A, нога B), спред s = lnA - beta*lnB
CANDIDATES: dict[str, dict] = {
    'AUDNZD': {'legs': ('AUDUSD', 'NZDUSD')},
    'AUDCAD': {'legs': ('AUDUSD', 'USDCAD')},
    'NZDCAD': {'legs': ('NZDUSD', 'USDCAD')},
    'EURGBP': {'legs': ('EURUSD', 'GBPUSD')},
    'EURCHF': {'legs': ('EURUSD', 'USDCHF')},
    'GBPCHF': {'legs': ('GBPUSD', 'USDCHF')},
    'XAUXAG': {'legs': ('XAUUSD', 'XAGUSD')},
}

__all__ = [
    'CANDIDATES', 'TEST_START', 'TRAIN_END', 'TIME_FORMAT',
    'build_log_spreads', 'load_ohlc_csv', 'resample_to_h1',
]


def load_ohlc_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=';')
    df['time'] = pd.to_datetime(df['time'], format=TIME_FORMAT)
    df = df.set_index('time').sort_index()
    df = df[~df.index.duplicated(keep='last')]
    for col in ('open', 'high', 'low', 'close'):
        df[col] = df[col].astype(float)
    df = df[df['close'] > 0]
    return df[['open', 'high', 'low', 'close']]


def resample_to_h1(m5: pd.DataFrame) -> pd.DataFrame:
    h1 = m5.resample('1h', label='left', closed='left').agg(
        {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'})
    return h1.dropna()


def build_log_spreads(closes_a: pd.Series, closes_b: pd.Series, beta: float) -> pd.Series:
    a, b = closes_a.align(closes_b, join='inner')
    return np.log(a) - beta * np.log(b)
```

- [ ] **Step 4: Запустить тесты, убедиться что проходят**

Run: `./.venv/bin/python -m pytest tests/test_pair_spread_data.py -q`
Expected: PASS (5 тестов).

- [ ] **Step 5: Commit**

```bash
git add statistics/pair_spread/pair_data.py tests/test_pair_spread_data.py
git commit -m "Add pair-spread data loading, cross spreads and split constants"
```

---

### Task 4: Скрининг screening.py (ступень 1)

**Files:**
- Create: `statistics/pair_spread/screening.py`
- Test: `tests/test_pair_spread_screening.py`

**Interfaces:**
- Consumes: `pair_data.build_log_spreads` (pd.Series спреда, M5, train-окно); `costs` dict — round-trip стоимость `c` в лог-единицах спреда (считает Task 6 из снимка спецификаций).
- Produces: `fit_beta(a_log, b_log) -> float` (OLS-наклон на всём train); `engle_granger_pvalue(a_log, b_log) -> float`; `half_life_bars(s) -> float` (`inf`, если rho вне (0,1)); `episode_bounds(z, entry_z) -> list[tuple[int, int]]` (старт — первый бар |z| ≥ entry после бара с |z| < entry; конец — первый бар с |z| ≤ |z_start|/2, «половина возврата»; незавершённые эпизоды не включаются); `spread_mu_sigma(s_train) -> tuple[float, float]`; `screening_metrics(s_train, z_train, cost_c, thresholds) -> dict` — включая `episode_durations_bars` и `median_episode_duration_bars` (аудит В-4: длительности нужны отчёту; аудит В-1: медиана длительности эпизодов TRAIN замораживается в screening.json и служит длиной блока bootstrap); `verdict_pass(metrics, thresholds) -> tuple[bool, list[str]]`; `@dataclass ScreeningThresholds(coint_p_max=0.05, half_life_min_bars=6, half_life_max_bars=2880, min_episodes_per_year=5.0, entry_z=2.0)`.

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_pair_spread_screening.py
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_MODULE_PATH = Path(__file__).resolve().parents[1] / 'statistics' / 'pair_spread' / 'screening.py'
_spec = importlib.util.spec_from_file_location('screening', _MODULE_PATH)
screening = importlib.util.module_from_spec(_spec)
sys.modules['screening'] = screening  # dataclass-аннотации резолвятся через sys.modules (аудит К-1)
_spec.loader.exec_module(screening)


def test_fit_beta_known_value():
    rng = np.random.RandomState(0)
    b = np.cumsum(rng.randn(5000)) + 100
    a = 3.0 + 1.5 * b + rng.randn(5000) * 0.01
    assert abs(screening.fit_beta(a, b) - 1.5) < 0.01


def test_half_life_known_rho():
    # AR(1) с rho=0.99 -> полураспад = -ln2/ln0.99 ≈ 68.97 баров
    rng = np.random.RandomState(1)
    n = 200000
    s = np.empty(n)
    s[0] = 0.0
    for i in range(1, n):
        s[i] = 0.99 * s[i - 1] + rng.randn() * 0.01
    hl = screening.half_life_bars(pd.Series(s))
    assert abs(hl - (-np.log(2) / np.log(0.99))) / 69.0 < 0.10


def test_half_life_antipersistent_is_inf():
    # чередующийся ряд: rho < 0 -> полураспад не определён (inf), детерминированно.
    # Примечание (аудит К-2.2): random walk даёт конечный полураспад (OLS rho<1),
    # от random walk полураспад-гейт не защищает — это делает EG-гейт.
    s = pd.Series(np.tile([1.0, -1.0], 2500))
    assert screening.half_life_bars(s) == float('inf')


def test_engle_granger_stationary_pair_low_p():
    rng = np.random.RandomState(3)
    x = np.cumsum(rng.randn(3000))          # random walk
    y = 2.0 + 0.8 * x + rng.randn(3000) * 0.1  # коинтегрирован с x
    p = screening.engle_granger_pvalue(y, x)
    assert p < 0.01


def test_engle_granger_independent_walks_high_p():
    # сид 2 проверен до коммита: p ≈ 0.96 (аудит К-2.3: сид 4 давал p=0.013)
    rng = np.random.RandomState(2)
    x = np.cumsum(rng.randn(3000))
    y = np.cumsum(rng.randn(3000))
    p = screening.engle_granger_pvalue(y, x)
    assert p > 0.10


def test_episode_bounds_basic():
    z = pd.Series([0.0, 2.5, 2.6, 1.2, 0.9, 0.1, -2.2, -0.8])
    eps = screening.episode_bounds(z, entry_z=2.0)
    # первый эпизод: старт 1 (|2.5|), половина = 1.25, бар 3: |1.2| <= 1.25 -> конец 3
    assert eps[0] == (1, 3)
    # второй эпизод: старт 6 (|-2.2|), половина = 1.1, бар 7: |-0.8| <= 1.1 -> конец 7
    assert eps[1] == (6, 7)


def test_episode_ignores_continuation():
    # |z| остаётся >= 2 подряд — это один эпизод, не несколько
    z = pd.Series([2.5, 2.7, 2.9, 0.5])
    eps = screening.episode_bounds(z, entry_z=2.0)
    assert len(eps) == 1
    assert eps[0][0] == 0


def test_spread_mu_sigma():
    s = pd.Series([1.0, 2.0, 3.0])
    mu, sigma = screening.spread_mu_sigma(s)
    assert mu == 2.0
    assert abs(sigma - np.std([1.0, 2.0, 3.0], ddof=1)) < 1e-12


def test_screening_metrics_episode_durations():
    # эпизоды те же, что в test_episode_bounds_basic: (1,3) и (6,7) -> длины 2 и 1
    idx = pd.date_range('2010-01-01', periods=8, freq='5min')
    z = pd.Series([0.0, 2.5, 2.6, 1.2, 0.9, 0.1, -2.2, -0.8], index=idx)
    s = pd.Series(np.linspace(0.0, 0.7, 8), index=idx)
    m = screening.screening_metrics(s, z, cost_c=0.001,
                                    thresholds=screening.ScreeningThresholds())
    assert m['n_episodes'] == 2
    assert m['episode_durations_bars'] == [2, 1]
    assert m['median_episode_duration_bars'] == 1.5


def test_verdict_all_pass():
    th = screening.ScreeningThresholds()
    metrics = {
        'coint_p': 0.01, 'half_life_bars': 100.0,
        'cost_c': 0.001, 'p75_abs_ds': 0.005,
        'median_episode_deviation': 0.01, 'episodes_per_year': 8.0,
    }
    ok, reasons = screening.verdict_pass(metrics, th)
    assert ok and reasons == []


def test_verdict_kills_on_each_gate():
    th = screening.ScreeningThresholds()
    base = {
        'coint_p': 0.01, 'half_life_bars': 100.0,
        'cost_c': 0.001, 'p75_abs_ds': 0.005,
        'median_episode_deviation': 0.01, 'episodes_per_year': 8.0,
    }
    for key, bad in [('coint_p', 0.2), ('half_life_bars', 2.0),
                     ('p75_abs_ds', 0.0005), ('median_episode_deviation', 0.0005),
                     ('episodes_per_year', 1.0)]:
        m = dict(base, **{key: bad})
        ok, reasons = screening.verdict_pass(m, th)
        assert not ok and len(reasons) >= 1
```

- [ ] **Step 2: Запустить, убедиться что падают**

Run: `./.venv/bin/python -m pytest tests/test_pair_spread_screening.py -q`
Expected: FAIL (нет модуля).

- [ ] **Step 3: Реализовать screening.py**

```python
# =============================================================================
# Файл: statistics/pair_spread/screening.py
# Назначение: ступень 1 kill-теста — метрики скрининга на train (спека, раздел 5)
# Обновлён: 2026-08-18
# Зависимости:
#   Входные данные: лог-спред train (pair_data), round-trip стоимость c (run_pair_spread)
#   Выходные данные: dict метрик + вердикт (куда: run_pair_spread.py)
#   Внешние зависимости: statsmodels.tsa.stattools.coint (Энгл-Грэнджер)
# =============================================================================
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint

__all__ = [
    'ScreeningThresholds', 'engle_granger_pvalue', 'episode_bounds',
    'fit_beta', 'half_life_bars', 'screening_metrics', 'spread_mu_sigma',
    'verdict_pass',
]


@dataclass(frozen=True)
class ScreeningThresholds:
    coint_p_max: float = 0.05
    half_life_min_bars: float = 6.0
    half_life_max_bars: float = 2880.0
    min_episodes_per_year: float = 5.0
    entry_z: float = 2.0


def fit_beta(a_log: np.ndarray | pd.Series, b_log: np.ndarray | pd.Series) -> float:
    x = np.asarray(b_log, dtype=float)
    y = np.asarray(a_log, dtype=float)
    x = x - x.mean()
    y = y - y.mean()
    return float((x * y).sum() / (x * x).sum())


def engle_granger_pvalue(a_log: np.ndarray | pd.Series, b_log: np.ndarray | pd.Series) -> float:
    _, p, _ = coint(np.asarray(a_log, dtype=float), np.asarray(b_log, dtype=float), trend='c')
    return float(p)


def half_life_bars(s: pd.Series) -> float:
    y = s.to_numpy(dtype=float)
    x_prev, y_next = y[:-1], y[1:]
    x = x_prev - x_prev.mean()
    yv = y_next - y_next.mean()
    rho = float((x * yv).sum() / (x * x).sum())
    if not (0.0 < rho < 1.0):
        return float('inf')
    return float(-np.log(2.0) / np.log(rho))


def spread_mu_sigma(s_train: pd.Series) -> tuple[float, float]:
    return float(s_train.mean()), float(s_train.std(ddof=1))


def episode_bounds(z: pd.Series, entry_z: float = 2.0) -> list[tuple[int, int]]:
    """Старт: первый бар с |z| >= entry после бара с |z| < entry.
    Конец: первый бар после старта с |z| <= |z_start|/2 (половина возврата).
    Незавершённые эпизоды отбрасываются."""
    zv = z.to_numpy(dtype=float)
    n = len(zv)
    episodes: list[tuple[int, int]] = []
    in_ep = False
    start = -1
    half = 0.0
    for i in range(n):
        if not in_ep:
            above = abs(zv[i]) >= entry_z
            was_below = (i == 0) or (abs(zv[i - 1]) < entry_z)
            if above and was_below:
                in_ep = True
                start = i
                half = abs(zv[i]) / 2.0
        else:
            if abs(zv[i]) <= half:
                episodes.append((start, i))
                in_ep = False
    return episodes


def screening_metrics(s_train: pd.Series, z_train: pd.Series, cost_c: float,
                      thresholds: ScreeningThresholds) -> dict:
    episodes = episode_bounds(z_train, thresholds.entry_z)
    years = max((z_train.index[-1] - z_train.index[0]).days / 365.25, 1e-9)
    ds = s_train.diff().dropna().abs()
    mu = float(s_train.mean())
    devs: list[float] = []
    durations: list[int] = []
    for start, end in episodes:
        devs.extend(abs(s_train.iloc[start:end + 1] - mu).tolist())
        durations.append(end - start)
    return {
        'n_episodes': len(episodes),
        'episodes_per_year': len(episodes) / years,
        'p75_abs_ds': float(np.percentile(ds, 75)) if len(ds) else float('nan'),
        'median_episode_deviation': float(np.median(devs)) if devs else 0.0,
        # длительности эпизодов: артефакт для отчёта (спека разделы 5, 8) и
        # замороженная длина блока bootstrap (спека раздел 6, аудит В-1/В-4)
        'episode_durations_bars': durations,
        'median_episode_duration_bars': float(np.median(durations)) if durations else 0.0,
        'cost_c': float(cost_c),
    }


def verdict_pass(metrics: dict, th: ScreeningThresholds) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if metrics['coint_p'] > th.coint_p_max:
        reasons.append(f"EG p {metrics['coint_p']:.4f} > {th.coint_p_max}")
    hl = metrics['half_life_bars']
    if not (th.half_life_min_bars <= hl <= th.half_life_max_bars):
        reasons.append(f'half-life {hl:.1f} вне [{th.half_life_min_bars}, {th.half_life_max_bars}]')
    if metrics['cost_c'] > metrics['p75_abs_ds']:
        reasons.append(f"cost {metrics['cost_c']:.6f} > P75|ds| {metrics['p75_abs_ds']:.6f}")
    if metrics['median_episode_deviation'] <= metrics['cost_c']:
        reasons.append('медианное отклонение в эпизодах <= round-trip стоимости')
    if metrics['episodes_per_year'] < th.min_episodes_per_year:
        reasons.append(f"эпизодов/год {metrics['episodes_per_year']:.2f} < {th.min_episodes_per_year}")
    return (len(reasons) == 0, reasons)
```

- [ ] **Step 4: Запустить тесты, убедиться что проходят**

Run: `./.venv/bin/python -m pytest tests/test_pair_spread_screening.py -q`
Expected: PASS (11 тестов). Если `test_episode_bounds_basic` падает на ожидании — сверить семантику с докстрингом (конец по половине возврата), тесты и код должны совпадать; при расхождении править тест под семантику спеки, не наоборот.

- [ ] **Step 5: Commit**

```bash
git add statistics/pair_spread/screening.py tests/test_pair_spread_screening.py
git commit -m "Add stage-1 screening metrics for pair-spread kill-test"
```

---

### Task 5: Бэктестер backtest.py (ступень 2)

**Files:**
- Create: `statistics/pair_spread/backtest.py`
- Test: `tests/test_pair_spread_backtest.py`

**Interfaces:**
- Consumes: сигнальный ряд z по close (train-нормировка), ряд исполнения s_exec по open следующего бара; времена баров; `round_trip_cost`, `swap_cost_long`, `swap_cost_short` (по стороне сделки, аудит В-6).
- Produces: `@dataclass Trade(side: int, entry_i: int, exit_i: int, pnl_gross: float, pnl_net: float, exit_reason: str, nights: int)`; `@dataclass BacktestResult(trades: list[Trade], dropped_open_at_end: int)` — счётчик позиции, открытой на последнем баре и не исполненной (аудит К-2.4/Q-3); `run_backtest(z, s_exec, times, round_trip_cost, swap_cost_long=0.0, swap_cost_short=0.0, entry_z=2.0, stop_z=4.0, timeout_bars=2880) -> BacktestResult` — правила спеки раздела 6: вход при flat и 2 ≤ |z| < 4 на закрытии бара, исполнение на открытии следующего; выход: пересечение z=0 (revert) / |z| ≥ 4 (stop) / таймаут; после stop и timeout повторный вход только после пересечения z = 0; одна позиция; своп начисляется по стороне: side=+1 → `swap_cost_long`, side=−1 → `swap_cost_short`; позиция, сигнал выхода которой выпал на последний бар, в `trades` не попадает и считается в `dropped_open_at_end`; `profit_factor(pnls) -> float`; `stationary_bootstrap_ci(pnls, expected_block, n_resamples=10000, quantile=0.05, seed=0) -> float`.

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_pair_spread_backtest.py
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_MODULE_PATH = Path(__file__).resolve().parents[1] / 'statistics' / 'pair_spread' / 'backtest.py'
_spec = importlib.util.spec_from_file_location('backtest', _MODULE_PATH)
backtest = importlib.util.module_from_spec(_spec)
sys.modules['backtest'] = backtest  # dataclass-аннотации резолвятся через sys.modules (аудит К-1)
_spec.loader.exec_module(backtest)


def _times(n):
    return pd.date_range('2023-01-02', periods=n, freq='5min').to_numpy()


def test_basic_revert_trade():
    # z: 0, 2.5 (сигнал), 2.6, 0.5, -0.1 (пересечение нуля на баре 4)
    z = np.array([0.0, 2.5, 2.6, 0.5, -0.1, 0.0])
    s = np.array([10.0, 10.0, 10.4, 10.3, 10.0, 10.0])  # исполнение по open-спреду
    trades = backtest.run_backtest(z, s, _times(6), round_trip_cost=0.1).trades
    assert len(trades) == 1
    t = trades[0]
    assert t.side == -1                    # z>=2 -> short спреда
    assert t.exit_reason == 'revert'
    # вход на open бара 2 (10.4), выход на open бара 5 (10.0): gross = -1*(10.0-10.4)=0.4
    assert abs(t.pnl_gross - 0.4) < 1e-12
    assert abs(t.pnl_net - 0.3) < 1e-12    # минус round-trip cost 0.1


def test_no_entry_in_stop_zone():
    z = np.array([0.0, 4.5, 4.6, 0.0])
    s = np.array([10.0, 10.0, 10.1, 10.0])
    result = backtest.run_backtest(z, s, _times(4), round_trip_cost=0.0)
    assert result.trades == []
    assert result.dropped_open_at_end == 0


def test_stop_exit_blocks_reentry_until_zero_cross():
    # вход на баре 1 (z=2.5), стоп на баре 2 (z=4.5), далее z всё ещё >=2 (бар 3) —
    # повторный вход запрещён; пересечение нуля на баре 4; новый сигнал на баре 5;
    # возврат и закрытие второго трейда на баре 7
    z = np.array([0.0, 2.5, 4.5, 2.6, -0.1, -2.5, -0.5, 0.1, 0.2])
    s = np.array([10.0, 10.0, 10.5, 10.6, 10.2, 9.8, 9.8, 9.9, 10.0])
    trades = backtest.run_backtest(z, s, _times(9), round_trip_cost=0.0).trades
    assert len(trades) == 2
    assert trades[0].exit_reason == 'stop'
    assert trades[1].side == 1             # z<=-2 -> long спреда (после пересечения нуля)
    assert trades[1].exit_reason == 'revert'


def test_timeout_exit():
    n = 2885
    z = np.zeros(n)
    z[1] = 2.5
    z[2:2882] = 2.1    # держится в зоне, нуля не пересекает
    s = np.full(n, 10.0)
    trades = backtest.run_backtest(z, s, _times(n), round_trip_cost=0.0).trades
    assert len(trades) == 1
    assert trades[0].exit_reason == 'timeout'
    # сигнал на баре 1, удержание 2880 баров, исполнение выхода на баре 1+2880+1
    assert trades[0].exit_i == 1 + 2880 + 1


def test_one_position_no_pyramiding():
    # завершающий бар 0.0 даёт исполнимый выход по возврату (аудит К-2.4)
    z = np.array([0.0, 2.5, 2.6, 2.7, 0.1, -0.1, 0.0])
    s = np.full(7, 10.0)
    result = backtest.run_backtest(z, s, _times(7), round_trip_cost=0.0)
    assert len(result.trades) == 1
    assert result.dropped_open_at_end == 0


def test_open_position_at_end_dropped_and_counted():
    # тот же сценарий без завершающего бара: сигнал выхода на последнем баре
    # исполнить негде — сделка не входит в trades, но подсчитана (аудит К-2.4/Q-3)
    z = np.array([0.0, 2.5, 2.6, 2.7, 0.1, -0.1])
    s = np.full(6, 10.0)
    result = backtest.run_backtest(z, s, _times(6), round_trip_cost=0.0)
    assert result.trades == []
    assert result.dropped_open_at_end == 1


def test_no_entry_on_last_bar():
    z = np.array([0.0, 2.5])   # сигнал на последнем баре — исполнять негде
    s = np.array([10.0, 10.0])
    result = backtest.run_backtest(z, s, _times(2), round_trip_cost=0.0)
    assert result.trades == []
    assert result.dropped_open_at_end == 0


def test_nights_and_swap_short_side():
    # удержание через 2 календарные ночи; z=+2.5 -> side=-1 -> swap_cost_short (аудит В-6)
    n = 3 * 288   # 3 суток по 288 баров M5
    z = np.zeros(n)
    z[1] = 2.5
    z[2:] = 0.9    # без пересечения нуля -> выход по таймауту
    times = pd.date_range('2023-01-02', periods=n, freq='5min').to_numpy()
    s = np.full(n, 10.0)
    trades = backtest.run_backtest(z, s, times, round_trip_cost=0.0,
                                   swap_cost_long=0.99, swap_cost_short=0.05,
                                   timeout_bars=2 * 288).trades
    assert len(trades) == 1
    assert trades[0].side == -1
    assert trades[0].nights == 2
    assert abs(trades[0].pnl_net - (trades[0].pnl_gross - 2 * 0.05)) < 1e-12


def test_nights_and_swap_long_side():
    # z=-2.5 -> side=+1 -> swap_cost_long (аудит В-6)
    n = 3 * 288
    z = np.zeros(n)
    z[1] = -2.5
    z[2:] = -0.9
    times = pd.date_range('2023-01-02', periods=n, freq='5min').to_numpy()
    s = np.full(n, 10.0)
    trades = backtest.run_backtest(z, s, times, round_trip_cost=0.0,
                                   swap_cost_long=0.07, swap_cost_short=0.99,
                                   timeout_bars=2 * 288).trades
    assert len(trades) == 1
    assert trades[0].side == 1
    assert trades[0].nights == 2
    assert abs(trades[0].pnl_net - (trades[0].pnl_gross - 2 * 0.07)) < 1e-12


def test_profit_factor():
    assert backtest.profit_factor([2.0, -1.0]) == 2.0
    assert backtest.profit_factor([-1.0, -2.0]) == 0.0
    assert backtest.profit_factor([]) == 0.0


def test_stationary_bootstrap_ci_bounds():
    rng = np.random.RandomState(0)
    pnls = list(rng.randn(200) * 0.5 + 0.1)   # положительное ожидание
    lo = backtest.stationary_bootstrap_ci(pnls, expected_block=10, n_resamples=500, seed=7)
    pf = backtest.profit_factor(pnls)
    assert 0.0 < lo <= pf
```

- [ ] **Step 2: Запустить, убедиться что падают**

Run: `./.venv/bin/python -m pytest tests/test_pair_spread_backtest.py -q`
Expected: FAIL (нет модуля).

- [ ] **Step 3: Реализовать backtest.py**

```python
# =============================================================================
# Файл: statistics/pair_spread/backtest.py
# Назначение: ступень 2 kill-теста — симулятор z-score правила (спека, раздел 6)
#             + stationary bootstrap BS_p05 (методология 09)
# Обновлён: 2026-08-18
# Зависимости:
#   Входные данные: z по close (train-нормировка), s_exec по open, времена, издержки
#   Выходные данные: BacktestResult(trades, dropped_open_at_end), PF, BS_p05
#                    (куда: run_pair_spread.py)
# Конвенция исполнения: сигнал на закрытии бара i -> исполнение на открытии i+1.
# =============================================================================
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ['BacktestResult', 'Trade', 'profit_factor', 'run_backtest',
           'stationary_bootstrap_ci']

ENTRY_Z = 2.0
STOP_Z = 4.0
TIMEOUT_BARS = 2880


@dataclass
class Trade:
    side: int            # +1 long спреда, -1 short спреда
    entry_i: int         # индекс бара исполнения входа (open)
    exit_i: int          # индекс бара исполнения выхода (open)
    pnl_gross: float
    pnl_net: float
    exit_reason: str     # 'revert' | 'stop' | 'timeout'
    nights: int


@dataclass
class BacktestResult:
    trades: list[Trade] = field(default_factory=list)
    # позиция, открытая на конец данных: сигнал выхода на последнем баре
    # исполнить негде — сделка не учитывается в PF, но подсчитывается (аудит К-2.4/Q-3)
    dropped_open_at_end: int = 0


def _nights_between(times, i_entry, i_exit) -> int:
    d0 = times[i_entry].astype('datetime64[D]')
    d1 = times[i_exit].astype('datetime64[D]')
    return int((d1 - d0).astype(int))


def run_backtest(z: np.ndarray, s_exec: np.ndarray, times: np.ndarray,
                 round_trip_cost: float,
                 swap_cost_long: float = 0.0, swap_cost_short: float = 0.0,
                 entry_z: float = ENTRY_Z, stop_z: float = STOP_Z,
                 timeout_bars: int = TIMEOUT_BARS) -> BacktestResult:
    """swap_cost_long/short — стоимость ночи удержания (положительная — издержка,
    отрицательная — кэрри-доход) для сделки side=+1 и side=-1 соответственно
    (аудит В-6: своп комбинированной позиции зависит от стороны)."""
    z = np.asarray(z, dtype=float)
    s_exec = np.asarray(s_exec, dtype=float)
    n = len(z)
    result = BacktestResult()
    need_zero_cross = False
    pos = None  # dict: side, entry_bar (бар сигнала), exec_i, entry_sign

    for i in range(n):
        # --- выход (проверяется на закрытии бара i при открытой позиции) ---
        if pos is not None:
            held = i - pos['entry_bar']
            crossed_zero = z[i] * pos['entry_sign'] <= 0.0
            reason = None
            if crossed_zero:
                reason = 'revert'
            elif abs(z[i]) >= stop_z:
                reason = 'stop'
            elif held >= timeout_bars:
                reason = 'timeout'
            if reason is not None and i + 1 < n:
                exec_exit = i + 1
                gross = pos['side'] * (s_exec[exec_exit] - s_exec[pos['exec_i']])
                nights = _nights_between(times, pos['exec_i'], exec_exit)
                swap = swap_cost_long if pos['side'] > 0 else swap_cost_short
                net = gross - round_trip_cost - swap * nights
                result.trades.append(Trade(pos['side'], pos['exec_i'], exec_exit,
                                           gross, net, reason, nights))
                pos = None
                need_zero_cross = reason in ('stop', 'timeout')
                continue
        # --- вход (проверяется на закрытии бара i при плоской позиции) ---
        if pos is None and i + 1 < n:
            if need_zero_cross:
                if i > 0 and z[i] * z[i - 1] < 0.0:
                    need_zero_cross = False
                else:
                    continue
            if entry_z <= abs(z[i]) < stop_z:
                pos = {
                    'side': -1 if z[i] > 0 else 1,
                    'entry_bar': i,
                    'exec_i': i + 1,
                    'entry_sign': 1.0 if z[i] > 0 else -1.0,
                }
    if pos is not None:
        result.dropped_open_at_end = 1
    return result


def profit_factor(pnls) -> float:
    gains = sum(p for p in pnls if p > 0)
    losses = -sum(p for p in pnls if p < 0)
    if losses <= 0:
        return 0.0 if gains <= 0 else float('inf')
    return gains / losses


def stationary_bootstrap_ci(pnls, expected_block: float, n_resamples: int = 10000,
                            quantile: float = 0.05, seed: int = 0) -> float:
    """Stationary bootstrap Политиса-Романо по ряду PnL сделок (временной порядок).
    Длина блока геометрическая с матожиданием expected_block.
    Возвращает нижнюю границу PF (BS_p05 по умолчанию)."""
    pnls = np.asarray(pnls, dtype=float)
    n = len(pnls)
    if n == 0:
        return 0.0
    rng = np.random.default_rng(seed)
    p = 1.0 / max(expected_block, 1.0)
    pfs = np.empty(n_resamples)
    for r in range(n_resamples):
        sample = np.empty(n)
        idx = rng.integers(n)
        for k in range(n):
            sample[k] = pnls[idx]
            if rng.random() < p:
                idx = rng.integers(n)
            else:
                idx = (idx + 1) % n
        pf = profit_factor(sample)
        pfs[r] = min(pf, 1e6)
    return float(np.quantile(pfs, quantile))
```

- [ ] **Step 4: Запустить тесты, убедиться что проходят**

Run: `./.venv/bin/python -m pytest tests/test_pair_spread_backtest.py -q`
Expected: PASS (11 тестов).

- [ ] **Step 5: Commit**

```bash
git add statistics/pair_spread/backtest.py tests/test_pair_spread_backtest.py
git commit -m "Add stage-2 z-score backtester and stationary bootstrap for pair-spread"
```

---

### Task 6: Оркестратор run_pair_spread.py

**Files:**
- Create: `statistics/pair_spread/run_pair_spread.py`
- Test: `tests/test_pair_spread_runner.py`

**Interfaces:**
- Consumes: `pair_data` (Task 3), `screening` (Task 4), `backtest` (Task 5), файлы Task 2 (`MT/MQL4/Files/M5/*_OHLC.csv`, `MT/MQL4/Files/H1/*_OHLC.csv` — независимый H1-срез брокера, аудит В-2; `MT/MQL4/Files/pair_spread_costs_snapshot.csv`).
- Produces: `DATA/pair_spread/screening.json`, `DATA/pair_spread/backtest.json`, `DATA/pair_spread/backtest_stress2x.json` (при `--stress-costs 2.0`; базовый артефакт не перезаписывается — аудит В-3); `build_costs(snapshot_csv_path) -> dict` (symbol → `{'spread_price': float, 'point': float, 'swap_long': float, 'swap_short': float}`); `round_trip_cost_c(spread_a_price, spread_b_price, price_a, price_b, beta) -> float` = `2*(spreadA/priceA + abs(beta)*spreadB/priceB)`; `stress_cost_c(cost_c, factor) -> float`; `pair_verdict(metrics) -> str` — EG-p(test) > 0.10 → KILLED первым гейтом, затем N-гейт → DIAGNOSTIC_ONLY, затем PF/BS (конвенция Q-1); цены для нормировки издержек — последние close TRAIN-окна (аудит В-5); своп XAUXAG по стороне сделки (аудит В-6); `backtest.json` содержит `dropped_open_at_end` и `expected_block_bars` по каждой паре; `main()` — полный прогон двух ступеней, аргумент `--stress-costs FLOAT` (1.0 = базовый прогон).

- [ ] **Step 1: Написать падающие тесты (на чистые функции руннера)**

```python
# tests/test_pair_spread_runner.py
import importlib.util
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / 'statistics' / 'pair_spread' / 'run_pair_spread.py'
_spec = importlib.util.spec_from_file_location('run_pair_spread', _MODULE_PATH)
runner = importlib.util.module_from_spec(_spec)
sys.modules['run_pair_spread'] = runner
_spec.loader.exec_module(runner)


def test_build_costs_parses_snapshot(tmp_path):
    p = tmp_path / 'costs.csv'
    p.write_text(
        'symbol;point;spread_points;spread_price;swap_long;swap_short;digits\n'
        'EURUSD;0.00001;10;0.00010;-5.0;1.0;5\n'
        'GBPUSD;0.00001;12;0.00012;-3.0;0.5;5\n')
    costs = runner.build_costs(p)
    assert abs(costs['EURUSD']['spread_price'] - 0.00010) < 1e-12
    assert abs(costs['GBPUSD']['swap_long'] - (-3.0)) < 1e-12


def test_round_trip_cost_c_uses_abs_beta():
    # beta отрицательный (mul-кросс) — вес ноги B по модулю
    c = runner.round_trip_cost_c(spread_a_price=0.0001, spread_b_price=0.0001,
                                 price_a=1.0, price_b=1.0, beta=-1.0)
    assert abs(c - 2 * (0.0001 + 0.0001)) < 1e-12


def test_stress_cost_c():
    assert abs(runner.stress_cost_c(0.001, 2.0) - 0.002) < 1e-15
    assert runner.stress_cost_c(0.001, 1.0) == 0.001


def test_pair_verdict_gates():
    base = {'pf': 1.5, 'bs_p05': 1.05, 'n_trades': 150, 'n_per_side_min': 60,
            'eg_p_test': 0.02}
    assert runner.pair_verdict(dict(base)) == 'SURVIVED'
    assert runner.pair_verdict(dict(base, pf=1.2)) == 'KILLED'
    assert runner.pair_verdict(dict(base, bs_p05=0.99)) == 'KILLED'
    assert runner.pair_verdict(dict(base, eg_p_test=0.2)) == 'KILLED'
    assert runner.pair_verdict(dict(base, n_trades=80)) == 'DIAGNOSTIC_ONLY'
    assert runner.pair_verdict(dict(base, n_per_side_min=20)) == 'DIAGNOSTIC_ONLY'
    # приоритет (аудит Q-1): слом коинтеграции убивает даже при малом N
    assert runner.pair_verdict(dict(base, n_trades=40, eg_p_test=0.9)) == 'KILLED'
```

- [ ] **Step 2: Запустить, убедиться что падают**

Run: `./.venv/bin/python -m pytest tests/test_pair_spread_runner.py -q`
Expected: FAIL (нет модуля).

- [ ] **Step 3: Реализовать run_pair_spread.py**

```python
# =============================================================================
# Файл: statistics/pair_spread/run_pair_spread.py
# Назначение: оркестратор двух ступеней kill-теста pair-spread; JSON-артефакты
# Обновлён: 2026-08-18
# Зависимости:
#   Входные данные:
#     - MT/MQL4/Files/M5/*_OHLC.csv, MT/MQL4/Files/H1/*_OHLC.csv (Task 2)
#     - MT/MQL4/Files/pair_spread_costs_snapshot.csv (Task 2)
#   Выходные данные:
#     - DATA/pair_spread/screening.json, DATA/pair_spread/backtest.json,
#       DATA/pair_spread/backtest_stress2x.json (при --stress-costs 2.0)
#   Внутренние зависимости: pair_data, screening, backtest (тот же каталог)
# Использование:
#   ./.venv/bin/python statistics/pair_spread/run_pair_spread.py [--stage 1|2|all]
#   [--stress-costs 2.0]
# Примечания: все пороги заморожены спекой 2026-08-17; изменения после запуска
#   только документированным решением.
# =============================================================================
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pair_data import (CANDIDATES, TEST_START, TRAIN_END, build_log_spreads,
                       load_ohlc_csv)
from screening import (ScreeningThresholds, engle_granger_pvalue, fit_beta,
                       half_life_bars, screening_metrics, verdict_pass)
from backtest import profit_factor, run_backtest, stationary_bootstrap_ci

ROOT = Path(__file__).resolve().parents[2]
M5_DIR = ROOT / 'MT' / 'MQL4' / 'Files' / 'M5'
H1_DIR = ROOT / 'MT' / 'MQL4' / 'Files' / 'H1'
COSTS_CSV = ROOT / 'MT' / 'MQL4' / 'Files' / 'pair_spread_costs_snapshot.csv'
OUT_DIR = ROOT / 'DATA' / 'pair_spread'

THRESHOLDS = ScreeningThresholds()  # заморожено спекой


def build_costs(snapshot_csv_path: Path) -> dict:
    df = pd.read_csv(snapshot_csv_path, sep=';')
    out = {}
    for _, row in df.iterrows():
        out[row['symbol']] = {
            'spread_price': float(row['spread_price']),
            'point': float(row['point']),
            'swap_long': float(row['swap_long']),
            'swap_short': float(row['swap_short']),
        }
    return out


def round_trip_cost_c(spread_a_price: float, spread_b_price: float,
                      price_a: float, price_b: float, beta: float) -> float:
    return 2.0 * (spread_a_price / price_a + abs(beta) * spread_b_price / price_b)


def stress_cost_c(cost_c: float, factor: float) -> float:
    """Стресс-множитель издержек (методология 12: обязательный стресс 2x)."""
    return cost_c * factor


def pair_verdict(m: dict) -> str:
    # Приоритет (аудит Q-1): слом коинтеграции на test убивает независимо от
    # PF и числа сделок (мощность EG-теста определяется барами, не сделками).
    # Гейт N ограничивает только SURVIVED (методология 06).
    if m['eg_p_test'] > 0.10:
        return 'KILLED'
    if m['n_trades'] < 100 or m['n_per_side_min'] < 30:
        return 'DIAGNOSTIC_ONLY'
    if m['pf'] >= 1.3 and m['bs_p05'] > 1.0:
        return 'SURVIVED'
    return 'KILLED'


def _load_legs(tf_dir: Path) -> dict[str, pd.DataFrame]:
    symbols = sorted({s for c in CANDIDATES.values() for s in c['legs']})
    return {s: load_ohlc_csv(tf_dir / f'{s}_OHLC.csv') for s in symbols}


def _stage1_for_tf(legs: dict[str, pd.DataFrame], costs: dict, tf: str) -> dict:
    results = {}
    for name, spec in CANDIDATES.items():
        sym_a, sym_b = spec['legs']
        df_a, df_b = legs[sym_a], legs[sym_b]
        a_close, b_close = df_a['close'].align(df_b['close'], join='inner')
        train_mask = a_close.index <= TRAIN_END
        a_log = np.log(a_close.to_numpy(dtype=float))
        b_log = np.log(b_close.to_numpy(dtype=float))
        beta = fit_beta(a_log[train_mask.to_numpy()], b_log[train_mask.to_numpy()])
        s = build_log_spreads(a_close, b_close, beta)
        s_train = s[s.index <= TRAIN_END]
        z_train = (s_train - s_train.mean()) / s_train.std(ddof=1)
        # нормировка издержек — последние цены TRAIN, не test (аудит В-5)
        a_train_close = a_close[train_mask.to_numpy()]
        b_train_close = b_close[train_mask.to_numpy()]
        cost_c = round_trip_cost_c(costs[sym_a]['spread_price'], costs[sym_b]['spread_price'],
                                   float(a_train_close.iloc[-1]),
                                   float(b_train_close.iloc[-1]), beta)
        metrics = screening_metrics(s_train, z_train, cost_c, THRESHOLDS)
        metrics.update({
            'beta': beta,
            'coint_p': engle_granger_pvalue(a_log[train_mask.to_numpy()],
                                            b_log[train_mask.to_numpy()]),
            'half_life_bars': half_life_bars(s_train),
            'mu_train': float(s_train.mean()),
            'sigma_train': float(s_train.std(ddof=1)),
        })
        passed, reasons = verdict_pass(metrics, THRESHOLDS)
        metrics['pass'] = passed
        metrics['kill_reasons'] = reasons
        results[name] = metrics
    return {'tf': tf, 'thresholds': vars(THRESHOLDS), 'candidates': results}


def _stage2(legs_m5: dict[str, pd.DataFrame], screening_out: dict, costs: dict,
            cost_factor: float = 1.0) -> dict:
    results = {}
    for name, m in screening_out['candidates'].items():
        if not m['pass']:
            continue
        sym_a, sym_b = CANDIDATES[name]['legs']
        df_a, df_b = legs_m5[sym_a], legs_m5[sym_b]
        a_o, b_o = df_a['open'].align(df_b['open'], join='inner')
        a_c, b_c = df_a['close'].align(df_b['close'], join='inner')
        beta, mu, sigma = m['beta'], m['mu_train'], m['sigma_train']
        s_sig = build_log_spreads(a_c, b_c, beta)
        s_exec = build_log_spreads(a_o, b_o, beta)
        idx = s_sig.index.intersection(s_exec.index)
        s_sig, s_exec = s_sig.loc[idx], s_exec.loc[idx]
        test_mask = idx >= TEST_START
        z_test = ((s_sig - mu) / sigma).to_numpy()[test_mask.to_numpy()]
        s_test = s_exec.to_numpy()[test_mask.to_numpy()]
        times = idx.to_numpy()[test_mask.to_numpy()]
        cost_c = stress_cost_c(m['cost_c'], cost_factor)
        swap_cost_long = swap_cost_short = 0.0
        if name == 'XAUXAG':
            # своп комбинированной позиции зависит от стороны (аудит В-6, спека раздел 7).
            # MT5 swap_long/swap_short — знаковый доход за ночь; стоимость = -доход.
            # side=+1: long ноги A / short ноги B; side=-1: наоборот.
            swap_cost_long = -(costs[sym_a]['swap_long'] + costs[sym_b]['swap_short'])
            swap_cost_short = -(costs[sym_a]['swap_short'] + costs[sym_b]['swap_long'])
        result = run_backtest(z_test, s_test, times, cost_c,
                              swap_cost_long=swap_cost_long,
                              swap_cost_short=swap_cost_short)
        trades = result.trades
        pnls = [t.pnl_net for t in trades]
        sides = [t.side for t in trades]
        n_long = sum(1 for x in sides if x > 0)
        n_short = len(sides) - n_long
        # длина блока bootstrap — медианная длительность эпизодов TRAIN,
        # заморожена в screening.json (спека раздел 6, аудит В-1)
        expected_block = float(m['median_episode_duration_bars']) or 1.0
        results[name] = {
            'n_trades': len(trades),
            'n_per_side_min': min(n_long, n_short),
            'dropped_open_at_end': result.dropped_open_at_end,
            'pf': profit_factor(pnls),
            'pf_gross': profit_factor([t.pnl_gross for t in trades]),
            'bs_p05': stationary_bootstrap_ci(pnls, expected_block, n_resamples=10000, seed=0),
            'expected_block_bars': expected_block,
            'cost_factor': cost_factor,
            'eg_p_test': engle_granger_pvalue(
                np.log(a_c.loc[idx[test_mask.to_numpy()]].to_numpy(dtype=float)),
                np.log(b_c.loc[idx[test_mask.to_numpy()]].to_numpy(dtype=float))),
            'exit_reasons': {r: sum(1 for t in trades if t.exit_reason == r)
                             for r in ('revert', 'stop', 'timeout')},
            'pnl_by_reason': {r: float(sum(t.pnl_net for t in trades if t.exit_reason == r))
                              for r in ('revert', 'stop', 'timeout')},
            'swap_cost_long': swap_cost_long,
            'swap_cost_short': swap_cost_short,
        }
        results[name]['verdict'] = pair_verdict(results[name])
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['1', '2', 'all'], default='all')
    ap.add_argument('--stress-costs', type=float, default=1.0,
                    help='множитель round-trip издержек (методология 12: стресс 2x); '
                         'пишет отдельный артефакт backtest_stress<F>x.json')
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    costs = build_costs(COSTS_CSV)
    screening_path = OUT_DIR / 'screening.json'

    if args.stage in ('1', 'all'):
        legs_m5 = _load_legs(M5_DIR)
        # H1 — независимая агрегация брокера (экспорт MT5, Task 2),
        # не ресемплинг M5 (аудит В-2, спека раздел 3.3)
        legs_h1 = _load_legs(H1_DIR)
        out_m5 = _stage1_for_tf(legs_m5, costs, 'M5')
        out_h1 = _stage1_for_tf(legs_h1, costs, 'H1')
        payload = {'M5': out_m5, 'H1': out_h1}
        screening_path.write_text(json.dumps(payload, indent=2))
        print(f'Stage 1 -> {screening_path}')
        for tf in ('M5', 'H1'):
            for name, m in payload[tf]['candidates'].items():
                status = 'PASS' if m['pass'] else 'KILL(' + '; '.join(m['kill_reasons']) + ')'
                print(f"  [{tf}] {name}: {status}")
        if args.stage == '1':
            return 0

    screening_out = json.loads(screening_path.read_text())['M5']
    legs_m5 = _load_legs(M5_DIR)
    stage2 = _stage2(legs_m5, screening_out, costs, cost_factor=args.stress_costs)
    if args.stress_costs == 1.0:
        backtest_path = OUT_DIR / 'backtest.json'
    else:
        backtest_path = OUT_DIR / f'backtest_stress{args.stress_costs:g}x.json'
    backtest_path.write_text(json.dumps(stage2, indent=2))
    print(f'Stage 2 (cost x{args.stress_costs:g}) -> {backtest_path}')
    for name, r in stage2.items():
        print(f"  {name}: {r['verdict']} PF={r['pf']:.2f} BS_p05={r['bs_p05']:.2f} N={r['n_trades']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 4: Запустить тесты, убедиться что проходят**

Run: `./.venv/bin/python -m pytest tests/test_pair_spread_runner.py -q`
Expected: PASS (4 теста).

- [ ] **Step 5: Прогнать весь набор тестов этапа**

Run: `./.venv/bin/python -m pytest tests/test_pair_spread_data.py tests/test_pair_spread_screening.py tests/test_pair_spread_backtest.py tests/test_pair_spread_runner.py -q`
Expected: все PASS.

- [ ] **Step 6: Commit**

```bash
git add statistics/pair_spread/run_pair_spread.py tests/test_pair_spread_runner.py
git commit -m "Add pair-spread orchestrator with frozen thresholds and JSON artifacts"
```

---

### Task 7: Запуск ступени 1 и фиксация скрининга

**Files:**
- Исполняются: данные Task 2, код Tasks 3–6.
- Создаются: `DATA/pair_spread/screening.json` (в .gitignore или коммит как артефакт — по размеру; JSON коммитим, он небольшой).

- [ ] **Step 1: Проверить готовность данных**

Run: `./.venv/bin/python statistics/pair_spread/check_data.py`
Expected: PASS. Если FAIL — вернуться к Task 2 Step 3 (ручной экспорт).

- [ ] **Step 2: Запустить ступень 1**

Run: `./.venv/bin/python statistics/pair_spread/run_pair_spread.py --stage 1`
Expected: таблица `[M5] CANDIDATE: PASS/KILL(reasons)` и `[H1] ...`; файл `DATA/pair_spread/screening.json`.

- [ ] **Step 3: Сверка M5/H1**

Сравнить pass/kill по двум таймфреймам. Расхождение вердиктов по паре = красный флаг нестабильности (раздел 3.3 спеки) — зафиксировать в отчёте, решение о снятии пары принимается по M5 (основной таймфрейм), факт расхождения — в отчёт.

- [ ] **Step 4: Проверить распределение длительности эпизодов**

Если по данным `screening.json` медианная длительность эпизодов близка к 1 бару M5 (≈5 минут) у большинства кандидатов — зафиксировать в отчёте триггер тиковой диагностики (раздел 3.3 спеки); саму тиковую диагностику в этом этапе не запускать.

- [ ] **Step 5: Диагностика структурных сдвигов (аудит У-3, спека §4/§5)**

Одноразовый диагностический прогон (в репо не сохраняется, вывод — в отчёт):
устойчивость β между половинами train по каждому кандидату и поведение спреда
EURCHF вокруг снятия пола SNB (15.01.2015).

```bash
./.venv/bin/python - <<'PY'
import importlib.util, sys
from pathlib import Path
import numpy as np
import pandas as pd

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

pd_mod = load('pair_data', 'statistics/pair_spread/pair_data.py')
scr = load('screening', 'statistics/pair_spread/screening.py')
syms = ('AUDUSD', 'NZDUSD', 'USDCAD', 'EURUSD', 'GBPUSD', 'USDCHF', 'XAUUSD', 'XAGUSD')
legs = {s: pd_mod.load_ohlc_csv(f'MT/MQL4/Files/M5/{s}_OHLC.csv') for s in syms}
train_end = pd_mod.TRAIN_END
for name, cand in pd_mod.CANDIDATES.items():
    a, b = cand['legs']
    ca = legs[a]['close'][legs[a].index <= train_end]
    cb = legs[b]['close'][legs[b].index <= train_end]
    la, lb = np.log(ca), np.log(cb)
    mid = la.index[len(la) // 2]
    b1 = scr.fit_beta(la[la.index <= mid], lb[lb.index <= mid])
    b2 = scr.fit_beta(la[la.index > mid], lb[lb.index > mid])
    print(f'{name}: beta_half1={b1:.4f} beta_half2={b2:.4f}')
eu, ch = legs['EURUSD']['close'], legs['USDCHF']['close']
e_tr, c_tr = eu[eu.index <= train_end], ch[ch.index <= train_end]
beta = scr.fit_beta(np.log(e_tr), np.log(c_tr))
s = pd_mod.build_log_spreads(eu, ch, beta)
w = s[(s.index >= '2014-12-01') & (s.index <= '2015-02-28')]
print('EURCHF SNB 12/2014-02/2015: bars =', len(w),
      'max |ds| bar-to-bar =', float(w.diff().abs().max()))
PY
```

Expected: вывод β по двум половинам train для 7 кандидатов и статистика спреда
EURCHF в окне SNB. Интерпретация — диагностическая (не гейт): расхождение β
между половинами и скачок спреда EURCHF фиксируются в отчёте (раздел 8 спеки).

- [ ] **Step 6: Commit артефакта**

```bash
git add DATA/pair_spread/screening.json
git commit -m "Freeze stage-1 screening results for pair-spread candidates"
```

---

### Task 8: Запуск ступени 2, отчёт и decision memo

**Files:**
- Создаются: `DATA/pair_spread/backtest.json`, `DATA/pair_spread/backtest_stress2x.json`, `docs/reports/2026-08-XX-pair-spread.md` (XX — дата запуска).

- [ ] **Step 1: Запустить ступень 2 (только если ступень 1 дала ≥ 1 PASS)**

Run: `./.venv/bin/python statistics/pair_spread/run_pair_spread.py --stage 2`
Expected: таблица вердиктов `SURVIVED/KILLED/DIAGNOSTIC_ONLY` с PF/BS_p05/N; `DATA/pair_spread/backtest.json`. Если ступень 1 не дала ни одного PASS — шаг пропускается, тема убита на ступени 1 (раздел 8 спеки).

- [ ] **Step 1b: Стресс издержек 2x (методология 12, аудит В-3)**

Run: `./.venv/bin/python statistics/pair_spread/run_pair_spread.py --stage 2 --stress-costs 2.0`
Expected: `DATA/pair_spread/backtest_stress2x.json`; базовый `backtest.json` не перезаписан. Аргумент `--stress-costs` реализован в Task 6; никаких код-фиксов на этом шаге не допускается.

- [ ] **Step 2: Написать отчёт этапа**

`docs/reports/<дата>-pair-spread.md` со структурой по методологии 16 и разделу 8 спеки:
- таблица метрик скрининга по всем 7 парам × {M5, H1} (включая убитые, с причинами);
- вердикты ступени 2: PF gross/net, BS_p05, PnL по причинам выхода (revert/stop/timeout отдельно), `dropped_open_at_end` по каждой паре, годовые срезы PF по test-окну;
- распределение длительности эпизодов (из screening.json);
- стресс издержек 2x: вердикты по `backtest_stress2x.json` рядом с базовыми;
- диагностика структурных сдвигов из Task 7 Step 5 (β по половинам train, EURCHF SNB-окно);
- конвенция приоритета вердиктов (Q-1): EG-kill первичен, N-гейт ограничивает только SURVIVED;
- оговорки: режимный перелом 2023 (раздел 6 спеки), множественность 7 кандидатов (раздел 9), ограничение спред-снимка (раздел 7), сайзинг при β<0 — `abs(β)` (аудит У-5, для будущего production-контура);
- вердикт по классу: убита / есть SURVIVED / мощность недостаточна (раздел 8 спеки).

- [ ] **Step 3: Полные тесты**

Run: `./.venv/bin/python -m pytest tests/ -q`
Expected: не хуже baseline (1605 passed, 1 failed pre-existing `test_mql_telemetry_params_csv_contract.py` по дрейфу tester .ini — к этапу отношения не имеет; зафиксировать в отчёте, если число отличается).

- [ ] **Step 4: Синхронизация report/CHANGELOG/CONTEXT_HANDOFF + wiki**

Скилл `stage-reporting`: закрыть этап, обновить CHANGELOG.md, CONTEXT_HANDOFF.md (active track, decision, next step), выполнить wiki Ingest.

- [ ] **Step 5: Decision memo по exit_decisions плана**

В отчёте явно записать решение: `close` (все убиты → переход к идее 2 роэдмэпа), `continue` (SURVIVED → новый план production-контура) или `unblock` (мощность недостаточна → тиковая диагностика отдельным треком).

- [ ] **Step 6: Commit**

```bash
git add DATA/pair_spread/backtest.json DATA/pair_spread/backtest_stress2x.json docs/reports/
git commit -m "Add pair-spread kill-test results and stage report"
```

---

## Self-Review Notes

- Спека раздел 3 (данные): Task 2 + Task 3 (загрузка/кроссы/сплит); fallback глубины — check_data.py.
- Раздел 4 (спред/β/конвенция): Task 3 (лог-спред), Task 5 (close-сигнал / open-исполнение).
- Раздел 5 (ступень 1, все 4 порога + операционализация |Δs|): Task 4, Task 6 (cost_c).
- Раздел 6 (машинные правила, σ, сайзинг, bootstrap, гейт N≥100, режимный перелом): Task 5 + Task 6 (pair_verdict) + Task 8 (годовые срезы в отчёте).
- Раздел 7 (издержки, комиссия 0, своп XAUXAG, стресс 2x): Task 6 (build_costs, swap в _stage2), Task 8 Step 2 (стресс).
- Раздел 8 (артефакты, gross/net, причины выхода): Task 6, Task 8.
- Раздел 9 (предрегистрация, множественность): пороги заморожены в коде Task 4/6; оговорка множественности — в отчёте (Task 8 Step 2).
- Типы/имена: `fit_beta`, `engle_granger_pvalue`, `half_life_bars`, `episode_bounds`, `spread_mu_sigma`, `screening_metrics`, `verdict_pass`, `run_backtest`, `profit_factor`, `stationary_bootstrap_ci`, `build_costs`, `round_trip_cost_c`, `stress_cost_c`, `pair_verdict`, `BacktestResult` — согласованы между задачами.

## Доработки по аудиту 2026-08-18 (`docs/superpowers/audit.md`)

- К-1: все 4 тестовых файла регистрируют модуль в `sys.modules` до `exec_module` (иначе `@dataclass` падает на Python 3.10).
- К-2: исправлены 4 контрольных примера (`test_build_log_spreads_beta` — a=b²; `test_half_life_antipersistent_is_inf` вместо random walk; EG-тест независимых рядов — сид 2, p≈0.96; `test_one_position_no_pyramiding` — добавлен завершающий бар) + новый `test_open_position_at_end_dropped_and_counted`.
- В-1/В-4: длительности эпизодов train в `screening_metrics`, медиана — длина блока bootstrap (замораживается в screening.json).
- В-2: H1-срез читается из `MT/MQL4/Files/H1/` (независимый экспорт брокера), не ресемплинг M5.
- В-3: `--stress-costs` в Task 6 + отдельный артефакт `backtest_stress2x.json` (Task 8 Step 1b).
- В-5: нормировка издержек по последним ценам TRAIN.
- В-6: своп XAUXAG по стороне сделки (`swap_cost_long`/`swap_cost_short`).
- У-1: интерфейс `screening_metrics` приведён к 4 аргументам.
- У-2: f-строка check_data.py исправлена.
- У-3: Task 7 Step 5 — диагностика β по половинам train и EURCHF SNB-окна.
- У-5: оговорка сайзинга `abs(β)` — в Global Constraints и отчёте.
- Q-1: конвенция приоритета вердиктов — в Global Constraints, `pair_verdict` и отчёт.
- Q-2: Task 0 — регистрация трека в roadmap.md.
- Q-3: `dropped_open_at_end` в `BacktestResult` и `backtest.json`.
- Отклонено: У-4 (векторизация bootstrap) — аудит сам помечает неблокирующим; корректность текущей реализации подтверждена тестами.
- Проверка: весь код плана извлечён и прогнан — 31 тест PASS (до фиксов: 23 passed, 4 failed + 2 файла не загружались).
