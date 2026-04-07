# Context Handoff

## Current Stage
Archetype × Filter Bridge завершён. `fav_3_vs_12 <= 0.653` обогащает winning архетип (+6.6 pp на holdout). `ratio_3_vs_12 > 4.751` не коррелирует с winning архетипом. Pullback поверх фильтра не нужен — winning signals не откатываются.

## Last Completed Stage
Archetype × Filter Bridge (2026-04-04).

## Next Step
Path forward выбран: идти по четырёхшаговому roadmap, сохраняя bridge-результат как текущий baseline.

1. **Сначала — validation-first protocol**: перевести весь search логики входа/выхода на `validation`, а `test` оставить как финальную проверку. Одновременно переякорить текущий bridge winner:
   - baseline candidate: `fav_3_vs_12 <= 0.653` + market
   - benchmark only: `ratio_3_vs_12 > 4.751` + pullback
   - первый search space: replicated spread features + threshold sensitivity

2. **Затем — ML exit / position management**: усилить текущий `regression_updn` трек без переобучения.

3. **Потом — Triple Barrier hardening**: довести parallel-трек до честного финального verdict.

4. **После этого — outcome-aligned retraining**: запускать новый широкий ML-трек под торговый исход, а не под raw excursions.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `AGENTS.md`
- `docs/superpowers/roadmap.md`
- `docs/reports/2026-04-04-archetype-filter-bridge.md`
- `docs/reports/2026-04-04-signal-path-atlas-readout.md`
- `docs/reports/2026-04-04-signal-quality-filter.md`

## Open Risks
- N=84 для `fav_3_vs_12 + market` — medium-sample. Достаточен для directional вывода, но точная PF оценка может сдвинуться.
- Фильтр `fav_3_vs_12 <= 0.653` enriches winning с 37% до 44% — не separation. 56% отфильтрованных сигналов всё ещё failure.
- Year-stability `fav_3_vs_12` нестабильна на discovery (деградация 2022→2024 с recovery в holdout).
- ATR bucket conditioning нестабильно (failed holdout replication при N=530).
- Locked Variant 3 winner ослаблен: оба pillar (ratio 4-5, ATR Q4) weakly supported.
- `ratio_3_vs_12 > 4.751` работает на pullback, но его edge = mechanical price improvement на failure сигналах, не archetype selection.

## Latest Report
`docs/reports/2026-04-04-archetype-filter-bridge.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
