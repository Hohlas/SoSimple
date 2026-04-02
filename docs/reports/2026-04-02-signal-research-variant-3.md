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
- Extended `tests/test_signal_research.py` with coverage for raw fractal parsing, row-level latest-fractal extraction, `pic_price` preservation, OHLC validation, limit-fill logic, scenario outcomes, and Variant 3 report smoke.
- Re-ran the OOS CLI flow after the `pic_price` fix and after ATR-normalizing the prep profile.

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

### Current auto-verdict is too permissive

The built-in `Variant 3 Shortlist Verdict` currently ranks by `PF`, `AvgPnL`, and `fill_pct` without a minimum-support floor. In the fresh OOS run it therefore selected tiny-fill rows such as:

- `ratio 4-5`: `cancel-window entry_close-3ATR@1b`, only `3` fills;
- `BUY`: `cancel-window entry_close-3ATR@1b`, only `14` fills;
- `ATR Q4`: `cancel-window entry_close-3ATR@1b`, only `6` fills.

These rows are still useful as exploratory tails of the matrix, but they are not strong enough to drive the next trading decision without an explicit robustness filter.

## Conclusions

Variant 3 is now implemented and runnable end-to-end inside `API/signal_research.py`.

The new matrix produced two practical conclusions:

- `pic_price` is now a validated research anchor, so pic-relative entry scenarios are safe to compare statistically;
- deep pullback-style entries can improve paper metrics on the primary cohorts, but similar improvements also appear on the negative controls, so the stage did not yet isolate a clean, cohort-specific winner.

So this stage is a tooling-and-evidence completion, not yet a final trading-rule selection. The matrix is ready; the interpretation still needs stronger robustness rules.

## Limitations / Open Questions

- The current `Variant 3 Shortlist Verdict` is low-fill-biased and should not be treated as final.
- The present comparison still uses the fixed baseline `12H / SL=5 / TP=50`; the choice of entry looks promising, but the barrier geometry remains harsh.
- Some of the strongest PF rows are based on fill rates below `10%`, which may be too thin for practical MT4 deployment even if they are statistically interesting.
- Negative controls also benefit from deeper entries, so the next decision step must separate “better entry price in general” from “better entry only where the signal is truly stronger”.

## Next Step

Do a robustness pass on the Variant 3 matrix before any EA work:

- tighten the auto-verdict with explicit support floors such as minimum `N_filled` and/or minimum `fill_pct`;
- re-rank the primary cohorts against `ratio 3-4` and `non-Q4` under those floors;
- select a compact set of candidate rules for EA prototyping only after the improvement remains meaningfully stronger on the shortlisted cohorts than on the controls.

## Related Materials

- [docs/reports/2026-04-01-signal-research-variant-2.md](2026-04-01-signal-research-variant-2.md)
- [docs/reports/2026-04-02-signal-research-variant-3-prep.md](2026-04-02-signal-research-variant-3-prep.md)
- [docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md](../superpowers/specs/2026-04-02-signal-research-variant-3-design.md)
- [docs/superpowers/plans/2026-04-02-signal-research-variant-3.md](../superpowers/plans/2026-04-02-signal-research-variant-3.md)
