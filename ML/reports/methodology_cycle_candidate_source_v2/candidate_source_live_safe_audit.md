# Candidate-Source Live-Safe Audit

Date: 2026-05-24

## Verdict

Stage verdict: `PASS` for the new cycle only if candidate-source is defined as the all-row current Nero/PIC snapshot universe and all inputs follow `feature_contract.csv`.

The old `signal != 0` gate is `FAIL` for production candidate-source.

## Reason

`entry_path_v1_live_safe` removed the forbidden model input `ret_dir_atr_lag1`, but previous production/export flow still used `signal != 0` as candidate-source. In offline labeled data that signal is created by `processing.label_signals.label_all()` using future rows. In current live raw `Nero.csv`, MQL writes top-level `signal=0` and `predict=0`.

Therefore the new ML cycle must test a live-safe replacement for candidate-source. It may use every current row/bar as the candidate universe, or a new model-generated surrogate, but that surrogate must use only live-safe fields.

## Baselines To Beat

- All-rows ranking baseline: frozen test PF `0.9134`, sequential PF `0.5908`.
- Direct bar model baseline: frozen test PF `1.1141`, sequential PF `1.1334`.
- Direct-direction Transformer/fractal-feature track is not a valid continuation target unless a new live-safe information source is introduced.

## Allowed

- Current-row `Nero.csv` fields proven by `lib_PIC.mqh`.
- MT-origin accumulated `fractal*.Up/Dn` as current snapshot state.
- Calendar and causal past-window row features.
- Validation-only winner and threshold selection.

## Forbidden

- Offline `label_all().signal != 0` as production candidate-source.
- `predict`, `ret_*`, `fav_*`, `adv_*`, `ret_dir_atr_lag1` as inputs.
- Test-based threshold repair.
- Treating current diagnostic raw `Nero.csv` from 2026-05-22 as forward profitability evidence.

## Stage 1 Decision

No `UNKNOWN` field is allowed into model inputs. `provider` and `timezone` remain metadata gaps, so provider-transfer or timezone-sensitive claims are forbidden until separately documented. They do not block the next stage for the same local historical XAUUSD split, because they are excluded from model inputs and transfer claims.
