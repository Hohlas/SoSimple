# Entry Path v1 Causal Surrogate

## Context

Цель: проверить, можно ли причинно воспроизвести offline `signal != 0` и затем применить score gate.

## Winner

- probability_threshold: `0.5`
- validation trades: `43`
- validation pf: `1.0507`
- active precision: `21.11%`
- active recall: `88.28%`

## Frozen Test

- trades: `36`
- pf: `1.1537`
- win_rate: `58.33%`
- mean_pnl_atr: `0.2319`

## Sequential Test

- trades: `31`
- pf: `1.4111`
- win_rate: `64.52%`
- mean_pnl_atr: `0.5854`