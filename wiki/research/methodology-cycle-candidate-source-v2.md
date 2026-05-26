---
last_updated: 2026-05-26
sources: 1
status: active
---

# Methodology Cycle Candidate Source v2

> Live-safe candidate-source cycle rebuilt the Nero/PIC pipeline and reached a validation-only Transformer freeze; the current rule is research-only pending frozen test.

## Хронология

Stages 00-02 fixed the hypothesis, gates, live-safe feature contract, raw data inventory, split protocol, and PLL normalization. The old offline `signal != 0` candidate-source gate was rejected because it depends on future-derived labels.

Stages 03-05 checked feature leakage, labeling, and EDA. The key data-quality finding is a volatility regime shift from train to validation, so later robustness must include per-year and per-regime slices.

Stages 07-08 established baselines and a first model sweep. Flat RF found `buy_sl3_tp3` as the only viable target but failed full robustness with one negative validation year. Stage 08 was corrected to exclude timeout rows from binary TP-vs-SL threshold/PF calculation and now saves validation predictions.

Stage 09 froze a deterministic Transformer checkpoint. The initial high-PF threshold (`0.60`) produced PF `2.57` on only `35` validation trades, with `77%` of trades in 2019. A validation-only stability refreeze replaced it with threshold `0.5359389781951904`, calibrated from top `1.5%` validation scores.

## Ключевые результаты

| Stage | Result |
|---|---|
| Data | `63006` Nero rows, sequential split `44104/9451/9451` |
| Baseline | RF `buy_sl3_tp3` validation PF `1.58`, `281` trades, `1` negative year |
| Model sweep | Transformer PF `11.60` / `63` trades, BiLSTM PF `1.74` / `293` trades on timeout-excluded binary validation |
| Initial freeze | Transformer threshold `0.60`, PF `2.57`, `35` trades, max year share `77%` |
| Stability refreeze | threshold `0.5359389781951904`, PF `1.97`, `142` trades, `0` negative years, `4` active years, max year share `47.9%`, bootstrap CI `[1.36, 3.00]` |

## Выводы

The current Transformer rule is a better validation candidate after stability refreeze: it trades more often and no longer depends mostly on 2019. It is still not production evidence. The status remains research-only until frozen test, robustness, costs, and MT4 parity pass with the unchanged checkpoint, normalizer, threshold, target, and execution mapping.

## Открытые вопросы

- Whether the validation-stable threshold survives Stage 10 frozen test.
- Whether robustness holds across volatility regimes, years, and future forward data.
- Whether single-seed deterministic training is enough, or a multi-seed rule is required before production candidacy.

## Источники

- `docs/reports/2026-05-25-methodology-cycle-stages-00-04.md` — methodology cycle Stages 00-09 and Stage 09 stability refreeze.
