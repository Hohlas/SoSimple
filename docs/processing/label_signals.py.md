# label_signals.py

## Назначение
Маркировка данных: `signal`, `predict` и up/dn fixed-horizon таргеты на основе forward-scan по фракталам.

## Входные данные
- DataFrame с отсортированными фракталами.
- Формат строки фрактала: `T:P:Dir:Frnt:Back:Strong:Brk:Rev:Pwr:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:Up3:Dn3:Up6:Dn6:FractalAtr:Shift` (23 поля).

## Выходные данные
- DataFrame с колонками `signal`, `predict`, `up_3`, `dn_3`, `up_6`, `dn_6`, `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48`.

## Ключевые функции

| Функция | Описание |
|---------|----------|
| `parse_fractal(str)` | Парсинг 23-полевой строки фрактала → dict; integer-like поля допускают нормализованную float-запись (`1.0`, `0.1700000018`) |
| `find_fractal_by_time(row, cols, t)` | Поиск фрактала по времени в строке |
| `label_all(input, output, debug)` | Маркировка signal + predict (forward-scan до пробоя/вытеснения) |
| `label_updn(df, debug)` | Извлечение up/dn таргетов: для fractal0 сканирует вперёд до вытеснения, берёт последние накопленные Up/Dn |
| `label_signals()` | Только signal (обёртка) |
| `label_predict_only()` | Только predict (обёртка) |

## Примечания
- `label_updn()` использует те же Up/Dn, что накоплены MQL4 в `LEVELS_FIND_AROUND()` — значения уже в CSV, Python только извлекает финальные.
- Look-ahead допустим только для обучающей разметки, не при инференсе.
- `parse_fractal()` в `label_signals.py` — semantic parser для разметки. Для ML-признаков из нормализованных CSV нельзя полагаться на восстановление исходных категорий `strong/break/count` через `int(float(...))`; такие каналы нужно читать как float-признаки отдельным feature extractor.
