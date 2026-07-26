# Fractal0 Fixed-11 Candidate Audit

> **Дата**: 2026-07-25
> **Статус**: Completed
> **Вердикт**: FAIL
> **Цель**: независимо проверить `fractal0_fixed11_rich_entry_locked_test` перед любым повышением статуса выше `candidate_check_required`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`

## Context

Этап относится к проверочному контуру. `locked_test` уже был открыт 2026-07-24 для 11 frozen normalized rich-entry правил, поэтому этот аудит не имел права выбирать нового winner, менять правила, менять cutoff или запускать новый поиск.

Проверяемые входы:

- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_summary.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_selection.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_yearly.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_side.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`

## What Was Done

Добавлен read-only аудит `ML/baseline/audit_fractal0_fixed11_candidate.py`.

Проверки:

- наличие JSON и всех CSV;
- 11 уникальных `rule_id`;
- pre-open freeze/policy artifacts;
- SHA256 исходников и входных файлов;
- split-роли и locked-test границы;
- запрет выбора по `locked_test`;
- PF, `BS_p05`, число сделок, стороны BUY/SELL и годовые срезы;
- раскрытие ограничения iid bootstrap;
- раскрытие восстановления movement-score;
- handoff статусов: stress-spread, MT4/tester parity и correlation pruning остаются follow-up.

## Changed Files

- `ML/baseline/audit_fractal0_fixed11_candidate.py`
- `tests/test_fractal0_fixed11_candidate_audit.py`
- `docs/ML/audit_fractal0_fixed11_candidate.py.md`
- `ML/reports/fractal0_fixed11_candidate_audit.json`
- `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`

## Verification

Команды:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_candidate_audit.py -q
./.venv/bin/python ML/baseline/audit_fractal0_fixed11_candidate.py \
  --input-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test \
  --output-prefix ML/reports/fractal0_fixed11_candidate_audit
./.venv/bin/python -m pytest tests/ -q
```

Целевые тесты: `17 passed`.

Аудит завершился кодом `2`, что соответствует блокирующему решению.

## Results

Structured artifact:

- `overall_decision`: `candidate_audit_blocked`
- `finding_count`: `20`
- `error_count`: `18`
- `warning_count`: `2`
- `source_runner_declared_path`: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- `source_runner_sha256`: `793f18b49e06f815f8144ac6ec1fb9eff1acb67d264a002874b00039e2f0911f`
- `bs_p05_method`: `current_iid_trade_bootstrap_despite_block_bootstrap_pf_name`
- `rule_count`: `11`
- `evaluated_rule_count`: `11`
- `gate_pass_count`: `11`
- `kept_candidates`: `11`
- `correlation_pruning_status`: `MISSING`

Source hashes recorded by audit:

- `source_rules_csv_sha256`: `d98c1194d954e20aaa7d7a132547a9ac52caf1c7073f5ce98997cda1ee3b808c`
- `source_artifact_sha256`: `20e6931a1b47d7d2fe3c5455e698d8bb3160bd570a418a35a0a0ea083358e0b6`
- `locked_test_sha256`: `5beb70f29ee27caa2b20a8cd80376879b64179d4ef0e5197a29357b58483f535`
- `execution_ohlc_sha256`: `504666ce286b27f3ae61679d5e722a629a0d8662d93a428c4f8dd5e6b2ce4f60`
- `h1_ohlc_sha256`: `4bf7a23ab79f41824713fa881078d06fb84fd7c484b2840c3cdec0bfdfda5aff`

Ключевые блокеры:

| severity | check_id | rule_id |
|---|---|---|
| ERROR | `pre_open_freeze_artifact_missing` | - |
| ERROR | `split_role_missing` | - |
| ERROR | `split_role_detail_missing` | - |
| ERROR | `locked_test_row_count_mismatch` | - |
| ERROR | `locked_test_period_mismatch` | - |
| ERROR | `locked_test_selection_disclosure_missing` | - |
| ERROR | `correlation_pruning_status_invalid` | - |
| ERROR | `yearly_low_n_unclassified` | 6 affected rules |
| ERROR | `movement_score_restoration_disclosure_missing` | - |
| WARNING | `source_runner_hash_missing_from_locked_test_json` | - |
| WARNING | `bs_p05_iid_bootstrap_limitation` | - |

## Conclusions

`candidate_audit_passed` не достигнут. Правильный итог этапа — `candidate_audit_blocked`.

Это не доказывает, что PF/BS locked-test результата неверны. Это означает, что текущий пакет артефактов недостаточен для перехода к mutual-correlation pruning, MT4/tester parity или обсуждению trading-статуса.

## Multiple Testing Context

Новый поиск не выполнялся. Этот этап только проверил уже созданные locked-test артефакты.

- current search budget: `0`;
- новые модели: `0`;
- новые профили: `0`;
- новые target: `0`;
- новые thresholds/cutoffs: `0`;
- locked-test selection: запрещён и не выполнялся.

## Validation Split Disclosure

В audited JSON есть только:

```json
{
  "train_core": "model_training_only",
  "locked_test": "one_shot_evaluation_only"
}
```

Этого недостаточно. Нет обязательных границ, row count, `val_select`, `val_eval` и явного подтверждения, что `locked_test` не использовался для выбора winner, thresholds, features, models или filters.

Audit дополнительно вычислил фактические границы из локальных CSV:

| role | row_count | min_time | max_time | source |
|---|---:|---|---|---|
| `train_core` | 44159 | `2004-07-06 20:00:00` | `2019-06-20 14:00:00` | `computed_from_local_csv` |
| `val_select` | 4731 | `2019-06-20 16:00:00` | `2021-03-08 03:00:00` | `computed_from_local_csv` |
| `val_eval` | 4732 | `2021-03-08 05:00:00` | `2022-12-02 07:00:00` | `computed_from_local_csv` |
| `locked_test` | 9463 | `2022-12-02 11:00:00` | `2026-06-04 12:00:00` | `computed_from_local_csv` |

Эти computed boundaries помогают handoff и проверке пересечений, но не заменяют structured disclosure в исходном locked-test JSON. Поэтому split-contract остаётся блокером.

## Limitations / Open Questions

- Pre-open freeze/policy artifacts отсутствуют локально. Ретроактивный файл может быть только disclosure, не доказательством pre-open freeze.
- `BS_p05` остаётся диагностическим, потому что используется iid bootstrap, а не block/stationary/timestamp-cluster bootstrap.
- Movement-score restoration раскрыт неполно для движения `movement_plus_time`.
- Low-N edge-year slices не классифицированы как `DIAGNOSTIC_ONLY`.
- Stress-spread и MT4/tester parity не выполнены и не засчитываются этим этапом.

## Next Step

Не переходить к pruning/parity.

Разрешённая следующая работа: исправить воспроизводимость и disclosure audit-producing artifacts без изменения frozen candidate rules и без нового выбора по `locked_test`. Если pre-open freeze/policy доказать невозможно, статус должен оставаться заблокированным или быть понижен до research-only.

## Related Materials

- `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`
- `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`
- `ML/reports/fractal0_fixed11_candidate_audit.json`
- `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`
- `docs/methodology/06-temporal-split.md`
- `docs/methodology/09-validation-freeze.md`
- `docs/methodology/10-frozen-test-oos.md`
- `docs/methodology/11-robustness.md`
- `docs/methodology/16-reporting-audit.md`
