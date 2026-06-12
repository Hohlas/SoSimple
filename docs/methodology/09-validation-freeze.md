## 9. Validation selection и freeze-протокол

### Цель

Выбрать одного кандидата на validation и заморозить всё до test.

### Входы

- validation predictions;
- baseline report;
- metric/gate plan;
- candidate rules;
- cost assumptions.

### Разделение validation

Если validation используется одновременно для model selection, подбора торгового правила и финальной оценки PF, он должен быть разделён хронологически на непересекающиеся роли:

- **val-stop**: для действий, влияющих на модель — early stopping, выбор числа деревьев/эпох, ablation winner.
- **val-select**: для grid search торговых параметров, threshold/top-k и выбора rule-family.
- **val-eval**: для финальной оценки уже выбранного правила перед test.

Запрещено использовать один и тот же набор данных для early stopping, grid search и финальной оценки, если результат претендует на `PASS` или frozen-candidate. Размер и границы разделения фиксируются до начала работы.

### Пошаговые действия

1. Провести grid/sweep только на `val-select`. `val-stop` не участвует в торговой оптимизации.
2. Считать не только PF, но и:
   - trades count;
   - trades per year;
   - win/loss;
   - yearly/monthly slices;
   - BUY/SELL slices;
   - drawdown;
   - concentration of profit.
3. Применить production gates до выбора winner.
4. Зафиксировать один winner и оценить его на `val-eval` без изменения правила.
5. Сохранить rule JSON, threshold, checkpoint path, feature contract, export command.
6. Сохранить execution contract: `entry_price`, spread, fill policy, PnL convention, no-fill handling.
7. Запретить изменение rule после просмотра test.
8. При grid search из N конфигураций зафиксировать N и применить коррекцию на множественное тестирование: отдельный `val-eval`, Bonferroni/FDR/Holm или permutation test с повторением того же процесса выбора на каждой перестановке.
9. Если используется permutation test после grid search: на каждой перестановке нужно повторять тот же search/selection protocol, что и на реальных предсказаниях. Permutation test только на уже выбранном grid — диагностический, а не полная коррекция множественного перебора.

### Обязательные проверки

- Winner selection уважает minimum trades и другие gates.
- Для winner рассчитан PF uncertainty: block bootstrap, stationary bootstrap или другой метод, учитывающий временную корреляцию сделок. Winner не выбирается только по точечному PF: сначала обязательные gates, затем заранее заданный risk-adjusted tie-breaker (`BS_p05`, EV/trade lower bound, drawdown limit и т.п.). При малом N оценён overfit risk.
- Нельзя выбирать максимальный PF среди кандидатов, которые не проходят gate.
- Test не участвует в выборе threshold/top-k/exit/filter.
- SeqPF не используется как gate-критерий выбора winner (допустим только diagnostic-only).
- Если используется ensemble/stacking, нужен out-of-fold protocol или отдельный holdout.
- Frozen rule невалиден после изменения `entry_price`, canonical spread, fill policy или PnL convention.
- Validation PF для execution-aware кандидата считается по PnL, а не по счёту TP/SL.
- Zero-spread validation sweep не может выбрать frozen winner для production, если canonical spread не равен нулю.

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
- Подменять frozen execution convention после validation и считать это тем же кандидатом.
- Сравнивать canonical-spread winner с zero-spread candidate как с равноправными торговыми вариантами.
- Считать рост PF доказательством улучшения модели без проверки, что изменился рейтинг сделок, а не цена входа: если PF вырос после смены entry_price/spread/fill, а рейтинг сделок не изменился — это entry-price effect, не signal improvement.
- Использовать validation для early stopping, grid search И финальной оценки одновременно (тройная утечка). Каждый уровень оптимизации на одном наборе завышает итоговую оценку.
- Не корректировать множественное тестирование при переборе >10 конфигураций на одном validation. Чем больше search budget, тем выше риск ложного winner; результат без коррекции не должен становиться frozen-candidate.

### Ветвления

- Если нет validation candidate, проходящего gates: reject или изменить гипотезу.
- Если несколько кандидатов близки: выбрать заранее заданным tie-breaker, а не по test.
- Если winner нестабилен между seeds: понизить статус или использовать более простое frozen rule.

---
