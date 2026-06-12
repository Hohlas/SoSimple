## 12. Backtest с торговыми издержками

### Цель

Проверить, сохраняется ли edge после реалистичного исполнения.

### Входы

- frozen signals или trades;
- OHLC/tick/tester data;
- trading protocol;
- cost assumptions;
- position constraints.
- oracle-preflight report, если trading protocol был выбран через будущие labels.

### Пошаговые действия

1. Описать cost model:
   - spread;
   - commission;
   - swap;
   - slippage;
   - requote/open failure;
   - latency (включая: row materialization delay, watcher polling interval, preprocessing/inference/export delay, order-send delay);
   - next-bar entry;
   - position limits.

   Типовые источники и порядок величин:

   | Издержка | Источник | Типовой диапазон |
   |----------|----------|-----------------|
   | Spread | Средний спред инструмента (из MT4 логов или спецификации счёта) | XAUUSD: 20–35 пунктов |
   | Commission | Спецификация счёта (на лот или на сделку) | Зависит от брокера |
   | Slippage | Базовая из MT4/брокерских логов; стресс-тест: кратно базовой (2x, 4x, 8x) | Базовая — из логов; стресс — кратно измеренной |
   | Swap | Для H1 обычно пренебрежим, проверить при hold >= 24 бара | Зависит от брокера |
   | Missed opens | Из MT4 tester log: OPEN_FAILED / total_signals | Допустимо < 5% |
   | Row materialization | Время записи строки в CSV (для watcher-контуров) | Секунды |
   | Watcher polling | Интервал проверки файла watcher-ом | Секунды |
   | Inference + export | Время preprocessing, model inference, CSV write | Сотни мс |
   | Order-send | Время отправки ордера в MT4 | Сотни мс |

   Проверить устойчивость Net PF к удвоению каждой издержки по отдельности.

   Для spread grid использовать порядок:
   - `1x canonical`: основной gate;
   - `2x stress`: обязательный стресс;
   - `4x` или выше: поиск break-point, если кандидат переживает `2x`;
   - `0x`: только optional diagnostic для отладки геометрии labeler-а и gross-edge sanity check.

   Если spread, `entry_price`, fill/no-fill policy или PnL convention влияют на labels, candidate selection или frozen rule, они относятся не только к backtest costs, а к target/execution contract. В таком случае они должны быть зафиксированы до Stage 04/07 и не могут впервые вводиться на Stage 12.

   Для OHLC-based симулятора обязательно указать price convention:
   - OHLC является bid, ask, mid или broker/tester executable price;
   - spread задан как full bid-ask spread или как уже готовый неблагоприятный price shift;
   - какие цены используются для entry, TP и SL-trigger.

   Если price convention неизвестен, результат не выше `DIAGNOSTIC_ONLY` для execution-выводов.

2. Считать gross и net results отдельно.
3. Запустить offline backtest по тому же trading protocol.
4. Запустить sequential simulation для single-position или max-positions ограничения.
5. Проверить повышенные costs.
6. Разделить close reasons: SL, TP, timeout, reversal, manual/forced close.
7. Для MT4-кандидата выполнить tester run.

### Обязательные проверки

- Cost assumptions указаны до final verdict.
- Entry timing совпадает с target и export, и entry price исполним после feature availability и runtime delays.
- Next-bar open используется только если runtime может поставить ордер к этому open; иначе применяется first executable tick/price или tester execution.
- Spread/commission/slippage не оставлены "на потом".
- Canonical spread является основным gate; zero-spread не участвует в `PASS/FAIL`.
- Выполнен stress grid по spread или явно обосновано, почему он неприменим.
- Timeout PnL и SL/TP PnL анализируются отдельно.
- Пропущенные входы не считаются нулевым риском без обоснования.

### Критерии успешного завершения

- Net PF и drawdown проходят gates.
- Известно, какие издержки убивают стратегию.
- Есть список расхождений offline vs tester.
- Gross-only результат не выдан за production.
- Zero-spread результат, если он был запущен, явно помечен `DIAGNOSTIC_ONLY`.
- Oracle-результат, если он использовался на раннем этапе, не смешан с реальным backtest результата модели.

### Типовые ошибки

- Игнорировать комиссии и spread при PF около 1.
- Считать OHLC close эквивалентом tick execution.
- Использовать `Close[row]` entry для системы, где сигнал появляется только после закрытия `row`.
- Считать `Open[row+1]` автоматически исполнимым без проверки задержек записи строки, watcher-а, inference и отправки ордера.
- Не учитывать requote и missed opens.
- Делать вывод о модели по M5 diagnostic, если production H1.
- Делать zero-spread результат каноническим или равноправным trading experiment.
- Менять spread/entry/fill convention после validation и считать это тем же frozen candidate.

### Проверка симулятора сделок

Симулятор сделок — такой же источник ошибок, как feature builder. Его логика должна быть проверена до использования результатов для verdict.

#### Обязательные проверки
- Label convention симулятора совпадает с label convention датасета (типы, диапазоны, edge cases: timeout, double-touch, reversal).
- До использования симулятора для verdict написать тесты на синтетических сделках с известным исходом:
  - TP-only → PnL положительный, close_reason=TP;
  - SL-only → PnL отрицательный, close_reason=SL;
  - SL-only с направленной spread-коррекцией согласно выбранной OHLC price convention;
  - Timeout → корректный timeout PnL;
  - TP+SL в одном окне → поведение соответствует конвенции.
- Не использовать simulator PF > 10 без ручной проверки первых 10 сделок.
- При изменении label convention перепроверить симулятор.
- SL-триггер должен проверяться по исполнимой стороне рынка, а не по абстрактной mid-цене. Если OHLC — mid и `spread` — full bid-ask spread, типовая коррекция: для BUY `stop_price + spread/2`, для SELL `stop_price - spread/2`. Если OHLC уже bid/ask или `spread` задан как полный неблагоприятный shift, формула должна быть другой и фиксируется в execution contract. Проверка SL-триггера по неподходящей цене систематически завышает или занижает PF.

#### Типовые ошибки
- Приведение типов (int/float), маскирующее разные исходы под один.
- Ветка else, съедающая SL и timeout без разбора.
- Timeout считается loss без явного решения.
- Проверять SL-триггер по цене, не соответствующей bid/ask/executable convention, — искажает PF и может маскировать реальные SL-срабатывания.

### Ветвления

- Если edge исчезает после costs: reject или redesign target/rule.
- Если расхождения только в timeout: отделить market-close risk от signal risk.
- Если requote/open failures частые: сначала чинить execution reliability, не модель.

---
