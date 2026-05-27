---
last_updated: 2026-05-27
sources: 1
status: active
---

# Methodology Cycle Candidate Source v2

> Live-safe candidate-source cycle rebuilt the Nero/PIC pipeline and reached a Stage 10 frozen-test candidate; production claims still require robustness, costs, MT4 parity and forward-test.

## Хронология

Stages 00-02 fixed the hypothesis, gates, live-safe feature contract, raw data inventory, split protocol, and PLL normalization. The old offline `signal != 0` candidate-source gate was rejected because it depends on future-derived labels.

Stages 03-05 checked feature leakage, labeling, and EDA. The key data-quality finding is a volatility regime shift from train to validation, so later robustness must include per-year and per-regime slices.

Stages 07-08 established baselines and a first model sweep. Flat RF found `buy_sl3_tp3` as the only viable target but failed full robustness with one negative validation year. Stage 08 was corrected to exclude timeout rows from binary TP-vs-SL threshold/PF calculation and now saves validation predictions.

Stage 09 froze a deterministic Transformer checkpoint. The initial high-PF threshold (`0.60`) produced PF `2.57` on only `35` validation trades, with `77%` of trades in 2019. A validation-only stability refreeze replaced it with threshold `0.5359389781951904`, calibrated from top `1.5%` validation scores.

Stage 09 script ownership is split deliberately: `validation_freeze.py` trains and round-trip verifies the checkpoint/normalizer, while `stage09_stability_refreeze.py` is the source of truth for the canonical `stage09_frozen_rule.json`.

Stage 10 applied the unchanged Stage 09 rule to the test split once. Aggregate gates passed (PF `3.00`, `37` trades, `0` negative years), but the result has structural risk: `27/37` trades were in 2023, 2022 had no trades, and most selected rows had `signal=0`, so BUY/SELL slices are diagnostic rather than live execution-side proof.

## Ключевые результаты

| Stage | Result |
|---|---|
| Data | `63006` Nero rows, sequential split `44104/9451/9451` |
| Baseline | RF `buy_sl3_tp3` validation PF `1.58`, `281` trades, `1` negative year |
| Model sweep | Transformer PF `11.60` / `63` trades, BiLSTM PF `1.74` / `293` trades on timeout-excluded binary validation |
| Initial freeze | Transformer threshold `0.60`, PF `2.57`, `35` trades, max year share `77%` |
| Stability refreeze | threshold `0.5359389781951904`, PF `1.97`, `142` trades, `0` negative years, `4` active years, max year share `47.9%`, bootstrap CI `[1.36, 3.00]` |
| Frozen test | threshold `0.5359389781951904`, PF `3.00`, `37` trades, `10.6` trades/year, `0` negative years, max year share `72.97%` |

## Выводы

The current Transformer rule passed the one-shot frozen test aggregate gates and can proceed to robustness as a candidate. It is still not production evidence. The high test concentration means Stage 11 must specifically stress yearly/regime stability before costs, export, MT4 parity or forward-test claims.

## Открытые вопросы

- Whether robustness holds across volatility regimes, years, and future forward data.
- Whether single-seed deterministic training is enough, or a multi-seed rule is required before production candidacy.

## Источники

- `docs/reports/2026-05-25-methodology-cycle-stages-00-04.md` — methodology cycle Stages 00-10, Stage 09 stability refreeze, and Stage 10 frozen test.
