## 12. Backtest с торговыми издержками

### Цель

Проверить, сохраняется ли edge после реалистичного исполнения.

### Входы

- frozen signals или trades;
- OHLC/tick/tester data;
- trading protocol;
- cost assumptions;
- position constraints.

### Пошаговые действия

1. Описать cost model:
   - spread;
   - commission;
   - swap;
   - slippage;
   - requote/open failure;
   - latency;
   - next-bar entry;
   - row materialization delay;
   - watcher polling interval;
   - preprocessing/inference/export delay;
   - order-send delay;
   - position limits.

   Типовые источники и порядок величин:

   | Издержка | Источник | Типовой диапазон |
   |----------|----------|-----------------|
   | Spread | Средний спред инструмента (из MT4 логов или спецификации счёта) | XAUUSD: 20–35 пунктов |
   | Commission | Спецификация счёта (на лот или на сделку) | Зависит от брокера |
   | Slippage | Базовая из MT4/брокерских логов; стресс-тест: кратно базовой (2x, 4x, 8x) | Базовая — из логов; стресс — кратно измеренной |
   | Swap | Для H1 обычно пренебрежим, проверить при hold >= 24 бара | Зависит от брокера |
   | Missed opens | Из MT4 tester log: OPEN_FAILED / total_signals | Допустимо < 5% |

   Проверить устойчивость Net PF к удвоению каждой издержки по отдельности.

2. Проверить, что entry price исполним после feature-ready time и runtime delays.
3. Считать gross и net results отдельно.
4. Запустить offline backtest по тому же trading protocol.
5. Запустить sequential simulation для single-position или max-positions ограничения.
6. Проверить повышенные costs.
7. Разделить close reasons: SL, TP, timeout, reversal, manual/forced close.
8. Для MT4-кандидата выполнить tester run.

### Обязательные проверки

- Cost assumptions указаны до final verdict.
- Entry timing совпадает с target, export и фактической live-доступностью feature snapshot.
- Next-bar open используется только если runtime может поставить ордер к этому open; иначе применяется first executable tick/price или tester execution.
- Spread/commission/slippage не оставлены "на потом".
- Timeout PnL и SL/TP PnL анализируются отдельно.
- Пропущенные входы не считаются нулевым риском без обоснования.

### Критерии успешного завершения

- Net PF и drawdown проходят gates.
- Известно, какие издержки убивают стратегию.
- Есть список расхождений offline vs tester.
- Gross-only результат не выдан за production.

### Типовые ошибки

- Игнорировать комиссии и spread при PF около 1.
- Считать OHLC close эквивалентом tick execution.
- Использовать `Close[row]` entry для системы, где сигнал появляется только после закрытия `row`.
- Считать `Open[row+1]` автоматически исполнимым без проверки задержек записи строки, watcher-а, inference и отправки ордера.
- Не учитывать requote и missed opens.
- Делать вывод о модели по M5 diagnostic, если production H1.

### Проверка симулятора сделок

Симулятор сделок — такой же источник ошибок, как feature builder. Его логика должна быть проверена до использования результатов для verdict.

#### Обязательные проверки
- Label convention симулятора совпадает с label convention датасета (типы, диапазоны, edge cases: timeout, double-touch, reversal).
- До использования симулятора для verdict написать тесты на синтетических сделках с известным исходом:
  - TP-only → PnL положительный, close_reason=TP;
  - SL-only → PnL отрицательный, close_reason=SL;
  - Timeout → корректный timeout PnL;
  - TP+SL в одном окне → поведение соответствует конвенции.
- Не использовать simulator PF > 10 без ручной проверки первых 10 сделок.
- При изменении label convention перепроверить симулятор.

#### Типовые ошибки
- Приведение типов (int/float), маскирующее разные исходы под один.
- Ветка else, съедающая SL и timeout без разбора.
- Timeout считается loss без явного решения.

### Ветвления

- Если edge исчезает после costs: reject или redesign target/rule.
- Если расхождения только в timeout: отделить market-close risk от signal risk.
- Если requote/open failures частые: сначала чинить execution reliability, не модель.

---
