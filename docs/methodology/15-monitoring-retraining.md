## 15. Monitoring и retraining policy

### Цель

Не допустить, чтобы после допуска к online candidate незаметно устарел, начал работать в другом data regime или был заменён новой моделью без полного validation cycle.

### Входы

- production candidate или confirmed model;
- online predictions;
- trade event-log;
- post-factum outcomes;
- baseline distributions train/validation/locked_test;
- feature contract version;
- risk limits.

### Пошаговые действия

1. Логировать каждый prediction:
   - timestamp;
   - feature contract version;
   - checkpoint/rule version;
   - score/probability;
   - signal;
   - skip/take reason.
2. Логировать каждую сделку:
   - signal_time;
   - entry_time;
   - direction;
   - Bid/Ask;
   - spread;
   - slippage;
   - commission;
   - swap;
   - close reason;
   - PnL.
3. Мониторить signal frequency, BUY/SELL balance, score distribution и skip rate.
4. Мониторить drift live-safe признаков относительно train/validation baseline.
5. Мониторить trading metrics: net PF, EV/trade, drawdown, missed opens, requotes, timeout PnL.
6. Задать retraining triggers:
   - календарный;
   - degradation по заранее заданным метрикам;
   - data drift;
   - feature/data contract change;
   - broker/provider change.
7. Новый retrain проводить только через полный cycle методики: feature contract -> validation -> locked test -> robustness/parity -> forward.
8. Поддерживать rollback: предыдущий frozen checkpoint/rule остаётся доступен до принятия нового.

### Обязательные проверки

- Monitoring не меняет threshold/rule online без нового validation cycle.
- Drift alert означает audit, а не автоматическое включение новой модели.
- Метрики исполнения отделены от метрик качества сигнала.
- Feature contract version сохранён рядом с prediction и trade event.
- Retrain не использует forward/locked_test как validation.

### Критерии успешного завершения

- Есть monitoring checklist и incident procedure.
- Есть политика: когда кандидат остаётся `watch`, когда отключается, когда допускается retrain.
- Есть rollback procedure.
- Есть минимальный набор полей логов для post-factum reconciliation.

### Типовые ошибки

- Менять threshold по live PnL без нового validation cycle.
- Смешивать broker execution failure с деградацией модели.
- Не хранить feature contract version рядом с prediction.
- Автоматически заменять production candidate свежим retrain checkpoint.
- Считать drift proof of failure без проверки trading impact и execution layer.

### Ветвления

- Если drift есть, а PnL и risk limits нормальные: статус `watch`, усилить monitoring.
- Если execution failures растут: чинить MT4/broker layer, не модель.
- Если signal quality деградировала на достаточном N: остановить candidate и запустить новый research cycle.
- Если contract изменился: старый checkpoint нельзя использовать без compatibility audit.

---
