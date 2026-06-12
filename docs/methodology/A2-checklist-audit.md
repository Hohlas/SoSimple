## Сводный чеклист аудита готового результата

Использовать перед повышением статуса кандидата.

- [ ] **Smoke-check данных пройден.** Вывод `statistics/data_contract_smoke_check.py` приложен: тензор форма, NaN/inf, домены признаков, ATR-инварианты, TB-метки. См. `docs/methodology/05-eda-data-quality.md`.
- [ ] Можно указать, какие данные модель видит в момент сделки.
- [ ] Нет `UNKNOWN` признаков.
- [ ] Нет future-derived input.
- [ ] Candidate-source live-safe.
- [ ] Training и online feature contract совпадают.
- [ ] Scale audit выполнен отдельно для input-признаков и target/label колонок.
- [ ] Normalization pools не смешивают inputs с target/future-derived.
- [ ] Внутри normalization pool нет dominance крупномасштабного поля над остальными.
- [ ] Нормализация не использует future-derived поля в live-пулах.
- [ ] Global scaler fit только на train.
- [ ] Target order одинаков в train/evaluate/export.
- [ ] Rule/checkpoint/threshold заморожены до test.
- [ ] Test не использовался для выбора.
- [ ] PF не основан на малом N без пометки research-only.
- [ ] Нет скрытого провала одной стороны BUY/SELL.
- [ ] Нет скрытого провала отдельных годов.
- [ ] Издержки включены или результат помечен gross diagnostic.
- [ ] Симулятор сделок проверен на синтетических тестах с известным исходом.
- [ ] Python export соответствует MT4 opened trades.
- [ ] Online/tester расхождения классифицированы.
- [ ] Все open failures и requote видимы в логах.
- [ ] Feature contract version сохраняется рядом с prediction/trade event.
- [ ] Monitoring не меняет rule без нового validation cycle.
- [ ] Reproducibility metadata сохранена.
- [ ] Для production/confirmed кандидата есть model card.
- [ ] Старые противоречащие выводы обновлены или помечены.
- [ ] Validation не использован одновременно для early stopping, grid search и финальной оценки (val-stop / val-eval разделены).
- [ ] Множественное тестирование скорректировано (Bonferroni или permutation test с перебором всех конфигураций на каждой перестановке).
- [ ] SL-триггер проверен с направленной spread-коррекцией (bid для BUY, ask для SELL).
- [ ] Bootstrap учитывает временную корреляцию сделок (block bootstrap или stationary bootstrap).
- [ ] При использовании календарных признаков — проверена их доля в важности модели и устойчивость PF к сдвигу часового пояса.

