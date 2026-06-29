# Context Handoff

Дата: 2026-06-26

## Текущий этап

Stage 5.3 завершён. Вердикт отчёта: **DIAGNOSTIC_ONLY**.

JSON artifact имеет статус `TARGET_REFORMULATION_FOUND`, но это не торговый кандидат. Статус означает только одно: дискретная постановка цели time-to-breach достойна следующего диагностического шага.

## Что сделано

Stage 5.3 проверил target reformulation поверх Stage 5.2 колонок:

- `sell_bars_to_breach_H6_off05`
- `buy_bars_to_breach_H6_off05`

Проверенные цели:

- main: `breach_after_k2`, `breach_after_k3`, `breach_after_k4`, `breach_after_k5`
- main buckets: `fast`, `medium`, `no_breach`
- baseline: `binary_breach`
- controls: `survives_at_least_k2..k5`

Профили:

- `time_only`
- `clock_shift`
- `clock_shift_back`
- `clock_shift_impulse`
- `clock_shift_back_impulse`
- `structure_full`

Полный прогон:

- `432/432` XGBoost-классификации
- `workers=12`
- `xgb_threads=1`
- elapsed `1888.193s`
- artifact: `ML/reports/stage5_3_time_to_breach_target_reformulation.json`
- report: `docs/reports/2026-06-26-stage5_3-time-to-breach-target-reformulation.md`

Кодовые изменения:

- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`

Важная техническая правка: Stage 5.3 runner предвычисляет признаки один раз на `(source, profile, split)`, иначе структурные профили повторно строились сотни раз и создавали видимое зависание. `build_stage5_2_features()` также получил fast path для `time_only` и более прямой индексный парсер фрактальных полей.

## Главный результат

Лучший main target на обеих сторонах — bucket `fast`.

Sell:

- winner: `sell_fast`
- profile: `clock_shift_back`
- val AUC `0.6967`
- val PR AUC `0.3171`
- positive_rate `0.1501`
- holdout AUC `0.6849`
- same-profile binary baseline AUC `0.6688`
- delta vs binary baseline `+0.0279` (median)
- per-seed delta: s42 `+0.0232`, s77 `+0.0328`, s123 `+0.0276` — **3/3 проходят порог ≥0.02**
- holdout drop: `−0.012` (умеренный)
- gate: `TARGET_REFORMULATION_FOUND`
- статус: подтверждённая диагностическая цель для Stage 5.4

Buy:

- winner: `buy_fast`
- profile: `clock_shift_back_impulse`
- val AUC `0.7127`
- val PR AUC `0.3235`
- positive_rate `0.1562`
- holdout AUC `0.6617`
- same-profile binary baseline AUC `0.6928`
- delta vs binary baseline `+0.0199` (median)
- per-seed delta: s42 `+0.0217` (PASS), s77 `+0.0182` (FAIL, отрыв 0.0018), s123 `+0.0171` (FAIL, отрыв 0.0029) — **1/3 проходит порог ≥0.02**
- holdout drop: `−0.051` (сильнее, чем у sell и любой другой buy-цели; согласуется с картиной "сигнал затухает на новых годах" из Stage 4.6/4.7 и 5.0f)
- gate: `DIAGNOSTIC_ONLY`
- статус: **пограничный** — держится на одном seed (42), не подтверждённая цель. Нужен расширенный seed list (Альтернатива A) или проверка в Stage 5.4.

Дополнительно по целям:

- `breach_after_k2` ≡ `medium` (тождественные векторы меток для целочисленного `bars_to_breach`); 36 из 252 main-прогонов дубликаты.
- `no_breach` ≈ инверсия binary breach; AUC практически совпадает с binary baseline, новой информации не несёт.
- `breach_after_k4/k5` на buy — лучший профиль `time_only`, не структурный: структура (`back`) помогает только ранним пробоям, не поздним.

Control `survives_at_least_k` показывает высокие AUC/PR AUC, но не может быть winner-ом: censored rows становятся positive, поэтому модель может учить "не пробито", а не время жизни уровня.

## Методические ограничения

- `2021-2022` использованы для выбора winner-а.
- `2023-2025` только diagnostic disclosure.
- `2026` low-N disclosure.
- Нет независимой candidate validation.
- 12 уникальных main side/target comparisons коррелированы (`breach_after_k2` и `medium` тождественны); строгая поправка множественного тестирования не превращает результат в кандидата.
- Stage 5.3 не добавлял `price`, `price_coord_atr`, `price_atr_scaled`, raw `ATR`, Up/Dn.
- Oracle-time PF не использовался как gate.

## Правильное направление дальше

Разрешённый следующий шаг: Stage 5.4 price-coordinate / ATR ablation вокруг выбранной target family `fast`.

Минимальный scope Stage 5.4:

- держать target family фиксированной: `fast`
- не смешивать новый target search и feature search
- сравнить узко выбранные price/ATR варианты против текущих `clock_shift_back` и `clock_shift_back_impulse`
- сохранить `2023-2025` как diagnostic disclosure, не как подтверждение

## Неправильное направление дальше

- Объявлять Stage 5.3 торговым кандидатом.
- Использовать `survives_at_least_k` как winner.
- Добавлять Up/Dn по умолчанию.
- Делать широкий перебор новых целей и признаков одновременно.
- Использовать `2023-2025` как независимое подтверждение.
- Использовать oracle-time PF как trading gate.

## Ключевые файлы

Код:

- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`

Артефакты:

- `ML/reports/stage5_3_time_to_breach_target_reformulation.json`
- `ML/reports/stage5_2_time_to_breach_regression.json`

Документация:

- `docs/reports/2026-06-26-stage5_3-time-to-breach-target-reformulation.md`
- `docs/reports/2026-06-25-stage5_2-time-to-breach-regression.md`
- `docs/superpowers/plans/2026-06-26-stage5_3-time-to-breach-target-reformulation.md`

Wiki:

- `wiki/research/fractal-stop-research.md`
