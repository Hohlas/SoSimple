# Context Handoff

## Current Stage
Variant 4 (Signal Quality Filter Research) завершён. Два holdout-confirmed кандидата готовы к верификации через Signal Path Atlas.

## Last Completed Stage
Signal Quality Filter Research (Variant 4) завершён 2026-04-04.

## Next Step
Верифицировать два holdout-confirmed кандидата из Variant 4 cross-analysis через Signal Path Atlas pipeline:

1. **Агрессивный**: `ratio_3_vs_12 > 4.751 + pullback entry_close-1ATR` (PF=1.62, N=94 holdout)
2. **Консервативный**: `ratio_3_vs_12 > 4.751 + pullback entry_close-3ATR` (PF=3.52, N=24 holdout)

Конкретно:
- Проверить, поддерживает ли path geometry (first-passage, ordering) pullback entry для cohort `ratio_3_vs_12 > 4.751`
- Убедиться, что atlas-level replication подтверждает cross-analysis findings
- Проверить BUY/SELL split внутри фильтров и threshold sensitivity
- Оставить Variant 3 winner `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR` только как benchmark

## Read First
- `AGENTS.md`
- `docs/reports/2026-04-04-signal-quality-filter.md`
- `docs/reports/2026-04-03-signal-path-atlas.md`
- `docs/reports/2026-04-02-signal-research-variant-3.md`
- `docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md`
- `docs/superpowers/plans/2026-04-03-signal-quality-filter.md`
- `API/signal_quality_research.py`
- `API/signal_path_atlas.py`

## Open Risks
- `ratio_3_vs_12 > 4.751 + pullback 3ATR`: holdout N=24 — medium-support, не large-sample.
- `fav_3_vs_12 <= 0.653` показывает нестабильный year-split на discovery (деградация 2022→2024) с recovery на holdout — может быть mean reversion или артефакт.
- Pullback entry сам по себе — generic "better price" effect; quality filter добавляет uplift, но не полностью отделим от generic эффекта.
- Negative control check показал, что `ratio_3_vs_12 > 4.751` частично generic (non_Q4 тоже улучшается).
- Signal Path Atlas smoke run всё ещё даёт `execution_implications = neither` — atlas interpretation layer ещё не завершён.
- `API/signal_path_atlas.py` и `API/signal_quality_research.py` — два крупных single-file research modules; при дальнейшем росте может потребоваться разделение.

## Latest Report
`docs/reports/2026-04-04-signal-quality-filter.md`
