# Context Handoff

Дата: 2026-06-25

## Текущий этап

Stage 5.1b завершён. Вердикт: **DIAGNOSTIC_ONLY**.

Ветка `H6_off05 stop broken` по-прежнему **не переоткрыта** как торговый или модельный кандидат. Stage 5.1b уточнил Stage 5.1: добавление `shift` в baseline не уничтожило сигнал `back`, а Up/Dn поля не дали достаточной добавки к полному структурному профилю.

## Что сделано

### Stage 5.1b (2026-06-25) — Up/Dn поля и baseline `clock + shift`

- Новый CLI: `--stage5-1b-updn-field-ablation`
- Зафиксированы:
  - 2 цели: `sell_stop_broken_H6_off05_flag`, `buy_stop_broken_H6_off05_flag`
  - 43 профиля: `clock_shift`, `structure_full`, `updn_full`, `structure_plus_updn`, `back_impulse_combo`, 19 `drop_*`, 19 `add_*`
  - 3 seed: `[42, 77, 123]`
- Stage 5.1b использует только XGBoost
- Baseline `clock_shift`:
  - `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`
  - token-level `log1p(shift)`
- Проверены:
  - 9 структурных полей: `direction`, `front`, `back`, `strong`, `break`, `reverse`, `power`, `count`, `impulse`
  - 10 Up/Dn полей: `up_3`, `dn_3`, `up_6`, `dn_6`, `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48`
- Split:
  - `train_core = 2004-2020`
  - `val_stop = 2021-2022`
  - `diagnostic_holdout = 2023-2025`
  - `low_n_disclosure = 2026`
- Выполнено `258` прогонов XGBoost
- Структурированный артефакт:
  - `ML/reports/stage5_1b_updn_field_ablation.json`
- Канонический отчёт:
  - `docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md`

Preflight:

- Up/Dn для структурных проверок читаются из raw-shadow `MT/MQL4/Files/Nero.csv`, а не из нормализованных `DATA/*_labeled.csv`
- `monotonicity.violations_total = 0` для sell и buy
- raw-shadow split выровнен с модельным split:
  - sell: `25672 / 2832 / 4211 / 316`
  - buy: `22745 / 2580 / 3832 / 293`
- Важно: модельные Up/Dn читаются из labeled CSV и уже нормализованы per-pair; raw-shadow preflight проверяет producer-контракт, а не шкалу модельного входа
- Delta CI для field verdicts не сохранены/не вычислены в итоговом JSON; verdicts опираются на seed counts/yearly signs

## Главный результат

1. `updn_full` даёт слабую добавку над `clock_shift`:
   - sell val AUC: `0.6317` vs `0.6259`, delta `+0.0048`
   - buy val AUC: `0.6401` vs `0.6333`, delta `+0.0059`
2. `structure_full` намного сильнее:
   - sell val AUC: `0.6720`, delta над `clock_shift` `+0.0460`
   - buy val AUC: `0.6898`, delta над `clock_shift` `+0.0561`
3. `structure_plus_updn` не улучшает `structure_full` на validation:
   - sell delta `-0.0017`
   - buy delta `-0.0021`
4. `back` сохранил `overall_likely_useful` даже после добавления `shift`:
   - sell: drop `-0.0171`, add `+0.0408`
   - buy: drop `-0.0186`, add `+0.0575`
5. `back_impulse_combo` почти догоняет `structure_full` на sell и превосходит его на buy, но это только диагностический контроль.
6. Единственный частный Up/Dn-сигнал: `dn_24` получил `target_likely_useful` только на sell; общий verdict = `target_specific_signal`.
7. `clock_shift` хуже Stage 5.1 `time_only` на обеих целях, поэтому add-one дельты нужно читать осторожно: baseline 5.1b оказался слабее, а не сильнее.

## Где мы сейчас

Состояние ветки:

- `H6_off05` остаётся `DIAGNOSTIC_ONLY`
- `2023-2025` нельзя трактовать как новый независимый frozen test
- Stage 5.1b не создаёт winner и не открывает trading rule
- Up/Dn не стоит включать в следующий стартовый профиль по умолчанию
- `dn_24` не считать сильным выводом: sell drop delta всего `-0.0030`, CI отсутствует

Правильное направление дальше:

- если нужен ещё один диагностический шаг по этой ветке, делать только узкий follow-up вокруг `back`/`impulse`
- если нужен честный подтверждающий ответ, брать новый независимый период `2026+`
- если цель проекта — production-кандидат, практичнее менять target/постановку, а не продолжать большой search по `H6_off05`

Неправильное направление дальше:

- объявлять `back` или `back+impulse` production-признаком
- включать весь `updn_full` в новый стартовый профиль без отдельной проверки
- использовать `2023-2025` как новое подтверждение
- запускать новый широкий перебор по `H6_off05`

## Ключевые файлы

Код:
- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`

Документация:
- `docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md`
- `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md`
- `docs/superpowers/specs/2026-06-24-stage5_1b-updn-fields-and-shift-baseline-design.md`

Артефакты:
- `ML/reports/stage5_1b_updn_field_ablation.json`
- `ML/reports/stage5_1_structural_field_ablation.json`
- `ML/reports/stage5_0f_signal_stationarity.json`

Wiki:
- `wiki/research/fractal-stop-research.md`

## Открытые вопросы

- Достаточно ли `back+impulse` близок к `structure_full`, чтобы проверять компактный профиль на новом независимом периоде.
- Нужно ли отдельно проверять `dn_24` как sell-only гипотезу, или это слишком слабый след после множественных сравнений.
- Стоит ли вообще продолжать ветку `H6_off05`, если для честного подтверждения всё равно нужен новый независимый период `2026+`.
