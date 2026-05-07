# Entry Path Quantile Over CPU Baseline

> **Date**: 2026-05-07
> **Status**: Completed
> **Goal**: Повторно проверить `entry_path_v1_quantile` поверх нового CPU
> baseline `entry_path_v1_live_safe + A @ 7.5%`.
> **Related reports**:
> [`2026-05-07-entry-path-live-safe-reproducibility.md`](2026-05-07-entry-path-live-safe-reproducibility.md),
> [`2026-05-07-cpu-gpu-reproducibility.md`](2026-05-07-cpu-gpu-reproducibility.md)

## Context

После исправления нормализации `predict -> front/back` и решения обучать
production checkpoint только на CPU нужно было заново проверить quantile-слой.

Старый `entry_path_v1_quantile_live_safe_baseline` был полезен как признак, что
идея не умерла, но он опирался на прежние baseline-артефакты. Новый запуск
проверяет quantile поверх per-seed CPU baseline `A @ 7.5%`.

## What Was Done

Запущен runner:

```bash
./.venv/bin/python -m ML.run_entry_path_quantile_live_safe_retrain \
  --output-dir ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline \
  --baseline-root ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed \
  --seeds 7 17 42 77 123 \
  --epochs 5 \
  --batch-size 256 \
  --baseline-coverage 0.075 \
  --clear-cache
```

Артефакты:

- `ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/manifest.json`
- `ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/multi_seed_summary.csv`
- `ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline/seed_*/`

## Results

| seed | baseline seq PF | baseline seq trades | quantile rule | quantile test PF | quantile test trades | quantile seq PF | quantile seq trades |
|---:|---:|---:|---|---:|---:|---:|---:|
| 7 | 2.0139 | 29 | `lb_gt_m_width_le_w` | 4.9557 | 16 | 2.7778 | 8 |
| 17 | 5.9352 | 27 | `lb_gt_m` | `inf` | 11 | `inf` | 6 |
| 42 | 5.9352 | 27 | `baseline` | 9.6234 | 66 | 6.2469 | 28 |
| 77 | 2.3249 | 27 | `lb_gt_m_width_le_w` | 2.8687 | 21 | 5.9134 | 10 |
| 123 | 1.8188 | 31 | `lb_gt_m` | `inf` | 4 | `inf` | 3 |

Summary:

- quantile sequential PF > 2.0: `5/5` seed;
- quantile finite sequential PF median: `5.9134`;
- quantile sequential trades: min `3`, median `8`, max `28`;
- same quantile rule max ratio: `2/5 = 0.40`;
- baseline `A @ 7.5%` sequential trades are more stable: `27..31`.

## Interpretation

Quantile did not collapse over the new CPU baseline. Profitability is present
in all five seed.

But it still should not be promoted to production:

- rule selection is unstable: `lb_gt_m_width_le_w`, `lb_gt_m`, and even plain
  `baseline` all win in different seed;
- the strongest-looking `inf` values come from very small trade counts
  (`3..6` sequential trades);
- only `2/5` seed have at least `10` sequential quantile trades.

Plain baseline `A @ 7.5%` remains the cleaner production candidate because it
has fewer moving parts and much steadier trade count.

## Verdict

`entry_path_v1_quantile` over the CPU live-safe baseline remains
**research-only**.

It is not invalidated: the profitable area is still visible. The blocker is not
PF, but rule stability and too few trades after filtering.

## Next Step

Do not run MT4 parity for quantile yet.

Continue audit of other historical systems. For `entry_path_v1_quantile`, the
next useful work would be a new narrow hypothesis that freezes one simple rule
before test and proves enough trades across seed.
