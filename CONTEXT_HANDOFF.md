# Context Handoff

Дата: 2026-05-27.

## Текущий этап

Методологический цикл `methodology_cycle_candidate_source_v2` остановлен на Stage 09.

Канонический статус:

- Stages 00-08: `PASS`
- Stage 09: `FAIL`
- Stage 10: `INVALID`

Переход к Stage 11 запрещён. Нужно либо закрывать текущую гипотезу как не прошедшую validation freeze, либо начинать новую validation-гипотезу/редизайн entry protocol и снова проходить Stage 09 до любого frozen test.

## Гипотеза

Live-safe candidate-source модель на текущем срезе Nero/PIC может заменить оффлайновый `signal != 0` gate и улучшить baselines.

Decision unit: строка/бар-кандидат с 3D fractal tensor.

Decision time: момент доступности MQL/PIC fractal state в строке `Nero.csv`; future-derived labels используются только как target.

## Критичный вывод по entry timing

В текущем MT-контуре `fractal0` полностью готов только на `Close` своего подтверждающего третьего бара. После этого MQL записывает строку 100 фракталов в `Nero.csv`, watcher читает файл раз в несколько секунд, выполняет preprocessing/inference/export, и только затем торговое решение может попасть в execution path.

Следствие: online не может открыть сделку по `Close[row]`. `Close[row]`-entry разрешён только как `DIAGNOSTIC_ONLY`. Даже `Open[row+1]` может быть оптимистичным, если задержка записи строки, polling watcher-а, inference и отправки ордера не позволяют попасть к этому open.

Production-quality labels/backtests должны использовать first executable price after feature availability and runtime latency или MT tester execution.

## Что сделано

- `MT/MQL4/Files/Nero.csv` обновлён пользователем как raw source of truth; старые `DATA/Nero_*_labeled.csv` были перегенерированы.
- Pipeline прошёл Stages 00-04: raw inventory, sort/label/split, feature contract/leakage, labeling.
- Train/validation/test split: `44104 / 9451 / 9451`, temporal order preserved, test not viewed before invalid Stage 10 attempt.
- PLL normalizer fit только на train; feature/target normalization разделены, группы нормализации проверены по scale.
- Stage 05 EDA: train+validation only, test not inspected.
- Stage 06 split manifest: no row overlap, no shuffle, no sorting errors; no purged embargo, accepted with restriction.
- Stage 07 baselines: RF_160 validation PF около `1.61` under R-multiple PnL, 262 trades, 1 negative year.
- Stage 08 model sweep: exploratory validation only; not a frozen rule.
- Stage 09 deterministic Transformer checkpoint saved with round-trip diff `0.0`.
- Stage 09 current stability refreeze under R-multiple PnL + entry=`Open[row+1]`: `eligible_count=0`, `canonical_rule=null`.
- Stage 10 current artifact is invalid: no frozen Stage 09 candidate and checkpoint hash mismatch against stale rule.

## Stage 09 Current Result

Canonical source of truth:

- `ML/stage09_stability_refreeze.py` writes `stage09_stability_refreeze.json`.
- `stage09_stability_refreeze.json`: `eligible_count=0`, `canonical_rule=null`.
- Existing `stage09_frozen_rule.json` is stale/superseded from the old count-based/Close-row protocol and must not be used as canonical.

Current validation facts:

- Best broad rule: threshold `0.30`, PF около `1.05`, 5448 trades, 2 negative years.
- Best PF rule: threshold `0.65`, PF `1.50`, 5 trades, 2 negative years, bootstrap low `0.5`.
- No rule passes PF, trades/year, negative years, active years, concentration and bootstrap gates together.

Verdict: `FAIL`.

## Stage 10 Current Result

`ML/stage10_frozen_test_oos.py` now invalidates the artifact if frozen protocol checks fail.

Current `stage10_frozen_test_oos.json`:

- `stage_verdict`: `INVALID`
- `model_verdict`: `invalid_frozen_protocol`
- `checkpoint_hash_matches_rule`: `false`
- metrics are diagnostic only and must not be used as OOS evidence.

## Git

Ветка: `ml-cycle-methodology-stage-0-1`.

Важное правило: не откатывать пользовательские изменения в `processing/label_signals.py`; там зафиксирован переход к R-multiple PnL и entry=`Open[row+1]`.

## Ключевые файлы

- `ML/reports/methodology_cycle_candidate_source_v2/stage01_gate_verdict.json` — canonical stage verdicts.
- `ML/reports/methodology_cycle_candidate_source_v2/stage09_stability_refreeze.json` — current Stage 09 validation-only stability scan.
- `ML/reports/methodology_cycle_candidate_source_v2/stage09_frozen_rule.json` — stale/superseded old rule, not canonical.
- `ML/reports/methodology_cycle_candidate_source_v2/stage10_frozen_test_oos.json` — invalid diagnostic Stage 10 artifact.
- `ML/stage09_stability_refreeze.py` — Stage 09 stability scan.
- `ML/stage10_frozen_test_oos.py` — Stage 10 runner with protocol invalidation.
- `ML/validation_freeze.py` — deterministic Transformer training + checkpoint round-trip.
- `DATA/Nero_{train,validation,test}_labeled.csv` — labeled temporal splits with R-multiple PnL columns.
- `docs/reports/2026-05-25-methodology-cycle-stages-00-04.md` — current report despite legacy filename.
- `wiki/research/methodology-cycle-candidate-source-v2.md` — wiki synthesis for this cycle.

## Gate-критерии

Validation gates:

- PF >= `1.5`
- trades/year >= `6`
- 0 negative years
- active years >= `3`
- max year trade share <= `0.60`
- bootstrap CI low >= `1.0`

Stage 10 gates are not applicable until Stage 09 produces a canonical frozen rule.

## Следующий шаг

Do not run Stage 11.

Allowed next work:

- close/reject the current candidate-source hypothesis under the live-executable R-PnL protocol; or
- define a new validation hypothesis, including explicit executable entry convention; then rerun Stage 09 before any frozen test.

## Открытые риски

- Entry convention is unresolved for production: first executable price after `fractal0` readiness, row write, watcher polling, inference and order-send must be proven.
- `Close[row]` diagnostics can overstate live performance and must not be used as production evidence.
- `Open[row+1]` may still be optimistic if runtime latency misses that open.
- Stage 06 has no purged embargo; accepted for current candidate-source workflow, but not purged-CV evidence.
- Trading metrics are gross; costs/slippage/spread are deferred to Stage 12 for future valid candidates.
- MT4 parity/export is not proven for this candidate; deferred until a valid frozen candidate exists.
- `provider` and `timezone` metadata gaps remain; provider-drift/transfer claims are prohibited.
