# Context Handoff

## Current Stage
Этап `entry_path_v1`: слой `торговать / не торговать` поверх рабочего базового варианта собран и доведён до практического базового варианта. На этом этапе были добавлены:

- простой фильтр `A` по `pred_ret_24_dir_atr`;
- составной фильтр `B` по нескольким выходам модели;
- скрипт проверки с подбором порога только на validation;
- защитное правило против слишком маленького и неустойчивого хвоста;
- отдельный путь по последовательности для головы `path_cls`.

Текущая модель после этого этапа:
- validation: `ret_pearson_r=0.2758`, `path_reg_pearson_r=0.2987`, `path_cls_f1_macro=0.4074`
- test: `ret_pearson_r=0.2507`, `path_reg_pearson_r=0.2667`, `path_cls_f1_macro=0.4013`
- active-only test: `ret_pearson_r=0.2241`, `path_cls_f1_macro=0.3208`

Текущий рабочий победитель для слоя отбора:
- `A @ 7.5%`
- validation: `36` сделок, `PF=2.67`, `stability_ratio=1.00`
- test: `44` сделки, `PF=4.29`
- последовательная проверка: `30` сделок, `PF=2.87`

Важно: составной фильтр `B` уже перестал быть копией `A`, но по общему правилу отбора победителем пока всё ещё остаётся `A`.

## Last Completed Stage
`entry_path_v1` слой отбора сделок и защитное правило выбора победителя (2026-04-09).

## Next Step
Следующий шаг уже не в новой переделке модели и не в новом подборе порогов для `A/B`.

1. Взять `A @ 7.5%` как замороженный рабочий базовый вариант для `entry_path_v1`.
2. Поверх него строить conformal-слой `торговать / не торговать`.
3. Сравнивать conformal не с сырыми сигналами, а именно с этим базовым вариантом.
4. `B` держать как вторую исследовательскую ветку и возвращаться к нему только если новый слой отбора даст повод.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `AGENTS.md`
- `docs/reports/2026-04-09-entry-path-trade-filter.md`
- `docs/reports/2026-04-08-entry-path-v1-baseline.md`
- `docs/reports/2026-04-09-entry-path-v1-loss-weighting.md`
- `docs/superpowers/specs/2026-04-08-entry-path-v1-design.md`
- `docs/superpowers/plans/2026-04-08-entry-path-v1.md`
- `ML/checkpoints/transformer_entry_path_v1_result.json`
- `ML/reports/evaluate_validation_entry_path_v1.md`
- `ML/reports/evaluate_test_entry_path_v1.md`
- `ML/reports/entry_path_trade_filter_report.md`
- `ML/reports/entry_path_trade_filter_selected_rule.json`

## Open Risks
- Класс `1` в `path_6_class` по-прежнему не ловится.
- Победитель всё ещё покрывает только узкую часть активных сигналов.
- `B` уже отличается от `A`, но пока не стал лучшим по текущему правилу отбора.
- Защитное правило в скрипте проверки пока простое и само по себе не заменяет будущий conformal-слой.

## Latest Report
`docs/reports/2026-04-09-entry-path-trade-filter.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
