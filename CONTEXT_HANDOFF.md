# Context Handoff

## Current Stage
Archetype × Filter Bridge завершён. `fav_3_vs_12 <= 0.653` обогащает winning архетип (+6.6 pp на holdout). `ratio_3_vs_12 > 4.751` не коррелирует с winning архетипом. Pullback поверх фильтра не нужен — winning signals не откатываются.

## Last Completed Stage
Archetype × Filter Bridge (2026-04-04).

## Next Step
Принять решение о path forward:

1. **Если приоритет — EA-прототип**: реализовать `fav_3_vs_12 <= 0.653` + market entry в EA. PF=1.78 на 84 holdout trades. Требует:
   - Добавить вычисление `fav_3_vs_12` в `generate_signals.py` или EA
   - Порого��ое значение: `pred_fav_3 / pred_fav_12 <= 0.653`
   - Вход: market entry при выполнении условия

2. **Если приоритет — улучшение фильтра**: искать лучший archetype predictor через replicated atlas features (spread slices, cross-horizon ratios). Текущий фильтр обогащает winning с 37% до 44% — это enrichment, не separation. Потенциальные направления:
   - Комбинация `fav_3_vs_12 <= 0.653` с replicated spread features
   - Проверить BUY/SELL split внутри фильтра (BUY advantage реплицирован)
   - Threshold sensitivity analysis

3. **Если приоритет — увеличение N**: `ratio_3_vs_12 > 4.751` даёт больше сигналов (176 vs 84), но работает только через pullback (market PF=0.81). Его edge — mechanical, не archetype-driven. Использовать только если готовы принять pullback mechanics как рабочую модель.

## Read First
- `AGENTS.md`
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
