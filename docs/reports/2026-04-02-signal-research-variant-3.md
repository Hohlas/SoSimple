# Signal Research Variant 3

> **Date**: 2026-04-02
> **Status**: Completed
> **Goal**: Implement and run the full Variant 3 entry-scenario matrix in Python on the shortlisted cohorts and negative controls
> **Related plan/spec**: [docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md](../superpowers/specs/2026-04-02-signal-research-variant-3-design.md), [docs/superpowers/plans/2026-04-02-signal-research-variant-3.md](../superpowers/plans/2026-04-02-signal-research-variant-3.md)
> **Related commit**: pending

## Context

Variant 2 showed that the current ML signal behaves more like weak drift than strong impulse. Variant 3 Prep then narrowed the research shortlist to `ratio 4-5 × ATR Q4`, `ratio 4-5`, `BUY`, and `ATR Q4`, with `ratio 3-4` and `non-Q4` reserved as negative controls.

The missing step was a fair execution-style comparison of entry mechanics under a common deadline. That required two things before any matrix result could be trusted:

- `pic_price` had to come from the real fractal `price` feature in raw `Nero.csv`, not from a proxy;
- pending-entry scenarios had to be compared under the same fixed baseline geometry `12H / SL=5 / TP=50`, with the same original `t+12` expiry for every scenario.

This stage closes that gap by extending `API/signal_research.py` from Variant 2 / Prep into full Variant 3 execution research.

## What Was Done

- Extended `API/signal_research.py` with full Variant 3 scenario simulation for `market`, `pullback`, `delayed`, and `cancel-window`.
- Added raw `pic_price` extraction from `MT/MQL4/Files/Nero.csv` by selecting the latest embedded fractal inside each row via `fractal_time`, then mirroring signal-side dedupe by `time`.
- Added `Pic Price Validation` against `DATA/XAUUSD_H1_OHLC.csv` using the embedded fractal time and the expected `High/Low` side from fractal direction.
- Parameterized `pullback` and `cancel-window` with ATR-based offsets instead of fixed raw-price offsets:
  - `entry_close - ATR14 * k`, `k=1,2,3` for `BUY`, mirrored for `SELL`;
  - `pic_price`, `pic_price + ATR14`, `pic_price - ATR14`, mirrored by direction handling.
- Added the three new CLI report sections:
  - `Variant 3 Scenario Matrix`
  - `Variant 3 Shortlist Verdict`
  - `Variant 3 Negative Controls`
- Added a robustness layer on top of the full Variant 3 matrix:
  - support ladder `10/5 -> 20/10 -> 30/10 -> 40/15` for `N_filled` / `fill_pct`;
  - baseline deltas vs same-cohort `market` rows (`PF_delta`, `AvgPnL_delta`);
  - stricter shortlist verdict that now requires positive uplift and support tier `>= Supported` (`30/10` or `40/15`), instead of ranking tiny-fill rows by raw `PF`.
- Extended `tests/test_signal_research.py` with coverage for raw fractal parsing, row-level latest-fractal extraction, `pic_price` preservation, OHLC validation, limit-fill logic, scenario outcomes, and Variant 3 report smoke.
- Extended the test suite again for robustness annotation, floor-by-floor support ladders, and the stricter shortlist verdict.
- Re-ran the OOS CLI flow after the robustness pass and compared primary cohorts vs negative controls under the same support filter.

## Changed Files

- `API/signal_research.py`
- `tests/test_signal_research.py`
- `docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md`
- `docs/superpowers/plans/2026-04-02-signal-research-variant-3.md`
- `docs/reports/2026-04-02-signal-research-variant-3.md`
- `docs/reports/2026-04-02-signal-research-variant-3-prep.md`
- `docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`

## Verification

Verification commands used in the stage:

```bash
./.venv/bin/python -m pytest tests/test_signal_research.py -q
./.venv/bin/python -m API.signal_research --test-only
```

## Results

### OOS coverage and anchor validation

The fresh OOS CLI run used the `2022-07-18 11:00:00 — 2026-03-20 06:00:00` slice and produced:

- `9403` merged signal rows in the test-only slice;
- `2603` real BUY/SELL signals with excursion data;
- `9403 / 9403` OOS `pic_price` matches to the expected OHLC `High/Low` side within tolerance.

This stage therefore removes the last major data-integrity objection to pic-relative entry scenarios: the anchor is now statistically trustworthy and traceable back to the raw feature source.

### Matrix highlights on primary cohorts

The matrix does show material upside over `market` on the primary cohorts when deeper pullback entries are allowed:

| Cohort | `market PF` | Best candidate with `N_filled>=20` and `fill_pct>=10` | Candidate PF | Fill |
|---|---:|---|---:|---:|
| `ratio 4-5 × ATR Q4` | `1.34` | `pullback pic_price-1ATR` | `6.20` | `22 / 101` (`21.8%`) |
| `ratio 4-5` | `1.15` | `pullback entry_close-3ATR` | `3.55` | `54 / 369` (`14.6%`) |
| `BUY` | `1.27` | `pullback entry_close-3ATR` | `2.35` | `227 / 1374` (`16.5%`) |
| `ATR Q4` | `1.12` | `pullback entry_close-3ATR` | `2.57` | `106 / 648` (`16.4%`) |

So the first-pass Variant 3 conclusion is not “market is best”. The matrix clearly shows that delayed/deeper entry can improve price-distribution outcomes on the shortlisted groups.

### Negative controls still improve too

The more important result is that the same family of improvements is not isolated to the shortlisted cohorts:

| Control cohort | `market PF` | Strong candidate under the same robustness floor | Candidate PF | Fill |
|---|---:|---|---:|---:|
| `ratio 3-4` | `0.92` | `pullback entry_close-3ATR` | `1.62` | `193 / 940` (`20.5%`) |
| `non-Q4` | `1.02` | `cancel-window entry_close-1ATR@1b` | `1.41` | `375 / 1954` (`19.2%`) |

That means the raw PF uplift in Variant 3 cannot yet be interpreted as a cohort-specific edge. At this stage it still looks at least partly like a generic execution effect from demanding a better entry price.

### Robustness pass removes the low-fill winners

To stop the shortlist from overreacting to thin tails, the completed matrix was re-ranked under four explicit support floors:

- `10/5`: `N_filled >= 10`, `fill_pct >= 5%`
- `20/10`: `N_filled >= 20`, `fill_pct >= 10%`
- `30/10`: `N_filled >= 30`, `fill_pct >= 10%`
- `40/15`: `N_filled >= 40`, `fill_pct >= 15%`

This immediately exposed the original low-fill verdict problem:

- `ratio 4-5`: the old winner `cancel-window entry_close-3ATR@1b` disappears because it has only `3` fills;
- `BUY`: the old winner `cancel-window entry_close-3ATR@1b` disappears because it has only `14` fills;
- `ATR Q4`: the old winner `cancel-window entry_close-3ATR@1b` disappears because it has only `6` fills;
- `ratio 4-5 × ATR Q4`: the flashy `pullback pic_price-1ATR` row remains interesting, but it only survives the `20/10` floor and therefore stays below the new verdict bar.

The strongest practical shortlist after the new filter is:

| Cohort | Robust survivor | Support tier | `PF` | `PF_delta vs market` | Fill |
|---|---|---|---:|---:|---:|
| `ratio 4-5 × ATR Q4` | `pullback entry_close-2ATR` | `Supported` | `3.69` | `+2.35` | `36 / 101` (`35.6%`) |
| `ratio 4-5` | `pullback entry_close-3ATR` | `Supported` | `3.55` | `+2.39` | `54 / 369` (`14.6%`) |
| `BUY` | `pullback entry_close-3ATR` | `Strong` | `2.35` | `+1.08` | `227 / 1374` (`16.5%`) |
| `ATR Q4` | `pullback entry_close-3ATR` | `Strong` | `2.57` | `+1.45` | `106 / 648` (`16.4%`) |

So the stricter verdict does not kill the pullback hypothesis. It removes the tail-artifacts and leaves a smaller, cleaner set of survivors.

### Primary cohorts vs negative controls under the same filter

Applying the same verdict logic to the negative controls gives:

| Control cohort | Same-filter leader | Support tier | `PF` | `PF_delta vs market` | Fill |
|---|---|---|---:|---:|---:|
| `ratio 3-4` | `pullback entry_close-3ATR` | `Strong` | `1.62` | `+0.69` | `193 / 940` (`20.5%`) |
| `non-Q4` | `cancel-window entry_close-1ATR@1b` | `Strong` | `1.41` | `+0.39` | `375 / 1954` (`19.2%`) |

This is the key transportability split:

- the broad `entry_close-3ATR` pullback still improves the controls, so it looks more like a generic “better price” mechanic than a cohort-exclusive edge;
- the filtered primary cohorts improve materially more than the controls, especially `ratio 4-5` and `ATR Q4`;
- the cleanest cohort-specific survivor is now `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`.

For that top cohort, the same `entry_close-2ATR` scenario looks much weaker on the controls:

- `ratio 4-5 × ATR Q4`: `PF=3.69`, `PF_delta=+2.35`, `36` fills;
- `ratio 3-4`: `PF=1.13`, `PF_delta=+0.21`, `342` fills;
- `non-Q4`: `PF=1.04`, `PF_delta=+0.01`, `663` fills.

So `entry_close-2ATR` is not just “improves everything”; its strongest uplift remains concentrated in the best shortlist cohort.

## Conclusions

Variant 3 is now implemented and runnable end-to-end inside `API/signal_research.py`.

The full matrix plus the robustness pass produced four practical conclusions:

- `pic_price` is now a validated research anchor, so pic-relative entry scenarios are safe to compare statistically;
- the original raw-PF verdict was indeed too permissive and promoted low-fill artifacts;
- after explicit support filtering, `pullback` still dominates the shortlist, but the broad `entry_close-3ATR` family is only partly cohort-specific because it also improves the controls;
- one qualified candidate does remain for future EA prototyping: `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`.

That candidate is not “proven production-ready”, but it is the first Variant 3 row that simultaneously has:

- non-trivial support (`36` fills, `35.6%` fill rate);
- strong uplift over its own market baseline (`PF 1.34 -> 3.69`);
- no comparable uplift on `ratio 3-4` or broad `non-Q4`.

So the stage is no longer just tooling. It now has a filtered statistical conclusion: there is a plausible EA-prototype candidate, but only one clearly cleaner than the generic deeper-entry effect.

## Limitations / Open Questions

- Even the cleanest surviving candidate `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR` still has only `36` fills in the OOS slice, so it remains a medium-support signal, not a large-sample result.
- The present comparison still uses the fixed baseline `12H / SL=5 / TP=50`; the choice of entry looks promising, but the barrier geometry remains harsh.
- `pullback entry_close-3ATR` still improves the negative controls, so it should be treated as a broad benchmark rule, not as a clean cohort-specific discovery.
- Some of the strongest exploratory rows are still below the new support bar and should stay in research only, not in the prototype shortlist.

## Next Step

If the project moves from research into EA prototyping, start with the filtered winner only:

- primary prototype candidate: `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`;
- keep `pullback entry_close-3ATR` on `ratio 4-5` / `BUY` / `ATR Q4` as broad research benchmarks, not as equally clean production candidates.

Before touching the EA, the safest optional confirmation step would be one more Python-only robustness check on the winner:

- year-split stability for `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`;
- sensitivity to nearby barrier geometry around the same fixed entry rule.

## Related Materials

- [docs/reports/2026-04-01-signal-research-variant-2.md](2026-04-01-signal-research-variant-2.md)
- [docs/reports/2026-04-02-signal-research-variant-3-prep.md](2026-04-02-signal-research-variant-3-prep.md)
- [docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md](../superpowers/specs/2026-04-02-signal-research-variant-3-design.md)
- [docs/superpowers/plans/2026-04-02-signal-research-variant-3.md](../superpowers/plans/2026-04-02-signal-research-variant-3.md)
