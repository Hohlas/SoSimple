# Stage 5.0 Transformer Breach Holdout — Результаты

**Дата:** 2026-06-17
**Статус:** DIAGNOSTIC_FAIL_WITH_PREPROCESSING_BUG
**Вердикт:** MODEL_FAIL (нормализация отсутствовала — требуется повторный прогон)

> **ВАЖНО:** Первоначальный прогон выполнен без нормализации признаков. StandardScaler был импортирован, но не применён. Признак `price` в долларах (390–2650) доминировал над остальными (0..1) в attention-механизме Transformer. Выводы относятся к прогону без нормализации. Исправленная версия с раздельным StandardScaler (token/row) и relative_price диагностическими профилями готова к повторному запуску.

## Контекст

После провала Stage 4.x табличных моделей (RF→XGBoost, лучший AUС=0.667, PF=1.015) и Stage 4.6 walk-forward (trail_atr_0_2 прошёл 2019-2022 но провалил 2023-2026), проверяем, даёт ли Transformer на последовательности фракталов улучшение breach-ранжирования.

Stage 5.0 — диагностический этап без торгового grid search: только модельный слой.

## Дизайн эксперимента

### Сплит

| Роль | Годы | Строк |
|------|------|-------|
| train | 2004—2020 | 25,672 |
| val_stop | 2021—2022 | 2,832 |
| holdout | 2023—2026 | 4,527 |

Train расширен до 2020 (вместо Stage 4.2: ≤2016) для увеличения обучающей выборки Transformer. 2019-2020 были XGBoost validation, не frozen test — утечки нет.

### Модель

Transformer Encoder (d_model=64, nhead=4, dim_feedforward=128, 2 слоя, dropout=0.15, masked mean + newest-token pooling, BCEWithLogitsLoss, AdamW lr=1e-3, weight_decay=1e-4, pos_weight из train, early stopping patience=8 на val_stop, до 60 эпох). CPU-прогон, один seed [42] (единственное разрешённое планом упрощение).

### Профили (A6-нотация)

| # | Профиль | Назначение |
|---|---------|-----------|
| 1 | `all100_base10_time` | Primary: все фракталы, base10, с временем |
| 2 | `all100_base10_no_time` | Calendar control |
| 3 | `newest20_base10_time` | Только 20 свежих фракталов |
| 4 | `nearest40_base10_time` | 40 ближайших по цене |
| 5 | `corridor_10atr_base10_time` | Коридор ±10 ATR |

### Baseline

XGBoost (те же признаки, тот же сплит):
- `base_raw_plus_time` — все фрактальные + временные признаки
- `no_time` — без временных признаков
- `time_only` — только временные признаки (ATR + hour/dow)

### Gate (primary profile only)

- holdout AUC ≥ max(XGBoost+0.02, time_only+0.04)
- holdout lift_bottom30 ≥ XGBoost lift_bottom30 + 0.10
- yearly AUC ≥ 0.55 в ≥3 из 4 лет holdout

## Результаты

### XGBoost baselines

| Baseline | Val AUC | Holdout AUC | Lift_10 | Lift_20 | Lift_30 |
|----------|---------|-------------|---------|---------|---------|
| base_raw_plus_time | 0.6631 | **0.6524** | 0.370 | 0.514 | 0.620 |
| no_time | 0.6273 | 0.6456 | 0.381 | 0.500 | 0.612 |
| time_only | 0.6314 | 0.6059 | 0.773 | 0.729 | 0.736 |

### Transformer

| Профиль | Val AUC | Holdout AUC | Lift_10 | Lift_20 | Lift_30 | Δ vs XGBoost | Эпох |
|---------|---------|-------------|---------|---------|---------|-------------|------|
| `all100_base10_time` (primary) | 0.6432 | 0.6018 | 0.702 | 0.723 | 0.766 | **−0.0506** | 40 |
| `all100_base10_no_time` | 0.5291 | 0.4987 | 0.920 | 0.995 | 0.996 | −0.1537 | 9 |
| `newest20_base10_time` | 0.6420 | 0.5953 | 0.865 | 0.769 | 0.777 | −0.0571 | 28 |
| `nearest40_base10_time` | 0.6432 | **0.6034** | 0.702 | 0.699 | 0.754 | −0.0490 | 29 |
| `corridor_10atr_base10_time` | 0.6426 | 0.6025 | 0.713 | 0.718 | 0.755 | −0.0499 | 29 |

Диагностическое ранжирование по holdout AUC (DIAGNOSTIC_ONLY):
1. nearest40: 0.6034
2. corridor_10atr: 0.6025
3. all100_base10: 0.6018
4. newest20: 0.5953
5. no_time: 0.4987

Все профили ниже XGBoost base_raw_plus_time (0.6524). Все профили ниже XGBoost no_time (0.6456). Только all100_base10_time выше time_only (0.6018 vs 0.6059) — нет, он ниже.

### Gate verdict

Lift_30 = доля пробоев в нижних 30% predict_break / общая доля. Меньше = лучше.

| Gate | Порог | Факт | Пройден |
|------|-------|------|---------|
| AUC vs XGBoost | +0.02 | −0.0506 | ❌ |
| Lift_30 vs XGBoost | −0.10 (меньше) | +0.1467 (хуже) | ❌ |
| Yearly AUC ≥ 0.55 в ≥3/4 лет | — | 3/4 | ✅ |
| **Вердикт** | | | **FAIL** |

Transformer проигрывает XGBoost и по AUC (−0.051), и в безопасной зоне (lift_30 0.766 vs 0.620).

### Годовой разрез holdout (all100_base10_time)

| Год | Строк | AUC | Lift_30 |
|-----|-------|-----|---------|
| 2023 | 1,370 | 0.6461 | 0.648 |
| 2024 | 1,431 | 0.6263 | 0.788 |
| 2025 | 1,410 | 0.5702 | 0.708 |
| 2026 | 316 | 0.5135 | 0.910 |

Деградация AUC со временем: 0.646→0.626→0.570→0.514. Согласуется с выводами Stage 4.6: модель ≤2020 не обобщается на 2023-2026.

### Corridor validation

| Коридор | Медиана фракталов | pct_empty | Статус |
|---------|-------------------|-----------|--------|
| 10 ATR | 65.0 | ~0% | OK |

Коридор 10 ATR заполнен отлично — высокое покрытие фракталами вокруг fractal0.

## Анализ

### Transformer не бьёт XGBoost

Полноразмерный Transformer (d_model=64, nhead=4, 40 эпох) проигрывает XGBoost на holdout: 0.6018 vs 0.6524, gap −0.051. Это не near-pass (gap > 0.02 в худшую сторону). Это FAIL.

Факт, что даже XGBoost без временных признаков (AUC=0.6456) бьёт Transformer со временем (0.6018), указывает на фундаментальную проблему: **Transformer не извлекает из последовательной структуры фракталов сигнал, сравнимый с flat-представлением XGBoost**. XGBoost видит те же фракталы как плоскую таблицу и справляется лучше.

### Календарный риск подтверждён

- `all100_base10_no_time` (AUC=0.4987) — ниже случайного. Без временных признаков Transformer не может предсказать breach вообще.
- `time_only` XGBoost (AUC=0.6059) почти догоняет Transformer с фракталами (0.6018).
- Вывод Stage 5-prep (time features несут 56% breach-сигнала) подтверждён на Transformer.

### Transformer хуже XGBoost и в low-risk зоне

Lift_30 = доля пробоев в нижних 30% predict_break / общая доля пробоев. Меньше = лучше (в безопасной зоне должно быть меньше пробоев). Transformer lift_30 = 0.766 против XGBoost 0.620 — Transformer **хуже** на 0.146 в безопасной зоне. Ни gate1 (AUC), ни gate2 (lift_30) не пройдены.

### Выбор фрактального подмножества несущественен

Разброс между профилями: 0.5953 (newest20) — 0.6034 (nearest40), диапазон 0.0081. Это шум, а не сигнал. Ни один способ отбора фракталов не даёт принципиального преимущества.

### yearly degradation совпадает с Stage 4.6

AUC падает с 0.646 (2023) до 0.514 (2026). Модель, обученная на данных ≤2020, теряет способность предсказывать breach на +5-6 лет вперёд. Это структурная проблема, а не недостаток Transformer.

## Выводы

1. **Transformer Stage 5.0 — DIAGNOSTIC_FAIL_WITH_PREPROCESSING_BUG.** Полноразмерный Transformer (d_model=64, 40 эпох) **без нормализации** не превосходит XGBoost на holdout 2023-2026. Gap −0.051 в пользу XGBoost.

2. **Отсутствие нормализации могло существенно повлиять на результат.** Признак `price` (390–2650 долларов) доминировал над остальными (0..1) в attention. StandardScaler не был применён несмотря на импорт. Требуется повторный прогон с исправленной нормализацией.

3. **5 последовательных этапов Fractal Stop провалились** (Stage 2→3→4→4.6→5.0). Но вывод о Stage 5.0 преждевременен до повторного прогона с нормализацией.

4. **Calendar risk — ключевой фактор.** Без временных признаков модель не работает (AUC=0.4987). С ними XGBoost достигает AUC=0.6524.

## Non-conclusions

- Не выбран trading winner.
- Не вычислен PF.
- 2023-2026 был diagnostic holdout, уже использованный в Stage 4.6/walk-forward — не чистый future test.
- Walk-forward diagnostics не запущены (Transformer FAIL на holdout).
- Все профили кроме primary имеют статус DIAGNOSTIC_ONLY.

## Legacy holdout disclosure

2023-2026 использовался как диагностический holdout в Stage 4.6/walk-forward. Это не чистый будущий test. Результат этого этапа не должен использоваться для ручной подгонки модели под этот период.

## Next step

1. Не строить Stage 5.1 trading layer.
2. Решение: пересмотреть постановку задачи Fractal Stop или закрыть ветку.
   - Альтернатива 1: трейлинг-стоп как execution-политика (trail_atr_0_2 показал PF=1.831 на Stage 4.5 diagnostic), а не breach-прогноз.
   - Альтернатива 2: пересмотр таргета (12 бинарных TB-таргетов, Stage 3.x Regression).
   - Альтернатива 3: закрыть Fractal Stop и вернуться к основному направлению (regression_updn, triple barrier).

## Приложение: параметры прогона

| Параметр | Значение |
|----------|---------|
| d_model | 64 |
| nhead | 4 |
| dim_feedforward | 128 |
| max_epochs | 60 |
| early_stopping_patience | 8 |
| batch_size | 256 |
| learning_rate | 1e-3 |
| weight_decay | 1e-4 |
| seeds | [42] (single, CPU) |
| device | CPU |
| Общее время | ~56 минут |

## Файлы

- `ML/baseline/benchmark_stage5_transformer_breach.py` — основной раннер
- `ML/models/fractal_breach_transformer.py` — модель Transformer
- `ML/reports/stage5_transformer_breach.json` — структурированный результат
- `tests/test_stage5_transformer_breach.py` — 39 тестов
- `docs/superpowers/plans/2026-06-16-stage5_0-transformer-breach-holdout.md` — план
