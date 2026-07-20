# ML/baseline/analyze_stage6_2_range_w1_postmortem.py

Диагностический post-mortem для Stage 6.2 `range_w1_atr`.

## Назначение

Скрипт объясняет, почему `range_w1_atr` стал главным price-action признаком в Stage 6.2, и почему проверка устойчивости осталась слабой.

Он не обучает модель заново и не выбирает новый профиль. Источник модельных результатов — уже созданный Stage 6.2 JSON.

## Входы

- `ML/reports/stage6_2_h12_price_action_feature_family.json`
- `DATA/Nero_XAUUSD_train_labeled.csv`
- `DATA/Nero_XAUUSD_validation_labeled.csv`
- `DATA/Nero_XAUUSD_test_labeled.csv`
- `DATA/XAUUSD_H1_OHLC.csv`

## Выходы

- `ML/reports/stage6_2_range_w1_postmortem.json`
- `docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md`

## Запуск

```bash
./.venv/bin/python ML/baseline/analyze_stage6_2_range_w1_postmortem.py
```

## Проверки

Скрипт собирает:

- доминирование `range_w1_atr` над вторым признаком;
- связь `range_w1_atr` с целевой колонкой и PnL;
- разрезы по BUY/SELL и годам;
- selected vs non-selected rows по seed-порогам из Stage 6.2;
- связь `range_w1_atr` с `ATR` и `bar_range_1_atr`;
- observed PF против случайной перестановки по seed;
- disclosure по zero-vector строкам для `val_stop`, `diagnostic_holdout`, `low_n_disclosure`.

## Ограничения

Результат остаётся `DIAGNOSTIC_ONLY`. Скрипт не открывает новый поиск по H12/ATR/TP/SL, не использует holdout для выбора и не продвигает Stage 6.2 в candidate.
