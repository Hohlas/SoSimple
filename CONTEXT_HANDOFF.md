# Context Handoff

**Дата:** 2026-06-30

## Текущий этап

Stage 6.2 завершён. Вердикт: **TRADING_GATE_FAILED** (`DIAGNOSTIC_ONLY`).

Проверялась fixed H12 price-action feature family: последние OHLC-окна `(1, 3, 6, 12, 24)` H1 баров до `row.time`, single-bar candle fields и regime add-on (`atr14`, source volume). Цель — понять, добавляют ли эти признаки сигнал для H12 TP/SL touch сверх same-run baseline `h12_clock_shift_back`.

## Главный результат

Artifact:

- `ML/reports/stage6_2_h12_price_action_feature_family.json`
- `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md`

Полный прогон:

- `15/15` runs = 5 профилей × 3 seed
- `xgb_n_jobs=24`
- elapsed `1341s`
- runner поддерживает initial checkpoint, checkpoint after preflight, checkpoint after every run, `--resume` / `--no-resume`

Primary `h12_price_action_core`:

- median val AUC `0.6233`
- PR AUC lift `0.1402`
- selected PF `1.307`
- trades/year and spread 0.20 PF checks passed
- median permutation p-value `0.160` > required `0.10`
- итог primary gate: trading/permutation gate failed

Same-run baseline `h12_clock_shift_back`:

- median val AUC `0.6174`
- selected PF `1.249`
- permutation p-value `0.225`

Combined delta:

- `h12_clock_shift_back_plus_price_action_core`: AUC delta `+0.0098`, PF delta `+0.0766`, median permutation p-value `0.185`
- `h12_clock_shift_back_plus_price_action_regime`: AUC delta `+0.0101`, PF delta `+0.0007`, median permutation p-value `0.255`
- оба ниже required AUC delta `+0.020`; delta gate FAIL

## Методический статус

Stage 6.2 — поисковый этап. Результат не может стать кандидатом.

Feature contract:

- OHLC features use only bars with timestamp `<= row.time`.
- Unit tests mutate future bars and `Open[row+1]`; features remain unchanged.
- Future-derived columns are denied: `stage6_*`, `trade_*`, `fav_*`, `adv_*`, `ret_*`, `path_*`, breach labels, bars-to-breach labels.

Warnings:

- Legacy data smoke-check failed on unused historical target column `target_buy_H6_val`; Stage 6.2-specific checks passed, but global data-contract debt remains.
- Missing exact OHLC rows: val `3`, holdout `48`, 2026 `551`; missing rows get all-zero price-action features by explicit diagnostic contract.
- 2026 disclosure is weak for price-action profiles because `551/1162` rows have zero-vector price-action features.
- `volume` is treated as source volume, not exchange volume.

## Правильное направление дальше

1. Не продвигать Stage 6.2 в candidate.
2. Если продолжать эту ветку, сначала сделать bounded post-mortem: почему `range_w1_atr` dominates и почему permutation остаётся слабой.
3. Новый эксперимент допустим только как materially new information family, а не мелкая вариация тех же OHLC windows.

## Неправильное направление дальше

- Открывать широкий перебор horizon/ATR/TP/SL.
- Выбирать профиль, seed или threshold по `2023-2025` или `2026`.
- Сравнивать Stage 6.2 delta с Stage 6.1 “на глаз”: только same-run baseline внутри Stage 6.2 JSON.
- Утверждать, что “price action не работает вообще”; отвергнута только проверенная fixed feature family.

## Ключевые файлы

Код:

- `ML/baseline/benchmark_stage6_2_price_action.py`
- `tests/test_stage6_2_price_action.py`

Артефакты:

- `ML/reports/stage6_2_h12_price_action_feature_family.json`
- `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md`

Контекст:

- `docs/superpowers/plans/2026-06-30-stage6_2-h12-price-action-feature-family.md`
- `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`
