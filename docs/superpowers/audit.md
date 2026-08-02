# Audit: 2026-08-01-mt5-execution-hygiene-postbatch.md

**Date:** 2026-08-02
**Auditor:** automated cross-check
**Object:** `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md` (193 lines)

---

## 1. Important — All SHA256 hashes match (positive result)

- **Importance:** important
- **Location:** report lines 92–101 (Artifact Hashes)
- **Issue:** all 10 hashes match the files on disk:
  - `error_inventory.json` `fc7d1070...` ✓
  - `error_summary.json` `57be2f56...` ✓
  - `error_rows_classified.csv` `79d5978b...` ✓
  - `event_anomaly_summary.json` `8a32bb2d...` ✓
  - `event_anomalies.csv` `fe759538...` ✓
  - `post_batch_diagnostics.json` `41932413...` ✓
  - `post_batch_top_candidates.csv` `ed73d7d9...` ✓
  - `batch_summary.json` `bbe2bf19...` ✓
  - `mt5_execution_metrics_20260731_tx_lifecycle.json` `e550d8bc...` ✓
  - `mt5_execution_metrics_20260730_entry_quality_filter.json` `9a5af9bc...` ✓
- **Evidence:** `sha256sum` of each listed path matches the report value.
- **Why:** previous audit of this report (before this pass) flagged three hash mismatches; they are now fixed.
- **Recommendation:** none.

## 2. Critical — Test count cited is stale: 29 vs factual 53

- **Importance:** important
- **Location:** report line 139
- **Issue:** Report states: `29 passed in 0.34s`. Actual run of the exact command on line 136 (`./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q`) gives **`53 passed in 0.47s`**.
- **Evidence:**
  - Rerun: `53 passed in 0.47s`.
  - Test count: `test_mt5_execution_diagnostics.py` has 24 test functions, `test_parse_mt5_execution_report.py` has 6, `test_mt5_signal_executor_schema.py` has 23 → 53.
  - Running only `test_mt5_execution_diagnostics.py` + `test_parse_mt5_execution_report.py` gives `30 passed` — closer to the report's 29, suggesting the report's command text doesn't match the actual command run.
- **Why:** Verification line is the canonical proof that the report is reproducible. A wrong pass count raises doubt that the cited command was actually run, or that artifacts changed post-publication.
- **Recommendation:** rerun the exact pytest command, update the line number, and either: (a) update the count to `53 passed` if all three files genuinely ran, or (b) align the command on line 136 to match what actually produced 29. The latter is unlikely; the report was written before added tests.

## 3. Improvement — `HEAD=aad3bc9 plus working-tree audit changes` is ambiguous

- **Importance:** improvement
- **Location:** report line 139
- **Issue:** Current `HEAD` is `8c961ad` (docs: report mt5 fill rate probe), not `aad3bc9`. The hash `aad3bc9` DOES exist in git history as `fix: keep mt5 hygiene verdict diagnostic only`, validating the claim that at publication time the report was based on that commit + uncommitted fixes. It is now committed and HEAD moved on.
- **Evidence:** `git rev-parse HEAD` → `8c961ad0cf516adbe4346df8261de528c890169b`; `git log --all | grep aad3bc9` → found.
- **Why:** The phrase "plus working-tree audit changes" leaves it ambiguous whether the audit-changed report itself was recommitted. For reproducibility, the final committed state should match the report.
- **Recommendation:** replace with a single pinned commit that reflects the final state at report publication, or delete the `HEAD=` note since the audit fixes are now committed.

## 4. Important — All numeric claims in Structured Artifact Cross-Check verified

- **Importance:** important (positive)
- **Location:** report lines 105–121 (Structured Artifact Cross-Check) and 143–149 (Results)
- **Issue:** Every number verified against source artifacts:
  - 6 discovered `ERROR_SoSimple_*.csv`: `error_inventory.json.files` count = 6 ✓
  - Missing `ERROR_SoSimple_163856259.csv`: present in `error_inventory.json.unknowns.not_found_expected_files` ✓
  - 1879 classified rows: `error_summary.json.total_rows = 1879` ✓
  - Error classes (`INVALID_STOPS=670`, `OTHER=621`, `REQUOTE=550`, `MODIFICATION_TOO_CLOSE=35`, `MARKET_CLOSED=2`, `INVALID_PRICE=1`): match `error_summary.json.by_error_class` exactly ✓
  - Source buckets (`mt4_files=1174`, `mt_tester_files=705`): match `error_summary.json.by_source_bucket` ✓
  - Lifecycle `position_count=269`, `CLOSED_TX=269`, `UNEXPLAINED=0`, `same_h1_count=17`: match `mt5_execution_metrics_20260731_tx_lifecycle.json.reconciliation` ✓
  - Single-rule `ORDER_EXPIRED=9`: matches metric file order_counts ✓
  - 32 batch event paths, `_smoke` excluded: `batch_run_count=32`, `excluded_service_dirs=['_smoke']` ✓
  - Batch `OPEN_FAILED=22767`, `ORDER_EXPIRED=67`: match `event_anomaly_summary.json.batch_runs.event_counts` ✓
  - Linkage `UNKNOWN`: ✓
  - `BATCH_NO_WINNER`, 11 failed low bootstrap lower bound, buckets `100-149=9` and `150+=2`, one profit-concentration fail: match `post_batch_diagnostics.json.top_failure_modes`
  - Top candidate `PF=1.2323`, `BS_p05=0.8867479736061653`, `trades_count=102`, `fill_rate=0.09444444444444444`, `gross_profit=5468.199999999997`, `gross_loss=4437.3`, `average_win=130.19523809523804`, `average_loss_abs=73.955`: all match `post_batch_diagnostics.json.top_candidates[0]` ✓
- **Recommendation:** none.

## 5. Important — Sample Size Disclosure fully verified

- **Importance:** important (positive)
- **Location:** report lines 125–131 (Sample Size Disclosure)
- **Issue:** All quoted sample sizes verified:
  - Reference event artifacts: 23050 events = `event_anomaly_summary.json.reference_runs.total_rows` ✓
  - Batch event artifacts: 54078 events across 32 runs = `batch_runs.total_rows=54078`, `batch_run_count=32` ✓
  - Batch candidate table: 32 valid + 11 eligible = `n_valid=32`, `n_eligible=11` ✓
  - 1424 trades among 11 eligible = `sample_sizes.eligible_top_candidate_trades=1424` ✓
  - 14954 active signal rows; 7092 buy, 7862 sell = `sample_sizes.eligible_top_candidate_*` ✓
- **Recommendation:** none.

## 6. Important — Hypothesis claim ("per-run reconciliation UNEXPLAINED=0") verified

- **Importance:** important (positive)
- **Location:** report line 159
- **Issue:** Report claims `batch reconciliation remains UNEXPLAINED=0 in per-run metrics`. Verified: across all 32 runs in `event_anomaly_summary.json.batch_runs.reconciliation_by_run`, no run has `UNEXPLAINED != 0`. Total: `UNEXPLAINED=0`, `CLOSED_TX=2508`, `OPEN_AT_END=0`.
- **Evidence:** `[(rid, v.class_counts.UNEXPLAINED) for rid,v in runs.items() if !=0]` returns empty list; total UNEXPLAINED across 32 runs = 0.
- **Recommendation:** none — the hypothesis basis is sound.

## 7. Improvement — Report omits TX_OPEN count for batch (potential for confusion)

- **Importance:** improvement
- **Location:** report line 147 (event anomaly summary sentence)
- **Issue:** Report discloses `OPEN_FAILED=22767` and `ORDER_EXPIRED=67` only. Available counters showing scale of execution: `TX_OPEN=2508`, `TX_CLOSE=2508`, `ORDER_PLACED=2601`, `OPEN=2367`. These show that 22659 of 22767 `OPEN_FAILED` events (~99.5%) are policy-block retries against the 2508 actually opened positions. This is structurally what later fill-rate probe analyzes; readers may misread `OPEN_FAILED=22767` as if 22767 distinct orders failed.
- **Evidence:** `event_anomaly_summary.json.batch_runs.event_counts` — full table.
- **Why:** The `OPEN_FAILED` number alone overstates execution failures because retries against the one-position policy are counted once per attempt; without `TX_OPEN` for context, the number can be misread.
- **Recommendation:** Add one sentence to Results: "Batch totals: `ORDER_PLACED=2601`, `OPEN=2367`, `TX_OPEN=2508` (one open position per run); the 22767 `OPEN_FAILED` events count retry attempts per same-bar signal under the single-position policy, not distinct broker refusals."

## 8. Improvement — Methodology citations valid but 09-validation-freeze.md is not central

- **Importance:** improvement
- **Location:** report line 36
- **Issue:** Report cites `00-research-management.md`, `09-validation-freeze.md`, `12-backtest-costs.md`, `13b-mt5-execution-parity.md`, `16-reporting-audit.md`, `A5-post-mortem-diagnostics.md`. All six exist and are relevant. `09-validation-freeze.md` is weakly invoked — the stage does not perform validation selection or open locked_test — but its split-role and `locked_test`-forbidden rules indirectly bind the report. Other cited files (A5, 00, 13b, 12:50/:127/:130, 16) are directly applied.
- **Evidence:** all six files confirmed present; `09-validation-freeze.md:46` ("Запретить изменение rule после просмотра `locked_test`") and `:57` ("`locked_test` не участвует в выборе") are the actually relevant lines.
- **Recommendation:** none required; optionally drop `09-validation-freeze.md` from the list since this stage performs neither selection nor freeze, and split disclosure (line 174) already handles it.

## 9. Important — All Related Materials files exist

- **Importance:** important
- **Location:** report lines 187–192
- **Issue:** All seven related-material paths exist:
  - Plan: `docs/superpowers/plans/2026-08-01-mt5-execution-hygiene-postbatch.md` ✓
  - `docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md` ✓
  - `docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md` ✓
  - `docs/reports/2026-07-31-mt5-nero-parity.md` ✓
  - `docs/reports/2026-07-31-mt5-batch-selection.md` ✓
  - `docs/superpowers/roadmap.md` ✓
  - `ML/reports/mt5_execution_loop/diagnostics/` (directory) ✓
- **Recommendation:** none.

## 10. Important — Report structure matches `16-reporting-audit.md` requirements

- **Importance:** important (positive)
- **Location:** whole report
- **Issue:** `16-reporting-audit.md:18–30` lists required sections: Context, Stage Level, What Was Done, Multiple Testing Context, Changed Files, Verification, Results, Conclusions, Limitations/Open Questions, Split Disclosure, Next Step, Related Materials. Plus Research-first disclosure (lines 64–77). The report contains all required sections:
  - Context (✓ line 26) — NO `Уровень этапа` heading but Stage Level section (✓ line 9)
  - Research-first disclosure (✓ line 13)
  - Multiple Testing Context (✓ line 40)
  - What Was Done (✓ line 44) with commands
  - Changed Files (✓ line 65)
  - Artifact Hashes (✓ extra)
  - Structured Artifact Cross-Check (✓ extra)
  - Sample Size Disclosure (✓ extra, matches `16:94` requirement)
  - Verification (✓ line 133)
  - Results (✓ line 141)
  - Conclusions (✓ line 151)
  - Limitations/Open Questions (✓ line 165)
  - Split Disclosure (✓ line 173)
  - Forbidden Interpretations (✓ line 177) — requirements met
  - Next Step (✓ line 181) — exactly one action as required
  - Related Materials (✓ line 185)
- **Recommendation:** none — exceeds the mandatory minimum.

## 11. Important — Forbidden interpretations explicit and compliant

- **Importance:** important (positive)
- **Location:** report lines 24 and 179
- **Issue:** Both explicit `forbidden_interpretations` line (24) and Forbidden Interpretations section (179) list: `profitable, ready, live-ready, tradable, new winner, model-quality proof`. No content claim raises verdict above `DIAGNOSTIC_ONLY`. No claim of "candidate" or model-quality. Report explicitly preserves `BATCH_NO_WINNER` (line 117, 153).
- **Evidence:** grep for forbidden words in report — none of them appear as claims.
- **Recommendation:** none.

## 12. Important — A5 partial-scope honestly disclosed (positive)

- **Importance:** important (positive)
- **Location:** report lines 160–163
- **Issue:** Report explicitly states A5 scope is partial and lists what is NOT done: oracle component decomposition, TP/SL/TIMEOUT exit slices, yearly gross loss contribution, feature-period contrasts, negative controls. Reason: "those require additional saved inputs or a new diagnostic cycle". This matches `A5-post-mortem-diagnostics.md` requirement to be honest about scope limits, and the A5 stop condition on missing required inputs.
- **Evidence:** `A5-post-mortem-diagnostics.md:309–320` lists stop conditions including insufficient objects and missing preconditions; report meets that honesty requirement.
- **Recommendation:** none.

## 13. Improvement — Costs limitation claim is procedurally OK

- **Importance:** improvement
- **Location:** report line 171 ("Cost model remains incomplete: swap, commission, slippage, latency, and stress-cost checks are not closed")
- **Issue:** Limitation matches `12-backtest-costs.md:20–22` (commission, swap, slippage requirements) and `:71` ("Spread/commission/slippage не оставлены 'на потом'"). Since the stage is `DIAGNOSTIC_ONLY` and produces no trading verdict, the open cost model is disclosed as a limitation, not as a violation.
- **Evidence:** plan for this stage explicitly bounds verdict to `DIAGNOSTIC_ONLY`, so unproven cost model is compliant.
- **Recommendation:** none — handled correctly.

## 14. Improvement — `CONTEXT_HANDOFF.md` no longer references this report as "latest report"

- **Importance:** improvement
- **Location:** report line 83 lists `CONTEXT_HANDOFF.md` as modified.
- **Issue:** Current `CONTEXT_HANDOFF.md` lists active track as `MT5 entry mechanics / trade-count frozen probe planning`; the report it points to is no longer this one (it has been superseded by the fill-rate probe report). This is normal because two later reports have since superseded this stage.
- **Evidence:** `CONTEXT_HANDOFF.md:5` reads `MT5 entry mechanics / trade-count frozen probe planning`; CHANGELOG entries for `2026-08-01 — MT5 Saved-Batch Fill-Rate Probe` and `2026-08-01 — MT5 diagnostic timing contract` are above this one.
- **Why:** The handoff state is correct for the project's current position, not a defect in this report.
- **Recommendation:** none — the report was correct at publication time.

## 15. Improvement — `execution_hygiene_status: EXECUTION_HYGIENE_PARTIAL` is project-specific, not methodology-defined

- **Importance:** improvement
- **Location:** report line 16
- **Issue:** The field `execution_hygiene_status` is not defined in any methodology file; it is project-internal vocabulary. It is consistent with related reports (`2026-08-01-mt5-diagnostic-timing-contract.md` uses `lifecycle_status: DIAGNOSTIC_ONLY` without execution_hygiene_status). The field adds information without contradicting methodology.
- **Evidence:** grep methodology files for `EXECUTION_HYGIENE` returns no matches.
- **Recommendation:** none — project-internal field; consider documenting the vocabulary in `docs/methodology/13b-mt5-execution-parity.md` if it appears in more reports.

---

## Summary

| Category    | Count | Items |
|-------------|-------|-------|
| Critical    | 0     | — |
| Important   | 9     | #1 hashes ✓, #2 verified, #3 sample ✓, #4 per-run UNEXPLAINED=0 ✓, #5 related materials ✓, #6 structure ✓, #7 forbidden interp ✓, #8 A5 partial ✓, #9 all numeric claims ✓ |
| Improvement | 6     | #3 HEAD ambiguity, #7 missing TX_OPEN context, #8 weak 09 ref, #13 cost limitation, #14 handoff superseded, #15 hygiene_status vocabulary |
| Issues      | 1     | #2 stale pytest count (29 vs 53) |

**Единственная реальная проблема:** строка 139 — устаревшее число тестов `29 passed` вместо фактического `53 passed`. Предположительно отчёт писался до того, как в `test_mt5_execution_diagnostics.py` и `test_mt5_signal_executor_schema.py` добавили новых тестов, и число не было обновлено. Все прочие числовые утверждения, хеши, cross-ссылки, методологические проверки и A5-scope disclosure — корректны и подтверждены напрямую из structured-артефактов.

**Существенных расхождений с методологией `docs/methodology/` не найдено.** Отчёт честно документирует неполноту A5, запрещённые интерпретации, split disclosure и `BATCH_NO_WINNER` без скрытого переопределения verdict.