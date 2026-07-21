## 9. Validation selection и freeze-протокол

### Цель

Выбрать одно правило на validation и заморозить всё до `locked_test`.

Этот раздел относится к позднему проверочному контуру. Он не предназначен для
широкого поиска. Если правило пришло из `research_hypothesis`, его
`origin_bias` сохраняется в отчёте; freeze проверяет одно заранее выбранное
правило, а не стирает историю поиска.

### Входы

- validation predictions;
- baseline report;
- metric/gate plan;
- candidate rules;
- cost assumptions.

### Разделение validation

Если validation используется одновременно для model selection, подбора торгового правила и финальной оценки PF, эти роли должны быть разведены:

- **val-stop**: для действий, влияющих на модель — early stopping, выбор числа деревьев/эпох, ablation winner.
- **val-select**: для grid search торговых параметров, threshold/top-k и выбора rule-family.
- **val-eval**: для финальной оценки уже выбранного правила перед `locked_test`.

Для SoSimple роли могут жить внутри одного крупного `validation`, если данных мало. Тогда результат не выше `RESEARCH_ONLY`. Такой этап может создать только `frozen_rule_for_locked_test`, не verdict `candidate`. Verdict `candidate` возможен только после PASS на `locked_test` и раскрытия полного `cumulative_search_budget`.

### Пошаговые действия

1. Провести grid/sweep только на `val-select`. `val-stop` не участвует в торговой оптимизации.
2. Считать не только PF, но и:
   - trades count;
   - trades per year;
   - win/loss;
   - yearly/monthly slices;
   - BUY/SELL slices;
   - drawdown;
   - profit concentration diagnostics: `effective_profit_years`,
     best-year share, PF without best year.
3. Применить production gates до выбора winner.
4. Зафиксировать один winner и оценить его на `val-eval` без изменения правила.
5. Сохранить rule JSON, threshold, checkpoint path, feature contract, export command.
6. Сохранить execution contract: `entry_price`, first executable price, latency proof, spread, fill policy, PnL convention, no-fill handling.
7. Запретить изменение rule после просмотра `locked_test`.
8. При grid search из N конфигураций зафиксировать N и применить коррекцию на множественное тестирование: отдельный `val-eval`, Bonferroni/FDR/Holm или permutation test с повторением того же процесса выбора на каждой перестановке.
9. Если используется permutation test после grid search: на каждой перестановке нужно повторять тот же search/selection protocol, что и на реальных предсказаниях. Permutation test только на уже выбранном grid — диагностический, а не полная коррекция множественного перебора.
10. Если гипотеза порождена наблюдением результатов предыдущего этапа (например, «профиль X был близок к лидеру»), следующий проверочный прогон — это **повторная проверка гипотезы**, а не независимое открытие. Это нужно явно отметить в плане и отчёте. Иначе возникает иллюзия заранее сделанного выбора (ошибка отбора по уже увиденному результату).

### Обязательные проверки

- Winner selection уважает minimum trades и другие gates.
- Для каждой validation-роли пройден `sample_size_gate` из [06-temporal-split.md](06-temporal-split.md); если роли объединены, это явно понижает статус до `RESEARCH_ONLY`.
- Для winner рассчитан PF uncertainty: block bootstrap, stationary bootstrap или другой метод, учитывающий временную корреляцию сделок. Winner не выбирается только по точечному PF: сначала обязательные gates, затем заранее заданный risk-adjusted tie-breaker (`BS_p05`, EV/trade lower bound, drawdown limit и т.п.). При малом N оценён overfit risk.
- Нельзя выбирать максимальный PF среди кандидатов, которые не проходят gate.
- `locked_test` не участвует в выборе threshold/top-k/exit/filter.
- SeqPF не используется как gate-критерий выбора winner (допустим только diagnostic-only).
- Если используется ensemble/stacking, нужен out-of-fold protocol или отдельный holdout.
- Frozen rule невалиден после изменения `entry_price`, canonical spread, fill policy или PnL convention.
- Frozen rule невалиден после изменения `execution_ohlc_path`, lower-timeframe
  ordering policy или same-bar TP/SL fallback, если эти параметры влияют на
  PnL/gates/winner selection. Такое изменение требует нового validation rerun
  или явно помечается как post-review diagnostic.
- Frozen rule невалиден без first executable price и доказательства, что признаки, inference и order-send доступны до входа.
- Validation PF для execution-aware кандидата считается по PnL, а не по счёту TP/SL.
- Zero-spread validation sweep не может выбрать frozen winner для production, если canonical spread не равен нулю.
- Profit concentration не должен быть единственным жёстким gate на коротком validation. Вместо правила вида `best_year_share <= X` использовать пакет проверок:
  `effective_profit_years`, число прибыльных лет, минимальный годовой PF, PF без лучшего года, `BS_p05` и stress по spread/costs.

### Profit concentration diagnostics

Для проверки, не держится ли PF на одном удачном году, считать долю валовой прибыли каждого года:

```text
share_y = gross_profit_y / sum(gross_profit_all_years)
```

Затем считать эффективное число прибыльных лет:

```text
effective_profit_years = 1 / sum(share_y^2)
```

Интерпретация:

- если вся прибыль пришла из одного года: `effective_profit_years = 1.0`;
- если прибыль распределена как `75/25` на двух годах: примерно `1.6`;
- если прибыль равномерно распределена по двум годам: `2.0`;
- если прибыль равномерно распределена по четырём годам: `4.0`.

Базовый gate для validation-кандидата:

```text
effective_profit_years >= max(1.5, 0.6 * n_years)
```

Этот gate не требует равномерной прибыли по годам, но отсекает случаи, где почти весь результат сделал один рыночный режим. Для короткого окна `n_years <= 3` провал только этой проверки понижает статус до `research_only` или `warning`, но не обязан автоматически отклонять кандидата, если остальные проверки сильные. Автоматический reject обоснован, когда вместе с концентрацией есть дополнительные проблемы: `BS_p05 < 1.0`, PF без лучшего года < 1.0, большинство лет убыточны или spread/cost stress ломает PF.

### Критерии успешного завершения

- Есть ровно один `frozen_rule_for_locked_test`.
- Есть frozen artifacts.
- Есть validation report с rejected alternatives.
- Если winner держится на малом числе сделок, статус не выше research_only.
- Известно, какой baseline кандидат должен побить на `locked_test`.

### Типовые ошибки

- `pick_winner` выбирает высокий PF на малом N без оценки статистической неопределённости.
- Менять threshold после `locked_test`.
- Выбирать rule-family по `locked_test`, а параметры по validation.
- Считать структурную стабильность между seeds доказанной без формального tolerance.
- Подменять frozen execution convention после validation и считать это тем же кандидатом.
- Добавлять M1/M5 ordering после выбора winner и повышать verdict без rerun
  того же selection protocol.
- Сравнивать canonical-spread winner с zero-spread candidate как с равноправными торговыми вариантами.
- Считать рост PF доказательством улучшения модели без проверки, что изменился рейтинг сделок, а не цена входа: если PF вырос после смены entry_price/spread/fill, а рейтинг сделок не изменился — это entry-price effect, не signal improvement.
- Использовать validation для early stopping, grid search И финальной оценки одновременно (тройная утечка). Каждый уровень оптимизации на одном наборе завышает итоговую оценку.
- Не корректировать множественное тестирование при переборе >10 конфигураций на одном validation. Чем больше search budget, тем выше риск ложного winner; результат без коррекции не должен становиться `frozen_rule_for_locked_test`.

### Ветвления

- Если нет validation candidate, проходящего gates: reject или изменить гипотезу.
- Если несколько кандидатов близки: выбрать заранее заданным tie-breaker, а не по `locked_test`.
- Если winner нестабилен между seeds: понизить статус или использовать более простое frozen rule.

---
