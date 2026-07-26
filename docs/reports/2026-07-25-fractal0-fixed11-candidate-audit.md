# Fractal0 Fixed-11 Candidate Audit

> **Дата**: 2026-07-25
> **Статус**: Completed
> **Вердикт**: PASS
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

Целевые тесты: `23 passed`.

Аудит завершился кодом `0`, что соответствует `candidate_audit_passed`.

## Results

Structured artifact:

- `overall_decision`: `candidate_audit_passed`
- `finding_count`: `14`
- `error_count`: `0`
- `warning_count`: `13`
- `info_count`: `1`
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

Ключевые предупреждения:

| severity | check_id | rule_id |
|---|---|---|
| WARNING | `pre_open_freeze_machine_artifact_missing` | - |
| WARNING | `source_runner_hash_missing_from_locked_test_json` | - |
| WARNING | `split_disclosure_reconstructed_from_forensic_evidence` | - |
| WARNING | `bs_p05_iid_bootstrap_limitation` | - |
| WARNING | `correlation_pruning_status_reconstructed_from_report` | - |
| WARNING | `yearly_low_n_edge_year_diagnostic` | 6 affected rules |
| WARNING | `movement_score_restoration_reconstructed_from_report` | - |

## Conclusions

`candidate_audit_passed` достигнут для 11 individual fixed rules.

Причина изменения относительно первичного аудита: отчёты `docs/reports`, locked-test plan, CSV artifacts и git history дают проверяемую цепочку доказательств по периоду поиска, периоду подтверждения, закрытой проверке, составу 11 правил и применению сохранённых cutoffs. Поэтому отсутствие отдельных `fractal0_fixed11_locked_test_freeze.json` / `selection_policy.json` остаётся предупреждением о форме, но не блокирует audit pass.

Это не означает trading-ready. Это означает: можно переходить к следующему методическому этапу — mutual-correlation pruning для 11 individual passed rules. MT4/tester parity идёт только после выбора retained subset.

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

Самого этого JSON-фрагмента было бы недостаточно. Но audit дополнительно проверил отчёт и план, где явно указаны `val_select`, отсутствие нового выбора по `locked_test`, применение сохранённых cutoffs и запрет full-grid на `locked_test`.

Audit дополнительно вычислил фактические границы из локальных CSV:

| role | row_count | min_time | max_time | source |
|---|---:|---|---|---|
| `train_core` | 44159 | `2004-07-06 20:00:00` | `2019-06-20 14:00:00` | `computed_from_local_csv` |
| `val_select` | 4731 | `2019-06-20 16:00:00` | `2021-03-08 03:00:00` | `computed_from_local_csv` |
| `val_eval` | 4732 | `2021-03-08 05:00:00` | `2022-12-02 07:00:00` | `computed_from_local_csv` |
| `locked_test` | 9463 | `2022-12-02 11:00:00` | `2026-06-04 12:00:00` | `computed_from_local_csv` |

Эти computed boundaries помогают handoff и проверке пересечений. Так как они согласуются с отчётом 2026-07-24 и locked-test CSV, split-contract принят как forensic-disclosure с предупреждением о том, что исходный JSON был слишком кратким.

## Limitations / Open Questions

- Pre-open freeze/policy artifacts отсутствуют как отдельные machine-readable JSON; доказательство принято по отчётам, плану, CSV и git history.
- `BS_p05` остаётся диагностическим, потому что используется iid bootstrap, а не block/stationary/timestamp-cluster bootstrap.
- Movement-score restoration принят по locked-test execution log, но следующий похожий runner должен писать structured contract в JSON.
- Low-N edge-year slices приняты как incomplete edge-year diagnostic disclosure.
- Stress-spread и MT4/tester parity не выполнены и не засчитываются этим этапом.

## Next Step

Следующий этап: mutual-correlation pruning для 11 individual passed rules.

После pruning MT4/tester parity, stress-spread disclosure и model card выполняются только для retained subset. Запрещено выбирать новый winner, менять cutoffs или менять frozen rules по `locked_test`.

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
