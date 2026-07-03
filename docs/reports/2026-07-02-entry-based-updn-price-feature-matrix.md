# Entry-Based Up/Dn Price-Feature Matrix

> **Дата**: 2026-07-02
> **Статус**: Completed
> **Вердикт**: `DIAGNOSTIC_ONLY`
> **Итоговый статус runner**: `WEAK_TRACE_FOUND`
> **Связанный план**: [2026-07-02-entry-based-updn-price-feature-matrix](../superpowers/plans/2026-07-02-entry-based-updn-price-feature-matrix.md)

## Зачем запускался этап

После отрицательного результата [next-open foundation](2026-07-02-next-open-entry-updn-foundation.md) осталось два возможных объяснения:

1. сама механика входа `next open after signal_time` разрушает полезный направленный сигнал;
2. сигнал частично есть, но `structure_full` без ценовых и `path-reaction` блоков его не поднимает.

Этот этап проверяет второй вариант на том же `entry-based` target и на том же split-контракте.

## Что было зафиксировано

- target не переопределялся: использован тот же `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*` от `next open after signal_time`;
- основной split интерпретации: `val_stop = 2021-2022`;
- disclosure split: `diagnostic_holdout = 2023-2025`, `low_n_disclosure = 2026`;
- семейство модели заморожено как `xgboost_depth3`;
- seed: `42`, `77`, `123`;
- stage остаётся строго `DIAGNOSTIC_ONLY`;
- `nearest_k`, `corridor_Xatr`, `zones_atr` сознательно не входили в эту матрицу.

Покрытие split:

| Split | Rows |
|---|---:|
| `train_core` | 44159 |
| `val_stop` | 5205 |
| `diagnostic_holdout` | 8091 |
| `low_n_disclosure` | 1162 |

## Профили матрицы

| Код | Профиль | Роль |
|---|---|---|
| `E0` | `structure_full` | baseline |
| `E1` | `structure_full_relative_price` | primary |
| `E2` | `structure_full_distance_atr` | secondary |
| `E3` | `structure_full_price_coord_atr` | primary |
| `E4` | `structure_full_short_updn_source_audited` | secondary |
| `E5` | `structure_full_path_reaction` | primary |
| `E6` | `structure_full_price_atr_scaled` | diagnostic-only |

`short_updn_source_audited` использовал только `Up3/Dn3`, `Up6/Dn6`, `Up12/Dn12` из `fractal*` полей. Аудит источника: `pass`, top-level `up_*/dn_*` в feature block не читались.

`price_atr_scaled` оставлен только как диагностический контроль масштаба цены: transform `asinh`.

## Важное ограничение перед интерпретацией

Runner выполнил `statistics/data_contract_smoke_check.py`, но smoke-check завершился со статусом `FAIL` не из-за тензорного контракта новой матрицы, а из-за ожидания старых колонок `target_buy_H6_val` / `target_sell_*` в стандартном smoke-check.

Что это значит:

- shape, NaN/inf, `signed_dist_atr`, breach targets и базовые инварианты train-части прошли;
- итог этого этапа всё равно нельзя поднимать выше `DIAGNOSTIC_ONLY`;
- сравнительные результаты по блокам допустимы только как bounded diagnostic evidence.

Дополнительные ограничения аудита:

- отдельный A7-style distribution audit для новых feature blocks не выполнялся; в JSON сохранены `feature_count`, `feature_names`, hash порядка признаков и transform metadata, но нет квантилирования/долей нулей/NaN до `fillna` по каждому split;
- `short_updn_source_audited` фактически строится из `fractal*` строк, но сам `audit_updn_feature_source()` остаётся декларативной проверкой: он фиксирует намерение и metadata, а не доказывает происхождение полей через независимую трассировку producer-а;
- seed `42`, `77`, `123` не являются полноценной проверкой стохастической устойчивости: при `subsample=1.0` и `colsample_bytree=1.0` XGBoost baseline фактически детерминирован, поэтому одинаковость seed нельзя трактовать как независимое подтверждение результата;
- `rows.csv` является preview-артефактом, а не полной таблицей run-level метрик: строки повторяются по run, не содержат `profile_key`/`seed`, и текущий файл записан comma-separated, тогда как проектный CSV-контракт требует `sep=";"`.

## Результат по `entry_log_ratio` на `val_stop`

Ни один primary или secondary блок не дал сильного и устойчивого улучшения. Лучшие значения `Spearman` на `val_stop`:

| Профиль | Лучший `entry_log_ratio` на `val_stop` | Комментарий |
|---|---:|---|
| `structure_full` | `-0.0181` | baseline остаётся отрицательным |
| `relative_price` | `-0.0006` | почти ноль |
| `distance_atr` | `0.0354` | лучший по `entry_log_ratio`, но слишком слабый |
| `price_coord_atr` | `-0.0006` | почти ноль |
| `short_updn_source_audited` | `0.0016` | почти ноль |
| `path_reaction` | `0.0014` | почти ноль |
| `price_atr_scaled` | `-0.0042` | диагностический блок, пользы нет |

На disclosure split знак не даёт устойчивого полезного выигрыша: значения обычно остаются малыми и не формируют убедительный winner.

## Отдельный след по `entry_up` / `entry_dn`

Хотя `entry_log_ratio` остался слабым, отдельные стороны движения дают воспроизводимый ненулевой след:

- `structure_full`: `val_stop entry_up` до `0.3044`, `entry_dn` до `0.2180`;
- `structure_full_path_reaction`: `val_stop entry_up` до `0.3071`, `entry_dn` до `0.2601`;
- `structure_full_distance_atr`: `val_stop entry_up` до `0.3018`, `entry_dn` до `0.2652`;
- `structure_full_short_updn_source_audited`: `val_stop entry_up` до `0.2803`, `entry_dn` до `0.2576`.

Важно: этот след нельзя считать доказанным вкладом новых блоков. `structure_full` уже показывает близкий `entry_up` trace, поэтому runner-статус `WEAK_TRACE_FOUND` означает не "новые блоки нашли сигнал", а более узкий факт: в постановке `next open` сохраняется амплитудная ранжируемость отдельных `entry_up`/`entry_dn`, но она почти не превращается в направленный баланс `entry_log_ratio`.

Практический вывод: новые блоки местами немного меняют amplitude trace, но не дают убедительного uplift поверх baseline.

## Uplift Относительно `structure_full`

Лучшие значения на `val_stop`:

| Профиль | Лучший `entry_log_ratio` | Uplift к `structure_full` | Лучший `entry_up` | Лучший `entry_dn` |
|---|---:|---:|---:|---:|
| `structure_full` | `-0.0181` | `0.0000` | `0.3044` | `0.2180` |
| `relative_price` | `-0.0006` | `+0.0174` | `0.2954` | `0.2540` |
| `distance_atr` | `0.0354` | `+0.0534` | `0.3018` | `0.2652` |
| `price_coord_atr` | `-0.0006` | `+0.0174` | `0.2954` | `0.2540` |
| `short_updn_source_audited` | `0.0016` | `+0.0197` | `0.2803` | `0.2576` |
| `path_reaction` | `0.0014` | `+0.0194` | `0.3071` | `0.2601` |
| `price_atr_scaled` | `-0.0042` | `+0.0139` | `0.2837` | `0.0646` |

Даже лучший uplift (`distance_atr`, `+0.0534`) остаётся ниже заранее полезного уровня и не подтверждает торгово значимый направленный сигнал.

## Матрица интерпретации по блокам

| Блок | Что показал | Интерпретация |
|---|---|---|
| `structure_full` | `entry_log_ratio` отрицателен, `entry_up/dn` не нули | baseline не даёт направленного сигнала, но видит грубую амплитуду |
| `relative_price` | почти нулевой uplift | локальное положение цены не решает проблему `next open` |
| `distance_atr` | лучший слабый `entry_log_ratio` (`0.0354`) | даёт небольшой uplift к baseline, но уровень слишком мал для candidate |
| `price_coord_atr` | повторяет `relative_price` | signed coordinate не даёт новой пользы поверх простого relative block |
| `short_updn_source_audited` | `entry_log_ratio` почти ноль, `entry_up/dn` ненулевые | локальная историческая реакция не даёт направленного улучшения, amplitude trace близок к baseline |
| `path_reaction` | `entry_log_ratio` почти ноль, самый сильный `entry_up` trace | почти не улучшает baseline по `entry_up`, но немного сильнее по `entry_dn` |
| `price_atr_scaled` | directional пользы нет | ценовой regime сам по себе не объясняет проблему |

Итог по типам сигнала:

- `adds directional balance`: нет;
- `adds amplitude only`: частично, но основной amplitude trace уже есть в `structure_full`;
- `mostly reconstructs legacy fractal0_price behavior`: явного winner нет;
- `unstable by years / disclosure splits`: да, сильного устойчивого directional winner нет.

## Итог

1. Ограниченная price-feature matrix воспроизводимо выполнена: `21/21` run, JSON и rows CSV сохранены.
2. Ни один primary или secondary блок не дал полезного устойчивого улучшения для `entry_log_ratio` на `val_stop`.
3. Runner завершился статусом `WEAK_TRACE_FOUND`, но этот статус нужно читать осторожно: он отражает наличие amplitude trace в задаче, а не доказанный вклад новых блоков поверх `structure_full`.
4. Следовательно, проблема ветки `next open` не выглядит как простой недобор одного ценового блока: bounded матрица не нашла winner для направленного баланса.

## Следующий шаг

Если продолжать, то только узким отдельным этапом:

- сначала исправить артефактный слой: писать rows/metrics CSV с `sep=";"`, добавить `profile_key`, `seed`, `split`, `target`, `horizon`, `spearman`, и не смешивать preview rows с run-level metrics;
- усилить summary logic: `WEAK_TRACE_FOUND` должен требовать uplift к `structure_full`, а не только абсолютный `entry_up/dn` trace;
- добавить distribution audit для новых price/path blocks или явно зафиксировать отказ от него как ограничение stage;
- если продолжать моделирование, заморозить один follow-up block, а не расширять матрицу;
- кандидат для follow-up только после исправления summary logic: `distance_atr`, потому что он дал лучший слабый `entry_log_ratio` uplift; `path_reaction` пока скорее amplitude-disclosure, чем направленный кандидат;
- цель follow-up: проверить, можно ли превратить amplitude trace в полезный directional gate без смены `entry-based` target.

Не делать следующий шаг в виде «добавим ещё фильтры к next open».

## Verification

- Focused tests: `./.venv/bin/python -m pytest tests/test_entry_based_updn_price_feature_matrix.py -q` -> `18 passed`.
- Artifact cross-check: ключевые максимумы `entry_log_ratio`, `entry_up`, `entry_dn` сверены с `ML/reports/entry_based_updn_price_feature_matrix.json`.
- Full test suite в рамках этого отчёта не запускался.

## Артефакты

- [JSON](../../ML/reports/entry_based_updn_price_feature_matrix.json)
- [Rows CSV](../../ML/reports/entry_based_updn_price_feature_matrix_rows.csv)
