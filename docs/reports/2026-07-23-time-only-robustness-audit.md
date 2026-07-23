# Time Only Robustness Audit

> **Дата**: 2026-07-23
> **Статус**: Completed
> **Вердикт**: research_only
> **Цель**: Проверить validation-slice устойчивость fixed normalized `time_only` winner без нового поиска и без открытия `locked_test`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`

## Context

Аудит проверяет только заранее выбранное правило:

```text
S2_fractal0_buffer_0_5_entry_floor_2 /
E3_open_pullback_1_0atr /
M0_no_mask /
X2_ml_opposite_any_p0_50 /
profile=time_only /
model=linear /
target=target_entry_ev_regression /
filter=top30 /
score_cutoff_on_val_select=-0.026718184259660646
```

Источник правила: `ML/reports/fractal0_rich_entry_quality_normalized.json`.
`locked_test` не открыт.

## Уровень Этапа

Проверочный audit поверх validation artifacts, не `locked_test`.
`scope=validation_artifact_robustness_slice`.

Research-first disclosure:

```text
lifecycle_status: research_only
origin_bias: broad normalized rich-entry validation search
research_priority: проверить устойчивость fixed time_only rule перед новым probe design
current_search_budget: no new search, one fixed rule
cumulative_search_budget: inherited from normalized rich-entry search, 243 ranked configs plus diagnostic controls
next_probe_freeze: not created in this stage
allowed_max_verdict: research_only
forbidden_interpretations: candidate, tradable, live_ready, production, permission_to_open_locked_test
```

## What Was Done

- Добавлен `ML/baseline/audit_time_only_robustness.py`.
- Добавлены unit-тесты `tests/test_time_only_robustness_audit.py`.
- Проверен fixed rule contract и запрет на opened `locked_test`.
- Посчитаны yearly, quarterly, side, year-side, score-shift, stricter-cutoff,
  top-k и calendar diagnostics.
- Для spread-stress, timezone-shift, calendar permutation importance и
  sequential записаны статусы отсутствующих проверок.
- Записаны audit artifacts `ML/reports/time_only_robustness_audit*`.

## Multiple Testing Context

Этот audit не добавляет новый model/profile/target/filter search. Он наследует
origin bias из normalized rich-entry search, где winner был выбран после
широкой validation-партии: `243` ranked configs плюс diagnostic controls.
Метрики PF/PnL ниже не являются торговым выводом и не дают права открывать
`locked_test`.

## Changed Files

- `ML/baseline/audit_time_only_robustness.py`
- `tests/test_time_only_robustness_audit.py`
- `docs/ML/audit_time_only_robustness.py.md`
- `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- `docs/reports/2026-07-23-time-only-robustness-audit.md`
- `docs/superpowers/roadmap.md`
- `CONTEXT_HANDOFF.md`
- `MODULE_INDEX.md`
- `CHANGELOG.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`
- `ML/reports/time_only_robustness_audit*.json/csv`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_time_only_robustness_audit.py -q
./.venv/bin/python ML/baseline/audit_time_only_robustness.py --input-prefix ML/reports/fractal0_rich_entry_quality_normalized --output-prefix ML/reports/time_only_robustness_audit
./.venv/bin/python -m pytest tests/ -q
```

Результат полного прогона: `1390 passed, 52 warnings`.

## Reproducibility

Входные normalized artifacts зафиксированы в
`ML/reports/time_only_robustness_audit.json.input_artifacts`:

- `fractal0_rich_entry_quality_normalized.json`: size `3480367`,
  sha256 `124859f3aba89a4fe2b4b663919740315d9218b8f2c748298a1dc013e00379cb`.
- `fractal0_rich_entry_quality_normalized_summary.csv`: size `349060`,
  sha256 `89e825e2d54f24c6cb0167dab4a87fba7e415036f62006f6402a53166aa6dd81`.
- `fractal0_rich_entry_quality_normalized_trades.csv`: size `310798934`,
  sha256 `871413b9bab8758a78b9924abe27223c8bf2df037947b49d23c79d7424b22259`.
- `fractal0_rich_entry_quality_normalized_scores.csv`: size `491649054`,
  sha256 `03a765a9134afd99add5c92dd58e018bcc0871156ebe650acb6d2f29f276f92d`.

## Results

Decision: `REGIME_REFORMULATION_REQUIRED`.

Aggregate `val_eval`: `n_trades=660`, `PF=4.0268`,
`sequential_block_BS_p05=3.3068`,
`pf_without_best_year=3.5465`, `max_drawdown_r=3.3906`,
`mean_pnl_r=0.3397`.

Старый source artifact `bs_p05=3.3955` не используется как robustness
evidence; audit пересчитывает block bootstrap с `block_size=20`,
`seed=20260723`.

Profit concentration: `n_years=2`, `effective_profit_years=1.9922`,
`best_year_share=0.5312`, `profitable_years=2`, `min_year_pf=3.5465`.

Yearly:

- `2021`: `n_trades=300`, `PF=4.7567`, `mean_pnl_r=0.3681`.
- `2022`: `n_trades=360`, `PF=3.5465`, `mean_pnl_r=0.3160`.

Side:

- `BUY`: `n_trades=303`, `PF=5.1463`, `mean_pnl_r=0.4135`.
- `SELL`: `n_trades=357`, `PF=3.2554`, `mean_pnl_r=0.2771`.

Calendar slices считаются отдельно по `signal_time`, `fill_time` и
`exit_time`. Худший квартал:

- `signal_time`: Q3, `n_trades=205`, `PF=3.5546`.
- `fill_time`: Q3, `n_trades=206`, `PF=3.4640`.
- `exit_time`: Q3, `n_trades=205`, `PF=3.3132`.

Худший месяц по `signal_time`: month `10`, `n_trades=54`, `PF=2.3309`.

Score shift:

- `val_select`: rows `4731`, mean score `-0.048507`, p10 `-0.090531`,
  p50 `-0.047495`, p90 `-0.010249`, fraction above fixed cutoff `0.301628`.
- `val_eval`: rows `4732`, mean score `-0.048318`, p10 `-0.090531`,
  p50 `-0.049335`, p90 `-0.008955`, fraction above fixed cutoff `0.309806`.

Stricter cutoff sensitivity:

- offset `0.000`: `n_trades=660`, `PF=4.0268`.
- offset `0.005`: `n_trades=536`, `PF=3.7064`.
- offset `0.010`: `n_trades=420`, `PF=3.7379`.
- offset `0.020`: `n_trades=139`, `PF=4.3791`.

Top-k sensitivity:

- `top30`: `n_trades=660`, `PF=4.0268`.
- `top40`: `n_trades=900`, `PF=3.7417`.
- `top50`: `n_trades=1109`, `PF=3.5710`.

Calendar no-ML baseline: `NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`, потому что
unfiltered no-ML calendar baseline отсутствует в saved artifacts; доступны
только `top30`, `top40`, `top50`.

```text
allowed_max_verdict=research_only
not_trading_evidence_reason=validation artifact slice, locked_test not opened, inherited broad-search origin bias
forbidden_interpretations=candidate/tradable/live_ready/production/permission_to_open_locked_test
```

## Conclusions

`time_only` не провалился по годам, сторонам, entry-time calendar slices и
top-k, но audit не может поднять статус из-за двух ограничений: stricter
cutoff становится маловыборочным при offset `0.020`, а stress costs нельзя
пересчитать из сохранённых сделок canonical spread. Решение:
`REGIME_REFORMULATION_REQUIRED`.

Это решение является консервативным маршрутом из плана, а не доказательством
провала режима. Перед полноценной reformulation следующий план должен закрыть
stress-cost resimulation, entry-time calendar robustness и timezone-shift
disclosure.

Это не разрешение открыть `locked_test`.

## Limitations / Open Questions

- `multi_seed_status=NOT_RUN`.
- `provider_drift_status=NOT_RUN`.
- `transfer_status=NOT_RUN`.
- `locked_test_status=not_opened`.
- `stress_costs_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`.
- `timezone_shift_status=NOT_RUN`.
- `calendar_permutation_importance_status=NOT_RUN`.
- `sequential_position_constraint_status=NOT_RUN`.
- SeqPF не использовался как доказательство качества.

## Split Disclosure

- `train_core`: обучение ML-exit/ML-entry/scaler; `2004-07-06 20:00:00` ..
  `2019-06-20 14:00:00`, raw rows `44159`, filled trades `21343`.
- `val_select`: выбор cutoff; `2019-06-20 16:00:00` ..
  `2021-03-08 03:00:00`, raw rows `4731`, filled trades `2294`.
- `val_eval`: fixed-rule audit; `2021-03-08 05:00:00` ..
  `2022-12-02 07:00:00`, raw rows `4732`, filled trades `2298`;
  fixed-rule selected trades `660`.
- `sample_size_gate`: fixed top-k имеет `top30/top40/top50 n_trades =
  660/900/1109`; stricter cutoff offset `0.020` имеет `n_trades=139` и
  поэтому отмечен как `stricter_cutoff_sample_fragile`.
- `locked_test`: not_opened.

## Next Step

Написать план `Regime filter reformulation` без открытия `locked_test`.
Первый блок плана должен закрыть stress-cost resimulation, entry-time calendar
slices и timezone-shift disclosure, чтобы не подменить недостающие проверки
новой гипотезой.

## Artifacts

- `ML/reports/time_only_robustness_audit.json`
- `ML/reports/time_only_robustness_audit_yearly.csv`
- `ML/reports/time_only_robustness_audit_quarterly.csv`
- `ML/reports/time_only_robustness_audit_side.csv`
- `ML/reports/time_only_robustness_audit_year_side.csv`
- `ML/reports/time_only_robustness_audit_score_shift.csv`
- `ML/reports/time_only_robustness_audit_stricter_cutoff.csv`
- `ML/reports/time_only_robustness_audit_topk_sensitivity.csv`
- `ML/reports/time_only_robustness_audit_calendar_no_ml_baselines.csv`
- `ML/reports/time_only_robustness_audit_calendar_slices.csv`
- `ML/reports/time_only_robustness_audit_spread_stress.csv`
- `ML/reports/time_only_robustness_audit_timezone_shift.csv`
- `ML/reports/time_only_robustness_audit_calendar_permutation_importance.csv`
- `ML/reports/time_only_robustness_audit_sequential.csv`

## Related Materials

- `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- `docs/superpowers/roadmap.md`
- `docs/methodology/09-validation-freeze.md`
- `docs/methodology/11-robustness.md`
- `docs/methodology/16-reporting-audit.md`
