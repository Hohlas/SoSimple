# Context Handoff

**Дата:** 2026-06-29

## Текущий этап

Stage 6.0 завершён. Вердикт: **MODEL_GATE_FAILED** (DIAGNOSTIC_ONLY).

## Что сделано

Построен isolated outcome-based baseline (TP/SL/timeout, first-touch scanning, entry `Open[row+1]`) на XAUUSD H1:

- **Preflight pass:** TP rate 37%, timeout 4%, валидных rows > 5k на каждом split
- **Oracle baseline:** all-trade PF ~0.96 (timeout компенсирует часть SL потерь)
- **Primary profile `clock_shift_back`:** median val AUC 0.585 (gate: ≥0.60 → **FAIL**)
- **PR AUC lift:** 0.079 (> 0.05 → PASS, но недостаточно)
- **Permutation p-value:** 1.0 — threshold PF не лучше случайного
- **JSON artifact:** `ML/reports/stage6_0_outcome_based_triple_barrier.json`
- **Report:** `docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`

## Главный результат

Outcome-based TP/SL target **не даёт устойчивого сигнала** с текущими признаками. AUC ~0.585, PF ~0.96, permutation p-value = 1.0. Модель не может отделить TP-сделки от SL/timeout выше случайного уровня.

All-trade baseline уже даёт PF ~0.96, и модель не улучшает его. Threshold selection бессмысленна — любой порог даёт тот же PF.

Timeout как отдельный исход оправдан (4% сделок, профиль отличен от SL), но доля слишком мала для существенного влияния.

## Методические ограничения

- Вход `Open[row+1]` — DIAGNOSTIC_ONLY (runtime timing не проверен)
- Spread stress: 0.20 и 0.40 price-unit (диагностические, снижают PF на 5-10%)
- Same-bar ambiguity: консервативный SL_FIRST
- Горизонт 24 бара фиксирован (не оптимизировался)
- `clock_shift_back` — единственный primary профиль

## Правильное направление дальше

1. **Regression Up/Dn (восстановить Stage 4 направление).** Outcome-based классификация не работает — попробовать предсказывать величину движения (up/dn в risk units) через регрессию без бинарного порога.
2. **Feature redesign.** `clock_shift_back` исчерпан. Нужны признаки, учитывающие режим волатильности, уровни накопления, или макро-контекст.
3. **Multi-timeframe.** H1 может быть слишком мелким для структурных сигналов — проверить H4/H12.

## Неправильное направление дальше

- Продолжать outcome-based TP/SL с текущими признаками.
- Открывать новый parameter search по horizon/ATR.
- Пытаться чинить threshold selection — проблема не в пороге, а в отсутствии сигнала.

## Ключевые файлы

Код:
- `ML/baseline/benchmark_stage6_outcome_based.py` — новый модуль
- `tests/test_stage6_outcome_based.py` — 12 тестов

Артефакты:
- `ML/reports/stage6_0_outcome_based_triple_barrier.json`
- `ML/reports/stage5_4_fast_price_atr_ablation.json`
- `ML/reports/stage5_3_time_to_breach_target_reformulation.json`

Документация:
- `docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`
- `docs/superpowers/plans/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`
