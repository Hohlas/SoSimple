# `audit_fractal0_fixed11_candidate.py`

## Назначение

Read-only аудит артефактов `fractal0_fixed11_rich_entry_locked_test*` перед любым переходом выше `candidate_check_required`.

Скрипт:

- не запускает новый search;
- не переоткрывает `locked_test` для выбора winner;
- не меняет frozen rules, cutoff, execution contract или spread;
- только читает существующие JSON/CSV и пишет отдельный audit artifact.

## Входы

- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_summary.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_selection.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_yearly.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_side.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`
- `ML/reports/fractal0_fixed11_locked_test_freeze.json`
- `ML/reports/fractal0_fixed11_locked_test_selection_policy.json`

## Проверки

- контракт bundle и ровно 11 правил;
- pre-open freeze / selection policy;
- SHA256 для ключевых source files;
- split roles и split boundaries;
- gates по `PF`, `BS_p05`, `n_trades`, BUY/SELL и yearly;
- disclosure для `movement_score` у `movement_plus_time`;
- handoff, что correlation pruning и MT4/tester parity остаются follow-up этапами.

## Команда

```bash
./.venv/bin/python ML/baseline/audit_fractal0_fixed11_candidate.py \
  --input-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test \
  --output-prefix ML/reports/fractal0_fixed11_candidate_audit
```

## Выходы

- `ML/reports/fractal0_fixed11_candidate_audit.json`
- `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`

`overall_decision`:

- `candidate_audit_passed`
- `candidate_audit_blocked`
- `research_only_downgrade_required`

Код возврата:

- `0` только для `candidate_audit_passed`
- `2` для blocked или downgrade

## Follow-up

- `candidate_audit_passed` не означает финальный portfolio selection;
- следующий этап: mutual-correlation pruning для индивидуально прошедших правил;
- MT4/tester parity и stress-spread disclosure идут только после этого.
