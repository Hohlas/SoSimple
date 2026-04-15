# Quantile NY Session Filter

> **Date**: 2026-04-15
> **Status**: Completed — rejected by validation gate
> **Goal**: Проверить, можно ли исключить NY-сессию из frozen `entry_path_v1_quantile` без изменения ML-сигнала и quantile rule
> **Related plan/spec**: [plan](../superpowers/plans/2026-04-13-ny-session-filter.md), [spec](../superpowers/specs/2026-04-13-quantile-execution-improvement-design.md)
> **Related commit**: pending

## Context

В PF uplift discovery исключение NY-сессии было strongest shortlist candidate:

- test `N=34`
- PF `20.276`
- uplift против quantile baseline: `+12.097`
- negative_year_slices `0`

Discovery был test-only probe. Этот этап проверял тот же механизм по validation-first discipline на frozen `entry_path_v1_quantile`: без retrain, без rule search, без изменения `lb_gt_m_q35`.

## What Was Done

Добавлен benchmark `ML/benchmark_quantile_ny_session.py` и тесты `tests/test_benchmark_quantile_ny_session.py`.

Benchmark:

- воспроизводит frozen quantile trade set через существующие helpers `attach_baseline_score`, `apply_conformal_correction`, `build_rule_mask`;
- размечает session по broker-hour buckets:
  - `0..6` asia
  - `7..12` london
  - `13..18` overlap
  - `19..23` ny
- строит filtered path через `session != ny`;
- считает baseline vs filtered metrics на validation;
- запускает test только если validation gate проходит;
- пишет JSON/CSV artifacts и seed diagnostics.

Exporter и MT4 parity не запускались, потому что Python validation gate не прошёл.

## Changed Files

- `ML/benchmark_quantile_ny_session.py`
- `tests/test_benchmark_quantile_ny_session.py`
- `ML/reports/quantile_ny_session/validation_summary.json`
- `ML/reports/quantile_ny_session/test_summary.json`
- `ML/reports/quantile_ny_session/per_seed_summary.csv`
- `ML/reports/quantile_ny_session/yearly_breakdown.csv`
- `ML/reports/quantile_ny_session/run_metadata.json`

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_ny_session.py -q
```

Result:

```text
12 passed
```

Canonical benchmark:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_ny_session \
  --validation-predictions ML/reports/entry_path_v1_quantile_validation_predictions.csv \
  --test-predictions ML/reports/entry_path_v1_quantile_test_predictions.csv \
  --baseline-validation-predictions ML/reports/entry_path_v1_validation_predictions.csv \
  --baseline-test-predictions ML/reports/entry_path_test_predictions.csv \
  --selected-rule ML/reports/entry_path_v1_quantile_selected_rule.json \
  --output-dir ML/reports/quantile_ny_session \
  --root-dir /home/hohla/git/SoSimple/ML/reports/entry_path_v1_quantile_robustness \
  --seeds 7,17,42,77,123
```

## Results

### Validation

| Metric | Quantile baseline | Non-NY filtered |
|---|---:|---:|
| trades | 27 | 24 |
| PF | 12.1458 | 41.2164 |
| win_rate | 0.8148 | 0.8333 |
| mean_pnl_atr | 2.7393 | 3.1599 |
| negative_year_slices | 0 | 0 |

Validation gate:

```text
gate_fail
```

Reason:

```text
filtered_n_trades=24 < 30
```

### Frozen test

Test verdict-stage не выполнялся, потому что validation gate не прошёл.

`test_summary.json`:

```text
status = skipped_due_to_validation_gate
reason = validation_gate_failed
```

### Multi-seed diagnostic

| Seed | Validation filtered PF | Validation filtered N | Validation gate | Test filtered PF | Test filtered N | Test diagnostic gate |
|---|---:|---:|---|---:|---:|---|
| 7 | 21.7970 | 28 | gate_fail | 20.2762 | 34 | gate_pass |
| 17 | 22.7491 | 37 | gate_pass | 15.9797 | 44 | gate_fail |
| 42 | 41.2164 | 24 | gate_fail | 39.3601 | 18 | gate_fail |
| 77 | 34.0911 | 19 | gate_fail | inf | 11 | gate_fail |
| 123 | 9.3691 | 34 | gate_pass | 14.4253 | 39 | gate_pass |

Multi-seed diagnostics are mixed: PF is strong, but support is often below gate and one seed has test negative_year_slices > 0. This does not override canonical validation failure.

## Conclusions

`NY session exclusion` **does not pass validation-first gate** for the current frozen `entry_path_v1_quantile`.

The mechanism still looks economically plausible: removing NY trades raises PF and mean PnL on validation. The blocker is support, not direction:

- baseline validation already has only `27` trades;
- after removing NY it falls to `24`;
- the project gate requires `N >= 30`.

Therefore the candidate is closed for productization under the current gate. It should not be added to exporter or MT4 settings now.

## Limitations / Open Questions

- Session buckets are broker-hour based. No MT4/DST parity was run because Python gate failed.
- The raw baseline join intentionally follows existing frozen quantile production semantics. A deduped baseline join changed canonical validation N and was rejected during review.
- Cross-instrument checks remain optional robustness stress-tests, not a replacement for same-instrument validation or forward data.

## Next Step

Do not productize NY session filter.

Next execution-uplift candidate from the shortlist: `pred_adv12 <= Q75 cap`, using the same validation-first discipline.

Forward validation for `entry_path_v1_quantile` remains the main operational gate once fresh post-decision data exists.

## Related Materials

- [PF uplift discovery](2026-04-13-pf-uplift-discovery.md)
- [Quantile early timeout](2026-04-14-quantile-early-timeout.md)
- `ML/reports/quantile_ny_session/validation_summary.json`
- `ML/reports/quantile_ny_session/test_summary.json`
- `ML/reports/quantile_ny_session/per_seed_summary.csv`
