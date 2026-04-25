# trim_pre2004_csv.py

## Назначение
CLI-утилита для освобождения места в проектных CSV за счёт удаления строк старше заданной даты.

## Входные данные
- Явно переданные CSV через `--files`
- По умолчанию:
  - `DATA/Nero_EURUSD_train_labeled.csv`
  - `DATA/Nero_GBPUSD_train_labeled.csv`
  - `DATA/Nero_USDCHF_train_labeled.csv`
  - `MT/MQL4/Files/Nero_EURUSD.csv`
  - `MT/MQL4/Files/Nero_GBPUSD.csv`
  - `MT/MQL4/Files/Nero_USDCHF.csv`
  - `MT/MQL4/Files/EURUSD_H1_OHLC.csv`
  - `MT/MQL4/Files/GBPUSD_H1_OHLC.csv`
  - `MT/MQL4/Files/USDCHF_H1_OHLC.csv`

## Поведение
- По умолчанию запускается в dry-run и только печатает, сколько строк было бы удалено.
- С `--apply` переписывает файлы in-place без резервных копий.
- Строки сохраняются, если `time >= cutoff`.
- Header CSV сохраняется.

## Использование
```bash
./.venv/bin/python -m processing.trim_pre2004_csv
./.venv/bin/python -m processing.trim_pre2004_csv --apply
./.venv/bin/python -m processing.trim_pre2004_csv --apply --files DATA/Nero_EURUSD_train_labeled.csv
```

## Ограничения
- Ожидается колонка `time` в формате `YYYY.MM.DD HH:MM`.
- Утилита рассчитана на проектные CSV с разделителем `;`.
- Если нужно другое граничное значение, можно передать `--cutoff YYYY-MM-DD`.
