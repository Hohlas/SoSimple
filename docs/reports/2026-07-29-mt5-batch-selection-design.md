# MT5 Batch Selection Design

> **Дата**: 2026-07-29
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Зафиксировать следующий шаг после single-rule prototype для batch selection из 20-50 кандидатов.
> **Related plan/spec**: `.superpowers/sdd/task-8-brief.md`

## Context

Этот этап не открывает production selection. Он описывает только диагностический контур: сначала должен работать single-rule prototype, затем можно переходить к batch selection для 20-50 кандидатов.

## What Was Done

Зафиксирован контракт `ML/reports/mt5_execution_loop/batch_selection_contract.json`.
Он ограничивает batch selection статусом `PLANNED_AFTER_SINGLE_RULE_PROTOTYPE`, оставляет `DIAGNOSTIC_ONLY` как верхний допустимый вердикт до успешного single-rule run и требует, чтобы `MT5 validation tester metrics` были источником итогового отбора.

## Changed Files

- `ML/reports/mt5_execution_loop/batch_selection_contract.json`
- `docs/reports/2026-07-29-mt5-batch-selection-design.md`

## Verification

Выполнен static check из Task 8:

```bash
rg -n "20-50|MT5 validation tester metrics|locked_test|DIAGNOSTIC_ONLY|single-rule" docs/reports/2026-07-29-mt5-batch-selection-design.md ML/reports/mt5_execution_loop/batch_selection_contract.json
```

Проверка проходит, потому что все искомые строки присутствуют в одном из двух файлов.

## Results

Документирован следующий шаг для перехода от одного диагностического MT5 прогона к batch evaluation 20-50 кандидатов.

## Conclusions

Python proxy metrics остаются допустимыми только для shortlist. Финальный выбор должен опираться на MT5 tester metrics в validation-контуре, а не в opened locked_test.

## Limitations / Open Questions

Batch selection не включается до подтверждения single-rule prototype и до документированного понимания parity для `Nero.csv` producer.

## Next Step

Переходить к реализации batch evaluation только после успешного single-rule run и фиксации MT5 execution parity.

## Related Materials

- `.superpowers/sdd/task-8-brief.md`
- `docs/methodology/09-validation-freeze.md`
- `docs/methodology/10-frozen-test-oos.md`
- `docs/methodology/13-export-mt4-parity.md`
