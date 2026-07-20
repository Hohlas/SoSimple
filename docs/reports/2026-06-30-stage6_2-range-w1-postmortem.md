# Stage 6.2 Range W1 Post-Mortem

> **Дата**: 2026-06-30
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Explain why `range_w1_atr` dominates Stage 6.2 and why the stability check remains weak.
> **Related plan/spec**: `docs/superpowers/plans/2026-06-30-stage6_2-range-w1-postmortem.md`

## Context

Stage 6.2 tested a fixed H12 OHLC price-action family. It stayed `DIAGNOSTIC_ONLY` because `h12_price_action_core` failed the permutation gate even though it had a weak validation ranking signal.

This post-mortem answers a narrower question: why `range_w1_atr` dominated feature importance, and why that did not become a robust trading result.

## What Was Done

- Added a bounded diagnostic script that reads the frozen Stage 6.2 JSON and rebuilds only the fixed `h12_price_action_core` features.
- Recomputed descriptive slices for `val_stop`, with `diagnostic_holdout` and `low_n_disclosure` kept as disclosure-only.
- Added bucket, side, year x side, selected-trade, activity-proxy, and permutation-context summaries.
- No model was retrained. No horizon, ATR, TP/SL, profile, seed, or threshold search was added.

## Changed Files

- `ML/baseline/analyze_stage6_2_range_w1_postmortem.py`
- `tests/test_stage6_2_range_w1_postmortem.py`
- `ML/reports/stage6_2_range_w1_postmortem.json`
- `docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md`
- `docs/ML/analyze_stage6_2_range_w1_postmortem.py.md`
- `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `MODULE_INDEX.md`, `wiki/*`

## Verification

Commands:

```bash
./.venv/bin/python ML/baseline/analyze_stage6_2_range_w1_postmortem.py
./.venv/bin/python -m pytest tests/test_stage6_2_range_w1_postmortem.py -q
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py tests/test_stage6_2_range_w1_postmortem.py -q
./.venv/bin/python -m pytest tests/ -q
git diff --check
./.venv/bin/python wiki/wiki.py verify
./.venv/bin/python wiki/wiki.py status
```

Observed before report generation:

- focused post-mortem tests: `7 passed`
- focused Stage 6.2 + post-mortem tests: `25 passed`
- full suite: `942 passed, 30 warnings`
- `git diff --check`: no output
- wiki verify/status: up to date, no gaps

## Results

Artifact consistency:

- Primary profile: `h12_price_action_core`.
- Stage 6.2 gate status: `TRADING_GATE_FAILED`.
- Stage 6.2 primary p-value: `0.16`.
- Top feature from Stage 6.2 JSON: `range_w1_atr`.

## Multiple Testing Context

- This post-mortem runs after the fixed Stage 6.2 search: 5 profiles x 3 seeds.
- It does not train models, add features, search thresholds, or change the gate.
- `val_stop` is used only to explain the already failed Stage 6.2 gate.
- `diagnostic_holdout` and `low_n_disclosure` remain disclosure-only.

Dominance and direct relation:

- Top feature: `range_w1_atr`.
- Top/second importance ratio: `7.561`.
- `range_w1_atr` vs target correlation on non-zero `val_stop`: `0.202`.
- `range_w1_atr` vs PnL correlation on non-zero `val_stop`: `0.008`.
- Zero-vector rows on `val_stop`: `3/5415`.
- Evidence strength: `weak`.

The bucket table shows the core pattern: TP-rate rises from `0.251` in `q1` to `0.526` in `q5`. So `range_w1_atr` is visibly related to TP/SL ordering. But PnL correlation is only `0.008`, so it almost does not explain result size in R.

| Bucket | Known rows | TP-rate |
|---|---:|---:|
| `q1` | 932 | 0.251 |
| `q2` | 907 | 0.292 |
| `q3` | 884 | 0.350 |
| `q4` | 839 | 0.404 |
| `q5` | 656 | 0.526 |

Selected trade analysis:

- Seeds available for selected-trade analysis: `3/3`.
- TP-rate denominator is known `stage6_definitive_tp_vs_sl_flag` rows, not all selected rows.

| Seed | Threshold | Selected rows | Selected known | Selected unknown | Selected TP-rate | Selected mean PnL | Non-selected known | Non-selected TP-rate |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 0.700 | 121 | 66 | 55 | 0.833 | 0.245 | 4152 | 0.346 |
| 77 | 0.725 | 91 | 50 | 41 | 0.820 | 0.232 | 4168 | 0.348 |
| 123 | 0.725 | 86 | 45 | 41 | 0.867 | 0.283 | 4173 | 0.348 |

BUY/SELL disclosure:

| Side | Rows | TP-rate | Mean PnL | range_w1 vs target corr | range_w1 vs PnL corr |
|---|---:|---:|---:|---:|---:|
| `buy` | 2580 | 0.357 | -0.036 | 0.199 | 0.009 |
| `sell` | 2832 | 0.351 | -0.029 | 0.205 | 0.007 |

Year x side disclosure:

| Year | Side | Rows | TP-rate | Mean PnL | range_w1 vs target corr | range_w1 vs PnL corr |
|---:|---|---:|---:|---:|---:|---:|
| 2021 | `buy` | 1290 | 0.356 | -0.041 | 0.186 | 0.004 |
| 2021 | `sell` | 1396 | 0.344 | -0.042 | 0.215 | 0.016 |
| 2022 | `buy` | 1290 | 0.357 | -0.031 | 0.215 | 0.015 |
| 2022 | `sell` | 1436 | 0.358 | -0.015 | 0.196 | -0.002 |

Activity proxy checks:

- `range_w1_atr` vs `ATR` correlation: `-0.059`.
- `range_w1_atr` vs `bar_range_1_atr` correlation: `0.846`.
- Zero-vector share on `val_stop`: `0.001`.
- Interpretation: the dominant feature is not mainly a broad ATR regime proxy. It mostly reflects the size of the last candle before the decision row.

Validation disclosure:

- `val_stop`: `3/5415` zero-vector rows.
- `diagnostic_holdout`: `48/8091` zero-vector rows.
- `low_n_disclosure`: `551/1162` zero-vector rows.
- `diagnostic_holdout` and `low_n_disclosure` were not used for choosing profiles, seeds, thresholds, or gates.

Permutation context:

- Primary permutation p-value: `0.16`; required `<= 0.1`.
- Seed p-value range: `0.155` to `0.35`.
- Observed median PF: `1.307`.
- Observed PF range: `1.180` to `1.359`.

| Seed | Observed PF | Random PF median | Random PF p95 | Observed - p95 | p-value |
|---:|---:|---:|---:|---:|---:|
| 42 | 1.307 | 1.089 | 1.504 | -0.197 | 0.160 |
| 77 | 1.180 | 1.093 | 1.532 | -0.353 | 0.350 |
| 123 | 1.359 | 1.095 | 1.567 | -0.208 | 0.155 |

The key stability fact is that observed PF is below random-permutation p95 for every seed. That explains why `p=0.160` does not pass the gate: the selected PF is still inside a strong random tail.

## Conclusions

- `range_w1_atr` does not look like a zero-vector artifact on `val_stop`.
- It also does not look like a broad ATR-regime artifact: correlation with `ATR` is only `-0.059`.
- It most likely reflects the size of the last candle before the decision row: correlation with `bar_range_1_atr` is `0.846`.
- TP-rate grows monotonically by `range_w1_atr` bucket, so there is a weak ranking signal for TP/SL ordering.
- The signal is not a robust trading edge: PnL correlation is almost zero, and observed PF stays below random-permutation p95 in all three seeds.
- Stage 6.2 remains `DIAGNOSTIC_ONLY`; this post-mortem does not promote the feature family.

## Limitations / Open Questions

- The post-mortem is descriptive and does not prove causality.
- Selected-trade TP-rate is computed on a small number of selected rows with known definitive TP/SL outcomes.
- `low_n_disclosure` is weak because `551/1162` rows are zero-vector price-action rows.
- The legacy global data-contract debt from Stage 6.2 remains: `statistics/data_contract_smoke_check.py` failed on unused historical target column `target_buy_H6_val`.
- The result cannot be used as a trading rule without a new clean validation cycle.

## Next Step

Proceed to `Regression Up/Dn target foundation`.

This report does not provide enough evidence for another minor OHLC-window variant.

## Related Materials

- `docs/superpowers/plans/2026-06-30-stage6_2-range-w1-postmortem.md`
- `ML/reports/stage6_2_range_w1_postmortem.json`
- `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md`
- `ML/reports/stage6_2_h12_price_action_feature_family.json`
- `ML/baseline/analyze_stage6_2_range_w1_postmortem.py`
