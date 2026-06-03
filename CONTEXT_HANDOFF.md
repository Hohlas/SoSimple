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

1. **Limit-order entry convention — baseline gate пройден**: Close-entry стал исполнимым через pending лимитные ордера. BUY buy_sl3_tp3: PF=1.53 (RF) на canonical spread=0.20, gate пройден (PF≥1.3, fill_rate≥20%, trades/year≥6, negative_years=0).
2. **Spread sensitivity**: PF монотонно деградирует: 1.56→1.53→1.23→1.02 при спредах 0→0.20→0.40→0.80. Робастность ограничена.
3. **SELL не работает при canonical spread=0.20**: XAUUSD bull market асимметрия — RF PF=0.91 (3 neg years), HGB PF=1.36 (1 neg year). Все SELL комбинации FAIL по negative_years.
4. **Fill — мгновенный для BUY**: 97.4% BUY лимитников заполняются на первом же баре (lag=0). BUY fill rate ~96% при canonical spread=0.20 (98.5% при spread=0).
5. **Transformer бесполезен**: на fractal features AUC=0.5 (чистая случайность). Повторяет вывод Transformer Direction (2026-05-21): fractal features не несут predictивного сигнала для нейросети.
6. **RF работает, Transformer — нет**: RF на плоском табличном представлении цен фракталов (102 признака: f0_price..f99_price + f0_dir + ATR) даёт PF=1.53. Transformer на сырых фрактальных sequence-признаках — AUC=0.5 (random). Разрыв не в engineered features, а в способе представления: деревьям подходит flat-таблица, Transformer не извлекает сигнал из sequence фракталов.

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

1. **Entry convention**: Limit-order прошёл baseline gate (PF=1.53 BUY). Требуется проверка рабочих гипотез (см. Следующий шаг). MT4 pending-order execution отложен до подтверждения устойчивости RF-результата.
2. **Feature engineering**: Fractal features исчерпаны для нейросетей (Transformer AUC=0.5). RF-деревья работают на 102 сырых фрактальных полях. Нужны ли engineered признаки для деревьев? Или достаточно текущего flat-набора?
3. **Transformer vs RF gap**: почему Transformer не извлекает сигнал из sequence фракталов — открытый вопрос. Возможно: недостаток данных (5k BUY fill строк), архитектура (classification head vs PnL regression), или фракталы действительно не несут sequence-сигнала.
4. **SELL исключён**: structural XAUUSD bull market — дальнейшие инвестиции в SELL не оправданы.

## Следующий шаг

Этап не закрыт. Проверить гипотезы перед переходом к MT4 execution:

1. **Гипотеза: RF на engineered признаках даст PF выше**: обучить RF на `build_grouped_features` (233 признака с агрегатами по окнам) вместо 102 сырых полей. Если PF вырастет — сигнал в engineered признаках есть, а Transformer-архитектура его теряет. Если нет — сигнал исчерпан на текущих данных.
2. **Гипотеза: data split по времени даст честную оценку**: текущий split 70/15/15 делает train самыми новыми данными, val — старыми. 30-bar purge убрал 70% train. Переделать split хронологически (train — старые, val — средние, test — новые), перезапустить RF baseline, сравнить PF.
3. **Гипотеза: RF-результат воспроизводится на BUY buy_sl2_tp3**: проверить вторую TB-комбинацию (SL=2, TP=3). Если тоже PASS — сигнал робастен к выбору барьеров.
4. **Если гипотезы 1-3 подтверждены**: переходить к MT4 pending-order execution (Strategy Tester parity).
