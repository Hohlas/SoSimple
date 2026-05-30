# Context Handoff

Дата: 2026-05-29.

## Текущий этап

Завершён Limit-Order Entry Convention experiment — проверка исполнимости Close-entry через pending BUY/SELL LIMIT на уровне Close[row].

### Результаты

| Фаза | Статус | Результат |
|------|--------|-----------|
| Spec + Plan | ✅ | Дизайн limit-order entry утверждён |
| Labeling + Pipeline + Purge | ✅ | `DATA/limit_order/` готов |
| Baseline spread grid (Phase 1+2) | ✅ | BUY PF=1.53 PASS, SELL FAIL |
| Transformer BUY (Phase 3) | ✅ | AUC=0.5 FAIL — нет сигнала |

### Ключевые находки

1. **Limit-order entry convention работает**: Close-entry стал исполнимым через pending лимитные ордера. BUY PF=1.53 (RF) на каноническом спреде 0.20, gate пройден.
2. **Spread sensitivity**: PF монотонно деградирует: 1.56→1.53→1.23→1.02 при спредах 0→0.20→0.40→0.80. Робастность ограничена.
3. **SELL не работает**: XAUUSD bull market асимметрия — все SELL комбинации FAIL по negative_years.
4. **Fill — мгновенный**: 97.4% BUY лимитников заполняются на первом же баре (lag=0). Fill rate ~96% при каноническом спреде.
5. **Transformer бесполезен**: на fractal features AUC=0.5 (чистая случайность). Повторяет вывод Transformer Direction (2026-05-21): fractal features не несут predictивного сигнала для нейросети.
6. **RF работает лучше Transformer**: за счёт деревьев на инженерных признаках, а не сырых фракталах.

### Git

Ветка: `feature/limit-order-entry-convention`.

### Созданные/изменённые файлы

- `docs/superpowers/specs/2026-05-27-limit-order-entry-design.md` — design spec (261 строк)
- `docs/superpowers/plans/2026-05-27-limit-order-entry-implementation.md` — imp plan
- `docs/reports/2026-05-29-limit-order-entry.md` — финальный отчёт
- `processing/label_signals.py` — `label_limit_order_barriers()` 
- `tests/processing/test_limit_order_barriers.py` — 15 тестов
- `processing/label_main.py` — `--limit-order --spread` флаги
- `processing/purge_split.py` — 30-bar time-based purge
- `processing/label_audit.py` — fill/ambiguity audit
- `ML/baseline/benchmark_limit_order_entry.py` — RF/HGB baseline
- `ML/baseline/reports/limit_order_spread_grid.md` — Phase 1+2 отчёт
- `ML/limit_order_train.py` — Phase 3 Transformer обучение
- `ML/reports/limit_order_transformer.json` — Phase 3 результаты
- `DATA/limit_order/` — лейблы limit-order
- `.opencode/agents/reviewer.md` — QA review agent
- `CHANGELOG.md` — запись от 2026-05-29

## Открытые вопросы

1. **Entry convention**: Limit-order (PF=1.53) — валидный кандидат для production. Нужен MT4 execution (pending orders в роботе) — отложен.
2. **Feature engineering**: Fractal features исчерпаны для нейросетей. Нужны engineered признаки (как у RF baseline) или новые источники данных.
3. **Transformer vs RF gap**: почему RF работает с engineered features а Transformer с сырыми фракталами — нет. Возможно, проблема в архитектуре (classification head вместо regression PnL) или недостатке данных (5k BUY fill строк).

## Следующий шаг

Обсудить стратегию:
- (a) MT4 execution лимитников — сделать limit-order готовым к live
- (b) Искать новые источники predictивного сигнала (не fractal features)
- (c) Улучшать RF baseline на engineered признаках (уже PF=1.53)
- (d) Закрыть ветку и переключиться на другие направления
