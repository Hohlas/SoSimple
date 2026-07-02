# Next Open Entry Up/Dn Foundation

> **Дата**: 2026-07-02
> **Статус**: Completed
> **Вердикт**: `DIAGNOSTIC_ONLY`
> **Итоговый статус runner**: `NO_SIGNAL_FOUND`
> **Цель**: Проверить, остаётся ли предсказуемость у `Regression Up/Dn`, если считать `up_h/dn_h` не от `fractal0_price`, а от первой реально доступной точки входа `next open after signal_time`.
> **Related plan/spec**: [2026-07-02-next-open-entry-updn-foundation plan](../superpowers/plans/2026-07-02-next-open-entry-updn-foundation.md)

## Context

Предыдущий audit показал, что для схемы `next open after signal_time` значимая часть движения уже происходит до входа. Поэтому сильная связь модели со старым target от `fractal0_price` сама по себе не отвечает на торговый вопрос.

Этот этап проверяет более честную постановку: можно ли предсказывать движение, которое начинается от фактического `entry_open`, а не от идеальной фрактальной цены.

Этап остаётся строго `DIAGNOSTIC_ONLY`. Здесь нет `PF`, `PnL`, spread, `Stop/Profit` и доказательства прибыльности.

## What Was Done

- Построен отдельный runner `ML/baseline/benchmark_next_open_entry_updn_foundation.py`.
- Для каждой строки `entry_time` зафиксирован как первый H1 `open` строго после `signal_time`.
- Новый target считается от `entry_open` по окну, которое включает бар входа и следующие `H-1` баров.
- Собраны split по прежнему исследовательскому правилу: `train_core`, `val_stop`, `diagnostic_holdout`, `low_n_disclosure`.
- Для сравнения со старым top-level target старые `up_h/dn_h` денормализованы через `processing/denormalize_updn.py` и `*_updn_params.npy`.
- Обучена фиксированная диагностическая модель: `structure_full` + `xgboost_depth3` + `seed=42`.
- Сохранены артефакты:
  - `ML/reports/next_open_entry_updn_foundation.json`
  - `ML/reports/next_open_entry_updn_rows.csv`

## Changed Files

- `ML/baseline/benchmark_next_open_entry_updn_foundation.py`
- `tests/test_next_open_entry_updn_foundation.py`
- `ML/reports/next_open_entry_updn_foundation.json`
- `docs/reports/2026-07-02-next-open-entry-updn-foundation.md`

## Verification

- `./.venv/bin/python -m pytest tests/test_next_open_entry_updn_foundation.py -q`
- Полный прогон runner завершён и записал:
  - [next_open_entry_updn_foundation.json](/home/hohla/git/SoSimple/ML/reports/next_open_entry_updn_foundation.json)
  - [next_open_entry_updn_rows.csv](/home/hohla/git/SoSimple/ML/reports/next_open_entry_updn_rows.csv)

## Results

### Contract And Coverage

Технический контракт нового target проходит:

- OHLC время распарсилось без пропусков.
- OHLC отсортирован.
- Времена уникальны.
- `entry_match_rate = 1.0` во всех split.
- Строк без `entry_open` нет.
- Строк без полного окна `H3/H6/H12` нет.

Покрытие:

| Split | Rows | Entry open available | Full H3 | Full H6 | Full H12 |
|---|---:|---:|---:|---:|---:|
| `train_core` | 44159 | 44159 | 44159 | 44159 | 44159 |
| `val_stop` | 5205 | 5205 | 5205 | 5205 | 5205 |
| `diagnostic_holdout` | 8091 | 8091 | 8091 | 8091 | 8091 |
| `low_n_disclosure` | 1162 | 1162 | 1162 | 1162 | 1162 |

OHLC ряд при этом не идеален календарно: `non_1h_gap_count = 5718`. Но для этого этапа это не ломает контракт, потому что вход выбирается по реальным временам OHLC, а не по календарному смещению.

Важно: `next open` здесь означает следующий доступный `open` в OHLC-истории, а не обязательно следующий календарный час. Большинство входов действительно происходит через 1 час, но есть разрывы:

| Split | Median delay, h | Share >1h | Share >=6h | Max delay, h |
|---|---:|---:|---:|---:|
| `train_core` | 1.0 | 5.28% | 1.20% | 102 |
| `val_stop` | 1.0 | 6.09% | 1.19% | 74 |
| `diagnostic_holdout` | 1.0 | 5.57% | 1.15% | 74 |
| `low_n_disclosure` | 1.0 | 3.79% | 0.77% | 74 |

Поэтому результат надо читать как проверку входа на следующий доступный H1 `open`, а не как гарантию, что вход всегда исполняется ровно через один час после `signal_time`.

### Distribution Shift Vs Legacy Target

Новый target заметно отличается от старого target от `fractal0_price`. Связь старого и нового `log_ratio` умеренная, но не высокая:

| Split | H3 | H6 | H12 |
|---|---:|---:|---:|
| `train_core` | 0.2935 | 0.4884 | 0.6566 |
| `val_stop` | 0.2801 | 0.4638 | 0.6326 |
| `diagnostic_holdout` | 0.2738 | 0.4673 | 0.6354 |
| `low_n_disclosure` | 0.2905 | 0.4667 | 0.6507 |

Это важный вывод сам по себе: target от реального входа не является просто косметической версией старого target.

### Model Signal On Entry-Based Target

На обучении модель видит некоторую связь с новым `entry_log_ratio`, но на основном и disclosure split она исчезает почти полностью:

| Split | H3 | H6 | H12 |
|---|---:|---:|---:|
| `train_core` | 0.1519 | 0.2034 | 0.2724 |
| `val_stop` | -0.0021 | 0.0136 | 0.0107 |
| `diagnostic_holdout` | 0.0055 | 0.0046 | 0.0203 |
| `low_n_disclosure` | -0.0074 | 0.0140 | -0.0122 |

Здесь показан `Spearman` между предсказанным и фактическим `entry_log_ratio_h`.

Практический смысл:

- на `train_core` модель частично подстраивается под новую цель;
- на `val_stop` полезной ранговой связи уже нет;
- на `2023-2025` и `2026` она тоже не восстанавливается.

### Separate Up And Down Targets

По отдельности `entry_up_h` и `entry_dn_h` модель показывает не нулевую, но слабую связь. Для `val_stop`:

| Target | H3 | H6 | H12 |
|---|---:|---:|---:|
| `entry_up_h` Spearman | 0.2794 | 0.2578 | 0.1906 |
| `entry_dn_h` Spearman | 0.2795 | 0.2471 | 0.0844 |

Это значит, что после входа модель ещё улавливает некоторую грубую величину отдельных сторон движения, но не умеет устойчиво ранжировать именно баланс `up` против `dn`, то есть не даёт полезного направленного сигнала для этой механики входа.

### Runner Gate

`NO_SIGNAL_FOUND` — это статус диагностического runner-а, а не методологический вердикт артефакта. Методологический вердикт этапа остаётся `DIAGNOSTIC_ONLY`.

Gate зафиксирован так: `PASS_DIAGNOSTIC` возможен только если хотя бы один из проверяемых `entry_log_ratio_h` на `val_stop`, `diagnostic_holdout` или `low_n_disclosure` достигает `Spearman >= 0.10`. Максимум среди всех этих проверок равен `0.0203`, поэтому runner возвращает `NO_SIGNAL_FOUND`.

Этот gate относится именно к направленному балансу `up` против `dn`. Он не отменяет слабую способность модели оценивать общий масштаб будущего движения по отдельным `entry_up_h` и `entry_dn_h`.

## Conclusions

1. Новый target от `entry_open` построен корректно и полностью покрывает исследуемые split.
2. Старый target от `fractal0_price` и новый target от реального входа различаются существенно.
3. Для `next open after signal_time` модель не сохраняет полезную связь с `entry_log_ratio_h` вне обучения.
4. Поэтому ветка `next open` получает честный отрицательный результат по направленному runner-gate: `NO_SIGNAL_FOUND`.
5. Этот результат не означает, что в данных нет никакого следа амплитуды движения: отдельные `entry_up_h` и `entry_dn_h` ранжируются слабо, но это не превращается в устойчивый направленный сигнал.

## Limitations / Open Questions

- Это только одна механика входа: `next open after signal_time`.
- В данном отчёте `next open` — следующий доступный H1 `open` в OHLC-истории; из-за рыночных разрывов это не всегда следующий календарный час.
- Этап не проверяет вход через возврат к `fractal0_price`, зону вокруг неё или `limit-entry`.
- Здесь не оценивались торговые издержки и финансовый результат.
- В runner пока не реализован полный runtime-контракт для benchmark runner-ов из методики. Особенно важно отдельно доказать, что все признаки действительно доступны к `signal_time`; если фактический `decision_time` позже, правило входа и target надо пересчитать ещё раз.

## Next Step

Следующий честный шаг не в том, чтобы спасать ветку `next open` фильтрами, а в том, чтобы отдельно проверить другую механику:

1. вход через зону около `fractal0_price`;
2. target снова считать только от фактической цены исполнения;
3. если и там устойчивой связи не будет, гипотеза о полезности этого сигнала для входа станет ещё слабее.

## Related Materials

- [JSON](../../ML/reports/next_open_entry_updn_foundation.json)
- [Rows CSV](../../ML/reports/next_open_entry_updn_rows.csv)
- [Plan](../superpowers/plans/2026-07-02-next-open-entry-updn-foundation.md)
- [Regression Up/Dn Already Moved Audit](2026-07-02-regression-updn-already-moved-audit.md)
