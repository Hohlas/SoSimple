# Task 1 Report: Freeze Current OHLC Sources And Labeled Input

Дата выполнения: 2026-07-29

## Что сделано

1. Проверил методологическую точку входа:
   - `docs/methodology/README.md`
   - `docs/methodology/01-raw-data-inventory.md`
   - `docs/methodology/12-backtest-costs.md`
2. Подтвердил наличие всех входов Task 1:
   - `DATA/XAUUSD_H1_OHLC.csv`
   - `DATA/XAUUSD_H1_OHLC_prev_20260701.csv`
   - `MT/MQL4/Files/XAUUSD_H1_OHLC.csv`
   - `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`
   - `DATA/Nero_XAUUSD_test_labeled.csv`
3. Снял контрольные sha256-хэши текущих источников.
4. Запустил существующий reconcile script:
   - `./.venv/bin/python ML/reports/fractal0_fixed11_retained_mt4_parity/reconcile_fill_chronology.py`
5. Проверил итоговый manifest:
   - `ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json`

## Команды и ключевые результаты

### Методология

Команды:

```bash
sed -n '1,90p' docs/methodology/README.md
sed -n '1,120p' docs/methodology/01-raw-data-inventory.md
sed -n '1,120p' docs/methodology/12-backtest-costs.md
```

Результат:

- `README.md` содержит `DIAGNOSTIC_ONLY`.
- `01-raw-data-inventory.md` содержит `Lower-Timeframe Execution OHLC Audit`.
- `12-backtest-costs.md` содержит `Lower-timeframe execution ordering`.

### Проверка файлов

Команда:

```bash
ls -l DATA/XAUUSD_H1_OHLC.csv DATA/XAUUSD_H1_OHLC_prev_20260701.csv MT/MQL4/Files/XAUUSD_H1_OHLC.csv MT/MQL4/Files/XAUUSD_M5_OHLC.csv DATA/Nero_XAUUSD_test_labeled.csv
```

Результат:

- Все требуемые файлы присутствуют.

### Контрольные хэши

Команда:

```bash
sha256sum DATA/XAUUSD_H1_OHLC.csv DATA/XAUUSD_H1_OHLC_prev_20260701.csv MT/MQL4/Files/XAUUSD_H1_OHLC.csv MT/MQL4/Files/XAUUSD_M5_OHLC.csv DATA/Nero_XAUUSD_test_labeled.csv
```

Результат:

- `DATA/XAUUSD_H1_OHLC.csv` = `MT/MQL4/Files/XAUUSD_H1_OHLC.csv`
- `DATA/XAUUSD_H1_OHLC_prev_20260701.csv` отличается от текущего H1
- `MT/MQL4/Files/XAUUSD_M5_OHLC.csv` имеет отдельный hash
- `DATA/Nero_XAUUSD_test_labeled.csv` присутствует и hashable

Хэши:

- current H1: `affd627e55ad777cd763a4f5105420e38cefdf6e4ae94974f14c33509865029f`
- previous H1: `4bf7a23ab79f41824713fa881078d06fb84fd7c484b2840c3cdec0bfdfda5aff`
- MT4 exported H1: `affd627e55ad777cd763a4f5105420e38cefdf6e4ae94974f14c33509865029f`
- M5 CSV: `85e6bbc49bc7e4049810cfb4a3d603576b9cd7b363c7b2f52bc43b59ef8c9a9b`
- labeled input: `5beb70f29ee27caa2b20a8cd80376879b64179d4ef0e5197a29357b58483f535`

### Reconcile

Команда:

```bash
./.venv/bin/python ML/reports/fractal0_fixed11_retained_mt4_parity/reconcile_fill_chronology.py
```

Результат:

- Команда завершилась с кодом `0`.
- Скрипт записал:
  - `ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json`
  - `ML/reports/fractal0_fixed11_retained_mt4_parity/chronology_examples.csv`
- Выведены event counts:
  - `OPEN`: 717
  - `CLOSE`: 717
  - `OPEN_FAILED`: 404
  - `ORDER_PLACED`: 1115

### Проверка manifest

Команда:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

p = Path("ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json")
d = json.loads(p.read_text(encoding="utf-8"))

required = [
    "previous_python_h1_vs_hst",
    "current_data_h1_vs_hst",
    "current_m5_vs_hst_m5",
    "previous_python_h1_vs_current_data_h1",
    "current_data_h1_vs_mt4_exported_h1",
]
missing = [k for k in required if k not in d]
assert not missing, missing

assert d["current_data_h1_vs_mt4_exported_h1"]["diff_rows"] == 0
assert d["current_data_h1_vs_hst"]["matched_rows"] > 120000
assert d["current_m5_vs_hst_m5"]["matched_rows"] > 1000000
assert d["previous_python_h1_vs_current_data_h1"]["diff_rows"] > 0

for name in ["current_data_h1", "previous_python_h1", "mt4_exported_h1", "m5_csv"]:
    info = d["artifact_hashes"][name]
    assert info["exists"] is True
    assert len(info["sha256"]) == 64

print("history_manifest_ok")
print("current_data_h1_vs_hst", d["current_data_h1_vs_hst"])
print("current_m5_vs_hst_m5", d["current_m5_vs_hst_m5"])
print("previous_python_h1_vs_current_data_h1", d["previous_python_h1_vs_current_data_h1"])
PY
```

Результат:

- `history_manifest_ok`
- `current_data_h1_vs_hst`:
  - `matched_rows`: `128679`
  - `diff_rows`: `1`
  - `csv_only_rows`: `19`
  - `hst_only_rows`: `0`
  - `large_differences_by_year`: `{"2026": 1}`
- `current_m5_vs_hst_m5`:
  - `matched_rows`: `1484849`
  - `diff_rows`: `1`
  - `csv_only_rows`: `355`
  - `hst_only_rows`: `0`
  - `large_differences_by_year`: `{"2026": 1}`
- `previous_python_h1_vs_current_data_h1`:
  - `matched_rows`: `127829`
  - `diff_rows`: `13504`
  - `left_only_rows`: `477`
  - `right_only_rows`: `869`

## Изменённые файлы

- `.superpowers/sdd/task-1-report.md`

## Проверенные артефакты

- `ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json`
- `ML/reports/fractal0_fixed11_retained_mt4_parity/chronology_examples.csv`

Оба tracked-артефакта были пересобраны reconcile-скриптом и затем проверены; git diff по ним остался пустым, то есть содержимое совпадает с текущим HEAD.

## Самопроверка

- Входные файлы Task 1 присутствуют и hashable.
- `DATA/XAUUSD_H1_OHLC.csv` и `MT/MQL4/Files/XAUUSD_H1_OHLC.csv` имеют одинаковый sha256.
- `DATA/XAUUSD_H1_OHLC_prev_20260701.csv` отличается от текущего H1.
- `DATA/Nero_XAUUSD_test_labeled.csv` сохранён как неизменённый labeled input.
- `fill_chronology_manifest.json` содержит требуемые секции и ключевые hash-поля.
- Проверки по H1/M5 к HST прошли; остались только одиночные расхождения в latest edge rows, что соответствует brief.
