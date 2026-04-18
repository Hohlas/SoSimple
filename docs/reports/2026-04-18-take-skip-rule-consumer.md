# Take/Skip V2 Rule Consumer

> **Date**: 2026-04-18 21:20
> **Status**: Completed
> **Goal**: Добавить единый consumer-слой для frozen `take_skip_trailing_stop_v2` rules, чтобы применять `quality` и `frequency` режимы к готовым prediction CSV без ручного разбора параметров.
> **Related plan/spec**: follow-up from `docs/reports/2026-04-18-take-skip-frequency-followup.md`
> **Related commit**: c72be6c

## Context

После фиксации двух канонических rule JSON для `take_skip_trailing_stop_v2` оставалась практическая проблема: правило уже было зафиксировано, но использовать его можно было только вручную, читая `score_target`, `selector` и `threshold` из JSON и отдельно применяя их к prediction CSV.

Это мешало следующему шагу:

- нельзя было одинаково и безошибочно прогонять `quality` и `frequency` режимы;
- rule JSON существовали как артефакты отчёта, но не как рабочий интерфейс;
- для MT4 и для повторяемых offline-check нужен был один явный CLI.

## What Was Done

- Добавлен новый exporter:
  - `API/export_take_skip_trailing_stop_v2_signals.py`
- Новый CLI принимает:
  - `--predictions`
  - `--rule-path`
  - `--output`
  - optional `--base-csv`
  - optional `--copy-to-mt4`
- Реализованы два режима применения frozen rule:
  - `prob_ge_threshold`
  - `top_k_probability`
- Экспортёр умеет:
  - работать прямо по sparse prediction CSV;
  - при необходимости разворачивать результат в полный временной ряд через `base-csv`;
  - писать один и тот же `ml_signals.csv` в tester/runtime каталоги MT4.
- Добавлены отдельные тесты на:
  - threshold rule;
  - top-k rule;
  - разворот в полный ряд;
  - ошибочный selector;
  - `copy-to-mt4`.

## Changed Files

- `API/export_take_skip_trailing_stop_v2_signals.py`
- `tests/test_export_take_skip_trailing_stop_v2_signals.py`
- `API/README.md`
- `docs/MT/ml_signal_integration.md`
- `MODULE_INDEX.md`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_export_take_skip_trailing_stop_v2_signals.py -q
./.venv/bin/python -m py_compile API/export_take_skip_trailing_stop_v2_signals.py
```

## Results

Новый consumer-слой теперь позволяет применять два уже зафиксированных frozen rule напрямую:

- `ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json`
- `ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json`

Ожидаемый прикладной путь стал таким:

```bash
./.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions <predictions.csv> \
  --rule-path ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json \
  --output MT/tester/files/ml_signals.csv
```

или:

```bash
./.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
  --predictions <predictions.csv> \
  --rule-path ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json \
  --output MT/tester/files/ml_signals.csv
```

## Conclusions

- Цель этого этапа была не в новом улучшении PF, а в том, чтобы превратить уже найденные режимы в рабочий интерфейс.
- Причина была практическая: без consumer-слоя rule JSON оставались “знанием в отчёте”, а не воспроизводимым шагом pipeline.
- Последствие положительное: теперь `quality` и `frequency` режимы можно применять единообразно, без ручной настройки и без повторного чтения отчёта.
- Решение получилось минимальным и безопасным: новый модуль не меняет обучение, benchmark и сами frozen rules, а только стандартизует их применение.

## Limitations / Open Questions

- Exporter не строит prediction CSV сам; он только применяет rule к уже готовому файлу.
- Для полного временного ряда нужен `--base-csv`, если исходный prediction CSV sparse.
- В текущем виде consumer не интегрирован в `API/generate_signals.py`; это отдельный явный путь.

## Next Step

Сделать маленький operational check:

1. применить `quality` и `frequency` rule к одному и тому же prediction CSV;
2. получить два готовых `ml_signals.csv`;
3. сравнить их уже на стороне MT4 или в offline execution-check без изменения модели.

## Related Materials

- `docs/reports/2026-04-18-take-skip-frequency-followup.md`
- `ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json`
- `ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json`
