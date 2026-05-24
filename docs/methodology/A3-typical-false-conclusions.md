## Типовые причины ложных выводов в проекте

Эти ошибки уже проявлялись в исследованиях и должны проверяться явно:

- Высокий исторический PF был получен на future-derived inputs.
- Training feature contract не совпадал с online contract.
- Offline candidate-source был недоступен в live.
- `signal != 0` использовался как gate, хотя в live raw data он не воспроизводится тем же способом.
- Lag от future outcome ошибочно считался безопасным.
- Future-derived поле влияло на normalization pool live-признаков.
- CPU/GPU training давали разные checkpoints при одном seed.
- Stale cache обучения: после смены feature contract модель обучалась на старом кеше — метрики завышены (Pearson r 0.53 вместо реального 0.27).
- Auto-winner selection выбирал высокий PF на малом числе сделок.
- Timeout/SL label convention смешивались в симуляторе.
- Test использовался как фактическая validation через повторные попытки.
- Python export и MT4 execution считались равными без parity.
- Duplicate timestamps интерпретировались как ошибка данных, хотя это разные события одного бара.
- Online/tester PnL-разница смешивала ML signal risk и execution risk.
- Spread, slippage, requote и missed opens не были включены в ранний вывод.
- Aggregate PF скрывал слабую сторону SELL или отрицательный год.
- BUY-only или SELL-filter объявлялись улучшением после test, хотя это новая гипотеза и требует нового validation cycle.
- Рост PF объяснялся "лучшим сигналом", хотя фактически мог идти от лучшей цены входа на провальных сигналах.
- Sequential PF (SeqPF) использовался как метрика качества модели. Shuffle-тест показал разброс 0.68–4728 при одном и том же PF=1.10 — SeqPF определяется порядком сделок, а не качеством модели. Исключён из gate-критериев.

