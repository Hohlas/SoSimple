# Label Convention Audit — Triple Barrier float labels

> **Date**: 2026-04-13 18:40
> **Status**: Completed
> **Goal**: Проверить все TB-консьюмеры на смешение float-лейблов `{1.0, 0.0, 0.5}` и закрыть подтверждённые баги без изменения source-of-truth
> **Related plan/spec**: `docs/superpowers/plans/2026-04-13-label-convention-audit.md`
> **Related commit**: pending

## Context

После stage `2026-04-12-tb-verdict` было известно, что один critical bug уже жил в `ML/triple_barrier_mt4_execution.py`: `int(outcome)` сливал `SL` и `Timeout`. Этот этап проверял, что аналогичный паттерн не остался в других TB-консьюмерах.

## What Was Done

- Поднят isolated worktree `label-convention-audit`
- Восстановлен pre-existing baseline blocker: добавлен отсутствующий `ML/benchmark_triple_barrier_mt4_execution.py`, которого ждал `tests/test_triple_barrier_mt4_execution.py`
- Собран inventory TB-консьюмеров в `ML/reports/label_convention_audit_inventory.csv`
- Выполнен статический аудит по rubric `R1..R8`
- Для всех non-`R8` findings созданы numerical reproducer-тесты
- Подтверждены и минимально исправлены 2 бага класса `R2 not_win_is_loss`
- Временный audit harness переведён в permanent guard `tests/test_tb_label_invariants.py`
- Выполнен frozen rerun `tb_selected_rule.json` на canonical `ml_signals_tb.csv` + `Nero_validation_labeled.csv` + `Nero_test_labeled.csv`

## Changed Files

- `ML/benchmark_triple_barrier_mt4_execution.py` — восстановлен missing benchmark module для baseline suite
- `ML/tb_signal_logic.py` — timeout исключён из losses, добавлен partition assert
- `ML/threshold_analysis.py` — losses считаются только по `0.0`
- `tests/test_tb_label_invariants.py` — постоянные invariant tests
- `ML/reports/label_convention_audit_inventory.csv` — inventory findings
- `ML/reports/label_convention_audit.md` — детальный audit report

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_triple_barrier_mt4_execution.py tests/test_triple_barrier_first_touch.py tests/test_triple_barrier_calibration.py tests/test_triple_barrier_training.py tests/test_signal_tracer_tb.py tests/test_generate_signals_research.py -q
# 16 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_tb_label_invariants.py -q
# 2 passed

/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_triple_barrier_mt4_execution.py tests/test_triple_barrier_first_touch.py tests/test_triple_barrier_calibration.py tests/test_triple_barrier_training.py tests/test_signal_tracer_tb.py tests/test_generate_signals_research.py tests/test_tb_label_invariants.py -q
# 18 passed

/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_triple_barrier_mt4_execution \
  --signals-path /home/hohla/git/SoSimple/MT/MQL4/Files/ml_signals_tb.csv \
  --labeled-path /home/hohla/git/SoSimple/DATA/Nero_validation_labeled.csv \
  --rule /home/hohla/git/SoSimple/ML/reports/tb_selected_rule.json \
  --output-trades /tmp/tb_validation_trades_rerun.csv \
  --output-summary /tmp/tb_validation_summary_rerun.json \
  --output-yearly /tmp/tb_validation_yearly_rerun.csv

/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_triple_barrier_mt4_execution \
  --signals-path /home/hohla/git/SoSimple/MT/MQL4/Files/ml_signals_tb.csv \
  --labeled-path /home/hohla/git/SoSimple/DATA/Nero_test_labeled.csv \
  --rule /home/hohla/git/SoSimple/ML/reports/tb_selected_rule.json \
  --output-trades /tmp/tb_test_trades_rerun.csv \
  --output-summary /tmp/tb_test_summary_rerun.json \
  --output-yearly /tmp/tb_test_yearly_rerun.csv
# validation/test summaries match 2026-04-12 exactly
```

## Results

- Confirmed bugs:
  - `ML/tb_signal_logic.py`: `loss_mask = ~win_mask` wrongly counted timeout rows as losses
  - `ML/threshold_analysis.py`: `losses = n_trades - wins` wrongly counted timeout rows as losses
- Frozen rerun on canonical artifacts:
  - validation: `28 trades`, `16 wins`, `4 losses`, `2 timeouts`, `PF=4.333333333333333`
  - test: `69 trades`, `29 wins`, `23 losses`, `5 timeouts`, `PF=1.2777777777777777`
  - both summaries exactly match `ML/reports/tb_mt4_verdict/{validation,test}_summary.json`
- Safe patterns documented as `R8 ok`:
  - `ML/data_loader.py`
  - `ML/evaluate_test.py`
  - `ML/tb_probability_calibration.py`
  - `statistics/signal_tracer.py`
  - `ML/triple_barrier_mt4_execution.py`
  - internal pre-canonical helper in `processing/label_signals.py`

## Conclusions

- Label convention drift после фикса симулятора действительно оставался ещё в двух аналитических TB-консьюмерах.
- Оба места искажали `losses`, `loss` и `PF` в сторону штрафования timeout как full SL.
- Канон в `processing/label_signals.py` не менялся.
- TB rule и frozen verdict не ретюнились.
- Frozen rerun подтверждает, что найденные баги не меняют historical TB verdict от `2026-04-12`.

## Limitations / Open Questions

- Rerun был выполнен не на локально сгенерированных артефактах worktree, а на canonical файлах из основного дерева репозитория.
- Это достаточно для проверки material impact verdict, но не является заново пересобранным TB pipeline end-to-end.

## Next Step

- Специального TB follow-up из этого аудита больше не требуется: material impact на frozen verdict не найден.

## Related Materials

- `docs/reports/2026-04-12-tb-verdict.md`
- `ML/reports/label_convention_audit.md`
- `ML/reports/label_convention_audit_inventory.csv`
- `tests/test_tb_label_invariants.py`
