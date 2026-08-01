# Audit: 2026-08-01-mt5-execution-hygiene-postbatch.md

**Date:** 2026-08-01
**Auditor:** automated cross-check

---

## 1. Hash mismatch: `batch_summary.json`

- **Importance:** critical
- **Location:** report line 99
- **Issue:** sha256 in report: `215fa1322a...657beafe`. Actual: `bbe2bf19a3a2b42c1fefb0f3207a29c6636eca5c5a8e0d4e37743cceb767e897`.
- **Evidence:** `sha256sum ML/reports/mt5_execution_loop/batch/batch_summary.json`
- **Why:** next agent cannot verify which `batch_summary.json` was used.
- **Recommendation:** recalculate and replace hash; if file changed post-generation, document it.

## 2. Critical — Hash mismatch: `event_anomaly_summary.json`

- **Importance:** critical
- **Location:** report line 95
- **Issue:** Report hash `ebc27151...25df69b0`. Actual: `8a32bb2df4881b3417544fa7fb9c0b13ec0417f9eadf11166eb88bff34bbb59b`.
- **Evidence:** `sha256sum ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json`
- **Recommendation:** recalculate and replace.

## 3. Critical — Hash mismatch: `event_anomalies.csv`

- **Importance:** critical
- **Location:** report line 96
- **Issue:** Report says `439d43661...f9493c4`. Actual: `fe758e38dc6090c8491333d961ed1c16918592aabf7be0fc0f2dfaded6c54bacea9`.
- **Evidence:** `sha256sum ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv`
- **Recommendation:** recalculate and replace.

## 4. Important — All numerical claims match structured artifacts (positive result)

- **Importance:** important
- **Location:** lines 105–152 (Structured Artifact Cross-Check and Results)
- **Issue:** Every number reported (1879 error rows, `INVALID_STOPS=670`, `REQUOTE=550`, `OTHER=621`, `MODIFICATION_TOO_CLOSE=35`, `MARKET_CLOSED=2`, `INVALID_PRICE=1`, `mt4_files=1174`, `mt_tester_files=705`, `position_count=269`, `CLOSED_TX=269`, `UNEXPLAINED=0`, `same_h1_count=17`, `ORDER_EXPIRED=9` (2026-07-30), `OPEN_FAILED=22767`, `ORDER_EXPIRED=67` (batch), `BATCH_NO_WINNER`, 11 eligible (all `BS_p05 < 1.0`), top candidate `PF=1.2323`, `BS_p05=0.886747...`, `trades_count=102`, `fill_rate=0.094444...`, `gross_profit=5468.199999999997`, `gross_loss=4437.3`, `average_win=130.196238...`, `average_loss_abs=73.955`) — все confirmed by reading corresponding JSON/CSV artifacts.
- **Recommendation:** none needed.

## 5. Important — Methodological references valid

- **Importance:** important
- **Location:** report line 36
- **Issue:** All 6 cited methodology files (`00-research-management.md`, `09-validation-freeze.md`, `12-backtest-costs.md`, `13b-mt5-execution-parity.md`, `A5-post-mortem-diagnostics.md`, `16-reporting-audit.md`) exist and contain relevant requirements.
- **Evidence:** verified by reading each file.

## 6 — Report structure follows `16-reporting-audit.md`

- **Importance:** important
- **Location:** whole report
- **Issue:** All required sections present: Context, State Level, What Was Done, Multiple Testing Context, Changed Files, Verification, Results, Conclusions, Limitations/Open Questions, Split Disclosure, Next Step, Related Materials. Plus Research-first disclosure and Structured Artifact Cross-Check.
- **Evidence:** `16-reporting-audit.md`, lines 19–20.
- **Recommendation:** none (except fixing hashes).

## 6 — A5 post-mortem scope correctly documented as partial

- **Importance:** important
- **Location:** lines 161–163
- **Issue:** Report honestly states A5 scope is partial: no oracle decomposition, no TP/SL/TIMEOUT exits 0, no yearly gross loss, no feature-period contrasts, no negative controls. Reason given: additional saved inputs or new diagnostic cycle needed.
- **Evidence:** `A5-post-mortem-diagnostics.md` requires these steps; report documents what's missing without hiding gaps.

## 8. Improvement — `research_priority` wording slighly non-standard

- **Importance:** improvement
- **Location:** line 18: `research_priority: infrastructure first, then post-batch diagnostics`
- **Issue:** `00-research-management.md` expects `research_priority: low|medium|high` with reason. The reason is given, but explicit level label is missing.
- **Recommendation:** Consider `high; infrastructure first, then post-batch diagnostics`.

## 8. Important — All artifacts listed in in "Cached Files" exist on disk

- **Importance:** important
- **Location:** lines 46–53 (generated) and 65–88 (committed files)
- **Issue:** All 7 generated JSON/CSV/py artifacts, plus `CONTEXT_HANDOFF.md`, `CHANGELOG.md`, `docs/superpowers/roadmap.md`, wiki files are present.
- **Evidence:** `glob` confirmed each path.

## 9. Important — No forbidden interpretations present

- **Importance:** important
- **Location:** Conclusions (152–162) and Forbidden Interpretations (179)
- **Issue:** No claim is "profitable", "ready", "live-ready", "tradable", "model-quality proof". No new winner selected. Report correctly preserves `DIAGNOSTIC_ONLY`.
- **Evidence:** Direct search for prohibited words.

---

## Summary

| Category | Count | Details |
|----------|-------|---------|
| Critical | 3 | Hash mismatches for `batch_summary.json`, `event_anomaly_summary.json`, `event_anomalies.csv` |
| Important | 7 | All numerical claims confirmed; methodology cites valid; structure follows standard; A5 scope documented; all artifacts exist; no forbidden interpretations; error-para handled correctly |
| Improvement | 1 | `research_priority` wording format |

**Все числа в отчёте сверены со structured artifacts — расхождений нет.** Единственная реальная проблема — три невалидных sha256-хеша, которые нужно исправить для воспроизводимости.