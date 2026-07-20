## 16. Отчётность и аудит ошибок

### Цель

Сделать результаты воспроизводимыми и пригодными для следующей итерации.

### Входы

- команды запуска;
- artifacts;
- metrics;
- modified files;
- reports;
- known limitations.

### Пошаговые действия

1. Написать отчёт с секциями:
    - Context;
    - Уровень этапа: поисковый / проверочный (см. [00-research-management.md](00-research-management.md));
    - What Was Done;
    - Multiple Testing Context: current и cumulative search budget (модели × профили × таргеты × стороны × горизонты × seed × инструменты × entry/exit policy × spread/fill convention × transforms/scalers × filters × параметры), применённая коррекция или статус `DIAGNOSTIC_ONLY`/`RESEARCH_ONLY`;
    - Changed Files;
    - Verification;
    - Results;
    - Conclusions;
    - Limitations / Open Questions;
    - Split Disclosure: границы `train`/`validation`/`locked_test`, роли `val-stop`/`val-select`/`val-eval`, `sample_size_gate`;
    - Next Step;
    - Related Materials.
2. Указать команды, версии, paths, hashes, rules, checkpoints.
3. Явно перечислить invalidated assumptions.
4. Если модель использует normalization/scaler, отчёт и structured artifact должны содержать:
   - `normalization_config`;
   - где fit-ился scaler и какие данные не участвовали в fit;
   - какие признаки, padding и mask исключены из fit;
   - `normalized_feature_distribution_audit` для train/validation/locked_test или disclosure holdout;
   - список флагов аудита распределений и решение по каждому флагу: block, fix, rerun или accept-as-warning;
   - какие дополнительные преобразования применены (`RobustScaler`, clipping, `log1p`, signed-log), почему они выбраны и на каком split принято решение;
   - подтверждение, что locked_test/disclosure holdout не использовался для выбора normalization/scaler/clipping/log-преобразований;
   - ссылку на artifact [A7 Feature Distribution Audit](A7-feature-distribution-audit.md), если создавался новый feature profile или sequence-вход;
   - итоговый вывод `scale_contract`: `PASS`/`FAIL`/`DIAGNOSTIC_ONLY`.
5. Для принятого кандидата создать model card:
   - назначение модели;
   - instrument/timeframe;
   - `decision_time`;
   - feature contract version;
   - target/label contract;
   - train/validation/locked_test/forward windows;
   - checkpoint/rule/export paths;
   - `cumulative_search_budget_id`;
   - cost assumptions;
   - validation/locked_test/forward verdict;
   - known risks;
   - monitoring/retraining policy;
   - stop conditions.
6. Если найден баг прошлого вывода:
   - доказать минимальным reproducer;
   - оценить material impact;
   - пометить старые выводы как invalid, superseded или unchanged.
7. Обновить changelog/handoff/wiki только если этап действительно закрыт или выводы изменили проектное знание.
8. Для `FAIL`/`reject` результата указать, выполнен ли [A5-post-mortem-diagnostics.md](A5-post-mortem-diagnostics.md). Если нет — зафиксировать причину: нет oracle-потолка, провал уже объяснён методической ошибкой, мало данных или ветка закрыта без дальнейшего исследования.

### Research-first disclosure

Для исследовательских отчётов добавить компактный блок:

```text
lifecycle_status:
origin_bias:
research_priority:
current_search_budget:
cumulative_search_budget:
next_probe_freeze:
allowed_max_verdict:
forbidden_interpretations:
```

Если исследовательский отчёт показывает PnL/PF, рядом с таблицей PnL/PF
обязательно указать:

- `allowed_max_verdict`;
- почему это не торговый вывод;
- какие проверки ещё не пройдены;
- запрещённые слова вывода: "прибыльно", "готово", "можно запускать",
  "live-ready", "tradable".

### Обязательные проверки

- Отчёт отделяет факты от гипотез.
- В отчёте явно указан уровень этапа: поисковый или проверочный. Для поискового — раскрыты current/cumulative search budget и явно отмечено, что результат не может быть кандидатом без нового проверочного цикла. Для проверочного — указано, какие правила, split и инструменты были заморожены до запуска.
- Исследовательский отчёт с PnL/PF содержит `allowed_max_verdict`, причину "не торговый вывод", список непройденных проверок и `forbidden_interpretations`.
- Выбор по holdout запрещён; отчёт содержит явное подтверждение, что holdout не использовался для выбора.
- Отчёт содержит количество raw rows, событий, сигналов и сделок после фильтров по каждому split; малый N понижает статус.
- Есть список limitations.
- Все источники результата доступны.
- Ключевые числа в отчёте (AUC, PF, trades count, yearly PF) сверены со structured artifact (JSON/CSV/parquet). Если structured artifact отсутствует, отчёт обязан содержать команду воспроизведения и hash входов. Расхождение отчёт↔artifact — блокирующая ошибка.
- Для моделей со scaler/normalization отчёт содержит `normalization_config`, `normalized_feature_distribution_audit` и явный `scale_contract` verdict.
- Если `normalized_feature_distribution_audit` содержит `ERROR`/`WARNING`, отчёт содержит реакцию на каждый флаг и не выдаёт неразрешённый preprocessing-риск за слабость модели.
- Для новых feature profiles отчёт содержит A7 artifact или явно объясняет, почему A7 не применялся.
- Для принятого кандидата есть model card.
- Старые противоречащие выводы помечены.
- Документировано, что запрещено делать дальше.
- Для проваленного кандидата с потенциально полезной механикой есть post-mortem выводы или явный отказ от post-mortem.

### Критерии успешного завершения

- Следующий агент может воспроизвести результат по отчёту.
- Ясно, что делать дальше.
- Ясно, какой статус получил кандидат.

### Типовые ошибки

- Писать только итоговый PF без команд.
- Повышать статус кандидата без model card.
- Не фиксировать, почему candidate rejected.
- Писать reject без объяснения, какая следующая гипотеза разрешена, а какая запрещена.
- Удалять неудачные эксперименты из истории.
- Не обновлять вывод после найденной ошибки симулятора.
- Копировать числа в отчёт вручную без сверки со structured artifact — источник расхождений отчёт↔результат.
- Не раскрывать параметры normalization/scaler в отчёте и JSON: следующий агент не сможет отличить ошибку preprocessing от слабости модели.

### Ветвления

- Если result strong, но contract failed: verdict `diagnostic_only`.
- Если bug не меняет verdict: зафиксировать unchanged impact.
- Если bug меняет verdict: закрыть старый candidate и запустить новый cycle.

---
