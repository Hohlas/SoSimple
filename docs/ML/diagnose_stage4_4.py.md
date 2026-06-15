# ML/baseline/diagnose_stage4_4.py

## Назначение

Stage 4.4 DIAGNOSTIC_ONLY: diagnostic micro-check перед Transformer Stage 5.0.
Проверяет три гипотезы на фиксированных Stage 4.2 моделях без нового обучения:
1. Relax breach filter p=0.5 — даёт ли ослабление фильтра рост PF?
2. Fixed TP (R ∈ {0.5, 0.7, 1.0}) — уступает ли fav-based TP фиксированному?
3. Breach-only entry + Fixed TP — работает ли breach без fav-фильтра?

Не выбирает winner, не открывает test, не меняет verdict Stage 4.

## Входы

- `DATA/Nero_XAUUSD_train_labeled.csv` — обучающая выборка
- `DATA/Nero_XAUUSD_validation_labeled.csv` — валидация
- `DATA/XAUUSD_H1_OHLC.csv` — OHLC бары

## Выход

- `ML/reports/stage4_4_micro_check.json` — structured artifact диагностики (8 cells)

JSON включает baseline (Stage 4.2 reproduction), три эксперимента (relax breach, fixed TP, breach-only), comparison summary, permutation tests и interpretation guards.

## Команда запуска

```bash
~/git/SoSimple/.venv/bin/python -m ML.baseline.diagnose_stage4_4 \
  --train DATA/Nero_XAUUSD_train_labeled.csv \
  --val DATA/Nero_XAUUSD_validation_labeled.csv \
  --ohlc DATA/XAUUSD_H1_OHLC.csv \
  --output ML/reports/stage4_4_micro_check.json \
  --spread 0.20 --seed 42
```

## Статус

`DIAGNOSTIC_ONLY` — все результаты являются `hypothesis_only`, пока не проверены отдельным val-select/val-eval протоколом.

## Ограничения интерпретации

- Не открывает test
- Не выбирает нового winner
- Лучшая ячейка не является торговым правилом — hypothesis_only
- Трейлинг-стоп не проверялся
- Stage 4 verdict не меняется
- Все ячейки оценены на тех же данных, где исторически выбран Stage 4 winner (historical selection bias не устранён)
- Permutation test не исправляет множественное тестирование/selection bias
- Результаты не доказывают, что breach работает без fav — только диагностика на исторических данных
