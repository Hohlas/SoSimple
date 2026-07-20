# benchmark_entry_based_updn_fractal_selection_ablation.py

## Назначение

Ограниченный runner для этапа `Fractal Selection Ablation On Entry-Based Target`.

Он держит фиксированными:

- target family `entry-based next open`;
- split-контракт `train_core` / `val_stop` / `diagnostic_holdout` / `low_n_disclosure`;
- модельную матрицу из четырёх tabular-моделей;
- общий плоский feature bundle `structure_full + distance_atr + price_coord_atr`.
- единый набор `Up/Dn` горизонтов `3/6/12`; `up_24/dn_24/up_48/dn_48` отбрасываются из всех профилей.

Меняется только способ отбора и группировки фракталов перед построением признаков:

- `all100`
- `nearest_k20/40/60/80`
- `corridor_5atr/10atr/15atr`
- `zones_atr`
- `zones_plus_nearest_k40`

## Что проверяет runner

- target-builder contract для `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*`;
- anchor contract:
  - anchor = `fractal0.price`;
  - шкала расстояния = row-level current `ATR`;
- единый feature bundle на всех representation profile;
- coverage и truncation до интерпретации model metrics;
- runtime contract benchmark runner-а:
  - `--resume` / `--no-resume`;
  - heartbeat;
  - progress JSON;
  - сохранение после каждого completed run;
  - disclosure фактического числа потоков.
- summary по всем `H3/H6/H12`, а не только по одному горизонту.
- `WEAK_TRACE_FOUND` требует повторения weak trace минимум на двух моделях; одиночный всплеск не поднимает runner status.
- `smoke_check_disclosure`: legacy smoke-check может падать на старом target-контракте, но это раскрывается отдельно от stage-specific `entry_based_target_contract_check`.

## Входные данные

- те же labeled CSV, что использует `ML/baseline/benchmark_next_open_entry_updn_foundation.py`;
- фрактальные колонки `fractal0..fractal99`;
- row-level `ATR`;
- канонический `entry-based` target-builder foundation stage.

## Выходные данные

- `ML/reports/entry_based_updn_fractal_selection_ablation.json`
- `ML/reports/entry_based_updn_fractal_selection_ablation_metrics.csv`
- `ML/reports/entry_based_updn_fractal_selection_ablation_rows.csv`

JSON хранит:

- `target_mode`;
- `entry_based_target_contract_check`;
- `data_contract_smoke_check`;
- `smoke_check_disclosure`;
- progress и elapsed metadata;
- representation preflight;
- distribution audit;
- результаты всех `profile/model/seed`;
- summary `best_by_model` и `best_by_representation`.

## Запуск

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py \
  --entry-based-updn-fractal-selection-ablation \
  --resume
```

Для чистого рестарта:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py \
  --entry-based-updn-fractal-selection-ablation \
  --no-resume
```

## Ограничения

- Этап не выбирает trading candidate и остаётся `DIAGNOSTIC_ONLY`.
- `val_stop=2021-2022` — единственный основной split для интерпретации.
- `diagnostic_holdout=2023-2025` и `low_n_disclosure=2026` используются только для disclosure.
- `WEAK_TRACE_FOUND` не равен подтверждённому направленному сигналу: в этом этапе лучшие точки в основном `amplitude-only`.
- Если coverage-аудит даёт `WARNING`, красивую метрику нельзя трактовать как самостоятельное подтверждение.
- Legacy `statistics/data_contract_smoke_check.py` может вернуть `FAIL` из-за старых `target_buy_H6_val`; для этого этапа решающим target-контрактом является `entry_based_target_contract_check`.
- Ridge-модель может выдавать предупреждения о плохо обусловленной матрице; её строки являются линейным диагностическим контролем, а не самостоятельным подтверждением сигнала.
