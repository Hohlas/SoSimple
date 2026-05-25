# Context Handoff

Дата: 2026-05-25.

## Текущий этап

Завершены Stages 00–02 methodology-цикла `candidate_source_v2` на ветке `ml-cycle-methodology-stage-0-1`.

## Гипотеза

Live-safe candidate-source модель на текущем срезе Nero/PIC может заменить оффлайновый `signal != 0` gate и улучшить baselines (direct_bar_model PF 1.1141, all_rows_ranking PF 0.9134).

## Что сделано

- Nero.csv перегенерирован (63006 строк, 2004–2026, 23-полный fractal формат с `Shift`)
- Python-парсеры обновлены под 23 поля
- Добавлены новые признаки: `log_price_rel`, `atr_band_4/12`, `count_in_band_4/12`, `delta_shift_N`
- Pipeline: sort → label → split (44104/9451/9451), без in-pipeline нормализации
- PLL-нормализатор: 8 групп (price, front_back, impulse, power, count, updn_h12/24/48), fit на train, checkpoint сохранён
- Feature contract: 32 live_safe поля, 0 unknown в model inputs
- Старый `signal != 0` gate отвергнут для production

## Git

Ветка: `ml-cycle-methodology-stage-0-1`.

## Ключевые файлы

- `ML/reports/methodology_cycle_candidate_source_v2/` — все stage-артефакты
- `ML/pll_normalizer.py` + `ML/checkpoints/pll_normalizer_v1.pkl` — PLL нормализатор
- `ML/fractal_level_feature_builder.py` — обновлён (+shift, +price features, +temporal density)
- `MT/MQL4/Include/lib_PIC.mqh` — +Shift поле в CSV экспорте
- `MT/MQL4/Files/Nero.csv` — 63007 строк, 2004–2026
- `DATA/Nero_{train,validation,test}_labeled.csv` — raw размеченные сплиты
- `docs/reports/2026-05-25-methodology-cycle-stages-00-02.md` — отчёт

## Gate-критерии (зафиксированы)

- Validation PF ≥ 1.5, ≥6 сделок/год, 0 отрицательных лет
- BUY и SELL PF ≥ 1.0 (если гипотеза не односторонняя)
- Test PF ≥ 1.5, те же пороги
- Uplift над baselines: direct_bar_model PF 1.1141, all_rows_ranking PF 0.9134

## Следующий шаг

Stage 03 — Feature Contract / Leakage Gate: формальная валидация отсутствия future-derived полей в model inputs, проверка изоляции normalization pool, верификация online/training contract match.

## Открытые риски

- `body_atr_3`, `range_atr_6` — constant zero, исключены; нужен фикс pipeline для их заполнения из OHLC
- `provider`, `timezone` — metadata gaps; transfer/provider-drift claims запрещены
- PLL параметры (percentile=0.95, band widths 4/12) — начальные, могут потребовать ablation
- Flat feature path (tree models) не пропущен через тот же PLL normalizer — для деревьев не критично
