# Context Handoff

## Current Stage
Этап `entry_path_v1_quantile` завершён.

Что зафиксировано:

- новый трек `entry_path_v1_quantile` встроен в обучение, оценку, экспорт и benchmark;
- выпущены live-артефакты:
  - `ML/checkpoints/transformer_entry_path_v1_quantile_best.pt`
  - `ML/checkpoints/transformer_entry_path_v1_quantile_result.json`
  - `ML/reports/entry_path_v1_quantile_{train,validation,test}_predictions.csv`
  - `ML/reports/evaluate_test_entry_path_v1_quantile.md`
  - `ML/reports/entry_path_v1_quantile_filter_{report,selected_rule,validation_summary,test_summary}.*`
- по текущему run success gate пройден;
- winner quantile-layer: `lb_gt_m` поверх frozen baseline `A @ 7.5%`.

## Last Completed Stage
Entry Path v1 Quantile (2026-04-10).

## Next Step
1. Слить ветку `entry-path-v1-quantile` в `main`.
2. Отдельным коротким этапом проверить устойчивость на нескольких seeds.
3. После подтверждения устойчивости решить вопрос о переносе quantile confidence-layer в MT4-контур.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `AGENTS.md`
- `docs/reports/2026-04-10-entry-path-v1-quantile.md`
- `docs/reports/2026-04-09-entry-path-trade-filter.md`
- `ML/reports/entry_path_v1_quantile_filter_selected_rule.json`
- `ML/reports/evaluate_test_entry_path_v1_quantile.md`

## Open Risks
- Результат подтверждён одним основным run; multi-seed стабильность ещё не подтверждена.
- MT4 parity-check для нового quantile-layer ещё не проводился.
- Класс `path_6_class = +1` в исторических этапах оставался слабым; здесь фокус был на quantile-слое для `ret_24`.

## Latest Report
`docs/reports/2026-04-10-entry-path-v1-quantile.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
