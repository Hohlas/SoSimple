# Context Handoff

**Дата:** 2026-06-29

## Текущий этап

Stage 6.1 завершён. Вердикт: **MODEL_GATE_FAILED** (`DIAGNOSTIC_ONLY`).

Гипотеза отвергнута: локальная геометрия фракталов вокруг fractal0, закодированная как относительные ATR-координаты, не предсказывает, какой барьер будет достигнут первым за 12 H1 баров.

## Что сделано в Stage 6.1

Новый модуль `ML/baseline/benchmark_stage6_1_relative_geometry.py`:

- Экстракция фракталов с относительными ATR-координатами
- 5 профилей геометрии: nearest_price, nearest_time, corridor3, corridor10, zones10 + baseline clock_shift_back
- A7-style preflight для всех профилей
- Definitive touch evaluation (только TP-vs-SL definitive rows для метрик, timeout исключён)
- Trading gate
- Runtime contract: `xgb_n_jobs=24`, heartbeat, checkpoint before preflight, checkpoint after each run, `--resume` / `--no-resume`, top-level and per-run `elapsed_sec`

## Главный результат

Полный прогон:

- artifact: `ML/reports/stage6_1_h12_relative_fractal_geometry.json`
- report: `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`
- `18/18` runs = 6 профилей × 3 seed
- elapsed: `3581s` (59.7 мин)
- gate: `MODEL_GATE_FAILED`

Primary `h12_corridor3_relative_geometry`:

- median val AUC: `0.5316` (случайный)
- threshold status: `NO_THRESHOLD`
- все 5 геометрических профилей показали AUC 0.51–0.55

Baseline `h12_clock_shift_back` подтверждает валидность эксперимента:

- median val AUC: `0.6174`
- threshold SELECTED, PF 1.249

## Методические ограничения

- Stage 6.1 — `DIAGNOSTIC_ONLY`, не может стать `CANDIDATE`.
- H12 фиксирован, TP/SL унаследованы от Stage 6.0.
- Только XAUUSD H1.
- Только одна семья признаков (fractal-level geometry).

## Правильное направление дальше

1. **Stage 6.2 (рекомендуется):** новая семья признаков (multi-timeframe momentum, micro-structure, объем) для H12.
2. **Stage 6.0 refinement:** ансамблирование или калибровка для улучшения trading PF baseline.
3. **Архивировать Stage 6.1** — код и отчёт сохранены, дальнейших вложений в fractal-level geometry для H12 не требуется без новых данных.

## Неправильное направление дальше

- Открывать перебор horizon/ATR/TP/SL.
- Выбирать порог или профиль на `2023-2025`.
- Признавать Stage 6.1 кандидатом.
- Продолжать инвестиции в fractal-level geometry features.

## Ключевые файлы

Код:

- `ML/baseline/benchmark_stage6_1_relative_geometry.py`
- `tests/test_stage6_1_relative_geometry.py` (`19` тестов)

Артефакты:

- `ML/reports/stage6_1_h12_relative_fractal_geometry.json`
- `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`
