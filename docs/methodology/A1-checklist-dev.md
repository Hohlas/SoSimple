## Сводный чеклист разработки

Использовать перед запуском нового ML-кандидата.

- [ ] Гипотеза описана до экспериментов.
- [ ] `decision_time` зафиксирован.
- [ ] Raw data inventory создан.
- [ ] Data Producer Audit выполнен: producer-код изучен, момент доступности полей доказан.
- [ ] Feature contract заполнен для всех input fields.
- [ ] Leakage preflight: `PASS`.
- [ ] Candidate-source live-safe: механизм отбора строк-кандидатов работает без оффлайн-разметки.
- [ ] Target contract описан и проверен.
- [ ] Для multi-target регрессии проверены корреляция, монотонность и метрики по каждому горизонту.
- [ ] Preprocessing воспроизводим.
- [ ] Scale audit выполнен отдельно для input-признаков и target/label колонок.
- [ ] Normalization groups выбраны по роли, фактическому масштабу и смыслу; dominance внутри pool проверен.
- [ ] Нормализация не использует будущие поля и не смешивает input с target/label в одном pool.
- [ ] Split строго временной. Для событийного ряда учтена специфика неравномерного сэмплирования.
- [ ] Validation/test/forward границы указаны.
- [ ] Baseline-модели запущены.
- [ ] Метрики и gates заданы до validation sweep.
- [ ] Hyperparameter/model selection не использует test.
- [ ] Один frozen candidate выбран на validation.
- [ ] Rule/checkpoint/exporter заморожены до test.
- [ ] Test открыт один раз для frozen candidate.
- [ ] Backtest учитывает spread, commission, swap, slippage и position limits. Проверена устойчивость к удвоению издержек.
- [ ] Симулятор сделок проверен на синтетических тестах с известным исходом.
- [ ] Проверены yearly/monthly slices.
- [ ] Проверены BUY/SELL отдельно.
- [ ] Проверена multi-seed или иная устойчивость.
- [ ] Export parity выполнен перед MT4 verdict.
- [ ] MT4 tester/reconciliation выполнены для execution candidate.
- [ ] Forward/online diagnostic не смешан с historical test.
- [ ] Для production retrain зафиксированы seed, устройство. Проверена воспроизводимость на локальной машине.
- [ ] Monitoring/retraining policy описана для production candidate.
- [ ] Для принятого кандидата создан model card.
- [ ] Итоговый отчёт содержит commands, artifacts, limitations, next step.
