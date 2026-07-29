# Fixed11 Python H1 Chronology Fix

> **Дата**: 2026-07-29
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: проверить corrected Python execution contract, где M5 уточняет фактическое время fill внутри H1, а выходы обрабатываются только в хронологически допустимом порядке после fill.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md`

## Context

Этот этап закрывает найденную ошибку Python-симулятора fixed11: раньше H1-бар fill считался началом жизни сделки, но фактическое M5-время исполнения лимитки не сохранялось. Из-за этого Python мог закрыть сделку внутри того же H1-бара до того, как лимитка реально могла исполниться.

Исправление не является новым locked-test доказательством. Изменены ML-exit feature contract и execution convention после уже открытого fixed11 locked_test, поэтому `allowed_max_verdict=DIAGNOSTIC_ONLY`.

## Stage Level

Диагностический debug/parity rerun в проверочном контуре. Это не новый
confirmatory locked-test и не candidate evidence. Нового выбора retained rules,
cutoffs, profiles, models, targets, filters, stop policy, entry rule, exit rule
или spread не было.

## Methodology

Применены ограничения:

- `docs/methodology/03-feature-contract-leakage.md`: будущие exit-поля не входят во вход ML-exit; `decision_time` теперь означает фактическое время доступности ML-exit решения, а `decision_bar_time` хранит H1-бар признаков.
- `docs/methodology/12-backtest-costs.md`: M5 используется только для порядка исполнения после H1-сигнала, не как ML-признак.
- `docs/methodology/13-export-mt4-parity.md`: Python M5 ordering не считается MT4 parity.
- `docs/methodology/16-reporting-audit.md`: результат, команды, hashes, limitations и invalidated assumptions зафиксированы.

## What Was Done

ML-exit feature contract changed:

- `bars_since_fill=0` исключён из рабочих ML-exit train/score rows;
- future exit fields остаются только target/diagnostic;
- `ML_CLOSE` execution согласован с `first_exit_execution_time`: решение по закрытому H1-бару исполняется на open следующего H1-бара;
- `M5` не используется как ML input, фильтр сделок или источник нового winner.

Execution chronology changed:

- `build_entry_rows(...)` принимает `execution_ohlc`;
- entry/trade rows сохраняют `fill_execution_time`, `fill_execution_time_source`, `fill_execution_confirmed`;
- same-H1 SL/TP проверяются по M5-барам не раньше фактического fill;
- same-H1 `ML_CLOSE` на H1-баре fill отключён до отдельного post-fill ML decision timestamp.

## What Did Not Change

Не менялись retained rules, cutoffs, profiles, models, targets, filters, stop policy, entry rule, exit rule, spread и MQL4-код.

## Multiple Testing Context

Новый search budget:

- `lifecycle_status=diagnostic_rerun_after_contract_bugfix`;
- `fixed_rules=11` уже зафиксированных rules;
- `new_selection=0`;
- `new_rules/cutoffs/profiles/models/targets/filters/spreads=0`;
- `changed_ml_exit_feature_contract=true`;
- `changed_fill_execution_convention=true`;
- `changed_spread=false`;
- `cumulative_search_budget=inherited_from_fixed11_locked_test_candidate_audit_and_pruning_reports`;
- `allowed_max_verdict=DIAGNOSTIC_ONLY`.

Запрещённые интерпретации: не читать PF/PnL как "прибыльно", "готово", "можно запускать", "live-ready" или "tradable".

## Changed Files

Code/test changes:

- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`
- `tests/test_fractal0_entry_exit_grid.py`

Documentation/context changes:

- `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`
- `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`
- `docs/superpowers/roadmap.md`
- `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`
- `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- `docs/ML/run_fractal0_fixed11_rich_entry_locked_test.py.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `MODULE_INDEX.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Verification

Команды:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_rich_entry_locked_test.py -q
./.venv/bin/python ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv --source-artifact ML/reports/fractal0_stop_grid_m5.json --locked-test-path DATA/Nero_XAUUSD_test_labeled.csv --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv --output-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix --diagnostic-only
```

Полный `./.venv/bin/python -m pytest tests/ -q` не запускался: план этого этапа явно запрещает полный suite и требует только целевые проверки.

## Artifacts

- `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json`, sha256 `1855ea1284501f80ce0561d3672488ffe7c3a02f59f52df78a527b7a293b1e5c`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix_trades.csv`, sha256 `f78537feca961543ac654c58acd8ce03bc7a3d78d6b8b43d2918b8c2c617cb78`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix_summary.csv`, sha256 `b9a00b19c19200b4e939829327c12d43d6cc3dec6e1d064a0b725918d0979b66`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix_selection.csv`, sha256 `1ba8896906196b2978d6526ca699dd42f5b002c9a682640c8544aef798cb11a6`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix_side.csv`, sha256 `cc1aa29ac7bc39bd464b66faa8c0c5e67deab0382a527710fafba5be3e8b9ed0`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix_yearly.csv`, sha256 `893ddc92eaf249082587bee5fcd2b3418890a2c5ef33b9dfcc828cdf2942ca6a`
- `ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json`, sha256 `eaa0b38fb5a3af285094f6c4e538fa1dc376491e14681d7e6b98e8d542153edd`

Старые locked-test/current-history artifacts не перезаписывались.

## Results

Runner до принудительной диагностической маркировки дал `original_runner_verdict=reject`, `best_pf=0.9388800897177361`, `kept_candidates=0`. После маркировки: `verdict=DIAGNOSTIC_ONLY`, `allowed_max_verdict=DIAGNOSTIC_ONLY`.

Сравнение current-history rerun -> H1 chronology fix:

- trades: `13039 -> 14387`;
- PnL R sum: `4065.034595 -> -530.513260`;
- PF range: `2.820656-3.424707 -> 0.819373-0.938880`;
- `hold_bars=0`: `4495 -> 488`;
- same-H1 fill/exit: `4495 -> 72`;
- same-H1 `ML_CLOSE`: `4070 -> 0`;
- fill confirmation: `0 -> 14387`, all new trades have `fill_execution_time_source=m5_touch`;
- ambiguous count: `0 -> 150`;
- close reasons: `ML_CLOSE=7379`, `TIME=4073`, `SL=2913`, `TP=22`.

## Chronology Checks

New contract fields in JSON:

- `ml_exit_feature_contract_status=PASS`;
- `bars_since_fill_0_ml_exit_policy=excluded_until_post_fill_decision_timestamp_exists`;
- `ml_exit_timing_contract=feature_time <= decision_time <= execution_time`;
- `decision_bar_time`: H1 timestamp бара, закрытые OHLC которого дают ML-exit input features;
- `feature_available_time`: первый H1 timestamp, когда эти признаки доступны;
- `decision_time` / `ml_decision_time`: фактический timestamp ML-exit решения, равный `feature_available_time`;
- `first_exit_execution_time`: первый исполнимый H1 timestamp для этого решения;
- `future_exit_fields_role=target_or_diagnostic_only`;
- `close_now_pnl_r_role=target_or_diagnostic_only_backward_compatibility_name`;
- `same_h1_ml_close_policy=disabled_on_fill_h1_until_real_post_fill_ml_decision_timestamp_exists`;
- `fill_m5_double_touch_policy=SL_first_with_ambiguous_true`.

## Normalization / Scale Disclosure

Wrapper заново считает `movement_score` для `locked_test` через прежний frozen
movement protocol:

- `movement_score_model_contract.feature_profile=simple_combined`;
- model: `extra_trees_small`;
- target: `entry_movement_3`;
- `normalization_config.scaler=RobustScaler`;
- scaler fit: только `train_core`;
- transformed splits: `locked_test`;
- `locked_test_used_for_scaler_fit=false`;
- `scale_contract=DIAGNOSTIC_ONLY`;
- `normalized_feature_distribution_audit`: не перезапускался в этом debug
  chronology rerun; для совместимости fixed11 использован inherited frozen
  movement protocol.

## Conclusions

Старый fixed11 positive locked-test вывод больше нельзя считать тем же frozen verification chain: он зависел от несовместимого ML-exit feature contract и от H1-only fill chronology. После исправления edge исчез в диагностическом rerun (`PF max < 1`), поэтому текущий fixed11 retained-subset path должен быть остановлен или переведён в post-mortem до нового MT4 export.

## Post-mortem Status

Post-mortem не выполнялся в этом этапе. Причина: план был ограничен исправлением
хронологии, диагностическим rerun и фиксацией invalidation. Отдельный A5
post-mortem нужен только если fixed11 mechanics продолжаются как инженерная или
исследовательская ветка; до него запрещено начинать новый выбор по старому
locked_test.

## Limitations / Open Questions

- Точный live bid/ask source не доказан.
- Полная эквивалентность M5 tester-history реальному исполнению не доказана.
- Python M5 ordering не заменяет MT4 tester parity.
- Same-H1 ML-close можно возвращать только отдельным планом с настоящим post-fill ML decision timestamp и новым feature-availability доказательством.

## Invalidated Assumptions

- Старые fixed11 locked-test/current-history PF и cutoffs не являются тем же проверочным результатом после изменения execution contract.
- `fill_time == exit_time` на H1 нельзя считать достаточным доказательством корректной хронологии без M5-порядка после fill.
- `bars_since_fill=0` нельзя использовать как рабочее ML-exit решение в текущем H1-only timestamp contract.

## Split Disclosure

Использованы прежние роли split: `train_core` для обучения ML-exit и rich-entry моделей, `val_select` как источник fixed rules/cutoffs из прошлого этапа, `locked_test` как диагностический rerun. Locked-test не использовался для нового выбора winner.

## Next Step

Узкий следующий шаг: не экспортировать новые MT4 fixed11 signals как candidate. Сначала принять решение по ветке:

- если текущий fixed11 path закрывается: написать post-mortem и оставить MT4 parity только как инженерную проверку;
- если продолжать механику: экспортировать corrected fixed11 signals/trades только как diagnostic и выполнить MT4 slot parity с reconciliation по `signal_time + direction`, open/fill/close reasons и missing opens.

## Related Materials

- `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`
- `docs/reports/2026-07-29-fixed11-current-history-rerun.md`
- `ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json`
