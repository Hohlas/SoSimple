# Stage 5.2 Time-To-Breach Regression

> **Дата**: 2026-06-25
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Проверить, можно ли заменить бинарную цель `stop broken / not broken` на регрессию времени до пробоя фрактального стопа.
> **Related plan/spec**: `docs/superpowers/specs/2026-06-25-stage5_2-time-to-breach-regression-design.md`, `docs/superpowers/plans/2026-06-25-stage5_2-time-to-breach-regression.md`

## Context

Stage 5.1 и Stage 5.1b показали, что в структурных фрактальных полях есть диагностический след, особенно в поле `back`, но ветка `H6_off05 stop broken` не была переоткрыта как кандидат. Stage 5.2 проверял другую постановку: не просто "будет пробой или нет", а "через сколько баров будет пробой".

Основная идея: если модель умеет ранжировать фракталы по времени до пробоя, это может быть полезнее бинарного ответа. Короткое время до пробоя означает плохой уровень для стопа; длинное время или отсутствие пробоя за горизонт означает потенциально более безопасный уровень.

Уровень этапа: поисковый. Результат не может стать торговым кандидатом без нового независимого проверочного цикла.

## What Was Done

Добавлена разметка `bars_to_breach`: первое касание уровня стопа в пределах горизонта или значение `H + 1`, если пробоя не было. Для основной проверки использованы цели:

- `sell_bars_to_breach_H6_off05`
- `buy_bars_to_breach_H6_off05`

Добавлен Stage 5.2 runner для XGBoost-регрессии:

- 7 профилей: `time_only`, `clock_shift`, `clock_shift_back`, `clock_shift_impulse`, `clock_shift_back_impulse`, `structure_full`, `structure_full_without_back`
- 2 цели: sell и buy
- 3 seed: `42`, `77`, `123`
- всего `42` model-run

Также добавлены:

- constant baseline: всегда предсказывает censored value `7`
- oracle-preflight через first-touch simulator
- censoring gate
- model gate по Spearman, MAE, AUC, годовой согласованности и приростам над baseline
- structured JSON: `ML/reports/stage5_2_time_to_breach_regression.json`

## Multiple Testing Context

Search budget: `7 профилей × 2 цели × 3 seed = 42` XGBoost-регрессии плюс constant baseline и oracle-preflight.

Коррекция множественного тестирования не применялась. Это допустимо только потому, что этап остаётся `DIAGNOSTIC_ONLY`: результаты нельзя использовать как подтверждение кандидата или как основание для торгового правила.

Выбор winner-а по `2023-2025` запрещён и не выполнялся. `2023-2025` используются только как diagnostic holdout disclosure.

## Changed Files

Код и тесты из коммита `7d77a1f`:

- `processing/label_signals.py` — добавлены `BR_TIME_TO_BREACH_COLUMNS` и расчёт первого бара пробоя.
- `processing/label_main.py` — добавлен heartbeat для долгой разметки.
- `ML/baseline/benchmark_stage5_transformer_breach.py` — добавлен Stage 5.2 pipeline, метрики, gate, oracle-preflight, CLI.
- `tests/processing/test_fractal_stop_breach_labels.py` — тесты контракта новой разметки.
- `tests/test_stage5_transformer_breach.py` — тесты профилей, метрик, gate, runner и CLI.
- `ML/reports/stage5_2_time_to_breach_regression.json` — structured artifact полного прогона.

## Verification

Команды проверки:

```bash
./.venv/bin/python -m pytest tests/processing/test_fractal_stop_breach_labels.py tests/test_stage5_transformer_breach.py -q
```

Результат:

```text
180 passed in 114.99s
```

Дополнительная проверка JSON:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("ML/reports/stage5_2_time_to_breach_regression.json")
d = json.loads(p.read_text())
assert d["status"] == "DIAGNOSTIC_ONLY"
assert d["progress"]["done_runs"] == d["progress"]["total_runs"] == 42
for target in d["targets"]:
    gate = d["gate_results"][target]
    assert gate["censoring_gate"]["pass"] is True
    assert gate["oracle_gate"]["pass"] is True
    assert gate["model_gate"]["pass"] is False
print("json_consistency_ok")
PY
```

Результат:

```text
json_consistency_ok
```

## Results

Итоговый статус JSON: `DIAGNOSTIC_ONLY`.

Прогон завершён полностью: `42 / 42`.

### Gate Summary

| Target | Censoring gate | Oracle gate | Model gate | Overall |
|---|---:|---:|---:|---|
| `sell_bars_to_breach_H6_off05` | PASS | PASS | FAIL | `MODEL_GATE_FAILED` |
| `buy_bars_to_breach_H6_off05` | PASS | PASS | FAIL | `MODEL_GATE_FAILED` |

### Censoring

Доля непробитых уровней в train ниже блокирующего порога `0.70`, поэтому censoring сам по себе не объясняет провал:

| Target | train censoring | val censoring | holdout censoring |
|---|---:|---:|---:|
| sell | `0.6114` | `0.6194` | `0.5923` |
| buy | `0.6299` | `0.6260` | `0.6441` |

### Oracle Preflight

Oracle формально проходит gate: если знать истинное время до пробоя, торговая логика имеет положительный PF. Но этот gate оказался слабее, чем предполагалось в дизайне.

| Target | oracle_time_pf | oracle_binary_pf | pf_delta_vs_binary | trades | trades/year | yearly PF |
|---|---:|---:|---:|---:|---:|---|
| sell | `1.6520` | `inf` | `None` | `2206` | `1103.0` | 2021 `1.6352`, 2022 `1.6682` |
| buy | `1.7244` | `inf` | `None` | `1997` | `998.5` | 2021 `1.6734`, 2022 `1.7723` |

Критическая оговорка: `oracle_binary_pf = inf`, потому что binary-oracle входит на строках, где `breach_flag == 0`. При таком выборе стоп по определению не пробивается внутри горизонта `H=6`, поэтому SL-исходов нет, а PF становится бесконечным. Из-за этого сравнение `oracle_time_pf` против `oracle_binary_pf` бессмысленно, `pf_delta_vs_binary = None`, а условие gate `(pf_delta is None or pf_delta >= 0.2)` проходит по умолчанию.

Следствие: oracle-preflight показывает только то, что знание будущего времени/факта пробоя создаёт высокий диагностический потолок. Он не доказывает, что именно регрессия времени до пробоя лучше бинарного знания `breach / no breach`.

Дополнительная оговорка: частота `998-1103` сделок в год слишком высокая для торгового потолка. Oracle входит примерно на большинстве безопасных строк, где стоп не пробивается быстро. Поэтому PF oracle-time завышен частотой входов и не должен трактоваться как реалистичный торговый результат.

### Model Results

Все профили дали идентичные итоговые метрики. Это аномалия, а не нормальный исследовательский результат.

| Target | Profile | val Spearman | val MAE | val AUC `true>=4` | holdout Spearman | holdout MAE | holdout AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| sell | `time_only` | `0.0000` | `4.5561` | `0.5000` | `0.0000` | `4.4526` | `0.5000` |
| sell | `clock_shift` | `0.0000` | `4.5561` | `0.5000` | `0.0000` | `4.4526` | `0.5000` |
| sell | `clock_shift_back` | `0.0000` | `4.5561` | `0.5000` | `0.0000` | `4.4526` | `0.5000` |
| sell | `clock_shift_impulse` | `0.0000` | `4.5561` | `0.5000` | `0.0000` | `4.4526` | `0.5000` |
| sell | `clock_shift_back_impulse` | `0.0000` | `4.5561` | `0.5000` | `0.0000` | `4.4526` | `0.5000` |
| sell | `structure_full` | `0.0000` | `4.5561` | `0.5000` | `0.0000` | `4.4526` | `0.5000` |
| sell | `structure_full_without_back` | `0.0000` | `4.5561` | `0.5000` | `0.0000` | `4.4526` | `0.5000` |
| buy | `time_only` | `0.0000` | `4.5671` | `0.5000` | `0.0000` | `4.5911` | `0.5000` |
| buy | `clock_shift` | `0.0000` | `4.5671` | `0.5000` | `0.0000` | `4.5911` | `0.5000` |
| buy | `clock_shift_back` | `0.0000` | `4.5671` | `0.5000` | `0.0000` | `4.5911` | `0.5000` |
| buy | `clock_shift_impulse` | `0.0000` | `4.5671` | `0.5000` | `0.0000` | `4.5911` | `0.5000` |
| buy | `clock_shift_back_impulse` | `0.0000` | `4.5671` | `0.5000` | `0.0000` | `4.5911` | `0.5000` |
| buy | `structure_full` | `0.0000` | `4.5671` | `0.5000` | `0.0000` | `4.5911` | `0.5000` |
| buy | `structure_full_without_back` | `0.0000` | `4.5671` | `0.5000` | `0.0000` | `4.5911` | `0.5000` |

`time_only` выбран только из-за tie-break: все 7 профилей имеют одинаковые медианные метрики. Это не означает, что `time_only` лучший по смыслу.

После сверки отчёта с кодом конкретная гипотеза "time-признаки нулевые, потому что `build_stage5_2_features()` не использует `build_row_features()`" не подтвердилась: текущий код вызывает `build_row_features(df, profile)`, а smoke-check на реальных строках строит разные feature matrices для `time_only`, `clock_shift`, `clock_shift_back` и `structure_full`. Но идентичные метрики от 4-признакового и 904-признакового профиля всё равно являются красным флагом. Итог Stage 5.2 нельзя трактовать как надёжный отрицательный исследовательский вывод до post-mortem модельного контура.

Constant baseline оказался намного лучше по MAE:

| Target | constant MAE | best model MAE | model MAE improvement |
|---|---:|---:|---:|
| sell | `1.4439` | `4.5561` | `-215.6%` |
| buy | `1.4329` | `4.5671` | `-218.7%` |

Практический смысл: модель не просто "слабая"; она хуже простой стратегии "всегда считать, что пробоя не будет за 6 баров".

Почему constant baseline силён: на validation примерно 62% строк имеют `target = 7`, то есть стоп не пробит за 6 баров. Постоянный прогноз `7` получает нулевую ошибку на этих строках. Модельная MAE около `4.56` совместима со схлопыванием предсказаний в почти постоянное низкое значение, которое сильно ошибается на большинстве censored-строк. Но сами массивы предсказаний в JSON не сохранены, поэтому это пока гипотеза, а не доказанный факт.

## Conclusions

Основной вывод после сверки с JSON: Stage 5.2 не переоткрывает ветку `H6_off05`, но отрицательный модельный результат нельзя считать надёжным доказательством слабости самой идеи. Идентичные метрики всех 7 профилей указывают на вероятную ошибку реализации, схлопывание предсказаний или неподходящий model/target contract.

Oracle-preflight при этом не является полноценным подтверждением идеи времени до пробоя: binary-oracle имеет бесконечный PF по построению, а `trades/year` слишком велик. Oracle показывает только диагностический потолок при знании будущего, а не реалистичную торгуемую механику.

Корректный вывод: текущий артефакт Stage 5.2 имеет статус `DIAGNOSTIC_ONLY` и требует технического post-mortem. До перезапуска с сохранением предсказаний и проверками feature/model contract нельзя делать вывод "регрессия времени до пробоя не работает".

## Limitations / Open Questions

- Все model gate checks провалены на обеих целях.
- Все профили дали одинаковые итоговые метрики; это вероятный признак проблемы в реализации или схлопывания предсказаний, а не нормальный исследовательский результат.
- В текущем JSON не сохранены массивы `y_pred`/`y_true`. Поэтому post-mortem распределений невозможен без перезапуска Stage 5.2 или отдельного диагностического job.
- Конкретная гипотеза про нулевые time-признаки не подтверждена текущим кодом: `build_stage5_2_features()` использует `build_row_features()`. Но этого недостаточно, чтобы снять подозрение с модельного контура.
- Oracle gate логически слабый: `oracle_binary_pf = inf`, `pf_delta_vs_binary = None`, и сравнение time-oracle против binary-oracle не работает.
- `trades_per_year` oracle (`998-1103`) нереалистично велик для торгового потолка и завышает интерпретацию oracle PF.
- `bars_to_breach = 7` означает "не пробит за 6 баров", а не фактический пробой на 7-м баре. Обычная регрессия плохо учитывает такую цензуру.
- `2023-2025` не является независимым frozen test, потому что эта ветка уже многократно использовала эти годы для диагностики.
- Scale contract: Stage 5.2 использует уже нормализованные `DATA/*_labeled.csv`; отдельного scaler внутри Stage 5.2 нет. Фрактальные поля наследуют rowwise normalization из preprocessing. Нового A7 feature distribution audit для Stage 5.2 не проводилось, потому что результат не проходит model gate и не становится кандидатом.
- Up/Dn поля намеренно не включались в стартовые профили Stage 5.2 по итогам Stage 5.1b.

## Validation Split Disclosure

Split соответствует Stage 5.x fixed protocol:

- `train_core`: до `2020`
- `val_stop`: `2021-2022`
- `diagnostic_holdout`: `2023-2025`
- `low_n_disclosure`: `2026`

`val_stop` использовался для model gate и выбора лучшего профиля. `diagnostic_holdout` раскрыт только для диагностики и не использовался для выбора параметров, winner-а или статуса кандидата. Поэтому результат не является frozen-candidate validation.

## Next Step

Не запускать новый широкий перебор по `H6_off05` в этой же постановке.

Допустимые следующие шаги:

- Сначала провести post-mortem Stage 5.2 с перезапуском: сохранить распределения `y_pred`/`y_true` по профилям и seed, проверить, действительно ли модель выдаёт почти константу.
- Добавить feature/model contract checks: shape, `nonzero`, variance, отличие матриц между профилями, variance предсказаний и сравнение с dummy regressor.
- Исправить oracle gate: не считать `pf_delta_vs_binary = None` автоматическим pass и явно обрабатывать случай `oracle_binary_pf = inf`.
- Если продолжать идею времени до пробоя, заменить обычную регрессию на постановку, которая учитывает цензуру: например, предсказывать вероятность `breach_after_k` для нескольких порогов `k`, а не одно число `bars_to_breach`.
- Проверять только узкий набор профилей вокруг `back`/`impulse`; широкий feature search по старому `H6_off05` не оправдан.
- Для статуса выше `DIAGNOSTIC_ONLY` нужен новый независимый период, например полноценный `2026+`, не использованный для выбора.

Запрещено делать дальше:

- Объявлять Stage 5.2 кандидатом.
- Использовать `time_only` как winner: он выбран только из-за равенства нулевых метрик.
- Использовать `2023-2025` как подтверждение.
- Делать торговое правило из oracle-результата: oracle использует недоступное в момент сделки знание.

## Related Materials

- `ML/reports/stage5_2_time_to_breach_regression.json`
- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `processing/label_signals.py`
- `tests/test_stage5_transformer_breach.py`
- `tests/processing/test_fractal_stop_breach_labels.py`
- `docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md`
- `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md`
