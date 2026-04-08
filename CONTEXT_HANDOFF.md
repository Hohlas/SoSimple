# Context Handoff

## Current Stage
Validation-first ML exit research завершён. Offline simulator на жёстком `validation` / `test` split показал, что ни `reverse`, ни `weak_edge`, ни `profit_guard`, ни layered exit не обгоняют baseline `timeout_only`. Frozen policy зафиксирован в `ML/reports/frozen_exit_policy.json`; новый MQL4 exit rule не переносился, потому что победитель уже совпадает с текущим `ML_Timeout(12H)` поведением.

## Last Completed Stage
Validation-first ML Exit Research (2026-04-08).

## Next Step
Path forward сужен: ML exit / position management не дал validated uplift против текущего timeout baseline, поэтому следующий содержательный шаг уже вне этого search space.

1. **Triple Barrier hardening**: довести parallel-трек до честного финального verdict уже без ожидания “быстрой победы” от exit-логики поверх `regression_updn`.
2. **Outcome-aligned retraining**: если нужен новый uplift для regression-track, искать его уже не в раннем закрытии, а в новом target / objective, который ближе к реальному торговому исходу.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `AGENTS.md`
- `docs/superpowers/roadmap.md`
- `docs/reports/2026-04-08-ml-exit-validation-first.md`
- `docs/reports/2026-04-04-archetype-filter-bridge.md`
- `docs/reports/2026-04-04-signal-path-atlas-readout.md`
- `docs/reports/2026-04-04-signal-quality-filter.md`
- `ML/reports/frozen_exit_policy.json`

## Open Risks
- Exit-policy uplift поверх `regression_updn` может просто отсутствовать: validation winner остался baseline `timeout_only`.
- Лучший новый кандидат (`profit_guard_p1.5_k1.8_h2`) близок к baseline по PF, но всё равно хуже него; есть риск переинтерпретировать trade-count uplift как реальное improvement.
- Position blocking остаётся высоким даже у frozen baseline (`avg_blocked_signals ≈ 3.73` на validation, `≈ 3.34` на test), но попытки лечить это одними exit-правилами пока только ухудшали PF.
- Если нужен новый edge, вероятнее всего он лежит не в выходе, а в более outcome-aligned target / execution track.

## Latest Report
`docs/reports/2026-04-08-ml-exit-validation-first.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
