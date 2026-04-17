# Trailing Stop Target First Wave

> **Date**: 2026-04-16
> **Status**: Completed
> **Goal**: Проверить новый training track с path-dependent target `trail_48_pnl_atr_x{2,3,5}` и матрицей `seq_len = 20 / 50 / 100`
> **Related spec/plan**: `docs/superpowers/specs/2026-04-16-trailing-stop-target-design.md`, `docs/superpowers/plans/2026-04-16-trailing-stop-target-retraining.md`

## Context

После исчерпания Track A для `entry_path_v1` был спроектирован новый трек с другой целевой постановкой. Вместо прогноза старых entry-path величин модель учится предсказывать реальный итог сделки при простом исполнимом правиле выхода:

- один параметр `X`,
- он же начальный стоп,
- он же трейлинг-стоп,
- окно наблюдения: `48` баров,
- target: `trail_48_pnl_atr_x2`, `trail_48_pnl_atr_x3`, `trail_48_pnl_atr_x5`.

Первый bounded проход ограничен одной архитектурой `transformer` и тремя длинами истории `20 / 50 / 100`.

## What Was Done

- В labeling layer добавлено семейство trailing-stop targets для `X = 2 / 3 / 5`.
- Для реального pipeline исправлен расчёт target-ов по OHLC lookup, а не по несуществующим `Close_1/High_1/...` колонкам split CSV.
- Новый task `trailing_stop_target_v1` протянут через train/evaluate/export stack.
- Добавлен bounded benchmark для validation-first отбора по каждому из трёх target-столбцов.
- Добавлен matrix runner для `seq_len = 20 / 50 / 100`.
- Во время operational прогона найден и исправлен критический orchestration bug:
  - `seq_len` терялся на evaluate/export для не-entry-path задач;
  - теперь runner передаёт фактический `seq_len` явно в `run_evaluation()` и `generate_signals()`;
  - корректность подтверждена тестами и живым сравнением: prediction exports `seq50` не совпадают с `seq20`.

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_labels.py \
  tests/test_trailing_stop_target_task.py \
  tests/test_benchmark_trailing_stop_target.py \
  tests/test_run_trailing_stop_target_matrix.py -q
# 23 passed
```

Дополнительно после фикса `seq_len` override:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trailing_stop_target_task.py -q
# 8 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_run_trailing_stop_target_matrix.py -q
# 5 passed
```

## Results

### Train / Validation Summary

| Config | Best val `pearson_r` | Best epoch | Test `pearson_r` | Verdict |
|---|---:|---:|---:|---|
| `transformer_seq20` | `0.0952` | `2` | `0.0909` | reject |
| `transformer_seq50` | `0.0544` | `1` | `0.0212` | reject |
| `transformer_seq100` | `0.0312` | `2` | `0.0154` | reject |

Главная динамика:

- увеличение истории с `20` до `50` и `100` не улучшило регрессионный сигнал;
- лучший ML-результат всей матрицы остался у `seq20`;
- `seq100` оказался самым слабым по validation correlation.

### Best Validation PF Per Config

| Config | Best target family | Validation PF | Trades | Ulcer |
|---|---|---:|---:|---:|
| `transformer_seq20` | `trail_48_pnl_atr_x3` | `0.4206` | `24` | `13.44` |
| `transformer_seq50` | `trail_48_pnl_atr_x2` | `0.2252` | `48` | `16.80` |
| `transformer_seq100` | `trail_48_pnl_atr_x5` | `0.1961` | `48` | `46.16` |

Ключевой факт этапа:

- ни один candidate ни в одной конфигурации не достиг даже мягкого gate `PF > 1` на `validation`;
- все `final_verdict.json` в матрице имеют `verdict = reject`.

## Conclusions

Первая волна нового trailing-stop target-а дала полезный отрицательный результат:

- новая path-dependent целевая постановка действительно обучаема, но сигнал остаётся слабым;
- более длинная память `50 / 100` не помогает, а ухудшает и ML-метрики, и trading benchmark;
- лучший найденный validation candidate (`seq20 + x3`) остановился на `PF = 0.4206`, что далеко ниже рабочего уровня;
- следовательно, сам переход от старого target-а к простому trailing-stop target-у в текущем виде не решает проблему входа.

Отдельно важен инфраструктурный вывод:

- во время этапа были найдены и закрыты два реальных operational defect-а:
  - разметка trailing-stop target-ов для split CSV требовала OHLC lookup;
  - matrix runner должен передавать `seq_len` в evaluate/export явно, а не полагаться на косвенный checkpoint contract.

## Next Step

Продолжение стоит делать только как следующий отдельный трек, а не как ещё один такой же bounded rerun.

Наиболее разумные варианты:

- попробовать другую целевую постановку из оставшихся families:
  - бинарное решение `брать/не брать`,
  - ранжирование сделок внутри периода;
- либо вернуться к уже подтверждённому `entry_path_v1_quantile` и усиливать execution layer вокруг него, а не переучивать слабый вход с нуля.

## Related Materials

- `ML/reports/trailing_stop_target_matrix/transformer_seq20/`
- `ML/reports/trailing_stop_target_matrix/transformer_seq50/`
- `ML/reports/trailing_stop_target_matrix/transformer_seq100/`
- `ML/reports/trailing_stop_target_matrix/manifest.json`
- `processing/label_signals.py`
- `ML/trailing_stop_target_task.py`
- `ML/benchmark_trailing_stop_target.py`
- `ML/run_trailing_stop_target_matrix.py`
