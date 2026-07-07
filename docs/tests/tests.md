# Тесты (tests/)

## Назначение

Набор unit и smoke-тестов для ключевых модулей SoSimple. Фиксируют статистический и функциональный контракт research-инструментов, не требуя реальных данных.

## Использование

```bash
# Все тесты
./.venv/bin/python -m pytest tests/ -q

# Конкретный файл
./.venv/bin/python -m pytest tests/test_signal_path_atlas.py -q
```

## Модули

### [test_label_updn.py](../../tests/test_label_updn.py)

**Тестирует**: `processing/label_signals.py`

| Тест | Проверяет |
|------|-----------|
| `test_parse_fractal_23_fields` | 23-польный фрактал → корректный парсинг всех полей, включая shift |
| `test_parse_fractal_accepts_integer_like_float_fields` | целые поля в записи `1.0` принимаются как integer-like |
| `test_parse_fractal_rejects_normalized_float_integer_fields` | дробные нормализованные значения в integer-like полях отвергаются |
| `test_parse_fractal_none_input` | None и пустая строка → None |
| `test_parse_fractal_wrong_fields` | 22 поля → None (строгий формат) |
| `test_label_updn_basic` | last-seen логика: значения fractal0 = последние найденные |
| `test_label_updn_fractal0_missing` | строка без fractal0 → нули |

---

### [test_inverse_piecewise.py](../../tests/test_inverse_piecewise.py)

**Тестирует**: `processing/normalize.py` + `statistics/signal_tracer.py`

Round-trip `piecewise_linear_log_transform → inverse_piecewise_linear_log`.

| Тест | Зона |
|------|------|
| `test_round_trip_linear_zone` | [0, brk] — линейная |
| `test_round_trip_log_zone` | (brk, cap] — логарифмическая |
| `test_round_trip_beyond_cap` | >cap клиппируется к 1.0 → inverse = cap |
| `test_zero_stays_zero` | 0 → 0 |
| `test_round_trip_realistic_updn` | реалистичные brk/cap из проекта (up_12, dn_12) |
| `test_normalize_rowwise_returns_updn_params` | normalize_rowwise с return_updn_params=True |

---

### [test_signal_research.py](../../tests/test_signal_research.py)

**Тестирует**: `API/signal_research.py`

| Область | Примеры тестов |
|---------|----------------|
| ATR14 | true range semantics, NaN для первых 13 баров |
| Excursions | pred_fav/pred_adv алиасы по направлению, pullback windows |
| Barrier outcomes | SL_FIRST при одновременном срабатывании |
| ratio_bin | `<2` для строк с up_12/dn_12 < 2 |
| Discovery/holdout split | calendar boundary |

---

### [test_signal_path_atlas.py](../../tests/test_signal_path_atlas.py)

**Тестирует**: `API/signal_path_atlas.py`

| Область | Примеры тестов |
|---------|----------------|
| Calendar split | fixed boundary 2025-01-01 |
| Path tensor | BUY/SELL выровнены в signed ATR-space |
| Slices | построение срезов по conditioning features |
| Archetypes | labeling по медиане пути |
| Holdout replication | репликация discovery-выводов |
| CLI smoke | базовый прогон без падений |

---

### [test_signal_quality_research.py](../../tests/test_signal_quality_research.py)

**Тестирует**: `API/signal_quality_research.py` (Variant 4)

| Область | Примеры тестов |
|---------|----------------|
| Filter features | ratio_N, spread_N, cross-horizon (3vs12, 6vs24, 12vs48) |
| Direction-aware | BUY: ratio=up/dn; SELL: ratio=dn/up |
| Variance check | flat feature (>90% в одном бине) убивается |
| Univariate response map | PF, N, net_ATR, uplift по бинам |
| Shallow tree | splits, importances, leaf stats |
| Score / holdout | rank normalization, PF_holdout, confirmed |

---

### [test_ml_fractal_parser_contract.py](../../tests/test_ml_fractal_parser_contract.py)

**Тестирует**: контракт чтения `fractal*` полей в `ML/`.

| Тест | Проверяет |
|------|-----------|
| `test_ml_code_does_not_import_label_signals_parse_fractal` | `ML/` не использует `processing.label_signals.parse_fractal()` как feature extractor |
| `test_ml_code_does_not_hard_cast_normalized_categorical_fractal_fields` | нормализованные `strong`, `break`, `count` не приводятся обратно к `int` |

---

### [test_entry_based_updn_fractal_selection_ablation.py](../../tests/test_entry_based_updn_fractal_selection_ablation.py)

**Тестирует**: `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`

| Область | Примеры тестов |
|---------|----------------|
| Frozen registry | порядок representation profile и model grid |
| CLI | `--resume` по умолчанию, `--no-resume` override |
| Anchor contract | `nearest_k` и `corridor_Xatr` строятся от `fractal0.price` и row-level `ATR` |
| Feature contract | общий `same_feature_bundle`, target denylist, запрет `up_24/dn_24/up_48/dn_48` во всех representation profile |
| Coverage audit | пустые строки, truncation, corridor coverage summary |
| Runtime contract | progress JSON, per-run save, `thread_count` propagation |
| Summary logic | `WEAK_TRACE_FOUND` / `NO_SIGNAL_FOUND`, best-by tables по всем `H3/H6/H12`, smoke-check disclosure |

### [test_entry_based_next_open_closeout.py](../../tests/test_entry_based_next_open_closeout.py)

**Тестирует**: `ML/baseline/benchmark_entry_based_next_open_closeout.py`

Команда:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py -q
```

| Область | Примеры тестов |
|---------|----------------|
| Frozen scope | shortlist `all100/corridor_5atr/nearest_k20/60/80`, `H3/H6/H12/H24`, no cross-pair validation |
| Entry smoke-check | stage-specific target columns без legacy target dependency, `NaN`/`inf`, вариативность target, `entry_time > signal_time`, порядок split-ов |
| Feature contract | `H24` target matrix, serialized `Up/Dn 3/6/12/24/48`, запрет top-level targets и нулевых `fractal0_updn` добавок во входе |
| Scale audit | `none_tree_raw`, разделение input/target normalization pools, dominance checks |
| Metrics | direction/amplitude Spearman и gross `simple_trade` diagnostic |
| Verdict | `STOP`, `PIVOT`, `CONTINUE` rules, запрет `CONTINUE` при combined validation roles и для `all100` control |

### [test_entry_based_powerful_tabular.py](../../tests/test_entry_based_powerful_tabular.py)

**Тестирует**: `ML/baseline/benchmark_entry_based_powerful_tabular.py`

Команда:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py -q
```

| Область | Примеры тестов |
|---------|----------------|
| Scope | `all100/corridor_5atr/nearest_k60/nearest_k80`, 10 model keys, один seed `42` |
| Control/candidate split | `all100` участвует в overall ranking, но не может дать `DIRECTION_REPLICATION_REQUIRED` |
| Model factory | XGBoost, LightGBM, CatBoost, ExtraTrees, HistGradientBoosting и thread-count metadata |
| Leakage guard | запрет top-level `entry_*`, `target_*`, `label_*`, `ret_*`, `fav_*`, `adv_*` во входах |
| Split contract | `low_n_disclosure=2026` не влияет на verdict, horizon embargo убирает boundary crossing |
| Audit contract | `WARNING` требует `audit_decisions`, `ERROR` блокирует fit |
| Runtime metadata | `feature_count`, `actual_thread_count`, top-level JSON metadata, `normalization_contract`, `yearly_metrics` в run payload |
| Verdict | `REJECT_CAPACITY_EXPLANATION`, `PIVOT_AMPLITUDE`, `DIRECTION_REPLICATION_REQUIRED`; freeze-like verdict запрещён |

### [test_entry_based_sequence_transformer.py](../../tests/test_entry_based_sequence_transformer.py)

**Тестирует**: `ML/baseline/benchmark_entry_based_sequence_transformer.py`

Команда:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_sequence_transformer.py -q
```

| Область | Примеры тестов |
|---------|----------------|
| Scope | `all100_sequence/nearest_k80_sequence/nearest_k60_sequence`, 3 model keys, один seed `42` |
| Tensor contract | shape `[rows, 100, token_features]`, порядок `fractal0 -> fractal99`, padding/mask |
| Feature contract | `fractal0` `Up/Dn` занулены, `fractal1..99` serialized `Up/Dn` разрешены |
| Leakage guard | запрет top-level `entry_*`, `target_*`, `label_*`, `ret_*`, `fav_*`, `adv_*` во входах |
| Split contract | `low_n_disclosure=2026` не влияет на winner selection, `locked_test` не открыт |
| Normalization | input scaler fit only on valid train tokens, target scaler fit only on train targets |
| Resume/output | `run_config_hash`, output isolation от closeout/powerful artifacts |
| Verdict | `REJECT_SEQUENCE_CAPACITY_EXPLANATION`, `PIVOT_AMPLITUDE`, `DIRECTION_REPLICATION_REQUIRED`; freeze-like verdict запрещён |

### [test_entry_based_amplitude_movement.py](../../tests/test_entry_based_amplitude_movement.py)

**Тестирует**: `ML/baseline/benchmark_entry_based_amplitude_movement.py`

Команда:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_amplitude_movement.py -q
```

| Область | Примеры тестов |
|---------|----------------|
| Target contract | `entry_movement_H = max(entry_up_H, entry_dn_H)`, train-only quantile thresholds |
| Feature profiles | simple baseline, post-entry diagnostic-only, no-time/no-price sequence profiles |
| Leakage guard | запрет target/outcome/return колонок во входах |
| Selection policy | post-entry diagnostic имеет `selection_eligible=false`, freeze-like verdict запрещён |
| Runtime contract | resume/progress, failed-run accounting, skipped profiles |
| Metrics | Spearman, top-lift, yearly check, yearly artifact identity, seed aggregate |
| Report contract | target unit contract, feature audit, verdict allowlist |

## Зависимости

- `pytest>=8.0`
- `numpy>=1.24`
- `pandas>=2.0`
- `scikit-learn` (только `test_signal_quality_research.py`)

## Ограничения

- Все тесты используют синтетические fixtures, не реальные данные.
- Research-инструменты (signal_path_atlas, signal_research) дополнительно верифицируются вручную на реальном датасете перед stage close.
