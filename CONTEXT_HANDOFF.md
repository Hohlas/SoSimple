# Context Handoff

Дата: 2026-06-25

## Текущий этап

Stage 5.2 завершён. Вердикт: **DIAGNOSTIC_ONLY**.

Ветка `H6_off05` по-прежнему **не переоткрыта** как торговый или модельный кандидат. Stage 5.2 проверил альтернативную постановку: вместо бинарного `stop broken / not broken` предсказывать `bars_to_breach` — время до пробоя фрактального стопа.

Главный итог после debug: Stage 5.2 старый JSON нельзя считать надёжным отрицательным исследовательским выводом. Root cause найден: `reg:pseudohubererror` выдавал почти константный raw-прогноз вне допустимого диапазона (`-171.076` на полном `time_only` split), а clipping превращал все предсказания в `1.0`. Код исправлен на `reg:squarederror`; нужен полный rerun Stage 5.2.

## Что сделано

### Stage 5.2 (2026-06-25) — Time-To-Breach Regression

- Новый CLI: `--stage5-2-time-to-breach-regression`
- Новая разметка Fractal Stop Breach:
  - `BR_TIME_TO_BREACH_COLUMNS`
  - `sell_bars_to_breach_H6_off05`
  - `buy_bars_to_breach_H6_off05`
- Контракт цели:
  - `bars_to_breach = 1..H` — первый бар пробоя
  - `bars_to_breach = H + 1` — пробоя не было в пределах горизонта
  - для основного `H=6`: censored value = `7`
- Профили:
  - `time_only`
  - `clock_shift`
  - `clock_shift_back`
  - `clock_shift_impulse`
  - `clock_shift_back_impulse`
  - `structure_full`
  - `structure_full_without_back`
- Цели:
  - `sell_bars_to_breach_H6_off05`
  - `buy_bars_to_breach_H6_off05`
- Seeds: `[42, 77, 123]`
- Выполнено `42/42` XGBoost-регрессии.
- Структурированный артефакт:
  - `ML/reports/stage5_2_time_to_breach_regression.json`
  - статус: **устаревший диагностический артефакт после bugfix objective**
- Канонический отчёт:
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
  - oracle gate: формально PASS, `oracle_time_pf = 1.6520`
  - caveat: `oracle_binary_pf = inf`, поэтому сравнение time-oracle vs binary-oracle невалидно
  - model gate: FAIL
  - status: `MODEL_GATE_FAILED`
- buy:
  - censoring gate: PASS, train censoring `0.6299`
  - oracle gate: формально PASS, `oracle_time_pf = 1.7244`
  - caveat: `oracle_binary_pf = inf`, поэтому сравнение time-oracle vs binary-oracle невалидно
  - model gate: FAIL
  - status: `MODEL_GATE_FAILED`

Model results:

- Все 7 профилей дали идентичные медианные метрики.
- Root cause найден: `reg:pseudohubererror` схлопнул raw-прогнозы, clipping замаскировал это.
- `time_only` выбран только из-за tie-break, это не содержательный winner.
- sell validation:
  - Spearman `0.0000`
  - MAE `4.5561`
  - AUC `0.5000`
- buy validation:
  - Spearman `0.0000`
  - MAE `4.5671`
  - AUC `0.5000`
- constant baseline лучше по MAE:
  - sell: `1.4439` vs model `4.5561`
  - buy: `1.4329` vs model `4.5671`

Важно: массивы `y_pred`/`y_true` в старом JSON не сохранены. Новый код добавляет `pred_summary` в метрики; для полного анализа всё равно желательно сохранять sampled `y_pred`/`y_true`.

## Где мы сейчас

Состояние ветки:

- `H6_off05` остаётся `DIAGNOSTIC_ONLY`.
- Stage 5.2 не создаёт winner и не открывает trading rule.
- Oracle-положительный результат не является торговым результатом: oracle использует недоступное в момент сделки знание, а binary-oracle имеет бесконечный PF по построению.
- Обычная регрессия `bars_to_breach` ещё не оценена честно после bugfix; старый результат superseded.

Практический смысл:

- Идея "время до пробоя может быть полезно" не закрыта.
- Текущий старый результат Stage 5.2 ненадёжен из-за найденного bug root cause.
- Если продолжать, следующий шаг — полный rerun Stage 5.2 на `reg:squarederror`.

## Правильное направление дальше

- Перезапустить Stage 5.2 полностью:
  - objective уже исправлен на `reg:squarederror`;
  - новый JSON должен содержать `pred_summary`;
  - желательно сохранить sampled `y_pred`/`y_true` по profile/seed/target;
  - сравнить распределение `y_true` и `y_pred` по годам.
- Добавить проверки:
  - shape и variance feature matrices по профилям;
  - отличие матриц между `time_only`, `clock_shift`, `clock_shift_back`, `structure_full`;
  - variance предсказаний;
  - сравнение с dummy regressor.
- Исправить oracle gate:
  - `pf_delta_vs_binary = None` не должен автоматически проходить;
  - `oracle_binary_pf = inf` должен помечать comparison как invalid.
- Если продолжать идею времени до пробоя, перейти от обычной регрессии к постановке с учётом цензуры:
  - несколько бинарных целей `breach_after_k`;
  - survival-style formulation;
  - ordinal buckets `fast / medium / no breach`.
- Ограничить дальнейшие признаки узким набором вокруг `back`/`impulse`.
- Для статуса выше `DIAGNOSTIC_ONLY` нужен новый независимый период `2026+`.

## Неправильное направление дальше

- Объявлять Stage 5.2 кандидатом.
- Использовать `time_only` как winner.
- Делать торговое правило из oracle-preflight.
- Запускать новый широкий перебор по `H6_off05` на тех же годах.
- Использовать `2023-2025` как новое подтверждение.

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

- Почему все Stage 5.2 профили дали одинаковые итоговые метрики.
- Схлопывается ли XGBoost в почти постоянное предсказание, или проблема в метриках/цели.
- Подходит ли `bars_to_breach` как одно регрессионное число, если большая часть наблюдений цензурирована.
- Стоит ли проверять ordinal/survival-постановку, или ветку `H6_off05` нужно окончательно оставить до появления независимого `2026+`.
