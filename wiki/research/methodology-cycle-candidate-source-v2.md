---
last_updated: 2026-05-27
sources: 1
status: active
---

# Methodology Cycle Candidate Source v2

> Live-safe candidate-source cycle rebuilt the Nero/PIC pipeline, but the current live-executable R-multiple protocol fails at Stage 09 and has no valid Stage 10 candidate.

## Хронология

Stages 00-02 fixed the hypothesis, gates, live-safe feature contract, raw data inventory, split protocol, and PLL normalization. The old offline `signal != 0` candidate-source gate was rejected because it depends on future-derived labels.

Stages 03-05 checked feature leakage, labeling, and EDA. The key data-quality finding is a volatility regime shift from train to validation, so later robustness must include per-year and per-regime slices.

Stages 07-08 established baselines and a first model sweep. Flat RF found `buy_sl3_tp3` as the only viable target but failed full robustness with one negative validation year. Stage 08 was corrected to exclude timeout rows from binary TP-vs-SL threshold/PF calculation and now saves validation predictions.

Stage 09 froze a deterministic Transformer checkpoint. Under the old count-based/Close-row protocol, a validation-only stability refreeze selected threshold `0.5359389781951904`. After switching to R-multiple PnL and entry=`Open[row+1]`, Stage 09 found `0` eligible stable rules and `canonical_rule=null`.

Stage 09 script ownership is split deliberately: `validation_freeze.py` trains and round-trip verifies the checkpoint/normalizer, while `stage09_stability_refreeze.py` is the source of truth for the current validation-only stability scan. Existing `stage09_frozen_rule.json` is stale/superseded after the R-PnL entry-protocol change.

Stage 10 is invalid under the current protocol. There is no valid frozen Stage 09 candidate, and the current `stage10_frozen_test_oos.json` records `checkpoint_hash_matches_rule=false`, `stage_verdict=INVALID`, and `model_verdict=invalid_frozen_protocol`.

Entry timing became a first-class methodology finding. `fractal0` is fully known only at the close of its confirming third bar; only after that does MQL write the row, watcher poll/process it, and execution receive a possible signal. Therefore `Close[row]` entry is diagnostic-only for this live path. Even `Open[row+1]` requires proof that runtime latency can place an order by that open.

## Ключевые результаты

| Stage | Result |
|---|---|
| Data | `63006` Nero rows, sequential split `44104/9451/9451` |
| Baseline | RF `buy_sl3_tp3` validation PF `1.58`, `281` trades, `1` negative year |
| Model sweep | Transformer PF `11.60` / `63` trades, BiLSTM PF `1.74` / `293` trades on timeout-excluded binary validation |
| Old protocol freeze | threshold `0.5359389781951904`, PF `1.97`, `142` trades, `0` negative years; superseded |
| Current Stage 09 | R-multiple PnL + entry=`Open[row+1]`: `eligible_count=0`, `canonical_rule=null`, verdict `FAIL` |
| Current Stage 10 | No valid frozen candidate; `stage_verdict=INVALID`, metrics diagnostic only |

## Выводы

The current Transformer rule did not survive the live-executable R-multiple validation freeze. No Stage 11 robustness work is allowed from this candidate. Future work must first define an executable entry convention and produce a new Stage 09 PASS before opening any frozen test.

## Открытые вопросы

- What first executable entry price should be used after `fractal0` readiness, row write, watcher polling, inference and order-send latency.
- Whether a new model/target can pass Stage 09 under that executable entry convention.
- Whether single-seed deterministic training is enough, or a multi-seed rule is required before production candidacy.

## Источники

- `docs/reports/2026-05-25-methodology-cycle-stages-00-04.md` — methodology cycle Stages 00-10, Stage 09 stability refreeze, and Stage 10 frozen test.
