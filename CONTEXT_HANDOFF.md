# Context Handoff

Дата: 2026-06-25

## Текущий этап

Stage 5.2 завершён после bugfix и полного rerun. Вердикт: **DIAGNOSTIC_ONLY**.

Ветка `H6_off05` по-прежнему **не переоткрыта** как торговый или модельный кандидат. Stage 5.2 проверил альтернативную постановку: вместо бинарного `stop broken / not broken` предсказывать `bars_to_breach` — время до пробоя фрактального стопа.

Первый Stage 5.2 JSON был невалиден: `reg:pseudohubererror` схлопывал raw-прогнозы в константу вне диапазона, а clipping превращал их в `1.0`. Root cause исправлен: objective заменён на `reg:squarederror`, добавлен `pred_summary`, oracle-gate больше не принимает `oracle_binary_pf = inf` как валидное сравнение. После этого выполнен полный rerun `42/42`.

## Что сделано

### Stage 5.2 (2026-06-25) — Time-To-Breach Regression

- CLI: `--stage5-2-time-to-breach-regression`
- Основные цели:
  - `sell_bars_to_breach_H6_off05`
  - `buy_bars_to_breach_H6_off05`
- Контракт цели:
  - `bars_to_breach = 1..H` — первый бар пробоя
  - `bars_to_breach = H + 1` — пробоя не было в пределах горизонта
  - для основного `H=6`: censored value = `7`
- Objective после bugfix: `reg:squarederror`
- Профили:
  - `time_only`
  - `clock_shift`
  - `clock_shift_back`
  - `clock_shift_impulse`
  - `clock_shift_back_impulse`
  - `structure_full`
  - `structure_full_without_back`
- Seeds: `[42, 77, 123]`
- Выполнено `42/42` XGBoost-регрессии.
- Rerun: `workers=8`, `xgb_threads=4`, elapsed `2983.555s`.
- Structured artifact:
  - `ML/reports/stage5_2_time_to_breach_regression.json`
- Report:
  - `docs/reports/2026-06-25-stage5_2-time-to-breach-regression.md`

Split:

- `train_core = <=2020`
- `val_stop = 2021-2022`
- `diagnostic_holdout = 2023-2025`
- `low_n_disclosure = 2026`

`2023-2025` нельзя использовать как независимое подтверждение или для выбора winner-а.

## Главный результат

Gate summary:

- sell:
  - censoring gate: PASS, train censoring `0.6114`
  - oracle gate: FAIL, reason `invalid_oracle_binary_comparison`
  - model gate: FAIL
  - status: `ORACLE_FAILED`
- buy:
  - censoring gate: PASS, train censoring `0.6299`
  - oracle gate: FAIL, reason `invalid_oracle_binary_comparison`
  - model gate: FAIL
  - status: `ORACLE_FAILED`

Почему oracle gate FAIL:

- `oracle_time_pf`: sell `1.6520`, buy `1.7244`
- `oracle_binary_pf = inf`
- `pf_delta_vs_binary = None`
- binary-oracle входит там, где `breach_flag == 0`, поэтому SL по определению не происходит в пределах H=6; сравнение time-oracle vs binary-oracle невалидно.

Model results:

- Аномалия одинаковых метрик устранена: профили различаются, `pred_summary.std` ненулевой.
- Лучший sell: `clock_shift_back`
  - val Spearman `0.3072`
  - val AUC `0.7005`
  - val MAE `1.6942`
  - holdout Spearman `0.2942`
  - holdout AUC `0.6784`
- Лучший buy: `clock_shift_back_impulse`
  - val Spearman `0.3280`
  - val AUC `0.7071`
  - val MAE `1.6434`
  - holdout Spearman `0.2660`
  - holdout AUC `0.6613`
- Constant baseline по MAE всё ещё лучше:
  - sell: `1.4439` vs best model `1.6942`
  - buy: `1.4329` vs best model `1.6434`

Вывод: Stage 5.2 показывает содержательное ранжирование времени до пробоя, но обычная регрессия одного числа `bars_to_breach` не проходит candidate-gate из-за цензуры и MAE хуже constant baseline.

## Где мы сейчас

Состояние ветки:

- `H6_off05` остаётся `DIAGNOSTIC_ONLY`.
- Stage 5.2 не создаёт winner и не открывает trading rule.
- `back` снова главный компактный сигнал: `clock_shift_back` лучший на sell, `clock_shift_back_impulse` лучший на buy.
- Oracle-time PF нельзя использовать как торговое подтверждение из-за невалидного binary-oracle comparison и нереалистичной частоты сделок (`998-1103` trades/year).
- Обычная регрессия `bars_to_breach` не подходит как candidate formulation, несмотря на Spearman/AUC.

## Правильное направление дальше

- Не запускать широкий перебор по `H6_off05`.
- Если продолжать time-to-breach:
  - проверить дискретную постановку `fast / medium / no breach`;
  - проверить бинарные цели `survives_at_least_k` или `breach_after_k`;
  - использовать узкие профили `clock_shift_back`, `clock_shift_back_impulse`, `structure_full`, `structure_full_without_back`;
  - добавить sampled `y_pred`/`y_true` в JSON для калибровки.
- Исправить дизайн oracle-preflight:
  - binary-oracle comparison в текущем виде неинформативен;
  - нужен другой baseline oracle или другой торговый sanity-check.
- Для статуса выше `DIAGNOSTIC_ONLY` нужен новый независимый период `2026+`.

## Неправильное направление дальше

- Объявлять Stage 5.2 кандидатом.
- Использовать oracle-time PF как торговый результат.
- Использовать `2023-2025` как новое подтверждение.
- Запускать новый широкий перебор по `H6_off05` на тех же годах.
- Оптимизировать обычную MAE-регрессию `bars_to_breach` без учёта цензуры.

## Ключевые файлы

Код:

- `processing/label_signals.py`
- `processing/label_main.py`
- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/processing/test_fractal_stop_breach_labels.py`
- `tests/test_stage5_transformer_breach.py`

Документация:

- `docs/reports/2026-06-25-stage5_2-time-to-breach-regression.md`
- `docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md`
- `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md`
- `docs/superpowers/specs/2026-06-25-stage5_2-time-to-breach-regression-design.md`
- `docs/superpowers/plans/2026-06-25-stage5_2-time-to-breach-regression.md`

Артефакты:

- `ML/reports/stage5_2_time_to_breach_regression.json`
- `ML/reports/stage5_1b_updn_field_ablation.json`
- `ML/reports/stage5_1_structural_field_ablation.json`

Wiki:

- `wiki/research/fractal-stop-research.md`

## Открытые вопросы

- Какая дискретизация time-to-breach лучше: `fast / medium / no breach` или набор `survives_at_least_k`.
- Можно ли использовать `back` как компактный признак для time-to-breach без полного structural profile.
- Какой oracle/sanity-check корректно сравнивает time-to-breach с binary breach, если binary-oracle по построению имеет бесконечный PF.
- Нужен ли отдельный новый период `2026+` для проверки `back`/time-to-breach после всех диагностических итераций.
