# ML/baseline/diagnose_stage4_3.py

## Назначение

Stage 4.3 DIAGNOSTIC_ONLY: декомпозиция потерь PF между Oracle и Stage 4.2 baseline.
Не выбирает winner, не открывает test, не меняет verdict Stage 4.

## Входы

- `DATA/Nero_XAUUSD_train_labeled.csv` — обучающая выборка
- `DATA/Nero_XAUUSD_validation_labeled.csv` — валидация
- `DATA/XAUUSD_H1_OHLC.csv` — OHLC бары

## Выход

- `ML/reports/stage4_3_diagnostics.json` — structured artifact диагностики

JSON включает baseline metrics, loss attribution, breach/fav buckets, cumulative 2D map, actual RR, TP-policy comparison и расширенный `oracle_deviation_attribution`:

- 4 режима model/oracle;
- взаимно исключающие breach-entry категории;
- fav-error категории на строках, где вход разрешён model breach или oracle breach;
- forced diagnostic PnL, yearly PF, TP/SL/TIMEOUT и block-bootstrap интервал среднего PnL по категориям.

## Команда запуска

```bash
~/git/SoSimple/.venv/bin/python -m ML.baseline.diagnose_stage4_3 \
  --train DATA/Nero_XAUUSD_train_labeled.csv \
  --val DATA/Nero_XAUUSD_validation_labeled.csv \
  --ohlc DATA/XAUUSD_H1_OHLC.csv \
  --output ML/reports/stage4_3_diagnostics.json \
  --spread 0.20 --seed 42
```

## Статус

`DIAGNOSTIC_ONLY` — найденные прибыльные зоны являются `hypothesis_only`, пока не проверены отдельным val-select/val-eval протоколом.

## Ограничения интерпретации

- Не открывает test
- Не выбирает нового winner
- Лучшая ячейка/политика не является торговым правилом
- Трейлинг-стоп не проверялся как Stage 4.3 candidate
- Stage 4 verdict не меняется
- Oracle labels — будущая информация, не торговые признаки
- Forced diagnostic PnL по категориям нужен только для атрибуции ошибок, а не для выбора winner
