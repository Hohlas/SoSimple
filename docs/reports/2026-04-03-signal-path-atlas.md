# Signal Path Atlas Stage

> **Date**: 2026-04-03
> **Status**: Completed
> **Goal**: Build and verify a standalone Python path-atlas tool that describes post-signal price geometry in ATR-normalized discovery/holdout space without returning to direct PF rule search.
> **Related plan/spec**: `docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md`, `docs/superpowers/plans/2026-04-03-signal-path-atlas.md`
> **Related commit**: pending

## Context

Variant 2 and Variant 3 established that the current signal is better described as weak drift with selective continuation than as a clean impulse edge. Variant 3 robustness left one narrow execution candidate alive, but its support remained too low for a comfortable transportable conclusion. The next stage therefore changed the research object: instead of searching for the next PF winner in Python, the project moved to a conditional path atlas that describes post-signal geometry first and postpones execution choice to a later step.

## What Was Done

- Added a new standalone research entry point: `API/signal_path_atlas.py`
- Implemented the fixed calendar split:
  - `discovery <= 2024-12-31 23:59:59`
  - `holdout >= 2025-01-01 00:00:00`
- Built a direction-aware ATR-normalized path tensor on `1..12` bars:
  - `signed_ret_h`
  - `fav_h`
  - `adv_h`
  - first-passage and ordering features
- Added discovery-only conditioning features and feature screen:
  - `ratio_h`
  - `spread_h`
  - short-vs-long derived ratios/spreads
  - fixed cohorts `signal_label`, `ratio_bin_12`, `atr_bucket`
- Added discovery atlas outputs:
  - global path quantiles
  - first-passage atlas
  - ordering atlas
  - numeric and categorical slices
  - path archetypes
- Added holdout replication layer with structured verdicts:
  - `Replicated`
  - `Directionally consistent`
  - `Failed`
  - `Exploratory`
- Hardened the implementation after review:
  - froze ATR bucket edges on discovery only to avoid holdout leakage
  - kept zero-support discovery archetypes in holdout verdicts
  - removed the `main()` crash path when no live numeric features survive screening
  - made numeric holdout slice membership interval-aware so repeated bin boundaries do not double-count rows
  - made collapsed/role-collision archetype naming deterministic and neutral
  - surfaced the full atlas report/export surface instead of only partial tables

## Changed Files

- `API/signal_path_atlas.py`
- `tests/test_signal_path_atlas.py`
- `API/README.md`
- `docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md`
- `docs/superpowers/plans/2026-04-03-signal-path-atlas.md`

## Verification

- `./.venv/bin/python -m pytest tests/test_signal_path_atlas.py -q`
  - result: `38 passed`
- `./.venv/bin/python -m API.signal_path_atlas --test-only`
  - result: completed successfully
- `rm -rf /tmp/signal_path_atlas && ./.venv/bin/python -m API.signal_path_atlas --test-only --export-dir /tmp/signal_path_atlas`
  - result: completed successfully
- Final export set written by the CLI:
  - `split_summary.csv`
  - `feature_screen.csv`
  - `path_quantiles.csv`
  - `first_passage.csv`
  - `ordering.csv`
  - `numeric_slices.csv`
  - `categorical_slices.csv`
  - `archetype_summary.csv`
  - `holdout_verdicts.csv`
  - `execution_implications.csv`

## Results

- The project now has a dedicated path-atlas CLI instead of extending `API/signal_research.py` further.
- The atlas contract is now explicit and reproducible:
  - discovery artifacts are frozen before holdout replication
  - holdout is no longer allowed to leak into ATR bucket construction
  - replication verdicts are produced for numeric slices, fixed cohorts, and archetypes
- On the current `--test-only` verification run, the split produced:
  - `discovery = 1752`
  - `holdout = 851`
- The current atlas smoke run shows two surviving reported archetype families on discovery:
  - `failure_or_adverse_continuation`
  - `flat_or_noisy_drift`
- The current holdout verdict surface no longer implies an immediate execution recommendation:
  - `execution_implications = neither`

## Conclusions

This stage successfully moved the project away from direct PF winner search and into a reusable path-atlas workflow. The core result is not a new EA rule but a verified research tool that can describe path geometry, freeze discovery artifacts, and check whether those effects replicate on holdout. That is the right methodological base for any later `market` or `pullback` decision.

The most important practical change versus the previous handoff is conceptual: the next Python step is no longer a narrow robustness pass around the old locked winner. The new default path is to use the atlas outputs to identify which path claims are actually replicated, and only then derive downstream execution hypotheses.

## Limitations / Open Questions

- `API/signal_path_atlas.py` is already a fairly large single-file research tool; maintainability is still acceptable, but future growth should likely split orchestration from analysis helpers.
- The shallow explanation tree is fitted but not yet surfaced as a first-class report/export artifact.
- Current verification used the documented `--test-only` path. That is sufficient for the stage close, but the next analytical pass should read the atlas outputs directly and convert them into a canonical human research summary.
- The current execution implication result is `neither`, which means the atlas layer is now built, but the research interpretation layer is still ahead of us.

## Next Step

Use the new atlas tooling to produce the first canonical path-atlas research readout from the frozen tables:

- review global path quantiles, first-passage, and ordering as the primary signal description;
- identify only the path claims that clearly replicate on holdout;
- decide whether any replicated cohort/archetype evidence supports a future `market` or `pullback` execution track;
- keep the old Variant 3 locked winner only as a benchmark, not as the main driver of the next stage.

## Related Materials

- `docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md`
- `docs/superpowers/plans/2026-04-03-signal-path-atlas.md`
- `docs/reports/2026-04-02-signal-research-variant-3.md`
- `docs/reports/2026-04-02-signal-research-variant-3-prep.md`
- `docs/reports/2026-04-01-signal-research-variant-2.md`
- `API/signal_path_atlas.py`
- `tests/test_signal_path_atlas.py`
