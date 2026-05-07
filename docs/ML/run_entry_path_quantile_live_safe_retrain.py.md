# run_entry_path_quantile_live_safe_retrain.py

`ML/run_entry_path_quantile_live_safe_retrain.py` запускает повторную проверку
`entry_path_v1_quantile` поверх нового live-safe CPU baseline `A @ 7.5%`.

Цель: не смешивать старые quantile-артефакты с новым baseline после исправления
нормализации `predict -> front/back`.

## Что Делает

Для каждого seed:

1. обучает `entry_path_v1_quantile`;
2. сохраняет checkpoint в отдельную `seed_XXX` папку;
3. экспортирует validation/test quantile predictions из этого checkpoint;
4. строит baseline rule `A @ 7.5%` из соответствующего CPU baseline seed;
5. запускает `benchmark_entry_path_v1_quantile_filter.py` поверх этого rule;
6. пишет `summary.json`.

В корень output-директории пишутся:

- `manifest.json`;
- `multi_seed_summary.csv`;
- `multi_seed_summary.json`.

## Важное Ограничение

Runner проверяет quantile поверх per-seed baseline `A @ 7.5%`.
Он не выбирает лучший baseline из `A/B/B_no_path6`, потому что production
baseline после аудита зафиксирован как простой `A`.

## Команда Для Сервера

```bash
./.venv/bin/python -m ML.run_entry_path_quantile_live_safe_retrain \
  --output-dir ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline \
  --baseline-root ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed \
  --seeds 7 17 42 77 123 \
  --epochs 5 \
  --batch-size 256 \
  --baseline-coverage 0.075 \
  --clear-cache
```

## Как Читать Результат

Главные поля в `multi_seed_summary.csv`:

- `baseline_*` - проверка базового `A @ 7.5%` для того же seed;
- `quantile_winner` / `quantile_rule` - какое quantile-правило выбрано на
  validation;
- `quantile_test_pf` / `quantile_test_trades` - frozen test по выбранному
  validation-правилу;
- `quantile_sequential_pf` / `quantile_sequential_trades` - проверка с
  single-position задержкой `24` бара.

Если quantile даёт высокий PF, но `quantile_winner` или `quantile_rule`
прыгают между seed, слой остаётся research-only.
