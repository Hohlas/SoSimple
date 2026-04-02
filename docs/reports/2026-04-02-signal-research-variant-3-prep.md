# Signal Research Variant 3 Prep

> **Date**: 2026-04-02
> **Status**: Completed
> **Goal**: Finish the cohort-oriented research prep stage before full Variant 3 entry-scenario testing
> **Related plan/spec**: [docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md](../superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md), [docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md](../superpowers/plans/2026-04-02-signal-research-variant-3-prep.md)
> **Related commit**: pending

## Context

Signal Research Variant 2 showed that the current ML signal behaves more like a weak drift than a strong impulse. That was enough to justify the next question, but not enough to answer it: which signal subgroups are worth testing in Variant 3, and where should entry timing research focus first.

This stage was created to avoid testing `market / pullback / delayed / cancel-window` on the full signal pool blindly. It also closed the MT4-vs-Python volatility gap by making `atr14` part of the canonical OHLC export.

The completed OOS run used `MT/MQL4/Files/ml_signals.csv` together with `DATA/XAUUSD_H1_OHLC.csv` on the `2022-07-18 11:00:00 — 2026-03-20 06:00:00` slice and produced `2603` real BUY/SELL signals with excursion data.

## What Was Done

- Extended `MT/MQL4/Scripts/ExportOHLC.mq4` so the MT4 export now writes canonical `atr14`.
- Updated `API/signal_research.py` to prefer CSV `atr14` with Python ATR fallback for legacy OHLC files.
- Added fixed baseline annotation for `12H / SL=5 / TP=50`.
- Added the new Variant 3 prep report sections `Cohort Map`, `Entry Opportunity Profile`, `Stability Split`, and `Priority Cohorts`.
- Extended `tests/test_signal_research.py` to cover canonical ATR loading, baseline cohort summaries, entry-opportunity calculations, and the new report sections.
- Re-ran the OOS research flow with the refreshed OHLC file that already contains `atr14`.
- Closed the stage with a canonical report, `CHANGELOG` entry, and refreshed `CONTEXT_HANDOFF`.

## Changed Files

- `API/signal_research.py`
- `tests/test_signal_research.py`
- `MT/MQL4/Scripts/ExportOHLC.mq4`
- `docs/DATA_FLOW.md`
- `docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md`
- `docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md`
- `docs/reports/2026-04-02-signal-research-variant-3-prep.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`

## Verification

Verification commands used in the stage:

```bash
python -m pytest tests/test_signal_research.py -q
python -m API.signal_research --test-only
```

## Results

### Core OOS summary

| Metric | Value |
|---|---:|
| OOS period | `2022-07-18 11:00:00 — 2026-03-20 06:00:00` |
| Real BUY/SELL signals | `2603` |
| Baseline setup | `12H / SL=5 / TP=50` |
| Baseline PF | `1.05` |
| Baseline AvgPnL | `0.2` |
| Broad `BUY PF_12` | `1.35` |
| Broad `SELL PF_12` | `0.95` |
| Broad `ATR Q4 PF_12` | `1.23` |
| Broad `non-Q4 PF_12` | `1.02` |
| Best broad ratio bucket | `4-5` |
| Persistent anti-pattern | `3-4` |

### `pic_price` extraction validation

Before using `pic_price` as a Variant 3 anchor, the extraction logic was validated against `DATA/XAUUSD_H1_OHLC.csv` on the full deduplicated `Nero.csv` universe:

- validated rows: `58766`
- match to fractal-bar `High/Low` within `0.05` price tolerance: `100.0%`
- peak rows (`direction=1`) vs `High`: `100.0%`
- trough rows (`direction=-1`) vs `Low`: `100.0%`
- max absolute error: `0.05`
- median absolute error: `0.02`

This confirms that the research `pic_price` anchor is aligned with the actual fractal bar in OHLC terms; the small non-zero error is a rounding/tick-scale effect, not a wrong-bar mismatch.

### Priority cohorts for Variant 3

| Cohort | N | PF_12 | Net_12 mean | AvgPnL_baseline |
|---|---:|---:|---:|---:|
| `ratio 4-5 × ATR Q4` | 101 | 2.62 | 22.2 | 1.4 |
| `ratio 4-5` | 369 | 1.95 | 6.4 | 0.5 |
| `BUY` | 1375 | 1.35 | 2.4 | 0.9 |
| `ATR Q4` | 649 | 1.23 | 4.1 | 0.5 |

### Anti-pattern cohorts

| Cohort | N | PF_12 | Net_12 mean | AvgPnL_baseline |
|---|---:|---:|---:|---:|
| `ratio 3-4` | 941 | 0.87 | -1.2 | -0.3 |
| `SELL` | 1228 | 0.95 | -0.5 | -0.6 |
| `non-Q4` | 1954 | 1.02 | 0.1 | 0.1 |
| `ratio 5+` | 658 | 1.05 | 0.3 | -0.0 |

### Entry-opportunity profile highlights

After converting the prep profile from raw-price thresholds to ATR-normalized thresholds, the path picture became more conservative and more informative:

| Cohort | `pullback>=1ATR_1H` | `fav>=1ATR_1H` | `fav>=3ATR_6H` | `close>0_6H` |
|---|---:|---:|---:|---:|
| `ratio 4-5 × ATR Q4` | `12.9%` | `24.8%` | `13.9%` | `51.5%` |
| `ATR Q4` | `12.6%` | `16.2%` | `10.2%` | `51.4%` |
| `ratio 4-5` | `21.1%` | `20.6%` | `11.1%` | `52.8%` |
| `non-Q4` | `19.2%` | `18.5%` | `11.6%` | `49.6%` |

The important correction is that the old raw-price impression of “Q4 gives much larger pullbacks” was mostly a volatility-scale artifact. After ATR normalization, early pullback incidence is no longer a strong discriminator, and broad `non-Q4` is not materially worse on normalized pullback depth.

What still survives normalization is the continuation side: the top shortlist cohort `ratio 4-5 × ATR Q4` remains the best early-favorable profile on `fav>=1ATR_1H` and the best long-window favorable profile on `fav>=3ATR_6H`, while `close>0_6H` stays roughly similar across the shortlisted cohorts.
These `...>=kATR...` thresholds are descriptive prep metrics from this stage, not fixed Variant 3 limit-entry offsets.

### Stability highlights

- `ratio 3-4` stayed weak in every shown year: `PF_12 = 0.78, 0.80, 0.81, 0.99, 0.83`.
- `ratio 4-5` was weak in `2022-2023`, turned positive in `2024`, and became much stronger in `2025-2026`.
- Broad `SELL` remained weak through `2023-2025` and improved only in `2026`, so it is still regime-sensitive.
- `ATR Q4` became meaningfully stronger in the later OOS years, especially `2025-2026`.

## Conclusions

Variant 3 prep did produce a real statistical research result, not just tooling:

- the strongest next-step research cohort is `ratio 4-5 × ATR Q4`;
- `ratio 4-5` remains the best broad ratio bucket and should stay in the primary shortlist;
- `ratio 3-4` remains a robust anti-pattern and should be used as a negative control, not a candidate;
- broad `SELL` is still too weak to treat as a primary Variant 3 target without extra filtering;
- `ATR Q4` is the clearest regime split for focusing entry-scenario work.
- `pic_price` is now validated as a trustworthy research anchor against OHLC `High/Low`, so pic-relative Variant 3 scenarios are statistically safe to compare.
- ATR-normalized prep metrics show that the strongest cohorts still have better favorable continuation, but not obviously larger normalized pullback depth; so `pullback` should be treated as a hypothesis to test, not as something already “proven” by prep.

The stage also clarified an important nuance: even strong cohorts can still show low `TP_FIRST%` under the fixed baseline `12H / SL=5 / TP=50`, because `TP=50` is far away and many rows finish as `SL_FIRST` or `NEITHER`. So the value of this stage is not “we found a ready-made trading rule”; it is “we found where entry-timing research is worth spending time”.

## Limitations / Open Questions

This stage did not simulate actual Variant 3 entry policies yet. It only prepared the evidence base and shortlist.

The main remaining questions are:

- does `pullback` entry outperform `market` on `ratio 4-5 × ATR Q4`;
- is `delayed` entry better than immediate entry for `ATR Q4` or only for the strongest ratio cohorts;
- should `ratio 5+` be kept only as a secondary benchmark rather than a primary candidate;
- can `SELL` be rescued by tighter cohort filters, or is it mostly a regime artifact in this OOS period.

## Next Step

Run the full Variant 3 entry-scenario research on the shortlist from this stage:

- primary cohorts: `ratio 4-5 × ATR Q4`, `ratio 4-5`, `BUY`, `ATR Q4`
- negative controls: `ratio 3-4`, `non-Q4`
- scenarios: `market`, `pullback limit entry`, `delayed entry`, `cancel-window`
- `pullback` and `cancel-window` parameterization: adaptive offsets `ATR14 * k` with `k=1,2,3` (instead of fixed absolute price offsets), using both `entry_close` and `pic_price` anchors; `pic_price` must come from the real fractal `price` feature in raw `Nero.csv`, after row-level ordering by embedded fractal time (mirroring `label_main.py`), not from the normalized labeled output.

The goal of the next stage should be to compare those entry mechanics explicitly on the shortlisted cohorts instead of on the full signal set.

## Related Materials

- [docs/reports/2026-04-01-signal-research-variant-2.md](2026-04-01-signal-research-variant-2.md)
- [docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md](../superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md)
- [docs/superpowers/plans/2026-04-02-signal-research-variant-3-prep.md](../superpowers/plans/2026-04-02-signal-research-variant-3-prep.md)
