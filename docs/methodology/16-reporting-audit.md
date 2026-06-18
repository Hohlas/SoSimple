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
    - What Was Done;
    - Multiple Testing Context: search budget (модели × профили × таргеты × параметры), применённая коррекция (или пометка `DIAGNOSTIC_ONLY`/`RESEARCH_ONLY`);
    - Changed Files;
    - Verification;
    - Results;
    - Conclusions;
    - Limitations / Open Questions;
    - Validation Split Disclosure: как данные были разделены на `val-stop`, `val-select`, `val-eval` (или почему результат не претендует на frozen-candidate);
    - Next Step;
    - Related Materials.
2. Указать команды, версии, paths, hashes, rules, checkpoints.
3. Явно перечислить invalidated assumptions.
4. Если модель использует normalization/scaler, отчёт и structured artifact должны содержать:
   - `normalization_config`;
   - где fit-ился scaler и какие данные не участвовали в fit;
   - какие признаки, padding и mask исключены из fit;
   - `normalized_feature_distribution_audit` для train/validation/test или holdout;
   - итоговый вывод `scale_contract`: `PASS`/`FAIL`/`DIAGNOSTIC_ONLY`.
5. Для принятого кандидата создать model card:
   - назначение модели;
   - instrument/timeframe;
   - `decision_time`;
   - feature contract version;
   - target/label contract;
   - training/validation/test/forward windows;
   - checkpoint/rule/export paths;
   - cost assumptions;
   - validation/test/forward verdict;
   - known risks;
   - monitoring/retraining policy;
   - stop conditions.
6. Если найден баг прошлого вывода:
   - доказать минимальным reproducer;
   - оценить material impact;
   - пометить старые выводы как invalid, superseded или unchanged.
7. Обновить changelog/handoff/wiki только если этап действительно закрыт или выводы изменили проектное знание.
8. Для `FAIL`/`reject` результата указать, выполнен ли [A5-post-mortem-diagnostics.md](A5-post-mortem-diagnostics.md). Если нет — зафиксировать причину: нет oracle-потолка, провал уже объяснён методической ошибкой, мало данных или ветка закрыта без дальнейшего исследования.

### Обязательные проверки

- Отчёт отделяет факты от гипотез.
- Есть список limitations.
- Все источники результата доступны.
- Ключевые числа в отчёте (AUC, PF, trades count, yearly PF) сверены со structured artifact (JSON/CSV/parquet). Если structured artifact отсутствует, отчёт обязан содержать команду воспроизведения и hash входов. Расхождение отчёт↔artifact — блокирующая ошибка.
- Для моделей со scaler/normalization отчёт содержит `normalization_config`, `normalized_feature_distribution_audit` и явный `scale_contract` verdict.
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
