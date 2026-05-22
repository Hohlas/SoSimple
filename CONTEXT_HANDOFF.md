# Context Handoff

Дата: 2026-05-19.

## Текущий этап

Direct-direction audit follow-up завершён на ветке `improve-direct-direction-results`.

Исправлены protocol/provenance blockers:

- `selection_policy()` и `selection_decision.json` для binary direct-direction benchmark;
- запрет target-dependent Up/Dn feature scaling в `normalize_rowwise()` по умолчанию;
- raw price / raw ATR distance contract через `raw_price_frame`;
- A/C `_atr` targets теперь требуют raw `up/dn / ATR`, default target-frequency использует только D для normalized split source.

## Validation Result

Запущен corrected validation-only baseline:

- nearest-k4 raw-distance features;
- Target D текущие параметры;
- RF и HGB;
- BUY/SELL side metrics;
- sequential PF;
- no frozen test.

Артефакты: `ML/reports/direct_direction_corrected_validation_baseline/`.

Итог: `winner_found=false`.

Side policy:

- BUY-only gate: fail. Лучший high-PF BUY-only slice имеет 73 сделки, ниже support floor 100.
- SELL gate: fail. SELL PF > 1 встречается только в нестабильных/one-sided/overfitting-risk rows, monotonicity не доказана.
- Combined: fail, потому что нет validation winner и обе стороны не прошли gates.

Frozen test не запускался.

## Следующий шаг

Не продолжать текущий direct-direction frozen-test путь. Если направление открывать снова, сначала материализовать raw train/validation feature-source artifacts с явным provenance, затем проверять BUY-only как отдельную validation-only гипотезу с support floor и yearly/rolling stability.

## Читать

- `docs/reports/2026-05-19-direct-direction-corrected-validation-chain.md`
- `docs/audit/2026-05-19-direct-direction-chain-audit.md`
- `ML/reports/direct_direction_corrected_validation_baseline/summary.md`
- `ML/reports/direct_direction_corrected_validation_baseline/selection_decision.json`
- `ML/reports/direct_direction_corrected_validation_baseline/feature_manifest.json`
- `ML/reports/direct_direction_corrected_validation_baseline/side_policy_summary.json`
