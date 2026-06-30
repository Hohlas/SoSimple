# Regression Up/Dn Target Foundation

> **Дата**: 2026-06-30
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Проверить, дают ли top-level `up_*/dn_*` чистую основу для регрессионной постановки без привязки к breach- или TP/SL-таргетам.
> **Related plan/spec**: [Stage Plan](../superpowers/plans/2026-06-30-regression-updn-target-foundation.md)

## Context

После Stage 6.3 следующим зафиксированным шагом была проверка, можно ли отделить задачу от торгового контракта и сначала ответить на более узкий вопрос: предсказываются ли сами будущие величины favorable/adverse movement (`up_h`, `dn_h`) достаточно хорошо, чтобы на них потом строить отдельную торговую формулировку.

Этап заранее ограничен статусом `DIAGNOSTIC_ONLY`. Он не выбирает торговое правило, не подбирает threshold и не использует `diagnostic_holdout` (`2023-2025`) или `low_n_disclosure` (`2026`) для выбора horizon/profile/model.

Уровень этапа: **поисковый**.

## What Was Done

Добавлен новый runner `ML/baseline/benchmark_regression_updn_target_foundation.py` и тесты `tests/test_regression_updn_target_foundation.py`.

Runner:

- читает XAUUSD labeled splits;
- трактует top-level `up_3/dn_3 ... up_48/dn_48` как labels only;
- использует allowlist-based feature contract и сохраняет `feature_source_contract` в JSON;
- сравнивает 5 профилей:
  - `clock_only`
  - `clock_shift`
  - `clock_shift_back`
  - `clock_shift_back_impulse`
  - `structure_full`
- сравнивает 5 baseline/model families:
  - `constant_median`
  - `ridge`
  - `decision_tree_depth3`
  - `random_forest_depth4`
  - `xgboost_depth3`
- считает метрики по всем 10 таргетам, edge-диагностику, block bootstrap и calendar-share disclosure;
- пишет checkpoint JSON после preflight и после каждого run.

## Multiple Testing Context

Search budget фиксирован и ограничен:

- 5 feature profiles
- 5 model families
- 5 horizons для анализа (`3/6/12/24/48`)
- 3 seeds
- всего обучений/оценок: `5 × 5 × 3 = 75` run-ов

Коррекция множественного тестирования не применялась. Поэтому даже при прохождении внутреннего research gate артефакт остаётся только `DIAGNOSTIC_ONLY`.

## Changed Files

- `ML/baseline/benchmark_regression_updn_target_foundation.py`
- `tests/test_regression_updn_target_foundation.py`
- `ML/reports/regression_updn_target_foundation.json`
- `docs/reports/2026-06-30-regression-updn-target-foundation.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Verification

Команды:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_target_foundation.py -q
./.venv/bin/python -m pytest tests/test_label_updn.py tests/test_regression_updn_target_foundation.py -q
./.venv/bin/python statistics/data_contract_smoke_check.py \
  --train DATA/Nero_XAUUSD_train_labeled.csv \
  --val DATA/Nero_XAUUSD_validation_labeled.csv \
  --test DATA/Nero_XAUUSD_test_labeled.csv
./.venv/bin/python ML/baseline/benchmark_regression_updn_target_foundation.py \
  --regression-updn-target-foundation --no-resume
```

Наблюдения:

- `tests/test_regression_updn_target_foundation.py`: `22 passed`
- `tests/test_label_updn.py tests/test_regression_updn_target_foundation.py`: `29 passed`
- полный benchmark завершён: `75/75`, `elapsed_sec=4074.6` (~67.9 мин)
- итоговый JSON:
  - `experiment = regression_updn_target_foundation`
  - `selected_profile = structure_full`
  - `selected_horizon = 3`
  - `research_gate_status = TARGET_FOUNDATION_PASSED`
  - `artifact_status = DIAGNOSTIC_ONLY`

Важно:

- `statistics/data_contract_smoke_check.py` на текущих XAUUSD split-файлах завершился с `FAIL` не по новому runner-у, а по историческому ожиданию колонки `target_buy_H6_val`, которой в текущих CSV нет. Это не ломает новый Up/Dn runner напрямую, но остаётся несинхронизированным data-contract риском общего smoke-check инструмента.

## Results

### Target Contract Summary

| Split | Rows | Targets present | Contract |
|---|---:|---:|---|
| `train_core` | 44159 | 10/10 | PASS |
| `val_stop` | 5205 | 10/10 | PASS |
| `diagnostic_holdout` | 8091 | 10/10 | PASS |
| `low_n_disclosure` | 1162 | 10/10 | PASS |

Top-level `up_*/dn_*` использовались только как labels. Во feature names они не попадали.

### Main Horizon/Profile Selection

Лучший по заранее неиспользующему holdout summary-score оказался:

- `selected_profile = structure_full`
- `selected_horizon = 3`

Параметры выбранной точки на `val_stop`:

| Metric | `up_3` | `dn_3` | `edge_3` |
|---|---:|---:|---:|
| normalized MAE improvement vs constant | 0.4716 | 0.4780 | — |
| Spearman rho | 0.7648 | 0.7736 | 0.8017 |
| bootstrap p05 | 0.4614 | 0.4651 | 0.7880 |

Seed stability for selected profile/horizon:

| Profile | Horizon | Seeds passing gate |
|---|---:|---:|
| `structure_full` | 3 | 3 / 3 |

Calendar dependence disclosure:

- `structure_full` calendar share: `0.0322`, `0.0335`, `0.0363` by seed
- warning threshold `> 0.30` not reached

### `val_stop` Profile Summary

Below are XGBoost medians on `val_stop`.

| Profile | Horizon | up improvement | dn improvement | up Spearman | dn Spearman | edge Spearman |
|---|---:|---:|---:|---:|---:|---:|
| `clock_only` | 6 | 0.0010 | 0.0056 | 0.1907 | 0.2048 | 0.0202 |
| `clock_shift` | 6 | 0.0010 | 0.0058 | 0.1906 | 0.2043 | 0.0185 |
| `clock_shift_back` | 6 | 0.0387 | 0.0266 | 0.2236 | 0.2121 | 0.0100 |
| `clock_shift_back_impulse` | 6 | 0.0391 | 0.0268 | 0.2244 | 0.2128 | 0.0326 |
| `structure_full` | 3 | 0.4716 | 0.4780 | 0.7648 | 0.7736 | 0.8017 |

Дополнительно по legacy reference `H12`:

| Profile | up_12 improvement | dn_12 improvement | up_12 Spearman | dn_12 Spearman | edge_12 Spearman |
|---|---:|---:|---:|---:|---:|
| `clock_shift_back` | -0.0076 | 0.0062 | 0.1776 | 0.1793 | -0.0005 |
| `clock_shift_back_impulse` | 0.0064 | 0.0065 | 0.1949 | 0.1889 | 0.0498 |
| `structure_full` | 0.1398 | 0.1776 | 0.5840 | 0.5675 | 0.5552 |

### Baseline Ladder: selected profile `structure_full`

`val_stop`, horizon `3`, medians over seeds:

| Model | up_3 improvement | dn_3 improvement | up_3 Spearman | dn_3 Spearman | edge_3 Spearman |
|---|---:|---:|---:|---:|---:|
| `ridge` | 0.1976 | 0.2033 | 0.6863 | 0.6783 | 0.6764 |
| `decision_tree_depth3` | 0.4711 | 0.4617 | 0.7568 | 0.7450 | 0.7667 |
| `random_forest_depth4` | 0.4870 | 0.4866 | 0.7751 | 0.7733 | 0.7810 |
| `xgboost_depth3` | 0.4716 | 0.4780 | 0.7648 | 0.7736 | 0.8017 |

Вывод по baseline ladder:

- сигнал не требует XGBoost как единственного носителя: он уже силён на `Ridge`, а затем резко усиливается на простом дереве и `RandomForest`;
- это хороший знак для target foundation, потому что сигнал не выглядит как артефакт только одной сложной модели.

### Disclosure-only Horizons

`structure_full` показывает монотонное ослабление по мере роста горизонта:

| Horizon | up improvement | dn improvement | up Spearman | dn Spearman | edge Spearman |
|---|---:|---:|---:|---:|---:|
| 3 | 0.4716 | 0.4780 | 0.7648 | 0.7736 | 0.8017 |
| 6 | 0.2860 | 0.3056 | 0.6804 | 0.6736 | 0.6805 |
| 12 | 0.1398 | 0.1776 | 0.5840 | 0.5675 | 0.5552 |
| 24 | 0.0239 | 0.0685 | 0.4205 | 0.4167 | 0.4323 |
| 48 | -0.0515 | 0.0303 | 0.3108 | 0.3289 | 0.3422 |

Практический смысл:

- target family не одинаково сильна на всех горизонтах;
- strongest foundation signal находится на коротких горизонтах `3` и `6`;
- `H12` остаётся рабочим только у `structure_full`, но уже заметно слабее коротких горизонтов;
- `H24/H48` на текущих профилях слишком слабы, чтобы считать их хорошей основой без нового цикла.

### Holdout / 2026 Disclosure

`diagnostic_holdout` и `low_n_disclosure` не использовались для выбора profile/horizon/model.

Из этого этапа зафиксировано только disclosure-правило:

- короткие горизонты выглядят сильнее длинных и вне `val_stop`;
- но эти данные не использовались для принятия research gate решения.

## Conclusions

1. **Top-level `up_*/dn_*` contract технически годен.** Все 10 таргетов присутствуют во всех split-секциях и изолированы от input contract.

2. **Foundation signal подтверждён, но не для всей семьи горизонтов одинаково.** На текущем bounded search лучшая точка — `structure_full` на `H3`; `H6` тоже силён; дальше качество снижается.

3. **Legacy H12 не является главным победителем.** Он остаётся рабочим только в `structure_full`, но по силе уступает `H3/H6`. Это важный отрицательный вывод против инерционного возврата к старому `up_12/dn_12` как “естественному” центру постановки.

4. **Сигнал не сводится к одной сложной модели.** Даже `Ridge` уже показывает сильную связь на `structure_full`, а дерево/лес ещё усиливают её. Это делает найденный target foundation более правдоподобным.

5. **Статус артефакта остаётся `DIAGNOSTIC_ONLY`.** Множественное тестирование не закрыто, trading rule не выбран, holdout не был частью gate, а общий project-level smoke-check сейчас несинхронизирован с фактической схемой XAUUSD CSV.

## Limitations / Open Questions

1. `smoke_check` для XAUUSD currently expects columns вроде `target_buy_H6_val`; это отдельный data-contract debt и его нужно чинить до более сильных заявлений о качестве всего research pipeline.

2. Runner сейчас действительно хранит `feature_source_contract`, но его heartbeat/logging слабее, чем в Stage 6.x. Для долгих прогонов стоит добавить явный progress `done/total`, ETA и per-run stdout.

3. `selected_horizon = 3` не означает, что именно H3 надо сразу превращать в торговую систему. Это только strongest target foundation point на текущем ограниченном наборе профилей.

4. `low_n_disclosure=2026` остаётся малой по объёму секцией (`1162` rows) и не подходит для выбора.

5. Single-instrument / single-timeframe: XAUUSD H1 only.

## Validation Split Disclosure

- `train_core`: `<= 2020`
- `val_stop`: `2021-2022`
- `diagnostic_holdout`: `2023-2025`
- `low_n_disclosure`: `2026`

Использование split-ролей:

- model fitting / scaler fit / bootstrap gate: `train_core` + `val_stop`
- horizon/profile/model selection: только `val_stop`
- `diagnostic_holdout` и `low_n_disclosure`: disclosure-only

Отдельных `val-select` и `val-eval` здесь нет, поэтому этап по определению не выше `DIAGNOSTIC_ONLY`.

## Next Step

Следующий допустимый шаг: новый узкий цикл поверх `structure_full`, где заранее заморозить:

- один короткий horizon candidate (`H3` или `H6`);
- отдельное сравнение с `H12` только как legacy reference;
- правило перехода от `up_h/dn_h` к торговому решению;
- отдельный confirmatory gate без расширения feature search.

Что не делать дальше:

- не возвращаться к широкому перебору horizon/ATR/TP/SL;
- не выбирать horizon/profile по `diagnostic_holdout` или `2026`;
- не объявлять `H3` торговым winner только потому, что он лучший в этом target-foundation run.

## Related Materials

- [JSON artifact](../../ML/reports/regression_updn_target_foundation.json)
- [Runner](../../ML/baseline/benchmark_regression_updn_target_foundation.py)
- [Tests](../../tests/test_regression_updn_target_foundation.py)
- [Stage 6.3 report](2026-06-30-stage6_3-h6-feature-parity-check.md)
- [Stage 6.2 post-mortem](2026-06-30-stage6_2-range-w1-postmortem.md)
- [Stage 5.1b Up/Dn ablation](2026-06-25-stage5_1b-updn-field-ablation.md)
