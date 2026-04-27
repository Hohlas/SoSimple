# benchmark_telemetry_frequency_calibration.py

## Назначение

`ML/benchmark_telemetry_frequency_calibration.py` подбирает частый diagnostic telemetry режим поверх готового take/skip prediction CSV.

Цель режима не прибыльность, а достаточная частота сделок для проверки цепочки:

```text
MT4 -> Nero.csv -> ML export -> ml_signals.csv -> MT4 -> daily reconciliation
```

## Что выбирает

Скрипт перебирает два типа отбора:

- `prob_ge_threshold` - оставить сигналы, где `pred_<score_target>` выше порога;
- `top_k_probability` - оставить верхнюю долю сигналов по `pred_<score_target>`.

Winner выбирается по частоте сделок. `PF` и PnL считаются только как диагностика, потому что для этого этапа допустима убыточная стратегия.

Текущая frozen-конфигурация `telemetry_frequency_v1`:

- `score_target=take_24_x8`;
- `selector=top_k_probability`;
- `threshold=1.0`;
- `stop_atr=3`;
- `take_profit_atr=5`;
- `max_hold_bars=24`;
- `max_positions=10`.

## Запуск

```bash
python -m ML.benchmark_telemetry_frequency_calibration \
  --predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --score-target take_24_x8 \
  --output-dir ML/reports/telemetry_frequency_v1/calibration
```

## Выходные файлы

- `calibration_grid.csv` - все проверенные кандидаты.
- `selected_rule.json` - frozen rule для telemetry export и MT4-параметров.
- `summary.json` - машинно-читаемый summary.
- `summary.md` - краткий отчёт.

## Ограничения

Это offline-калибровка частоты, а не доказательство торгового качества. Проверка реального исполнения остаётся за MT4 tester/demo и `ML/telemetry_daily_reconciliation.py`.
