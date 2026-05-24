## 9. Validation selection и freeze-протокол

### Цель

Выбрать одного кандидата на validation и заморозить всё до test.

### Входы

- validation predictions;
- baseline report;
- metric/gate plan;
- candidate rules;
- cost assumptions.

### Пошаговые действия

1. Провести grid/sweep только на validation.
2. Считать не только PF, но и:
   - trades count;
   - trades per year;
   - win/loss;
   - yearly/monthly slices;
   - BUY/SELL slices;
   - drawdown;
   - concentration of profit.
3. Применить production gates до выбора winner.
4. Зафиксировать один winner.
5. Сохранить rule JSON, threshold, checkpoint path, feature contract, export command.
6. Запретить изменение rule после просмотра test.

### Обязательные проверки

- Winner selection уважает minimum trades и другие gates.
- Для winner рассчитан confidence interval или bootstrap PF/EV/trade; при малом N оценён overfit risk.
- Нельзя выбирать максимальный PF среди кандидатов, которые не проходят gate.
- Test не участвует в выборе threshold/top-k/exit/filter.
- SeqPF не используется как gate-критерий выбора winner (допустим только diagnostic-only).
- Если используется ensemble/stacking, нужен out-of-fold protocol или отдельный holdout.

### Критерии успешного завершения

- Есть ровно один frozen candidate.
- Есть frozen artifacts.
- Есть validation report с rejected alternatives.
- Если winner держится на малом числе сделок, статус не выше research_only.
- Известно, какой baseline кандидат должен побить на test.

### Типовые ошибки

- `pick_winner` выбирает высокий PF на малом N без оценки статистической неопределённости.
- Менять threshold после test.
- Выбирать rule-family по test, а параметры по validation.
- Считать структурную стабильность между seeds доказанной без формального tolerance.

### Ветвления

- Если нет validation candidate, проходящего gates: reject или изменить гипотезу.
- Если несколько кандидатов близки: выбрать заранее заданным tie-breaker, а не по test.
- Если winner нестабилен между seeds: понизить статус или использовать более простое frozen rule.

---

