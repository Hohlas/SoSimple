# Context Handoff

## Current Stage
Этап `entry_path_v1`: baseline пересчитан честно. Найдена и исправлена причина ложных ранних цифр: `ML.train` принимал `--clear_cache`, но не передавал его в `train_model()`, поэтому обучение шло на старом `entry_path` кэше. После чистой пересборки и нового обучения `ret_*` больше не выглядит ни “чудесно сильным”, ни сломанным: validation `ret_pearson_r=0.2656`, test `ret_pearson_r=0.2450`. Путь цены выглядит ещё лучше: validation `path_reg_pearson_r=0.3004`, test `path_reg_pearson_r=0.2745`.

## Last Completed Stage
`entry_path_v1` baseline после исправления кэша и чистого retrain (2026-04-08).

## Next Step
Следующий шаг теперь уже другой: не искать старую причину падения, а решать проблему сильного перекоса нулевых строк.

1. Проверить вариант обучения, где `ret_*` и `path_6_class` считаются только по активным строкам `signal != 0`.
2. Сравнить этот вариант с текущим baseline по validation и test.
3. Отдельно решить судьбу `path_6_class`: оставить, ослабить или временно убрать.
4. Перед merge в main сделать один чистый полный rebuild датасета и артефактов штатным проходом.

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
- Активных сигналов только около `5%`, поэтому обычный loss сильно забивается строками `signal=0`.
- `path_6_class` почти вырождается: на активных строках модель в основном предсказывает `0`.
- Общие метрики по всем строкам полезны, но для реальной сделки нужно обязательно смотреть active-only блок.
- Перед merge в main нужен один чистый полный rebuild через `label_main`, а не смесь локальных шагов.

## Latest Report
`docs/reports/2026-04-08-entry-path-v1-baseline.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
