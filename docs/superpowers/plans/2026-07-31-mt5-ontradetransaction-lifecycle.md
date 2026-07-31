# MT5 OnTradeTransaction Lifecycle Closure Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the trade-event lifecycle of the MT5 diagnostic executor: log every open/close through native `OnTradeTransaction` events, re-run the same single-rule tester scenario, classify all 252 opens from the 2026-07-30 run pattern (closed / open-at-end / unexplained), and resolve `same_h1_lifecycle_status`.

**Architecture:** Keep the existing H1-polling lifecycle (`MT5_LogLifecycleForCurrentState`) untouched and add a parallel, independent transaction-event stream from `OnTradeTransaction`. Both streams write into the same event CSV with distinct event names, so one run yields a built-in cross-check: old polling (18 CLOSE observed) vs native transactions (expected full coverage). Python parser and schema learn the new event types; a reconciliation step classifies every opened position.

**Tech Stack:** MQL5 (`OnTradeTransaction`, `MqlTradeTransaction`), MetaEditor 5 + MT5 Strategy Tester under Wine/xvfb, Python 3 via `./.venv/bin/python`, pandas, pytest.

```text
depends_on: docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md; docs/superpowers/plans/2026-07-30-mt5-single-rule-diagnostic-run.md
blocks: MT5 Nero.csv parity check; ERROR-4756 classification; MT5 batch selection for 20-50 candidates
supersedes: none
exit_decisions: continue | close | unblock
locked_test_policy: not used; no winner/threshold/rule/cost/entry/exit/stop selection by tester results
```

## Global Constraints

- Same entry CSV as the 2026-07-30 run: `ML/reports/mt5_execution_loop/mt5_entry_signals_20260730_entry_quality_filter.csv`, sha256 `0b30fc5b6e8da9b2460ed1c21f9203b51b53852bfee531a08c62b33caecf9900`. Do not regenerate or reselect signals.
- Same tester scenario: XAUUSD, H1, 2019.06.20–2022.12.03, Model 1 (1 minute OHLC), same `.set` profile except a new `InpMT5_EventFile` name is allowed.
- All results are `DIAGNOSTIC_ONLY`. No PnL/PF/profitability claims. `profit_sum`-style aggregates must carry the same guard wording as the 2026-07-30 report.
- Do not modify entry rule, signal preparation scripts, or `prepare_mt5_entry_source.py`.
- Do not remove or alter the existing H1-polling lifecycle logic in this plan; it is the comparison baseline.
- Run only targeted tests: `tests/test_parse_mt5_execution_report.py`, `tests/test_mt5_signal_executor_schema.py` (plus any new test files added by this plan).
- No `git push`. Commit only when the user explicitly asks.

## Methodology Map

- `docs/methodology/13b-mt5-execution-parity.md`: primary. Required: compile from git source with saved log, record tester metadata, classify all execution discrepancies.
- `docs/methodology/03-feature-contract-leakage.md`: general principle only — features must be available at decision time. The actual 4-link timing contract `feature_time <= feature_available_time <= decision_time <= execution_time` is defined by `validate_mt5_event_frame` in `ML/baseline/mt5_signal_schema.py` (and verified in the 2026-07-30 report); methodology 13b states the shorter 3-link form. TX rows without a known signal index must leave timing fields empty rather than fabricate them.
- `docs/methodology/16-reporting-audit.md`: report must record commands, hashes, limitations, verdict; structured artifact (manifest) must carry key numbers.

## Design Decisions (fixed before implementation)

1. **New event names:** `TX_OPEN` (deal entry IN), `TX_CLOSE` (deal entry OUT/OUT_BY). Logged from `OnTradeTransaction` on `TRADE_TRANSACTION_DEAL_ADD` only. Same 46-column event CSV schema (writer `MT5_ML_LogEvent`: 27 args + auto-filled market columns); unused ML columns: `bars_since_fill=-1` (INIT convention, since `0` is a meaningful value), other unused numeric fields zero, strings empty. `DEAL_ENTRY_INOUT` (reversal) is expected impossible in this executor (one position at a time, limit entries only); if observed — log it as both TX_CLOSE of the old position and TX_OPEN of the new one, and record the finding in the report.
2. **Identity:** each TX row records deal ticket in the `ticket` column and position id in the `comment` (`position_id=<id>|deal=<ticket>|reason=<deal_reason>` — internal separator `|`, never `;`, because the event CSV delimiter is `;` and MQL5 `FileWrite` does not quote strings). Signal linkage is NOT attempted at write time (at deal time the H1-polling tracker has usually not yet observed the ticket): TX rows leave timing fields empty; linkage position id → signal index is done in Python reconciliation (join via tracked OPEN rows / order open time).
3. **Close reason:** taken from `DEAL_REASON_*` enum of the deal (`SL`, `TP`, `EXPERT`, etc.) and written to the `close_reason` column — replaces the old `broker_history_limited` placeholder for TX rows.
4. **Handler location:** `OnTradeTransaction` added to `MT/MQL5/Experts/$o$imple.mq5`, guarded by `MT5_DiagnosticExecutor == true`; body implemented in `MT/MQL5/Include/lib_ML_Signal.mqh` (`MT5_OnTradeTransaction(...)`).
5. **Reconciliation classes** (per opened position id): `CLOSED_TX` (TX_CLOSE observed), `OPEN_AT_END` (no TX_CLOSE, position open at test end), `UNEXPLAINED` (neither). Success requires `UNEXPLAINED == 0` or each remainder listed row-by-row.
6. **same_h1_lifecycle_status:** resolved by counting positions whose TX_OPEN and TX_CLOSE fall within the same H1 bar; status becomes `MEASURED:<count>` in the report and manifest.

## Known Unknowns / Risks

- LiveUpdate loop may return if the terminal re-downloads build 6070+; mitigation: re-check `liveupdate/` dir before launch, move payload out again if present.
- Tester in hedging mode: position id vs order ticket mapping must be verified on real transaction data, not assumed.
- `OnTradeTransaction` behavior under Model 1 (1-minute OHLC) in the tester is documented but not yet observed in this environment; Task 3 verifies on a short date range first.
- Event CSV grows (extra TX rows + ML_EVAL 1915); parser memory is fine at this scale.

---

## Task 1: MQL5 — Transaction Logging

**Files:**
- Edit: `MT/MQL5/Include/lib_ML_Signal.mqh` (add `MT5_OnTradeTransaction`, position-id→signal-index map)
- Edit: `MT/MQL5/Experts/$o$imple.mq5` (add `OnTradeTransaction` handler, new input default `InpMT5_EventFile` unchanged)

**Steps:**
- [x] Add position-id→signal-index registration where `MT5_TrackedTicket` is assigned (used by Python reconciliation via OPEN rows; TX rows themselves do not carry signal timing — Design Decision 2).
- [x] Implement `MT5_OnTradeTransaction`: on `TRADE_TRANSACTION_DEAL_ADD`, select deal from history, log `TX_OPEN`/`TX_CLOSE` per Design Decision 1–3.
- [x] Guard: no-op unless diagnostic executor is on.
- [x] Compile headless per methodology 13b command (absolute unix paths via wine). Known fallback if the log is not produced (observed 2026-07-31 with Windows-style absolute paths containing spaces): run MetaEditor from the terminal directory (`drive_c/Program Files/MetaTrader 5`) with relative `/compile:"MQL5\..."` and `/log:"MQL5\..."` paths. Save UTF-8 log to `ML/reports/mt5_execution_loop/`; verdict must be `0 errors`.

## Task 2: Python — Schema And Parser Support

**Files:**
- Edit: `ML/baseline/mt5_signal_schema.py` (NEW check: explicit event-name whitelist — 8 existing event types from 13b plus `TX_OPEN`, `TX_CLOSE`; today any typo passes silently)
- Edit: `ML/baseline/parse_mt5_execution_report.py` (count new events; reconciliation summary: per-position classification, `same_h1_count`)
- Edit/Add: `tests/test_parse_mt5_execution_report.py`, `tests/test_mt5_signal_executor_schema.py` (fixtures with TX rows, same-H1 case, unknown-event-name rejection; fixture confirming existing behavior that empty timing fields pass validation — no code change needed for that)

**Steps:**
- [x] Add event-name whitelist validation to the schema (new check, not an extension of an existing enum — none exists today).
- [x] Add reconciliation: group by position id, classify per Design Decision 5, emit `same_h1_count`.
- [x] Targeted pytest green.

## Task 3: Short Smoke Run

**Steps:**
- [x] Check/clean `liveupdate/` payload before launch.
- [x] Run tester on a short range (e.g. 2019.06.20–2019.07.20) with the new build.
- [x] Verify: TX_OPEN count equals fills observed, every TX row parses, deal reasons non-empty, and every position id from TX rows links to a signal at the reconciliation stage (not at row level — TX rows carry no signal timing by design).
- [x] If TX events do not fire under Model 1, stop and record findings; decision point before full run.

## Task 4: Full Re-Run And Reconciliation

**Steps:**
- [x] Full run, same scenario as 2026-07-30; event CSV name `mt5_trade_events_20260731_tx_lifecycle.csv` (copy to `ML/reports/mt5_execution_loop/`, hash it).
- [x] Parse, validate schema, run reconciliation.
- [x] Success criteria: every opened position classified (`UNEXPLAINED == 0` or itemized); `same_h1_lifecycle_status=MEASURED:<n>`; old-polling CLOSE (expected ≈18) vs TX_CLOSE coverage compared and the gap explained; timing contract PASS on rows that carry timing.
- [x] Cross-check vs 2026-07-30 run: ORDER_PLACED/OPEN counts should match (same signals, same scenario); any drift must be explained or the run is not comparable.

## Task 5: Report And Handoff

**Files:**
- Create: `docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md`
- Create/Update: run manifest JSON in `ML/reports/mt5_execution_loop/` (tester metadata, hashes, reconciliation numbers, compile log)
- Update: `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `docs/superpowers/roadmap.md` (remove completed step 1 from Next action — roadmap does not keep closed steps; outcome goes to the report and `CHANGELOG.md`)

**Steps:**
- [x] Report per methodology 16: stage level (infrastructure diagnostic, no search budget), multiple-testing context (no new selection), split disclosure, forbidden_interpretations (no PnL, no rule quality), limitations.
- [x] Decision memo: `continue` (to Nero parity) | `close` | `unblock`.
