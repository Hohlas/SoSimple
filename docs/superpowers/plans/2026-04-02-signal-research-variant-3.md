# Signal Research Variant 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add full Variant 3 entry-scenario research to `API/signal_research.py` with `market`, `pullback`, `delayed`, and `cancel-window` comparisons on the shortlisted cohorts and negative controls.

**Architecture:** Keep `API/signal_research.py` as the single research entry point. Extend the data-enrichment layer with `pic_price` from raw `Nero.csv` by extracting the latest fractal per row via embedded fractal-time ordering, mirror `generate_signals.py` dedupe by `time`, add a small scenario-simulation layer for delayed and limit-entry policies, and build report helpers that summarize scenario outcomes by cohort without disturbing the existing Variant 2 / Prep sections.

**Tech Stack:** Python 3.11+, pandas, NumPy, pytest, OHLC CSV, raw Nero feature CSV

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `API/signal_research.py` | Modify | Load `pic_price`, simulate Variant 3 scenarios, summarize outputs, print new report sections |
| `tests/test_signal_research.py` | Modify | Lock down `pic_price` parsing, scenario fill logic, scenario summaries, and report smoke coverage |
| `docs/superpowers/specs/2026-04-02-signal-research-variant-3-design.md` | Read | Approved execution research design |

## Tasks

### Task 1: Add failing tests for Variant 3 scenario simulation

- [ ] Write unit tests for `pic_price` extraction from the latest embedded fractal in a raw row.
- [ ] Write unit tests for limit-order fill logic on `BUY` and `SELL`.
- [ ] Write unit tests for `market`, `delayed`, `pullback`, and `cancel-window` outcomes on a compact OHLC fixture.
- [ ] Add smoke coverage for the new Variant 3 report sections.
- [ ] Run `pytest tests/test_signal_research.py -q` and confirm the new expectations fail before production changes.

### Task 2: Load `pic_price` and implement reusable scenario helpers

- [ ] Add raw-data loading that reads `time` plus `fractal*` columns from `Nero.csv`.
- [ ] Extract the latest fractal `price` per row via embedded fractal-time ordering and merge it into the research dataframe as `pic_price`.
- [ ] Add helpers for pending-limit fills, delayed fills, and common-deadline outcome evaluation.
- [ ] Keep the fixed baseline `12H / SL=5 / TP=50`.

### Task 3: Build Variant 3 summaries and report sections

- [ ] Define the Variant 3 scenario grid:
  - `market`
  - `delayed: delay=1,3`
  - `pullback: entry_close +/- ATR14*k, k=1,2,3`
  - `pullback: pic_price, pic_price+ATR14, pic_price-ATR14`
  - `cancel-window`: same pullback levels with expiries `1,3,6`
- [ ] Summarize outcomes by `cohort x scenario x params`.
- [ ] Print the three new report sections:
  - `Variant 3 Scenario Matrix`
  - `Variant 3 Shortlist Verdict`
  - `Variant 3 Negative Controls`

### Task 4: Verify end to end

- [ ] Run `pytest tests/test_signal_research.py -q`.
- [ ] Run `python -m API.signal_research --test-only`.
- [ ] Check that the new sections appear and that primary cohorts plus negative controls are all represented.
