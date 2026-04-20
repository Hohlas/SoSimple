# Context Handoff

## Current Stage
Этап `take_skip_original_contour_feature_ablation` завершён (2026-04-20).

Что зафиксировано:

- создан план: `docs/superpowers/plans/2026-04-20-take-skip-original-contour-feature-ablation.md`;
- добавлен runner `ML/run_take_skip_original_contour_feature_matrix.py`;
- добавлены тесты `tests/test_take_skip_original_contour_feature_matrix.py`;
- добавлена документация `docs/ML/run_take_skip_original_contour_feature_matrix.py.md`;
- обновлены `ML/README.md`, `MODULE_INDEX.md`, `CHANGELOG.md`.
- canonical report: `docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md`.

Смысл runner-а:

- проверить `lib_PIC` path/geometry признаки не в новом dual-stream контуре, а в старом single-tensor `take_skip_v2` представлении;
- `original_baseline` воспроизводит старый подход: parsed fractals + multi-scale summaries + старые row-wise признаки;
- `original_plus_path` и `original_plus_geometry_path` добавляют новые признаки поверх старого baseline, а не заменяют его.

Проверка:

- выполнено:
  - `/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_original_contour_feature_matrix.py tests/test_take_skip_trailing_stop_v2_task.py tests/test_take_skip_lib_pic_feature_matrix.py -q`
  - результат: `15 passed`, одно стандартное предупреждение PyTorch про nested tensors.

Главные результаты:

- контроль `original_baseline_seq50` восстановил старый контур:
  - `input_features=539`;
  - `take_24_x8`, `prob>=0.70`;
  - validation `PF=inf`, `7.75` trades/year;
  - test `PF=49.58`, `9.2` trades/year, negative years `0`.
- полная матрица `3 feature modes × seq_len 20/50/100`:
  - runtime `2840.42 sec`;
  - все 9 конфигураций получили `go`;
  - лучший practical candidate: `original_plus_path_seq50`;
  - rule: `take_24_x8`, `prob_ge_threshold >= 0.60`, exit `x8`;
  - validation: `9.75` trades/year, `PF=16.07`, negative years `0`;
  - test: `10.2` trades/year, `PF=38.78`, negative years `0`, max DD `3.89 ATR`.

Решение:

- `path` признаки полезны как practical frequency uplift поверх quality-системы;
- `geometry` не продвигать в MT4 сейчас: высокий PF, но test частота только `4.8` trades/year;
- `original_baseline_seq50/100` оставить как quality anchor;
- `original_plus_path_seq50` проверить в MT4 как третий candidate рядом с `quality` и `frequency`.

Следующий шаг:

1. Сформировать selected rule для `original_plus_path_seq50`.
2. Экспортировать сигналы из `take_skip_original_contour_feature_matrix/original_plus_path_seq50`.
3. Проверить в MT4 с `ML_TrailATR=8`, `ML_TakeProfitATR=0`.

## Previous Stage
Этап `take_skip_lib_pic_feature_training` завершён (2026-04-20).

Что зафиксировано:

- добавлен `ML/run_take_skip_lib_pic_feature_matrix.py`;
- добавлена модель `ML/models/take_skip_dual_stream_transformer.py`;
- добавлены тесты `tests/test_take_skip_lib_pic_feature_matrix.py`;
- runner поддерживает:
  - `baseline_clean`;
  - `baseline_clean_path`;
  - `baseline_clean_geometry_path`;
  - `seq_len 20/50/100`;
  - авто-выбор доступных `take_skip_v2` target columns по CSV;
  - параллельный запуск через `--jobs`;
  - авто-настройку CPU через `--jobs auto --torch-threads auto --cpu-load`.
- canonical report: `docs/reports/2026-04-20-take-skip-lib-pic-feature-training.md`.

Главные результаты:

- полный серверный runtime: `3123.32 sec`;
- проверено `9` конфигураций;
- все `9` конфигураций получили `verdict=reject`;
- validation grid:
  - всего строк: `1377`;
  - `PF > 1`: `79`;
  - `PF > 1` и `trades_per_year >= 6`: `0`;
- лучший practical-area результат:
  - `baseline_clean_seq20`;
  - `take_12_x2`;
  - `top_k=5%`;
  - `trades_per_year=6.0`;
  - validation `PF=0.9476`.

Решение:

- simple dual-stream добавление `lib_PIC`-признаков внутрь модели не дало рабочего торгового отбора;
- `lib_PIC`-признаки пока полезнее как внешний фильтр, чем как простая добавка во вход модели;
- этот результат не доказывает, что “новые признаки вредят старой модели”, потому что training contour отличается от старого прибыльного baseline;
- следующий рациональный шаг — controlled ablation:
  - воспроизвести исходный прибыльный baseline в максимально близком контуре;
  - добавить к нему сильные `lib_PIC` path-признаки;
  - отдельно проверить полный `baseline + path + geometry`;
  - сравнить validation-first и только потом смотреть frozen test.

## Previous Stage
Этап `take_skip_lib_pic_external_selection` завершён (2026-04-20).

Что зафиксировано:

- добавлен `ML/benchmark_take_skip_lib_pic_selection.py`;
- добавлены тесты `tests/test_benchmark_take_skip_lib_pic_selection.py`;
- benchmark проверяет внешний слой отбора поверх готовых `take_skip_trailing_stop_v2` prediction CSV без нового обучения;
- prediction CSV соединяется с source/labeled CSV по порядку строк и `time`;
- используется профиль признаков `baseline_clean_geometry_path`;
- пороги `lib_PIC`-признаков выбираются только на validation и frozen-применяются на test;
- canonical report: `docs/reports/2026-04-20-take-skip-lib-pic-selection.md`.

Главные результаты:

- `quality-first` снова выбрал старое правило без feature-фильтра:
  - `take_24_x8`, `prob >= 0.70`, exit `x8`;
  - test: `PF=39.74`, `trades_per_year=8.2`, `negative_year_slices=0`.
- raw `frequency-first` без feature-фильтра:
  - `take_24_x4`, `top_k 20%`, exit `x10`;
  - test: `PF=7.18`, `trades_per_year=19.2`, `negative_year_slices=1`.
- лучший режим с обязательным `lib_PIC`-фильтром:
  - `take_24_x8`, `top_k 20%`, exit `x10`;
  - `pic_path_win_proxy24_share_w20 >= 0.25`;
  - test: `PF=5.30`, `trades_per_year=14.8`, `negative_year_slices=0`.

Решение:

- внешний `lib_PIC`-фильтр не заменяет текущие `quality` / `frequency` правила;
- фильтр выглядит полезным как диагностический устойчивостный сигнал;
- не усложнять внешний selection-layer дальше;
- следующий рациональный шаг — новый training track, где `lib_PIC`-производные признаки участвуют внутри модели.

## Previous Stage
Этап `execution_policy_v2` завершён (2026-04-19).

Что зафиксировано:

- добавлен `ML/benchmark_execution_policy_v2.py` для сравнения вариантов выхода на готовых `quality` и `frequency` ML-сигналах без нового обучения;
- benchmark пишет:
  - `ML/reports/execution_policy_v2/summary.csv`
  - `ML/reports/execution_policy_v2/summary.json`
  - `ML/reports/execution_policy_v2/trades.csv`
  - отдельный узкий прогон `ML/reports/execution_policy_v2/frequency_trail_scan/`
- добавлены метрики формы equity:
  - `max_drawdown_atr`
  - `ulcer_index_atr`
  - `equity_linearity_r2`
  - `profit_concentration_top_1/3/10`
  - `negative_months / negative_years`
  - худшая сделка и худшие серии
- в MT4 добавлен `ML_TakeProfitATR`:
  - `0` -> take profit выключен
  - `>0` -> broker-side take profit в ATR от входа
- MT4 direct ML mode теперь умеет:
  - `ML_ExitMode=1`
  - `ML_TrailATR`
  - `ML_TakeProfitATR`
  - `ML_MaxPositions` как аварийный потолок, не как торговое правило

Главные результаты:

- `quality`:
  - `TrailATR=8, TP=0`: net `18037.59`, `20` trades, `PF=51.95`, DD `11.70%`
  - `TrailATR=8, TP=12`: net `11544.89`, `20` trades, `PF=33.61`, DD `4.97%`
  - вывод: TP=12 делает equity ровнее и режет экстремальную сделку, но снижает прибыль
- `frequency`:
  - `TrailATR=6, TP=0`: net `18455.93`, `56` trades, `PF=4.22`, DD `16.78%`
  - `TrailATR=8, TP=0`: net `24521.88`, `56` trades, `PF=3.77`, DD `25.71%`
  - `TrailATR=10, TP=0`: net `26137.10`, `56` trades, `PF=3.31`, DD `27.44%`
  - `TrailATR=8, TP=12`: net `12085.05`, `56` trades, `PF=2.37`, DD `17.27%`
  - вывод: для `frequency` take profit временно снят, основной режим — чистый trailing
- Python scan по `frequency`:
  - `trail_x6`: PF `4.08`, net `169.72 ATR`, DD `18.00 ATR`, R2 `0.821`, top1 `13.8%`
  - `trail_x8`: PF `3.73`, net `215.77 ATR`, DD `22.54 ATR`, R2 `0.766`, top1 `18.9%`
  - `trail_x10`: PF `4.12`, net `323.09 ATR`, DD `39.66 ATR`, R2 `0.564`, top1 `30.3%`

Решение:

- основной practical candidate для `frequency`: `ML_TrailATR=8`, `ML_TakeProfitATR=0`
- осторожный candidate: `ML_TrailATR=6`, `ML_TakeProfitATR=0`
- `TrailATR=10` оставить как агрессивный диагностический вариант, но не основной из-за худшей формы equity и высокой концентрации прибыли
- canonical report: `docs/reports/2026-04-19-execution-policy-v2.md`

## Previous Stage
Этап `mt4_trailing_stop_execution` завершён (2026-04-18).

Что зафиксировано:

- в прямой MT4-контур `iSignal=3` добавлен отдельный режим выхода:
  - `ML_ExitMode=0` -> timeout parity-check
  - `ML_ExitMode=1` -> trailing-stop по `ML_TrailATR * ATR`
- добавлен новый параметр:
  - `ML_TrailATR`
- реализация сделана внутри `MT/MQL4/Include/lib_ML_Signal.mqh`, без возврата к старому `OUTPUT()/TRAILING_STOP()` контуру
- trailing-mode хранит лучший ход цены после входа:
  - BUY: лучший максимум по `High[bar]`
  - SELL: лучший минимум по `Low[bar]`
- в лог tester добавлены явные причины:
  - `MLP_TrailingStop`
  - диагностика `best`, `trail`, `trail_atr`
- обновлены:
  - `docs/MT/ml_signal_integration.md`
  - `docs/MT/trading_strategy.md`
- canonical report: `docs/reports/2026-04-18-mt4-trailing-stop-execution.md`

## Previous Stage
Этап `take_skip_rule_consumer` завершён (2026-04-18).

Что зафиксировано:

- добавлен новый прикладной exporter `API/export_take_skip_trailing_stop_v2_signals.py`
- exporter читает:
  - prediction CSV
  - frozen rule JSON
  - optional `base-csv`
- поддержаны оба frozen selector-а:
  - `prob_ge_threshold`
  - `top_k_probability`
- exporter может:
  - писать sparse `time;signal`
  - разворачивать sparse export в полный временной ряд
  - копировать результат сразу в tester/runtime каталоги MT4
- добавлены тесты `tests/test_export_take_skip_trailing_stop_v2_signals.py` (`5/5` зелёные)
- canonical report: `docs/reports/2026-04-18-take-skip-rule-consumer.md`

## Previous Stage
Этап `take_skip_frequency_followup` завершён (2026-04-18).

Что зафиксировано:

- новый training-cycle не запускался;
- добавлен read-only benchmark `ML/benchmark_take_skip_trailing_stop_v2_followup.py`;
- trailing-stop grid для labels и `take_skip_v2` contract расширен до `x10 / x12`;
- follow-up сделан поверх уже обученного `take_skip_trailing_stop_v2` winner-а `seq50`;
- из-за отсутствия канонически сохранённых `v2` prediction CSV score был локально восстановлен из checkpoint, без обучения, с тем же feature representation (`539` входов);
- получены три полезных режима:
  - `quality-first`:
    - `score = take_24_x8`
    - `selector = prob >= 0.70`
    - `exit = x8`
    - test: `PF=39.74`, `trades_per_year=8.2`, `negative_year_slices=0`
  - `frequency-first`:
    - `score = take_24_x4`
    - `selector = top_k 20%`
    - `exit = x10`
    - test: `PF=7.18`, `trades_per_year=19.2`, `negative_year_slices=1`
  - `anchor-expansion`:
    - `score = take_24_x8`
    - `selector = top_k 20%`
    - `exit = x8`
    - test: `PF=7.17`, `trades_per_year=19.2`, `negative_year_slices=0`
  - `anchor-sweet-spot`:
    - `score = take_24_x8`
    - `selector = top_k 17%`
    - `exit = x8`
    - test: `PF=13.12`, `trades_per_year=16.4`, `negative_year_slices=0`, `max_drawdown_atr=4.03`
- canonical report: `docs/reports/2026-04-18-take-skip-frequency-followup.md`
- canonical rules:
  - `ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json`
  - `ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json`

## Current Stage
Этап `quantile_forward_validation_scaffold` завершён (2026-04-13).

Что зафиксировано:

- создан frozen benchmark `ML/benchmark_quantile_forward_validation.py` + тесты `tests/test_benchmark_quantile_forward_validation.py` (`16/16` зелёные)
- benchmark использует только внешний forward prediction CSV и не перенастраивает `entry_path_v1_quantile`
- CLI пишет:
  - `ML/reports/quantile_forward_validation/summary.json`
  - `ML/reports/quantile_forward_validation/time_slices.csv`
  - `ML/reports/quantile_forward_validation/run_metadata.json`
- operational verdict текущего состояния:
  - `verdict = watch`
  - `reason = no_forward_data`
- причина: в репозитории нет нового strictly-forward prediction CSV после production decision; доступны только historical validation/test prediction-файлы
- canonical report: `docs/reports/2026-04-13-quantile-forward-validation.md`

## Previous Stage
Этап `fav_3_vs_12_standalone_verdict` завершён (2026-04-13).

Что зафиксировано:

- создан standalone benchmark `ML/benchmark_fav_3_vs_12_standalone.py` + тесты `tests/test_benchmark_fav_3_vs_12_standalone.py` (`17/17` зелёные)
- benchmark использует:
  - `ML/reports/quantile_fav_composition/updn_active_source/*` как источник `pred_fav_3`, `pred_fav_12`, `fav_3_vs_12`
  - `ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_*_predictions.csv` как источник фактического результата сделки `true_ret_24_dir_atr`
- выбор порога делается только на `validation`, с жёсткой проверкой устойчивой зоны:
  - отсортированные уникальные пороги
  - полный центрированный window
  - приоритет устойчивости окна, а не локального PF-пика
  - плохой год = `PF < 1.0`, годы с `trades < 3` не считаются самостоятельным gate-fail
- итог standalone run:
  - `selected_threshold = null`
  - `verdict = reject_as_standalone`
  - на validation лучший порог с `N >= 30` всё равно слабый: `threshold=0.22`, `N=36`, `PF=0.1378609915504136`, `negative_year_slices=4`
  - на test лучшая диагностическая точка тоже слабая: `threshold=0.24`, `N=164`, `PF=0.3129480021818097`, `negative_year_slices=5`
- canonical report: `docs/reports/2026-04-13-fav-3-vs-12-standalone.md`

## Earlier Stage
Этап `quantile_fav_composition_verdict` завершён (2026-04-13).

Что зафиксировано:

- создан benchmark `ML/benchmark_quantile_fav_composition.py` + тесты `tests/test_benchmark_quantile_fav_composition.py` (`5/5` зелёные)
- quantile control numbers воспроизведены exactly against `ML/reports/entry_path_v1_quantile_selected_rule.json`:
  - validation: `N=32`, `PF=11.240091883688192`
  - test: `N=48`, `PF=8.178675196069868`
- root cause устранён:
  - `fav_3_vs_12` больше не берётся из внешнего research CSV
  - добавлен `ML/export_updn_active_predictions.py`, который считает `pred_fav_3 / pred_fav_12` из `transformer_updn_best.pt` на тех же активных строках validation/test
  - verified one-to-one alignment: порядок активных строк в `DATA/Nero_{validation,test}_labeled.csv` и quantile predictions совпадает exactly
- честный composition rerun:
  - validation: `quantile_only N=32 PF=11.240091883688192`, `composition N=28 PF=21.852917603463066`
  - test: `quantile_only N=48 PF=8.178675196069868`, `composition N=47 PF=7.860844837655267`
  - intersection diagnostic: `47 / 48` quantile trades survived (`trades_lost_from_quantile = 1`)
  - composition почти не режет quantile, но добавляет один отрицательный годовой срез: `2023 PF=0.47526255177309695 (N=5)`
- `n_boost_composition.json`: `verdict = gate_fail`, `n_trades = 47`, `pf = 7.860844837655267`, `negative_year_slices = 1`
- formal verdict: **CLOSED — gate fail**
- canonical report: `docs/reports/2026-04-13-quantile-fav-composition.md`

## Historical Stage
Этап `label_convention_audit` завершён (2026-04-13).

Что зафиксировано:

- baseline blocker устранён:
  - отсутствовал `ML/benchmark_triple_barrier_mt4_execution.py`, из-за чего `tests/test_triple_barrier_mt4_execution.py` падал на import во время collection
  - модуль восстановлен минимально, baseline suite снова зелёный
- label convention audit завершён:
  - source of truth `processing/label_signals.py` не менялся
  - confirmed bugs:
    - `ML/tb_signal_logic.py`: `loss_mask = ~win_mask` включал timeout в losses
    - `ML/threshold_analysis.py`: `losses = n_trades - wins` включал timeout в losses
  - оба места исправлены на явный `SL == 0.0`
  - добавлены permanent guards: `tests/test_tb_label_invariants.py`
  - inventory: `ML/reports/label_convention_audit_inventory.csv`
  - audit report: `ML/reports/label_convention_audit.md`
- frozen rerun выполнен на canonical artifacts из основного дерева:
  - `MT/MQL4/Files/ml_signals_tb.csv`
  - `DATA/Nero_validation_labeled.csv`
  - `DATA/Nero_test_labeled.csv`
  - validation summary совпал exactly: `28 / 16 / 4 / 2`, `PF=4.333333333333333`
  - test summary совпал exactly: `69 / 29 / 23 / 5`, `PF=1.2777777777777777`
  - значит найденные bugs в `ML/tb_signal_logic.py` и `ML/threshold_analysis.py` **не меняют** historical verdict из `2026-04-12-tb-verdict.md`

## Older Historical Stage
Этап `triple_barrier_mt4_verdict` завершён. Этап `entry_path_v1_quantile_productization` закрыт ранее (2026-04-12, коммит `0023d92`).

Что зафиксировано:

- **`entry_path_v1_quantile`** — production-ready parallel execution mode:
  - winner `lb_gt_m_q35` (median m/w/correction по 5 сидам)
  - n-boost gate PASS: N=48, PF=8.18, win_rate=0.8125, negative_year_slices=0, same_winner_ratio=1.0
  - MT4 parity 20/20 сделок, win rate 80% exact, PF=11.91 в деньгах (tester лог `20260412.log`)
  - production rule: `ML/reports/entry_path_v1_quantile_selected_rule.json`
  - канонический экспорт: `API.export_entry_path_v1_quantile_signals --rule-path ...`
  - канонический seed: `seed_007`
- **Triple Barrier** — **не production**:
  - в симуляторе `ML/triple_barrier_mt4_execution.py` был баг: `int(outcome)` приводил label в float-конвенции `{1.0=TP, 0.0=SL, 0.5=Timeout}` к целому, SL и Timeout сливались в одну ветку `else → HoldOverTime, pnl=+0.5`. Все прежние прогоны TB давали `losses=0, pf=inf` — это артефакт, а не результат.
  - фикс: `_classify_tb_outcome` с порогами `>=0.75` → TP, `<=0.25` → SL, else → Timeout; патч применён в обеих точках закрытия позиции
  - тесты `tests/test_triple_barrier_mt4_execution.py` переведены с устаревшей `{1, -1, 0}` int-схемы на float; 6/6 зелёные
  - честный прогон `tb_selected_rule.json` (`theta=0.475`, `min_ev=0.1`) на исправленном симуляторе:
    - validation (2019–2022): N=28, PF=4.33, win_rate=57.1%, все годы положительные
    - test (2023–2026): N=69, PF=1.28, win_rate=42.0%, negative years: 2023 (PF=0.55), 2026 (PF=0.00)
  - gate-проверка (унифицированно с quantile: N≥30, PF>2.0, negative_year_slices=0): **fail** (PF и negative years)
  - `tb_selected_rule.json` зафиксирован как frozen исторический артефакт, в MT4 не подключается
  - пересмотр возможен только после накопления forward-данных post-2026-06

## Last Completed Stage
Quantile Forward Validation Scaffold (2026-04-13).

Adjacent local stage also present: PF Uplift Discovery — Beyond ML Layer (2026-04-13), verdict **SHORTLISTED (3)**.

PF uplift discovery зафиксировал:

- Read-only discovery прогон на `entry_path_v1_quantile` test set (N=48, PF=8.179)
- 20 гипотез по 5 категориям (R/S/E/F/X), hard bans соблюдены
- 6 cheap probes выполнены на `trade_enriched.csv` (N=72 baseline_selected, N=48 quantile)
- Shortlisted (3 STRONG):
  1. NY session exclusion: PF=20.276, N=34, pf_delta=+12.097
  2. Early timeout hold_bars=12: PF=13.731, N=48, pf_delta=+5.552
  3. pred_adv12 ≤ Q75 cap: PF=12.746, N=37, pf_delta=+4.567

## Next Step
1. Собрать новый forward prediction CSV для `entry_path_v1_quantile` после production decision.
2. Запустить `ML.benchmark_quantile_forward_validation` на этом CSV с `--historical-pf 8.178675196069868`.
3. Только после фактического forward verdict решать, остаётся ли `quantile` просто parallel mode или можно усиливать его роль.
4. Не возвращаться к `fav_3_vs_12` как composition или standalone track без нового сильного основания.
5. Следующий research-фокус после появления forward-данных: execution improvement вокруг `quantile`, сначала выход, потом вход.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `docs/reports/2026-04-13-quantile-forward-validation.md` — текущий forward validation status (`watch / no_forward_data`)
- `docs/reports/2026-04-13-pf-uplift-discovery.md` — discovery verdict (SHORTLISTED 3)
- `docs/superpowers/plans/2026-04-13-quantile-execution-improvement.md` — следующий план
- `docs/superpowers/plans/2026-04-13-ny-session-filter.md` — skeleton plan #1
- `docs/superpowers/plans/2026-04-13-early-timeout-bar12.md` — skeleton plan #2
- `docs/superpowers/plans/2026-04-13-pred-adv-cap.md` — skeleton plan #3
- `docs/reports/2026-04-13-fav-3-vs-12-standalone.md` — standalone verdict
- `docs/reports/2026-04-13-quantile-fav-composition.md` — composition verdict (`CLOSED — gate fail`)
- `ML/reports/pf_uplift_discovery/` — артефакты discovery (baseline_numbers.json, trade_enriched.csv, probe_*.json)
- `AGENTS.md`
- `ML/reports/entry_path_v1_quantile_selected_rule.json`

## Open Risks
- **No forward data yet**: новый benchmark готов, но не может подтвердить `quantile` без strictly newer prediction CSV.
- **TB regime shift**: между validation (2019–2022) и test (2023–2026) PF падает с 4.33 до 1.28. Если 2026-ый catastrophic year — локальный всплеск, решение пересмотрится на forward-данных, но сейчас это "не production" definitively.
- **Quantile low-frequency**: 22 sequential trades на test, PF=3.64. Достаточно для parallel mode, но не для полной замены baseline. Forward validation критична.
- **Label convention risk**: симулятор и два analytics-consumer уже исправлены, но любой новый TB/label consumer должен явно различать `1.0 / 0.5 / 0.0` или документированно бинаризовать timeout как non-TP.

## Latest Report
`docs/reports/2026-04-13-quantile-forward-validation.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
