# Cross-Instrument Robustness Check

> **Date**: 2026-04-24 00:10
> **Status**: Completed
> **Goal**: Отделить эффект смены провайдера котировок на `XAUUSD` от реального переноса frozen-систем на новые инструменты и получить каноническую матрицу робастности.
> **Related plan/spec**: `docs/superpowers/plans/2026-04-23-cross-instrument-robustness-check.md`
> **Related commit**: 7d25c8a

## Context

После `signal_export_parity` следующий риск был методологический: нельзя было смешивать в одном выводе две разные вещи:

- drift котировок `MetaQuotes -> Alpari` на том же `XAUUSD`;
- реальный перенос систем на новые инструменты.

Поэтому этап был разбит на две независимые проверки:

1. `provider_drift_baseline` на `XAUUSD`;
2. `cross_instrument_transfer` на `XAGUSD`, `EURUSD`, `GBPUSD`, `USDCHF` без ретюнинга правил.

## What Was Done

- Добавлен и покрыт тестами benchmark-модуль `ML/benchmark_cross_instrument_robustness.py`.
- Зафиксирован manifest-driven формат запуска для `provider_drift` и `transfer`.
- Подготовлены baseline manifests и reference-артефакты для `MetaQuotes` baseline и `XAUUSD` provider drift.
- Выполнен `XAUUSD MetaQuotes -> Alpari` benchmark тем же execution protocol для `quality`, `frequency`, `original_plus_path`.
- Для новых инструментов собран frozen transfer pipeline:
  - preprocessing через `processing/label_main.py`;
  - generation/export predictions;
  - export `time;signal`;
  - benchmark через `ML.benchmark_cross_instrument_robustness`.
- Исправлен практический runtime-барьер:
  - raw `Nero_XXX.csv` нельзя было честно использовать напрямую;
  - для `USDCHF` test-split пришлось отдельно дочислить недостающие `updn/trade/path/trailing` колонки;
  - `original_plus_path` для `USDCHF` был досчитан chunked-inference, потому что один большой проход в среде оказался нестабилен.

## Changed Files

- `ML/benchmark_cross_instrument_robustness.py`
- `tests/test_benchmark_cross_instrument_robustness.py`
- `docs/ML/benchmark_cross_instrument_robustness.py.md`
- `ML/export_take_skip_v2_predictions.py`
- `tests/test_export_take_skip_v2_predictions.py`
- `ML/reports/cross_instrument_robustness/run_transfer_exports.sh`
- `ML/reports/cross_instrument_robustness/run_single_instrument_transfer.py`
- `ML/reports/cross_instrument_robustness/finalize_labeled_temp.py`
- `ML/reports/cross_instrument_robustness/*.json`
- `ML/reports/cross_instrument_robustness/generated/*`
- `ML/README.md`
- `MODULE_INDEX.md`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_export_take_skip_v2_predictions.py tests/test_benchmark_cross_instrument_robustness.py tests/test_benchmark_execution_policy_v2.py tests/test_export_take_skip_trailing_stop_v2_signals.py tests/test_signal_export_parity.py -q
./.venv/bin/python -m ML.benchmark_cross_instrument_robustness --manifest ML/reports/cross_instrument_robustness/manifest_xauusd_provider_drift.json --baseline-reference ML/reports/cross_instrument_robustness/metaquotes_baseline_reference.json --output-dir ML/reports/cross_instrument_robustness/xauusd_provider_drift
./.venv/bin/python -m ML.benchmark_cross_instrument_robustness --manifest ML/reports/cross_instrument_robustness/generated/USDCHF/usdchf_transfer_manifest.json --baseline-reference ML/reports/cross_instrument_robustness/metaquotes_baseline_reference.json --output-dir ML/reports/cross_instrument_robustness/usdchf_transfer_test_labeled
```

## Results

### 1. XAUUSD provider drift baseline

`MetaQuotes -> Alpari` на том же `XAUUSD` не сломал ни одну из трёх систем.

| System | Verdict |
|---|---|
| `quality` | `provider_stable` |
| `frequency` | `provider_stable` |
| `original_plus_path` | `provider_stable` |

Это означает, что провайдерский drift заметен в данных, но на уровне frozen execution-систем пока не приводит к практическому отказу.

### 2. Cross-instrument transfer matrix

| Instrument | `quality` | `frequency` | `original_plus_path` |
|---|---|---|---|
| `XAGUSD` | `transfer_failed` | `transfer_supported` | `transfer_failed` |
| `EURUSD` | `transfer_failed` | `transfer_failed` | `transfer_failed` |
| `GBPUSD` | `transfer_inconclusive` | `transfer_inconclusive` | `transfer_supported` |
| `USDCHF` | `transfer_supported` | `transfer_supported` | `transfer_supported` |

Итог по режимам:

| System | supported | inconclusive | failed |
|---|---:|---:|---:|
| `quality` | 1 | 1 | 2 |
| `frequency` | 2 | 1 | 1 |
| `original_plus_path` | 2 | 0 | 2 |

Ключевые числа:

- `XAGUSD / frequency`: `47` trades, `17.72` trades/year, `PF=1.80`, `max_drawdown_atr=24.27`, `transfer_supported`.
- `EURUSD / frequency`: `100` trades, `PF=0.67`, `max_drawdown_atr=96.42`, `transfer_failed`.
- `GBPUSD / original_plus_path`: `24` trades, `6.63` trades/year, `PF=9.03`, `max_drawdown_atr=3.95`, `transfer_supported`.
- `USDCHF / quality`: `15` trades, `PF=inf`, `max_drawdown_atr=0.0`, `transfer_supported`.
- `USDCHF / frequency`: `91` trades, `21.31` trades/year, `PF=1.32`, `max_drawdown_atr=30.36`, `transfer_supported`.
- `USDCHF / original_plus_path`: `41` trades, `9.83` trades/year, `PF=6.01`, `max_drawdown_atr=7.52`, `transfer_supported`.

## Conclusions

- Методологическое разделение `provider drift` и `cross-instrument transfer` было правильным: `XAUUSD` на новом провайдере держится, а значит проблемы переноса на новых рынках нельзя списать на один лишь drift котировок.
- `EURUSD` оказался явным провалом для всех трёх режимов. Это сильный сигнал, что перенос не универсален.
- `USDCHF` неожиданно дал лучший перенос: все три режимы остались практически рабочими.
- `frequency` выглядит самым живучим по ширине переноса.
- `original_plus_path` не универсален, но дал два поддержанных переноса из четырёх и выглядит сильнее `quality` по breadth.
- `quality` как самый строгий режим сохранил высокий класс на части инструментов, но по breadth это самый хрупкий режим.

## Limitations / Open Questions

- Transfer проверялся как stress-test, а не как замена реального forward периода на каждом новом инструменте.
- `USDCHF` потребовал технический workaround с enrichment test-split и chunked inference; это не меняет verdict, но этот путь стоит потом упростить.
- В benchmark alignment уже видны отдельные duplicate-time cases, особенно в более частых режимах; они не сломали этап, но важны для будущего portfolio-level анализа.
- Матрица пока не отвечает на вопрос о совместимости систем между собой по времени и просадкам.

## Next Step

Перейти к `System correlation and portfolio check` из roadmap:

1. собрать сделки `quality`, `frequency`, `original_plus_path` на общем горизонте;
2. посчитать пересечение по времени, совпадение направления и корреляцию прибыли;
3. решить, какие системы можно объединять в один portfolio-layer, а какие дублируют один и тот же риск.

## Related Materials

- `docs/superpowers/plans/2026-04-23-cross-instrument-robustness-check.md`
- `ML/reports/cross_instrument_robustness/xauusd_provider_drift/provider_drift.csv`
- `ML/reports/cross_instrument_robustness/xagusd_transfer_test_labeled/transfer_matrix.csv`
- `ML/reports/cross_instrument_robustness/eurusd_transfer_test_labeled/transfer_matrix.csv`
- `ML/reports/cross_instrument_robustness/gbpusd_transfer_test_labeled/transfer_matrix.csv`
- `ML/reports/cross_instrument_robustness/usdchf_transfer_test_labeled/transfer_matrix.csv`
