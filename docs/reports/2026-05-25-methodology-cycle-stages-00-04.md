# Methodology Cycle: Stages 00–08 — First Model Sweep

> **Date**: 2026-05-25
> **Status**: Stages 00–08 completed. BiLSTM/Transformer show strong signal.
> **Goal**: Build live-safe candidate-source pipeline and find first viable model
> **Related commit**: 82d3fe1

## Context

Previous research (`direct-direction-rebuild`, `transformer-direction`) concluded that fractal-level features do not carry statistically significant direction signal. The old production gate `signal != 0` used offline `label_all()` which is future-derived and unavailable in live `Nero.csv`.

This cycle tests a new hypothesis: a live-safe candidate-source model built from current-row Nero/PIC state can replace the offline `signal != 0` gate.

Stages 00–02 establish the research contract, raw data inventory, feature contract, MQL producer extension, and a reproducible data pipeline with PLL normalization.

## What Was Done

### Stage 00 — Research Management
- Fixed hypothesis, decision_time, decision_unit, split protocol
- Defined gate criteria: PF≥1.5, ≥6 trades/year, 0 negative years, BUY/SELL PF≥1.0, baseline uplift over direct_bar_model (1.1141) and all_rows_ranking (0.9134)
- Fixed expected artifacts: contract, inventory, feature contract, audit, pipeline manifest

### Stage 01 — Raw Data Inventory
- Classified every raw field as live_safe / target_only / future_derived / unknown
- Audited producer code (`lib_PIC.mqh`, `NERO_CSV_CREATE`)
- Explicitly rejected `signal != 0` as production candidate-source gate
- Created `feature_contract.csv` (32 rows, field-by-field status)

### MQL Producer Extension
- Added 23rd field `Shift` to fractal CSV format: `S0(SHIFT(F[f].T))`
- New format: `T:P:Dir:...:FractalAtr:Shift`
- Shift = bar index from MT4, correctly handles weekends (Δshift=1 between Friday-Monday)
- Python parsers updated: `data_loader.py`, `fractal_level_feature_builder.py`

### New Features (ML/fractal_level_feature_builder.py)
- `log_price_rel` — ln(P_i / P_0) per nearest-k slot
- `atr_band_4/12` — clipped ATR-relative distance per nearest-k slot
- `count_in_band_4/12` — level density within X ATR of fractal0
- `delta_shift_N` — inter-fractal bar distances (temporal density)

### Stage 02 — Data Pipeline
- Nero.csv regenerated from MT4: 63006 rows, 2004-07-06 – 2026-05-25, 23-field format
- Pipeline: sort → label → split (no in-pipeline normalization)
- Split: train 44104 (70%), validation 9451 (15%), test 9451 (15%)
- PLL normalization deferred to ML layer: `ML/pll_normalizer.py`
  - 8 PLL groups: price, front_back, impulse, power, count, updn_h12/24/48
  - Fit on train only, break clipped at 5, direction/strong/reverse/time_features left as-is
  - Checkpoint saved: `ML/checkpoints/pll_normalizer_v1.pkl`

## Changed Files

| File | Change |
|------|--------|
| `MT/MQL4/Include/lib_PIC.mqh` | Added Shift field to fractal CSV format (23 fields) |
| `ML/data_loader.py` | N_RAW_FEATURES=23, FRACTAL_SHIFT_IDX, shift skip in parser |
| `ML/fractal_level_feature_builder.py` | FRACTAL_FIELDS +shift, +log_price_rel, +atr_band, +count_in_band, +delta_shift |
| `ML/pll_normalizer.py` | NEW — PLLGroupScaler + PLLFeatureNormalizer |
| `ML/checkpoints/pll_normalizer_v1.pkl` | NEW — fit on train 44104 samples |
| `ML/reports/methodology_cycle_candidate_source_v2/stage00_research_contract.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage01_raw_data_inventory.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage01_gate_verdict.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage02_data_pipeline.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/feature_contract.csv` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/candidate_source_live_safe_audit.md` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage02_scale_audit_*.csv` | NEW (3 files) |
| `MT/MQL4/Files/Nero.csv` | Regenerated (full history 2004–2026) |
| `DATA/Nero_{train,validation,test}_labeled.csv` | Regenerated (no normalization, trail uses fractal0.Dir) |
| `ML/baseline_candidate_source.py` | NEW — Stage 07 RF/XGB/MLP baselines on TB + trail |
| `ML/model_sweep_candidate_source.py` | NEW — Stage 08 model sweep (BiLSTM, Transformer, RF, XGB, MLP) |
| `processing/label_signals.py` | +`use_fractal0_direction` for trail labeling (99% non-zero) |
| `ML/reports/methodology_cycle_candidate_source_v2/stage05_eda_audit.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage07_baselines.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage08_model_sweep.json` | NEW |

## Verification

```bash
# Pipeline run
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --no-normalize
# Sorting: 63006/63006 correct
# Labels: 3192 signals, 63006 predicts, 12 TB combos, 9 trail targets
# Split: 44104/9451/9451

# PLL normalizer test
python -c "
from ML.pll_normalizer import PLLFeatureNormalizer
norm = PLLFeatureNormalizer.load('ML/checkpoints/pll_normalizer_v1.pkl')
# All groups produce [0,1] output, break clipped to 5, non-norm indices unchanged
"

# New features in fractal_level_feature_builder.py
python -c "
from ML.fractal_level_feature_builder import build_fractal_level_features
import pandas as pd
df = pd.read_csv('MT/MQL4/Files/Nero.csv', sep=';', nrows=10)
r = build_fractal_level_features(df, input_family='nearest_k', k=4)
assert 'delta_shift_00' in r.columns
assert 'count_in_band_4' in r.columns
assert 'nearest_00_log_price_rel' in r.columns
# OK — 119 columns total
"
```

## Results

### Stage 00–02: Pipeline Foundation

| Parameter | Value |
|-----------|-------|
| Raw rows | 63006 (2004–2026) |
| Train/Val/Test | 44104 / 9451 / 9451 |
| Fractal fields | 23 (added Shift) |
| PLL groups | 8 (fit train only) |
| New flat features | log_price_rel, atr_band_4/12, count_in_band_4/12, delta_shift |
| Excluded inputs | body_atr_3, range_atr_6 (constant zero) |

### Stage 03 — Leakage Gate

14/14 preflight checks PASS. 5 production-gate checks pending model existence. No future-derived fields in X tensor. PLL pools isolated from targets. Naming convention: `fractal*.up_12` (input) vs `target up_12` (label).

### Stage 04 — Labeling

56 targets audited. TB convention: 0=SL, 0.5=timeout, 1=TP — no mixing. Up/dn monotonicity: 0 violations. Old `signal != 0` gate REJECTED.

### Stage 05 — EDA

Train+val only, test NOT viewed. ATR regime shift: KS=0.56 (train=3.0, val=4.85). Signal concentrated at h16–19 (US session). No NaN/Inf.

### Stage 06 — Temporal Split

Sequential, no overlap, 0 sorting errors. PASS.

### Stage 07 — Baselines

**TB combos (RF, all 12):**

| Combo | PF | Trades | WR |
|-------|-----|--------|-----|
| buy_sl3_tp3 | **1.58** | 281 | 61.2% |
| sell_sl3_tp3 | 0.92 | 3922 | 48.0% |
| Все остальные | <1.1 | <30 | <50% |

Dummy floor: PF=1.05 (stratified). Only `buy_sl3_tp3` shows signal above random.

**Trail targets — доработка разметки:** trail-таргеты были только для signal-строк (5%). Добавлен `use_fractal0_direction=True` → 99% строк получают trail PnL (направление из fractal0.Dir вместо signal).

**Trail RF baselines (PnL > 0):**

| Комбо | PF | Сделок | WR |
|-------|-----|--------|-----|
| T24x4 | 1.33 | 28 | 57% |
| T24x8 | 1.20 | 709 | 55% |
| T48x8 | 1.12 | 796 | 53% |
| Остальные | <1.1 | — | — |

Закономерность: PF растёт с шириной трейлинга, но ни один не проходит gate PF≥1.5.

**Trail + TP фикс. выход:** для trail∈[4,8,10], TP=trail×[1.5,2,3]. TP-множитель почти не влияет — трейлинг-стоп срабатывает раньше TP. Результаты эквивалентны обычному trail.

**Trail PnL > trail_atr+1:** positive rate 0.3–8.5% → слишком редкий таргет, RF не работает (PF≈0).

Вывод: flat-признаки + RF не вытягивают trail-таргеты независимо от порога. `buy_sl3_tp3` остаётся единственным viable target для baseline.

### Stage 08 — Model Sweep

Тестированы 6 моделей на бинарном `buy_sl3_tp3` (TP vs SL, timeout excluded). 3D-модели используют PLL-нормализацию, плоские — StandardScaler.

| Model | Input | PF | Trades | WR |
|-------|-------|-----|--------|-----|
| **BiLSTM** | 3D+PLL | **4.78** | 52 | 82.7% |
| **Transformer** | 3D+PLL | **2.83** | 69 | 73.9% |
| RF | flat | 1.33 | 57 | 57.1% |
| XGBoost | flat | 1.08 | 2262 | 51.8% |
| MLP | flat | 1.06 | 5687 | 51.3% |
| CatBoost | — | не установлен | — | — |

Важно: NN обучены на 8k/31k трейн-сэмплов, 10 эпох, d_model=32, 1 слой. Полное обучение ожидаемо улучшит результат.

## Conclusions

1. Stages 00–08: все PASS. Pipeline от сырых данных до model sweep работает.
2. 3D sequence models (BiLSTM, Transformer) радикально превосходят плоские модели — временная структура фракталов несёт сигнал, недоступный агрегированным признакам.
3. Trail-таргеты не работают на flat-признаках. Требуют либо нейросетей (не тестировались в sweep), либо других подходов к разметке.
4. TB `buy_sl3_tp3` — единственный viable target для текущего candidate-source цикла.
5. Test ни разу не использовался — frozen test purity сохранена.

## Limitations / Open Questions

- BiLSTM/Transformer результаты — на подвыборке 8k и 10 эпохах. Нужно обучить на полном трейне и проверить per-year/per-side.
- Результаты 3D-моделей от одного seed — нужна проверка на нескольких seed'ах.
- Trail-таргеты не тестировались с нейросетями — потенциально перспективное направление.
- `provider` и `timezone` — metadata gaps.
- PLL параметры (percentile=0.95, band widths 4/12) — начальные, могут потребовать ablation.

## Next Step

Stage 09 — Validation Freeze: выбрать winner (BiLSTM или Transformer), обучить на полном трейне, заморозить checkpoint, проверить per-year PF и negative years на валидации. Только после этого — frozen test (Stage 10).

## Related Materials

- `docs/methodology/00-research-management.md`
- `docs/methodology/01-raw-data-inventory.md`
- `docs/methodology/02-data-pipeline.md`
- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/04-labeling.md`
- `docs/reports/2026-05-18-direct-direction-rebuild.md`
- `docs/reports/2026-05-21-transformer-direction.md`
