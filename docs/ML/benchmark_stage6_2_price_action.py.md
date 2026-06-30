# ML/baseline/benchmark_stage6_2_price_action.py

Stage 6.2 DIAGNOSTIC_ONLY runner для проверки H12 price-action feature family.

## Назначение

Скрипт проверяет, добавляют ли recent OHLC price-action признаки сигнал для H12 TP/SL touch outcome сверх same-run baseline `h12_clock_shift_back`.

Фиксированный контракт:

- XAUUSD H1
- H12
- entry `Open[row+1]`
- SL `0.5 ATR`
- TP `2.0 ATR`
- same-bar ambiguity = SL-first
- selection only on `val_stop` (`2021-2022`)
- `diagnostic_holdout` (`2023-2025`) and `low_n_disclosure` (`2026`) are disclosure-only

## Входы

- `DATA/Nero_XAUUSD_train_labeled.csv`
- `DATA/Nero_XAUUSD_validation_labeled.csv`
- `DATA/Nero_XAUUSD_test_labeled.csv`
- `DATA/XAUUSD_H1_OHLC.csv`

OHLC features use only bars with timestamp `<= row.time`. `Open[row+1]`, future H12 bars and future-derived columns are not used as inputs.

## Выходы

- `ML/reports/stage6_2_h12_price_action_feature_family.json`
- canonical report: `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md`

JSON contains input manifest hashes, feature names and hashes, preflight, feature audit, raw seed/profile runs, summary, baseline-delta summary, gate, top-level and per-run `elapsed_sec`.

## Запуск

```bash
./.venv/bin/python ML/baseline/benchmark_stage6_2_price_action.py \
  --stage6-2-price-action --resume
```

Fresh run:

```bash
./.venv/bin/python ML/baseline/benchmark_stage6_2_price_action.py \
  --stage6-2-price-action --no-resume
```

## Runtime Contract

- `xgb_n_jobs=24`
- heartbeat на preflight, feature build и каждом seed-run
- checkpoint before preflight
- checkpoint after every run
- `--resume` skips completed `(profile, seed)` pairs

## Ограничения

Stage 6.2 is exploratory. The artifact status is capped at `DIAGNOSTIC_ONLY`; passing metrics here cannot create a production candidate without a separate confirmatory plan.
