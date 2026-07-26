# Fractal0 Fixed-11 Candidate Audit

> **Дата**: 2026-07-25
> **Статус**: Completed
> **Вердикт**: FAIL
> **Цель**: независимо проверить `fractal0_fixed11_rich_entry_locked_test*` артефакты перед любым повышением статуса выше `candidate_check_required`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`

## Context

На предыдущем этапе `locked_test` уже был открыт ровно один раз для 11 frozen rules и дал вердикт `candidate_check_required`. Текущий этап не переоткрывает `locked_test`, не выбирает нового winner и не меняет frozen rules. Его задача - только независимый read-only аудит JSON/CSV bundle, freeze/disclosure и split/gate contract.

Уровень этапа: проверочный audit готовых locked-test артефактов.

## What Was Done

- Добавлен read-only модуль `ML/baseline/audit_fractal0_fixed11_candidate.py`.
- Добавлены тесты `tests/test_fractal0_fixed11_candidate_audit.py` на:
  - contract-loading bundle;
  - отсутствие pre-open freeze/policy;
  - hash mismatch и missing hash;
  - split-role / split-boundary disclosure;
  - candidate gates по `PF`, `BS_p05`, `n_trades`, BUY/SELL, yearly и `movement_score`.
- Добавлен CLI, который пишет:
  - `ML/reports/fractal0_fixed11_candidate_audit.json`
  - `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`
- Запущен фактический audit на `ML/reports/fractal0_fixed11_rich_entry_locked_test`.

## Multiple Testing Context

Этот этап не расширяет search budget и не запускает новый подбор. Он проверяет уже открытый one-shot `locked_test` для 11 frozen rules.

```text
lifecycle_status: candidate_check_required_audit
origin_bias: inherited_from_fixed11_locked_test
current_search_budget: 0 new configurations
cumulative_search_budget: inherited from frozen fixed11 selection pipeline; audit does not add new models/profiles/targets/filters/cutoffs
allowed_max_verdict: candidate_audit_passed
forbidden_interpretations:
  - "новый winner выбран по locked_test"
  - "можно переходить к MT4/tester parity без устранения блокеров"
  - "movement_plus_time disclosure можно восстановить по памяти без frozen artifact"
```

## Changed Files

- `ML/baseline/audit_fractal0_fixed11_candidate.py`
- `tests/test_fractal0_fixed11_candidate_audit.py`
- `docs/ML/audit_fractal0_fixed11_candidate.py.md`
- `ML/reports/fractal0_fixed11_candidate_audit.json`
- `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`

## Verification

Команды:

```bash
./.venv/bin/python ML/baseline/audit_fractal0_fixed11_candidate.py \
  --input-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test \
  --output-prefix ML/reports/fractal0_fixed11_candidate_audit

./.venv/bin/python -m pytest tests/test_fractal0_fixed11_candidate_audit.py -q
./.venv/bin/python -m pytest tests/ -q
```

Результат:

- audit CLI завершился с кодом `2` и записал JSON/CSV audit artifacts;
- `tests/test_fractal0_fixed11_candidate_audit.py`: `11 passed`;
- полный `tests/`: `1456 passed`, `52 warnings`.

## Results

Итоговый audit verdict:

```text
overall_decision = candidate_audit_blocked
finding_counts = {ERROR: 15, WARNING: 2}
source_runner_declared_path = ML/baseline/benchmark_fractal0_entry_quality_filter.py
source_runner_sha256 = 793f18b49e06f815f8144ac6ec1fb9eff1acb67d264a002874b00039e2f0911f
rule_count = 11
evaluated_rule_count = 11
gate_pass_count = 11
kept_candidates = 11
correlation_pruning_status = MISSING
bs_p05_method = current_iid_trade_bootstrap_despite_block_bootstrap_pf_name
```

Ключевые source hashes, подтверждённые audit CLI:

- `source_rules_csv_sha256 = d98c1194d954e20aaa7d7a132547a9ac52caf1c7073f5ce98997cda1ee3b808c`
- `source_artifact_sha256 = 20e6931a1b47d7d2fe3c5455e698d8bb3160bd570a418a35a0a0ea083358e0b6`
- `locked_test_sha256 = 5beb70f29ee27caa2b20a8cd80376879b64179d4ef0e5197a29357b58483f535`
- `h1_ohlc_sha256 = 4bf7a23ab79f41824713fa881078d06fb84fd7c484b2840c3cdec0bfdfda5aff`
- `execution_ohlc_sha256 = 504666ce286b27f3ae61679d5e722a629a0d8662d93a428c4f8dd5e6b2ce4f60`

Основные блокеры:

| severity | check_id | count | Смысл |
|---|---:|---:|---|
| ERROR | `pre_open_freeze_artifact_missing` | 1 | Нет machine-readable pre-open freeze/policy artifacts, которые доказали бы freeze до открытия `locked_test` |
| ERROR | `split_role_missing` | 2 | В source JSON не раскрыты `val_select` и `val_eval` |
| ERROR | `split_boundaries_missing` | 1 | В source JSON нет structured split boundaries |
| ERROR | `correlation_pruning_status_missing` | 1 | Нет явного handoff, что correlation pruning ещё не выполнен |
| ERROR | `yearly_low_n_not_diagnostic` | 6 | Для 6 rule-year строк (`2022`) `n_trades < 30`, но они не размечены как `DIAGNOSTIC_ONLY` |
| ERROR | `movement_score_restoration_missing` | 4 | Для всех `movement_plus_time` rules нет structured disclosure восстановления `movement_score` |
| WARNING | `source_runner_hash_missing_from_locked_test_json` | 1 | Runner hash отсутствует в исходном locked-test JSON, но теперь записан audit artifact |
| WARNING | `bs_p05_iid_bootstrap_limitation` | 1 | Текущий `BS_p05` остаётся diagnostic-only, потому что заявленный block bootstrap фактически iid-like |

## Validation Split Disclosure

Audit сам вычислил фактические границы split-ов из локальных CSV:

| role | row_count | min_time | max_time | source |
|---|---:|---|---|---|
| `train_core` | 44159 | `2004-07-06 20:00:00` | `2019-06-20 14:00:00` | `computed_from_local_csv` |
| `val_select` | 4731 | `2019-06-20 16:00:00` | `2021-03-08 03:00:00` | `computed_from_local_csv` |
| `val_eval` | 4732 | `2021-03-08 05:00:00` | `2022-12-02 07:00:00` | `computed_from_local_csv` |
| `locked_test` | 9463 | `2022-12-02 11:00:00` | `2026-06-04 12:00:00` | `computed_from_local_csv` |

Вывод: временного overlap audit не обнаружил, но structured disclosure в исходном locked-test JSON неполный, поэтому split-contract считается не закрытым.

## Conclusions

- Сам `locked_test` bundle не развалился: 11 rules, source hashes и базовые aggregate/side PF остаются согласованными.
- Но audit не может подтвердить `candidate_audit_passed`, потому что отсутствуют обязательные доказательства freeze/disclosure.
- Блокировка не разрешает:
  - переход к correlation pruning как к следующему рабочему этапу;
  - MT4/tester parity;
  - model card;
  - любые trading-status выводы.

## Limitations / Open Questions

- Pre-open freeze/policy artifacts отсутствуют в дереве проекта; retroactive reconstruction допустима только как disclosure, не как доказательство.
- `movement_plus_time` branch нельзя честно поднимать выше research-only без structured movement restoration contract.
- Edge-year `2022` для 6 rules имеет `n_trades < 30`; без явной diagnostic classification эти yearly slices нельзя использовать как stability evidence.
- `BS_p05` пока не является полноценным uncertainty gate из-за текущей iid-like реализации.

## Next Step

Разрешён только узкий follow-up без нового выбора по `locked_test`:

1. восстановить или явно зафиксировать отсутствие pre-open freeze/policy artifacts;
2. добавить structured split disclosure (`val_select`, `val_eval`, boundaries);
3. оформить structured `movement_score_restoration` contract для 4 `movement_plus_time` rules;
4. классифицировать low-N yearly edge slices как `DIAGNOSTIC_ONLY` в audit/reporting слое;
5. только после снятия этих блокеров заново запускать candidate audit.

Mutual-correlation pruning, MT4/tester parity и model card остаются запрещёнными до повторного audit pass.

## Related Materials

- `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`
- `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`
- `docs/superpowers/plans/2026-07-23-fractal0-fixed11-locked-test-protocol.md`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- `ML/reports/fractal0_fixed11_candidate_audit.json`
- `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`
