# Entry Path v1: слой отбора сделок доведён до рабочего базового варианта

> **Date**: 2026-04-09 15:54 MSK
> **Status**: Completed
> **Goal**: Построить и проверить слой `торговать / не торговать` поверх `entry_path_v1`, а затем выбрать рабочее правило отбора сделок
> **Related plan/spec**: `docs/superpowers/specs/2026-04-08-entry-path-v1-design.md`, `docs/superpowers/plans/2026-04-08-entry-path-v1.md`, `docs/reports/2026-04-09-entry-path-v1-loss-weighting.md`
> **Related commit**: `3e2fb45`

## Context

После выбора рабочего базового варианта `entry_path_v1` стало ясно, что следующий шаг уже не в новой подгонке функции потерь, а в реальном слое отбора сделок.

Нужно было ответить на три вопроса:

- есть ли у `entry_path_v1` практический слой `торговать / не торговать`;
- даёт ли составной фильтр что-то сверх простого фильтра по `pred_ret_24_dir_atr`;
- не выбирает ли скрипт проверки слишком красивый, но слишком маленький хвост сделок.

## What Was Done

- Добавлен новый модуль [ML/entry_path_trade_filter.py](/home/hohla/git/SoSimple/.worktrees/entry-path-trade-filter/ML/entry_path_trade_filter.py) с:
  - простым фильтром `A` по `pred_ret_24_dir_atr`;
  - составным фильтром `B` по `ret_*`, `fav/adv` и `path_6`;
  - расчётом `PF`, доли выигрышных сделок, средней прибыли в ATR, проверки по периодам и последовательной проверки.
- Добавлен CLI-скрипт проверки [ML/benchmark_entry_path_trade_filter.py](/home/hohla/git/SoSimple/.worktrees/entry-path-trade-filter/ML/benchmark_entry_path_trade_filter.py), который:
  - подбирает порог только на validation;
  - замораживает правило;
  - применяет его на test без нового подбора.
- Добавлены тесты [tests/test_entry_path_trade_filter.py](/home/hohla/git/SoSimple/.worktrees/entry-path-trade-filter/tests/test_entry_path_trade_filter.py).
- В [ML/models/entry_path_transformer.py](/home/hohla/git/SoSimple/.worktrees/entry-path-trade-filter/ML/models/entry_path_transformer.py) сначала разделены последние блоки модели по головам `ret`, `path_reg`, `path_cls`.
- Затем для `path_cls` добавлен отдельный проход по последовательности, чтобы эта голова смотрела не только на общий итоговый вектор, но и на форму временного ряда.
- В [ML/entry_path_task.py](/home/hohla/git/SoSimple/.worktrees/entry-path-trade-filter/ML/entry_path_task.py) и [ML/train.py](/home/hohla/git/SoSimple/.worktrees/entry-path-trade-filter/ML/train.py) добавлены и уточнены active-only метрики для `path_6_class`.
- Выяснено, что без защитного правила скрипт проверки выбирает слишком маленький хвост сделок.
- После этого правило выбора победителя в [ML/entry_path_trade_filter.py](/home/hohla/git/SoSimple/.worktrees/entry-path-trade-filter/ML/entry_path_trade_filter.py) ужесточено:
  - режимы с числом сделок меньше `30` не считаются рабочими, если есть более живые альтернативы;
  - нужен хотя бы `1` пригодный период, если такие режимы вообще есть.

## Changed Files

- `ML/entry_path_trade_filter.py`
- `ML/benchmark_entry_path_trade_filter.py`
- `ML/models/entry_path_transformer.py`
- `ML/entry_path_task.py`
- `ML/train.py`
- `tests/test_entry_path_trade_filter.py`
- `tests/test_entry_path_model.py`
- `tests/test_entry_path_training.py`
- `tests/test_entry_path_reports.py`
- `ML/checkpoints/transformer_entry_path_v1_best.pt`
- `ML/checkpoints/transformer_entry_path_v1_result.json`
- `ML/reports/evaluate_validation_entry_path_v1.md`
- `ML/reports/evaluate_test_entry_path_v1.md`
- `ML/reports/entry_path_v1_validation_predictions.csv`
- `ML/reports/entry_path_test_predictions.csv`
- `ML/reports/entry_path_trade_filter_report.md`
- `ML/reports/entry_path_trade_filter_selected_rule.json`

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_trade_filter.py tests/test_entry_path_model.py tests/test_entry_path_training.py tests/test_entry_path_reports.py -q
/home/hohla/git/SoSimple/.venv/bin/python -m ML.train --model transformer --task entry_path_v1 --epochs 5 --seed 42
/home/hohla/git/SoSimple/.venv/bin/python -m ML.evaluate_test --task entry_path_v1 --checkpoint ML/checkpoints/transformer_entry_path_v1_best.pt
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_entry_path_trade_filter --validation-csv ML/reports/entry_path_v1_validation_predictions.csv --test-csv ML/reports/entry_path_test_predictions.csv --output-dir ML/reports --coverage-grid 0.05 0.075 0.10 0.125 0.15 0.20 0.25 0.30
```

Observed:

- `pytest`: `28 passed`
- лучший checkpoint после переобучения: `epoch=5`
- обновлены `evaluate_validation_entry_path_v1.md` и `evaluate_test_entry_path_v1.md`
- обновлены `entry_path_trade_filter_report.md` и `entry_path_trade_filter_selected_rule.json`

## Results

### Модель после доработки `path_cls`

Validation:

| Metric | Value |
|---|---:|
| `ret_pearson_r` | `0.2758` |
| `path_reg_pearson_r` | `0.2987` |
| `path_cls_f1_macro` | `0.4074` |
| active `path_cls_f1_macro` | `0.3125` |

Test:

| Metric | Value |
|---|---:|
| `ret_pearson_r` | `0.2507` |
| `path_reg_pearson_r` | `0.2667` |
| `path_cls_f1_macro` | `0.4013` |
| active `ret_pearson_r` | `0.2241` |
| active `path_cls_f1_macro` | `0.3208` |

### Что изменилось в отборе сделок

После отдельного временного пути для `path_cls` составной фильтр `B` перестал быть почти точной копией `A`.

На validation по активным строкам:

| Сравнение | Spearman | Jaccard 7.5% | Jaccard 10% | Jaccard 12.5% |
|---|---:|---:|---:|---:|
| `A` vs `B` | `0.9983` | `0.9459` | `0.7385` | `0.9231` |
| `A` vs `B_no_path6` | `0.9995` | `0.8947` | `0.7385` | `0.9231` |

Это означает, что `B` уже начал выбирать другой набор сделок, особенно в зоне `7.5%–12.5%`.

### Финальный рабочий победитель после защитного правила

Победитель на validation:

| Candidate | Coverage | Trades | PF | Stability | Worst period PF |
|---|---:|---:|---:|---:|---:|
| `A` | `7.61%` | `36` | `2.6684` | `1.00` | `1.0608` |

Test для замороженного победителя:

| Candidate | Coverage | Trades | PF | Win rate | Mean PnL ATR |
|---|---:|---:|---:|---:|---:|
| `A @ 7.5%` | `9.17%` | `44` | `4.2936` | `72.73%` | `2.3238` |

Последовательная проверка:

| Trades | PF | Win rate | Mean PnL ATR |
|---:|---:|---:|---:|
| `30` | `2.8712` | `66.67%` | `1.7694` |

### Что показал составной фильтр `B`

Хотя победителем остался `A`, сам `B` уже не пустой.

Например, на `10%`:

| Candidate | Test trades | Test PF | Sequential trades | Sequential PF |
|---|---:|---:|---:|---:|
| `A` | `74` | `1.0763` | `50` | `0.6891` |
| `B` | `55` | `2.1670` | `36` | `1.5035` |

Значит, `B` уже даёт полезную альтернативу, но по текущему правилу отбора лучший рабочий базовый вариант всё ещё `A @ 7.5%`.

## Conclusions

Этап дал рабочий и полезный результат.

Главные выводы:

- слой `торговать / не торговать` для `entry_path_v1` теперь есть и работает;
- простого фильтра `A` уже достаточно, чтобы получить живой и устойчивый базовый вариант;
- составной фильтр `B` больше не является копией `A`, но пока ещё не стал общим победителем;
- защитное правило в скрипте проверки оказалось обязательным: без него победитель получался слишком красивым, но слишком маленьким.

На сегодня самый честный и практичный базовый вариант такой:

- модель `entry_path_v1` после доработки `path_cls`;
- отбор `A`;
- замороженный порог на validation в зоне `7.5%`.

## Limitations / Open Questions

- Класс `1` в `path_6_class` всё ещё не ловится: его `F1` остаётся `0.0`.
- Победитель всё ещё покрывает только узкую часть активных сигналов.
- `B` уже отличается от `A`, но пока не выигрывает по общему правилу отбора.
- Защитное правило в скрипте проверки пока простое: `trades >= 30` и хотя бы `1` пригодный период, если такие режимы есть.

## Next Step

Следующий практический шаг уже не в новой переделке модели, а в использовании замороженного базового варианта как основы для следующего слоя отбора.

Рекомендуемый порядок:

1. взять `A @ 7.5%` как текущий рабочий базовый вариант;
2. поверх него построить conformal-слой `торговать / не торговать`;
3. сравнивать conformal не с “сырыми” сигналами, а именно с этим уже замороженным базовым вариантом;
4. `B` оставить как вторую исследовательскую ветку, а не как основной текущий победитель.

## Related Materials

- `docs/reports/2026-04-09-entry-path-v1-loss-weighting.md`
- `docs/reports/2026-04-08-entry-path-v1-baseline.md`
- `ML/reports/evaluate_validation_entry_path_v1.md`
- `ML/reports/evaluate_test_entry_path_v1.md`
- `ML/reports/entry_path_trade_filter_report.md`
- `ML/reports/entry_path_trade_filter_selected_rule.json`
