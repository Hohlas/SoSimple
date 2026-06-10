# Context Handoff

Дата: 2026-06-10.

## Текущий этап

Stage 2 «Fractal Stop + Fav Trade» завершён. Результат: ❌ FAIL — торговая постановка не работает на текущих признаках.

### Результаты Stage 2

| Фаза | Статус | Результат |
|------|--------|-----------|
| Fav labeling | ✅ | 4 H-specific колонки размечены |
| Trade evaluator | ✅ | `evaluate_fractal_stop_trade()` per spec |
| Tests (9) | ✅ | Все PASS |
| Smoke check | ✅ | ALL CHECKS PASSED |
| RF baseline (val) | ✅ | 8 combos, grid search 81 порог |
| Frozen test | ✅ | sell_H12_off05 PF=0.837 |
| Критерии перехода | ❌ FAIL | PF < 1.0 на val и test |

### Ключевые находки

1. Breach-классификатор работает (AUC 0.65), fav-регрессор слаб (MSE ~3–5)
2. Ни одна комбинация порогов не дала PF > 1.0 на каноническом спреде 0.20
3. Лучшая val: sell_H12_off05 PF=0.975. Frozen test: PF=0.837, 3/5 лет убыточны
4. Diagnostic spread (0.0) даёт PF=1.06 → маржинальность не переживает издержки
5. 8 блокеров плана исправлены до реализации (H-specific колонки, stop_val_actual, _fractal_str 22→23 поля, OHLC-кеш)

### Созданные/изменённые файлы

- `processing/label_signals.py` — +2 функции
- `processing/label_main.py` — `--fractal-stop-fav`
- `tests/processing/test_fractal_stop_fav.py` — 9 тестов (NEW)
- `ML/baseline/benchmark_fractal_stop_fav.py` — RF baseline + grid search + frozen test (NEW)
- `ML/reports/fractal_stop_fav.json` — val результаты (NEW)
- `ML/reports/fractal_stop_fav_frozen_rule.json` — замороженное правило (NEW)
- `ML/reports/fractal_stop_fav_frozen_test.json` — frozen test (NEW)
- `statistics/data_contract_smoke_check.py` — +fav checks
- `docs/reports/2026-06-10-fractal-stop-fav-stage2.md` — финальный отчёт Stage 2 (NEW)
- `docs/superpowers/plans/2026-06-10-fractal-stop-fav-plan.md` — план (8 исправлений)
- `CHANGELOG.md` — запись Stage 2
- `DATA/Nero_XAUUSD_*_labeled.csv` — +4 fav колонок

### Git

Ветка: `feature/fractal-stop-fav-spec`.

### Не staged

- `docs/audit/to_do.md` — pre-existing change

## Следующий шаг

Fractal-stop research остановлен: breach сигнал не транслируется в прибыль через текущую торговую механику. Опции:

1. **Feature engineering** — новые признаки помимо фракталов (спред, волатильность, макро)
2. **Другая механика** — trailing stop, partial TP, time-based exit
3. **Более сложная модель** — Transformer, XGBoost вместо RF для fav-регрессии
4. **Другой актив/таймфрейм** — H4, индексы, другие инструменты

Решение за аналитиком.
