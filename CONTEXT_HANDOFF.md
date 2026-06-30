# Context Handoff

**Дата:** 2026-06-30

## Текущий этап

Stage 6.2 H12 price-action feature family закрыт как **TRADING_GATE_FAILED** (`DIAGNOSTIC_ONLY`).

Post-mortem по `range_w1_atr` также завершён. Он не меняет вердикт Stage 6.2 и не продвигает price-action family в candidate.

## Главные артефакты

- `ML/reports/stage6_2_h12_price_action_feature_family.json`
- `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md`
- `ML/reports/stage6_2_range_w1_postmortem.json`
- `docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md`

## Главный вывод

`range_w1_atr` действительно доминирует среди price-action признаков Stage 6.2, но доказательство слабое:

- top/second importance ratio: `7.56`;
- связь с target на non-zero `val_stop`: `corr=0.202`;
- связь с PnL почти отсутствует: `corr=0.008`;
- primary permutation p-value: `0.160` при требовании `<=0.10`;
- seed p-value range: `0.155..0.350`;
- 2026 disclosure слабый: `551/1162` zero-vector строк.

Итоговая сила доказательства в JSON: `weak`.

## Следующий шаг

Proceed to `Regression Up/Dn target foundation`.

Do not reopen H12/ATR/TP/SL search from Stage 6.2 results.

## Запрещённые направления

- Не открывать новый широкий перебор horizon/ATR/TP/SL.
- Не выбирать профиль, seed или threshold по `diagnostic_holdout` или `low_n_disclosure`.
- Не делать ещё одну мелкую вариацию тех же OHLC windows без materially new information family.
- Не утверждать, что price action вообще бесполезен; отвергнута только проверенная Stage 6.2 family.
