# Signal Path Atlas Research — Design Spec

> **Date**: 2026-04-03
> **Status**: Draft
> **Scope**: Python-only statistical research around conditional post-signal path geometry
> **Out of scope**: EA changes, model retraining, SL/TP optimization, execution-rule selection

## Context

Variant 2 established that the current ML signal behaves more like weak drift than strong impulse. Variant 3 Prep then showed that ATR-normalized pullback incidence is not an obvious discriminator by itself, while favorable continuation remains stronger on the best cohorts. Variant 3 robustness finally produced one filtered execution candidate:

- `ratio 4-5 x ATR Q4 + pullback entry_close-2ATR`

That locked winner remains useful as a benchmark, but it still has low support and is not the main object of this stage.

The current risk is methodological: continuing to rank `PF` winners in Python would mostly reproduce rule-search pressure in a different form. This stage therefore changes the research object. Instead of searching directly for the next trading rule, it aims to build a conditional path atlas for the signal itself, then use that atlas later to justify or reject downstream execution hypotheses.

## Goal

Build a reproducible `path atlas` for post-signal price behavior in ATR-normalized coordinates, using a strict `discovery / holdout` split.

The stage must answer:

- what the typical post-signal path geometry looks like globally;
- which feature slices materially change path shape, event ordering, or first-passage probabilities;
- whether those path effects replicate on holdout;
- whether the evidence supports future `market`, `pullback`, both, or neither as downstream execution research.

The stage must not choose a new EA rule or optimize fixed barrier geometry.

## Research contract

- Main result: `conditional path atlas`
- Secondary result: a small set of replicated path claims
- Locked benchmark retained for reference only:
  - `ratio 4-5 x ATR Q4 + pullback entry_close-2ATR`
- No `SL=5 / TP=50` baseline inside the core atlas
- No execution ranking by `PF` as the primary output
- `Holdout` is touched only after all discovery artifacts are frozen

## Data sources

- `MT/MQL4/Files/ml_signals.csv`
- `DATA/XAUUSD_H1_OHLC.csv`

The atlas operates on the same real BUY/SELL signal universe used in Variant 2/3.

## Time split

- `discovery`: signal time `<= 2024-12-31 23:59:59`
- `holdout`: signal time `>= 2025-01-01 00:00:00`

`Holdout` is not used for:

- feature screening;
- quantile-bin construction;
- archetype definition;
- tree fitting;
- threshold selection;
- claim discovery.

It is used once, at the end, only for replication of already locked atlas artifacts.

## Path representation

All path metrics are direction-aware so `BUY` and `SELL` can be analyzed in one aligned coordinate system.

Anchor:

- `entry_close`

Scale:

- `ATR14`

Base horizon grid:

- internal computation on `1..12` bars after signal;
- report emphasis on `1 / 3 / 6 / 12` bars.

Per-signal path tensor:

- `signed_ret_h`: signed close-to-close return by horizon `h`, in ATR units
- `fav_h`: maximum favorable excursion up to horizon `h`, in ATR units
- `adv_h`: maximum adverse excursion up to horizon `h`, in ATR units

First-passage levels:

- adverse levels: `-1 / -2 / -3 ATR`
- favorable levels: `+1 / +2 / +3 / +5 ATR`

Event-ordering features:

- `adverse_first`
- `favorable_first`
- `dip_then_rally`
- `rally_then_dip`

Time-to-hit features:

- first bar index where each adverse or favorable level is reached

The atlas must prioritize quantiles, hit probabilities, and ordering probabilities over mean curves.

## Feature families

The atlas may use the same pre-signal feature families already discussed for signal-quality filtering, but only as conditioning variables for path analysis:

- `ratio_h`
- `spread_h`
- `short_vs_long`
- other live pre-signal axes already available in the merged research frame

Post-signal quantities are response variables only. They must not be reused as conditioning features.

## Step 0 — Feature screen on discovery

For each candidate conditioning feature on `discovery`:

- `mean`
- `std`
- `Q10`
- `Q50`
- `Q90`
- `IQR`
- `n_unique`

Near-constant or degenerate features are removed before any atlas slicing.

Minimum kill criteria:

- `Q90 == Q10`;
- `IQR == 0`;
- fewer than `20` distinct values on discovery;
- attempted `5`-quantile slicing collapses to fewer than `3` non-empty bins.

This step exists to stop fake cohort effects caused by near-constant axes.

## Step 1 — Global atlas on discovery

Produce the unconditional post-signal path summary for the full discovery sample.

Required outputs:

- quantile curves for `signed_ret_h`
- quantile curves for `fav_h`
- quantile curves for `adv_h`
- first-passage probability matrix by level and horizon
- event-ordering table
- time-to-hit summary

This section is descriptive, not selective.

## Step 2 — Univariate atlas slices

For each live conditioning feature:

- construct locked quantile bins on discovery;
- use `5` bins by default;
- merge adjacent bins automatically if support becomes too thin.

Final bin support floor:

- each final bin must contain at least `80` discovery signals and at least `5%` of discovery rows;
- if that is impossible, the feature stays descriptive in Step 0 only and is excluded from Step 2+ slicing.

For each final bin, report:

- `N`
- quantile path profile for `signed_ret_h`, `fav_h`, `adv_h`
- first-passage probabilities
- ordering probabilities
- time-to-hit summaries

The goal is not to rank bins by `PF`, but to detect meaningful path-shape differences:

- stronger early adverse dip;
- stronger continuation after dip;
- flatter drift;
- faster favorable move;
- persistent failure pattern.

## Step 3 — Path archetypes

Cluster or otherwise group signals by path signature, not by PnL ranking.

Desired archetype types:

- immediate continuation
- deep dip then recovery
- flat or noisy drift
- failure or adverse continuation

Archetype construction is fixed as:

- standardized path-signature vector built from `signed_ret_1..12`, `fav_1..12`, and `adv_1..12`;
- `k-means` with `k=4` on discovery only;
- if any cluster has less than `10%` of discovery rows, merge it into the nearest remaining centroid and relabel the final atlas back to `4` interpretable archetype names only if support remains adequate, otherwise reduce the final reported archetype count to `3`.

For each archetype, report:

- `N`
- archetype path signature
- first-passage profile
- ordering profile
- dominant conditioning-feature tendencies

The archetypes must be locked on discovery before any holdout check.

## Step 4 — Interpretable explanation layer

If a shallow tree is used, it is not a winner-selection engine. Its only role is interpretability.

Acceptable use:

- explain which `2-3` feature splits best separate path archetypes;
- create human-readable cohort definitions for atlas interpretation.

Not acceptable:

- ranking trading rules directly by `PF`;
- using the tree as a proxy EA optimizer.

Tree constraints should remain intentionally small and stable, for example depth-limited and with meaningful minimum leaf size.
Required constraints:

- maximum depth `2`;
- minimum leaf size `max(80, 5% of discovery rows)`.

## Discovery claims to lock before holdout

Before touching `holdout`, freeze:

- the final list of live features;
- quantile-bin boundaries;
- the chosen atlas claims to validate;
- archetype definitions or assignment logic;
- any shallow-tree splits kept for interpretation.

The holdout stage cannot add new claims.

## Holdout replication protocol

The holdout stage validates path geometry, not trading performance.

Validation objects:

- global atlas shape
- univariate slice differences
- archetype signatures
- ordering probabilities

Minimum practical support:

- any slice, cohort, or archetype with `N_holdout < 30` is labeled `Exploratory`, not `Validated`

Replication verdict classes:

- `Replicated`
- `Directionally consistent`
- `Failed`
- `Exploratory`

Guidance:

- `Replicated`: same directional effect and similar path geometry with adequate support
- `Directionally consistent`: same general effect, weaker magnitude
- `Failed`: sign flip, shape flip, or clear breakdown
- `Exploratory`: insufficient holdout support

Holdout comparison must use:

- `Q10 / Q50 / Q90` path summaries
- first-passage probabilities
- ordering probabilities
- archetype frequencies

Formal p-values are not the main success criterion. Reproducibility of path shape is the main criterion.

## Deliverables

### 1. Canonical atlas report

A single report describing:

- experiment setup and split
- path representation
- global atlas
- univariate slices
- path archetypes
- holdout replication verdicts
- execution implications

### 2. Structured atlas tables

Reusable tables for:

- global first-passage matrix
- event-ordering summaries
- per-feature per-bin path summaries
- archetype summaries
- discovery vs holdout comparison

### 3. Interpretable cohort and archetype definitions

All bins, archetypes, and explanation rules must be explicitly serializable or reproducible from the code and report.

### 4. Replication verdict sheet

A compact summary of which atlas claims:

- replicated;
- stayed directionally consistent;
- failed;
- remained exploratory.

### 5. Next-step recommendation

A short decision-support summary stating whether the validated atlas supports:

- future `market` research;
- future `pullback` research;
- both;
- neither.

## Success criteria

- The project ends the stage with a reproducible ATR-normalized path atlas, not just another list of PF winners.
- The report identifies which conditioning features actually change path geometry or event ordering.
- The holdout pass validates at least some path claims without turning into a second discovery loop.
- The stage produces decision-support evidence for the next execution-focused research step.

## Failure modes to avoid

- Hidden rule search disguised as atlas work
- Tuning bins or archetypes on holdout
- Using thin tails as primary evidence
- Returning to fixed `SL/TP` optimization too early
- Letting mean path alone drive conclusions

## Related materials

- [docs/reports/2026-04-01-signal-research-variant-2.md](../../reports/2026-04-01-signal-research-variant-2.md)
- [docs/reports/2026-04-02-signal-research-variant-3-prep.md](../../reports/2026-04-02-signal-research-variant-3-prep.md)
- [docs/reports/2026-04-02-signal-research-variant-3.md](../../reports/2026-04-02-signal-research-variant-3.md)
- [docs/superpowers/specs/2026-04-03-signal-quality-filter-design.md](2026-04-03-signal-quality-filter-design.md)
