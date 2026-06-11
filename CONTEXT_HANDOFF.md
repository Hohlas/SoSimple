# Context Handoff

Дата: 2026-06-11.

## Текущий этап

Stage 3 «Feature Profile Comparison» завершён. `relative_geometry` (+10 фич) даёт +57…+258 bp AUC uplift над `base_raw` и является текущим победителем среди feature profile на validation. `base_plus_path` (folded mov_h + shift + atr_ratio) — провал (−64…−166 bp).

### Результаты Stage 3

| Профиль | N фич | ΔAUC mean (bp) | Вердикт |
|---------|-------|----------------|---------|
| base_raw | 1001 | — | baseline |
| base_plus_path | 1701 | −119 | ❌ FAIL — folded mov_h + shift + atr_ratio hurt |
| relative_geometry | 1011 | **+119** | ✅ PASS как целый профиль — price/ATR + density + time |

### Ключевые находки

1. Комбинированный профиль folded `mov_h` + shift + atr_ratio ухудшает RF breach AUC; отдельно компоненты ещё не изолированы
2. Price→(price−f0_price)/ATR улучшает breach AUC: делает уровни сопоставимыми при разных абсолютных ценах
3. Density (фракталы в ±1/2/3 ATR) перспективен, но вклад не изолирован от price/time; текущая реализация считает `fractal0`
4. Time-фичи (sin/cos часа + дня недели) перспективны, но вклад не изолирован
5. Все профили: 0/32 year-slices AUC<0.55 — годовая устойчивость не пострадала
6. Gap до AUC≥0.75 остаётся большим: около 7.2 процентного пункта по лучшему target и 9.2 по среднему AUC
7. Ранняя оценка пустых фрактальных ячеек была артефактом `parse_fractal()` на нормализованных float-полях; Stage 3 pandas-экстрактор этой ошибкой не затронут

### Файлы Stage 3

- `ML/baseline/benchmark_fractal_stop_stage3.py` — 3 профиля, RF breach, uplift calc (NEW)
- `ML/reports/stage3_profiles.json` — полные результаты (NEW)
- `docs/reports/2026-06-10-feature-profiles-stage3.md` — отчёт (NEW)
- `CHANGELOG.md` — запись Stage 3

### Git

Ветка: `feature/fractal-stop-fav-spec`.

### Не staged

- `docs/audit/to_do.md` — pre-existing change

## Следующий шаг

Stage 3.1: очистить и разложить `relative_geometry` на компоненты до XGBoost.

Минимальная матрица: `base_raw`, `relative_price_only`, `relative_price_plus_density_excl_f0`, `relative_price_plus_time`, `relative_geometry_clean`.

Если `relative_geometry_clean` сохраняет большую часть uplift Stage 3, следующий шаг — XGBoost/LightGBM на очищенном профиле с небольшим grid search только на validation. Test не открывать.
