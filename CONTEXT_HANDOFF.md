# Context Handoff

Дата: 2026-06-24

## Текущий этап

Stage 5.1 завершён. Вердикт: **DIAGNOSTIC_ONLY**.

Ветка `H6_off05 stop broken` по-прежнему **не переоткрыта** как торговый или модельный кандидат. Stage 5.1 дал только один устойчивый диагностический сигнал: поле `back` выглядит наиболее полезным внутри структурного профиля.

## Что сделано

### Stage 5.1 (2026-06-24) — структурная абляция фрактальных полей

- Новый CLI: `--stage5-1-structural-field-ablation`
- Зафиксированы:
  - 2 цели: `sell_stop_broken_H6_off05_flag`, `buy_stop_broken_H6_off05_flag`
  - 20 профилей: `time_only`, `structure_full`, 9 `drop_*`, 9 `add_*`
  - 3 seed: `[42, 77, 123]`
- Stage 5.1 использует только XGBoost
- `time_only` содержит только:
  - `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`
- Полностью исключены:
  - `price`
  - `price_coord_atr`
  - `price_atr_scaled`
  - `ATR`
- Split:
  - `train_core <= 2020`
  - `val_stop = 2021-2022`
  - `diagnostic_holdout = 2023-2025`
  - `low_n_disclosure = 2026`
- Выполнено `120` прогонов XGBoost
- Структурированный артефакт:
  - `ML/reports/stage5_1_structural_field_ablation.json`
- Канонический отчёт:
  - `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md`

## Главный результат

Итог Stage 5.1:

1. `structure_full` заметно лучше `time_only` на обеих целях, значит структурная часть сигнала не сводится к одним clock-признакам.
2. Единственное поле с согласованным итогом на обеих целях: `back`.
3. `back` получил `likely_useful`:
   - sell: `drop_back` ухудшает val AUC на `-0.0100`, `add_back` улучшает val AUC на `+0.0213`
   - buy: `drop_back` ухудшает val AUC на `-0.0209`, `add_back` улучшает val AUC на `+0.0359`
4. Все остальные поля получили `mixed_or_unclear`.
5. Полей с итоговым `likely_noise` не найдено.

Ключевые числа:

- `structure_full` vs `time_only`:
  - sell val AUC: `0.6693` vs `0.6351`
  - sell holdout AUC: `0.6662` vs `0.6144`
  - buy val AUC: `0.6879` vs `0.6418`
  - buy holdout AUC: `0.6610` vs `0.6252`
- `elapsed_sec = 9185.3`
- `done_runs = total_runs = 120`

## Где мы сейчас

Состояние ветки:

- `H6_off05` остаётся `DIAGNOSTIC_ONLY`
- `2023-2025` нельзя трактовать как новый независимый frozen test
- Stage 5.1 не создаёт winner и не открывает trading rule

Правильное направление дальше:

- если нужен ещё один диагностический шаг по этой ветке, делать только **узкий follow-up вокруг `back`**
- если нужен честный подтверждающий ответ, брать новый независимый период `2026+`
- если цель проекта — production-кандидат, практичнее менять target/постановку, а не продолжать большой search по `H6_off05`

Неправильное направление дальше:

- объявлять `back` уже доказанным production-признаком
- выкидывать остальные структурные поля как будто они доказанно шумовые
- использовать `2023-2025` как новое подтверждение
- запускать новый широкий перебор по `H6_off05`

## Ключевые файлы

Код:
- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`

Документация:
- `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md`
- `docs/ML/benchmark_stage5_transformer_breach.py.md`
- `MODULE_INDEX.md`

Артефакты:
- `ML/reports/stage5_1_structural_field_ablation.json`
- `ML/reports/stage5_0f_signal_stationarity.json`

Wiki:
- `wiki/research/fractal-stop-research.md`

## Открытые вопросы

- Достаточно ли сильный след у `back`, чтобы тратить ещё один узкий диагностический цикл именно на него.
- Нужен ли отдельный follow-up по `impulse`, который выглядит интересным, но не прошёл порог согласованности.
- Стоит ли вообще продолжать ветку `H6_off05`, если для честного подтверждения всё равно нужен новый независимый период `2026+`.
