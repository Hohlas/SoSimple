# Quantile pred_adv12 Cap

> **Date**: 2026-04-15
> **Status**: Completed — rejected by validation gate
> **Goal**: Проверить `pred_adv_12_atr <= Q75(validation)` поверх frozen `entry_path_v1_quantile`
> **Related plan/spec**: [plan](../superpowers/plans/2026-04-13-pred-adv-cap.md), [spec](../superpowers/specs/2026-04-13-quantile-execution-improvement-design.md)
> **Related commit**: 12a2609

## Context

В PF uplift discovery фильтр `pred_adv12 <= Q75` выглядел сильным:

- test `N=37`
- PF `12.746`
- uplift против quantile baseline: `+4.567`
- negative_year_slices `0`

Но discovery threshold был получен на test probe. В этом этапе threshold фиксировался строго на validation selected trades.

## What Was Done

Добавлен benchmark `ML/benchmark_quantile_pred_adv_cap.py` и тесты `tests/test_benchmark_quantile_pred_adv_cap.py`.

Benchmark:

- воспроизводит frozen quantile-selected trades;
- сохраняет `pred_adv_12_atr` из quantile predictions;
- считает threshold как `Q75(pred_adv_12_atr)` только на validation selected trades;
- применяет cap inclusive: `pred_adv_12_atr <= threshold`;
- test оценивает только если validation gate passes;
- пишет JSON/CSV artifacts и seed diagnostics.

Exporter и MT4 parity не запускались, потому что Python validation gate не прошёл.

## Changed Files

- `ML/benchmark_quantile_pred_adv_cap.py`
- `tests/test_benchmark_quantile_pred_adv_cap.py`
- `ML/reports/quantile_pred_adv_cap/validation_summary.json`
- `ML/reports/quantile_pred_adv_cap/test_summary.json`
- `ML/reports/quantile_pred_adv_cap/per_seed_summary.csv`
- `ML/reports/quantile_pred_adv_cap/yearly_breakdown.csv`
- `ML/reports/quantile_pred_adv_cap/run_metadata.json`

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_pred_adv_cap.py -q
```

Result:

```text
23 passed
```

Canonical benchmark:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_pred_adv_cap \
  --validation-predictions ML/reports/entry_path_v1_quantile_validation_predictions.csv \
  --test-predictions ML/reports/entry_path_v1_quantile_test_predictions.csv \
  --baseline-validation-predictions ML/reports/entry_path_v1_validation_predictions.csv \
  --baseline-test-predictions ML/reports/entry_path_test_predictions.csv \
  --selected-rule ML/reports/entry_path_v1_quantile_selected_rule.json \
  --output-dir ML/reports/quantile_pred_adv_cap \
  --root-dir /home/hohla/git/SoSimple/ML/reports/entry_path_v1_quantile_robustness \
  --seeds 7,17,42,77,123 \
  --quantile 0.75
```

## Results

Validation threshold:

```text
Q75(pred_adv_12_atr) = 0.02345952
```

Critical diagnostic:

```text
All 27 canonical validation selected trades have pred_adv_12_atr = 0.02345952.
```

### Validation

| Metric | Quantile baseline | pred_adv cap |
|---|---:|---:|
| trades | 27 | 27 |
| PF | 12.1458 | 12.1458 |
| win_rate | 0.8148 | 0.8148 |
| mean_pnl_atr | 2.7393 | 2.7393 |
| negative_year_slices | 0 | 0 |

Validation gate:

```text
gate_fail
```

Reasons:

```text
filtered_n_trades=27 < 30
seed_pf_values_contain_non_finite: [None, None, None]
```

### Frozen test

Test verdict-stage не выполнялся, потому что validation gate не прошёл.

`test_summary.json`:

```text
status = skipped_due_to_validation_gate
```

### Multi-seed diagnostic

| Seed | Validation baseline N | Validation filtered N | Validation filtered PF | Validation gate |
|---|---:|---:|---:|---|
| 7 | 32 | 0 | n/a | gate_fail |
| 17 | 41 | 41 | 13.0032 | gate_pass |
| 42 | 27 | 27 | 12.1458 | gate_fail |
| 77 | 19 | 0 | n/a | gate_fail |
| 123 | 38 | 0 | n/a | gate_fail |

Seed diagnostics confirm that the frozen validation threshold does not transfer cleanly across seeds: several seed validation selections are entirely above the canonical threshold and collapse to zero trades.

## Conclusions

`pred_adv12 <= Q75(validation)` **does not work as a productizable execution filter** for the current frozen `entry_path_v1_quantile`.

The main finding is not just support failure. On canonical validation, `pred_adv_12_atr` is constant across all selected trades, so the validation-derived Q75 cap does not filter anything:

- baseline `N=27`;
- filtered `N=27`;
- same PF, same win rate, same mean PnL.

This means the strong discovery result came from test-period distribution that is not represented in canonical validation selected trades. Under validation-first discipline, this candidate is closed.

## Limitations / Open Questions

- The result does not prove `pred_adv_12_atr` is useless globally. It proves that this specific Q75 cap is not usable on current frozen quantile validation.
- Future research could test `pred_adv` in a relaxed/standalone universe, but that is a new plan and cannot reuse this production verdict.
- Cross-instrument checks remain optional robustness stress-tests, not a replacement for same-instrument validation.

## Next Step

Do not productize `pred_adv12 <= Q75` for current quantile path.

The three initial PF uplift candidates are now all closed under strict validation-first gates. The next useful research questions are:

1. `session filter` as a standalone system;
2. relaxed quantile rule plus session/pred_adv filter to recover support;
3. forward validation once fresh post-decision data exists.

## Related Materials

- [PF uplift discovery](2026-04-13-pf-uplift-discovery.md)
- [Quantile NY session filter](2026-04-15-quantile-ny-session.md)
- [Quantile early timeout](2026-04-14-quantile-early-timeout.md)
- `ML/reports/quantile_pred_adv_cap/validation_summary.json`
- `ML/reports/quantile_pred_adv_cap/per_seed_summary.csv`
