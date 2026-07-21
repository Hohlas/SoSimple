# Wiki Log — SoSimple
> Append-only chronological record of wiki operations.
> Format: `## [YYYY-MM-DD] operation | description`

## [2026-07-08] ingest | Entry-based movement filter freeze
- Добавлен охват `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`.
- Обновлён `wiki/research/fractal-stop-research.md`: bounded movement-filter ветка дополнена freeze-репликацией; зафиксировано, что результат означает только frozen research segmentation mask для следующего плана.
- Обновлён `wiki/index.md`: охват fractal-stop research расширен до 44 report updates.
- Зафиксировано методическое знание: freeze не является direction, PnL/PF, trading candidate, live rule или permission to open `locked_test`.

## [2026-07-07] ingest | Entry-based movement filter design
- Добавлен охват `docs/reports/2026-07-07-entry-based-movement-filter-design.md`.
- Обновлён `wiki/research/fractal-stop-research.md`: amplitude / movement-regime ветка продолжена bounded movement-filter этапом; зафиксирован единственный допустимый research-only winner `simple_combined / extra_trees_small / H3 / top_fraction=0.05`.
- Обновлён `wiki/index.md`: охват fractal-stop research расширен до 43 report updates.
- Зафиксировано методическое знание: новый этап не поднимает ветку до direction или trading candidate; следующий допустимый шаг — только узкая репликация/заморозка одного filter-а без расширения search space.

## [2026-07-03] update | Entry-based price-feature matrix report sync
- Добавлен охват `docs/reports/2026-07-02-entry-based-updn-price-feature-matrix.md`.
- Обновлён `wiki/research/fractal-stop-research.md`: после next-open target foundation добавлен bounded follow-up с ценовыми и path-блоками; зафиксировано, что `next open` не переоткрыт ни `entry_open` target-ом, ни ограниченной price-feature matrix.
- Обновлён `wiki/index.md`: охват fractal-stop research расширен до 37 report updates.
- Зафиксировано методическое знание: текущий `WEAK_TRACE_FOUND` в matrix-этапе нельзя трактовать как надёжный исследовательский вердикт без усиления summary logic; устойчивого winner между `distance_atr` и `path_reaction` нет.

## [2026-07-03] update | Fractal selection ablation clean rerun
- Добавлен охват `docs/reports/2026-07-03-fractal-selection-ablation-entry-based-target.md`.
- Обновлён `wiki/research/fractal-stop-research.md`: после исправления feature horizon contract (`Up/Dn` только 3/6/12) и all-horizon summary лучший чистый след — `corridor_5atr / xgboost_depth3 / H12 = 0.0795`, но устойчивого directional winner нет.
- Обновлён `wiki/index.md`: охват fractal-stop research расширен до 38 report updates.
- Зафиксировано методическое знание: старый `zones_plus_nearest_k40 / H3` shortlist был следствием `H3-only` summary и смешанных `Up/Dn` горизонтов; следующий допустимый shortlist — `corridor_5atr`, `nearest_k20`, `nearest_k60`, `nearest_k80`.
- Post-review correction: runner status logic приведена к weak-trace rule плана; отчёт дополнен disclosure split, distribution flags, direction-vs-amplitude таблицей и оговоркой, что H12 требует отдельного методического решения перед rerun.

## [2026-07-02] ingest | Regression Up/Dn ratio + already moved audits
- Добавлен охват `docs/reports/2026-07-01-regression-updn-ratio-audit.md` и `docs/reports/2026-07-02-regression-updn-already-moved-audit.md`.
- Обновлён `wiki/research/fractal-stop-research.md`: target foundation теперь продолжена двумя новыми этапами, которые отделяют сигнал от `fractal0_price` от схемы немедленного входа.
- Обновлён `wiki/index.md`: охват fractal-stop research расширен до 35 report updates.
- Зафиксировано новое проектное знание: target family `Regression Up/Dn` подтверждена, но `next open after signal_time` для неё отклонён; следующий допустимый шаг только через entry-механику, привязанную к `fractal0_price` или её ретесту.

## [2026-06-30] ingest | Stage 6.3 H6 feature parity check
- Добавлен охват `docs/reports/2026-06-30-stage6_3-h6-feature-parity-check.md`.
- Обновлён `wiki/research/fractal-stop-research.md`: Stage 6.3 — H6 feature parity check подтвердил NO_ADDITIVE_VALUE; H6 baseline сильнее H12, price-action на H6 почти проходит gate, но additive delta не достигает порога +0.02 и permutation не пройдена.
- Обновлён `wiki/index.md`: охват fractal-stop-research расширен до 32 report updates.
- Зафиксировано: H6 feature parity не изменила verdict; следующий шаг — Regression Up/Dn target foundation.

## [2026-07-01] update | Regression Up/Dn target foundation post-review refresh
- Пересчитан `ML/reports/regression_updn_target_foundation.json` после правок audit/diagnostics; полный прогон снова завершён `75/75`, elapsed `4501.9s`.
- Обновлён `wiki/research/fractal-stop-research.md`: target foundation дополнен честным `feature_read_audit`, disclosure по `log_ratio` и расширенной `calendar_dependence`.
- Обновлён `wiki/index.md`: описание fractal-stop research уточнено без изменения охвата.
- Зафиксировано: главный вывод не изменился — `structure_full` на `H3` остаётся лучшей bounded target-foundation точкой, статус `TARGET_FOUNDATION_PASSED / DIAGNOSTIC_ONLY`.

## [2026-06-30] ingest | Regression Up/Dn target foundation
- Добавлен охват `docs/reports/2026-06-30-regression-updn-target-foundation.md`.
- Обновлён `wiki/research/fractal-stop-research.md`: target family `up_*/dn_*` получила сильное bounded подтверждение на коротких горизонтах; лучший result дал `structure_full` на `H3`, а не legacy `H12`.
- Обновлён `wiki/index.md`: охват fractal-stop-research расширен до 33 report updates.
- Зафиксировано: `TARGET_FOUNDATION_PASSED / DIAGNOSTIC_ONLY`; следующий шаг — confirmatory cycle с замороженным trading mapping поверх `structure_full` и `H3/H6`.

## [2026-06-30] ingest | Stage 6.2 range_w1_atr post-mortem
- Добавлен охват `docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md`.
- Обновлён `wiki/research/fractal-stop-research.md`: `range_w1_atr` доминирует, но evidence strength остаётся `weak`; Stage 6.2 не продвигается.
- Обновлён `wiki/index.md`: охват fractal-stop-research расширен до 31 report updates.
- Следующее направление зафиксировано как `Regression Up/Dn target foundation`; H12 OHLC-window variations не переоткрывать.

## [2026-06-29] ingest | Stage 6.1: H12 Relative Fractal Geometry
- Добавлен охват `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`
- Обновлён `wiki/research/fractal-stop-research.md`: Stage 6.1 MODEL_GATE_FAILED — текущие H12 geometry-only профили вокруг fractal0 не предсказывают TP/SL touch (AUC 0.51–0.55)
- Обновлён `wiki/index.md`: охват fractal-stop-research расширен до 6.1 (29 report updates)
- Статус: tested H12 geometry-only branch закрыта; baseline+geometry delta test выполнен отдельным follow-up ниже.

## [2026-06-29] update | Stage 6.1 runtime artifact refresh
- Пересчитан `ML/reports/stage6_1_h12_relative_fractal_geometry.json` новым runner-ом с `xgb_n_jobs=24`, checkpoint before preflight, heartbeat, `started_at`/`finished_at` и per-run `elapsed_sec`.
- Обновлены `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`, `CHANGELOG.md` и `CONTEXT_HANDOFF.md` под фактический elapsed `3581s` (59.7 мин).
- Исследовательский вывод не изменился: Stage 6.1 остаётся `MODEL_GATE_FAILED` / `DIAGNOSTIC_ONLY`.

## [2026-06-29] update | Stage 6.1 baseline+geometry delta
- Добавлены 3 combined-профиля: `clock_shift_back + nearest_time40`, `clock_shift_back + corridor3`, `clock_shift_back + corridor10`.
- Полный прогон стал `27/27`; все 3 combined-профиля провалили delta gate: AUC delta только `+0.0026..+0.0048`, median PF хуже baseline.
- Обновлены report/changelog/handoff/wiki; итог Stage 6.1 остаётся `MODEL_GATE_FAILED` / `DIAGNOSTIC_ONLY`.
- Граница вывода: закрыта tested encoding family around `fractal0` на XAUUSD H1 H12, а не вся идея фрактальной геометрии.

## [2026-06-29] ingest | Stage 5.4: Fast Price/ATR Ablation
- Добавлен охват `docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md`
- Обновлён `wiki/research/fractal-stop-research.md`: Stage 5.4 REJECT_PRICE_COORD — price/ATR координата не улучшает `fast` ни на sell, ни на buy
- Обновлён `wiki/index.md`: охват fractal-stop-research расширен до 5.4 (27 report updates)
- Статус: price/ATR признаки не объясняют missing `fast` сигнал. Расширение price-поиска не требуется.

## [2026-06-25] ingest | Stage 5.1b: Up/Dn абляция и baseline clock+shift
- Добавлен охват `docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md`
- Обновлён `wiki/research/fractal-stop-research.md`: Stage 5.1b подтвердил, что `back` остаётся устойчивым после добавления `shift`, а Up/Dn дают только слабый самостоятельный сигнал и не улучшают `structure_full`
- Обновлён `wiki/index.md`: охват fractal-stop-research расширен до 5.1b (24 report updates)
- Зафиксировано: Up/Dn не стоит включать в следующий стартовый профиль по умолчанию; допустимый следующий шаг только узкий follow-up вокруг `back`/`impulse`
- Post-review correction: модельные Up/Dn нормализованы per-pair в labeled CSV, raw-shadow preflight проверяет producer; delta CI для field verdicts Stage 5.1b отсутствуют
> Parse last 5 entries: `grep "^## \[" wiki/log.md | tail -5`

## [2026-06-24] ingest | Stage 5.1: структурная абляция фрактальных полей
- Добавлен охват `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md`
- Обновлён `wiki/research/fractal-stop-research.md`: добавлен Stage 5.1 и уточнён общий итог по ветке `H6_off05`
- Обновлён `wiki/index.md`: охват fractal-stop-research расширен до 5.1 (23 report updates)
- Зафиксировано: `back` = единственное поле с итогом `likely_useful`; все остальные поля `mixed_or_unclear`; полей `likely_noise` не найдено; Stage 5.1 не переоткрывает `H6_off05`
> Parse last 5 entries: `grep "^## \[" wiki/log.md | tail -5`

## [2026-06-24] ingest | Stage 5.0f: диагностика устойчивости сигнала во времени
- Добавлен охват `docs/reports/2026-06-24-stage5_0f-signal-stationarity.md`
- Обновлён `wiki/research/fractal-stop-research.md`: Stage 5.0f переписан с уточнёнными выводами
- Обновлён `wiki/index.md`: охват fractal-stop-research расширен до 5.0f (22 report updates)
- Зафиксировано: H2 (temporal decay) скорее опровергнута (fixed > rolling), H1 не подтверждена (AUC > 0.68 в некоторых конфигурациях), Spearman на n=3 неинформативен (p=0.0 — артефакт), природа отрицательного результата не установлена, без нового периода `2026+` большой перебор не оправдан
> Parse last 5 entries: `grep "^## \[" wiki/log.md | tail -5`

## [2026-06-23] ingest | Stage 5.0e: малый Transformer после провала
- Добавлен охват `docs/reports/2026-06-23-stage5_0e-small-transformer-check.md`
- Обновлён `wiki/research/fractal-stop-research.md`: добавлен Stage 5.0e, выводы 29-30, новый закрытый вопрос про размер модели
- Обновлён `wiki/index.md`: охват fractal-stop-research расширен до 5.0e (21 report updates)
- Зафиксировано: `small_regularized` уменьшает признаки переобучения, но `H6_off05` остаётся закрытым
> Parse last 5 entries: `grep "^## \[" wiki/log.md | tail -5`

## [2026-06-23] lint | Stage 5.0d: отчёт исправлен, wiki обновлена
- Отчёт docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md исправлен: неточная формулировка «фрактальные признаки не добавляют информации», добавлена годовая деградация, holdout «молчит», противоречие с 5.0-prep, H1/H2
- wiki/research/fractal-stop-research.md обновлён: summary (status active), Stage 5.0d timeline section, выводы 26-28, открытые вопросы (H1/H2, противоречие с prep)
- wiki/index.md: без изменений (охват тот же)
> Parse last 5 entries: `grep "^## \[" wiki/log.md | tail -5`

## [2026-06-23] ingest | Stage 5.0d diagnostic screening
- Обновлён research/fractal-stop-research.md: добавлен Stage 5.0d (XGBoost + Logistic скрининг, h6_off05_target_exhausted)
- Обновлены выводы (пункт 26), открытые вопросы (5.0d закрыт)
- wiki/index.md: обновлён охват fractal-stop-research до 5.0d (20 reports)
- Новый отчёт: docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md
> Parse last 5 entries: `grep "^## \[" wiki/log.md | tail -5`

## [2026-06-23] ingest | Stage 5.0c cross-target replication rerun
- Обновлён research/fractal-stop-research.md: добавлен Stage 5.0c (FAIL, multi-seed, Transformer переобучение)
- Обновлены выводы (пункты 22-25) и открытые вопросы (5.0c закрыт, 5.0d как следующий шаг)
- wiki/index.md: обновлён охват fractal-stop-research до 5.0c (19 reports)
- Новый отчёт: docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md
> Parse last 5 entries: `grep "^## \[" wiki/log.md | tail -5`

## [2026-06-17] ingest | Stage 5.0 Transformer Breach Holdout synced into wiki
- Added coverage for `docs/reports/2026-06-17-stage5-transformer-breach.md`.
- Updated `wiki/research/fractal-stop-research.md` with Stage 5.0 full results.
- Transformer (d_model=64, 40 эпох) holdout AUC 0.6018 vs XGBoost 0.6524 — FAIL.
- All 5 feature profiles trail XGBoost. Transformer also worse in low-risk zone (lift_30 0.766 vs 0.620).
- no_time profile AUC=0.4987 — below random without time features.
- Methodological risk: features not scaled for neural net (price in hundreds/thousands, others ~0..1). Conclusion refers to current implementation and normalization.
- Added conclusions 15-17: 5 stages failed, models reached ceiling. Formulation softened per methodological risk.
- Updated open questions: Transformer question answered, trailing question answered.
- Updated `wiki/index.md` coverage (11 reports, stages 1-5.0).

## [2026-06-15] ingest | Stage 4.6 clean candidate-cycle synced into wiki (ext to 2026)
- Added coverage for `docs/reports/2026-06-15-stage4_6-clean-candidate-cycle.md`.
- Updated `wiki/research/fractal-stop-research.md` with Stage 4.6 extended results.
- trail_atr_0_2: val_select 2019-2022 PF=2.041, BS_p05=1.618, conc=0.434 — PASS.
- Val_eval 2023-2026 (Nero.csv): PF=0.897 — FAIL. Breach model ≤2016 doesn't generalize.
- Permutation test: exit-policy dominates breach signal in selection protocol.
- Updated `wiki/index.md` coverage.

## [2026-06-15] ingest | Stage 4.5 exit mechanics synced into wiki
- Added coverage for `docs/reports/2026-06-15-stage4_5-exit-mechanics.md`.
- Updated `wiki/research/fractal-stop-research.md` with Stage 4.5 section.
- trail_atr_0_2: PF=1.831, BS_p05=1.462 — first diagnostic result warranting clean candidate-cycle.
- Breakeven kills PF (0.717); partial exit marginal improvement (1.051).
- Spread 0.40: trail_atr_0_2 PF=1.501 — passes cost stress.
- Updated `wiki/index.md` coverage.

## [2026-06-15] ingest | Stage 5.0-prep diagnostics synced into wiki
- Added coverage for `docs/reports/2026-06-15-stage5-prep-diagnostics.md`.
- Updated `wiki/research/fractal-stop-research.md` with Stage 5.0-prep section.
- Feature ablation: time_only AUC=0.6286 beats no_time AUC=0.6113 — calendar risk significant.
- AUC→PF sensitivity: gate PF>1.15 at alpha=0.1 (AUC=0.8442), required uplift +1768 bp from baseline 0.6674.
- Updated `wiki/index.md` coverage for fractal-stop research.

## [2026-06-15] ingest | Stage 4.4 diagnostic micro-check synced into wiki
- Added coverage for `docs/reports/2026-06-15-stage4_4-micro-check.md`.
- Updated `wiki/research/fractal-stop-research.md` with Stage 4.4 section.
- Recorded key findings: fixed TP (R=0.7) not worse than fav-based TP, breach-only unprofitable, fav needed as filter not TP price.
- Updated `wiki/index.md` coverage for fractal-stop research.

## [2026-06-11] update | Fractal Stop Stage 4 synced into wiki
- Updated `wiki/research/fractal-stop-research.md` after reading `docs/reports/2026-06-11-stage4-trade-xgboost.md`.
- Recorded Stage 4 verdict: XGBoost breach + RF fav does not pass validation trading gates; winner `sell_H6_off05` PF=1.106 with BS_p05=0.923 is not statistically significant.
- Updated `wiki/index.md` coverage from Stage 1-3.x to Stage 1-4.

## [2026-06-11] update | Fractal Stop Stage 3.x synced into wiki
- Updated `wiki/research/fractal-stop-research.md` after `docs/reports/2026-06-10-feature-profiles-stage3.md` was extended with Stage 3.1 ablation and Stage 3.2 XGBoost results.
- Recorded that Stage 3.1 isolated time features as the main RF uplift source.
- Recorded that XGBoost `base_raw_plus_time` is the preferred simple candidate for Stage 4 validation-only trading simulation.
- Updated `wiki/index.md` summary for the Fractal Stop research line.

## [2026-06-10] update | Fractal Stop Stage 2 oracle synced into wiki
- Updated `wiki/research/fractal-stop-research.md` after oracle diagnostics were added to `docs/reports/2026-06-10-fractal-stop-fav-stage2.md`.
- Recorded that RF Stage 2 remains FAIL, but oracle shows a high diagnostic ceiling for the mechanics.
- Reframed the next step from "stop research" to Stage 3: improve breach classifier and features.

## [2026-06-10] ingest | Fractal Stop Breach Stage 1 synced into wiki
- Added coverage for `docs/reports/2026-06-10-fractal-stop-breach-stage1.md`.
- Created `wiki/research/fractal-stop-research.md`.
- Recorded Stage 1 verdict: breach signal confirmed on validation and frozen test, but no trading PASS yet.
- Recorded Stage 2 caveat: trading layer must prove PnL/PF with costs and cannot use zero-spread as PASS.

## [2026-05-21] ingest | Direct direction improvement synced into wiki
- Added coverage for `docs/reports/2026-05-15-direct-direction-improvement.md`.
- Updated `wiki/research/execution-tracks-reconciliation-plus-audit.md` with §20 Direct Direction Improvement.
- Updated `wiki/research/execution-tracks-overview.md` from 39 to 40 reports and recorded the open SELL-side risk.
- Updated `wiki/index.md` report counts and coverage range for the reconciliation/candidate-source track.

## [2026-05-14] ingest | Entry path candidate-source audit
- Added `docs/reports/2026-05-14-entry-path-all-rows-ranking.md`.
- Updated `wiki/research/execution-tracks.md` with signal-only ablation and all-rows ranking result.
- Recorded verdict: all-rows ranking with `fractal0.direction` is rejected as a production path.
- Next research step: causal surrogate for `label_all().signal`.

## [2026-05-06] update | live-safe system tracker
- Added an Audit Tracker to `docs/reports/2026-05-05-live-safe-ml-audit.md`.
- Synced `wiki/research/execution-tracks.md` with the current follow-up order:
  focus `entry_path_v1_live_safe` first, then revisit quantile, keep take/skip
  paused unless a new live-safe hypothesis appears.
- Updated `entry_path_v1_live_safe` note after exporter support for `B` and
  `B_no_path6`; remaining question is rule-family stability, not export.
- Recorded decision: freeze `A` as the conservative live-safe baseline because
  it is simplest and repeated in `3 / 5` seeds.
- Recorded quantile follow-up after baseline `A`: n-boost remains
  `gate_fail` on stability, so quantile stays research-only.
- Added follow-up audit for `entry_path_v1_live_safe + A`: rule-family is
  robust with per-seed validation thresholds, but exact seed-42 threshold does
  not transfer across seed score scales.

## [2026-05-05] update | Take/skip live-safe baseline probe
- Added `live_safe_baseline_seq50` result to `wiki/research/execution-tracks.md`
- Recorded that direct take/skip rebuild without `predict`, `ret_dir_atr_lag1`,
  `ret_*`, `fav_*`, `adv_*` produced no validation winner
- Best observed validation PF was 1.5178 on only 3 trades; verdict `reject`
- Added follow-up note: MT-origin `Up/Dn` in `Nero.csv` are treated as live-safe
  accumulated `lib_PIC` state; `live_safe_path_seq50` is planned for remote
  server execution because local feature construction is too slow
- Added source-audit table to the canonical report: Python `predict`, `ret_*`,
  `fav_*`, `adv_*`, and `ret_dir_atr_lag1` are future-derived; MT-origin
  `Up/Dn` is treated separately
- Updated with server result: `live_safe_path_seq50` verdict `reject`, best
  validation PF 0.9893, no validation winner
- Updated with server result: `live_safe_geometry_seq50` verdict `reject`,
  best validation PF 0.5726, no validation winner
- Kept `wiki/index.md` coverage at 32 reports because the canonical report remained `2026-05-05-live-safe-ml-audit.md`

## [2026-05-05] update | Entry path v1 quantile over live-safe baseline
- Repeated `entry_path_v1_quantile` over the new `entry_path_v1_live_safe` baseline.
- Updated `wiki/research/execution-tracks.md`:
  - sequential PF > 2.0 for 4/5 seeds
  - one seed selected 0 sequential trades
  - n-boost `lb_gt_m_q40`: frozen test 35 trades, PF 32.4125
  - gate failed on stability: `same_winner_ratio=0.60 < 0.80`
- Kept `wiki/index.md` coverage at 32 reports because the canonical report remained `2026-05-05-live-safe-ml-audit.md`

## [2026-05-05] ingest | Entry path v1 live-safe retrain synced into wiki
- Extended report `docs/reports/2026-05-05-live-safe-ml-audit.md`
- Updated `wiki/research/execution-tracks.md` with `entry_path_v1_live_safe`:
  - removed `ret_dir_atr_lag1` from the new built-in profile
  - validation winner PF 2.8881
  - frozen test PF 3.6567
  - sequential test 25 trades, PF 2.3419
- Kept `wiki/index.md` coverage at 32 reports after merging the separate retrain report into the audit report

## [2026-05-05] update | Entry path v1 live-safe multi-seed follow-up
- Repeated retrain for seeds `7`, `17`, `42`, `77`, `123`
- Updated `wiki/research/execution-tracks.md`:
  - median sequential PF 2.3419
  - min sequential PF 1.5171, max 4.5985
  - PF > 2.0 for 3/5 seeds
  - PF <= 1.0 for 0/5 seeds
- Recorded exporter limitation: `A` supported, `B` / `B_no_path6` not yet supported

## [2026-04-09] bootstrap | Initial wiki structure created
- Created wiki/wiki.py (generate/verify tool)
- Created wiki/WIKI_index.md (552 files tracked)
- Created wiki/index.md (catalog of wiki pages)
- Created wiki/log.md (this file)

## [2026-04-09] ingest | First bootstrap ingest: all 14 reports from docs/reports/
- Ingested 14 reports (2026-04-01 — 2026-04-09)
- Created wiki/research/signal-quality-research.md (synthesis of 7 signal quality reports)
- Created wiki/research/execution-tracks.md (synthesis of 7 execution track reports)
- Created wiki/concepts/signal-archetypes.md (key concept: bimodal 64/36 structure)
- Updated wiki/index.md with new pages
- Deleted wiki/LLM Wiki_method.md and wiki/wiki_index_method.md (design inputs, no longer needed)
- Updated MODULE_INDEX.md (+31 modules)

## [2026-04-10] ingest | Refresh execution tracks with latest reports
- Re-read all execution-track reports from 2026-04-08 onward
- Updated wiki/research/execution-tracks.md to include:
  - MT4 confirmation of frozen entry_path winner (2026-04-09)
  - quantile layer for entry_path_v1 (2026-04-10)
- Updated wiki/index.md coverage from 7 to 9 reports
- Regenerated wiki/REPO_integrity.md

## [2026-04-11] ingest | Quantile robustness stage synced into wiki
- Added report `docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md`
- Updated `wiki/research/execution-tracks.md` with multi-seed robustness verdict:
  - `same_rule_count = 5`
  - `negative_year_slices = 0`
  - final verdict `go_mt4`
- Updated `wiki/index.md` coverage from 9 to 10 reports
- Regenerated `wiki/REPO_integrity.md`

## [2026-04-11] ingest | Quantile MT4 parity stage synced into wiki
- Added report `docs/reports/2026-04-11-entry-path-v1-quantile-mt4-parity.md`
- Updated `wiki/research/execution-tracks.md` with quantile MT4 parity verdict:
  - exporter dedupe fix `keep='last'`
  - canonical export `8872` rows / `8` active signals
  - MT4 result `PF=58.88`, `7W/1L`, `DD=2.85%`
  - reconciliation artifact `ML/reports/entry_path_v1_quantile_mt4_reconciliation.csv`
- Updated `wiki/index.md` coverage from 10 to 11 reports
- Regenerated `wiki/REPO_integrity.md`

## [2026-04-12] ingest | Quantile status decision + TB verdict synced into wiki
- Added report `docs/reports/2026-04-12-quantile-status-decision.md` (production parallel mode verdict для quantile-layer)
- Added report `docs/reports/2026-04-12-tb-verdict.md` (TB gate_fail, не production)
- Updated `wiki/research/execution-tracks.md`:
  - new section "Quantile Status Decision (04-12)" с details про n-boost gate (PF=8.18, win_rate=0.8125), MT4 parity 20/20, 4 устранённых бага pipeline
  - new section "MT4 Verdict (04-12)" под TB-трек: fixed simulator bug (`int(outcome)` на float-лейблах), honest test PF=1.28, gate fail по PF и negative years 2023/2026
  - обновлена сравнительная таблица треков: quantile → production parallel mode, TB → gate fail
  - обновлены открытые вопросы (composition, forward validation, TB regime shift)
- Updated `wiki/index.md` coverage from 11 to 13 reports
- Header `execution-tracks.md`: `last_updated: 2026-04-12`, `sources: 13`
- Regenerated `wiki/REPO_integrity.md`

## [2026-04-13] audit | TB float-label convention audit completed
- Added report `docs/reports/2026-04-13-label-convention-audit.md`
- Added audit artifacts:
  - `ML/reports/label_convention_audit.md`
  - `ML/reports/label_convention_audit_inventory.csv`
- Fixed two post-verdict TB analytics bugs:
  - `ML/tb_signal_logic.py`: timeout no longer counted as loss via `~win_mask`
  - `ML/threshold_analysis.py`: timeout no longer counted as loss via `n_trades - wins`
- Added permanent guards: `tests/test_tb_label_invariants.py`
- Additional frozen rerun against canonical main-tree artifacts matched `2026-04-12` exactly:
  - validation: `28 / 16 / 4 / 2`, `PF=4.333333333333333`
  - test: `69 / 29 / 23 / 5`, `PF=1.2777777777777777`
- Conclusion: audit fixes did not change historical TB verdict

## [2026-04-13] ingest | Quantile × fav composition verdict synced into wiki
- Added report `docs/reports/2026-04-13-quantile-fav-composition.md`
- Updated `wiki/research/execution-tracks.md`:
  - new section for composition verdict
  - updated comparison table with `quantile × fav_3_vs_12`
  - final verdict corrected from initial source-mismatch `INCONCLUSIVE` to honest `gate_fail`
  - added note about rebuilt aligned `updn` source and 2023 negative yearly slice
- Updated `wiki/index.md` coverage from 13 to 14 reports
- Header `execution-tracks.md`: `last_updated: 2026-04-13`, `sources: 14`

## [2026-04-13] ingest | Fav 3 vs 12 standalone verdict synced into wiki
- Added report `docs/reports/2026-04-13-fav-3-vs-12-standalone.md`
- Updated `wiki/research/execution-tracks.md`:
  - corrected composition subsection header to final closed status
  - added standalone `fav_3_vs_12` verdict section
  - updated comparison table with standalone rejection
- Updated `wiki/index.md` coverage from 14 to 15 reports
- Header `execution-tracks.md`: `last_updated: 2026-04-13`, `sources: 15`

## [2026-04-13] ingest | PF uplift discovery synced into wiki
- Added report `docs/reports/2026-04-13-pf-uplift-discovery.md`
- Added 3 skeleton plans: `docs/superpowers/plans/2026-04-13-{ny-session-filter,early-timeout-bar12,pred-adv-cap}.md`
- Added artifacts: `ML/reports/pf_uplift_discovery/` (trade_enriched.csv, 6 probe JSON, regime_crosstab.csv, baseline_numbers.json)
- Updated `wiki/research/execution-tracks.md`:
  - added "PF Uplift Discovery (04-13)" section with probe results table and path-dep findings
  - updated open questions with PF uplift реализация item
- Updated `wiki/index.md` coverage from 16 to 17 reports
- Header `execution-tracks.md`: `last_updated: 2026-04-13`, `sources: 17`
- Verdict: 3 STRONG hypotheses shortlisted (NY session +12.1 PF, early timeout bar=12 +5.55 PF, pred_adv12 cap +4.57 PF)

## [2026-04-13] ingest | Quantile forward validation scaffold synced into wiki
- Added report `docs/reports/2026-04-13-quantile-forward-validation.md`
- Added benchmark `ML/benchmark_quantile_forward_validation.py`
- Current operational verdict: `watch / no_forward_data`
- Updated `wiki/research/execution-tracks.md`:
  - added forward validation scaffold section
  - clarified that historical test was not reused as forward data
  - updated comparison table and open question for strictly-forward prediction CSV
- Updated `wiki/index.md` coverage from 15 to 16 reports
- Header `execution-tracks.md`: `last_updated: 2026-04-13`, `sources: 16`

## [2026-04-18] ingest | Take/skip frequency follow-up synced into wiki
- Added report `docs/reports/2026-04-18-take-skip-frequency-followup.md`
- Updated `wiki/research/execution-tracks.md`:
  - added take/skip v2 frequency follow-up section
  - captured split between `quality-first` and `frequency-first`
  - recorded practical trade-off: `8.2 -> 19.2` trades/year on test at the cost of one negative year slice
- Updated `wiki/index.md` coverage from 17 to 18 reports
- Header `execution-tracks.md`: `last_updated: 2026-04-18`, `sources: 18`

## [2026-04-18] ingest | Anchored frequency refinement synced into wiki
- Re-read `docs/reports/2026-04-18-take-skip-frequency-followup.md` after follow-up refinement
- Updated `wiki/research/execution-tracks.md`:
  - added `anchor-expansion` as the main frequent candidate
  - corrected frequent-mode conclusion: raw `frequency-first` is exploratory, anchored mode is the better frozen candidate
- No new report added; synthesis updated in place

## [2026-04-18] ingest | Anchored sweet-spot refinement synced into wiki
- Re-read `docs/reports/2026-04-18-take-skip-frequency-followup.md` after narrow `16%–20%` frozen sweep
- Updated `wiki/research/execution-tracks.md`:
  - added `top_k 17%` as current best anchored sweet spot
  - recorded improved frequent compromise: `test PF=13.12`, `trades_per_year=16.4`, `negative_year_slices=0`

## [2026-04-18] ingest | Take/skip v2 rule artifacts synced into wiki
- Re-read `docs/reports/2026-04-18-take-skip-frequency-followup.md` after packaging frozen rule artifacts
- Updated `wiki/research/execution-tracks.md`:
  - added canonical paths for quality and frequent frozen rules
  - clarified that `take_24_x8 + top_k 17%` is the current packaged frequent candidate

## [2026-04-18] ingest | Take/skip rule consumer synced into wiki
- Added report `docs/reports/2026-04-18-take-skip-rule-consumer.md`
- Updated `wiki/research/execution-tracks.md`:
  - added consumer-layer subsection for take/skip v2
  - recorded that frozen quality/frequency rules are now executable through a dedicated CLI
  - noted optional full-series expansion via `--base-csv`

## [2026-04-18] ingest | MT4 trailing-stop execution synced into wiki
- Added report `docs/reports/2026-04-18-mt4-trailing-stop-execution.md`
- Updated `wiki/research/execution-tracks.md`:
  - added MT4 direct trailing-stop execution subsection for `iSignal=3`
  - recorded new runtime parameters `ML_ExitMode` and `ML_TrailATR`
  - clarified that timeout path remains default, while trailing-stop is a separate explicit mode
- Updated `wiki/index.md` coverage from 19 to 20 reports

## [2026-04-19] ingest | Execution policy v2 synced into wiki
- Added report `docs/reports/2026-04-19-execution-policy-v2.md`
- Added benchmark `ML/benchmark_execution_policy_v2.py` and tests

## [2026-04-20] ingest | take_skip lib_PIC feature training synced into wiki
- Added report `docs/reports/2026-04-20-take-skip-lib-pic-feature-training.md`
- Updated `wiki/research/execution-tracks.md`:
  - added dual-stream `take_skip_v2` feature training verdict
  - recorded 9/9 rejects, `PF > 1` rows only at very low trade frequency
  - recorded next step: controlled ablation against the original baseline contract
- Updated `wiki/index.md` coverage from 22 to 23 reports
- Updated `wiki/research/execution-tracks.md`:
  - added Python + MT4 execution policy v2 subsection
  - recorded `ML_TakeProfitATR` as a broker-side TP parameter for direct ML mode
  - captured final frequent candidate: `ML_TrailATR=8`, `ML_TakeProfitATR=0`
  - captured cautious frequent alternative: `ML_TrailATR=6`, `ML_TakeProfitATR=0`
- Updated `wiki/index.md` coverage from 20 to 21 reports

## [2026-04-20] ingest | take_skip lib_PIC external selection synced into wiki
- Added report `docs/reports/2026-04-20-take-skip-lib-pic-selection.md`
- Added benchmark `ML/benchmark_take_skip_lib_pic_selection.py` and tests
- Updated `wiki/research/execution-tracks.md`:
  - recorded that `lib_PIC` filters did not replace the current quality/frequency rules
  - captured feature-frequency candidate: `pic_path_win_proxy24_share_w20 >= 0.25`, test `PF=5.30`, `trades_per_year=14.8`, `negative_year_slices=0`
  - clarified next step: use `lib_PIC` features inside a new training track rather than making a more complex external selector
- Updated `wiki/index.md` coverage from 21 to 22 reports

## [2026-04-20] ingest | take_skip original-contour feature ablation synced into wiki
- Added report `docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md`
- Added runner `ML/run_take_skip_original_contour_feature_matrix.py` and tests
- Updated `wiki/research/execution-tracks.md`:
  - recorded that the old single-tensor contour was reproduced with `input_features=539`
  - captured `original_plus_path_seq50` as practical candidate: `take_24_x8`, `prob>=0.60`, test `PF=38.78`, `trades_per_year=10.2`, negative years `0`
  - recorded that geometry candidates are not promoted because frozen test frequency falls to `4.8` trades/year
- Updated `wiki/index.md` coverage from 23 to 24 reports

## [2026-04-20] ingest | original_plus_path MT4 confirmation synced into wiki
- Updated report `docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md`
- Updated `wiki/research/execution-tracks.md`:
  - recorded MT4 confirmation for `original_plus_path_seq50`
  - captured `TrailATR=8, TP=0`: `29` trades, net `22294.65`, PF `23.79`, relative DD `14.74%`
  - captured cautious `TrailATR=8, TP=12`: `29` trades, net `15873.12`, PF `17.23`, relative DD `6.64%`
  - recorded parity caveat: exported rows can duplicate the same H1 timestamp, while MT4 consumes one direct ML signal per bar time

## [2026-04-22] ingest | signal export parity benchmark synced into wiki
- Added report `docs/reports/2026-04-22-signal-export-parity.md`
- Added benchmark `ML/benchmark_signal_export_parity.py` and tests
- Updated `wiki/research/execution-tracks.md`:
  - recorded that duplicate timestamps are expected because one H1 bar can form multiple different `lib_PIC` peaks/levels
  - captured `original_plus_path_20260420`: `51` nonzero rows, `37` unique `time+signal`, `29` MT4 opened trades
  - clarified that DATA should not be collapsed; runtime `time;signal` is coarser than DATA row identity
- Updated `wiki/index.md` coverage from 24 to 25 reports

## [2026-04-24] ingest | cross-instrument robustness check synced into wiki
- Added report `docs/reports/2026-04-24-cross-instrument-robustness-check.md`
- Updated `wiki/research/execution-tracks.md`:
  - recorded explicit split between `provider_drift_baseline` and `cross_instrument_transfer`
  - captured that `XAUUSD MetaQuotes -> Alpari` stayed `provider_stable` for all three systems
  - captured transfer matrix across `XAGUSD/EURUSD/GBPUSD/USDCHF`
  - recorded breadth conclusion: `frequency` is most robust by transfer width, `USDCHF` is strongest positive case, `EURUSD` is strongest negative case
- Updated `wiki/index.md` coverage from 25 to 26 reports

## [2026-04-24] ingest | entry_path cross-instrument robustness synced into wiki
- Added report `docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md`
- Updated `wiki/research/execution-tracks.md`:
  - added fixed-hold `entry_path` transfer subsection with `hold_24_backstop_50`
  - recorded `XAUUSD MetaQuotes -> Alpari` as `provider_stable` for both `entry_path_v1` and `entry_path_v1_quantile`
  - captured transfer matrix across `EURUSD/GBPUSD/USDCHF/XAGUSD`
  - recorded breadth conclusion: quantile variant is more robust than baseline `entry_path_v1`
- Updated `wiki/index.md` coverage from 26 to 27 reports

## [2026-04-24] ingest | system correlation and portfolio check synced into wiki
- Added report `docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`
- Added benchmark `ML/benchmark_system_correlation.py` and tests
- Updated `wiki/research/execution-tracks.md`:
  - added portfolio-level subsection for pairwise system correlation on `XAUUSD`
  - recorded explicit split between `redundant`, `complementary` and `partially_overlapping` pairs
  - captured main redundant pair: `frequency × original_plus_path`
  - captured main complementary line: `quality` / `original_plus_path` versus `entry_path` systems
- Updated `wiki/index.md` coverage from 27 to 28 reports

## [2026-04-27] docs | documentation architecture compacted
- Added `docs/README.md` as the documentation entry map.
- Added `docs/DOCS_ARCHITECTURE.md` as the source-of-truth matrix.
- Shortened `CONTEXT_HANDOFF.md` to current baton only.
- Converted `CLAUDE.md` into a thin Claude Code adapter to `AGENTS.md`.
- Updated `wiki/index.md` to point agents to the documentation architecture contract.

## [2026-04-27] docs | documentation map merged
- Merged `docs/DOCS_ARCHITECTURE.md` into `docs/README.md` to keep one documentation entrypoint.
- Updated agent and wiki references to use `docs/README.md`.

## [2026-04-27] docs | docs readme scoped to docs directory
- Scoped `docs/README.md` to artifacts inside `docs/`.
- Moved agent/navigation responsibility back to `AGENTS.md`.
- Added explicit `MODULE_INDEX.md` point-read rule to `AGENTS.md`.

## [2026-04-27] ingest | telemetry frequency demo launch synced into wiki
- Added report `docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`.
- Updated `wiki/research/execution-tracks.md`:
  - added `telemetry_frequency_v1` diagnostic launch section;
  - recorded frequency-first rule selection and ATR-sized SL/TP preset;
  - captured MQL reuse decision: extend `lib_ML_Signal.mqh::ML_TRADE()`, keep ticket-level helpers for multi-position, reuse `SERVICE.mqh` where compatible;
  - captured daily reconciliation CLI and required MLP log fields.
- Updated `wiki/index.md` coverage from 28 to 29 reports.

## [2026-04-27] ingest | telemetry frequency demo launch completed
- Updated report `docs/reports/2026-04-27-telemetry-frequency-demo-launch.md` to `Completed`.
- Updated `wiki/research/execution-tracks.md` with final tester proof:
  - `495` expected signals, `468` opened trades;
  - `critical_mismatch_count=0`;
  - broker-side `TakeProfit` / `StopLoss` closes logged via `source=broker_history`;
  - diagnostic contour ready for online demo launch.

## [2026-04-28] ingest | MQL runtime architecture snapshot
- Added report `docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`.
- Updated `wiki/research/execution-tracks.md`:
  - recorded `RECOUNT_HISTORY()` startup warmup for `PIC()` / `F[]`;
  - recorded `POC_SIMPLE()` as part of the atomic `PIC()` step;
  - recorded watcher runtime snapshot window (`--max-runtime-rows 12000`);
  - captured full-vs-12000 parity result (`signal_mismatch_rows=0`, `pred_* <= 3.37e-7`);
  - captured open finding: live `Nero.csv` has `signal=0` and `predict=0`, so diagnostic export cannot produce trades yet.
- Updated `wiki/index.md` coverage from 29 to 30 reports.

## [2026-04-29] save | online causal preprocessing contract
- Updated `wiki/research/execution-tracks.md` with the new online watcher contract:
  - raw `runtime_input_snapshot.csv` is no longer fed directly to inference;
  - `runtime_input_preprocessed.csv` applies fractal sorting and rowwise normalization;
  - diagnostic direction now refers to `fractal0.direction` after sorting.

## [2026-04-29] save | online inference contract guard
- Updated `wiki/research/execution-tracks.md` after audit of online/test parity:
  - recorded that legacy `original_baseline` used future-derived row features as model input;
  - recorded watcher contract guard and `--allow-unsafe-future-features` override;
  - clarified that unsafe override is only mechanical chain diagnostics, not ML-correct online validation.

## [2026-04-29] ingest | online inference contract hardening report
- Added `docs/reports/2026-04-29-online-inference-contract-hardening.md`.
- Updated `wiki/research/execution-tracks.md` and `wiki/index.md` coverage from 30 to 31 reports.

## [2026-05-05] ingest | live-safe ML audit
- Added `docs/reports/2026-05-05-live-safe-ml-audit.md`.
- Updated `wiki/research/execution-tracks.md`:
  - recorded legacy PF vs live-safe verdict for five profitable systems;
  - marked all five audited systems as `FAIL`;
  - recorded `ret_dir_atr_lag1` as future-derived after source/timing audit;
  - recorded live-safe `entry_path_v1` rebuild/retrain as the next blocker.
- Updated `wiki/index.md` coverage from 31 to 32 reports.

## [2026-05-07] ingest | entry path live-safe CPU baseline
- Added wiki coverage for:
  - `docs/reports/2026-05-07-cpu-gpu-reproducibility.md`;
  - `docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md`;
  - `docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md`.
- Updated `wiki/research/execution-tracks.md`:
  - recorded CPU-only production retrain decision;
  - recorded `entry_path_v1_live_safe + A @ 7.5%` as the main live-safe candidate;
  - recorded `entry_path_v1_quantile` as research-only over the CPU baseline;
  - recorded final take/skip `geometry_path` reject.
- Updated `wiki/index.md` coverage from 32 to 35 reports.

## [2026-05-11] save | online BackTest mode clarification
- Updated `wiki/research/execution-tracks.md` to record the operational split:
  - online/forward diagnostic uses `BackTest=0`;
  - Strategy Tester uses `BackTest=2` to select the current telemetry row.

## [2026-05-11] save | M5 online diagnostic event log
- Updated `wiki/research/execution-tracks.md`:
  - recorded `ML_MaxPositions=20` for the long-run M5 diagnostic;
  - recorded `MT/MQL4/Files/ml_trade_events.csv` as the detailed online/test
    trade-event log for price, spread, slippage, commission and swap analysis.

## [2026-05-13] ingest | online/tester execution reconciliation

- Ingested `docs/reports/2026-05-12-online-tester-execution-reconciliation.md`
  into `wiki/research/execution-tracks.md`.
- Updated `wiki/index.md` coverage from 36 to 37 execution-track reports.
- Linked `docs/ML/online_tester_reconciliation.py.md` as the canonical
  instruction for repeat online/tester reconciliation runs.

## [2026-05-14] ingest | entry path causal surrogate

- Added `docs/reports/2026-05-14-entry-path-causal-surrogate.md`.
- Updated `wiki/research/execution-tracks.md`:
  - recorded causal surrogate validation/test/sequential metrics;
  - recorded low active precision and high active recall;
  - marked the surrogate as research baseline, not production-rule.
- Updated `wiki/index.md` coverage for the new report.

## [2026-05-14] ingest | entry path direct bar model

- Added `docs/reports/2026-05-14-entry-path-direct-bar-model.md`.
- Updated `wiki/research/execution-tracks.md`:
  - recorded direct `BUY/SELL/SKIP` validation/test/sequential metrics;
  - recorded that offline `signal` is not used as gate;
  - marked direct score+direction as the best next research direction, not
    production-ready yet.
- Updated `wiki/index.md` coverage from 39 to 40 execution-track reports.

## 2026-05-18 - Ingest direct-direction audit
- Added `wiki/research/execution-tracks-direct-direction-audit.md` covering `docs/reports/2026-05-15-direct-direction-improvement.md` and `docs/audit/2026-05-18-codex-direct-direction-chain-audit.md`.
- Updated `wiki/index.md` and `wiki/research/execution-tracks-overview.md` coverage from 39/40 to 41 execution-track reports.
2026-05-21 23:00 — Ingest: added Direct Direction Rebuild (§22) to execution-tracks-direct-direction-audit.md; updated index (3 reports). Ran wiki.py generate.
[2026-05-23] Ingest: updated execution-tracks-take-skip-v2 (+v1 matrix, +v2 handoff, 04-17 reports), execution-tracks-direct-direction-audit (+transformer encoder direction, 05-21 report). Updated wiki/index.md, execution-tracks-overview.md.
### 2026-06-10: Stage 2 Ingest
- Updated wiki/research/fractal-stop-research.md: добавлены результаты Stage 2 (FAIL), статус changed from active to completed
- Updated wiki/index.md: sources count 1->2, status completed
### 2026-06-10: Save concept — folded-mov-channels
- Created wiki/concepts/folded-mov-channels.md: свёртка 10 up/dn → 5 mov_h, границы применимости (не для breach)
- Updated wiki/index.md: added to Concepts table
- Sources: EDA нормализации (2026-06-10), Stage 3 feature profiles
### 2026-06-11: Ingest Stage 3 feature profiles
- Updated `docs/reports/2026-06-10-feature-profiles-stage3.md`: clarified that `relative_geometry` is a profile-level winner, density/time are not isolated, `parse_fractal()` empty-fractal artifact does not affect Stage 3, and Stage 3.1 must precede XGBoost.
- Updated `CONTEXT_HANDOFF.md`: next step changed from immediate XGBoost to Stage 3.1 ablation.
- Updated `wiki/research/fractal-stop-research.md` and `wiki/index.md`: coverage Stage 1-3, 3 reports.
### 2026-06-11: Update concept — folded-mov-channels
- Updated `wiki/concepts/folded-mov-channels.md`: documented the decision to keep `Nero.csv` in the 23-field format, compute `mov_h` in Python only when needed, avoid `lib_PIC.mqh` re-export/relabel work, and keep current priority on `relative_geometry`.
### 2026-06-12: Update Stage 4 report with Stage 4.1 controls
### 2026-07-02: Ingest Next Open Entry Up/Dn Foundation
- Updated `docs/reports/2026-07-02-next-open-entry-updn-foundation.md`: clarified `DIAGNOSTIC_ONLY` vs `NO_SIGNAL_FOUND`, explicit all-horizon/all-split runner gate, next-available-open delay distribution, and the difference between weak amplitude ranking and absent directional `entry_log_ratio` signal.
- Updated `ML/baseline/benchmark_next_open_entry_updn_foundation.py`, `ML/reports/next_open_entry_updn_foundation.json`, and `tests/test_next_open_entry_updn_foundation.py`: separated artifact status from runner status and made gate evaluation cover primary/disclosure splits and all declared horizons.
- Fixed `ML/baseline/analyze_regression_updn_already_moved_audit.py`: removed forbidden ML import of `processing.label_signals.parse_fractal` and kept only local `fractal0` field extraction needed by the audit.
- Updated `CHANGELOG.md`, `wiki/research/fractal-stop-research.md`, and `wiki/index.md`: recorded that next-open target retraining from actual `entry_open` still yields `NO_SIGNAL_FOUND` for directional ranking while leaving fractal-price entry mechanics open.

### 2026-07-04: Ingest Entry-Based Next Open Closeout
- Added `docs/reports/2026-07-04-entry-based-next-open-closeout.md`.
- Updated `wiki/research/fractal-stop-research.md`: recorded closeout verdict `PIVOT`, weak direction (`all100 / xgboost_depth3 / H24 = 0.0533 -> 0.0335`), strong amplitude trace (`nearest_k80 / hist_gradient_boosting / entry_up H3 = 0.3414 -> 0.4449`), and the next-step shift toward amplitude / movement-regime targets.
- Post-review closeout sync: recorded that `all100` is control-only and cannot produce `CONTINUE`, candidate-only direction is weaker (`nearest_k60 / xgboost_depth5 / H12 = 0.0373 -> 0.0274`), `simple_trade` is unstable between `val_select` and `val_eval`, and zero `fractal0_updn` add-on features were removed from the closeout runner.
- Updated `wiki/index.md`: Fractal Stop coverage now extends through 2026-07-04 closeout, 39 report updates.

### 2026-07-06: Ingest Entry-Based Powerful Tabular Models
- Added `docs/reports/2026-07-06-entry-based-powerful-tabular-models.md`.
- Updated `wiki/research/fractal-stop-research.md`: recorded the stronger tabular model check, direction failure (`nearest_k80 / hist_gradient_boosting_strong / H12 = 0.0519 -> -0.0009`), amplitude confirmation (`nearest_k60 / hist_gradient_boosting_strong / entry_up H3 = 0.3412 -> 0.4419`), and verdict `PIVOT_AMPLITUDE`.
- Post-review sync: recorded that best-by-`val_eval` direction (`corridor_5atr / extra_trees_regressor / H12 = 0.0475`) has weak `val_select=0.0042` and is hindsight disclosure only.
- Updated `wiki/index.md`: Fractal Stop coverage now extends through 2026-07-06 powerful tabular capacity check, 40 report updates.

- Updated existing `docs/reports/2026-06-11-stage4-trade-xgboost.md` instead of creating a new report.
- Updated `wiki/research/fractal-stop-research.md`: added Stage 4.1 XGBoost-fav and combined breach results, corrected Stage 4 yearly winner table, and marked quick controls rejected.
- Updated `wiki/index.md`: coverage wording changed to Stage 1-4.1.
### 2026-06-12: Ingest Stage 4.2 diagnostic recalc
- Updated `wiki/research/fractal-stop-research.md`: added Stage 4.2 corrected diagnostic recalc, PF 1.015, BS_p05 0.837, 0/500 permutation result for fixed inherited rule, and retained `DIAGNOSTIC_ONLY`/FAIL trading verdict.
- Updated `wiki/index.md`: coverage wording changed to Stage 1-4.2.
### 2026-06-15: Ingest Stage 4.3 diagnostics
- Updated `wiki/research/fractal-stop-research.md`: added Stage 4.3 post-mortem diagnostics, baseline reproduction, loss attribution, fav/breach bucket results, oracle-deviation regimes, and caveat that oracle-attribution categories are not fully implemented against the plan.
- Updated `wiki/index.md`: coverage wording changed to Stage 1-4.3.
### 2026-06-15: Update Stage 4.3 oracle attribution
- Updated `wiki/research/fractal-stop-research.md`: removed the incomplete-attribution caveat after `diagnose_stage4_3.py` was extended with category PnL/yearly/bootstrap; recorded breach false-safe, missed oracle-safe, fav false-accept, overpredict and underpredict category results.
- Updated `wiki/index.md`: Stage 4.3 wording now reflects joint breach-ranking and fav/TP weakness.
### 2026-06-18: Ingest Stage 5.0a feature preflight
- Updated `wiki/research/fractal-stop-research.md`: added Stage 5.0a preflight, clean-controls, `nearest40` anchor contract, relative-price rerun candidates, absolute-price disclosure, and corridor truncation results.
- Updated `wiki/index.md`: coverage wording changed to Stage 1-5.0a.
- Ran `wiki/wiki.py generate`.
### 2026-06-18: Update Stage 5.0a corridor full addendum
- Updated `wiki/research/fractal-stop-research.md`: added honest raw corridor coverage, `corridor_*_full`, distinction between ATR-in-coordinate and ATR-as-row-input, and rerun guidance through `corridor_*_atr_full`.
- Updated `wiki/index.md`: wording now reflects corridor full addendum and rejection of old capped corridor as main rerun candidate.
- Ran `wiki/wiki.py generate`.
### 2026-06-22: Ingest Stage 5.0a A7 audit and Stage 5.0b asinh rerun
- Updated `wiki/research/fractal-stop-research.md`: added Stage 5.0a A7 distribution audit, `asinh` vs `piecewise_tail`, `price/ATR` diagnostics, Stage 5.0b sell/buy results, buy loader fix, and `all100_absolute_price_atr_scaled_time_asinh` as next narrow candidate.
- Updated `wiki/index.md`: Fractal Stop coverage now extends to Stage 5.0b and records that Transformer did not beat XGBoost on sell or buy.
- Sources: `docs/reports/2026-06-20-stage5_0a-feature-distribution-audit.md`, `docs/reports/2026-06-21-stage5_0b-asinh-rerun.md`.
### 2026-06-22: Ingest older uncovered Fractal Stop reports
- Updated `wiki/research/fractal-stop-research.md`: added exact coverage for `2026-06-14-stage4-deep-diagnostics.md`, `2026-06-15-stage4_4-micro-check.md`, `2026-06-15-stage5-prep-diagnostics.md`, and `2026-06-15-walk-forward-diagnostics.md`.
- Added missing synthesis for Stage 4 deep diagnostics and Stage 4.7 walk-forward diagnostics; Stage 4.4 and Stage 5.0-prep were already summarized but lacked exact source coverage.
- Updated `wiki/index.md`: Fractal Stop coverage now records 18 report updates.

### 2026-06-24: Sync Stage 5.1 report refinements
- Updated `CHANGELOG.md`: added Stage 5.1 refinements about `back` CI/yearly consistency, partial structural-premium coverage, `impulse`, and low-N 2026 sell risk.
- Updated `wiki/research/fractal-stop-research.md`: synchronized Stage 5.1 synthesis with the revised report, including `back_val` interpretation, 5/5 yearly drop signs, `time+back` follow-up framing, and `sources: 23`.
- Updated `wiki/index.md`: clarified that `back` is not a replacement for the full structural profile and that `impulse` remains unconfirmed.

### 2026-06-25: Ingest Stage 5.2 time-to-breach regression
- Added `docs/reports/2026-06-25-stage5_2-time-to-breach-regression.md`.
- Updated `wiki/research/fractal-stop-research.md`: added Stage 5.2 target contract, oracle-positive result, full model gate failure, constant-baseline comparison, and censored/ordinal next-step framing.
- Updated `wiki/index.md`: Fractal Stop coverage now extends through Stage 5.2, 25 report updates.

### 2026-06-25: Correct Stage 5.2 interpretation after JSON review
- Updated `docs/reports/2026-06-25-stage5_2-time-to-breach-regression.md`: marked identical profile metrics as likely implementation/model-contract anomaly, disclosed `oracle_binary_pf = inf`, unrealistic oracle trade frequency, and missing prediction arrays.
- Updated `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `wiki/research/fractal-stop-research.md`, and `wiki/index.md`: Stage 5.2 is now framed as an artifact requiring technical post-mortem, not a reliable negative result about time-to-breach itself.

### 2026-06-25: Stage 5.2 root cause found
- Updated `ML/baseline/benchmark_stage5_transformer_breach.py`: Stage 5.2 objective changed from `reg:pseudohubererror` to `reg:squarederror`, `pred_summary` added to regression metrics, oracle gate rejects invalid `oracle_binary_pf = inf` comparison.
- Updated `tests/test_stage5_transformer_breach.py`: added regression tests for objective selection, prediction summaries, and invalid oracle comparison.
- Updated report/changelog/handoff/wiki: old Stage 5.2 JSON is superseded by bugfix and requires full rerun.

### 2026-06-25: Stage 5.2 rerun after bugfix
- Reran `--stage5-2-time-to-breach-regression --stage5-2-workers 8 --stage5-2-xgb-threads 4`; completed `42/42`.
- Updated `docs/reports/2026-06-25-stage5_2-time-to-breach-regression.md`, `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `wiki/research/fractal-stop-research.md`, and `wiki/index.md`.
- Result: time-to-breach ranking exists (`clock_shift_back` sell, `clock_shift_back_impulse` buy), but candidate-gate remains `DIAGNOSTIC_ONLY` due to invalid oracle comparison and MAE worse than constant baseline.

### 2026-06-26: Ingest Stage 5.3 time-to-breach target reformulation
- Added `docs/reports/2026-06-26-stage5_3-time-to-breach-target-reformulation.md`.
- Updated `wiki/research/fractal-stop-research.md`: added Stage 5.3 `fast` bucket finding, binary-baseline deltas, control-only interpretation for `survives_at_least_k`, and Stage 5.4 scope constraints.
- Updated `wiki/index.md`: Fractal Stop coverage now extends through Stage 5.3, 26 report updates.

### 2026-06-29: Sync Stage 5.3 corrected interpretation
- Updated `docs/superpowers/roadmap.md`: moved Stage 5.2/5.3 to closed context and set Stage 5.4 price-coordinate / ATR ablation around fixed `fast` as the next step.
- Updated `CONTEXT_HANDOFF.md`: corrected main comparisons from 14 to 12 unique side/target comparisons.
- Updated `wiki/research/fractal-stop-research.md` and `wiki/index.md`: corrected Stage 5.3 buy interpretation from sign-positive seed count to threshold-passing count (`1/3` seed for delta ≥ 0.02).

### 2026-06-29: Review Stage 5.4 report synchronization
- Updated `docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md`: clarified that the gate evaluates the predeclared primary candidate, not the globally best profile among all diagnostic profiles; fixed secondary/diagnostic wording.
- Updated `CHANGELOG.md` and `CONTEXT_HANDOFF.md`: corrected Stage 5.3 buy seed-count wording and separated Stage 5.3 `TARGET_REFORMULATION_FOUND` from Stage 5.4 `DIAGNOSTIC_ONLY`.
- Updated `wiki/research/fractal-stop-research.md`: added Stage 5.4 synthesis and marked price/ATR ablation as rejected.

### 2026-06-29: Ingest Stage 6.0 review-fix rerun
- Updated `wiki/research/fractal-stop-research.md`: Stage 6.0 supersedes the old H24-only `MODEL_GATE_FAILED` reading; H6 passes model gate but fails trading gate due to `NO_THRESHOLD`.
- Updated `wiki/index.md`: Fractal Stop coverage now records corrected Stage 6.0 `TRADING_GATE_FAILED` outcome.

### 2026-06-30: Ingest Stage 6.2 H12 price action
- Added `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md`.
- Updated `wiki/research/fractal-stop-research.md`: added Stage 6.2 OHLC price-action result, primary `h12_price_action_core` weak standalone signal, failed permutation gate, failed additive delta gate, and narrow rejection scope.
- Updated `wiki/index.md`: Fractal Stop coverage now extends through Stage 6.2, 30 report updates.

### 2026-06-30: Review-fix Stage 6.2 summary aggregation
- Updated `ML/baseline/benchmark_stage6_2_price_action.py`: Stage 6.2 summary now stores per-seed rows, aggregates permutation p-values by median/min/max over seeds, and selects the representative threshold row by median PF.
- Updated Stage 6.2 report/handoff/wiki wording: clarified row-time zero-vector contract, legacy smoke-check scope, top-importance selection rule, per-seed metrics, and weak validation ranking interpretation.
### 2026-07-07: Ingest entry-based sequence Transformer closeout
- Added `docs/reports/2026-07-07-entry-based-fractal-sequence-transformer.md`.
- Updated `wiki/research/fractal-stop-research.md`: sequence Transformer did not rescue `entry-based next open` direction (`0.0539 -> 0.0050`), while amplitude remained stronger (`0.3229 -> 0.3337`).
- Updated `wiki/index.md`: Fractal Stop coverage now includes ordered sequence Transformer and records 41 report updates.

### 2026-07-07: Refine sequence Transformer report after review
- Updated `docs/reports/2026-07-07-entry-based-fractal-sequence-transformer.md`: narrowed the sequence conclusion, strengthened `price_coord_atr` warning treatment, renamed `simple_trade` to post-hoc sanity check, and added required controls for the next amplitude plan.
- Updated `CONTEXT_HANDOFF.md`, `wiki/research/fractal-stop-research.md`, and `wiki/index.md`: clarified that the current result closes only the bounded `entry-based next open` direction branch, not the whole idea of fractal sequence representations.

### 2026-07-07: Ingest entry-based amplitude movement-regime audit
- Added `docs/reports/2026-07-07-entry-based-amplitude-movement-regime.md`.
- Updated `wiki/research/fractal-stop-research.md`: movement-regime target `max(entry_up_H, entry_dn_H)` is strong diagnostically but explained by simple baselines; no complex representation winner and no trading verdict.
- Updated `wiki/index.md`: Fractal Stop coverage now includes amplitude movement-regime audit and records 42 report updates.

### 2026-07-07: Refine amplitude movement-regime audit after review
- Updated `ML/reports/entry_based_amplitude_movement_yearly.csv` and JSON yearly rows: added `profile`, `model_key`, `seed`, `target_family` to each yearly diagnostic row.
- Updated `docs/reports/2026-07-07-entry-based-amplitude-movement-regime.md`: clarified skipped distance-control, feature-audit warning families, target-distribution shift, winner disclosure on 2026, and simple-vs-complex comparison.
- Updated `wiki/research/fractal-stop-research.md` and `wiki/index.md`: clarified that amplitude is explained mainly by `time+ATR`, while `distance_to_level_pre_entry_only` was not a valid completed control.

### 2026-07-08: Ingest direction inside frozen movement contract failure
- Added `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`.
- Updated `wiki/research/fractal-stop-research.md`: direction-inside-mask plan stopped with `ABORT_CONTRACT_FAIL` because `split + time` is not unique in freeze scores and split rows; no direction baselines were trained.
- Updated `wiki/index.md`: Fractal Stop coverage now records 45 report updates and points the next step to row-id repair before repeating direction-inside-mask.

### 2026-07-08: Continue direction inside frozen movement after row-id repair
- Updated `ML/reports/entry_based_movement_filter_freeze_scores.csv`: added `split_row_id` as the stable join key while keeping the frozen movement rule unchanged.
- Updated `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`: final verdict changed from contract abort to `REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME` after the repaired direction run.
- Updated `wiki/research/fractal-stop-research.md` and `wiki/index.md`: recorded that `split + time` duplicates come from multiple entry rows per bar, and direction inside the frozen mask is rejected after repair.

### 2026-07-09: Ingest rich-features direction-inside-mask runner fix
- Added `docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md`.
- Updated `wiki/research/fractal-stop-research.md`: rich-features runner is now wired to real split/freeze inputs; smoke `simple_combined / H3 / entry_log_ratio / extra_trees` produces real metrics and rejects the simple control.
- Updated `wiki/index.md`: Fractal Stop coverage now records 46 report updates and marks the full rich-features grid as still pending.

### 2026-07-09: Ingest rich-features direction-inside-mask full grid
- Updated `docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md`: full grid `240/240` replaces the earlier smoke-only result.
- Updated `wiki/research/fractal-stop-research.md`: recorded `DIRECTION_REPLICATION_REQUIRED` for `nearest_k60 / H3 / entry_log_ratio / extra_trees` with `val_select_inside_mask=0.570170` and `val_eval_inside_mask=0.529056`.
- Updated `wiki/index.md`: Fractal Stop coverage now records 47 report updates and marks the next step as a narrow replication plan, not candidate promotion.

### 2026-07-10: Ingest narrow direction-inside-mask replication reject
- Added `docs/reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md`.
- Updated `wiki/research/fractal-stop-research.md`: recorded `REJECT_DIRECTION_REPLICATION` for the pre-registered `nearest_k60 / extra_trees / entry_log_ratio` narrow matrix; H3 median `val_eval_inside_mask=0.499080`, only `2/5` seeds reached `>=0.52`, H9 skipped by target preflight.
- Updated `wiki/index.md`: Fractal Stop coverage now records 48 report updates and moves the next branch away from direction-inside-mask toward execution-aware `fractal0_price` mechanics.

### 2026-07-10: Ingest fractal0 price entry mechanics oracle-preflight
- Added `docs/reports/2026-07-10-fractal0-price-entry-mechanics.md`.
- Added `ML/baseline/benchmark_fractal0_price_entry_mechanics.py` and `tests/test_fractal0_price_entry_mechanics.py`.
- Updated `wiki/research/fractal-stop-research.md`: recorded selected `zone_edge / 0.5 ATR / lag 6 / H3 / spread 0.2`, `val_stop favorable_to_adverse_ratio=1.2421`, stress ratio `1.1895`, side contract `PASS`, and failed gate due to `active_years=2 < 3`.
- Updated `wiki/index.md`: Fractal Stop coverage now records 49 report updates and points any continuation to a separate frozen probe-plan.

### 2026-07-20: Review fixes for fractal0 price entry mechanics
- Updated `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`: `ratio_without_best_year` removes the year with best yearly ratio, `research_gate` requires simple-rule comparison, and `audit_side_contract` requires both directions.
- Updated `docs/reports/2026-07-10-fractal0-price-entry-mechanics.md`, `CONTEXT_HANDOFF.md`, `CHANGELOG.md`, `docs/superpowers/roadmap.md`, and module docs with corrected robustness/gate contract.
- Updated `wiki/research/fractal-stop-research.md` metadata to `sources: 49` and recorded the review fixes.

### 2026-07-21: Ingest Fractal0 entry/exit grid diagnostic result
- Added `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`.
- Added `ML/baseline/benchmark_fractal0_entry_exit_grid.py` and `tests/test_fractal0_entry_exit_grid.py`.
- Updated `wiki/research/fractal-stop-research.md`: recorded full `4 x 2 x 48` entry/exit grid, winner `E3_open_pullback_1_0atr / M0_no_mask / X2_ml_opposite_any_p0_55`, `val_eval PF=1.9438`, `BS_p05=1.7601`, stress PF `1.5743`, permutation PASS, and `diagnostic_only` cap from H1 `ambiguous_same_bar_rate=0.2250`.
- Updated `wiki/index.md`: Fractal Stop coverage now records 50 report updates and points next work to execution-refinement with a lower timeframe for fill/exit ordering.

### 2026-07-21: Update Fractal0 entry/exit grid after M5 winner-only ambiguity fix
- Updated `ML/baseline/benchmark_fractal0_entry_exit_grid.py`: added optional M5 `execution_ohlc_path`, fast H1-hour index for execution OHLC, and fixed ambiguity semantics so ML-exit rules do not count hypothetical fixed TP touches.
- Added `ML/reports/fractal0_entry_exit_grid_m5_winner.json`: previous winner only, M5 execution ordering, `val_eval PF=1.9438`, `BS_p05=1.7601`, stress PF `1.5743`, `ambiguous_same_bar_rate=0.0`.
- Updated `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`, `wiki/research/fractal-stop-research.md`, and `wiki/index.md`: old `diagnostic_only` ambiguity cap is marked stale for the ML-exit winner; next step is full rerun or frozen subset with M5 execution contract.

### 2026-07-21: Review fixes for Fractal0 entry/exit grid artifacts
- Fixed `ML/baseline/benchmark_fractal0_entry_exit_grid.py`: `rows_by_split_before_after_mask.before` now reports entry rows before mask, trades include per-trade `spread`, and `effective_profit_years` uses the methodology formula `1 / sum(share_y^2)`.
- Added `ML/reports/fractal0_entry_exit_grid_m5_winner_winner_yearly.csv`: current yearly breakdown for previous winner on `val_eval`, canonical spread, `2298` trades, `effective_profit_years=1.9864`.
- Updated primary `ML/reports/fractal0_entry_exit_grid.json`: added `canonical_current_artifact`, `post_review_artifacts`, `superseded_fields`, and limitations for old trades without per-trade spread.

### 2026-07-21: Full M5 rerun for Fractal0 entry/exit grid
- Added `ML/reports/fractal0_entry_exit_grid_m5_full.json` and companion CSV artifacts: full `384` canonical configs, `384` stress configs, `progress.completed=1152`, `failed=0`.
- Recorded new M5 full-grid winner `E3_open_pullback_1_0atr / M0_no_mask / X0_fixed_r_0_7`: `val_eval PF=2.7247`, `BS_p05=2.4868`, stress PF `2.2945`, `ambiguous_same_bar_rate=0.0074`.
- Updated `docs/reports/2026-07-21-fractal0-entry-exit-grid.md`, `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`, `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `wiki/research/fractal-stop-research.md`, and `wiki/index.md`: current next step is stop-policy / entry-quality follow-up, not full M5 rerun.
- Corrected report/module/wiki wording: listed `m5_full_trades.csv`, separated old `20` bootstrap disclosure from current full M5 `200`, and updated the report source note from winner-only to full M5 rerun.

### 2026-07-21: Ingest Fractal0 stop-policy grid M5 result
- Added `docs/reports/2026-07-21-fractal0-stop-grid-m5.md`.
- Updated `ML/baseline/benchmark_fractal0_entry_exit_grid.py`: added stop-policy registry, stop-aware resume/matching/permutation keys, per-stop-policy ML-exit training, `stop_grid` exit shortlist, `--skip-stress-spread`, and stop diagnostics.
- Added `ML/reports/fractal0_stop_grid_m5.json` and companion CSV artifacts: `288` selection cells, `progress.completed=576`, `failed=0`, stress-spread deferred.
- Updated `wiki/research/fractal-stop-research.md` and `wiki/index.md`: recorded winner `S2_fractal0_buffer_0_5_entry_floor_2 / E3_open_pullback_1_0atr / M0_no_mask / X2_ml_opposite_any_p0_50`, `val_eval PF=2.7873`, `BS_p05=2.5085`, permutation PASS, `locked_test=not_opened`.

### 2026-07-21: Review corrections for Fractal0 stop-policy grid report
- Updated `docs/reports/2026-07-21-fractal0-stop-grid-m5.md`: weakened the S2 conclusion because S2 improves PF but does not beat S0/X0 baseline by `val_eval BS_p05` (`2.5085` vs `2.5120`).
- Updated artifacts: `ML/reports/fractal0_stop_grid_m5.json` now contains `rejected_alternatives`, `sample_size_warnings`, stress-spread interpretation, and yearly scope; `ML/reports/fractal0_stop_grid_m5_spread_stress.csv` now contains a status row.
- Added `ML/reports/fractal0_stop_grid_m5_focused_stop_diagnostics.csv` and `ML/reports/fractal0_stop_grid_m5_all_grid_yearly.csv`; updated wiki synthesis to distinguish all-grid diagnostics from winner diagnostics.

### 2026-07-21: Ingest Fractal0 entry-quality filter result
- Added `docs/reports/2026-07-21-fractal0-entry-quality-filter.md`.
- Added `ML/baseline/benchmark_fractal0_entry_quality_filter.py` and `tests/test_fractal0_entry_quality_filter.py`: bounded ML-entry filter runner for `S2/E3/M0/X2`, reusing the stop-grid simulator and ML-exit layer.
- Added `ML/reports/fractal0_entry_quality_filter.json` and companion CSV artifacts: `17` filters x `2` validation roles = `34` completed rows, `locked_test=not_opened`.
- Updated `wiki/research/fractal-stop-research.md` and `wiki/index.md`: recorded winner `entry_quality_top20`, `val_eval PF=2.9439`, `BS_p05=2.1886`, no proven superiority over no-mask `BS_p05=2.2865`, and next step as frozen shortlist/stress probe only.

### 2026-07-21: Audit corrections for Fractal0 entry-quality filter
- Fixed `ML/baseline/benchmark_fractal0_entry_quality_filter.py`: top fraction cutoffs now ignore missing scores, JSON artifact is self-contained, and score distribution diagnostics are exported.
- Updated `ML/baseline/benchmark_fractal0_entry_exit_grid.py`: E3 entry rows now include planned limit/stop/R fields so the entry-quality feature contract is pre-order rather than post-fill.
- Recomputed `ML/reports/fractal0_entry_quality_filter*`: corrected winner is `entry_quality_top10`; it passes `val_select` selection diagnostics but fails `val_eval` versus no-mask (`BS_p05=0.9713` vs `2.2865`), lifecycle `research_hint`.
- Updated report, handoff, changelog and wiki synthesis to reject the selected entry-quality rule as a frozen candidate.
