# Quantile Early Timeout (hold_bars=12)

> **Date**: 2026-04-14
> **Status**: Completed — rejected by validation gate
> **Goal**: Проверить, можно ли заменить `ML_HoldBars=24` на `ML_HoldBars=12` для frozen `entry_path_v1_quantile` без изменения ML-сигнала и quantile rule
> **Related plan/spec**: [plan](../superpowers/plans/2026-04-13-early-timeout-bar12.md), [spec](../superpowers/specs/2026-04-13-quantile-execution-improvement-design.md)
> **Related commit**: pending

## Context

В PF uplift discovery ранний выход на баре 12 выглядел сильным кандидатом:

- test `N=48`
- PF `13.730869333509215`
- uplift против hold24: `+5.552`

Но discovery был read-only и опирался на test-only числа. Следующий этап должен был ответить на другой вопрос: проходит ли тот же механизм по validation-first дисциплине на frozen `entry_path_v1_quantile`, без retrain и без retune.

## What Was Done

Добавлен отдельный benchmark `ML/benchmark_quantile_early_timeout.py` и тестовый контур `tests/test_benchmark_quantile_early_timeout.py`.

Benchmark делает следующее:

- повторно выбирает тот же frozen набор quantile-сделок по `entry_path_v1_quantile_selected_rule.json`;
- сравнивает эти же сделки под `hold_bars=24` и proxy `hold_bars=12`;
- считает `n_trades`, `PF`, win_rate, mean PnL в ATR и годовые срезы;
- сначала принимает verdict на validation;
- frozen test считает только если validation gate проходит;
- дополнительно строит seed-level summary по `7, 17, 42, 77, 123`.

MT4 parity stage был явно оставлен за Python gate и не запускался после validation fail.

## Changed Files

- `ML/benchmark_quantile_early_timeout.py`
- `tests/test_benchmark_quantile_early_timeout.py`
- `ML/reports/quantile_early_timeout/validation_summary.json`
- `ML/reports/quantile_early_timeout/test_summary.json`
- `ML/reports/quantile_early_timeout/per_seed_summary.csv`
- `ML/reports/quantile_early_timeout/yearly_breakdown.csv`
- `ML/reports/quantile_early_timeout/run_metadata.json`

## Verification

Основная regression suite для нового benchmark:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_early_timeout.py -q
```

Результат:

```text
28 passed in 3.77s
```

Canonical benchmark run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_early_timeout \
  --validation-predictions ML/reports/entry_path_v1_quantile_validation_predictions.csv \
  --test-predictions ML/reports/entry_path_v1_quantile_test_predictions.csv \
  --baseline-validation-predictions ML/reports/entry_path_v1_validation_predictions.csv \
  --baseline-test-predictions ML/reports/entry_path_test_predictions.csv \
  --selected-rule ML/reports/entry_path_v1_quantile_selected_rule.json \
  --output-dir ML/reports/quantile_early_timeout \
  --root-dir /home/hohla/git/SoSimple/ML/reports/entry_path_v1_quantile_robustness \
  --seeds 7,17,42,77,123
```

## Results

### Validation

| Metric | hold12 | hold24 |
|---|---:|---:|
| trades | 27 | 27 |
| PF | 30.9912 | 12.1458 |
| win_rate | 0.9630 | 0.8148 |
| mean_pnl_atr | 1.6348 | 2.7393 |
| negative_year_slices | 0 | — |

Validation gate:

```text
gate_fail
```

Reasons:

```text
hold12_n_trades=27 < 30
hold12_mean_pnl_atr=1.6348 < hold24_mean_pnl_atr=2.7393
```

### Frozen test

Test stage не выполнялся как исследовательская оценка кандидата, потому что validation gate не прошёл.

`test_summary.json` зафиксирован как:

```text
skipped = true
skip_reason = validation_gate_failed
gate.verdict = skipped_due_to_validation_gate
```

### Multi-seed diagnostic

| Seed | Validation PF hold12 | Validation PF hold24 | Validation N hold12 | Test PF hold12 | Test PF hold24 | Test N hold12 |
|---|---:|---:|---:|---:|---:|---:|
| 7 | 16.0989 | 11.2401 | 32 | 13.7309 | 8.1787 | 48 |
| 17 | 28.5503 | 13.0032 | 41 | 17.7668 | 10.8794 | 57 |
| 42 | 30.9912 | 12.1458 | 27 | 368.8909 | 54.2400 | 28 |
| 77 | inf | 34.0911 | 19 | inf | inf | 17 |
| 123 | 15.0031 | 7.1862 | 38 | 11.0248 | 7.6573 | 53 |

Multi-seed diagnostics показывают, что идея сама по себе не мёртвая: коллапса `PF <= 1.0` нет. Но это не переопределяет canonical validation verdict на основном frozen пути.

## Conclusions

Ранний выход `hold_bars=12` **не проходит validation-first gate** как ближайший execution uplift для `entry_path_v1_quantile`.

Причина не в слабом PF. Наоборот, PF на validation высокий. Кандидат отклонён по двум более важным ограничениям:

1. support недостаточен для принятия решения (`N=27 < 30`);
2. средний PnL на сделку падает относительно текущего `hold_bars=24`, то есть PF растёт ценой более раннего и менее ёмкого выхода.

Практический вывод: discovery uplift по test и multi-seed нельзя использовать как основание для productization. Для текущего canonical path приоритет уходит обратно к другим execution-гипотезам.

## Limitations / Open Questions

- `hold12` здесь оценивается через prediction/proxy benchmark, а не через MT4 parity run; parity сознательно не делался после gate fail.
- Multi-seed CLI покрыт helper/artifact тестами, но отдельного end-to-end regression на seed-path resolution пока нет.
- Cross-instrument idea остаётся допустимым robustness stress-test, но не заменяет ни этот verdict, ни forward validation на текущем инструменте.

## Next Step

Не продолжать productization по `early_timeout_hold_bars=12`.

Следующие приоритеты:

1. сохранить forward validation `entry_path_v1_quantile` как главный нерешённый operational gate;
2. вернуться к shortlist execution uplift и проверить следующий кандидат по validation-first дисциплине, начиная с `NY session exclusion`;
3. cross-instrument transfer test рассматривать только как отдельный robustness-stage после основного verdict по текущему инструменту.

## Related Materials

- [PF uplift discovery](2026-04-13-pf-uplift-discovery.md)
- [Quantile forward validation](2026-04-13-quantile-forward-validation.md)
- `ML/reports/quantile_early_timeout/validation_summary.json`
- `ML/reports/quantile_early_timeout/test_summary.json`
- `ML/reports/quantile_early_timeout/per_seed_summary.csv`
