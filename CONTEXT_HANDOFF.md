# Context Handoff

## Current Stage
Этап `entry_path_v1`: первый baseline собран и зафиксирован. Новый трек теперь существует end-to-end: разметка, DataLoader, multitask transformer, обучение, test-отчёт и исследовательские CSV. Главный вывод этапа такой: на validation `ret_*` выглядит сильно, но на test этот слой пока не переносится. При этом слой пути цены (`fav/adv`) на test выглядит заметно лучше и стабильнее.

## Last Completed Stage
`entry_path_v1` baseline и рабочие артефакты (2026-04-08).

## Next Step
Следующий шаг теперь узкий и понятный: не переучивать модель наугад, а разобрать, почему `ret_*` ломается на test.

1. Сравнить train / validation / test по распределениям `ret_6_dir_atr`, `ret_12_dir_atr`, `ret_24_dir_atr`.
2. Проверить ranking quality по split:
   - top/bottom quantiles по `pred_ret_24_dir_atr`
   - связь `pred_ret_*` с `true_ret_*`
   - отдельно для BUY и SELL.
3. Проверить, нет ли перекоса в loss balance:
   - не тянет ли модель слишком сильно в сторону `path_reg`;
   - не даёт ли `path_cls` только формальную нагрузку без пользы.
4. После этого решить, что менять первым:
   - веса loss;
   - архитектуру;
   - или сам главный `ret_*` target.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `AGENTS.md`
- `docs/superpowers/specs/2026-04-08-entry-path-v1-design.md`
- `docs/superpowers/plans/2026-04-08-entry-path-v1.md`
- `docs/reports/2026-04-08-entry-path-v1-baseline.md`
- `ML/checkpoints/transformer_entry_path_v1_result.json`
- `ML/reports/evaluate_test_entry_path_v1.md`
- `ML/reports/entry_path_v1_validation_predictions.csv`
- `ML/reports/entry_path_v1_test_predictions.csv`

## Open Risks
- Главный риск сейчас — ложная сила `ret_*` на validation при слабом переносе на test.
- `path_6_class` почти вырождается в класс `0`, значит этот слой пока даёт мало полезной структуры.
- В этой ветке полный `label_main` на всём наборе не был доведён до одного чистого финального прохода: train/validation уже были локально пересчитаны, а test был отдельно дополнен слоем `entry_path_v1`. Перед merge в main нужен полный rebuild.
- `transformer_entry_path_v1_result.json` был синхронизирован после отдельного validation-pass, поэтому `training_time` там пустой.

## Latest Report
`docs/reports/2026-04-08-entry-path-v1-baseline.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
