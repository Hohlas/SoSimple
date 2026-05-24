## Сводный чеклист аудита готового результата

Использовать перед повышением статуса кандидата.

- [ ] Можно указать, какие данные модель видит в момент сделки.
- [ ] Нет `UNKNOWN` признаков.
- [ ] Нет future-derived input.
- [ ] Candidate-source live-safe.
- [ ] Training и online feature contract совпадают.
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

