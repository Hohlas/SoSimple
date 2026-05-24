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
   - Changed Files;
   - Verification;
   - Results;
   - Conclusions;
   - Limitations / Open Questions;
   - Next Step;
   - Related Materials.
2. Указать команды, версии, paths, hashes, rules, checkpoints.
3. Явно перечислить invalidated assumptions.
4. Для принятого кандидата создать model card:
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
5. Если найден баг прошлого вывода:
   - доказать минимальным reproducer;
   - оценить material impact;
   - пометить старые выводы как invalid, superseded или unchanged.
6. Обновить changelog/handoff/wiki только если этап действительно закрыт или выводы изменили проектное знание.

### Обязательные проверки

- Отчёт отделяет факты от гипотез.
- Есть список limitations.
- Все источники результата доступны.
- Для принятого кандидата есть model card.
- Старые противоречащие выводы помечены.
- Документировано, что запрещено делать дальше.

### Критерии успешного завершения

- Следующий агент может воспроизвести результат по отчёту.
- Ясно, что делать дальше.
- Ясно, какой статус получил кандидат.

### Типовые ошибки

- Писать только итоговый PF без команд.
- Повышать статус кандидата без model card.
- Не фиксировать, почему candidate rejected.
- Удалять неудачные эксперименты из истории.
- Не обновлять вывод после найденной ошибки симулятора.

### Ветвления

- Если result strong, но contract failed: verdict `diagnostic_only`.
- Если bug не меняет verdict: зафиксировать unchanged impact.
- Если bug меняет verdict: закрыть старый candidate и запустить новый cycle.

---

