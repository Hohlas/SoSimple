# Entry Path v1 Direct Bar Model

## Context

Цель: проверить модель, которая сама выбирает BUY/SELL/SKIP для каждого бара.

## Winner

- probability_threshold: `0.8`
- validation trades: `1450`
- validation pf: `1.1673`
- active precision: `93.52%`
- active recall: `15.47%`
- direction accuracy on selected active: `50.74%`
- correct signal precision: `47.45%`

## Frozen Test

- trades: `1277`
- pf: `1.1141`
- win_rate: `48.24%`
- mean_pnl_atr: `0.1631`
- direction accuracy on selected active: `50.52%`
- correct signal precision: `45.50%`

## Sequential Test

- trades: `274`
- pf: `1.1334`
- win_rate: `45.26%`
- mean_pnl_atr: `0.1660`