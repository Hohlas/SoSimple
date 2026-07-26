# Changelog SoSimple

> Компактный индекс отчётов, решений и ключевых артефактов завершённых этапов (новые записи в начале).

## Формат записи

```md
## [YYYY-MM-DD] — Краткое описание (VERDICT)
- **report**: `docs/reports/YYYY-MM-DD-topic.md`
- **topics**: `topic_a`, `topic_b`
- **summary**: 1-2 предложения о сути этапа.
- **artifacts**: `path/to/main_artifact`, `path/to/main_entrypoint`
- **decision**: что (не) достигнуто; что принято / запрещено.
- **notes**: только критичные ограничения, если есть.
```
---

## [2026-07-25] — Fixed-11 candidate audit (FAIL)
- **report**: `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`
- **topics**: `fractal0`, `fixed11`, `candidate_audit`, `locked_test`, `reproducibility`
- **summary**: Added read-only audit for `fractal0_fixed11_rich_entry_locked_test*` artifacts. Audit produced `candidate_audit_blocked`: 18 errors and 2 warnings.
- **artifacts**: `ML/reports/fractal0_fixed11_candidate_audit.json`, `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`, `ML/baseline/audit_fractal0_fixed11_candidate.py`
- **decision**: Do not proceed to mutual-correlation pruning, MT4/tester parity or trading-status discussion until blockers are resolved without changing frozen candidate rules.
- **notes**: Main blockers: missing pre-open freeze/policy artifacts, incomplete split disclosure, unclassified low-N yearly slices, incomplete movement-score restoration disclosure.

## [2026-07-24] — Fixed-11 rich-entry locked test (candidate_check_required)
- **report**: `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`
- **topics**: `fractal0`, `fixed11`, `rich_entry_quality`, `locked_test`, `m5_execution_ordering`
- **summary**: One-shot OOS evaluation of 11 frozen normalized rich-entry leaderboard rules on locked_test split using the M5 execution contract. All 11 rules pass PF/BS/sample-size gates; PF range `2.6747-3.3667`.
- **artifacts**: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`, `ML/reports/fractal0_fixed11_rich_entry_locked_test_summary.csv`, `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`
- **decision**: `candidate_check_required`; next required checks are independent audit, MT4/tester parity, stress-spread disclosure and model card.
- **notes**: `kept_candidates=11`; BUY PF range `3.6196-5.1218`; SELL PF range `1.9485-3.0798`; movement_plus_time locked-test scores were restored via the frozen movement protocol because source scores did not include locked_test.

## [2026-07-23] — Fixed-11 internal closure rerun (research_only risk-flagged)
- **report**: `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md`
- **topics**: `fractal0`, `fixed11`, `stress_cost`, `timezone`, `calendar`, `multi_seed`
- **summary**: Producer-level fixed rerun computed stress-cost, frozen timezone/calendar diagnostics and bounded multi-seed for the exact 11 normalized leaderboard rule families with `--threads 24`.
- **artifacts**: `ML/reports/fractal0_fixed11_internal_closure_rerun.json`, `ML/reports/fractal0_fixed11_internal_closure_rerun_classification.csv`, `ML/baseline/fractal0_fixed11_internal_closure_rerun.py`
- **decision**: `FIXED11_INTERNAL_CLOSURE_RISK_FLAGS_RESEARCH_ONLY`; all diagnostics computed, but all 11 rules are risk-flagged by stress/calendar evidence.
- **notes**: `locked_test=not_opened`; `provider_drift_status=NOT_IN_SCOPE`; `transfer_status=NOT_IN_SCOPE`; next step is close rich/fractal entry-quality as time-heavy research-only and write a narrower regime-filter reformulation plan.

## [2026-07-23] — Leaderboard cost/calendar/sequential/multi-seed closure (research_only)
- **report**: `docs/reports/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md`
- **topics**: `fractal0`, `leaderboard`, `costs`, `calendar`, `sequential_positions`, `multi_seed`
- **summary**: Added closure/disclosure audit for the same 11 fixed normalized leaderboard rows. Time-calendar and sequential-position diagnostics are computed; stress-cost, timezone shift, calendar permutation/no-ML baseline and multi-seed are disclosed as not computable from saved artifacts.
- **artifacts**: `ML/reports/leaderboard_closure_audit.json`, `ML/reports/leaderboard_closure_audit_classification.csv`, `ML/baseline/audit_leaderboard_closure.py`
- **decision**: `LEADERBOARD_CLOSURE_INCOMPLETE_RESEARCH_ONLY`; no winner selection and no freeze/locked-test permission.
- **notes**: `locked_test=not_opened`; `provider_drift_status=NOT_IN_SCOPE`; `transfer_status=NOT_IN_SCOPE`; next step is producer-level stress-cost resimulation, frozen timezone rescore, bounded multi-seed rerun for exactly 11 families, or closing rich/fractal entry-quality as time-heavy research-only.

## [2026-07-23] — Leaderboard robustness audit (research_only)
- **report**: `docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md`
- **topics**: `fractal0`, `rich_entry_quality`, `leaderboard`, `robustness`, `validation_slice`
- **summary**: Added validation-slice robustness audit for 11 fixed normalized rich-entry leaderboard input rows without new search and without opening `locked_test`.
- **artifacts**: `ML/reports/leaderboard_robustness_audit.json`, `ML/reports/leaderboard_robustness_audit_classification.csv`, `ML/baseline/audit_leaderboard_robustness.py`
- **decision**: `LEADERBOARD_ROBUSTNESS_INCOMPLETE_NEEDS_COST_TIME_CHECKS`.
- **notes**: `verdict=research_only`; `scale_contract=DIAGNOSTIC_ONLY` because final normalized audit has accepted `WARNING` rows; winner selection was not performed; `locked_test=not_opened`; missing stress/time/sequential/provider/multi-seed checks disclosed.

## [2026-07-23] — Time-only robustness audit (research_only)
- **report**: `docs/reports/2026-07-23-time-only-robustness-audit.md`
- **topics**: `fractal0`, `time_only`, `robustness`, `validation_slice`, `regime_filter`
- **summary**: Добавлен audit fixed normalized `time_only / linear / target_entry_ev_regression / top30` winner по saved validation artifacts без нового поиска и без открытия `locked_test`.
- **artifacts**: `ML/reports/time_only_robustness_audit.json`, `ML/reports/time_only_robustness_audit_yearly.csv`, `ML/reports/time_only_robustness_audit_side.csv`, `ML/baseline/audit_time_only_robustness.py`
- **decision**: `REGIME_REFORMULATION_REQUIRED`; следующий active-трек — regime filter reformulation.
- **notes**: `locked_test=not_opened`; `stricter_cutoff_sample_fragile`; `stress_costs_not_computable`; entry-time calendar slices added; `timezone_shift_status=NOT_RUN`, `calendar_permutation_importance_status=NOT_RUN`, `multi_seed_status=NOT_RUN`, `provider_drift_status=NOT_RUN`, `transfer_status=NOT_RUN`.

## [2026-07-22] — Fractal0 Rich Entry Quality Normalized Rerun (RESEARCH_HINT_RICH_FEATURES)
- **report**: `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- **topics**: `fractal0`, `rich_entry_quality`, `normalized_features`, `feature_contract`, `train_only_scaler`
- **summary**: Rich-entry search rerun выполнен с normalized contract: raw price-like inputs запрещены, price-like признаки переведены в ATR-координаты и затем в `[0,1]` через train-core scaler.
- **artifacts**: `ML/reports/fractal0_rich_entry_quality_normalized.json`, `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`, `ML/reports/fractal0_rich_entry_quality_normalized_protocol_comparison.csv`, `ML/reports/fractal0_rich_entry_quality_normalized_normalization_config.json`
- **decision**: Winner не изменился: `time_only / linear / target_entry_ev_regression / top30`; fixed `val_eval PF=4.0268`, `BS_p05=3.3955`. Normalized contract улучшил protocol comparison для `rich_combined_k40`, `price_action_h1` и `structure_f0_only`, но не доказал превосходство rich/fractal profiles над `time_only`.
- **leaderboard**: в отчёте добавлены секции `Candidate Shortlist / Leaderboard` и `Normalization impact on leaderboard rules`. Они показывают, что top-11 practical screen после нормализации занят только `time_only` и `movement_plus_time`; фрактальные профили туда не вошли.
- **notes**: `locked_test=not_opened`; ranked budget `243`, executed jobs `324` из-за diagnostic-only controls; full-selection permutation не выполнена (`permutation_gate=NOT_RUN_FOR_FULL_SELECTION`); final normalized audit имеет `ERROR=0`, но `WARNING` по constant/near-constant features и token truncation disclosure.

## [2026-07-21] — Fractal0 Rich Entry Quality (RESEARCH_HINT_RICH_FEATURES)
- **report**: `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`
- **topics**: `fractal0`, `rich_entry_quality`, `ml_entry`, `feature_contract`, `research_hint`
- **summary**: Добавлен rich-entry mode для `S2/E3/M0/X2`: 243 eligible Phase A configurations по профилям признаков, моделям, целям и top-фильтрам; planned/no-fill diagnostics и полный feature contract сохранены в structured artifacts.
- **artifacts**: `ML/reports/fractal0_rich_entry_quality.json`, `ML/reports/fractal0_rich_entry_quality_summary.csv`, `ML/reports/fractal0_rich_entry_quality_feature_contract.csv`, `ML/baseline/benchmark_fractal0_entry_quality_filter.py`, `tests/test_fractal0_entry_quality_filter.py`
- **decision**: После audit bugfix и corrected full rerun winner остался `time_only / linear / target_entry_ev_regression / top30`; fixed `val_eval PF=4.0268`, `BS_p05=3.3955`. Structural/rich profiles прошли feature-contract gates, но не победили selection protocol.
- **leaderboard**: в отчёте есть таблица `Candidate Shortlist`, отсортированная по fixed `val_eval` screen. Она показывает research shortlist из `planned_geometry_only`, `movement_plus_time`, `structure_nearest_k40`/`relative_geometry_k40` для следующей заранее заданной проверки, а не новый winner selection.
- **notes**: `locked_test=not_opened`; внесён bugfix переноса `fractal*`, nearest selection, score diagnostics, movement provenance и audit artifacts. JSON теперь раскрывает cumulative search budget, `TIME_ONLY_WINNER` как note, `feature_importance_by_profile.csv=NOT_PRODUCED` и `permutation_null_repeats_executed_for_full_selection=0`.

## [2026-07-21] — Fractal0 Entry Quality Filter (RESEARCH_ONLY)
- **report**: `docs/reports/2026-07-21-fractal0-entry-quality-filter.md`
- **topics**: `fractal0`, `entry_quality_filter`, `ml_entry`, `m5_execution_ordering`, `research_only`
- **summary**: Добавлен bounded runner ML-entry фильтра для `S2/E3/M0/X2` stop-grid winner; после аудита cutoff для simple baselines стал NaN-safe, а ML-entry признаки переведены на pre-order planned limit/stop/R contract.
- **artifacts**: `ML/reports/fractal0_entry_quality_filter.json`, `ML/reports/fractal0_entry_quality_filter_summary.csv`, `ML/reports/fractal0_entry_quality_filter_score_diagnostics.csv`, `ML/baseline/benchmark_fractal0_entry_quality_filter.py`, `tests/test_fractal0_entry_quality_filter.py`
- **decision**: Исправленный winner `entry_quality_top10` выбран на `val_select`, но провалился на `val_eval`: `PF=1.9543`, `BS_p05=0.9713` против no-mask `BS_p05=2.2865`; lifecycle `research_hint`, не frozen rule.
- **notes**: `locked_test=not_opened`; actual `val_eval` selected fraction `2.31%`; simple baselines теперь валидны и конкурентны (`simple_r_value_top50 val_eval BS_p05=2.3350`).

## [2026-07-21] — Fractal0 Stop Grid M5 (RESEARCH_ONLY)
- **report**: `docs/reports/2026-07-21-fractal0-stop-grid-m5.md`
- **topics**: `fractal0`, `stop_policy`, `m5_execution_ordering`, `ml_exit`, `research_only`
- **summary**: Stop-policy grid `4 x 3 x 2 x 12` выполнен без полного stress-spread: `completed=576`, `failed=0`; `stop_policy_id` включён в ключи выбора, resume, permutation, attribution и artifacts.
- **artifacts**: `ML/reports/fractal0_stop_grid_m5.json`, `ML/reports/fractal0_stop_grid_m5_summary.csv`, `ML/reports/fractal0_stop_grid_m5_stop_diagnostics.csv`, `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- **decision**: Winner по `val_select`: `S2_fractal0_buffer_0_5_entry_floor_2 / E3_open_pullback_1_0atr / M0_no_mask / X2_ml_opposite_any_p0_50`; на `val_eval` PF `2.7873`, `BS_p05=2.5085`, но он не доказал превосходство над S0/X0 baseline по BS_p05.
- **notes**: `locked_test=not_opened`; `stress_spread_status=deferred_shortlist_only`; `pnl_r` означает одинаковый риск на сделку, а не одинаковый фиксированный лот; M1 control имеет малый N и не сравнивается с M0 на равных.

## [2026-07-21] — Fractal0 Entry/Exit Grid (RESEARCH_ONLY)
- **report**: `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`
- **topics**: `fractal0`, `entry_exit_grid`, `ohlc_simulation`, `ml_exit`, `permutation_correction`
- **summary**: Полная сетка `4 x 2 x 48` выполнена на H1 и затем полностью пересчитана с M5 execution ordering; permutation correction PASS, stress-spread disclosure выполнен.
- **artifacts**: `ML/reports/fractal0_entry_exit_grid_m5_full.json`, `ML/reports/fractal0_entry_exit_grid_m5_full_summary.csv`, `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, `tests/test_fractal0_entry_exit_grid.py`
- **decision**: Новый M5 full-grid winner `E3_open_pullback_1_0atr / M0_no_mask / X0_fixed_r_0_7` остаётся `research_only`, не candidate: `locked_test` не открыт, winner выбран после широкого validation grid-search.
- **notes**: `val_eval PF=2.7247`, `BS_p05=2.4868`, stress PF `2.2945`, `ambiguous_same_bar_rate=0.0074`; следующий шаг — заранее зафиксированный stop-policy / entry-quality follow-up, не `locked_test`.

## [2026-07-10] — Fractal0 Price Entry Mechanics Oracle-Preflight (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-07-10-fractal0-price-entry-mechanics.md`
- **topics**: `fractal0_price`, `entry_mechanics`, `oracle_preflight`, `retest_zone`, `research_only`
- **summary**: Добавлен oracle-runner для входа через возврат цены к зоне около `fractal0_price`; выбранное на `train_core` правило `zone_edge / 0.5 ATR / lag 6 / H3 / spread 0.2` дало diagnostic ratio `1.2421` на `val_stop`.
- **artifacts**: `ML/reports/fractal0_price_entry_mechanics.json`, `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`, `tests/test_fractal0_price_entry_mechanics.py`
- **decision**: Gate не пройден: `val_stop` содержит 2 активных года при требовании 3, поэтому verdict `diagnostic_only`, lifecycle `exploratory_result`; повышение до `research_only` запрещено.
- **notes**: Review fixes 2026-07-20: `ratio_without_best_year` считает лучший год по yearly ratio, gate требует simple-rule comparison, side audit требует обе стороны. `locked_test` не открыт; `spread=0.00` не участвовал в gate; exit contract отсутствует.

## [2026-07-10] — Direction Inside Frozen Mask Narrow Replication (FAIL / REJECT_DIRECTION_REPLICATION)
- **report**: `docs/reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md`
- **topics**: `entry_based`, `direction`, `frozen_movement_mask`, `narrow_replication`, `seed_stability`, `reject_direction`
- **summary**: Заранее зафиксированная narrow replication матрица `nearest_k60 / extra_trees / entry_log_ratio` выполнена на seeds `41..45`; H9 пропущен preflight из-за отсутствующих target columns, выполнено `10/10`.
- **artifacts**: `ML/reports/direction_inside_frozen_movement_regime_narrow_replication.json`, `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`, `tests/test_direction_inside_frozen_movement_regime_rich_features.py`
- **decision**: H3 не воспроизвёл weak direction-effect: median `val_eval_inside_mask=0.499080`, seeds `>=0.52` только `2/5`; verdict `REJECT_DIRECTION_REPLICATION`. Direction-inside-frozen-mask снят с near-term roadmap.
- **notes**: H6 был сильнее, но secondary robustness horizon не может заменить H3 задним числом; `locked_test` не открыт, PnL/PF/trading claims запрещены.

## [2026-07-09] — Direction Inside Frozen Mask Rich Features Full Grid (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md`
- **topics**: `entry_based`, `direction`, `frozen_movement_mask`, `rich_features`, `full_grid`, `resume`
- **summary**: Rich-features runner завершил полный grid `240/240` с full-train политикой, frozen-mask только для оценки, heartbeat/progress/resume и `24` потоками для параллельных моделей.
- **artifacts**: `ML/reports/direction_inside_frozen_movement_regime_rich_features.json`, `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`, `tests/test_direction_inside_frozen_movement_regime_rich_features.py`
- **decision**: Winner `nearest_k60 / H3 / entry_log_ratio / extra_trees`: `val_select_inside_mask=0.570170`, `val_eval_inside_mask=0.529056`; verdict `DIRECTION_REPLICATION_REQUIRED`, статус остаётся `DIAGNOSTIC_ONLY`.
- **notes**: `locked_test` не открыт; PnL/PF/trading claims запрещены; следующий шаг — заранее зафиксированная репликация, а не tuning по `val_eval`.

## [2026-07-08] — Direction Inside Frozen Movement Regime (REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME)
- **report**: `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`
- **topics**: `entry_based`, `direction`, `frozen_movement_mask`, `split_row_id`, `reject_direction`
- **summary**: Расследован root cause дубликатов `split + time`: один бар может дать несколько entry-строк/фракталов, поэтому freeze export получил `split_row_id` и direction join переведён на `split + split_row_id`. После repair baseline-и запущены, но direction signal отвергнут.
- **artifacts**: `ML/reports/direction_inside_frozen_movement_regime.json`, `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py`, `tests/test_direction_inside_frozen_movement_regime.py`
- **decision**: Winner `extra_trees_small` выбран только на `val_select`, но не прошёл `val_eval`/robustness: `val_eval balanced_accuracy=0.5287`, `mcc=0.0579`, disclosure 2026 хуже случайного. Ветка закрыта как reject, не trading candidate.
- **notes**: `locked_test` не открыт; PnL/PF и trading claims запрещены; frozen movement rule не менялся.

## [2026-07-08] — Entry-Based Movement Filter Replication Freeze (FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN)
- **report**: `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`
- **topics**: `entry_based`, `movement_filter`, `freeze`, `replication`, `research_segmentation`
- **summary**: Заморожен ровно один заранее выбранный movement-filter без расширения search space: `simple_combined / extra_trees_small / H3 / top_fraction=0.05`. Source hashes, frozen rule hash, frozen config hash, yearly gate, random baseline и score cutoff diagnostics зафиксированы в freeze artifact.
- **artifacts**: `ML/reports/entry_based_movement_filter_freeze.json`, `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`, `tests/test_entry_based_movement_filter_freeze.py`
- **decision**: Разрешён только вывод `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`; это research segmentation mask для следующего плана, а не direction, не PnL/PF, не trading candidate, не live rule и не permission to open `locked_test`.
- **notes**: `2026` остаётся disclosure-only; `top_fraction=0.05` не является фиксированным абсолютным cutoff между split-ами и годами.

## [2026-07-07] — Entry-Based Movement Filter Design (SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY)
- **report**: `docs/reports/2026-07-07-entry-based-movement-filter-design.md`
- **topics**: `entry_based`, `movement_filter`, `movement_regime`, `simple_baseline`
- **summary**: Поверх amplitude artifact добавлен bounded CLI для простого pre-entry movement filter без direction и без PnL/PF. Выбран один filter: `simple_combined / extra_trees_small / H3 / top_fraction=0.05`; на `val_eval` он дал `movement_lift=2.4806` при `selected_n=333`.
- **artifacts**: `ML/reports/entry_based_movement_filter.json`, `ML/baseline/benchmark_entry_based_movement_filter.py`, `tests/test_entry_based_movement_filter.py`
- **decision**: Разрешён только вывод `SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY`; direction, торговая интерпретация и открытие `locked_test` запрещены. Следующий допустимый шаг — только узкая репликация/заморозка этого одного filter-а без расширения search space.
- **notes**: `2026` остаётся только disclosure (`selected_n=59`, `movement_lift=1.6292`); full verification: `1180 passed, 30 warnings`.

## [2026-07-07] — Entry-Based Amplitude Movement Regime Audit (DIAGNOSTIC_ONLY / AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES)
- **report**: `docs/reports/2026-07-07-entry-based-amplitude-movement-regime.md`
- **topics**: `entry_based`, `amplitude`, `movement_regime`, `simple_baselines`, `leakage_audit`
- **summary**: Полный clean run завершён: `384/384`, `failed_runs=[]`, `elapsed_sec=4008.4`, `effective_threads=24`. Лучший eligible результат `simple_combined / extra_trees_small / H3`: `val_select_spearman_median=0.571142`, `val_eval_spearman_median=0.693452`; после ревью `yearly.csv` расширен до `2136 x 11` с идентификаторами запуска.
- **artifacts**: `ML/reports/entry_based_amplitude_movement.json`, `ML/baseline/benchmark_entry_based_amplitude_movement.py`, `ML/reports/entry_based_amplitude_movement_seed_aggregate.csv`
- **decision**: Amplitude / movement-regime связь сильная, но объясняется простыми baseline-признаками (`time+ATR`, `simple_combined`). Verdict: `AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES`; freeze, direction-trading вывод и открытие `locked_test` запрещены.
- **notes**: `low_n_disclosure=2026` не использовался для verdict; `distance_to_level_pre_entry_only` пропущен как `SKIPPED_NO_DECISION_PRICE`; post-entry diagnostic имеет `selection_eligible=false`; wide search требует отдельной репликации.

## [2026-07-07] — Entry-Based Fractal Sequence Transformer (DIAGNOSTIC_ONLY / PIVOT_AMPLITUDE)
- **report**: `docs/reports/2026-07-07-entry-based-fractal-sequence-transformer.md`
- **topics**: `entry_based`, `next_open`, `sequence_transformer`, `fractal_sequence`, `pivot_amplitude`
- **summary**: Полный sequence-прогон завершён: `9/9`, `failed_runs=[]`, `elapsed_sec=45477.6`, `entry_based_smoke_check.status=PASS`, `split_horizon_overlap_check.status=PASS`, `tensor_audit.status=WARNING` с `audit_decisions`.
- **artifacts**: `ML/reports/entry_based_sequence_transformer.json`, `ML/baseline/benchmark_entry_based_sequence_transformer.py`
- **decision**: Sequence Transformer не спас direction для `entry-based next open`: лучший candidate direction `nearest_k80_sequence / transformer_medium / H24` дал `0.0539 -> 0.0050`. Amplitude снова сильнее: `nearest_k60_sequence / sequence_flat_hist_gradient_boosting / entry_up H3` дал `0.3229 -> 0.3337`. Вердикт: `PIVOT_AMPLITUDE`; следующий честный шаг — отдельная amplitude / movement-regime постановка.
- **notes**: `locked_test` не открыт; 2026 только disclosure; `tensor_audit=WARNING`; amplitude не является trading signal.

## [2026-07-06] — Entry-Based Powerful Tabular Models (DIAGNOSTIC_ONLY / PIVOT_AMPLITUDE)
- **report**: `docs/reports/2026-07-06-entry-based-powerful-tabular-models.md`
- **topics**: `entry_based`, `next_open`, `powerful_tabular`, `pivot_amplitude`, `xgboost`
- **summary**: Чистый прогон `--no-resume` завершён: `40/40`, `failed_runs=[]`, `elapsed_sec=37777.7`, `thread_count=24`. `entry_based_smoke_check.status=PASS`, `split_horizon_overlap_check.status=PASS`, `scale_audit.status=WARNING`, `audit_decisions` записаны.
- **artifacts**: `ML/reports/entry_based_powerful_tabular.json`, `ML/baseline/benchmark_entry_based_powerful_tabular.py`
- **decision**: Рост мощности табличных моделей не спас direction в текущей mechanics `entry-based next open`. Вердикт: `PIVOT_AMPLITUDE`. Этот отчёт закрывает tabular-capacity гипотезу, но не roadmap-пункт про sequence-transformer на serialized 100-fractal history. Ближайший незавершённый шаг — отдельный bounded plan для sequence-transformer; amplitude / movement-regime остаётся следующим допустимым направлением после этой проверки или отдельной параллельной веткой.
- **notes**: `locked_test` не открыт; `scale_audit=WARNING`; amplitude не является trading signal.

## [2026-07-04] — Entry-Based Next Open Closeout (DIAGNOSTIC_ONLY / PIVOT)
- **report**: `docs/reports/2026-07-04-entry-based-next-open-closeout.md`
- **topics**: `entry_based`, `next_open`, `fractal_selection`, `updn`
- **summary**: Чистый прогон `--no-resume` завершён: `20/20`, `elapsed_sec=2274.4`, `thread_count=24`. `entry_based_smoke_check.status=PASS`; rows: `train=44159`, `validation=13296`, `low_n_disclosure=1162`.
- **artifacts**: `ML/reports/entry_based_next_open_closeout.json`, `ML/baseline/benchmark_entry_based_next_open_closeout.py`
- **decision**: Текущая направленная ветка `entry-based next open` не проходит closeout как direction signal. Вердикт closeout: `PIVOT`. Следующий допустимый шаг — отдельная bounded постановка для amplitude / movement-regime target, без открытия `locked_test` до freeze.
- **notes**: `locked_test` не открывать до freeze; есть low-N disclosure

## [2026-07-03] — Fractal Selection Ablation On Entry-Based Target (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-07-03-fractal-selection-ablation-entry-based-target.md`
- **topics**: `entry_based`, `next_open`, `fractal_selection`, `updn`
- **summary**: Чистый повторный прогон `--no-resume` завершён: `120/120` run за `12525.8s` (`3 ч 29 мин`), `target_mode=rebuilt`, `entry_based_target_contract_check=PASS`. Контрольные точки зафиксированы в structured artifact: `anchor_contract`, `same_feature_bundle`, `updn_horizons=3/6/12`, target-builder fingerprint и progress metadata.
- **artifacts**: `ML/reports/entry_based_updn_fractal_selection_ablation.json`, `ML/reports/entry_based_updn_fractal_selection_ablation_rows.csv`, `ML/reports/entry_based_updn_fractal_selection_ablation_metrics.csv`
- **decision**: Смена способа отбора фракталов не переоткрыла ветку `entry-based next open` как устойчивый направленный сигнал. Если продолжать линию, сначала нужно решить, имеет ли `H12` практический смысл для `next open after signal_time`, и добавить entry-based smoke-check. Узкий rerun по `corridor_5atr`, `nearest_k20`, `nearest_k60`, `nearest_k80` допустим только после этого решения.
- **notes**: `diagnostic_holdout` и `low_n_disclosure` только disclosure; `distribution_audit=WARNING`.

## [2026-07-02] — Entry-Based Up/Dn Price-Feature Matrix (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-07-02-entry-based-updn-price-feature-matrix.md`
- **topics**: `entry_based`, `next_open`, `updn`
- **summary**: На том же `entry-based` target и той же механике `next open after signal_time` проверены 7 профилей (`21/21` run, 3 seed). Ни один primary или secondary блок не дал убедительного направленного сигнала: лучший `val_stop entry_log_ratio` у `distance_atr` только `0.0354`; на disclosure лучший блок уже `path_reaction` (`0.0445` на `2023-2025`, `0.0881` на `2026`), то есть устойчивого winner нет.
- **artifacts**: `ML/reports/entry_based_updn_price_feature_matrix.json`, `ML/reports/entry_based_updn_price_feature_matrix_rows.csv`, `ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py`
- **decision**: Ограниченная price-feature matrix не переоткрыла ветку `next open`: проблема не выглядит как недобор одного простого ценового блока. Следующий допустимый шаг — только после исправления summary logic и артефактного слоя; выбирать один follow-up block сейчас преждевременно.
- **notes**: нужен fix summary/artifact layer; единственного follow-up кандидата нет.

## [2026-07-02] — Next Open Entry Up/Dn Foundation (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-07-02-next-open-entry-updn-foundation.md`
- **topics**: `next_open`, `updn`, `h6`, `h12`
- **summary**: Target пересчитан от фактического `entry_open`: первый доступный H1 `open` строго после `signal_time`. Направленный `entry_log_ratio` вне обучения почти не ранжируется: `val_stop` `-0.0021/0.0136/0.0107`, `2023-2025` `0.0055/0.0046/0.0203`, `2026` `-0.0074/0.0140/-0.0122` для `H3/H6/H12`.
- **artifacts**: `ML/reports/next_open_entry_updn_rows.csv`, `ML/reports/next_open_entry_updn_foundation.json`, `ML/baseline/benchmark_next_open_entry_updn_foundation.py`
- **decision**: Ветка `next open after signal_time` отклонена именно как направленная механика входа для `Regression Up/Dn`. Открытым остаётся только отдельный сценарий входа через область `fractal0_price` или другой target, измеряемый от фактического исполнения.
- **notes**: есть low-N disclosure; доступность всех `structure_full` признаков к `signal_time` отдельно не доказана.

## [2026-07-02] — Regression Up/Dn Already Moved Audit (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-07-02-regression-updn-already-moved-audit.md`
- **topics**: `updn`, `regression_updn`, `already_moved`, `h6`, `h12`
- **summary**: Во всех трёх split связь `pred_log_ratio` с будущим движением после входа на следующий `open` остаётся около нуля: `H3/H6/H12` на `val_stop` `-0.0149/-0.0174/0.0010`, на `2023-2025` `-0.0336/-0.0252/-0.0173`, на `2026` `-0.0040/-0.0038/0.0043`. При этом связь с исходным target от `fractal0_price` остаётся высокой: на `val_stop` Spearman `0.8786 / 0.7815 / 0.6749` для `H3/H6/H12`.
- **artifacts**: `ML/baseline/analyze_regression_updn_already_moved_audit.py`
- **decision**: Для target family `Regression Up/Dn` схема входа `next open after signal_time` отклонена. Следующий допустимый шаг — только механика входа, привязанная к `fractal0_price` или её ретесту, без возврата к немедленному `market-entry` на следующем баре.
- **notes**: есть low-N disclosure

## [2026-07-01] — Regression Up/Dn Ratio Audit (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-07-01-regression-updn-ratio-audit.md`
- **topics**: `next_open`, `updn`, `regression_updn`, `already_moved`, `ratio_audit`
- **summary**: Отношение `up_h/dn_h` действительно хорошо предсказывается от цены фрактала: на `val_stop` Spearman `pred_log_ratio` vs `actual_log_ratio` равен `0.7881 / 0.7212 / 0.6264` для `H3/H6/H12`. Для входа на следующем `open` этот же сигнал почти исчезает: Spearman с `next-open log-ratio` равен `-0.011 / -0.017 / 0.001`.
- **artifacts**: `ML/reports/regression_updn_ratio_audit_predictions.csv`
- **decision**: Target-сигнал и сигнал немедленного входа оказались разными объектами. Ratio audit стал прямой методической подводкой к already-moved audit: перед торговой интерпретацией нужно отдельно измерять, какая часть движения уже произошла до доступной точки входа.
- **notes**: JSON/cache из отчёта отсутствуют в текущем дереве.

## [2026-06-30] — Regression Up/Dn Target Foundation (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-30-regression-updn-target-foundation.md`
- **topics**: `updn`, `regression_updn`
- **summary**: Полный прогон: `75/75` (5 профилей × 5 model families × 3 seed), elapsed `4501.9s`, `xgb_n_jobs=24`. Лучший bounded target-foundation signal: `selected_profile=structure_full`, `selected_horizon=3`.
- **artifacts**: `ML/reports/regression_updn_target_foundation.json`, `ML/baseline/benchmark_regression_updn_target_foundation.py`
- **decision**: `research_gate_status = TARGET_FOUNDATION_PASSED`, но `artifact_status = DIAGNOSTIC_ONLY`. Следующий шаг: отдельный узкий confirmatory cycle поверх `structure_full` и короткого horizon (`H3` или `H6`) без нового широкого search.
- **notes**: нет

## [2026-06-30] — Stage 6.3: H6 Feature Parity Check (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-30-stage6_3-h6-feature-parity-check.md`
- **topics**: `stage6`, `h6`, `h12`, `price_action`
- **summary**: Полный прогон: `39/39` (13 профилей × 3 seed), `xgb_n_jobs=24`, elapsed `3175s`. H6 baseline (`h6_clock_shift_back`): median val AUC `0.6649` (vs H12 `0.6174`), selected PF `1.006`, но permutation p-value `0.700`.
- **artifacts**: `ML/reports/stage6_3_h6_feature_parity.json`, `ML/baseline/benchmark_stage6_3_h6_feature_parity.py`
- **decision**: Новый тест `tests/test_stage6_3_h6_feature_parity.py`: 24 теста (контракт, профили, feature names, билдеры, gate, runner, CLI, resume). Gate: `NO_ADDITIVE_VALUE_CONFIRMED`; H6 parity не меняет standing conclusions.
- **notes**: нет

## [2026-06-30] — Stage 6.2: range_w1_atr post-mortem (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md`
- **topics**: `stage6`, `range`, `atr`, `post`, `mortem`
- **summary**: `range_w1_atr` доминирует в Stage 6.2: top/second importance ratio `7.56`. На non-zero `val_stop` связь с target умеренная (`corr=0.202`), но связь с PnL почти нулевая (`corr=0.008`).
- **artifacts**: `ML/reports/stage6_2_range_w1_postmortem.json`, `ML/baseline/analyze_stage6_2_range_w1_postmortem.py`
- **decision**: Stage 6.2 остаётся `DIAGNOSTIC_ONLY`; следующий исследовательский шаг — `Regression Up/Dn target foundation`.
- **notes**: нет

## [2026-06-30] — Stage 6.2: H12 Price Action Feature Family (TRADING_GATE_FAILED)
- **report**: `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md`
- **topics**: `stage6`, `h12`, `price_action`
- **summary**: Полный прогон: `15/15` (5 профилей × 3 seed), `xgb_n_jobs=24`, elapsed `1341s`. Primary `h12_price_action_core`: median val AUC `0.6233`, PR AUC lift `0.1402`, selected PF `1.307`, но median permutation p-value `0.160` > `0.10`.
- **artifacts**: `ML/reports/stage6_2_h12_price_action_feature_family.json`, `ML/baseline/benchmark_stage6_2_price_action.py`
- **decision**: Новый тест `tests/test_stage6_2_price_action.py`: 17 тестов (контракт, denylist, no-future OHLC windows, feature names, preflight, definitive mask, gate, runtime metadata, CLI flags). Combined profiles дали AUC delta около `+0.010`, ниже required `+0.020`, и median permutation p-value `0.185`/`0.255`; delta gate FAIL.
- **notes**: нет

## [2026-06-29] — Stage 6.1: H12 Relative Fractal Geometry (MODEL_GATE_FAILED)
- **report**: `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`
- **topics**: `stage6`, `h12`, `relative_geometry`
- **summary**: Полный прогон: `27/27` (9 профилей × 3 seed) за 55.2 мин. Primary `h12_corridor3_relative_geometry`: median val AUC `0.5316` -> MODEL_GATE_FAILED.
- **artifacts**: `ML/baseline/benchmark_stage6_1_relative_geometry.py`
- **decision**: Baseline `h12_clock_shift_back` подтверждает валидность: AUC `0.6174`, threshold SELECTED PF 1.25. Baseline+geometry delta test: три combined-профиля дали только `+0.0026..+0.0048` AUC и ухудшили median PF; delta gate FAIL.
- **notes**: нет

## [2026-06-29] — Stage 6.0: Outcome-Based Triple-Barrier Foundation (TRADING_GATE_FAILED)
- **report**: `docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`
- **topics**: `stage6`, `h6`, `triple_barrier`
- **summary**: Полный прогон: `12/12` (2 горизонта × 2 профиля × 3 seed). Primary `H6_clock_shift_back`: median val AUC `0.6888`, PR AUC lift `0.1141` -> model gate PASS.
- **artifacts**: `ML/baseline/benchmark_stage6_outcome_based.py`
- **decision**: Короткий H6 target содержит модельный сигнал, но текущий fixed-threshold протокол не превращает его в торговое правило. Следующий допустимый шаг — только bounded H6 calibration/threshold follow-up, без широкого перебора horizon/ATR/TP/SL.
- **notes**: нет

## [2026-06-29] — Stage 5.4: Fast Price/ATR Ablation (DIAGNOSTIC_ONLY, REJECTED)
- **report**: `docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md`
- **topics**: `stage5`, `fast`, `price`, `atr`, `ablation`
- **summary**: Полный прогон: `72/72`, `workers=12`, `xgb_threads=1`. JSON status: `DIAGNOSTIC_ONLY`.
- **artifacts**: `docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md`
- **decision**: Gate: per-seed delta ≥ 0.02 в 2/3 seeds + PR AUC lift ≥ 0.03. Вывод: REJECT_PRICE_COORD. Price/ATR признаки не объясняют missing `fast` сигнал. Расширение price-поиска не требуется.
- **notes**: нет

## [2026-06-26] — Stage 5.3: дискретная постановка time-to-breach (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-26-stage5_3-time-to-breach-target-reformulation.md`
- **topics**: `stage5`, `time_to_breach`, `back_impulse`
- **summary**: Полный прогон завершён: `432/432`, `workers=12`, `xgb_threads=1`. JSON status: `TARGET_REFORMULATION_FOUND`.
- **artifacts**: `ML/reports/stage5_3_time_to_breach_target_reformulation.json`
- **decision**: Stage 5.3 completed target reformulation diagnostics for time-to-breach; status is taken from `ML/reports/stage5_3_time_to_breach_target_reformulation.json`; artifact `ML/reports/stage5_3_time_to_breach_target_reformulation.json`. Вердикт отчёта остаётся `DIAGNOSTIC_ONLY`: `2023-2025` — diagnostic disclosure, не независимое подтверждение.
- **notes**: `2023-2025` только diagnostic disclosure

## [2026-06-25] — Stage 5.2: регрессия времени до пробоя фрактального стопа (COMPLETED)
- **report**: `docs/reports/2026-06-25-stage5_2-time-to-breach-regression.md`
- **topics**: `stage5`, `time_to_breach`, `back_impulse`, `fractal_stop`
- **summary**: Вердикт: DIAGNOSTIC_ONLY Прогон завершён полностью: `42/42`
- **artifacts**: `ML/reports/stage5_2_time_to_breach_regression.json`
- **decision**: Stage 5.2 не переоткрывает `H6_off05`, но после bugfix показывает содержательное ранжирование времени до пробоя. Главный повторяющийся сигнал снова `back`. Текущая обычная регрессия одного числа `bars_to_breach` не проходит candidate-gate из-за MAE хуже constant baseline и невалидного oracle comparison; следующий шаг — дискретная/цензурированная постановка (`breach_after_k`, ordinal buckets), без широкого перебора.
- **notes**: `2023-2025` только diagnostic disclosure

## [2026-06-25] — Stage 5.1b: Up/Dn абляция и baseline `clock + shift` (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md`
- **topics**: `updn`, `stage5`, `back_impulse`, `xgboost`
- **summary**: Вердикт: DIAGNOSTIC_ONLY `updn_full` даёт слабую добавку над `clock_shift`: sell `+0.0048` AUC, buy `+0.0059`
- **artifacts**: `ML/reports/stage5_1b_updn_field_ablation.json`, `MT/MQL4/Files/Nero.csv`
- **decision**: Stage 5.1b не переоткрывает `H6_off05`. Up/Dn поля не стоит включать в следующий стартовый профиль по умолчанию: их самостоятельный сигнал мал, а добавка к структуре отрицательна на validation. Главный устойчивый след остаётся у `back`; допустимый следующий шаг — только узкий follow-up вокруг `back`/`impulse`, без нового широкого поиска по `H6_off05`.
- **notes**: `2023-2025` только diagnostic disclosure; есть low-N disclosure

## [2026-06-24] — Stage 5.1: структурная абляция фрактальных полей (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md`
- **topics**: `stage5`, `xgboost`
- **summary**: Вердикт: DIAGNOSTIC_ONLY Единственное поле с согласованным итогом на обеих целях: `back` = `likely_useful`
- **artifacts**: `ML/reports/stage5_1_structural_field_ablation.json`
- **decision**: Stage 5.1 показывает диагностическую прибавку структурных полей над clock-only baseline, но не переоткрывает `H6_off05` как кандидата. Самый сильный след — `back` (`back_val`, сила тыловой границы уровня). Следующий допустимый шаг по этой ветке — только узкий mini-follow-up `time_only / time+back / time+impulse / time+back+impulse / structure_full / structure_full_without_back`, без нового широкого перебора.
- **notes**: `2023-2025` только diagnostic disclosure; есть low-N disclosure

## [2026-06-24] — Stage 5.0f: диагностика устойчивости сигнала во времени (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-24-stage5_0f-signal-stationarity.md`
- **topics**: `stage5`, `signal_stationarity`, `xgboost`
- **summary**: Вердикт: DIAGNOSTIC_ONLY, overall_verdict = inconclusive Общий итог: неопределённый — не удалось ни доказать распад сигнала, который лечится более близким по времени обучением, ни подтвердить его устойчивость
- **artifacts**: `ML/reports/stage5_0f_signal_stationarity.json`
- **decision**: Stage 5.0f не даёт оснований ни закрыть тему как доказанно неустойчивую, ни реабилитировать её как устойчивую. H2 (temporal decay) скорее опровергнута направлением fixed>rolling, но природа отрицательного результата (H1 vs H2) не установлена. Без нового независимого периода `2026+` большой перебор по `H6_off05` не оправдан.
- **notes**: нет

## [2026-06-23] — Stage 5.0e: проверка малого Transformer после провала (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-23-stage5_0e-small-transformer-check.md`
- **topics**: `stage5`, `h6`, `xgboost`, `transformer`
- **summary**: Вердикт: DIAGNOSTIC_ONLY. `overfit_hypothesis_supported = yes`: `small_regularized` уменьшил median `overfit_drop_after_best` с `0.0170` до `0.0009` при потере median `val_auc` только `-0.0028`.
- **artifacts**: `ML/reports/stage5_0e_small_transformer_check.json`
- **decision**: Меньшая модель действительно уменьшает признаки переобучения, но не меняет итогового решения. `H6_off05 stop broken` остаётся закрытым; дальнейшие шаги только через новую цель или новые признаки.
- **notes**: нет

## [2026-06-23] — Stage 5.0d: диагностический скрининг профилей (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md`
- **topics**: `stage5`, `h6`, `fractal_stop`, `xgboost`, `transformer`
- **summary**: Вердикт: DIAGNOSTIC_ONLY, решение этапа: `h6_off05_target_exhausted` — ни один профиль не прошёл порог +0.02. Лучший: sell `all100_relative_price_time` (delta +0.0111), lift_pass OK (0.5415 ≤ 0.5539), но AUC_pass FAIL.
- **artifacts**: `ML/reports/stage5_0d_diagnostic_screening.json`
- **decision**: Вердикт: DIAGNOSTIC_ONLY, решение этапа: `h6_off05_target_exhausted` — ни один профиль не прошёл порог +0.02. Лучший: sell `all100_relative_price_time` (delta +0.0111), lift_pass OK (0.5415 ≤ 0.5539), но AUC_pass FAIL.
- **notes**: нет

## [2026-06-22] — Stage 5.0c: повторная проверка на двух целях (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md`
- **topics**: `stage5`, `xgboost`, `transformer`
- **summary**: overall_pass: FAIL — гипотеза не воспроизвелась. G1 (AUC): FAIL — Transformer уступил XGBoost same-profile на обеих целях. Sell: median val AUC 0.6643 vs XGBoost 0.6723 (0 seeds выше порога). Buy: median val AUC 0.6752 vs XGBoost 0.6873 (0 seeds выше порога).
- **artifacts**: `ML/reports/stage5_0c_cross_target_rerun.json`
- **decision**: G3 (cross_target): FAIL — ни одна цель не прошла G1+G2. G5 (seed_spread): PASS — sell spread 0.0054, buy spread 0.0104 (оба < 0.03).
- **notes**: holdout раскрыт только диагностически

## [2026-06-21] — Stage 5.0b: Asinh Transformer rerun (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-21-stage5_0b-asinh-rerun.md`
- **topics**: `stage5`, `h6`, `xgboost`, `transformer`
- **summary**: Sell: лучший Transformer `all100_relative_price_time` не прошёл AUC-порог (`0.6719` против `0.6731`); разрыв `0.0012` мал и в single-seed режиме не считается устойчивым сигналом. `lift_30` на `val_stop` лучше XGBoost (`0.5044` против `0.5539`), но оба условия отбора одновременно не выполнены. Buy: цель оказалась непустой после исправления загрузки (`22745` train rows, positive_rate `0.3701`, OHLC verification `PASS 50/50`). Лучший Transformer `all100_relative_price_time` уступил XGBoost по AUC (`0.6762` против `0.6894`).
- **artifacts**: `ML/reports/stage5_0b_asinh_rerun.json`
- **decision**: DIAGNOSTIC_ONLY. Stage 5.0b не открывает multi-seed продолжение и не объявляет trading winner. Следующая обоснованная гипотеза — отдельный заранее зафиксированный прогон `all100_absolute_price_atr_scaled_time_asinh` по sell и buy с честным сравнением против XGBoost на тех же строках.
- **notes**: holdout раскрыт только диагностически

## [2026-06-21] — Stage 5.0a: Feature Distribution Audit + transform comparison (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-20-stage5_0a-feature-distribution-audit.md`
- **topics**: `stage5`, `feature`, `distribution`, `audit`, `transform`
- **summary**: Для 7 rerun-кандидатов после `log1p(ATR)` + signed-log(`price_coord_atr`) исчезли `TAIL_GT10/TAIL_GT20`; остался только `REGIME_SHIFT in ATR`: train p95=1.66, holdout p95=4.80, delta=3.14. Per-position audit выявил скрытую проблему старого `price_coord_atr`: `all100_relative_price_*` имел `TAIL_GT10` на позиции 99 (самый старый фрактал); signed-log убрал этот хвост.
- **artifacts**: `ML/reports/stage5_0a_transform_comparison.json`, `ML/reports/stage5_0a_feature_stats_per_position.csv`, `ML/reports/stage5_0a_transform_comparison_summary.csv`
- **decision**: DIAGNOSTIC_ONLY. `asinh` и `piecewise_tail` лучше текущего варианта по проверке распределения признаков, но это не доказательство качества модели: обучение не запускалось. Следующий Transformer rerun можно планировать с заранее зафиксированным transform-кандидатом или как явно диагностическое сравнение, чтобы не создать новый скрытый перебор конфигураций.
- **notes**: нет

## [2026-06-17] — Stage 5.0: Transformer Breach Holdout — FAIL (FAIL)
- **report**: `docs/reports/2026-06-17-stage5-transformer-breach.md`
- **topics**: `stage5`, `transformer_breach`, `xgboost`, `transformer`
- **summary**: Полноразмерный Transformer (d_model=64, nhead=4, dim_feedforward=128, 40 эпох, train ≤2020) на CPU, single seed [42] Primary profile `all100_base10_time` holdout AUC=0.6018 vs XGBoost=0.6524 (gap −0.051)
- **artifacts**: `ML/reports/stage5_transformer_breach.json`, `ML/models/fractal_breach_transformer.py`, `ML/baseline/benchmark_stage5_transformer_breach.py`
- **decision**: 5 последовательных этапов Fractal Stop провалились (Stage 2->3->4->4.6->5.0). Breach-сигнал статистически подтверждён, но недостаточен для устойчивого ML-превосходства ни в табличной, ни в sequence-архитектуре. Методический risk: признаки Transformer не масштабированы под нейросеть (цена в сотнях/тысячах, остальные ~0..1) — вывод относится к текущей реализации и нормализации. Не строить Stage 5.1 trading layer. Решение: пересмотр постановки или закрытие Fractal Stop ветки.
- **notes**: нет

## [2026-06-15] — Stage 4.7: Walk-Forward Optimization Diagnostics (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-15-walk-forward-diagnostics.md`
- **topics**: `walk_forward`, `xgboost`, `transformer`
- **summary**: Expanding Window (Stage 4.6 protocol — temporal early stopping): ≤2016 -> 2023-2026 PF=0.897, BS_p05=0.679, 357 trades — точное совпадение со Stage 4.6. Расширение обучения до ≤2022: PF=0.84, BS_p05=0.739. Self-val (Anchored/Rolling/Warm-start) завышает количество сделок (1364-1973 vs 357), но паттерн «2023-2026 провал» устойчив во всех 4 вариантах.
- **artifacts**: `ML/reports/walk_forward_diagnostics.json`, `ML/baseline/diagnose_walk_forward.py`
- **decision**: DIAGNOSTIC_ONLY. Проблема не в объёме данных — расширение обучения не спасает. Требуется иной подход (Stage 5.0 Transformer с календарным baseline). Официальный frozen test не открыт; 2023-2026 = диагностический holdout.
- **notes**: нет

## [2026-06-15] — Stage 4.x Remaining Hypotheses Master Plan (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-15-stage4_4-micro-check.md`
- **topics**: `stage5`, `fractal_stop`, `feature_ablation`, `transformer`
- **summary**: Stage 5.0-prep: календарный риск подтверждён (time_only AUC=0.6286 > no_time 0.6113), oracle-mix: PF-gate при AUC≥0.8442 (gap +1768 bp) Stage 4.5: trail_atr_0_2 PF=1.831 (BS_p05=1.462) — лучший diagnostic-результат Fractal Stop; breakeven PF=0.717
- **artifacts**: `ML/baseline/diagnose_stage5_prep.py`, `ML/baseline/benchmark_stage4_6_clean_cycle.py`, `ML/baseline/diagnose_stage4_5_exit_mechanics.py`
- **decision**: DIAGNOSTIC_ONLY. Все гипотезы `docs/audit/to_do.md` выполнены. Stage 4.x закрыт. Следующий шаг — Stage 5.0 Transformer с календарным baseline. Fixed TP R=0.7 — baseline торгового слоя. Trail_atr_0_2 — отдельная диагностическая ветка.
- **notes**: нет

## [2026-06-14] — Stage 4: Глубокая диагностика провала и трейлинг-стоп (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-14-stage4-deep-diagnostics.md`
- **topics**: `fav`, `quantile`
- **summary**: Partial Oracle: fav — большее узкое место, чем breach (PF 14.72 vs 6.61), но синергия колоссальна (perfect_both PF=104.88) Параметры и фильтры: все уже оптимальны. tp_fraction/stop_offset/min_rr — уникальный локальный оптимум. Strong fractal (~0 сделок), ATR regime (вредит), combined breach (вредит), quantile fav (слишком консервативен)
- **artifacts**: `ML/reports/stage4_gap_diagnostics.json`, `ML/baseline/improve_stage4.py`, `ML/baseline/trail_stop_stage4.py`
- **decision**: Модель находит хорошие точки входа, но фиксированный TP/SL не даёт зафиксировать прибыль до разворота. Трейлинг-стоп atr_02 решает проблему механики выхода (PF=1.655) без переобучения моделей. Gap до oracle (104.88) остаётся — нужен Transformer (Stage 5.0) для улучшения breach+fav. Stage 5.1 должен тестировать Transformer с трейлинг-стопом.
- **notes**: нет

## [2026-06-12] — Stage 4.2: Diagnostic recalc с исправленной методикой (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-11-stage4-trade-xgboost.md`
- **topics**: `h6`, `fractal_stop`, `xgboost`
- **summary**: PF Stage 4 winner: 1.106 -> Stage 4.2: 1.015 (Δ = −0.091 — совокупный эффект исправленного диагностического протокола, не изолированное «завышение») BS_p05: 0.923 -> 0.837 (Δ = −0.086)
- **artifacts**: `ML/reports/stage4_2_diagnostic.json`, `ML/baseline/benchmark_fractal_stop_stage4_2.py`
- **decision**: DIAGNOSTIC — breach-модель добавляет реальный сигнал для фиксированного правила (0/500 перестановок, p ≈ 0.002, +0.20 PF над случайным), но его силы недостаточно для устойчивой прибыльности (gate PF > 1.15, исторический selection bias winner не исправлен). Совокупный эффект исправленного диагностического протокола: ΔPF = −0.091. Проблема не в отсутствии сигнала, а в его слабости. Табличные модели на текущем представлении фракталов достигли потолка. Next: Transformer encoder (Stage 5.0) с чистой методикой от Stage 4.2.
- **notes**: нет

## [2026-06-11] — Stage 4: XGBoost Trading Layer + Stage 4.1 controls (COMPLETED)
- **report**: `docs/reports/2026-06-11-stage4-trade-xgboost.md`
- **topics**: `h6`, `h12`, `relative_geometry`, `fractal_stop`, `xgboost`
- **summary**: Primary (`base_raw_plus_time`): winner sell_H6_off05, PF=1.106, BS_p05=0.923, 1/8 таргетов PF≥1.0 Control (`relative_geometry_clean`): winner sell_H6_off05, PF=1.142, BS_p05=0.906, 2/8 таргетов PF≥1.0
- **artifacts**: `ML/reports/stage4_1.json`, `ML/reports/stage4_trade.json`, `ML/reports/stage4_trade_geom.json`
- **decision**: FAIL — рост AUC breach-классификатора с RF 0.645 до XGBoost 0.680 (+345 bp) не конвертируется в статистически значимый PF. Stage 4.1 не подтвердил быстрые улучшения: XGBoost-fav хуже RF-fav, combined breach не проходит gate. Табличные модели (RF, XGBoost) на плоских фрактальных признаках достигли потолка для текущей торговой постановки. Next: Transformer encoder на фрактальной sequence либо пересмотр торговой логики/таргета.
- **notes**: нет

## [2026-06-11] — Fractal parser contract hardening (COMPLETED)
- **report**: `docs/reports/2026-06-11-stage4-trade-xgboost.md`
- **topics**: `fractal`, `parser`, `contract`, `hardening`
- **summary**: `processing/label_signals.py`: `parse_fractal()` теперь принимает только integer-like значения в полях `time`, `direction`, `strong`, `break`, `count`, `shift` (`1`, `1.0`) и отвергает дробные нормализованные значения (`0.1700000018`). Добавлен regression-тест, который предотвращает тихое применение разметочного parser-а к нормализованным `fractal*` полям.
- **artifacts**: `processing/label_signals.py`
- **decision**: `processing/label_signals.py`: `parse_fractal()` теперь принимает только integer-like значения в полях `time`, `direction`, `strong`, `break`, `count`, `shift` (`1`, `1.0`) и отвергает дробные нормализованные значения (`0.1700000018`). Добавлен regression-тест, который предотвращает тихое применение разметочного parser-а к нормализованным `fractal*` полям.
- **notes**: нет

## [2026-06-10] — Stage 3.x: feature profiles + XGBoost breach classifier (FAIL)
- **report**: `docs/reports/2026-06-10-feature-profiles-stage3.md`
- **topics**: `relative_geometry`, `fractal_stop`, `xgboost`, `breach_classifier`
- **summary**: Stage 3 RF: `base_plus_path` (+700 фич: folded mov_h + shift + atr_ratio) FAIL — AUC drops 64–166 bp on all 8 targets Stage 3 RF: `relative_geometry` (+10 фич: price->ATR-relative, density, time) PASS as whole profile — mean +119 bp
- **artifacts**: `ML/reports/stage3_profiles.json`, `ML/reports/stage3_2_xgboost.json`, `ML/reports/stage3_1_profiles.json`
- **decision**: Folded mov_h не несут breach-сигнала для RF в комбинированном профиле. Практический uplift Stage 3.1 даёт time, а не density. Лучший простой кандидат для Stage 4 — XGBoost `base_raw_plus_time`; `relative_geometry_clean` выше всего на 9 bp, но сложнее. Mean AUC 0.70 формально не достигнут: gap около 192–201 bp. Next: Stage 4 validation-only trading simulation.
- **notes**: нет

## [2026-06-10] — Fractal Stop Fav Stage 2: торговый слой (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-10-fractal-stop-fav-stage2.md`
- **topics**: `h12`, `fractal_stop`, `fav`
- **summary**: Grid search на val (8 комбинаций H x off x side, 81 порог): лучшая комбинация sell_H12_off05 PF=0.975. Ни одна не достигла PF > 1.0 Frozen test (test 2022–2026, frozen rule sell_H12_off05): PF=0.837 canonical, 3/5 лет убыточны
- **artifacts**: `ML/baseline/benchmark_fractal_stop_fav.py`
- **decision**: FAIL — торговая постановка breach+fav на RF не работает: PF 0.6–0.98, gap 10–30× до oracle. Oracle (проверка потолка) показывает высокий диагностический потолок механики (perfect_breach PF=8–28, perfect_fav PF=7–24, perfect_both PF=∞ на val), но не является торговым доказательством. Рекомендация: Stage 3 — улучшение breach-классификатора и признаков.
- **notes**: нет

## [2026-06-10] — Fractal Stop Breach Stage 1: сигнал о пробое уровня подтверждён (PASS)
- **report**: `docs/reports/2026-06-10-fractal-stop-breach-stage1.md`
- **topics**: `fractal_stop`, `fractal`, `stop`, `breach`
- **summary**: RF baseline (val, 8 primary таргетов): AUC 0.62–0.68, lift 1.52–1.77, без годовых провалов Frozen test (H=6, off=0.2): buy AUC=0.640, sell AUC=0.649 — сигнал подтверждён на невиданных данных
- **artifacts**: `statistics/data_contract_smoke_check.py`, `ML/baseline/benchmark_fractal_stop_breach.py`
- **decision**: Фрактальные признаки несут сигнал о будущем пробое уровня. Можно переходить к торговому слою (Этап 2).
- **notes**: нет

## [2026-06-04] — Direction-only signal confirmed + TB extension (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-06-04-fractal-ablation.md`
- **topics**: `direction_only`, `direction`, `only`, `signal`, `confirmed`
- **summary**: `parse_fractals_to_3d()`: up_3/dn_3/up_6/dn_6 (поля 17-20) включены в тензор, N_FRACTAL_FEATURES=26 `normalize.py`: per-pair нормализация up/dn (5 пар со своим p85/p99), параметры из фракталов без таргетов
- **artifacts**: `ML/reports/fractal_ablation.json`, `ML/reports/tb_direction_signal.json`, `ML/reports/direction_only_signal.json`
- **decision**: `direction_only_signal.py`, `tb_direction_signal.py`: `json_safe()` — inf/nan -> null для строгого JSON `statistics/data_contract_smoke_check.py` — обязательный входной контроль перед ML-экспериментами (тензор, цена не бинарна, direction ∈ {-1,1}, ATR-признаки не в [0,1], доли классов TB-таргетов)
- **notes**: нет

## [2026-05-29] — Limit-Order Entry Convention: Phase 1–3 (FAIL)
- **report**: `docs/reports/2026-05-29-limit-order-entry.md`
- **topics**: `limit_order`, `transformer`
- **summary**: Skipped rows (bad fractal0, missing time): TB targets теперь получают NO_FILL_SENTINEL вместо stale default 0.5 Mismatch bug: fill_lag=-1 в skipped rows, TB targets оставались на 0.5 вместо -999
- **artifacts**: `processing/purge_split.py`, `processing/label_audit.py`, `processing/label_signals.py`
- **decision**: Phase 3 Transformer FAIL: Mean AUC=0.575, главный target buy_sl2_tp3 AUC=0.498 — fractal features без predictивного сигнала Вердикт: Close-entry сделан исполнимым через лимитные ордера. Transformer на fractal features не работает (консистентно с transformer-direction 2026-05-21).
- **notes**: нет

## [2026-05-27] — Methodology Cycle: Entry Timing Correction (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-05-25-methodology-cycle-stages-00-04.md`
- **topics**: `methodology`, `cycle`, `timing`, `correction`
- **summary**: Методика усилена правилом исполнимой entry price: label/backtest не может входить раньше фактической доступности признаков и runtime-задержек. Для `fractal0` зафиксировано: он полностью готов только на `Close` подтверждающего третьего бара; `Close[row]` entry в текущем live path является `DIAGNOSTIC_ONLY`.
- **artifacts**: `docs/reports/2026-05-25-methodology-cycle-stages-00-04.md`
- **decision**: Результаты с `Close[row]` больше нельзя интерпретировать как live/OOS evidence для MT watcher-контура. Следующий валидный кандидат должен доказать first executable entry после feature readiness.
- **notes**: нет

## [2026-05-25] — Methodology Cycle: Stages 00–02 — Pipeline Foundation (COMPLETED)
- **report**: `docs/reports/2026-05-25-methodology-cycle-stages-00-04.md`
- **topics**: `updn`, `h12`, `live_safe`
- **summary**: Pipeline: 63006 rows (2004–2026) -> sort (0 errors) -> label (3192 signals, 63006 predicts) -> split 44104/9451/9451 Все raw поля классифицированы (live_safe / target_only / future_derived / unknown)
- **artifacts**: `ML/checkpoints/pll_normalizer_v1.pkl`
- **decision**: Фундамент live-safe candidate-source цикла заложен. Данные готовы к baseline-экспериментам.
- **notes**: есть запрет на future-derived признаки

## [2026-05-21] — Transformer Encoder Direction: TB/Reg/Trail таргеты (FAIL)
- **report**: `docs/reports/2026-05-21-transformer-direction.md`
- **topics**: `transformer`, `encoder`, `direction`, `reg`
- **summary**: Raw up/dn баг: fractal.price нормализован (ratio), исправлено на OHLC close Checkpoint загрузка: num_classes=10 не был в model_kwargs
- **artifacts**: `docs/reports/2026-05-21-transformer-direction.md`
- **decision**: TB: 16 комбинаций, лучший BUY PF=1.35 (val), Gate A провален Вердикт: fractal features не несут direction-сигнала. Тупик для direct direction prediction.
- **notes**: нет

## [2026-05-21] — Direct Direction Rebuild (FAIL)
- **report**: `docs/reports/2026-05-18-direct-direction-rebuild.md`
- **topics**: `transformer`, `direct`, `direction`, `rebuild`, `audit`
- **summary**: Phase A validation: PF=1.77, SeqPF=1.99 (83 сделки) — gate passed Phase B (+regime features): PF=1.64, SeqPF=2.22 — regime features не улучшили
- **artifacts**: `docs/reports/2026-05-18-direct-direction-rebuild.md`
- **decision**: Вердикт: fractal-level признаки не несут direction-сигнала. Test BUY win rate 50.5% (случайный). Рекомендация: не деплоить; исследовать Transformer encoder + score gate.
- **notes**: нет

## [2026-05-16] — Wiki: execution-tracks.md decomposition (COMPLETED)
- **report**: `wiki/index.md`
- **topics**: `triple_barrier`, `live_safe`
- **summary**: `search_knowledge("Triple Barrier")` вернёт `execution-tracks-early-research.md` (84 строки) вместо монолита. `search_knowledge("live safe retrain")` вернёт `execution-tracks-live-safe-audit.md` (243 строки).
- **artifacts**: `wiki/research/execution-tracks-overview.md`, `wiki/index.md`, `wiki/.archive/execution-tracks-monolith-deprecated.md`
- **decision**: `search_knowledge("live safe retrain")` вернёт `execution-tracks-live-safe-audit.md` (243 строки). Экономия токенов: агент получает ~200 строк вместо 1450 при поиске по конкретной теме.
- **notes**: источник найден в wiki; канонический `docs/reports` отчёт не найден

## [2026-05-15] — Direct direction improvement experiments E0–E5 (COMPLETED)
- **report**: `docs/reports/2026-05-15-direct-direction-improvement.md`
- **topics**: `entry_path`, `feature_ablation`
- **summary**: E0 Feature Ablation: k=4 (97 features) — лучший вариант. Увеличение k ухудшает PF. up/dn признаки дают маргинальный вклад. E1 Binary Models: RF margin=0.10 — validation winner (PF=1.25, SeqPF=1.30, 1923 trades, BUY/SELL balance=0.37)
- **artifacts**: `docs/reports/2026-05-15-direct-direction-improvement.md`
- **decision**: 3-class SELL/SKIP/BUY нежизнеспособна. Binary BUY/SELL RF с margin rule — лучший результат (Test PF=1.23 > direct bar baseline PF=1.11). SELL направление слабое, требует отдельного решения.
- **notes**: нет

## [2026-05-14] — Entry path candidate-source audit (COMPLETED)
- **report**: `docs/reports/2026-05-14-entry-path-all-rows-ranking.md`
- **topics**: `live_safe`, `entry_path`
- **summary**: Проверены `signal_only` ablation, all-rows ranking, causal surrogate и прямая модель `BUY / SELL / SKIP` без offline `signal != 0` gate. Offline gate сам по себе убыточен, а прямой score+direction выглядит лучшим направлением, но остаётся слабым.
- **artifacts**: `docs/reports/2026-05-14-entry-path-all-rows-ranking.md`, `docs/reports/2026-05-14-entry-path-causal-surrogate.md`, `docs/reports/2026-05-14-entry-path-direct-bar-model.md`
- **decision**: Просто снять `signal != 0` gate нельзя; causal surrogate не провалился, а прямой score+direction выглядит лучшим направлением. Production-ready статус не достигнут: test PF слабый, 2022 год отрицательный, направление среди active-строк почти случайное.
- **notes**: нет

## [2026-05-13] — Live-safe entry_path online watcher (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `live_safe`, `entry_path`, `telemetry`
- **summary**: `API.telemetry_signal_watcher` переведён на production-кандидат `entry_path_v1_live_safe + A @ 7.5%` по умолчанию. Legacy take/skip watcher оставлен отдельным режимом `telemetry_frequency_v1_legacy` и требует unsafe override.
- **artifacts**: `API/telemetry_signal_watcher.py`, `ML/reports/entry_path_v1_live_safe/runtime/telemetry_signal_watcher.log`, `ML/reports/entry_path_v1_live_safe/runtime/runtime_state.json`
- **decision**: M5 diagnostic зафиксирован как threshold override того же checkpoint/rule/feature profile; `--entry-path-diagnostic-all-rows` оставлен только как mechanical stress mode, не parity с production candidate.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-05-12] — Online/tester execution reconciliation (FAIL)
- **report**: `docs/reports/2026-05-12-online-tester-execution-reconciliation.md`
- **topics**: `online`, `tester`, `execution`, `reconciliation`
- **summary**: Проверена M5-цепочка `MT4 -> ML -> MT4` на online/tester срезах: сигналы и направления совпадают, `OPEN_FAILED` фиксируется явно, потерянных сигналов без следа в новом срезе нет.
- **artifacts**: `docs/reports/2026-05-12-online-tester-execution-reconciliation.md`, `docs/ML/online_tester_reconciliation.py.md`
- **decision**: Основной практический риск перед реальным счётом — `requote ERROR-138` при исполнении; follow-up перевёл `OrderSend`/`OrderClose` для ML-сделок на адаптивный slippage с ATR-потолком и 5 попытками.
- **notes**: нет

## [2026-05-05] — Live-safe ML audit and entry_path rebuilds (COMPLETED)
- **report**: `docs/reports/2026-05-05-live-safe-ml-audit.md`
- **topics**: `fav`, `live_safe`, `entry_path`, `quantile`, `mt4_parity`
- **summary**: Проведён live-safe аудит исторически прибыльных контуров: старые `quality`, `frequency`, `original_plus_path`, `entry_path_v1` и `entry_path_v1_quantile` нельзя переносить в online как есть из-за future-derived признаков.
- **artifacts**: `docs/reports/2026-05-05-live-safe-ml-audit.md`, `docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md`, `docs/reports/2026-05-07-entry-path-mt4-parity.md`
- **decision**: Основным production-кандидатом после очистки выбран `entry_path_v1_live_safe + A @ 7.5%`; он прошёл retrain, CPU reproducibility follow-up и MT4 parity. Quantile-слой оставлен research-only из-за нестабильного выбора правила и малого числа сделок.
- **notes**: есть запрет на future-derived признаки

## [2026-04-29] — Online inference contract hardening (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-04-29-online-inference-contract-hardening.md`
- **topics**: `fav`, `live_safe`, `telemetry`
- **summary**: `processing.online_causal_preprocessing` теперь проверяет порядок `fractal*` после сортировки и запускает `normalize_rowwise(verbose=False)`
- **artifacts**: `docs/reports/2026-04-29-online-inference-contract-hardening.md`
- **decision**: Старый watcher можно использовать с `--allow-unsafe-future-features` только для механической диагностики связи MT4 -> Python -> CSV -> MT4.
- **notes**: есть запрет на future-derived признаки

## [2026-04-28] — MQL runtime architecture snapshot (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`
- **topics**: `mql_runtime`, `mql`, `runtime`, `architecture`, `snapshot`
- **summary**: `Nero.csv` локально пересобирается по истории и дописывается при новых уровнях. Full-vs-12000 проверка на хвосте дала `signal_mismatch_rows=0`, максимальное отличие `pred_* <= 3.37e-7`.
- **artifacts**: `docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`
- **decision**: Следующий этап - оставить M5-наблюдение на несколько часов, собрать статистику `MLP_WAIT/NO_SIGNAL/ZERO_SIGNAL/BUY/SELL`, затем решить, нужен ли баланс diagnostic-сигналов. Подробности: `docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`
- **notes**: нет

## [2026-04-27] — Telemetry frequency demo launch (COMPLETED)
- **report**: `docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`
- **topics**: `telemetry`, `frequency`, `demo`, `launch`
- **summary**: MT4 tester proof на `XAUUSD,H1` за 2025: `495` ожидаемых сигналов;
- **artifacts**: `docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`
- **decision**: На дату 2026-04-27 diagnostic-контур считался готовым к online demo launch как механическая цепочка; 2026-04-29 этот вывод уточнён: legacy
- **notes**: нет

## [2026-04-24] — System correlation and portfolio check (COMPLETED)
- **report**: `docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`
- **topics**: `entry_path`, `quantile`, `portfolio`
- **summary**: Построен канонический pairwise benchmark по пяти зрелым `XAUUSD` системам: `quality`
- **artifacts**: `ML/reports/system_correlation_portfolio/xauusd_system_correlation/`, `ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json`
- **decision**: На `XAUUSD` нельзя считать `frequency` и `original_plus_path` двумя независимыми portfolio sleeves. Прагматичный первый portfolio-layer: `quality + entry_path_v1_quantile`; baseline `entry_path_v1` не нужно ставить рядом с quantile-версией как отдельный слой.
- **notes**: нет

## [2026-04-24] — Entry path cross-instrument robustness (FAIL)
- **report**: `docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md`
- **topics**: `entry_path`, `quantile`, `cross_instrument`, `execution_policy`
- **summary**: Для `entry_path_v1` и `entry_path_v1_quantile` введён единый export-contract `time;signal`. `XAUUSD MetaQuotes -> Alpari` проверен отдельно как `provider drift baseline`:
- **artifacts**: `ML/reports/entry_path_cross_instrument_robustness/`, `API/export_entry_path_v1_signals.py`, `API/README.md`
- **decision**: Provider drift на том же `XAUUSD` не является основной проблемой для `entry_path` execution-систем. Перенос baseline `entry_path_v1` узкий; quantile-версия заметно живучее, но тоже не универсальна.
- **notes**: нет

## [2026-04-24] — Cross-instrument robustness check (FAIL)
- **report**: `docs/reports/2026-04-24-cross-instrument-robustness-check.md`
- **topics**: `cross_instrument`, `take_skip_v2`
- **summary**: Этап разделён на `provider_drift_baseline` и `cross_instrument_transfer`, чтобы не смешивать эффект нового провайдера и эффект нового рынка. На `XAUUSD MetaQuotes -> Alpari` все три режима сохранили статус `provider_stable`.
- **artifacts**: `ML/reports/cross_instrument_robustness/`
- **decision**: Drift котировок сам по себе не ломает текущие системы на `XAUUSD`. Реальный перенос на новые инструменты частичный, а не универсальный: `EURUSD` провалился полностью, `USDCHF` прошёл полностью.
- **notes**: нет

## [2026-04-22] — Signal export parity benchmark (COMPLETED)
- **report**: `docs/reports/2026-04-22-signal-export-parity.md`
- **topics**: `cross_instrument`, `signal`, `export`, `parity`, `benchmark`
- **summary**: Добавлен инструмент, который сравнивает exported `ml_signals.csv` с MT4 tester log. Для `original_plus_path_20260420`: `51` ненулевая строка export, `37` уникальных `time+signal`, `29` MT4 opened trades.
- **artifacts**: `docs/reports/2026-04-22-signal-export-parity.md`
- **decision**: Дубли времени в DATA являются ожидаемыми разными пиками одного бара и не должны схлопываться. Runtime-формат `time;signal` грубее DATA: он исполняет сигнал на уровне времени бара.
- **notes**: нет

## [2026-04-20] — take_skip_v2 original contour feature ablation (PASS)
- **report**: `docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md`
- **topics**: `take_skip_v2`, `lib_pic`, `trailing_stop`, `feature_ablation`
- **summary**: Реализован отдельный runner для проверки `lib_PIC` path/geometry признаков в старом single-tensor `take_skip_v2` контуре. Старый baseline не заменяется на `baseline_clean`: новые признаки добавляются поверх исходного engineered-представления.
- **artifacts**: `ML/reports/take_skip_trailing_stop_v2_original_plus_path_selected_rule.json`
- **decision**: `path` признаки дают полезный trade-off: больше сделок, PF остаётся высоким. `geometry` не выбран как practical candidate: высокий PF, но test частота только `4.8` trades/year.
- **notes**: нет

## [2026-04-20] — take_skip_v2 lib_PIC feature training (FAIL)
- **report**: `docs/reports/2026-04-20-take-skip-lib-pic-feature-training.md`
- **topics**: `take_skip_v2`, `lib_pic`, `transformer`
- **summary**: Проверен training track, где модель получает фрактальную последовательность и `lib_PIC` feature profile внутри одной dual-stream модели. Полная сетка: `baseline_clean`, `baseline_clean_path`, `baseline_clean_geometry_path` × `seq_len 20/50/100`.
- **artifacts**: `ML/models/take_skip_dual_stream_transformer.py`
- **decision**: Простое добавление `lib_PIC`-признаков внутрь этой модели не создало рабочий selection layer. `lib_PIC`-признаки пока выглядят полезнее как внешний фильтр, чем как добавка во вход dual-stream модели.
- **notes**: нет

## [2026-04-20] — take_skip_v2 lib_PIC external selection benchmark (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-04-20-take-skip-lib-pic-selection.md`
- **topics**: `take_skip_v2`, `lib_pic`, `trailing_stop`
- **summary**: Проверен внешний слой отбора поверх готовых `take_skip_trailing_stop_v2` exports без нового обучения. Quality-first снова выбрал старый rule без `lib_PIC`-фильтра: test `PF=39.74`, `trades_per_year=8.2`, `negative_year_slices=0`.
- **artifacts**: `docs/reports/2026-04-20-take-skip-lib-pic-selection.md`
- **decision**: `lib_PIC`-фильтр не заменяет текущие `quality` / `frequency` правила. Признак `pic_path_win_proxy24_share_w20` выглядит полезным как диагностический фильтр устойчивости: он режет часть сделок, но убирает отрицательный годовой срез.
- **notes**: нет

## [2026-04-17] — Take/skip trailing-stop matrix verdict (FAIL)
- **report**: `docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md`
- **topics**: `quantile`, `trailing_stop`
- **summary**: Во всех трёх конфигурациях `seq20/50/100`: `verdict = reject` Ни один кандидат не прошёл gate `PF >= 1.0`
- **artifacts**: `docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md`
- **decision**: Ни один кандидат не прошёл gate `PF >= 1.0` Вывод: смена постановки с regression/quantile на бинарный `take/skip` не решила проблему. Модель выдаёт слишком слабый и сжатый скор. Текущий Track A почти исчерпан.
- **notes**: нет

## [2026-04-17] — Multi-horizon take/skip feature track handoff (COMPLETED)
- **report**: `docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md`
- **topics**: `trailing_stop`, `data_loader`, `transformer`
- **summary**: Локальный smoke-run `transformer_seq20`: `verdict = go` Validation winner: `take_48_x4 + top_k_probability 0.05`, `PF=6.39`, 24 сделки, `negative_year_slices=0`
- **artifacts**: `API/generate_signals.py`
- **decision**: Это не итоговый verdict — ждёт полного remote matrix run Подробности: `docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md`
- **notes**: нет

## [2026-04-19] — Clean lib_PIC feature profile diagnostic (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-04-19-lib-pic-feature-source-audit.md`
- **topics**: `entry_path`, `lib_pic`, `transformer`
- **summary**: В `ML/reports/feature_bank_clean_comparison/report.md` зафиксирована read-only диагностика признаков для цели `trail_24_pnl_atr_x8`. Лучший диагностический вариант: `baseline_clean` — 117 признаков, validation R² `0.083736`, MAE `0.238819`, совпадение знака `0.842623`.
- **artifacts**: `ML/reports/feature_bank_clean_comparison/report.md`
- **decision**: Чистка групп `direction`, `price_position`, `path_long`, `path_short` выглядит полезной на диагностике признаков. Follow-up `entry_path_v1` training не подтвердил улучшение: `transformer + baseline_clean seq20` дал validation `ret_pearson_r=0.2920` против старого `0.2921`, но test `ret_pearson_r=0.2269` против старого `0.2681`.
- **notes**: нет

## [2026-04-19] — Execution policy v2: Python benchmark + MT4 confirmation (COMPLETED)
- **report**: `docs/reports/2026-04-19-execution-policy-v2.md`
- **topics**: `execution_policy`, `execution`, `policy`, `python`, `benchmark`
- **summary**: Добавлен benchmark вариантов выхода для готовых `quality` и `frequency` ML-сигналов без нового обучения. В MT4 добавлен `ML_TakeProfitATR`: take profit в ATR от входа, `0=выключен`.
- **artifacts**: `MT/MQL4/Experts/$o$imple.mq4`, `MT/MQL4/Include/lib_ML_Signal.mqh`
- **decision**: Для `frequency` take profit временно снимается: основной выход — чистый trailing. `TrailATR=10` не выбран основным, потому что даёт больше прибыли ценой худшей формы equity и высокой концентрации прибыли.
- **notes**: нет

## [2026-04-18] — MT4 trailing-stop execution for direct ML mode (COMPLETED)
- **report**: `docs/reports/2026-04-18-mt4-trailing-stop-execution.md`
- **topics**: `trailing_stop`, `mt4`, `trailing`, `stop`, `execution`
- **summary**: В прямой MT4-контур `iSignal=3` добавлен новый режим выхода: `ML_ExitMode=0` -> timeout
- **artifacts**: `MT/MQL4/Experts/$o$imple.mq4`, `MT/MQL4/Include/lib_ML_Signal.mqh`, `docs/superpowers/plans/2026-04-18-mt4-trailing-stop-execution.md`
- **decision**: Теперь MT4 может честно проверять не только новый слой входа, но и новый тип выхода, под который строился `take_skip_trailing_stop_v2` Следующий шаг — ручной MT4 прогон `quality` и `frequency` уже в trailing-mode
- **notes**: нет

## [2026-04-18] — Take/skip v2 rule consumer (COMPLETED)
- **report**: `docs/reports/2026-04-18-take-skip-rule-consumer.md`
- **topics**: `trailing_stop`, `take`, `skip`, `rule`, `consumer`
- **summary**: Добавлен единый CLI для применения frozen `take_skip_trailing_stop_v2` rules к готовому prediction CSV Поддержаны оба зафиксированных режима:
- **artifacts**: `API/export_take_skip_trailing_stop_v2_signals.py`, `API/README.md`
- **decision**: `take_skip_trailing_stop_v2_*_selected_rule.json` теперь стали не только отчётными артефактами, но и рабочим интерфейсом применения Следующий шаг уже операционный: сравнивать `quality` и `frequency` режимы на одном и том же prediction CSV без ручного разбора rule JSON
- **notes**: нет

## [2026-04-18] — Take/skip frequency follow-up (COMPLETED)
- **report**: `docs/reports/2026-04-18-take-skip-frequency-followup.md`
- **topics**: `take_skip_v2`, `trailing_stop`
- **summary**: На базе уже обученного `seq50` без нового training-cycle выполнен follow-up benchmark quality-first winner сохранился:
- **artifacts**: `ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json`, `ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json`, `processing/label_signals.py`
- **decision**: Частоту сделок удалось резко поднять без падения ниже `PF > 1` raw `frequency-first` показал полезную область, но не стал финальным winner-ом
- **notes**: нет

## [2026-04-17] — Trailing-stop target quantile first wave (FAIL)
- **report**: `docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md`
- **topics**: `quantile`, `trailing_stop`, `data_loader`, `transformer`
- **summary**: bounded run: `transformer_seq20_x3_quantile`, `trail_48_pnl_atr_x3`, `q10/q50/q90` best val `q50_pearson_r=0.0389`, test `q50_pearson_r=0.0541`
- **artifacts**: `API/generate_signals.py`, `ML/models/trailing_stop_target_quantile_transformer.py`
- **decision**: quantile-постановка не улучшила обычную regression-постановку на том же target-е (`0.1750` против `0.4206` best validation PF) дальнейшее расширение этой же family на `seq_len=50/100` без новой идеи не выглядит рациональным
- **notes**: нет

## [2026-04-16] — Trailing-stop target first wave verdict (COMPLETED)
- **report**: `docs/reports/2026-04-16-trailing-stop-target-first-wave.md`
- **topics**: `trailing_stop`, `transformer`
- **summary**: Первый bounded run нового target-а завершён для `transformer_seq20/50/100` Лучший validation candidate всего этапа: `transformer_seq20 + trail_48_pnl_atr_x3`, `PF=0.4206`
- **artifacts**: `API/generate_signals.py`, `processing/label_main.py`, `processing/label_signals.py`
- **decision**: Новый trailing-stop target в текущем виде не вытягивает вход: даже лучший candidate далеко ниже `PF > 1` Увеличение длины истории до `50 / 100` не помогло
- **notes**: нет

## [2026-04-15] — Track A max-out verdict (COMPLETED)
- **report**: `docs/reports/2026-04-15-track-a-max-out.md`
- **topics**: `entry_path`, `transformer`
- **summary**: Short sweep `6 configs x 3 epochs` и deeper rerun лучших `transformer_seq20/seq50` (`10 epochs`) завершены Лучший validation candidate всего этапа: `transformer_seq50 + ret24_over_adv24`, `PF=0.4784297662870411`
- **artifacts**: `ML/models/entry_path_dual_stream_transformer.py`
- **decision**: Track A заметно улучшен, но не достиг даже мягкого success gate `PF > 1` на validation Следующий шаг должен менять само обучение или постановку задачи, а не повторять ещё один похожий benchmark-only цикл
- **notes**: нет

## [2026-04-13] — Quantile forward validation scaffold (PASS)
- **report**: `docs/reports/2026-04-13-quantile-forward-validation.md`
- **topics**: `entry_path`, `quantile`
- **summary**: Инструмент готов: CLI пишет `summary.json`, `time_slices.csv`, `run_metadata.json` Нового strictly-forward prediction CSV в репозитории нет; доступны только historical validation/test prediction-файлы
- **artifacts**: `ML/reports/quantile_forward_validation/`
- **decision**: `quantile` не подтверждён и не опровергнут на новых данных: нужна новая forward-выборка после production decision Старый frozen test не использован повторно, чтобы не подменять forward validation уже известным окном
- **notes**: нет

## [2026-04-13] — PF uplift discovery beyond ML layer: SHORTLISTED (FAIL)
- **report**: `docs/reports/2026-04-13-pf-uplift-discovery.md`
- **topics**: `entry_path`, `quantile`
- **summary**: Baseline: `entry_path_v1_quantile` test set N=48, PF=8.179, WR=81.25%, negative_year_slices=0 20 гипотез по 5 категориям проверены, 6 cheap read-only probes на `trade_enriched.csv`, path-dep check через OHLC simulation
- **artifacts**: `docs/reports/2026-04-13-pf-uplift-discovery.md`
- **decision**: Три ортогональных механизма (session / hold duration / predicted adverse) дают значимый PF uplift без переобучения. Skeleton plans созданы. Следующий шаг: `/writing-plans` для любой из трёх. Подробности: `docs/reports/2026-04-13-pf-uplift-discovery.md`
- **notes**: нет

## [2026-04-13] — Composition track verdict (FAIL)
- **report**: `docs/reports/2026-04-13-fav-3-vs-12-standalone.md`
- **topics**: `fav`, `quantile`
- **summary**: `quantile_only` воспроизведён exactly: validation `N=32, PF=11.240091883688192`; test `N=48, PF=8.178675196069868` после пересборки правильного источника `pred_fav_3/pred_fav_12` на тех же активных строках composition стал честно измерим: test `N=47`, `PF=7.860844837655267`, `n_boost_composition.verdict = gate_fail`
- **artifacts**: `docs/reports/2026-04-13-fav-3-vs-12-standalone.md`
- **decision**: Направление composition закрыто: дополнительный фильтр почти ничего не добавляет к `quantile`, но ломает yearly stability, поэтому усложнение не оправдано
- **notes**: нет

## [2026-04-13] — Fav 3 vs 12 standalone verdict (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-04-13-fav-3-vs-12-standalone.md`
- **topics**: `fav`, `quantile`
- **summary**: самостоятельная проверка `fav_3_vs_12 <= threshold` на active universe не нашла ни одного рабочего порога: на validation лучший порог с `N>=30` дал только `PF=0.1378609915504136` (`threshold=0.22`, `N=36`) на test лучшая диагностическая точка с `N>=30` тоже слабая: `PF=0.3129480021818097` (`threshold=0.24`, `N=164`)
- **artifacts**: `docs/reports/2026-04-13-fav-3-vs-12-standalone.md`
- **decision**: Направление `fav_3_vs_12` как самостоятельной второй торговой системы закрыто: без `quantile` и без другого базового отбора признак не даёт рабочего standalone-режима
- **notes**: нет

## [2026-04-13] — Label convention audit: timeout больше не штрафуется как SL в TB analytics (COMPLETED)
- **report**: `docs/reports/2026-04-13-label-convention-audit.md`
- **topics**: `triple_barrier`, `label_convention`, `threshold_analysis`
- **summary**: `ML/reports/label_convention_audit_inventory.csv`: inventory всех релевантных TB label handling patterns с risk-категориями `R1..R8` `ML/reports/label_convention_audit.md`: полный audit report
- **artifacts**: `ML/reports/label_convention_audit.md`, `processing/label_signals.py`
- **decision**: Аудит подтвердил ещё два реальных `R2 not_win_is_loss` бага после уже известного фикса MT4 simulator. Source-of-truth в `processing/label_signals.py` не менялся, frozen `tb_selected_rule.json` не ретюнился. Подробности: `docs/reports/2026-04-13-label-convention-audit.md` Дополнительный frozen rerun на canonical `ml_signals_tb.csv` + `Nero_{validation,test}_labeled.csv` подтвердил, что historical verdict от `2026-04-12` не меняется: validation/test summary совпали exactly.
- **notes**: нет

## [2026-04-12] — Triple Barrier verdict: не production (gate_fail)
- **report**: `docs/reports/2026-04-12-tb-verdict.md`
- **topics**: `triple_barrier`, `quantile`
- **summary**: После фикса прогон на `tb_selected_rule.json` (`theta=0.475`, `min_ev=0.1`): Validation (2019–2022): 28 trades, PF=4.33, win_rate=57.1%, все годы положительные
- **artifacts**: `processing/label_signals.py`
- **decision**: TB-слой не подключается к MT4 как production или parallel execution mode — gate_fail на test, явный regime shift между validation и test. Production-опора остаётся `regression_updn` baseline + `entry_path_v1_quantile` parallel. `tb_selected_rule.json` зафиксирован как frozen исторический артефакт; пересмотр возможен только после накопления forward-данных post-2026-06. Подробности: `docs/reports/2026-04-12-tb-verdict.md`
- **notes**: нет

## [2026-04-12] — Entry Path v1 Quantile: production-ready через n-boost gate (PASS)
- **report**: `docs/reports/2026-04-12-quantile-status-decision.md`
- **topics**: `entry_path`, `quantile`
- **summary**: Gate PASS на frozen test (seed 007, production параметры median): `n_trades=48`, `pf=8.18`, `win_rate=0.8125`
- **artifacts**: `ML/reports/n_boost_result.json`, `ML/reports/entry_path_v1_quantile_selected_rule.json`, `API/export_entry_path_v1_quantile_signals.py`
- **decision**: `entry_path_v1_quantile` подтверждён как production-ready parallel execution mode для MT4. Winner `lb_gt_m_q35` стабилен по 5 сидам (все выбирают `lb_gt_m` с q∈{30,35,40}). Production rule зафиксирован в `entry_path_v1_quantile_selected_rule.json` через median параметры. Старый plan `2026-04-11-entry-path-v1-quantile-production-path.md` superseded. Подробности: `docs/reports/2026-04-12-quantile-status-decision.md`
- **notes**: нет

## [2026-04-11] — Entry Path v1 Quantile: MT4 parity подтверждён (PASS)
- **report**: `wiki/research/execution-tracks-reproducibility-plus-parity.md`
- **topics**: `entry_path`, `quantile`, `mt4_parity`
- **summary**: после исправления exporter-а канонический `ml_signals.csv` для quantile-layer содержит `8872` строк и `8` активных сигналов (`4 BUY`, `4 SELL`) MT4 tester по `20260411.log` показал:
- **artifacts**: `ML/reports/entry_path_v1_quantile_filter_report.md`, `ML/reports/entry_path_v1_quantile_filter_selected_rule.json`, `wiki/research/execution-tracks-reproducibility-plus-parity.md`
- **decision**: `entry_path_v1_quantile` теперь подтверждён и по multi-seed robustness, и в реальном MT4-контуре. Следующий практический вопрос уже не в новом поиске, а в решении, становится ли quantile-layer основным execution mode. Синтез: `wiki/research/execution-tracks-overview.md`
- **notes**: источник найден в wiki/ML/reports; канонический `docs/reports` отчёт не найден

## [2026-04-11] — Entry Path v1 Quantile: multi-seed robustness pass подтверждён (PASS)
- **report**: `wiki/research/execution-tracks-reproducibility-plus-parity.md`
- **topics**: `triple_barrier`, `entry_path`, `quantile`
- **summary**: Полный 5-seed pass (`7, 17, 42, 77, 123`) дал: `same_rule_count = 5`
- **artifacts**: `ML/reports/entry_path_v1_quantile_filter_report.md`, `ML/reports/entry_path_v1_quantile_selected_rule.json`, `ML/reports/entry_path_v1_quantile_live_safe_baseline/multi_seed_summary.json`
- **decision**: `entry_path_v1_quantile` вышел из статуса single-run гипотезы и прошёл multi-seed robustness-pass. Следующий главный шаг теперь не новый поиск, а `MT4 parity-check` для quantile-layer. Синтез: `wiki/research/execution-tracks-overview.md`
- **notes**: источник найден в wiki/ML/reports; канонический `docs/reports` отчёт не найден

## [2026-04-10] — Entry Path v1 Quantile: гибридный трек прошёл success gate (COMPLETED)
- **report**: `docs/reports/2026-04-10-entry-path-v1-quantile.md`
- **topics**: `entry_path`, `quantile`
- **summary**: Validation (`entry_path_v1_quantile`): `ret_pearson_r=0.1981`, `interval_coverage=0.8013`, `median_interval_width=7.1442` Test: `ret_pearson_r=0.1455`, `interval_coverage=0.7562`, `median_interval_width=7.0826`
- **artifacts**: `docs/reports/2026-04-10-entry-path-v1-quantile.md`
- **decision**: `entry_path_v1_quantile` в текущем run проходит success gate и даёт рабочий confidence-layer поверх `A @ 7.5%`. Подробности: `docs/reports/2026-04-10-entry-path-v1-quantile.md`
- **notes**: нет

## [2026-04-09] — MT4-сверка: замороженный победитель подтверждён одним финальным прогоном (PASS)
- **report**: `docs/reports/2026-04-09-mt4-parity-check-winner.md`
- **topics**: `mt4`
- **summary**: Финальный MT4-прогон по уже отфильтрованному `ml_signals.csv` дал: `8872` строк в CSV, `22` активных сигнала
- **artifacts**: `MT/MQL4/Include/MAIN.mqh`, `MT/MQL4/Include/lib_ML_Signal.mqh`
- **decision**: Финальный победитель подтверждён в MT4 по одному честному прогону на `test`. Теперь главный технический долг не в новом выборе победителя, а в переносе скрипта выпуска CSV и слоя отбора из черновой ветки в основной контур. Подробности: `docs/reports/2026-04-09-mt4-parity-check-winner.md`
- **notes**: нет

## [2026-04-09] — Entry Path v1: добавлен слой отбора сделок и выбран рабочий базовый вариант (COMPLETED)
- **report**: `docs/reports/2026-04-09-entry-path-trade-filter.md`
- **topics**: `entry_path`, `transformer`
- **summary**: После доработки модели: validation: `ret_pearson_r=0.2758`, `path_reg_pearson_r=0.2987`, `path_cls_f1_macro=0.4074`
- **artifacts**: `ML/models/entry_path_transformer.py`
- **decision**: Слой `торговать / не торговать` для `entry_path_v1` теперь есть и уже даёт рабочий базовый вариант. Текущий лучший практический вариант — простой фильтр `A` в зоне `7.5%`. Следующий шаг — строить conformal-слой поверх этого базового варианта, а `B` пока держать как вторую исследовательскую ветку. Подробности: `docs/reports/2026-04-09-entry-path-trade-filter.md`
- **notes**: нет

## [2026-04-09] — Entry Path v1: проверено перевзвешивание функции потерь, выбран рабочий базовый вариант (COMPLETED)
- **report**: `docs/reports/2026-04-09-entry-path-v1-loss-weighting.md`
- **topics**: `entry_path`, `data_loader`
- **summary**: Проверены три режима: только активные строки: провал (`test ret_pearson_r=0.0112`)
- **artifacts**: `docs/reports/2026-04-09-entry-path-v1-loss-weighting.md`
- **decision**: Лучший рабочий вариант для `entry_path_v1` сейчас — перевзвешивание активных строк с весом `5.0` сразу в `ret_*` и `path_6_class`. Следующий шаг уже не в новом подборе весов, а в слое `торговать / не торговать` поверх этого базового варианта. Подробности: `docs/reports/2026-04-09-entry-path-v1-loss-weighting.md`
- **notes**: нет

## [2026-04-08] — Entry Path v1: baseline очищен от старого кэша, результаты пересчитаны (COMPLETED)
- **report**: `docs/reports/2026-04-08-entry-path-v1-baseline.md`
- **topics**: `fav`, `entry_path`, `transformer`
- **summary**: Старые числа `best_ret_pearson_r=0.5253` и `test ret_pearson_r=-0.0216` оказались неактуальны: они были получены на старом cache После чистого retrain новый baseline стал таким:
- **artifacts**: `docs/reports/2026-04-08-entry-path-v1-baseline.md`
- **decision**: Теперь baseline выглядит честно: `ret_*` не сломан, а просто заметно слабее старого ложного результата. `entry_path_v1` можно сохранять как рабочий исследовательский трек. Следующий шаг уже уже не в поиске “почему test упал”, а в том, как учить этот трек на реальных сделках при том, что активных строк всего около `5%`. Подробный отчёт: `docs/reports/2026-04-08-entry-path-v1-baseline.md`
- **notes**: нет

## [2026-04-08] — Outcome-aligned retraining: validation-first verdict = no winner (COMPLETED)
- **report**: `docs/reports/2026-04-08-outcome-aligned-retraining.md`
- **topics**: `h12`, `data_loader`
- **summary**: После signal-only retraining на `2208` train / `473` validation signal rows: `trade_outcome_cls`: best val `AUC=0.6534`
- **artifacts**: `processing/label_main.py`, `processing/label_signals.py`
- **decision**: Validation-first protocol отработал правильно: outcome-aligned track в текущем виде не дал ни одного target family, который можно честно переносить на `test`. Это не “лучший из плохих”, а явный сигнал пересмотреть саму label definition ближе к реальному execution loop MT4. Подробности: `docs/reports/2026-04-08-outcome-aligned-retraining.md`
- **notes**: нет

## [2026-04-08] — Triple Barrier: найдена причина старого расхождения Python ↔ MT4 (COMPLETED)
- **report**: `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md`
- **topics**: `triple_barrier`, `triple`, `barrier`, `python`, `mt4`
- **summary**: Старый отрицательный вывод по MT4 оказался ложным: главная причина была в сдвиге времени в TB-разметке После полной пересборки зафиксированное правило стало таким: `theta=0.475`, `min_ev=0.10`, validation `PF=1.53`, test `PF=1.11`
- **artifacts**: `MT/MQL4/Include/OUTPUT.mqh`, `processing/label_signals.py`, `statistics/signal_tracer.py`
- **decision**: Triple Barrier больше нельзя считать треком, который “ломается” при переносе в MT4. Главная старая ошибка найдена и исправлена. Теперь следующий шаг не в новых порогах, а в оценке вне MT4, которая повторяет правила торговли MT4 один в один. Подробный отчёт: `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md`
- **notes**: нет

## [2026-04-08] — Triple Barrier: усиление схемы и исправленная база вне MT4 (COMPLETED)
- **report**: `docs/reports/2026-04-08-triple-barrier-hardening.md`
- **topics**: `triple_barrier`, `threshold_analysis`
- **summary**: Validation зафиксированное правило: `theta=0.475`, `min_ev=0.10`, `N=121`, `wins=70`, `losses=51`, `timeouts=14`, `PF=1.53`
- **artifacts**: `ML/reports/tb_selected_rule.json`, `ML/reports/tb_validation_logits.npy`, `ML/reports/tb_validation_targets.npy`
- **decision**: Это усиление было нужно и полезно, но старые слишком сильные TB-цифры больше не актуальны: после исправления времени старта сделки база вне MT4 стала заметно слабее, зато честнее. Теперь смысл TB определяется не “бумажным PF”, а тем, что после новой проверки в MT4 он больше не расходится с торговой системой по самой сути сделки. Подробный отчёт: `docs/reports/2026-04-08-triple-barrier-hardening.md`
- **notes**: нет

## [2026-04-08] — Validation-first ML Exit Research: frozen winner = timeout-only (COMPLETED)
- **report**: `docs/reports/2026-04-08-ml-exit-validation-first.md`
- **topics**: `validation`, `first`, `exit`, `research`, `frozen`
- **summary**: Validation grid-search по exit-policy library (`reverse`, `weak_edge`, `profit_guard`, layered) не обогнал baseline: `timeout_only`: `PF=1.17`, `N=567`, `win_rate=50.97%`, `avg_hold_bars=12.0`
- **artifacts**: `ML/reports/frozen_exit_policy.json`, `MT/MQL4/Include/OUTPUT.mqh`, `API/exit_policy_research.py`
- **decision**: Validation-first protocol отработал как intended: ни одно новое ML-exit правило не прошло честную проверку против уже существующего `ML_Timeout(12H)` baseline. Поэтому новый exit rule в MQL4 не переносился; замороженной политикой остаётся `timeout_only`, уже реализованный в `MT/MQL4/Include/OUTPUT.mqh`. Подробный отчёт: `docs/reports/2026-04-08-ml-exit-validation-first.md`
- **notes**: нет

## [2026-04-04] — Archetype × Filter Bridge: fav_3_vs_12 обогащает winning архетип, pullback не нужен (FAIL)
- **report**: `docs/reports/2026-04-04-archetype-filter-bridge.md`
- **topics**: `fav`, `archetype_filter`
- **summary**: `fav_3_vs_12 <= 0.653` повышает долю winning архетипа на holdout: 44.0% vs 37.4% baseline (+6.6 pp) `ratio_3_vs_12 > 4.751` НЕ обогащает winning архетип: 33.5% на holdout (хуже baseline)
- **artifacts**: `docs/reports/2026-04-04-archetype-filter-bridge.md`
- **decision**: `fav_3_vs_12 <= 0.653` — единственный фильтр, коррелирующий с winning архетипом. С ним market entry достаточен (PF=1.78). Pullback поверх фильтра теряет winning сигналы (они не откатываются). `ratio_3_vs_12 > 4.751` работает только через pullback + mechanical price improvement, не через archetype selection. Оба фильтра ортогональны. Подробный отчёт: `docs/reports/2026-04-04-archetype-filter-bridge.md`
- **notes**: нет

## [2026-04-04] — Signal Path Atlas Readout: двумодальная структура сигнала, edge = selection, не timing (FAIL)
- **report**: `docs/reports/2026-04-04-signal-path-atlas-readout.md`
- **topics**: `signal_path_atlas`, `signal`, `atlas`, `readout`, `edge`
- **summary**: Первый канонический atlas readout на 1752 discovery + 851 holdout signals Глобальный сигнал direction-neutral: медиана signed_ret_12 = -0.064 ATR, first-passage и ordering практически симметричны
- **artifacts**: `docs/reports/2026-04-04-signal-path-atlas-readout.md`
- **decision**: Atlas переформулирует задачу: проблема edge — в отборе 36% winning signals (flat_or_noisy_drift), а не в оптимизации entry timing на population из 64% failures. Pullback «работает» через mechanical price improvement + selection filtering, а не через direction-level dip-then-rally pattern. Locked Variant 3 winner ослаблен (оба pillar — ratio 4-5 и ATR Q4 — weakly supported). Следующий шаг — проверить, предсказывают ли quality filters принадлежность к winning архетипу. Подробный отчёт: `docs/reports/2026-04-04-signal-path-atlas-readout.md`
- **notes**: нет

## [2026-04-04] — Signal Quality Filter Research (Variant 4): multi-horizon quality filters × pullback entry (PASS)
- **report**: `docs/reports/2026-04-04-signal-quality-filter.md`
- **topics**: `fav`, `signal`, `quality`, `filter`, `research`
- **summary**: Score-based подход (additive score из нескольких features) не работает — holdout не подтверждает (7/8 NOT CONFIRMED) Индивидуальные правила работают: 7/10 top rules подтверждены на holdout
- **artifacts**: `API/signal_quality_research.py`
- **decision**: Multi-horizon predictions дают лучшую фильтрацию, чем ratio_12 alone, но через индивидуальные правила, а не additive scores. Pullback entry без фильтра — generic "better price" effect; quality filter добавляет cohort-specific uplift поверх. Следующий шаг — верификация кандидатов через Signal Path Atlas pipeline. Подробный отчёт: `docs/reports/2026-04-04-signal-quality-filter.md`
- **notes**: нет

## [2026-04-03] — Signal Path Atlas: standalone research CLI, frozen holdout replication и stage close (PASS)
- **report**: `docs/reports/2026-04-03-signal-path-atlas.md`
- **topics**: `quantile`, `signal_path_atlas`
- **summary**: Новый atlas CLI успешно проходит верификацию: `pytest tests/test_signal_path_atlas.py -q` -> `38 passed`
- **artifacts**: `API/signal_path_atlas.py`, `API/README.md`
- **decision**: Stage B research сместился с narrow winner-specific PF follow-up к reusable path-atlas workflow. Следующий шаг — читать atlas outputs как канонический research artefact и уже из replicated path claims решать, оправдан ли будущий `market`, `pullback`, оба или ни один. Подробный отчёт: `docs/reports/2026-04-03-signal-path-atlas.md`
- **notes**: нет

## [2026-04-02] — signal_research Variant 3 robustness pass: support ladder и stricter shortlist (PASS)
- **report**: `docs/reports/2026-04-02-signal-research-variant-3.md`
- **topics**: `signal_research`, `signal`, `research`, `variant`, `robustness`
- **summary**: Low-fill artefacts удалены из shortlist: `cancel-window entry_close-3ATR@1b` / `@3b` больше не становятся “победителями”, а `ratio 4-5 × ATR Q4 + pullback pic_price-1ATR` понижен до exploratory/standard-only варианта После фильтра robust survivors для primary cohorts: `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR` (`PF=3.69`, `36` fill-ов, `35.6%`), `ratio 4-5 + pullback entry_close-3ATR` (`PF=3.55`), `BUY + pullback entry_close-3ATR` (`PF=2.35`), `ATR Q4 + pullback entry_close-3ATR` (`PF=2.57`)
- **artifacts**: `API/signal_research.py`
- **decision**: Robustness pass оставил один действительно интересный кандидат для будущего EA-прототипа: `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`. Более глубокий `entry_close-3ATR` остаётся сильным research-эффектом на primary cohorts, но уже не выглядит чисто cohort-specific, потому что заметно улучшает и controls. Подробный отчёт: `docs/reports/2026-04-02-signal-research-variant-3.md`
- **notes**: нет

## [2026-04-02] — signal_research Variant 3: scenario matrix, raw pic_price и OHLC validation (COMPLETED)
- **report**: `docs/reports/2026-04-02-signal-research-variant-3.md`
- **topics**: `signal_research`, `signal`, `research`, `variant`, `scenario`
- **summary**: OOS CLI run (`2022-07-18 11:00:00` — `2026-03-20 06:00:00`) дал `2603` реальных сигналов с excursion-данными и полную Variant 3 matrix на shortlist/controls OOS `pic_price` validation: `9403/9403` test-slice rows matched expected OHLC `High/Low` side within tolerance
- **artifacts**: `API/signal_research.py`, `MT/MQL4/Files/Nero.csv`
- **decision**: Variant 3 tooling и каноническая execution matrix готовы, но финальный winner ещё не зафиксирован: текущий auto-verdict слишком чувствителен к low-fill сценариям, а uplift частично переносится и на negative controls. Следующий шаг — ужесточить robustness-фильтр и только потом выбирать кандидатов для EA. Подробный отчёт: `docs/reports/2026-04-02-signal-research-variant-3.md`
- **notes**: нет

## [2026-04-02] — signal_research Variant 3 prep: canonical ATR, cohort map и shortlist для Variant 3 (COMPLETED)
- **report**: `docs/reports/2026-04-02-signal-research-variant-3-prep.md`
- **topics**: `signal_research`, `signal`, `research`, `variant`, `prep`
- **summary**: OOS `2022-07-18 11:00:00` — `2026-03-20 06:00:00`: `2603` реальных сигналов с excursion-данными Лучший кандидат для Variant 3: `ratio 4-5 × ATR Q4` (`N=101`, `PF_12=2.62`, `Net_12 mean=22.2`, `AvgPnL_baseline=1.4`)
- **artifacts**: `API/signal_research.py`, `MT/MQL4/Scripts/ExportOHLC.mq4`
- **decision**: Этап подтвердил, что Variant 3 нужно запускать не по всей выборке, а по shortlist когорт. При этом ATR-нормализация убрала иллюзию “очевидного pullback edge” у Q4, поэтому главный приоритет теперь — прямое сравнение `market / pullback / delayed / cancel-window` на `ratio 4-5 × ATR Q4`, `ratio 4-5`, `BUY`, `ATR Q4`, с `ratio 3-4` и `non-Q4` как отрицательными контролями. Подробный отчёт: `docs/reports/2026-04-02-signal-research-variant-3-prep.md`
- **notes**: нет

## [2026-04-01] — signal_research Variant 2: path-dependent профили сигнала и торговые выводы (PASS)
- **report**: `docs/reports/2026-04-01-signal-research-variant-2.md`
- **topics**: `signal_research`, `signal`, `research`, `variant`, `dependent`
- **summary**: OOS `2022-07-18` — `2026-03-20`: `2603` реальных сигналов с excursion-данными Ранний откат после входа существенный: `adv_1=5.6`, `adv_3=8.8`, `adv_6=12.2` пункта по всей выборке
- **artifacts**: `API/signal_research.py`
- **decision**: Исследование подтвердило, что сигнал даёт не сильный импульс, а слабый статистический дрейф, который легко теряется неудачной механикой входа. Для Variant 3 нужно тестировать не только `SL/TP`, но и сам способ входа: `market`, вход на откате, задержанный вход и окна отмены сигнала. Подробный отчёт: `docs/reports/2026-04-01-signal-research-variant-2.md`
- **notes**: нет

## [2026-04-01] — 10-target модель, новый CSV формат, исследование фильтров (COMPLETED)
- **report**: `docs/reports/2026-04-01-signal-research-variant-2.md`
- **topics**: `signal_research`, `target`, `csv`
- **summary**: MT4 PF=1.18 (идентично 6-target — сигнал по-прежнему на up_12/dn_12) Filter3/Filter6 как ratio-threshold бесполезны: 96% сигналов имеют ratio_3 > 5.0
- **artifacts**: `API/signal_research.py`
- **decision**: Короткие горизонты (up_3 r=0.80, up_6 r=0.67) предсказываются отлично, но как фильтр направления не работают — модель всегда согласна по направлению на всех горизонтах. Нужен другой подход: амплитудный фильтр, исключение убыточного ratio-бакета 3-4, или оптимизация SL/TP.
- **notes**: нет

## [2026-03-31] — Bugfix: ATR-индекс сдвинулся при добавлении полей B.1 — PF восстановлен 1.24 (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `data_loader`, `bugfix`, `atr`
- **summary**: Старый чекпоинт (из `cfeacfc`) на исправленном пайплайне: PF=1.24 ✓ (baseline воспроизведён) BUY=8460, SELL=7962 — баланс сигналов восстановлен (~1:1)
- **artifacts**: `processing/normalize.py`, `ML/data_loader.py`, `ML/reports/evaluate_test_H12.md`
- **decision**: Добавление полей up_3/dn_3/up_6/dn_6 в формат фрактала (Phase B.1) сдвинуло `fractal_atr` с индекса 17 на 21. Python-код не был обновлён синхронно -> единственный символ `==` убил все результаты. Гипотезы о нормализации и capacity dilution были ложными. После исправления свежеобученная модель (pearson_r=0.437): PF=1.18, 584 сделки, просадка 12.66% — лучше старого чекпоинта по числу сделок и прибыли. Добавлены три уровня валидации в `data_loader.py` для предотвращения повторных рассинхронов формата.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-31] — Phase B.1: Добавлены 3H/6H таргеты — pearson_r вырос, PF упал (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `updn`, `pearson`
- **summary**: pearson_r: 0.433 -> 0.565 (+30%) — значительное улучшение качества модели PF: 1.20 -> 0.87 — результат в тестере хуже baseline
- **artifacts**: `processing/label_signals.py`, `processing/normalize.py`, `ML/reports/architecture_comparison_regression_updn.md`
- **decision**: Добавление 3H/6H таргетов без раздельной нормализации не работает. Возможные направления: (1) нормализовать up_3/dn_3/up_6/dn_6 отдельным пулом от up_12..dn_48; (2) использовать 3H/6H только как фичи, не как таргеты; (3) откатить B.1 и пробовать другой подход.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-31] — Phase B.4: Directional Asymmetric Loss — эксперимент провален (FAIL)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `updn`, `regression_updn`, `asymmetric_loss`, `transformer`
- **summary**: Directional α=2.5: PF=1.04, 352 сделки (baseline: PF=1.20, 366 сделок) Directional α=5.0: PF=0.97, 533 сделки (убыточно)
- **artifacts**: `ML/losses.py`, `ML/train.py`, `ML/reports/optuna_study_bilstm_regression_20260316_102024.json`
- **decision**: Directional asymmetric loss не работает. Снижение r с 0.56 до 0.43 не компенсируется консервативностью на adverse direction — модель теряет предсказательную силу сильнее, чем выигрывает от асимметрии. Production модель восстановлена (`git checkout ML/checkpoints/transformer_updn_best.pt`). Не повторять: directional asymmetric loss на regression_updn с текущими фичами не даёт прироста PF.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-27] — Phase A EA Optimization: финал PF=1.23, лучшая конфигурация найдена (PASS)
- **report**: `docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md`
- **topics**: `optimization`
- **summary**: PF: 0.53 -> 1.23 — лучший конфиг: ML_MaxRatio=4.5, ML_RR_Mode=1, ML_ExitEnabled=1, ExitThreshold=2.0 ML_Exit OFF + T1=7 (21 баров): PF=1.20 — хуже: avg loss растёт ($85->$95) сильнее avg win ($108->$114)
- **artifacts**: `docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md`, `statistics/signal_tracer.py`, `ML/reports/evaluate_test_H12.md`
- **decision**: Phase A потолок достигнут — дальнейший рост требует переобучения модели Phase B план: `docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md`
- **notes**: источник найден в docs/superpowers/plans; канонический `docs/reports` отчёт не найден

## [2026-03-26] — ME-13 Diagnostics: анализ 922 сделок MT4 Strategy Tester (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `mt4`, `strategy`, `tester`
- **summary**: PF(SL/TP) = 0.53 при текущих параметрах (922 сделки, WR=37.3%). 51% сделок закрываются по MARKET-таймауту, не достигая ни SL, ни TP Ratio > 4.5 — убыточная зона: TP = 8 ATR недостижим, PF падает до 0.08–0.40. Прибыльный диапазон — ratio [3.5, 4.5) с PF=1.05–1.13
- **artifacts**: `docs/archive/answer.md`, `statistics/signal_tracer.py`
- **decision**: Полный отчёт: `docs/archive/signal_tracer/trade_analysis_20260324.md` (архивный файл отсутствует в текущем дереве)
- **notes**: исторический архивный источник `docs/archive/signal_tracer/trade_analysis_20260324.md` отсутствует; найден общий архивный источник `docs/archive/answer.md`; канонический `docs/reports` отчёт не найден

## [2026-03-25] — ME-13 Diagnostics: per-row updn_params + точная денормализация ground truth (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `updn`, `per`, `row`, `params`
- **summary**: Классификация TP_CLEAR/SL_CLEAR/BOTH_HIT/TIMEOUT: ранее up_12/dn_12 брались из fractal[0] (всегда 0) -> все сделки падали в TIMEOUT. Теперь правильно денормализуются из строки labeled CSV.
- **artifacts**: `processing/normalize.py`, `statistics/signal_tracer.py`
- **decision**: Инструмент `signal_tracer.py` теперь способен выдавать реальные категории расхождения Python/MT4: какой % сделок — BOTH_HIT (MFE/MAE иллюзия), какой — SL_CLEAR (реальные убытки)
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-24] — ME-13 Diagnostics: signal_tracer.py v2.0 (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `signal`, `tracer`, `trade`, `level`, `reconciliation`
- **summary**: Погрешность формулы: `SL Δ = −3.91`, `TP Δ = −7.40` (причина: fractal_atr < ATR на баре входа).
- **artifacts**: `statistics/signal_tracer.py`
- **decision**: 1. MFE/MAE иллюзия подтверждена: 33 сделки — Python видел TP достижимым, MT4 выбило SL первым. 2. SL от пола (Min_SL_ATR): `pred_dn * ScaleK * ATR` ≪ `ATR * 2.0` — модель предсказывает dn близко к нулю при высоком ratio, но реальный ход вниз превышает SL.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-23] — Triple Barrier Classification (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `updn`, `regression_updn`, `triple_barrier`, `threshold_analysis`
- **summary**: Transfer learning: Энкодер из regression_updn checkpoint обязателен — обучение с нуля даёт AUC=0.5000 (коллапс энкодера при BCE+pos_weight=n_neg/n_pos создаёт нейтральную точку sigma=0.5). Val Mean AUC = 0.7172 (transformer, 104k params, epoch 5, LR=0.001).
- **artifacts**: `ML/reports/threshold_analysis_tb.md`, `ML/reports/tb_selected_rule.json`, `ML/reports/evaluate_test_tb.md`
- **decision**: Цель: устранить разрыв между Python PF (MFE-based, 4.50) и MT4 PF (фиксированные SL/TP, 1.03). Triple Barrier считает PF из фиксированных уровней — Python PF напрямую соответствует торговой механике MT4. Ожидаемый gap < 20%.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-23] — ME-14 & ME-15: Адаптивная фиксация прибыли и Оптимизация (PASS)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `trailing_stop`, `trailing`, `stop`
- **summary**: Проблема блокировки сигналов решена: исполнено 762 сделки. Экстремальный рост доли прибыльных сделок (Win Rate): с 34.55% до 54.07%.
- **artifacts**: `MT/MQL4/Include/lib_ML_Signal.mqh`, `MT/MQL4/Experts/$o$imple.mq4`, `ML/reports/evaluate_test_H12.md`
- **decision**: После выноса метрик во внешние переменные (`SoSimple.mq4`) мы пробили долгожданный порог прибыльности в MT4! Лучший сет (PF=1.03, Сделок=922, Profit=+1207.61):
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-22] — ME-13: Асимметричный R:R и диагностика ML-интеграции (DIAGNOSTIC_ONLY)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `project_history`
- **summary**: ML DIAGNOSTICS: Strategy Tester Report:
- **artifacts**: `MT/MQL4/Include/lib_ML_Signal.mqh`, `MT/MQL4/Experts/$o$imple.mq4`
- **decision**: 1. Первопричина расхождения PF=4.50 (OOS) -> PF<1 (MT4): Python PF считает суммы сырых экскурсий (true_up vs true_dn) без SL/TP, а MT4 использует фиксированный SL=TP=1.6×ATR. Ошибка заглядывания в будущее (Look-ahead bias) в Python забирает идеальный пик прибыли (MFE), тогда как MT4 выходит по закрытию 12-го бара (HoldOverTime), когда цена уже откатилась. 2. Главный bottleneck — Position blocking (51.3%): больше половины сигналов теряются из-за уже открытой позиции. В Python все сигналы независимы. В логе видно: модель генерирует противоположный сигнал (ratio=25.49), но он отклоняется, текущая позиция потом hit SL.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-21] — ME-12: Отладка ML_TRADE() в MT4 Strategy Tester (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `trade`, `mt4`, `strategy`, `tester`
- **summary**: ME-12: Отладка ML_TRADE() в MT4 Strategy Tester
- **artifacts**: `MT/MQL4/Include/lib_ML_Signal.mqh`, `MT/MQL4/Include/MAIN.mqh`
- **decision**: Модель генерирует сигналы, механика торговли работает корректно. Фундаментальная проблема: win rate ~46% при симметричном R:R=1:1 -> PF < 1. Следующий шаг: асимметричный R:R на основе `ratio` (TP = SL × ratio / ML_MinRatio), либо повышение порога ML_MinRatio.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-20] — ME-11: Conformal Prediction — Исследование и Инфраструктура (COMPLETED)
- **report**: `docs/ML/conformal_prediction.md`
- **topics**: `quantile`, `conformal_prediction`
- **summary**: ME-11: Conformal Prediction — Исследование и Инфраструктура
- **artifacts**: `API/generate_signals.py`, `ML/conformal/calibrate.py`, `ML/conformal/conformal_quantiles.json`
- **decision**: Split Conformal Prediction не добавляет ценности при θ=2.665. Причина: порог θ уже настолько агрессивен, что пропускает только 23.6% фракталов — все высококачественные сигналы. Глобальный квантиль не может отличить хорошие сигналы от плохих внутри этой группы. Из 16 отфильтрованных сигналов 15 оказались прибыльными. CP будет полезен при более мягком θ, для управления размером позиции или при переходе на CQR (Conformalized Quantile Regression). Инфраструктура готова для будущих экспериментов.
- **notes**: источник найден в docs/ML; канонический `docs/reports` отчёт не найден

## [2026-03-20] — ME-10: MT4 ↔ ML Integration (PASS)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `updn`, `transformer`
- **summary**: Полная цепочка работает: `Python -> ml_signals.csv -> MQL4 -> торговые сигналы в тестере` Логи тестера подтверждают: `ML_INIT: Loaded 58540 signals`, `ML Signal=1/−1` с корректными pred_up/pred_dn
- **artifacts**: `API/generate_signals.py`, `MT/MQL4/Include/MAIN.mqh`, `MT/MQL4/Include/lib_ML_Signal.mqh`
- **decision**: Отказ от HTTP/WebRequest (`lib_ML_API.mqh`, `api_server.py`, `SoSimple_ML.mq4`) в пользу файлового обмена. WebRequest не работает в Strategy Tester и ненадёжен под Wine (error 5200). Логи тестера подтверждают: `ML_INIT: Loaded 58540 signals`, `ML Signal=1/−1` с корректными pred_up/pred_dn
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-19] — ME-9: Out-of-Sample Evaluation & Threshold Analysis (COMPLETED)
- **report**: `ML/reports/evaluate_test_H12.md`
- **topics**: `updn`, `regression_updn`, `h12`, `threshold_analysis`, `data_loader`
- **summary**: Скрипт `ML/evaluate_test.py`: Запуск обученной модели на отложенной (Test) выборке `Nero_test_labeled.csv`. `ML/data_loader.py`: Поддержка загрузки и кэширования тестовой выборки (`TEST_FILE`).
- **artifacts**: `ML/reports/evaluate_test_H12.md`, `ML/reports/threshold_analysis_12H.md`, `ML/evaluate_test.py`
- **decision**: Этот результат подтверждает устойчивость выявленных (Transformer) рыночных паттернов на новых данных и открывает дорогу к интеграции модели в торговый эксперт MQL4.
- **notes**: источник найден в ML/reports; канонический `docs/reports` отчёт не найден

## [2026-03-19] — ME-8: Multi-Task Regression (COMPLETED)
- **report**: `ML/reports/architecture_comparison_regression_updn.md`
- **topics**: `updn`, `regression_updn`, `data_loader`, `transformer`
- **summary**: Per-target Pearson r: up_12=0.502, dn_12=0.538, up_24=0.406, dn_24=0.421, up_48=0.333, dn_48=0.359 Средний Pearson r: 0.427 | MAE: 0.169 | R²: 0.183
- **artifacts**: `ML/reports/architecture_comparison_regression_updn.md`, `ML/reports/optuna_best_params_transformer_regression_updn.json`, `ML/data_loader.py`
- **decision**: Transformer и BiLSTM практически идентичны. Transformer выбран для Optuna-оптимизации. `optimize.py`: поддержка `--task regression_updn`, архитектурные параметры для transformer (d_model, nhead, num_layers, dim_feedforward, dropout).
- **notes**: источник найден в ML/reports; канонический `docs/reports` отчёт не найден

## [2026-03-19] — ME-7: Time Features + Up/Dn Normalization + ATR_ratio Fix (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `normalization`, `data_loader`
- **summary**: `data_loader.py`: ATR_ratio теперь вычисляется как `log(fractal_Atr.Fast / Atr.Slow)`. `label_main.py`: Убрана ATR нормализация (RobustScaler). Atr.Slow сохраняется в CSV сырым — используется только как знаменатель для ATR_ratio в data_loader.
- **artifacts**: `ML/data_loader.py`, `processing/normalize.py`, `processing/label_main.py`
- **decision**: Артефакт `DATA/Nero_atr_scaler.pkl` больше не создаётся. Вызовы `normalize_atr_train()` / `normalize_atr_inference()` убраны из pipeline.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-18] — ME-6: Up/Dn Fixed-Horizon Targets + ATR_ratio (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `updn`, `fixed`, `horizon`, `targets`, `atr`
- **summary**: `dataset_description.md`: Добавлены признаки `Up/Dn` (12/24/48 баров) и Atr.Fast для каждого фрактала. `up_N` = max(High - P), `dn_N` = max(P - Low) за первые N баров после формирования фрактала. Оба ≥ 0, не зависят от направления.
- **artifacts**: `processing/label_signals.py`, `processing/label_main.py`, `docs/DATA_FLOW.md`
- **decision**: Все 4 модели убыточны (PF=0.728). Решение: заменить таргет `predict` шумный (переменный горизонт, зависимость от `direction`) на — direction-independent таргеты с фиксированным горизонтом.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-16] — ME-5: Custom Trading Loss (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `threshold_analysis`, `optuna`
- **summary**: `ML/losses.py`: Реализован класс `AsymmetricLoss`, позволяющий задавать разные штрафы за перепрогноз (over-prediction, FP) и недопрогноз (under-prediction, FN). `ML/train.py`: Добавлена поддержка `--regression_loss asymmetric` с параметрами `--asym_over_penalty` и `--asym_under_penalty`.
- **artifacts**: `ML/losses.py`, `ML/train.py`, `ML/optimize.py`
- **decision**: Вывод: Изменение функции потерь помогает, но основной лимит — в слабых признаках или шумном таргете.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-12] — ME-3: Feature Engineering (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `threshold_analysis`, `data_loader`
- **summary**: Profit Factor остался ниже 1.0 (0.5908). Ни подбор гиперпараметров (ME-1), ни усечение истории (ME-2), ни новые динамические признаки (ME-3) не смогли вытянуть прибыльную модель регрессии.
- **artifacts**: `ML/data_loader.py`
- **decision**: Интеграция в пайплайн загрузки `ML/data_loader.py` — теперь сеть получает 16 признаков вместо сырых 11, что должно усилить сигнал тренда. Profit Factor остался ниже 1.0 (0.5908). Ни подбор гиперпараметров (ME-1), ни усечение истории (ME-2), ни новые динамические признаки (ME-3) не смогли вытянуть прибыльную модель регрессии.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-12] — ME-2: Ablation Study (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `ablation`, `study`
- **summary**: Создан скрипт `ML/ablation_study.py` для оценки влияния длины подаваемой истории фракталов (`seq_len`). Критический вывод: Усечение `seq_len` со 100 до 20 последних фракталов сохраняет и даже чуть улучшает качество модели (Pearson r = 0.328 vs 0.324), при этом сокращая время обучения в 2.5 раза (18 с вместо 46 с). Огромный пласт "старых" данных признан шумом.
- **artifacts**: `ML/ablation_study.py`, `ML/data_loader.py`
- **decision**: Критический вывод: Усечение `seq_len` со 100 до 20 последних фракталов сохраняет и даже чуть улучшает качество модели (Pearson r = 0.328 vs 0.324), при этом сокращая время обучения в 2.5 раза (18 с вместо 46 с). Огромный пласт "старых" данных признан шумом.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-12] — Оптимизация regression завершена! (COMPLETED)
- **report**: `ML/reports/optuna_best_params_bilstm_regression.json`
- **topics**: `optuna`, `regression`
- **summary**: HPO для BiLSTM успешно отработал, найдя параметры (lr=0.004, batch=256, dropout=0.36), которые позволили поднять best_value (Pearson r) с 0.323 до 0.342 "сырые" данные фракталов (цены + базовый ATR) исчерпали свой потенциал
- **artifacts**: `ML/reports/optuna_best_params_bilstm_regression.json`, `ML/reports/optuna_study_bilstm_regression_20260312_003636.json`, `ML/optimize.py`
- **decision**: Лучшие параметры сохранены: `ML/reports/optuna_best_params_bilstm_regression.json` История trials сохранена: `ML/reports/optuna_study_bilstm_regression_20260312_003636.json`
- **notes**: источник найден в ML/reports; канонический `docs/reports` отчёт не найден

## [2026-03-11] — ME-1: Подготовка к Optuna HPO для регрессии (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `optuna`, `hpo`
- **summary**: `ML/train.py`: функция `train_model` теперь принимает `model_kwargs` и прокидывает их в `get_model()` для инициализации параметров архитектуры. Добавлено сохранение этих параметров в логи `experiments_log.csv`. `ML/optimize.py`: добавлена поддержка функции генерации гиперпараметров архитектуры `hidden_size`, `num_layers`, `dropout` для `bilstm`.
- **artifacts**: `ML/train.py`, `ML/optimize.py`, `ML/reports/experiments_log.csv`
- **decision**: `ML/train.py`: функция `train_model` теперь принимает `model_kwargs` и прокидывает их в `get_model()` для инициализации параметров архитектуры. Добавлено сохранение этих параметров в логи `experiments_log.csv`. `ML/optimize.py`: добавлена поддержка функции генерации гиперпараметров архитектуры `hidden_size`, `num_layers`, `dropout` для `bilstm`.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-11] — QW-4: Threshold Analysis (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `threshold_analysis`, `threshold`, `regression`, `trading`
- **summary**: При Pearson r ≈ 0.32 (BiLSTM): лучший PF = 0.618, precision = 23%, recall = 20% Вывод: сигнал слишком слаб для торговли -> необходим HPO (ME-1) или feature engineering (ME-3)
- **artifacts**: `ML/threshold_analysis.py`, `ML/reports/threshold_analysis_12H.md`
- **decision**: Вывод: сигнал слишком слаб для торговли -> необходим HPO (ME-1) или feature engineering (ME-3)
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-11] — Обеспечение 100% воспроизводимости экспериментов (COMPLETED)
- **report**: `ML/reports/reproducibility_report_12H.md`
- **topics**: `weighted_sampler`
- **summary**: В `experiments_log.csv` теперь логируются все гиперпараметры, влияющие на результат: `seed`, `weight_decay`, `huber_delta`, `scheduler_patience`, `scheduler_factor`, `focal_gamma`, `use_weighted_sampler`, `num_parameters`. Автоматический сбор текущего `git_commit` при каждом запуске для точной привязки чекпоинта к кодовой базе.
- **artifacts**: `ML/reports/reproducibility_report_12H.md`, `ML/reports/experiments_log.csv`
- **decision**: Скрипт ML/reproducibility_tests.py успешно отработал и сгенерировал отчёт ML/reports/reproducibility_report.md. Вот главные выводы: Тест 2 (Детерминизм): Три запуска с seed=42 выдали абсолютно идентичный результат вплоть до 5-го знака: Pearson r = 0.32255. Это подтверждает, что при фиксированном seed проект строго детерминирован.
- **notes**: источник найден в ML/reports; канонический `docs/reports` отчёт не найден

## [2026-03-11] — Ускорение загрузки данных (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `data_loader`
- **summary**: Кэширование распарсенных тензоров в `.npy` файлы в `data_loader.py` для значительного ускорения повторных запусков обучения.
- **artifacts**: `ML/data_loader.py`
- **decision**: Кэширование распарсенных тензоров в `.npy` файлы в `data_loader.py` для значительного ускорения повторных запусков обучения.
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-03-10] — Ключевые находки аудита проекта (COMPLETED)
- **report**: `docs/archive/answer.md`
- **topics**: `data_loader`, `docs`, `archive`, `audit`, `answers`
- **summary**: DirAcc = 97.5% — НЕ data leakage. Это артефакт кода. В `ML/data_loader.py` (строка 270) регрессионный таргет берётся как `np.abs(df_train[target])` — все значения ≥ 0. Метрика `directional_accuracy` в `ML/utils.py` (строка 145) вычисляет `sign(y_true) == sign(y_pred)`. Поскольку y_true ≥ 0 и модель обучена предсказывать неотрицательные значения, DirAcc тривиально высок. `direction` как feature: `fractal[0].direction` ∈ {-1, 1} напрямую коррелирует со знаком `predict` (по определению: `predict = -back * direction`). Для задачи классификации `signal` это может быть мягкая форма leakage — direction определяет направление сигнала, хотя не его наличие. Для регрессии `|predict|` проблемы нет, т.к. знак удалён.
- **artifacts**: `docs/archive/answer.md`, `ML/data_loader.py`, `ML/utils.py`
- **decision**: Для регрессии: все 43 593 примера вносят вклад (регрессия на `|predict|`). Ratio параметров к примерам ≈ 3.4:1 — приемлемо. Validation: 232 Sell + 244 Buy = 476 примеров для оценки. Стандартная ошибка F1 при таком размере: ±0.03-0.05. Разница между моделями (0.017 F1) статистически незначима.
- **notes**: источник найден в docs/archive; исходный архивный audit path из старой записи отсутствует

## [2026-02-27] — Оптимизация под торговые сигналы: метрики и балансировка (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `project_history`
- **summary**: Ошибка в WeightedRandomSampler: преобразование меток {-1, 0, 1} -> {0, 1, 2} через `y_train + 1` вместо list comprehension
- **artifacts**: `ML/train.py`, `ML/utils.py`, `ML/data_loader.py`
- **decision**: WeightedRandomSampler используется только для train; val/test сохраняют реальное распределение Для `metric_mode=signal_precision` применяется штраф, если recall < min_signal_recall
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-02-27] — Критический анализ: ловушка дисбаланса классов (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `project_history`
- **summary**: Macro F1 = 0.57 — обманчивая метрика: высокое значение достигается за счёт F1(0)=0.95 (neutral, 95% данных) Торгово-значимые классы (-1 и 1) имеют F1 ≈ 0.35 — катастрофически низкое качество
- **artifacts**: `docs/archive/answer.md`, `ML/utils.py`
- **decision**: Модели с "хорошим" Macro F1 фактически непригодны для торговли Требуется смена целевой метрики (F1 minority, MCC) и балансировка батчей (WeightedRandomSampler)
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-02-27] — Сравнение архитектур нейросетей (COMPLETED)
- **report**: `ML/reports/architecture_comparison_regression.md`
- **topics**: `transformer`
- **summary**: Bi-LSTM: лучший Pearson r = 0.3236, 147K параметров Hybrid CNN+LSTM: Pearson r = 0.2825, 83K параметров
- **artifacts**: `ML/reports/architecture_comparison_regression.md`, `ML/reports/architecture_comparison_classification.md`
- **decision**: 1D-CNN: Pearson r = 0.2518, 42K параметров (самая быстрая) Transformer: Pearson r = 0.1143, 70K параметров
- **notes**: источник найден в ML/reports; канонический `docs/reports` отчёт не найден

## [2026-02-25] — Оптимизация гиперпараметров (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `optuna`
- **summary**: Автоматический подбор гиперпараметров с помощью Optuna Поддержка pruning (досрочная остановка неперспективных trials)
- **artifacts**: `ML/optimize.py`, `ML/reports/optuna_best_params_cnn1d_classification.json`
- **decision**: Поддержка pruning (досрочная остановка неперспективных trials) Оптимизация для classification (macro F1) и regression (pearson_r)
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-02-23] — Поддержка обучения в режиме регрессии (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `predict_target`, `predict`, `target`
- **summary**: Поддержка раннего останова по корреляции Пирсона (`pearson_r`) HuberLoss (δ=1.0) для робастной функции ошибок при регрессии
- **artifacts**: `ML/train.py`, `ML/utils.py`
- **decision**: HuberLoss (δ=1.0) для робастной функции ошибок при регрессии Метрики регрессии: MAE, RMSE, R², pearson_r, DirAcc
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-02-18] — Baseline ML эксперименты (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `xgboost`, `baseline`
- **summary**: 5 baseline-моделей: Dummy, LogReg, RF, XGBoost, LightGBM
- **artifacts**: `ML/reports/architecture_comparison_classification.md`, `ML/reports/architecture_comparison_regression.md`
- **decision**: 5 baseline-моделей: Dummy, LogReg, RF, XGBoost, LightGBM
- **notes**: канонический `docs/reports` отчёт не найден

## [2026-02-07] — Исправление нормализации predict (COMPLETED)
- **report**: отсутствует (legacy запись; канонический отчёт не найден)
- **topics**: `predict`
- **summary**: Обработка знакового `predict` в `normalize.py` `predict` теперь корректно нормализуется: модуль -> нормализация -> восстановление знака
- **artifacts**: `processing/normalize.py`
- **decision**: Обработка знакового `predict` в `normalize.py` `predict` теперь корректно нормализуется: модуль -> нормализация -> восстановление знака
- **notes**: канонический `docs/reports` отчёт не найден
