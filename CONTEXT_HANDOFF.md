# Context Handoff

## Current Stage
Этап `entry_path_v1`: базовый вариант после перевзвешивания функции потерь выбран и синхронизирован в артефактах. Проверены три режима обучения при сильном перекосе `signal=0`: жёсткий режим только по активным строкам, вес только для `path_6_class`, и вес `5.0` сразу для `ret_*` и `path_6_class`. Выбран последний вариант как рабочая база.

Текущие цифры выбранного варианта:
- validation: `ret_pearson_r=0.2736`, `path_reg_pearson_r=0.3006`, `path_cls_f1_macro=0.4059`
- test: `ret_pearson_r=0.2494`, `path_reg_pearson_r=0.2722`, `path_cls_f1_macro=0.4160`
- active-only test: `ret_pearson_r=0.2285`

Отдельно исправлена и другая рабочая проблема: `evaluate_test` и markdown-отчёт теперь явно показывают `Checkpoint epoch` и лучший `val`-результат, чтобы не путать свежие и старые артефакты.

## Last Completed Stage
`entry_path_v1` перевзвешивание функции потерь и выбор рабочего базового варианта (2026-04-09).

## Next Step
Следующий шаг уже не в новом подборе ручных весов. Базовый цикл обучения для `entry_path_v1` на этом этапе можно считать замороженным.

1. Взять текущий вариант с весом `5.0` для активных строк в `ret_*` и `path_6_class` как замороженную базу.
2. Поверх него строить слой `торговать / не торговать`.
3. Первым кандидатом проверить conformal-подход для отбора сделок.
4. Сравнивать уже не только общие test-метрики, но и active-only срез и будущий слой отбора.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `AGENTS.md`
- `docs/superpowers/specs/2026-04-08-entry-path-v1-design.md`
- `docs/superpowers/plans/2026-04-08-entry-path-v1.md`
- `docs/reports/2026-04-09-entry-path-v1-loss-weighting.md`
- `docs/reports/2026-04-08-entry-path-v1-baseline.md`
- `ML/checkpoints/transformer_entry_path_v1_result.json`
- `ML/reports/evaluate_test_entry_path_v1.md`
- `docs/reports/2026-04-08-outcome-aligned-retraining.md`
- `ML/reports/outcome_target_validation_benchmark.md`

## Open Risks
- Активных сигналов всё ещё около `5%`, поэтому даже выбранный базовый вариант остаётся чувствительным к перекосу данных.
- Класс `1` в `path_6_class` по-прежнему почти не ловится.
- Общие срезы по всем строкам остаются сильно разбавленными `signal=0`; для практики важнее active-only блок и будущий слой отбора.
- `entry_path_v1` пока ещё не превращён в правило сделки; сейчас это сильнее выглядит как хорошая исследовательская база.
- Outcome-aligned track остаётся отдельным тупиком и не должен смешиваться с `entry_path_v1`.

## Latest Report
`docs/reports/2026-04-09-entry-path-v1-loss-weighting.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
