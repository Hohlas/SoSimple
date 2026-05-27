# Context Handoff

Дата: 2026-05-27.

## Текущий этап

Завершены Stages 00-10 methodology-цикла `methodology_cycle_candidate_source_v2` на ветке `ml-cycle-methodology-stage-0-1`.

Статус Stage 10: `PASS`. Модель получила `candidate` verdict на frozen test, но это не production approval. Следующий этап нельзя начинать без явного `PASS` пользователя.

## Гипотеза

Live-safe candidate-source модель на текущем срезе Nero/PIC может заменить оффлайновый `signal != 0` gate и улучшить baselines.

Decision unit: строка/бар-кандидат с 3D fractal tensor.

Decision time: момент доступности MQL/PIC fractal state в строке `Nero.csv`; future-derived labels используются только как target.

## Что сделано

- `MT/MQL4/Files/Nero.csv` обновлён пользователем как raw source of truth; старые `DATA/Nero_*_labeled.csv` были перегенерированы.
- Pipeline прошёл Stages 00-04: raw inventory, sort/label/split, feature contract/leakage, labeling.
- Train/validation/test split: `44104 / 9451 / 9451`, temporal order preserved, test not viewed.
- PLL normalizer fit только на train; feature/target normalization разделены, группы нормализации проверены по scale.
- Stage 05 EDA: train+validation only, test not inspected.
- Stage 06 split manifest: no row overlap, no shuffle, no sorting errors; no purged embargo, accepted with restriction.
- Stage 07 baselines: RF_160 validation PF `1.5761`, 281 trades, 1 negative year; baseline to beat on test is RF_160 plus 0 negative years.
- Stage 08 model sweep: exploratory validation only; Transformer max-PF row PF `11.6` on 63 trades is not canonical.
- Stage 09 deterministic Transformer checkpoint saved with round-trip diff `0.0`.
- Stage 09 canonical rule selected by `ML/stage09_stability_refreeze.py`: threshold `0.5359389781951904`, calibrated from validation top_k `1.5%`.
- Stage 10 frozen test/OOS run once with unchanged Stage 09 rule: PF `3.0`, 37 trades, 10.6 trades/year, 0 negative years, model verdict `candidate`.

## Stage 09 Frozen Rule

Canonical source of truth:

- `ML/stage09_stability_refreeze.py` writes `stage09_frozen_rule.json` and `stage09_stability_refreeze.json`.
- `ML/validation_freeze.py` trains checkpoint + normalizer and verifies round-trip only; it does not overwrite the canonical frozen rule.

Canonical validation metrics:

- PF `1.9722`
- trades `142`
- trades/year `40.5714`
- win rate `0.6636`
- TP/SL `71/36`
- negative years `0`
- active years `4`
- max year trade share `0.4789`
- bootstrap CI `[1.3554, 3.0]`

Superseded high-PF rule:

- threshold `0.60`
- PF `2.5714`
- trades `35`
- rejected because validation trades were concentrated in 2019 and 2022 had no trades.

## Stage 10 Frozen Test

Frozen test protocol:

- Test split read by `ML/stage10_frozen_test_oos.py`.
- No retraining, no normalizer refit, no threshold/top-k search.
- Checkpoint and normalizer hashes matched `stage09_frozen_rule.json`.
- Threshold stayed `0.5359389781951904`.

Test metrics:

- PF `3.0`
- trades `37`
- trades/year `10.5663`
- win rate `0.75`
- TP/SL `21/7`
- negative years `0`
- active years `4`
- idle years: `2022`
- max year trade share `0.7297` in `2023`
- max drawdown `3.0R`, ending PnL `14.0R`

Stage 10 limitations:

- Test trades are sparse and concentrated: 27/37 in 2023.
- 30/37 selected rows have `signal=0`; BUY/SELL slices are diagnostic and do not define a live execution side.
- Metrics are gross; costs/slippage/spread are still deferred.

## Git

Ветка: `ml-cycle-methodology-stage-0-1`.

Последние значимые commits:

- `5a98691` — Stage 09 source-of-truth split: `stage09_stability_refreeze.py` writes frozen rule, `validation_freeze.py` is checkpoint-only.
- `8057aca` — wiki integrity refresh.
- `6cb85fa` — methodology cycle: stabilize stages 05-09.

## Ключевые файлы

- `ML/reports/methodology_cycle_candidate_source_v2/stage01_gate_verdict.json` — canonical stage verdicts.
- `ML/reports/methodology_cycle_candidate_source_v2/stage09_frozen_rule.json` — canonical frozen validation rule.
- `ML/reports/methodology_cycle_candidate_source_v2/stage09_stability_refreeze.json` — full validation-only stability scan.
- `ML/reports/methodology_cycle_candidate_source_v2/stage10_frozen_test_oos.json` — one-shot frozen test summary.
- `ML/reports/methodology_cycle_candidate_source_v2/stage10_test_predictions.csv` — frozen test predictions.
- `ML/reports/methodology_cycle_candidate_source_v2/stage10_test_trades.csv` — selected frozen test trades.
- `ML/stage09_stability_refreeze.py` — Stage 09 source of truth for frozen rule.
- `ML/stage10_frozen_test_oos.py` — Stage 10 frozen test runner.
- `ML/validation_freeze.py` — deterministic Transformer training + checkpoint round-trip.
- `ML/checkpoints/transformer_winner.pt` — frozen checkpoint.
- `ML/checkpoints/pll_normalizer_v1.pkl` — train-fit normalizer.
- `DATA/Nero_{train,validation,test}_labeled.csv` — labeled temporal splits.
- `docs/reports/2026-05-25-methodology-cycle-stages-00-04.md` — current report covering Stages 00-09 despite legacy filename.
- `wiki/research/methodology-cycle-candidate-source-v2.md` — wiki synthesis for this cycle.

## Gate-критерии

Validation gates:

- PF >= `1.5`
- trades/year >= `6`
- 0 negative years
- active years >= `3`
- max year trade share <= `0.60`
- bootstrap CI low >= `1.0`

Frozen test gates for Stage 10:

- Test PF >= `1.5`
- trades/year >= `6`
- 0 negative years
- baseline uplift over RF_160 validation reference and simple baselines
- no threshold/top-k/rule changes after viewing test

## Следующий шаг

Stage 11 — Robustness.

Rules before Stage 11:

- Do not retrain checkpoint.
- Do not refit normalizer.
- Do not change threshold `0.5359389781951904`.
- Do not change target, feature contract, seq_len, execution mapping, or selection rule.
- Treat Stage 10 test as already opened; do not use test to tune any rule.

## Открытые риски

- Stage 09 is single-seed deterministic; multi-seed robustness is not proven.
- Stage 10 passed aggregate gates, but trade concentration is high: max year share `72.97%`.
- Stage 06 has no purged embargo; accepted for current candidate-source workflow, but not purged-CV evidence.
- Trading metrics are gross; costs/slippage/spread are deferred to Stage 12.
- MT4 parity/export is not proven for this candidate; deferred to Stage 13.
- `provider` and `timezone` metadata gaps remain; provider-drift/transfer claims are prohibited.
- PLL parameters are initial and need ablation only after frozen-test discipline is preserved.
