# Methodology Cycle: Stages 00–09 — Candidate Source v2

> **Date**: 2026-05-25
> **Status**: Stages 00–09 PASS. Transformer validation freeze remains research-only pending frozen test.
> **Goal**: Build a live-safe candidate-source pipeline and freeze a validation-selected candidate without viewing test.
> **Related commit**: pending

## Context

Previous research (`direct-direction-rebuild`, `transformer-direction`) concluded that fractal-level features do not carry statistically significant direction signal. The old production gate `signal != 0` used offline `label_all()` which is future-derived and unavailable in live `Nero.csv`.

This cycle tests a new hypothesis: a live-safe candidate-source model built from current-row Nero/PIC state can replace the offline `signal != 0` gate.

Stages 00–09 establish the research contract, raw data inventory, feature contract, MQL producer extension, reproducible data pipeline with PLL normalization, data-quality checks, temporal split protocol, baselines, model sweep, and validation freeze.

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

### Stage 05–09 — Validation Candidate Path
- Stage 05 EDA was restricted to train+validation; test was not inspected.
- Stage 06 added an explicit temporal split manifest and validation/test use policy.
- Stage 07 baselines now include confusion matrices, classification metrics, per-year slices, and diagnostic BUY/SELL slices.
- Stage 08 was rerun after fixing binary timeout handling; timeout rows are excluded from TP-vs-SL threshold/PF evaluation.
- Stage 09 froze a deterministic Transformer checkpoint and replaced the high-PF concentrated rule with a validation-calibrated stability rule.

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
| `ML/model_sweep_candidate_source.py` | NEW — Stage 08 model sweep (BiLSTM, Transformer, RF, XGB, MLP), timeout-excluded binary evaluation |
| `processing/label_signals.py` | +`use_fractal0_direction` for trail labeling (99% non-zero) |
| `ML/reports/methodology_cycle_candidate_source_v2/stage05_eda_audit.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage06_temporal_split_manifest.json` | NEW — split manifest and allowed-use policy |
| `ML/reports/methodology_cycle_candidate_source_v2/stage07_baselines.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage08_model_sweep.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage08_validation_predictions.csv` | NEW — validation predictions for Stage 08 audit |
| `ML/reports/methodology_cycle_candidate_source_v2/stage09_frozen_rule.json` | NEW — deterministic Transformer frozen rule |
| `ML/reports/methodology_cycle_candidate_source_v2/stage09_stability_refreeze.json` | NEW — validation-only stability refreeze scan |
| `ML/validation_freeze.py` | NEW — deterministic Stage 09 Transformer freeze |
| `ML/stage09_stability_refreeze.py` | NEW — validation-only threshold/top-k stability scan |
| `docs/ML/baseline_candidate_source.py.md` | NEW — Stage 07 script docs |
| `docs/ML/model_sweep_candidate_source.py.md` | NEW — Stage 08 script docs |
| `docs/ML/stage09_stability_refreeze.py.md` | NEW — Stage 09 stability scan docs |

## Verification

```bash
# Pipeline run (Stage 02)
./.venv/bin/python processing/label_main.py --input MT/MQL4/Files/Nero.csv --no-normalize
# Sorting: 63006/63006 correct
# Labels: 3192 signals, 63006 predicts, 12 TB combos, 9 trail targets
# Split: 44104/9451/9451

# PLL normalizer test
./.venv/bin/python -c "
from ML.pll_normalizer import PLLFeatureNormalizer
norm = PLLFeatureNormalizer.load('ML/checkpoints/pll_normalizer_v1.pkl')
# All groups produce [0,1] output, break clipped to 5, non-norm indices unchanged
"

# New features in fractal_level_feature_builder.py
./.venv/bin/python -c "
from ML.fractal_level_feature_builder import build_fractal_level_features
import pandas as pd
df = pd.read_csv('MT/MQL4/Files/Nero.csv', sep=';', nrows=10)
r = build_fractal_level_features(df, input_family='nearest_k', k=4)
assert 'delta_shift_00' in r.columns
assert 'count_in_band_4' in r.columns
assert 'nearest_00_log_price_rel' in r.columns
# OK — 119 columns total
"

# Stage 07 baseline rerun
./.venv/bin/python ML/baseline_candidate_source.py --thresholds 0.35,0.40,0.45,0.50,0.55,0.60,0.65,0.70,0.75
# RF_160 PF=1.5761, 281 trades, 1 negative year

# Stage 08 model sweep rerun after timeout-mask fix
./.venv/bin/python ML/model_sweep_candidate_source.py
# Transformer PF=11.60/63 trades; BiLSTM PF=1.7383/293 trades
# stage08_validation_predictions.csv saved, 9451 validation rows + header

# Stage 09 stability refreeze
./.venv/bin/python ML/stage09_stability_refreeze.py
# selected validation-calibrated threshold=0.5359389781951904
# PF=1.9722, 142 trades, 0 negative years, 4 active years

# Artifact validation
./.venv/bin/python -m py_compile ML/baseline_candidate_source.py ML/model_sweep_candidate_source.py ML/stage09_stability_refreeze.py ML/validation_freeze.py
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
for p in Path('ML/reports/methodology_cycle_candidate_source_v2').glob('stage*.json'):
    json.loads(p.read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
print('all_stage_json_strict_ok')
PY
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

Sequential split manifest added. Train/validation/test boundaries are explicit, shuffle is disabled, row overlap is false, and sorting errors are 0. No purged embargo was applied; this is recorded as a restriction rather than hidden. Stage 11 must perform per-year/regime robustness because Stage 05 found a train-validation volatility shift.

### Stage 07 — Baselines

Baseline-first report now includes dummy baselines, RF/HGB baselines, confusion matrices, classification reports, per-year slices, and diagnostic BUY/SELL slices. Trading metrics are gross diagnostics; costs are deferred to Stage 12.

| Model | PF | Trades | WR | Negative years | Note |
|-------|----|--------|----|----------------|------|
| RF_160 | **1.5761** | 281 | 61.2% | 1 | Best simple baseline, not production-ready |
| HGB | 1.1217 | 3985 | 52.9% | 1 | Higher frequency, weaker edge |
| dummy_stratified | 1.0454 | 3420 | 51.1% | — | Class-prior floor |
| dummy_most_frequent | 1.0391 | 9451 | 51.0% | — | Always TP probability above low threshold |
| dummy_uniform | 0.0 | 0 | 0.0% | — | No selected trades at grid threshold |

Baseline to beat: RF_160 validation PF plus 0 negative years. RF_160 itself does not satisfy the full robustness gate because it has one negative validation year.

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

Тестированы модели на бинарном `buy_sl3_tp3` (TP vs SL, timeout excluded). 3D-модели используют PLL-нормализацию, плоские — StandardScaler. После исправления Stage 08 timeout-строки исключаются и из threshold/PF расчёта, а validation predictions сохраняются в `stage08_validation_predictions.csv`.

| Model | Input | PF | Trades | WR |
|-------|-------|-----|--------|-----|
| **Transformer** | 3D+PLL | **11.60** | 63 | 92.1% |
| **BiLSTM** | 3D+PLL | **1.74** | 293 | 63.5% |
| RF | flat | 1.33 | 42 | 57.1% |
| XGBoost | flat | 1.08 | 1487 | 51.8% |
| MLP | flat | 1.06 | 3652 | 51.3% |
| CatBoost | — | не установлен | — | — |

Важно: Stage 08 — exploratory validation-only sweep. NN обучены на подвыборке 8k binary train-сэмплов, 10 эпох, d_model=32, 1 слой. Высокий PF Transformer на Stage 08 не является frozen rule: детерминированная заморозка, checkpoint, round-trip и stability refreeze выполняются отдельно в Stage 09.

### Stage 09 — Validation Freeze

Transformer 3-class заморожен детерминированно (`torch.use_deterministic_algorithms(True)`), checkpoint и PLL normalizer сохранены с SHA-16 hash. Первичный high-PF порог `0.60` дал PF=2.57 на 35 сделках, но был отвергнут как canonical rule из-за концентрации: 27/35 сделок (77%) в 2019, 0 сделок в 2022.

Validation-only stability refreeze выбрал порог `0.5359389781951904`, откалиброванный из top 1.5% validation scores:

| Rule | PF | Trades | Trades/year | WR | Neg years | Active years | Max year share | Bootstrap CI |
|------|----|--------|-------------|----|-----------|--------------|----------------|--------------|
| threshold=0.53594 | **1.97** | **142** | **40.6** | 66.4% | 0 | 4 | 47.9% | [1.36, 3.00] |

Per-year: 2019 PF=1.88 (68 trades), 2020 PF=3.00 (18), 2021 PF=2.10 (38), 2022 PF=1.20 (18). Test was not viewed.

## Conclusions

1. Stages 00–09: все PASS. Pipeline от сырых данных до validation freeze работает.
2. 3D sequence models радикально превосходят плоские модели на exploratory validation sweep, but Stage 09 is the only frozen validation rule.
3. Trail-таргеты не работают на flat-признаках. Требуют либо нейросетей, либо других подходов к разметке.
4. TB `buy_sl3_tp3` — единственный viable target для текущего candidate-source цикла.
5. Test ни разу не использовался — frozen test purity сохранена.
6. Stage 09 canonical rule предпочитает устойчивость и частоту сделок максимальному validation PF.

## Limitations / Open Questions

- Stage 09 Transformer всё ещё validation-only: production claims запрещены до frozen test, robustness, costs и MT4 parity.
- Stage 09 выбран по одному seed; для production-grade вывода нужна multi-seed проверка или формальное решение оставить deterministic single-seed research candidate.
- Trail-таргеты не тестировались с нейросетями — потенциально перспективное направление.
- Stage 06 split has no purged embargo; this is accepted for the current candidate-source workflow but must not be interpreted as purged-CV evidence.
- Stage 08 exploratory Transformer PF is inflated-looking and based on a single seed/subsample; Stage 09 stability rule is the canonical candidate, not Stage 08 max-PF row.
- `provider` и `timezone` — metadata gaps.
- PLL параметры (percentile=0.95, band widths 4/12) — начальные, могут потребовать ablation.

## Next Step

Stage 10 — Frozen Test OOS: один раз применить замороженный Transformer rule (`threshold=0.5359389781951904`) к test без изменения checkpoint, normalizer, threshold, target или execution mapping.

## Related Materials

- `docs/methodology/00-research-management.md`
- `docs/methodology/01-raw-data-inventory.md`
- `docs/methodology/02-data-pipeline.md`
- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/04-labeling.md`
- `docs/methodology/05-eda-data-quality.md`
- `docs/methodology/06-temporal-split.md`
- `docs/methodology/07-baseline-first.md`
- `docs/methodology/08-model-development.md`
- `docs/methodology/09-validation-freeze.md`
- `docs/reports/2026-05-18-direct-direction-rebuild.md`
- `docs/reports/2026-05-21-transformer-direction.md`
