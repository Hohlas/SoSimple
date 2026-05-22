# Combined Direct Direction Chain Audit

> **Date**: 2026-05-19
> **Status**: Completed
> **Goal**: Объединить аудиты direct-direction ветки после исследования E0-E5 и оценить, какие замечания доказаны, какие частично обоснованы, а какие требуют дополнительной проверки.
> **Related plan/spec**: `docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md`
> **Related report**: `docs/reports/2026-05-15-direct-direction-improvement.md`
> **Related audits**: `docs/audit/2026-05-18-kimi-independent-audit.md`, `docs/audit/2026-05-18-codex-direct-direction-chain-audit.md`, `docs/archive/answer.md`
> **Related commit**: pending

## Context

Исследование `2026-05-15-direct-direction-improvement` проверяло улучшение direct-direction модели, которая должна была заменить фиксированное направление `fractal0.direction` на модельное решение `SELL / SKIP / BUY` или на две независимые binary-модели.

Главный результат этапа:

| Metric | Value |
|---|---:|
| Frozen config | `D_rf_buy0.40_sell0.60_m0.10` |
| Test PF | `1.226` |
| Test Seq PF | `1.537` |
| Test trades | `2045` |
| BUY PF | `1.904` |
| SELL PF | `0.618` |
| Negative years | `2` (`2022`, `2023`) |

Результат лучше direct-bar baseline (`PF=1.114`, `SeqPF=1.133`), но не является production-ready: общий PF низкий, SELL направление убыточно, устойчивость по годам слабая.

## What Was Combined

Объединены три источника:

1. `docs/audit/2026-05-18-codex-direct-direction-chain-audit.md`
   - сильная сторона: проверка всей цепочки данных и воспроизводимые минимальные проверки;
   - главный фокус: feature provenance, нормализация, единицы измерения признаков, winner selection.

2. `docs/audit/2026-05-18-kimi-independent-audit.md`
   - сильная сторона: side-specific анализ BUY/SELL, precision, calibration, regime instability;
   - главный фокус: слабость SELL, шумность target-а, ограниченность текущих признаков.

3. `docs/archive/answer.md`
   - это не самостоятельный аудит, а скорректированный промпт для следующего исследования;
   - полезен как список проверок и анти-паттернов, но его предложения не являются доказанными выводами.

Дополнительно для проверки использованы:

- `AGENTS.md`;
- `docs/DATA_FLOW.md`;
- `docs/dataset_description.md`;
- `CONTEXT_HANDOFF.md`;
- `CHANGELOG.md` первые 300 строк;
- `wiki/index.md`;
- `wiki/research/execution-tracks-direct-direction-audit.md`;
- `ML/reports/direct_direction_chain_audit/minimal_repro_checks.json`;
- `ML/reports/entry_path_v1_binary_direction/summary.json`;
- `ML/reports/entry_path_v1_binary_direction/frozen_test.json`;
- `ML/reports/entry_path_v1_binary_direction/frozen_test_grid.csv`;
- `ML/reports/entry_path_v1_binary_direction/feature_importance.csv`;
- `processing/normalize.py`;
- `ML/fractal_level_feature_builder.py`;
- `ML/entry_path_direct_direction_targets.py`;
- `ML/benchmark_entry_path_binary_direction.py`;
- `ML/benchmark_entry_path_score_direction.py`.

## Findings By Evidence Strength

### F1. Frozen test config does not match automatic validation winner

**Verdict**: confirmed.

Evidence:

- `summary.json` winner: `D_hgb_buy0.30_sell0.60_m0.05_standalone`;
- winner has `one_sided_candidate=True`, `buy_sell_balance=0.0896`;
- `frozen_test.json` config: `D_rf_buy0.40_sell0.60_m0.10`;
- `pick_validation_winner()` in `ML/benchmark_entry_path_binary_direction.py` filters by mode, trades, PF, sequential PF and overfitting risk, but does not exclude `one_sided_candidate`, does not require `negative_years == 0`, and sorts by `validation_pf` before `validation_sequential_pf`.

Impact:

The RF frozen result is not automatically invalid, because the report explicitly preferred a balanced candidate. But the selection protocol is not mechanically reproducible from artifacts. This is a real methodology defect.

Fix:

Define winner gates in code and artifact schema:

- exclude or separately classify `one_sided_candidate=True`;
- require documented yearly-stability gate;
- sort by the exact primary metric stated in the plan;
- write an explicit `selection_decision.json` if a human overrides the automatic winner.

### F2. SELL weakness is real and severe

**Verdict**: confirmed.

Evidence from frozen test:

| Side | Trades | PF | Win rate |
|---|---:|---:|---:|
| BUY | `1202` | `1.904` | `0.527` |
| SELL | `843` | `0.618` | `0.407` |

Additional target precision check on the already-used test artifact:

| Quantity | Value |
|---|---:|
| Test rows | `9415` |
| BUY target positives | `2416` (`0.257`) |
| SELL target positives | `1745` (`0.185`) |
| Selected BUY target precision | `0.283` |
| Selected SELL target precision | `0.153` |

So the selected SELL trades have lower target precision than the unconditional SELL positive rate for Target D on the test split.

Impact:

Current SELL output is not just weaker than BUY; in this frozen artifact it behaves like an anti-signal. Any attempt to "repair SELL" by changing test thresholds would be invalid. SELL needs a new validation-only hypothesis, or it should be disabled.

Fix:

Treat SELL as rejected for the current architecture until proven otherwise on validation:

- evaluate BUY-only as an explicit one-sided candidate;
- require SELL side-specific validation gates before enabling SELL;
- do not combine BUY and SELL unless both sides pass gates.

### F3. SELL probability calibration is inverted or at least non-monotonic

**Verdict**: confirmed for the frozen artifact; not yet proven as a stable property across validation windows.

Evidence from frozen selected SELL trades:

| `p_sell` bin | Trades | Win rate | Mean return ATR |
|---|---:|---:|---:|
| `0.5..0.7` | `702` | `0.413` | `-0.596` |
| `0.7..1.0` | `141` | `0.376` | `-0.583` |

Higher SELL confidence does not improve win rate. This supports Kimi's calibration warning.

Impact:

Raising the SELL threshold is not a justified fix unless validation shows monotonic improvement after recalibration.

Fix:

Before any SELL threshold experiment:

- build calibration plots on train/validation only;
- test side-specific probability calibration, such as isotonic calibration;
- use calibration only if it improves validation, not test.

### F4. `normalize_rowwise()` lets top-level target columns influence fractal `Up/Dn` feature scaling

**Verdict**: confirmed.

Evidence:

`processing/normalize.py` builds `updn_pool` from:

- fractal fields `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48`;
- top-level row targets `up_3`, `dn_3`, `up_6`, `dn_6`, `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48`.

The minimal perturbation check in `ML/reports/direct_direction_chain_audit/minimal_repro_checks.json` changed only top-level `up_*/dn_*` values and observed changed normalized `fractal1.Up/Dn` fields:

```text
top_level_only_changed=True
fractal1_equal=False
changed_fields=up_12,dn_12,up_24,dn_24,up_48,dn_48
```

Impact:

For models trained from already-normalized split CSVs, old-fractal `Up/Dn` features can inherit scaling from row-level future targets. This does not mean every result is fully leaked, but feature provenance is unsafe for direct-direction experiments.

Fix:

Rebuild direct-direction feature source so model inputs are independent from target-only row columns:

- use raw/current-row source for features;
- keep target columns out of feature normalization;
- add a regression test: changing top-level targets must not change any model input feature.

### F5. Distance features are computed in inconsistent units

**Verdict**: confirmed.

Evidence:

`docs/DATA_FLOW.md` states that split CSVs contain normalized fractal `price` while `ATR` remains raw. `ML/fractal_level_feature_builder.py` computes:

```text
(fractal.price - fractal0.price) / ATR
```

on those split CSVs.

Impact:

`raw_distance_atr`, nearest-k ordering, zone assignment and zone aggregates do not represent true price distance in ATR units. This weakens all geometry-heavy conclusions, especially the negative result for `zones`.

Fix:

Compute distance features from raw prices and raw ATR, or explicitly store a raw-price feature source for direct-direction benchmarks.

### F6. Target A/C names imply ATR units but use normalized `up/dn`

**Verdict**: confirmed for current implementation.

Evidence:

`ML/entry_path_direct_direction_targets.py` builds:

```text
buy_fav_{horizon}_atr = source["up_{horizon}"]
buy_adv_{horizon}_atr = source["dn_{horizon}"]
sell_fav_{horizon}_atr = source["dn_{horizon}"]
sell_adv_{horizon}_atr = source["up_{horizon}"]
```

The source is the labeled split CSV where `up/dn` are normalized by `normalize_rowwise()`. They are not raw `up/dn / ATR`.

Impact:

A/C target families are mislabeled and cannot be interpreted as ATR thresholds. The decision to skip E4 because "3-class formulation is weak" is understandable, but any future A/C reuse must first fix units.

Fix:

Either:

- rebuild A/C from raw `up/dn / ATR`; or
- rename them as normalized-scale targets and set thresholds accordingly.

### F7. E5 score-direction selection is asymmetric

**Verdict**: confirmed.

Evidence:

`ML/benchmark_entry_path_score_direction.py` selects rows using:

```text
score >= old_score_threshold
and P(BUY) >= threshold
```

Then it assigns BUY or SELL by comparing `P(BUY)` and `P(SELL)`. Therefore high thresholds are BUY-confidence thresholds, not symmetric direction-confidence thresholds.

Impact:

The statement "SELL disappears at high thresholds" is not proven as a property of the data. It can be an artifact of BUY-first selection.

Fix:

Use a symmetric rule:

- candidate source: old score gate only;
- direction gate: `max(P_BUY, P_SELL) >= threshold`;
- direction: argmax side;
- report side-specific coverage and PF.

### F8. Current nearest-k features do not show strong directional signal

**Verdict**: mostly confirmed, but the exact causal interpretation is not proven.

Evidence:

`feature_importance.csv` for RF shows diffuse importances. Top features for BUY and SELL are mostly `front`, `back`, `impulse` from nearest levels. `fractal0_direction` is not in the top-20 in the checked binary RF feature importance artifact.

Impact:

This supports the claim that the current tabular geometry feature set is weak for direction prediction. It does not prove that no useful signal exists in raw data or sequence features.

Fix:

Do not keep tuning nearest-k thresholds. Test stronger feature contracts:

- raw-distance features fixed first;
- sequence/order features;
- transformer-derived score features;
- side-specific feature sets for BUY and SELL.

### F9. Target D trailing-profit target is noisy

**Verdict**: plausible but not fully proven by the audits.

Evidence:

The target has weak selected precision:

- selected BUY target precision `0.283`;
- selected SELL target precision `0.153`;
- recall is low in Kimi's audit.

However, the audits did not provide a direct comparison against alternative targets under the corrected feature contract.

Impact:

The target may be a major limitation, but the stronger proven blockers are feature provenance, units and selection protocol. Replacing Target D before fixing those would mix causes.

Fix:

After feature-source repair, run a validation-only target grid:

- corrected A/C in ATR units;
- D variants with different trail/profit/horizon;
- simpler directional close targets;
- report side-specific precision, PF and yearly stability.

### F10. Regime instability is a real risk, but causal explanation is not proven

**Verdict**: partially confirmed.

Evidence:

Frozen test yearly PF:

| Year | Trades | PF |
|---|---:|---:|
| 2022 | `92` | `0.350` |
| 2023 | `512` | `0.939` |
| 2024 | `600` | `1.309` |
| 2025 | `620` | `1.482` |
| 2026 | `221` | `2.430` |

SELL is bad across the already-used test artifact. Kimi's bull-regime explanation is plausible, but the audit did not prove it as the root cause.

Impact:

Single chronological split is insufficient to claim stability. The system may be exploiting a favorable period rather than learning a durable rule.

Fix:

Use rolling or walk-forward validation before any new frozen test. Report side-specific PF by window and year.

### F11. "PF > 2.0 is impossible on current features" is not proven

**Verdict**: not proven.

Evidence:

The current results show weak performance and several pipeline defects. They do not prove a mathematical or empirical upper bound for all corrected feature/target variants. Kimi's statement is useful as a warning, not as a verified conclusion.

Impact:

The correct conclusion is narrower: continuing threshold tuning on the current normalized split features is unjustified. A corrected rebuild is required before declaring the direction task impossible.

Fix:

State the stop rule explicitly:

- if corrected validation-only rebuild cannot exceed agreed gates, close the direction research line;
- do not infer impossibility from defective artifacts alone.

### F12. "Use Transformer encoder" and "regime-aware features" are valid hypotheses, not audit findings

**Verdict**: speculative recommendations.

Evidence:

Project docs show the regression_updn Transformer has meaningful target correlations and `pred_ret_24_dir_atr` is already important in entry-path systems. But the audits did not run controlled experiments using transformer-derived features in the direct-direction setup.

Impact:

These are reasonable next experiments, not proven fixes.

Fix:

Add them to a follow-up plan after the data contract is fixed:

- baseline: corrected raw nearest-k only;
- add transformer score feature;
- add regime features;
- compare by validation-only gates.

## Consolidated Root Cause Assessment

The strongest combined conclusion is:

> The 2026-05-15 direct-direction result should not be improved by threshold tuning. The current experiment chain has feature-source and metric-selection defects, and the published frozen artifact shows a severe SELL failure.

Root causes by confidence:

| Priority | Root cause | Confidence | Why |
|---|---|---:|---|
| 1 | Target-dependent feature normalization | High | Minimal perturbation check confirms it |
| 2 | Wrong units for distance/zone features | High | Code uses normalized price divided by raw ATR |
| 3 | Winner selection not reproducible | High | `summary.json` winner and frozen config differ |
| 4 | SELL anti-signal in frozen artifact | High | PF, precision and yearly breakdown confirm it |
| 5 | A/C targets mislabeled as ATR units | High | Code uses normalized split `up/dn` |
| 6 | E5 asymmetric BUY-first threshold | High | Code confirms selection rule |
| 7 | Target D noise | Medium | Supported by precision/recall, not isolated experimentally |
| 8 | Regime instability | Medium | Yearly PF confirms instability, cause unknown |
| 9 | Need Transformer/regime/alternative targets | Low as finding, medium as hypothesis | Plausible but not yet tested |

## Recommended Next Plan

### Gate 0. Freeze test discipline

Before any new experiment:

- mark test split as closed for this line until a final candidate is frozen;
- all new decisions use train/validation or walk-forward validation only;
- write selection gates into code.

Success:

- candidate selection is reproducible from a machine-readable artifact.

### Gate 1. Repair feature and target provenance

Required fixes:

- build direct-direction features from raw/current-row data;
- ensure model input is unchanged when top-level target columns are perturbed;
- compute distances in raw price / raw ATR;
- rebuild A/C targets from raw `up/dn / ATR` or rename them honestly;
- add tests for all above invariants.

Success:

- provenance tests pass;
- feature manifest distinguishes `feature_source`, `target_source`, `diagnostic_source`.

### Gate 2. Re-run minimal validation baseline

Run corrected validation-only baseline:

- nearest-k4 raw-distance features;
- Target D current parameters;
- RF and HGB;
- side-specific metrics;
- no frozen test.

Success:

- validation PF and sequential PF exceed old weak baseline; or
- result proves that previous uplift was caused by defective features/selection.

### Gate 3. Side policy

Evaluate side-specific policy on validation:

- BUY-only;
- SELL-only diagnostic;
- combined only if both sides pass.

Suggested gates:

- BUY-only: validation PF >= `1.5`, SeqPF >= `1.5`, yearly instability acceptable;
- SELL: side PF > `1.0` and calibrated confidence monotonicity;
- combined: both sides pass side gates.

### Gate 4. New hypotheses after contract repair

Only after Gates 0-3:

- corrected target grid: A/C/D variants and directional close;
- symmetric score-direction resolver;
- transformer-derived `pred_ret_24_dir_atr` as an input feature;
- regime-aware features;
- sequence/order features.

Each experiment must have:

- validation-only gate;
- side-specific PF;
- yearly or rolling-window stability;
- explicit stop condition.

### Gate 5. One final frozen test

Run one frozen test only for the selected final candidate. If no candidate passes validation gates, close the line without a new test.

## Final Verdict On The Audits

The Codex audit is the most technically solid because its core claims are tied to code and reproducible checks. Its recommendations should be treated as blockers.

The Kimi audit is useful and mostly directionally correct on SELL failure, calibration and methodological risk. Its strongest numeric SELL findings are confirmed. However, its broader claims about impossibility, bull-regime causality and transformer/regime fixes are hypotheses, not proven audit conclusions.

`docs/archive/answer.md` should be treated as a follow-up research prompt. It contains good checklists and anti-patterns, but it should not be cited as evidence unless the proposed checks are executed.

Overall decision:

1. Do not continue tuning thresholds on the current normalized split feature set.
2. Do not enable SELL from the current model.
3. Rebuild feature/target provenance first.
4. Use BUY-only only as a clearly labeled interim validation candidate, not as proof of a robust two-sided system.
5. Require rolling/side-specific validation before any production or MT4 parity work.

