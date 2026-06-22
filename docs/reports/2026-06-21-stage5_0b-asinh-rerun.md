# Stage 5.0b Asinh Rerun

> **Дата**: 2026-06-21
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Выполнить отдельный Stage 5.0b rerun для Transformer с заранее зафиксированным `asinh`, обязательными проверками перед обучением и честным сравнением с baseline без объявления trading winner.
> **Related plan/spec**: `docs/superpowers/plans/2026-06-21-stage5_0b-asinh-rerun.md`

## Context

После Stage 5.0a transform comparison был нужен отдельный rerun, где `asinh` фиксируется до обучения, holdout 2023-2026 используется только для disclosure, а решение о возможном продолжении принимается только по `val_stop`.

## What Was Done

Добавлен отдельный CLI `--stage5-0b-asinh-rerun`, заморожены confirmatory и diagnostic profile sets, включён transform-aware training path с `transform_variant="asinh"`, отключён dynamic corridor `seq_len` для Stage 5.0b, а в JSON добавлены обязательные проверки, baseline-метрики и summary target-контрактов для sell/buy.

Запущен реальный single-seed rerun на CPU через:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0b-asinh-rerun --single-seed
```

## Changed Files

- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`
- `ML/reports/stage5_0b_asinh_rerun.json`
- `docs/ML/benchmark_stage5_transformer_breach.py.md`
- `docs/reports/2026-06-21-stage5_0b-asinh-rerun.md`
- `CHANGELOG.md`

## Verification

- `./.venv/bin/python -m pytest tests/ -q` -> `775 passed, 29 warnings`
- `PYTHONUNBUFFERED=1 ./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0b-asinh-rerun --single-seed` -> completed, JSON written to `ML/reports/stage5_0b_asinh_rerun.json`

## Results

### Setup

- Target: `sell_stop_broken_H6_off05_flag`
- Transform: `asinh`
- Scaler: train-only `StandardScaler`
- Dynamic corridor `seq_len`: disabled
- Holdout: 2023-2026, disclosure only
- Trading winner: not declared

### Decision Policy

Multi-seed candidate only if confirmatory profile passes predefined `val_stop` rules:

- `val_auc >= max(xgb_base_raw_plus_time + 0.01, xgb_time_only + 0.03)`
- `val_lift_30 <= min(xgb_base_raw_plus_time, xgb_time_only)`
- `normalized_distribution_audit.status != "ERROR"`
- profile role = confirmatory only

### Mandatory Checks

- OHLC verification status: `PASS`
- Label sanity status: `SANITY_ONLY`
- Label positive rate (holdout disclosure): `0.406450187762315`
- XGBoost `base_raw_plus_time` val AUC: `0.6631095529328142`
- XGBoost `base_raw_plus_time` val lift_30: `0.5538852868484367`
- XGBoost `time_only` val AUC: `0.6314223730333846`
- XGBoost `time_only` val lift_30: `0.6962245225748507`

### Confirmatory Candidates

| Profile | val_auc | val_lift_30 | holdout_auc | holdout_lift_30 | multi_seed |
|---|---:|---:|---:|---:|---|
| `all100_relative_price_time` | 0.6718975762793974 | 0.5043759874653363 | 0.6373443593145742 | 0.646786754818467 | False |
| `nearest40_relative_price_time` | 0.6337113367167122 | 0.6467152231917502 | 0.5951951626996327 | 0.7627373215086124 | False |
| `corridor_5atr_relative_price_atr_full` | 0.6146827394791232 | 0.6683755416718566 | 0.6062987451659358 | 0.7120089485816739 | False |
| `corridor_10atr_relative_price_atr_full` | 0.6161995481306445 | 0.6312435671345312 | 0.6142567474636332 | 0.7029503105590061 | False |

### Diagnostic Controls

| Profile | val_auc | val_lift_30 | holdout_auc | holdout_lift_30 |
|---|---:|---:|---:|---:|
| `all100_relative_price_no_time` | 0.61973109965454 | 0.649809554403194 | 0.6094142894127927 | 0.6975151277454056 |
| `nearest40_relative_price_no_time` | 0.563133986879711 | 0.8354694270898207 | 0.5497749834145078 | 0.8786878881987578 |
| `all100_absolute_price_atr_scaled_time_asinh` | 0.6672908253173768 | 0.5631682804827681 | 0.6447599957929483 | 0.6485984824230006 |
| `corridor_5atr_price_unit_atr_full` | 0.6215403752461905 | 0.6931301913634069 | 0.6104815253798482 | 0.6938916725363385 |
| `corridor_10atr_price_unit_atr_full` | 0.6122856212040118 | 0.6652812104604129 | 0.6132591907897931 | 0.7083854933726067 |

### Target Contracts

Sell target `sell_stop_broken_H6_off05_flag`:

- train: `n_non_null=25672`, `null_rate=0.0`, `positive_rate=0.3885945777500779`
- val_stop: `n_non_null=2832`, `null_rate=0.0`, `positive_rate=0.3806497175141243`
- holdout: `n_non_null=4527`, `null_rate=0.0`, `positive_rate=0.406450187762315`

Buy candidate columns were discovered and summarized for disclosure. For all detected `buy_stop_broken_*_flag` columns in this rerun, every split had `n_non_null=0` and `null_rate=1.0`, so buy remained contract-only and was not trained.

## Conclusions

Stage 5.0b stays `DIAGNOSTIC_ONLY`. Ни один confirmatory profile не прошёл multi-seed policy. Лучший confirmatory профиль `all100_relative_price_time` почти достиг AUC-gate (`0.6719` vs required `0.6731`) и прошёл lift gate (`0.5044 <= 0.5539`), но правила требуют одновременное выполнение всех условий.

Diagnostic control `all100_absolute_price_atr_scaled_time_asinh` выглядит близко к confirmatory лидеру по AUC, но это не winner и не основание менять решение Stage 5.0b. Это только отдельная гипотеза для нового плана.

## Limitations / Open Questions

- Holdout 2023-2026 приведён только для disclosure; он не использовался в выборе.
- Прогон один seed (`42`); multi-seed продолжение не открыто.
- Buy-side targets формально присутствуют как contract summary, но фактически пусты (`null_rate=1.0`) и пока непригодны для Stage 5.0b training.

## Next Step

Multi-seed continuation для Stage 5.0b не открывать. Если нужно развивать ветку дальше, оформить отдельный план по новой гипотезе, не переопределяя задним числом frozen confirmatory policy Stage 5.0b.

## Related Materials

- `ML/reports/stage5_0b_asinh_rerun.json`
- `docs/ML/benchmark_stage5_transformer_breach.py.md`
- `docs/reports/2026-06-20-stage5_0a-feature-distribution-audit.md`
- `docs/superpowers/plans/2026-06-21-stage5_0b-asinh-rerun.md`
