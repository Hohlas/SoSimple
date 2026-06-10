# Context Handoff

Дата: 2026-06-10.

## Текущий этап

Stage 1 «Fractal Stop Breach — Пробой уровня» завершён. Сигнал подтверждён на val и frozen test. Готовимся к Этапу 2: Торговый слой.

### Результаты Stage 1

| Фаза | Статус | Результат |
|------|--------|-----------|
| Spec + Plan | ✅ | Дизайн утверждён, 3 бага в спеке исправлено |
| Labeling + Tests | ✅ | `label_fractal_stop_breach()`, 10 тестов PASS |
| Smoke check | ✅ | Breach колонки ∈ {0,1}, ALL CHECKS PASSED |
| Baseline (RF, val) | ✅ | 8 primary таргетов, AUC 0.62–0.68, lift 1.52–1.77 |
| Frozen test (test) | ✅ | H=6/off=0.2, buy AUC=0.640, sell AUC=0.649 |

### Ключевые находки

1. **Фрактальные признаки несут сигнал о пробое уровня**: RF AUC 0.64–0.68 на val, 0.64–0.65 на frozen test. Dummy = 0.5.
2. **H=12 лучше H=6**: AUC 0.68 vs 0.64, PR-AUC 0.76 vs 0.62. Длинный горизонт — больше событий, меньше дисбаланс (breach 50–63% vs 38–47%).
3. **SELL ≳ BUY**: AUC на 0.01–0.03 выше. XAUUSD bull market даёт больше SELL-кандидатов.
4. **RF работает на 1001 плоском признаке**: 10 каналов × 100 фракталов + ATR. Feature contract с allowlist.

### Git

Ветка: `feature/fractal-stop-fav-spec`.

### Созданные/изменённые файлы

- `processing/label_signals.py` — `label_fractal_stop_breach()`, константы `BR_*`
- `processing/label_main.py` — `--fractal-stop-breach`
- `tests/processing/test_fractal_stop_breach_labels.py` — 10 тестов
- `ML/baseline/benchmark_fractal_stop_breach.py` — baseline + frozen test
- `ML/reports/fractal_stop_breach_baseline.json` — отчёт val
- `ML/reports/fractal_stop_breach_frozen_test.json` — отчёт frozen test
- `statistics/data_contract_smoke_check.py` — breach-проверки
- `docs/reports/2026-06-10-fractal-stop-breach-stage1.md` — финальный отчёт
- `docs/superpowers/plans/2026-06-10-fractal-stop-breach-plan.md` — план
- `docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md` — спек (был до начала)
- `CHANGELOG.md` — запись 2026-06-10
- `DATA/Nero_XAUUSD_*_labeled.csv` — +12 breach колонок

### Не staged (untracked/modified, не committено)

- `docs/audit/to_do.md` — pre-existing change на ветке (не Stage 1)

## Следующий шаг

План Этапа 2 готов: [`docs/superpowers/plans/2026-06-10-fractal-stop-fav-plan.md`](docs/superpowers/plans/2026-06-10-fractal-stop-fav-plan.md).

Задачи плана:
1. `label_fractal_stop_fav_targets()` — fav regression labels
2. `evaluate_fractal_stop_trade()` — first-touch SL/TP/TIMEOUT per spec
3. Подключение в `label_main.py` (`--fractal-stop-fav`)
4. Тесты (4 fav + 5 trade evaluation)
5. RF baseline с grid search порогов на val
6. Frozen test

Ключевые решения:
- RF regressor (не Transformer — RF уже доказал пригодность на фракталах)
- Grid search: p ∈ {0.3,0.4,0.5}, min_fav ∈ {0.3,0.5,0.7}, min_rr ∈ {1.0,1.5,2.0}, tp_fraction ∈ {0.3,0.5,0.7}
- Spread: 0.20 canonical, 0.40 stress, 0.0 diagnostic
- Минимум 30 сделок/год на val для допуска

Готов к выполнению.

## Контекст для Этапа 2

- Данные готовы: `DATA/Nero_XAUUSD_*_labeled.csv` с breach-колонками
- Baseline: `ML/baseline/benchmark_fractal_stop_breach.py` — можно расширить
- Спек: `docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md` стр. 173+
- Лучшая конфигурация: H=12, off=0.2, sell (AUC=0.68, PR-AUC=0.76)
- Frozen test подтвердил сигнал для H=6/off=0.2
- Test нельзя переиспользовать для выбора — только для финального frozen test Этапа 2
