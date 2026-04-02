# Signal Research Variant 3 Prep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `API/signal_research.py` so it can identify strong `ex-ante` signal cohorts, measure entry opportunities before Variant 3, and consume canonical `atr14` from `DATA/XAUUSD_H1_OHLC.csv`.

**Architecture:** Keep `API/signal_research.py` as the single research entry point, but split the new work into small pure helpers. First, make ATR loading deterministic by preferring the exported `atr14` column and only falling back to Python ATR for legacy files. Second, annotate each signal with the best base-horizon barrier outcome once and reuse that enriched frame for cohort tables, entry-opportunity tables, and stability splits. Third, print a short priority shortlist so Variant 3 can start from selected cohorts instead of the full signal pool.

**Tech Stack:** Python 3.11+, pandas, NumPy, pytest, canonical OHLC CSV exported from MT4

---

## Constraints

- Do not modify EA trading logic in this plan.
- Do not retrain the model.
- Do not implement the full Variant 3 execution simulator here.
- Keep `signal_research.py` readable: add helpers instead of piling more logic into `main()`.
- Do not add git commit steps: this repository is operated with manual git control unless the user explicitly asks for a commit.

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `API/signal_research.py` | Modify | Prefer canonical `atr14`, build cohort/entry/stability tables, and print Variant 3 prep sections |
| `tests/test_signal_research.py` | Modify | Lock down ATR source selection, cohort summaries, entry-opportunity math, and new report smoke coverage |
| `docs/superpowers/specs/2026-04-02-signal-research-variant-3-prep-design.md` | Read | Approved scope and expected output for this stage |

## Current File Map

- `API/signal_research.py:46-90` loads `ml_signals.csv` and `XAUUSD_H1_OHLC.csv`, currently recomputing `atr14` in Python.
- `API/signal_research.py:103-252` builds the enriched excursion frame and ratio / ATR buckets.
- `API/signal_research.py:439-736` prints Variant 2 report sections.
- `tests/test_signal_research.py` already covers ATR math, excursion aliases, barrier ordering, and Variant 2 report smoke tests.

The plan keeps the script single-file, but adds a reusable “best setup annotation + grouped summaries” layer so the new sections do not duplicate barrier logic.

---

### Task 1: Add failing tests for canonical ATR loading and cohort summaries

**Files:**
- Modify: `tests/test_signal_research.py`
- Read: `API/signal_research.py:46-252`

- [ ] **Step 1: Add tests that lock ATR source selection**

Append focused tests that prove `load_data()` prefers CSV `atr14` and only falls back when the column is missing:

```python
def test_load_data_prefers_atr14_column_from_csv(monkeypatch, tmp_path):
    signals = tmp_path / 'signals.csv'
    ohlc = tmp_path / 'ohlc.csv'

    signals.write_text(
        "time;signal;up_3;dn_3;up_6;dn_6;up_12;dn_12;up_24;dn_24;up_48;dn_48\n"
        "2026-01-01 00:00:00;1;0.3;0.1;0.4;0.2;0.5;0.2;0.6;0.3;0.7;0.4\n",
        encoding='utf-8',
    )
    ohlc.write_text(
        "time;open;high;low;close;volume;atr14\n"
        "2026-01-01 00:00:00;100;101;99;100;10;7.5\n",
        encoding='utf-8',
    )

    monkeypatch.setattr(sr, 'SIGNALS_FILE', signals)
    monkeypatch.setattr(sr, 'OHLC_FILE', ohlc)

    df, merged_ohlc = sr.load_data()

    assert df.loc[0, 'atr14'] == pytest.approx(7.5, abs=1e-9)
    assert merged_ohlc.loc[0, 'atr14'] == pytest.approx(7.5, abs=1e-9)


def test_load_data_falls_back_to_python_atr_when_csv_has_no_atr14(monkeypatch, tmp_path):
    signals = tmp_path / 'signals.csv'
    ohlc = tmp_path / 'ohlc.csv'

    signals.write_text(
        "time;signal;up_3;dn_3;up_6;dn_6;up_12;dn_12;up_24;dn_24;up_48;dn_48\n"
        "2026-01-01 13:00:00;1;0.3;0.1;0.4;0.2;0.5;0.2;0.6;0.3;0.7;0.4\n",
        encoding='utf-8',
    )

    rows = ["time;open;high;low;close;volume"]
    for i in range(16):
        rows.append(f"2026-01-01 {i:02d}:00:00;100;102;100;101;10")
    ohlc.write_text("\n".join(rows) + "\n", encoding='utf-8')

    monkeypatch.setattr(sr, 'SIGNALS_FILE', signals)
    monkeypatch.setattr(sr, 'OHLC_FILE', ohlc)

    df, merged_ohlc = sr.load_data()

    assert 'atr14' in merged_ohlc.columns
    assert df.loc[0, 'atr14'] == pytest.approx(2.0, abs=1e-9)
```

- [ ] **Step 2: Add tests for cohort and entry-opportunity helpers**

Add focused unit tests for the helpers introduced in later tasks:

```python
def test_summarize_signal_groups_returns_best_outcome_shares_and_pf():
    frame = pd.DataFrame([
        {'cohort': 'A', 'net_12': 4.0, 'mfe_12': 8.0, 'mae_12': 2.0, 'best_outcome': 'TP_FIRST', 'best_pnl': 10.0},
        {'cohort': 'A', 'net_12': -2.0, 'mfe_12': 5.0, 'mae_12': 4.0, 'best_outcome': 'SL_FIRST', 'best_pnl': -5.0},
        {'cohort': 'B', 'net_12': 3.0, 'mfe_12': 6.0, 'mae_12': 2.0, 'best_outcome': 'NEITHER', 'best_pnl': 3.0},
    ])

    summary = sr.summarize_signal_groups(frame, ['cohort'])

    row_a = summary[summary['cohort'] == 'A'].iloc[0]
    assert row_a['N'] == 2
    assert row_a['PF_12'] == pytest.approx(2.0, abs=1e-9)
    assert row_a['TP_FIRST_pct'] == pytest.approx(50.0, abs=1e-9)
    assert row_a['SL_FIRST_pct'] == pytest.approx(50.0, abs=1e-9)


def test_build_entry_opportunity_profile_counts_pullback_and_favorable_levels():
    frame = pd.DataFrame([
        {'time': pd.Timestamp('2026-01-01 00:00'), 'cohort': 'A', 'signal': 1, 'adv_1': 3.0, 'adv_3': 5.0, 'adv_6': 8.0,
         'fav_1': 2.0, 'fav_3': 12.0, 'fav_6': 25.0, 'close_net_1': 1.0, 'close_net_3': 4.0, 'close_net_6': 7.0},
        {'time': pd.Timestamp('2026-01-01 01:00'), 'cohort': 'A', 'signal': 1, 'adv_1': 0.0, 'adv_3': 2.0, 'adv_6': 3.0,
         'fav_1': 1.0, 'fav_3': 8.0, 'fav_6': 15.0, 'close_net_1': -1.0, 'close_net_3': 2.0, 'close_net_6': 4.0},
    ])

    table = sr.build_entry_opportunity_profile(frame, 'cohort', ['A'])
    row = table.iloc[0]

    assert row['pullback>=3_1H'] == pytest.approx(50.0, abs=1e-9)
    assert row['pullback>=5_3H'] == pytest.approx(50.0, abs=1e-9)
    assert row['fav>=20_6H'] == pytest.approx(50.0, abs=1e-9)
```

- [ ] **Step 3: Add a smoke test for the new report sections**

Extend the existing smoke coverage so the final CLI report must include the new section headers:

```python
    sr.report_cohort_map(exc, barriers, barrier_outcomes)
    sr.report_entry_opportunities(exc)
    sr.report_stability_splits(exc, barriers, barrier_outcomes)
    sr.report_priority_cohorts(exc, barriers, barrier_outcomes)

    out = capsys.readouterr().out
    assert 'Cohort Map' in out
    assert 'Entry Opportunity Profile' in out
    assert 'Stability Split' in out
    assert 'Priority Cohorts' in out
```

- [ ] **Step 4: Run the tests and confirm they fail for the missing behavior**

Run:

```bash
cd /home/hohla/git/SoSimple && .venv/bin/python -m pytest tests/test_signal_research.py -q
```

Expected:
- failures for missing/new helper functions,
- or failures because `load_data()` does not yet distinguish CSV `atr14` from fallback ATR.

---

### Task 2: Prefer canonical `atr14` in `load_data()` and update the file header

**Files:**
- Modify: `API/signal_research.py`
- Test: `tests/test_signal_research.py`

- [ ] **Step 1: Update the module header/docstring to mention canonical `atr14` and Variant 3 prep**

Adjust the header and docstring near the top of `API/signal_research.py` so they describe both the existing Variant 2 blocks and the new Variant 3 prep blocks:

```python
# Назначение: Variant 2 + Variant 3 prep исследование качества ML-сигналов по реальным OHLC

"""
Исследование: как ведёт себя цена после каждого ML-сигнала.

Variant 2 отчёт строит базовые path-dependent таблицы.
Variant 3 prep добавляет:
1. Cohort Map по ex-ante подгруппам
2. Entry Opportunity Profile
3. Stability Split для лучших когорт
4. Priority Cohorts shortlist

Если в OHLC CSV уже есть `atr14`, используется каноническое значение из MT4.
Если колонки нет, ATR(14) временно досчитывается в Python как fallback.
"""
```

- [ ] **Step 2: Change `load_data()` so CSV `atr14` wins and Python ATR is fallback-only**

Replace the current unconditional ATR overwrite with this pattern:

```python
def load_data(test_only: bool = False):
    sig = pd.read_csv(SIGNALS_FILE, sep=';', parse_dates=['time'])
    ohlc = pd.read_csv(OHLC_FILE, sep=';', parse_dates=['time'])

    ohlc.sort_values('time', inplace=True)
    ohlc.reset_index(drop=True, inplace=True)

    if 'atr14' not in ohlc.columns:
        ohlc['atr14'] = compute_atr14(ohlc)
    else:
        ohlc['atr14'] = pd.to_numeric(ohlc['atr14'], errors='coerce')

    df = sig.merge(
        ohlc[['time', 'open', 'high', 'low', 'close', 'atr14']],
        on='time',
        how='inner',
    )
```

- [ ] **Step 3: Re-run the focused ATR-source tests**

Run:

```bash
cd /home/hohla/git/SoSimple && .venv/bin/python -m pytest tests/test_signal_research.py -q -k "load_data_prefers_atr14 or load_data_falls_back"
```

Expected:
- both ATR-source tests pass,
- other new tests still fail because cohort helpers are not implemented yet.

---

### Task 3: Add a reusable best-setup annotation and generic cohort summarizer

**Files:**
- Modify: `API/signal_research.py`
- Test: `tests/test_signal_research.py`

- [ ] **Step 1: Add a helper that attaches the best base-horizon setup to each signal**

Create a single helper that selects the best base setup and merges its outcome into the excursion frame:

```python
def attach_best_setup_outcomes(exc: pd.DataFrame, barrier_outcomes: pd.DataFrame, barrier_summary: pd.DataFrame):
    best = _select_base_barrier_setups(barrier_summary, top_n=1)
    if best.empty:
        frame = exc.copy()
        frame['best_outcome'] = pd.NA
        frame['best_pnl'] = np.nan
        frame['best_setup'] = 'n/a'
        return frame

    row = best.iloc[0]
    label = f"H{int(row['horizon'])} SL={int(row['SL'])} TP={int(row['TP'])}"
    outcome = barrier_outcomes[
        (barrier_outcomes['horizon'] == row['horizon']) &
        (barrier_outcomes['SL'] == row['SL']) &
        (barrier_outcomes['TP'] == row['TP'])
    ][['time', 'outcome', 'pnl']].rename(columns={'outcome': 'best_outcome', 'pnl': 'best_pnl'})

    merged = exc.merge(outcome, on='time', how='left')
    merged['best_setup'] = label
    return merged
```

- [ ] **Step 2: Add a generic grouped summary helper for ex-ante cohorts**

Implement one reusable summarizer rather than hardcoding each cohort table separately:

```python
def summarize_signal_groups(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    grouped = frame.groupby(group_cols, dropna=False)

    for keys, sub in grouped:
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = {col: value for col, value in zip(group_cols, keys)}
        outcome = sub['best_outcome'].dropna()

        row.update({
            'N': len(sub),
            'Net_12_mean': sub['net_12'].mean(),
            'Net_12_median': sub['net_12'].median(),
            'PF_12': _profit_factor(sub['net_12'].dropna()),
            'MFE_12_mean': sub['mfe_12'].mean(),
            'MAE_12_mean': sub['mae_12'].mean(),
            'TP_FIRST_pct': (outcome == 'TP_FIRST').mean() * 100 if len(outcome) else np.nan,
            'SL_FIRST_pct': (outcome == 'SL_FIRST').mean() * 100 if len(outcome) else np.nan,
            'NEITHER_pct': (outcome == 'NEITHER').mean() * 100 if len(outcome) else np.nan,
            'AvgPnL_best': sub['best_pnl'].mean(),
        })
        rows.append(row)

    return pd.DataFrame(rows)
```

- [ ] **Step 3: Run the focused cohort-summary tests**

Run:

```bash
cd /home/hohla/git/SoSimple && .venv/bin/python -m pytest tests/test_signal_research.py -q -k "summarize_signal_groups"
```

Expected:
- the grouped-summary test passes,
- entry-opportunity and report smoke tests still fail until later tasks are implemented.

---

### Task 4: Implement `Cohort Map` and `Entry Opportunity Profile`

**Files:**
- Modify: `API/signal_research.py`
- Test: `tests/test_signal_research.py`

- [ ] **Step 1: Implement `report_cohort_map()` using the reusable summarizer**

Add a new reporting block that builds the required ex-ante slices:

```python
def report_cohort_map(exc: pd.DataFrame, barrier_summary: pd.DataFrame, barrier_outcomes: pd.DataFrame):
    print_separator("Cohort Map")

    enriched = attach_best_setup_outcomes(exc, barrier_outcomes, barrier_summary)
    enriched = enriched.copy()
    enriched['side'] = np.where(enriched['signal'] == 1, 'BUY', 'SELL')
    enriched['atr_regime'] = np.where(enriched['atr_bucket'] == 'Q4', 'Q4', 'non-Q4')

    specs = [
        ('BUY/SELL × ratio_12', ['side', 'ratio_bin']),
        ('BUY/SELL × atr_bucket', ['side', 'atr_bucket']),
        ('ratio_12 × atr_bucket', ['ratio_bin', 'atr_bucket']),
        ('ratio_12 × atr_regime', ['ratio_bin', 'atr_regime']),
    ]

    for title, cols in specs:
        print(f"\\n  [{title}]")
        table = summarize_signal_groups(enriched.dropna(subset=['net_12']), cols)
        print(table.to_string(index=False))
```

- [ ] **Step 2: Implement `build_entry_opportunity_profile()` and `report_entry_opportunities()`**

Create a helper that measures pullback/favorable thresholds inside `1H / 3H / 6H`:

```python
def build_entry_opportunity_profile(frame: pd.DataFrame, group_col: str, group_values: list[str]) -> pd.DataFrame:
    rows = []
    thresholds_pullback = [3, 5, 8]
    thresholds_fav = [10, 20, 30]
    windows = [1, 3, 6]

    for value in group_values:
        sub = frame[frame[group_col] == value]
        row = {group_col: value, 'N': len(sub)}
        for w in windows:
            for level in thresholds_pullback:
                row[f'pullback>={level}_{w}H'] = (sub[f'adv_{w}'] >= level).mean() * 100 if len(sub) else np.nan
            for level in thresholds_fav:
                row[f'fav>={level}_{w}H'] = (sub[f'fav_{w}'] >= level).mean() * 100 if len(sub) else np.nan
            row[f'close>0_{w}H'] = (sub[f'close_net_{w}'] > 0).mean() * 100 if len(sub) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def report_entry_opportunities(exc: pd.DataFrame):
    print_separator("Entry Opportunity Profile")

    priority = exc.copy()
    priority['priority_cohort'] = np.where(
        (priority['ratio_bin'] == '4-5') & (priority['atr_bucket'] == 'Q4'),
        '4-5×Q4',
        np.where(priority['ratio_bin'].isin(['3-4', '4-5', '5+']), priority['ratio_bin'].astype(str), 'other')
    )

    values = [value for value in ['3-4', '4-5', '5+', '4-5×Q4', 'other'] if (priority['priority_cohort'] == value).any()]
    table = build_entry_opportunity_profile(priority, 'priority_cohort', values)
    print(table.to_string(index=False))
```

- [ ] **Step 3: Run the focused tests for entry-opportunity math and report smoke**

Run:

```bash
cd /home/hohla/git/SoSimple && .venv/bin/python -m pytest tests/test_signal_research.py -q -k "entry_opportunity or variant2_reports_smoke"
```

Expected:
- the new entry-opportunity helper test passes,
- the smoke test now includes `Cohort Map` and `Entry Opportunity Profile`,
- stability/priority sections may still be missing.

---

### Task 5: Add `Stability Split`, `Priority Cohorts`, and wire the final CLI flow

**Files:**
- Modify: `API/signal_research.py`
- Test: `tests/test_signal_research.py`

- [ ] **Step 1: Implement `report_stability_splits()`**

Add a lightweight stability table using calendar-year buckets on the enriched best-setup frame:

```python
def report_stability_splits(exc: pd.DataFrame, barrier_summary: pd.DataFrame, barrier_outcomes: pd.DataFrame):
    print_separator("Stability Split")

    enriched = attach_best_setup_outcomes(exc, barrier_outcomes, barrier_summary)
    enriched = enriched.copy()
    enriched['year'] = pd.to_datetime(enriched['time']).dt.year.astype(str)
    enriched['side'] = np.where(enriched['signal'] == 1, 'BUY', 'SELL')

    shortlist = enriched[enriched['ratio_bin'].isin(['4-5', '5+']) | (enriched['atr_bucket'] == 'Q4')]
    if shortlist.empty:
        print("  No shortlist rows available.")
        return

    table = summarize_signal_groups(shortlist.dropna(subset=['net_12']), ['year', 'side', 'ratio_bin'])
    print(table.to_string(index=False))
```

- [ ] **Step 2: Implement `report_priority_cohorts()`**

Build a compact shortlist for Variant 3 from the grouped summaries:

```python
def report_priority_cohorts(exc: pd.DataFrame, barrier_summary: pd.DataFrame, barrier_outcomes: pd.DataFrame):
    print_separator("Priority Cohorts")

    enriched = attach_best_setup_outcomes(exc, barrier_outcomes, barrier_summary)
    enriched = enriched.copy()
    enriched['side'] = np.where(enriched['signal'] == 1, 'BUY', 'SELL')
    enriched['atr_regime'] = np.where(enriched['atr_bucket'] == 'Q4', 'Q4', 'non-Q4')

    base = summarize_signal_groups(
        enriched.dropna(subset=['net_12']),
        ['side', 'ratio_bin', 'atr_regime'],
    )

    base = base[base['N'] >= 25].copy()
    if base.empty:
        print("  No cohorts with sufficient sample size.")
        return

    best = base.sort_values(['PF_12', 'AvgPnL_best', 'N'], ascending=[False, False, False]).head(5)
    worst = base.sort_values(['PF_12', 'AvgPnL_best', 'N'], ascending=[True, True, False]).head(3)

    print("\\n  [Best candidates]")
    print(best.to_string(index=False))
    print("\\n  [Anti-pattern cohorts]")
    print(worst.to_string(index=False))
```

- [ ] **Step 3: Wire the new sections into `main()` after the existing Variant 2 blocks**

Extend the CLI flow at the bottom:

```python
    report_signal_passport(exc)
    report_by_ratio(exc)
    report_pullback_profile(exc)
    report_first_hit_barriers(barrier_summary)
    report_amplitude_filters(exc, barrier_outcomes, barrier_summary)
    report_regime_splits(exc, barrier_outcomes, barrier_summary)
    report_prediction_vs_reality(exc)
    report_cohort_map(exc, barrier_summary, barrier_outcomes)
    report_entry_opportunities(exc)
    report_stability_splits(exc, barrier_summary, barrier_outcomes)
    report_priority_cohorts(exc, barrier_summary, barrier_outcomes)
    print_practical_conclusions(exc, barrier_summary)
```

- [ ] **Step 4: Run the full test file**

Run:

```bash
cd /home/hohla/git/SoSimple && .venv/bin/python -m pytest tests/test_signal_research.py -q
```

Expected:
- all tests pass,
- smoke coverage includes the new Variant 3 prep sections.

---

### Task 6: Run the real OOS report and capture what changed

**Files:**
- Modify: `API/signal_research.py` (only if verification reveals formatting/edge-case issues)
- Read: `DATA/XAUUSD_H1_OHLC.csv`

- [ ] **Step 1: Run the full OOS report against the updated OHLC CSV**

Run:

```bash
cd /home/hohla/git/SoSimple && .venv/bin/python -m API.signal_research --test-only
```

Expected:
- the report runs without crashing,
- `atr14` is read from `DATA/XAUUSD_H1_OHLC.csv`,
- the output includes `Cohort Map`, `Entry Opportunity Profile`, `Stability Split`, and `Priority Cohorts`.

- [ ] **Step 2: Sanity-check the output for actionable Variant 3 inputs**

Review the output and confirm:

```text
1. there is at least one cohort shortlist for Variant 3,
2. `ratio_12 = 4-5` and `ATR Q4` are still visible as separate or combined candidates,
3. weak cohorts remain visible as anti-patterns rather than disappearing from the report,
4. no section silently degenerates into a single giant “ALL” bucket.
```

- [ ] **Step 3: If the report is clean, stop at research output**

Do not move on to EA changes or Variant 3 simulator code inside this plan.

The handoff after execution should be:
- updated `signal_research.py`,
- passing tests,
- one fresh OOS report run,
- a clear shortlist of cohorts to use in the next `Variant 3` plan.
