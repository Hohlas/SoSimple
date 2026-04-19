# feature_importance_diagnostics.py

## Назначение

Read-only диагностика важности групп текущих признаков из `Nero_*_labeled.csv`.

Инструмент нужен перед изменением `lib_PIC.mqh`: он показывает, какие уже экспортируемые группы признаков реально помогают объяснять выбранную цель, а какие выглядят слабыми.

## Входные данные

- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`

CSV читается чанками и только по нужным колонкам.

## Выходные данные

По умолчанию:

```text
ML/reports/current_feature_importance/group_importance.csv
ML/reports/current_feature_importance/feature_importance.csv
ML/reports/current_feature_importance/summary.json
ML/reports/current_feature_importance/report.md
```

## Логика

1. Берёт хвостовую выборку train/validation.
2. Парсит текущий 22-полевой формат фракталов.
3. Строит агрегаты по окнам `5/10/20/50/100`.
4. Группирует признаки по смыслу:
   `price_position`, `direction`, `geometry`, `strength`, `break_impulse`, `path_long`, `path_short`, `atr`, `row_context`.
5. Обучает лёгкую `RandomForestRegressor`.
6. Считает важность групп через перестановку всей группы на validation.

## Использование

```bash
python -m ML.feature_importance_diagnostics \
  --target trail_24_pnl_atr_x8 \
  --seq-len 20 \
  --max-train-rows 12000 \
  --max-validation-rows 6000 \
  --n-estimators 120
```

## Ограничения

- Это не торговый benchmark и не PF-оценка.
- Это не новое обучение Track A.
- Высокая важность группы не означает, что признак можно безопасно использовать в production.
- Группы `path_long` и `path_short` требуют отдельной проверки риска утечки будущего перед использованием в новых постановках.
