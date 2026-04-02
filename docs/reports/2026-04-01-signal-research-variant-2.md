# Signal Research Variant 2

> **Date**: 2026-04-01
> **Status**: Completed
> **Goal**: Finish OHLC-oriented signal research before Variant 3
> **Related plan/spec**: [docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md](../superpowers/specs/2026-04-01-signal-research-variant-2-design.md)
> **Related commit**: pending

## Context

The goal of this stage was to turn `API/signal_research.py` into a trading-oriented OHLC research tool and answer the practical questions needed before Variant 3: entry timing, pullback behavior, `SL/TP` geometry, and regime splits.

The work was built on the existing `regression_updn` signal pipeline and the OHLC research design. The stage was explicitly meant to avoid changing the EA yet and instead collect evidence about how the current signal behaves in path-dependent trade mechanics.

The OOS run covered `2022-07-18 11:00:00` to `2026-03-20 06:00:00` on `DATA/XAUUSD_H1_OHLC.csv` with `MT/MQL4/Files/ml_signals.csv` as the signal source.

## What Was Done

- Expanded `API/signal_research.py` for Variant 2 research blocks.
- Added or extended `tests/test_signal_research.py` to cover the new research behavior.
- Updated `CHANGELOG.md` with the stage outcome.
- Ran the Variant 2 verification flow against the OHLC dataset and real BUY/SELL signals.

## Changed Files

- `API/signal_research.py`
- `tests/test_signal_research.py`
- `CHANGELOG.md`

## Verification

Verification commands used in the stage:

```bash
python -m pytest tests/test_signal_research.py -q
python -m API.signal_research --test-only
```

## Results

Key OOS facts from the completed research:

| Metric | Value |
|---|---:|
| Real BUY/SELL signals | 2603 |
| `adv_1` | 5.6 |
| `adv_3` | 8.8 |
| `adv_6` | 12.2 |
| Best base setup | `12H / SL=5 / TP=50 / PF=1.05` |
| Best `ratio_12` bucket | `4-5` |
| Weak `ratio_12` bucket | `3-4` |
| `BUY PF_12` | 1.35 |
| `SELL PF_12` | 0.95 |
| `ATR Q4 PF_12` | 1.23 |

The stage also confirmed that the signal profile is not a strong impulse; it is a weak positive drift with meaningful early adverse movement.

## Conclusions

Variant 2 showed that the current ML signal has a weak positive edge, but not enough of a directional impulse to rely on direction alone.

The most important practical conclusions are:

- signal behavior is closer to weak drift than to a strong breakout impulse;
- timing of entry matters because early adverse movement is common;
- `ratio_12 = 3-4` is dangerous and should not be treated as a preferred subgroup;
- `ratio_12 = 4-5` is the priority subgroup for the next stage;
- Variant 2 does not prove that limit entry is better, so that hypothesis remains open for Variant 3.

## Limitations / Open Questions

This stage did not answer the algorithmic entry question. It only showed that the current signal often moves against the entry first and that the path-dependent trade profile is sensitive to how entry is timed.

Open questions carried into Variant 3:

- Is market entry better than pullback entry?
- Does a delayed entry improve the path profile?
- Should some signals be cancelled if the expected setup does not appear quickly enough?
- Are these effects different for `BUY`, `SELL`, `ratio_12` buckets, and `ATR` regimes?

## Next Step

Compare `market`, `pullback`, `delayed`, and `cancel-window` entry scenarios in Variant 3. Use the current `12H` baseline and keep the comparison explicit across `BUY` / `SELL`, `ratio_12`, and `ATR` subsets.

## Related Materials

- [docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md](../superpowers/specs/2026-04-01-signal-research-variant-2-design.md)
- [docs/superpowers/plans/2026-04-01-signal-research-variant-2.md](../superpowers/plans/2026-04-01-signal-research-variant-2.md)
- [docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md](../superpowers/specs/2026-04-01-signal-research-variant-2-findings.md)
