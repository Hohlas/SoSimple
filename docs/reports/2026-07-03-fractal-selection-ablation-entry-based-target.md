# Fractal Selection Ablation On Entry-Based Target

> **Дата**: 2026-07-03
> **Статус**: Completed
> **Вердикт**: `DIAGNOSTIC_ONLY`
> **Итоговый статус runner**: `WEAK_TRACE_FOUND`
> **Цель**: Проверить, даёт ли смена способа отбора и группировки фракталов устойчивый сигнал на уже зафиксированном `entry-based next open` target.
> **Related plan/spec**: [2026-07-03-fractal-selection-ablation-entry-based-target plan](../superpowers/plans/2026-07-03-fractal-selection-ablation-entry-based-target.md)

## Context

Предыдущие этапы показали, что `entry-based next open` target существенно отличается от старого target от `fractal0_price`, а расширение price-block признаков не открыло устойчивый направленный сигнал.

Этот этап проверял более узкий вопрос: не скрыт ли слабый след в способе отбора фракталов для плоского tabular runner-а:

- полный хвост `all100`;
- ближайшие к anchor уровни `nearest_k`;
- локальный corridor вокруг `fractal0`;
- агрегаты по ATR-зонам;
- гибрид zones + nearest.

Этап заранее остаётся `DIAGNOSTIC_ONLY`: он не выбирает торговое правило, не создаёт frozen candidate и не доказывает прибыльность.

## What Was Done

- Реализован bounded runner `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`.
- Зафиксирована representation matrix из 10 профилей: `all100`, `nearest_k20/40/60/80`, `corridor_5atr/10atr/15atr`, `zones_atr`, `zones_plus_nearest_k40`.
- Зафиксирована model matrix из 4 моделей: `xgboost_depth3`, `xgboost_depth5`, `hist_gradient_boosting`, `ridge`.
- Зафиксирован anchor contract: selection anchor = `fractal0.price`, ATR anchor = row-level current `ATR`.
- После ревью исправлена честность сравнения:
  - `nearest/zones` больше не протаскивают `up_24/dn_24/up_48/dn_48`;
  - все profile metadata фиксируют `updn_horizons = 3/6/12`;
  - summary выбирает лучшие точки по всем `H3/H6/H12`, а не только по `H3`;
  - добавлен явный `smoke_check_disclosure`.
- Выполнен чистый полный прогон `--no-resume`: `120/120`.

## Changed Files

- `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`
- `tests/test_entry_based_updn_fractal_selection_ablation.py`
- `ML/reports/entry_based_updn_fractal_selection_ablation.json`
- `ML/reports/entry_based_updn_fractal_selection_ablation_metrics.csv`
- `ML/reports/entry_based_updn_fractal_selection_ablation_rows.csv`
- `docs/ML/benchmark_entry_based_updn_fractal_selection_ablation.py.md`
- `docs/reports/2026-07-03-fractal-selection-ablation-entry-based-target.md`

## Verification

- `./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -q`
- `./.venv/bin/python ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py --entry-based-updn-fractal-selection-ablation --no-resume`

Фактически подтверждено в JSON:

- `progress.done_runs = 120`
- `progress.total_runs = 120`
- `progress.thread_count = 24`
- `progress.started_at = 2026-07-03T15:59:39+00:00`
- `progress.finished_at = 2026-07-03T19:27:57+00:00`
- `progress.elapsed_sec = 12525.8`
- `entry_based_target_contract_check.status = PASS`
- `smoke_check_disclosure.interpretation = LEGACY_SMOKE_FAIL_STAGE_CONTRACT_PASS`
- запрещённые `up_24/dn_24/up_48/dn_48` в `feature_names`: `0`

## Results

### Contract And Runtime

Ключевые контрольные точки:

- `target_mode = rebuilt`
- `entry_based_target_contract_check = PASS`
- target-builder fingerprint: `9de7f59e1358a321b02e0e76b86ce67d32d07e5be0b155e6a6a7e7d2b7c753e3`
- `representation_preflight = PASS`
- `distribution_audit = WARNING`
- `data_contract_smoke_check = FAIL`
- `smoke_check_disclosure = LEGACY_SMOKE_FAIL_STAGE_CONTRACT_PASS`

Legacy smoke-check падает на старом target-контракте (`target_buy_H6_val`), который не является target-контрактом этого stage. Поэтому он раскрыт как legacy failure, но интерпретация метрик опирается на stage-specific `entry_based_target_contract_check = PASS`.

Distribution audit предупреждает по `all100`. Это не блокирует diagnostic run, но запрещает трактовать baseline-строки как чистое подтверждение без оговорки о распределениях.

### Feature Contract Correction

Главная исправленная проблема: старый прогон смешивал разные `Up/Dn` горизонты между профилями. В чистом прогоне все представления используют только `3/6/12`.

| Representation | Feature count | Up/Dn horizons |
|---|---:|---|
| `all100` | 1985 | `3/6/12` |
| `nearest_k20` | 405 | `3/6/12` |
| `nearest_k40` | 805 | `3/6/12` |
| `nearest_k60` | 1205 | `3/6/12` |
| `nearest_k80` | 1605 | `3/6/12` |
| `corridor_5atr` | 1985 | `3/6/12` |
| `corridor_10atr` | 1985 | `3/6/12` |
| `corridor_15atr` | 1985 | `3/6/12` |
| `zones_atr` | 105 | `3/6/12` |
| `zones_plus_nearest_k40` | 907 | `3/6/12` |

Feature count остаётся разным по природе representation: `nearest_k20` и `zones_atr` физически содержат меньше слотов/агрегатов, чем `all100`. Это допустимо для selection ablation, но выводы относятся к representation profile целиком, а не к одному полю.

### Best By Model

Лучшие точки по основному split `val_stop`, с выбором по всем `H3/H6/H12`:

| Model | Best representation | Target | Horizon | Score | Uplift vs all100 | Character |
|---|---|---|---|---:|---:|---|
| `xgboost_depth3` | `corridor_5atr` | `entry_log_ratio` | `H12` | `0.0795` | `+0.0498` | amplitude-only |
| `xgboost_depth5` | `nearest_k60` | `entry_log_ratio` | `H12` | `0.0663` | `+0.0142` | amplitude-only |
| `hist_gradient_boosting` | `nearest_k60` | `entry_log_ratio` | `H12` | `0.0614` | `+0.0221` | amplitude-only |
| `ridge` | `all100` | `entry_log_ratio` | `H12` | `0.0445` | `+0.0000` | amplitude-only |

Содержательно это слабый след, а не направленный winner: score ниже `0.10`, а amplitude trace сильнее directional trace.

`WEAK_TRACE_FOUND` после правки summary logic требует повторения weak trace минимум на двух моделях и не может выставляться из-за одного одиночного model-level всплеска.

### Best By Representation

| Representation | Best model | Horizon | Score | Role |
|---|---|---|---:|---|
| `all100` | `xgboost_depth5` | `H6` | `0.0520` | baseline |
| `nearest_k20` | `xgboost_depth3` | `H12` | `0.0714` | primary |
| `nearest_k40` | `xgboost_depth3` | `H12` | `0.0581` | primary |
| `nearest_k60` | `xgboost_depth5` | `H12` | `0.0663` | primary |
| `nearest_k80` | `xgboost_depth5` | `H12` | `0.0659` | primary |
| `corridor_5atr` | `xgboost_depth3` | `H12` | `0.0795` | primary |
| `corridor_10atr` | `xgboost_depth3` | `H12` | `0.0514` | primary |
| `corridor_15atr` | `xgboost_depth3` | `H12` | `0.0535` | primary |
| `zones_atr` | `hist_gradient_boosting` | `H3` | `0.0242` | secondary |
| `zones_plus_nearest_k40` | `xgboost_depth3` | `H3` | `0.0447` | secondary |

После исправления summary старый shortlist меняется: `zones_plus_nearest_k40` уже не главный кандидат, потому что прежнее место было следствием `H3-only` summary.

### Disclosure Split Check

Winner выбран только по `val_stop`; disclosure split не используется для выбора. Таблица ниже показывает, что лучший `val_stop` профиль не становится убедительным winner на `diagnostic_holdout`.

| Profile | Model | Horizon | `val_stop` | `diagnostic_holdout` same horizon | Best holdout for profile |
|---|---|---|---:|---:|---:|
| `corridor_5atr` | `xgboost_depth3` | `H12` | `0.0795` | `0.0095` | `0.0143` |
| `nearest_k20` | `xgboost_depth3` | `H12` | `0.0714` | `0.0235` | `0.0235` |
| `nearest_k60` | `xgboost_depth5` | `H12` | `0.0663` | `-0.0039` | `0.0085` |
| `nearest_k80` | `xgboost_depth5` | `H12` | `0.0659` | `-0.0081` | `0.0107` |
| `all100` | `xgboost_depth5` | `H6` | `0.0520` | `-0.0023` | `0.0238` |
| `zones_plus_nearest_k40` | `xgboost_depth3` | `H3` | `0.0447` | `0.0036` | `0.0222` |

Практический вывод: `corridor_5atr` — лучший `val_stop` trace, но disclosure не подтверждает его как устойчивый representation winner.

### Direction Versus Amplitude

| Model | Profile | Horizon | `entry_log_ratio` | Best `entry_up/dn` | Log uplift | Amp uplift | Disclosure same horizon |
|---|---|---|---:|---:|---:|---:|---:|
| `xgboost_depth3` | `corridor_5atr` | `H12` | `0.0795` | `0.1789` | `+0.0498` | `-0.0602` | `0.0095` |
| `xgboost_depth5` | `nearest_k60` | `H12` | `0.0663` | `0.1730` | `+0.0142` | `-0.0545` | `-0.0039` |
| `hist_gradient_boosting` | `nearest_k60` | `H12` | `0.0614` | `0.1662` | `+0.0221` | `-0.0746` | `-0.0021` |
| `ridge` | `all100` | `H12` | `0.0445` | `0.1261` | `+0.0000` | `+0.0000` | `-0.0646` |

Даже когда `entry_log_ratio` улучшается относительно `all100`, амплитудный след сильнее направленного. При этом amplitude uplift к `all100` у лучших directional строк отрицательный, то есть local representation не улучшает общий amplitude trace относительно полного хвоста.

### Distribution Audit Detail

Profile-level status `WARNING` выставлен только для `all100`, но количество distribution flags велико почти по всем представлениям. Это не блокирует diagnostic stage, но снижает силу любого ranking.

| Profile | Status | Val flags | Holdout flags | NEAR_CONSTANT | TAIL_GT10 | Short note |
|---|---|---:|---:|---:|---:|---|
| `all100` | `WARNING` | 551 | 551 | 426 | 676 | many tail/constant flags |
| `nearest_k20` | `PASS` | 68 | 68 | 40 | 96 | many tail/constant flags |
| `nearest_k40` | `PASS` | 168 | 168 | 80 | 256 | many tail/constant flags |
| `nearest_k60` | `PASS` | 268 | 268 | 120 | 416 | many tail/constant flags |
| `nearest_k80` | `PASS` | 368 | 368 | 160 | 576 | many tail/constant flags |
| `corridor_5atr` | `PASS` | 236 | 236 | 276 | 196 | many tail/constant flags |
| `corridor_10atr` | `PASS` | 168 | 168 | 32 | 304 | many tail/constant flags |
| `corridor_15atr` | `PASS` | 347 | 347 | 28 | 666 | many tail/constant flags |
| `zones_atr` | `PASS` | 22 | 22 | 2 | 42 | limited flags |
| `zones_plus_nearest_k40` | `PASS` | 188 | 188 | 82 | 294 | many tail/constant flags |

Итог: distribution audit не запрещает читать метрики, но запрещает делать сильный вывод о превосходстве профиля без отдельной проверки устойчивости.

### Why H12 Became Best

После all-horizon summary лучшие `entry_log_ratio` точки почти все находятся на `H12`. Это согласуется с предыдущей картиной: короткий `next open` directional signal слаб, а модель лучше улавливает более дальний баланс/амплитуду движения.

Но это же ограничивает практический смысл результата. Если механика входа предполагает быстрое решение после следующего `open`, то `H12` может быть слишком поздним горизонтом: он ближе к диагностике будущего диапазона, чем к немедленному торговому edge. Поэтому следующий шаг должен сначала решить, допустим ли `H12` как целевой горизонт для этой ветки.

### Interpretation

Фактическая картина:

- устойчивый направленный winner не найден;
- лучший directional score на `val_stop` — `corridor_5atr / xgboost_depth3 / H12 = 0.0795`;
- `nearest_k20/60/80` тоже дают слабые H12-следы выше `all100`;
- `zones_atr` и `zones_plus_nearest_k40` после честного пересчёта не выглядят главными кандидатами;
- amplitude trace остаётся сильнее directional trace;
- ridge давал `LinAlgWarning: Ill-conditioned matrix`, поэтому ridge-строки надо читать только как слабый линейный контроль.

`WEAK_TRACE_FOUND` означает только ограниченный диагностический след. Это не подтверждение торговой гипотезы и не основание выбирать candidate.

## Conclusions

1. Первичный отчёт был методически слишком мягким: в нём не было раскрыто, что `nearest/zones` содержали дополнительные `up_24/up_48`, а summary фактически был `H3-only`.
2. После исправления feature contract все representation profile используют одинаковые `Up/Dn` горизонты `3/6/12`.
3. Чистый `120/120` прогон сохранил слабый след, но он стал более узким: основной сигнал теперь находится на `H12`, особенно у `corridor_5atr` и части `nearest_k`.
4. Ни один профиль не достиг уровня убедительного directional winner.
5. Ветка `entry-based next open` остаётся слабой: локальные представления могут быть лучше полного хвоста `all100`, но это пока diagnostic trace, а не trading edge.

## Limitations / Open Questions

- Legacy `data_contract_smoke_check` остаётся `FAIL`, потому что проверяет старый target-контракт; нужен отдельный entry-based smoke-check, чтобы убрать эту двусмысленность.
- `distribution_audit = WARNING` по `all100`.
- `ridge` даёт предупреждения о плохо обусловленной матрице; его результаты нельзя использовать как самостоятельное подтверждение.
- `diagnostic_holdout` и `low_n_disclosure` остаются disclosure only.
- Множественные проверки не корректировались статистически; этап остаётся exploratory.
- Feature count различается между representation по числу слотов/агрегатов, поэтому вывод относится к профилям представления, а не к одному изолированному признаку.
- Повторение по seed не является полноценной проверкой устойчивости: для части моделей текущие параметры фактически детерминированы, поэтому одинаковые seed-результаты нельзя читать как независимое подтверждение.

## Validation Split Disclosure

Разделение данных осталось тем же:

- `train_core` — обучение;
- `val_stop = 2021-2022` — основной split для интерпретации;
- `diagnostic_holdout = 2023-2025` — disclosure only;
- `low_n_disclosure = 2026` — disclosure only.

Выбор representation winner по disclosure split запрещён.

## Next Step

Не запускать новый широкий перебор.

Перед новым обучением нужен не confirmatory cycle, а короткое методическое решение:

1. Решить, имеет ли `H12` практический смысл для механики `next open after signal_time`.
2. Если `H12` не подходит, остановить эту ветку или сформулировать отдельный короткий-horizon stop condition.
3. До любого rerun добавить entry-based smoke-check, который не зависит от старых `target_buy_H6_val`.
4. Только если `H12` признан допустимым, обсуждать узкий shortlist:
   - `corridor_5atr`
   - `nearest_k20`
   - `nearest_k60`
   - `nearest_k80`
5. Не добавлять новые `k`, corridor width и model family.

## Related Materials

- [Plan](../superpowers/plans/2026-07-03-fractal-selection-ablation-entry-based-target.md)
- [JSON](../../ML/reports/entry_based_updn_fractal_selection_ablation.json)
- [Metrics CSV](../../ML/reports/entry_based_updn_fractal_selection_ablation_metrics.csv)
- [Rows CSV](../../ML/reports/entry_based_updn_fractal_selection_ablation_rows.csv)
- [Foundation report](2026-07-02-next-open-entry-updn-foundation.md)
- [Price-feature matrix report](2026-07-02-entry-based-updn-price-feature-matrix.md)
