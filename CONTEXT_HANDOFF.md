# Context Handoff

**Дата:** 2026-07-05

## Текущий этап

Этап `Entry-Based Next Open Closeout` завершён.

Итоговый structured artifact:

- `ML/reports/entry_based_next_open_closeout.json`
- closeout verdict: `PIVOT`
- verdict этапа: `DIAGNOSTIC_ONLY / PIVOT`

Текущая направленная ветка `entry-based next open` не прошла closeout как direction signal. Directional gate не пройден, но amplitude trace заметно сильнее, поэтому ветка не закрыта как "нет вообще никакого следа"; её нужно перенаправить на amplitude / movement-regime target.

## Главные артефакты

- `docs/reports/2026-07-04-entry-based-next-open-closeout.md`
- `ML/reports/entry_based_next_open_closeout.json`
- `ML/reports/entry_based_next_open_closeout_metrics.csv`
- `ML/reports/entry_based_next_open_closeout_rows.csv`
- `ML/reports/entry_based_next_open_closeout_scale_audit.csv`
- `docs/ML/benchmark_entry_based_next_open_closeout.py.md`

## Главный вывод

Технический контракт этапа выполнен:

- `entry_based_smoke_check.status = PASS`
- split: `train=44159`, `validation=13296`, `low_n_disclosure=1162`
- `locked_test` не открыт
- `EURUSD` и cross-pair validation не запускались
- closeout features используют serialized `Up/Dn` horizons `3/6/12/24/48`
- отдельные `fractal0_up_*` / `fractal0_dn_*` удалены как полностью нулевые; живые `Up/Dn` остаются в `slot_*`
- старый ablation runner сохраняет default `3/6/12`
- `representation_preflight = PASS`
- `distribution_audit = WARNING`
- `scale_audit = WARNING`
- `thread_count = 24`
- чистый полный прогон `20/20`, `elapsed_sec = 2281.3`, `finished_at = 2026-07-05T04:50:33+00:00`

По содержанию:

- лучший direction: `all100 / xgboost_depth3 / H24`, `val_select=0.0533`, `val_eval=0.0335`;
- `all100` является control baseline, не candidate, и не может дать `CONTINUE`;
- direction gate `0.10` не пройден;
- лучший amplitude: `nearest_k80 / hist_gradient_boosting / entry_up H3`, `val_select=0.3414`, `val_eval=0.4449`;
- лучший gross simple trade diagnostic: `all100 / xgboost_depth3 / H24`, `select_mean=0.0833`, `eval_mean=0.0129`;
- simple trade diagnostic не является backtest и не учитывает costs.

`PIVOT` означает: не продолжать текущий вопрос "up or down" для этой mechanics, а формулировать отдельную амплитудную постановку.

## Следующий шаг

Следующий файл читать:

- `docs/reports/2026-07-04-entry-based-next-open-closeout.md`
- `docs/ML/benchmark_entry_based_next_open_closeout.py.md`

Если продолжать исследование, писать новый bounded plan для amplitude / movement-regime target:

- заранее зафиксировать target family и gates;
- не использовать `entry_log_ratio` как главный вопрос;
- не открывать `locked_test` до freeze;
- не использовать 2026 для выбора;
- раскрыть search width.

## Запрещённые направления

- Не трактовать `PIVOT` как trading candidate.
- Не трактовать `all100` как candidate для freeze.
- Не продолжать широкий перебор `k`, corridor width, model family или entry rule внутри этой же ветки.
- Не использовать `low_n_disclosure=2026` для выбора.
- Не открывать `locked_test` без отдельного frozen-rule плана.
