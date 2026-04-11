# Entry Path v1 Quantile MT4 Export Design

> **Date**: 2026-04-11 15:05
> **Status**: Draft
> **Goal**: Добавить воспроизводимый экспортёр `entry_path_v1_quantile -> ml_signals.csv` для честного MT4 parity-check без ручной сборки CSV

## Context

После stage `entry_path_v1_quantile_robustness` следующий практический шаг — `MT4 parity-check` для frozen winner `lb_gt_m`.

Текущий MT4 runtime (`iSignal=3`) уже умеет честно исполнять готовый `ml_signals.csv`, но в основном Python-контуре нет канонического CLI, который:

- берёт уже замороженный quantile winner;
- применяет его без re-fit;
- выпускает готовый `time;signal` CSV для MT4.

Без этого следующий parity-check снова превращается в ручной обходной путь, что уже было признано техническим долгом в отчёте `2026-04-09-mt4-parity-check-winner.md`.

## Decision

Добавляется отдельный CLI:

- `API/export_entry_path_v1_quantile_signals.py`

Он не обучает модель, не подбирает правило и не использует MT4 score-filter как часть quantile logic. Его задача узкая: взять уже готовые frozen артефакты одного seed-run и выпустить финальный `ml_signals.csv`.

## Rejected Approaches

### 1. Полный prediction CSV + фильтрация в MT4

Отклонено, потому что `lb_gt_m` зависит не только от `pred_ret_24_dir_atr`, но и от quantile lower bound после conformal correction.  
Текущий MT4 runtime этого не считает, значит parity был бы неполным и методологически неверным.

### 2. Ручная сборка `time;signal`

Отклонено как нерепродуцируемый обходной путь.  
Для stage-level parity-check нужен воспроизводимый CLI в основном кодовом контуре.

## Scope

### In scope

- выпуск `time;signal` CSV из frozen quantile winner
- поддержка `validation` и `test`
- работа от уже существующего `seed_dir`
- возможность записать CSV в произвольный путь
- опциональное копирование в:
  - `MT/tester/files/ml_signals.csv`
  - `MT/MQL4/Files/ml_signals.csv`
- тесты на frozen export behavior
- обновление docs, если выясняются нюансы формата или процедуры

### Out of scope

- новый поиск winner-а
- retrain или re-benchmark модели
- реализация quantile-логики внутри MQL4
- автоматический запуск MT4 tester
- reconciliation по логу MT4 в этом же change-set

## Inputs

CLI работает от директории конкретного seed-run, например:

`ML/reports/entry_path_v1_quantile_robustness/seed_123`

Из неё используются:

- `entry_path_v1_quantile_filter_selected_rule.json`
- `entry_path_v1_quantile_test_predictions.csv` или `entry_path_v1_quantile_validation_predictions.csv`

Источник истины для export logic — `entry_path_v1_quantile_filter_selected_rule.json`, потому что там уже заморожены:

- `winner.rule`
- `winner.m`
- `winner.w`
- `correction`
- `baseline_threshold`
- `alpha`

## Output Contract

Основной выход:

```text
time;signal
2025.01.01 00:00;1
2025.01.01 01:00;0
2025.01.01 02:00;-1
```

Требования:

- все строки сохраняются, не только активные
- формат времени совпадает с текущим ожиданием MT4: `%Y.%m.%d %H:%M`
- `signal` равен исходному `signal`, если строка проходит frozen quantile rule
- иначе `signal=0`

Это важно: exporter не должен выбрасывать строки.  
Он должен выпускать полный time-aligned series, чтобы MT4 искал сигнал по `Time[bar]` так же, как сейчас ожидает runtime.

## Export Logic

1. Загрузить prediction frame нужного split.
2. Загрузить frozen rule JSON.
3. Для каждой строки восстановить:
   - `lb = min(q10, q90) - correction`
   - `ub = max(q10, q90) + correction`
   - `width = ub - lb`
4. Восстановить baseline gate:
   - `signal != 0`
   - `pred_ret_24_dir_atr >= baseline_threshold`
5. Применить frozen winner rule:
   - для текущего robust winner это `lb_gt_m`
   - но CLI должен читать rule из JSON, а не хардкодить только этот вариант
6. Сформировать итоговый `signal_out`:
   - если строка проходит winner rule, оставить исходный `signal`
   - иначе поставить `0`
7. Записать `time;signal`

CLI не должен заново выбирать winner и не должен ничего считать на `validation`, кроме прямого применения уже сохранённого frozen rule.

## CLI Interface

Предлагаемый интерфейс:

```bash
./.venv/bin/python -m API.export_entry_path_v1_quantile_signals \
  --seed-dir ML/reports/entry_path_v1_quantile_robustness/seed_123 \
  --split test \
  --output MT/tester/files/ml_signals.csv
```

Опции:

- `--seed-dir` — обязательный путь к seed report dir
- `--split` — `validation` или `test`
- `--output` — путь итогового CSV
- `--copy-to-mt4` — опциональный флаг для дублирования в оба стандартных MT4 пути

Поведение `--copy-to-mt4`:

- писать в `MT/tester/files/ml_signals.csv`
- писать в `MT/MQL4/Files/ml_signals.csv`
- основной `--output` при этом остаётся допустимым и независимым

## Error Handling

CLI должен падать с понятной ошибкой, если:

- отсутствует rule JSON
- отсутствует CSV нужного split
- в prediction CSV нет обязательных колонок:
  - `time`
  - `signal`
  - `pred_ret_24_dir_atr`
  - `pred_ret_24_q10`
  - `pred_ret_24_q90`
- в rule JSON указан неизвестный тип rule

CLI не должен молча деградировать в baseline-only export.

## Testing

Тесты нужны на три вещи:

1. exporter применяет frozen rule, а не делает re-fit
2. exporter пишет полный `time;signal` series, а не только selected rows
3. exporter корректно обнуляет сигналы вне winner mask

Минимальный набор:

- unit test на synthetic prediction frame + synthetic frozen rule
- test на `lb_gt_m`
- test на `baseline`
- test на неизвестный rule
- test на `--copy-to-mt4`, если он включён

## Documentation Impact

Нужно обновить:

- `docs/MT/ml_signal_integration.md`

Если по коду подтвердится новый важный operational nuance, обновить также:

- `docs/MT/trading_strategy.md`

## Success Criteria

Из одного frozen seed-run можно одной командой получить воспроизводимый `ml_signals.csv`, пригодный для `iSignal=3` parity-check.

Успешный экспорт должен гарантировать:

- нулевой re-fit
- нулевую ручную фильтрацию
- совпадение Python export logic с frozen quantile rule из report-артефактов

## Implementation Notes

Лучше переиспользовать логику из:

- `ML/benchmark_entry_path_v1_quantile_filter.py`

но не тянуть весь benchmark в exporter.  
В exporter стоит вынести только необходимую frozen rule application logic, чтобы код оставался узким и читаемым.
