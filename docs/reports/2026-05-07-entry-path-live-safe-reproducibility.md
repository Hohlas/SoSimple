# Entry Path Live-Safe Reproducibility

> **Date**: 2026-05-07
> **Status**: Completed
> **Goal**: Проверить воспроизводимость `entry_path_v1_live_safe` после исправления нормализации и отделить качество модели от устойчивости торгового фильтра.
> **Related plan/spec**: `docs/audit/ml_trading_methodology.md#3-feature-contract-и-leakage-gate`
> **Related commit**: pending

## Context

После исправления нормализации `predict -> front/back` нужно было понять,
сохранился ли кандидат `entry_path_v1_live_safe + A`.

Первый провал retrain (`ret_pearson_r ~= 0.004`) был вызван не
нормализацией, а неверным источником данных: текущий
`MT/MQL4/Files/Nero.csv` содержит M5-строки, а `entry_path_v1` требует H1.
Проверочный retrain был перенесён на H1-источник
`MT/MQL4/Files/Nero_XAUUSD.csv`.

## What Was Done

- Добавлен `ML.train --output-dir`, чтобы каждый seed/device сохранял свой
  checkpoint и result JSON.
- Добавлен `ML/run_entry_path_live_safe_retrain.py`, который по каждому seed
  выполняет train -> export validation/test -> benchmark.
- На сервере CPU (`torch 2.11.0+cu130`) выполнен multi-seed прогон:
  `7`, `17`, `42`, `77`, `123`.
- Отдельно пересчитан production baseline `A @ 7.5%`, потому что общий runner
  выбирает лучшего validation winner среди `A`, `B`, `B_no_path6`, а ранее
  production-кандидатом был выбран именно простой rule-family `A`.

## Changed Files

- `ML/train.py` - добавлен `--output-dir` и runtime metadata.
- `ML/run_entry_path_live_safe_retrain.py` - новый runner.
- `tests/test_run_entry_path_live_safe_retrain.py` - unit-тесты runner-а.
- `docs/ML/run_entry_path_live_safe_retrain.py.md` - документация runner-а.

## Verification

```bash
./.venv/bin/python -m py_compile ML/train.py ML/run_entry_path_live_safe_retrain.py
./.venv/bin/python -m pytest tests/test_run_entry_path_live_safe_retrain.py tests/test_entry_path_training.py tests/test_export_entry_path_predictions.py tests/test_entry_path_trade_filter.py -q
```

Результат: `26 passed`.

Серверный запуск:

```bash
./.venv/bin/python -m ML.run_entry_path_live_safe_retrain \
  --output-dir ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed \
  --seeds 7 17 42 77 123 \
  --epochs 5 \
  --batch-size 256 \
  --clear-cache
```

## Results

### Server CPU Auto-Winner

| seed | winner | ret_r | validation PF | test PF | sequential PF | seq trades |
|---:|---|---:|---:|---:|---:|---:|
| 7 | B | 0.2714 | 2.3369 | 2.3889 | 1.6183 | 31 |
| 17 | A | 0.2756 | 1.3271 | 1.3491 | 0.8925 | 39 |
| 42 | B | 0.2806 | 1.5847 | 1.6870 | 1.2055 | 41 |
| 77 | A | 0.2807 | 2.7197 | 3.3997 | 2.3249 | 27 |
| 123 | A | 0.2703 | 2.4466 | 2.8461 | 1.8188 | 31 |

Сводка auto-winner:

- median sequential PF: `1.6183`;
- min sequential PF: `0.8925`;
- max sequential PF: `2.3249`;
- PF > 2.0: `1/5`;
- PF <= 1.0: `1/5`;
- winner `A`: `3/5`, winner `B`: `2/5`.

### Server CPU Production Baseline `A @ 7.5%`

| seed | validation PF | validation trades | test PF | test trades | sequential PF | seq trades |
|---:|---:|---:|---:|---:|---:|---:|
| 7 | 2.1367 | 36 | 2.8014 | 44 | 2.0139 | 29 |
| 17 | 2.1827 | 36 | 7.4892 | 42 | 5.9352 | 27 |
| 42 | 2.2482 | 36 | 7.5737 | 41 | 5.9352 | 27 |
| 77 | 2.7197 | 36 | 3.3997 | 40 | 2.3249 | 27 |
| 123 | 2.4466 | 36 | 2.8461 | 46 | 1.8188 | 31 |

Сводка `A @ 7.5%`:

- median sequential PF: `2.3249`;
- min sequential PF: `1.8188`;
- max sequential PF: `5.9352`;
- PF > 2.0: `4/5`;
- PF <= 1.0: `0/5`.

## Conclusions

Модельная часть воспроизводимости закрыта достаточно хорошо:
`ret_pearson_r` на сервере держится в диапазоне `0.2703..0.2807`.

Торговый слой нужно читать аккуратно:

- если разрешить runner-у автоматически выбирать winner среди `A/B/B_no_path6`,
  результат слабее и менее стабилен;
- если проверять заранее выбранный production baseline `A @ 7.5%`, результат
  устойчивее: PF > 2.0 у `4/5` seed и нет seed с PF <= 1.0.

Практический вывод: для `entry_path_v1_live_safe` подтверждён именно простой
baseline `A @ 7.5%`, а не автоматический выбор любого validation winner.

## Limitations / Open Questions

- MT4 parity пока сознательно не запускался.
- CPU/GPU дают разные checkpoint и разные верхние сделки, хотя средняя
  модельная точность близкая. Причина и принятое решение описаны в
  [`2026-05-07-cpu-gpu-reproducibility.md`](2026-05-07-cpu-gpu-reproducibility.md).
  Это не блокирует baseline `A`, но требует фиксировать checkpoint и окружение
  для production.
- Проверка сделана на XAUUSD H1 split. M5 `Nero.csv` не подходит для этого
  контура.
- Для текущей очищенной `entry_path_v1_live_safe + A @ 7.5%` cross-instrument
  проверка на других валютных парах ещё не выполнялась. Старые проверки
  `entry_path_v1` / `entry_path_v1_quantile` на `EURUSD`, `GBPUSD`, `USDCHF`,
  `XAGUSD` относятся к до-audit контуру и не доказывают переносимость текущей
  live-safe версии.

## Next Step

Следующий шаг - переходить ко второму пункту плана: аудит других систем.
Начинать стоит с `entry_path_v1_quantile_live_safe_baseline`, но читать его
как research-only слой поверх подтверждённого baseline `A`, а не как
production-кандидат.

## Related Materials

- `ML/run_entry_path_live_safe_retrain.py`
- `ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/`
- `docs/reports/2026-05-05-live-safe-ml-audit.md`
- `docs/audit/ml_trading_methodology.md#3-feature-contract-и-leakage-gate`
