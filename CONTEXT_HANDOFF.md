# Context Handoff

**Дата:** 2026-06-30

## Текущий этап

Stage 6.3 H6 feature parity check закрыт как **DIAGNOSTIC_ONLY** (`NO_ADDITIVE_VALUE_CONFIRMED`).

H6 parity confirmed: shorter horizon (H6) improves ranking over H12 (AUC 0.665 vs 0.617) but permutation robustness remains weak. Geometry features still fail on H6. Price-action shows a stronger trace on H6 but still fails the delta gate.

Stage 6.3 is a bounded diagnostic — it does not change the standing conclusions from Stage 6.1 and 6.2.

## Главные артефакты

- `ML/reports/stage6_3_h6_feature_parity.json`
- `docs/reports/2026-06-30-stage6_3-h6-feature-parity-check.md`
- `ML/baseline/benchmark_stage6_3_h6_feature_parity.py`
- `tests/test_stage6_3_h6_feature_parity.py`

## Главный вывод

H6 horizon helps ranking but does not fix the core robustness problem (permutation p-values remain high). No profile or combined profile passes the delta gate. The bounded H6 parity check is complete.

## Следующий шаг

Proceed to `Regression Up/Dn target foundation`.

Do not reopen H6/H12/ATR/TP/SL search from Stage 6.3 results.

## Запрещённые направления

- Не открывать новый широкий перебор horizon/ATR/TP/SL.
- Не выбирать профиль, seed или threshold по `diagnostic_holdout` или `low_n_disclosure`.
- Не использовать H6 parity как аргумент для возобновления geometry или price-action поиска.
