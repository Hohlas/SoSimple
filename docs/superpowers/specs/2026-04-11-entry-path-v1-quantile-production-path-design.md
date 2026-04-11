# Entry Path v1 Quantile Production Path Design

> **Date**: 2026-04-11 18:12
> **Status**: Draft
> **Goal**: Перевести `entry_path_v1_quantile` из подтверждённого research-stage в официальный production export path для MT4, не ломая существующий baseline-контур

## Context

На 2026-04-11 линия `entry_path_v1_quantile` уже прошла два ключевых этапа:

- multi-seed robustness-pass с verdict `go_mt4`;
- отдельный `MT4 parity-check` для frozen winner `lb_gt_m`.

Это означает, что главный открытый вопрос больше не исследовательский.  
Нужно не искать ещё один winner, а определить, как именно quantile-layer должен жить в основном рабочем контуре проекта.

Сейчас quantile export уже реализован через `API/export_entry_path_v1_quantile_signals.py`, но по смыслу он всё ещё описан как parity/research tool.  
Если оставить это в таком виде, проект сохранит уже подтверждённый execution mode в статусе времянки.

## Decision

Принимается **dual-path migration**:

- `entry_path_v1_quantile` становится **официальным рекомендуемым production path** для `iSignal=3`;
- baseline path остаётся в репозитории как **backup / legacy path**;
- default execution logic в MQL4 не меняется;
- основной переход происходит на уровне Python export path, документации и source of truth для frozen winner.

## Alternatives Considered

### 1. Немедленно заменить default path на quantile

Отклонено.

Плюсы:

- один путь вместо двух;
- меньше решений в документации.

Минусы:

- слишком резкий переход;
- ухудшает rollback story;
- создаёт лишний риск тихо сломать старые сценарии и сравнения с baseline.

### 2. Dual-path migration

Принято.

Плюсы:

- quantile получает официальный production status;
- baseline остаётся как fallback;
- проще поддерживать эксплуатацию и диагностику;
- не требует немедленно менять MT4 runtime или удалять historical tooling.

Минусы:

- некоторое время в проекте живут два export path.

### 3. Оставить quantile как research-only CLI

Отклонено.

Это не соответствует текущему статусу линии: quantile уже подтверждён и по Python, и по MT4.

## Scope

### In Scope

- закрепить официальный production source of truth для quantile winner;
- сделать quantile exporter каноническим operational path;
- описать baseline как backup / legacy;
- добавить явный production-oriented CLI entrypoint или режим поверх уже существующего exporter-а;
- обновить docs, handoff и registry так, чтобы новый рекомендуемый путь был недвусмысленным;
- покрыть тестами выбор production source и export behavior.

### Out of Scope

- удаление baseline path;
- изменение `ML_TRADE()` в MQL4;
- новый search / benchmark / re-fit;
- новый MT4 tester run в рамках этого этапа;
- перевод `triple_barrier` в production path.

## Production Source of Truth

Для quantile production path должен существовать один явный источник истины, который отвечает на вопрос:

**какой именно frozen winner сейчас считается рабочим production режимом?**

Рекомендуемый вариант, который фиксируется этим spec:

- хранить production manifest в отдельном small JSON artifact вне конкретного `seed_dir`;
- manifest указывает:
  - активный `seed_dir`;
  - active split (`test` как operational reference);
  - expected winner rule (`lb_gt_m`);
  - expected hold/reversal settings;
  - output mode `time;signal`.

Manifest не должен дублировать всю логику rule JSON.  
Его задача только в том, чтобы зафиксировать, **какой frozen run считается production-source**, а не пересохранять саму quantile-математику.

## Architecture

### 1. Quantile Exporter

Текущий `API/export_entry_path_v1_quantile_signals.py` остаётся основным техническим модулем экспорта.

Его production role:

- читать production manifest или явный `--seed-dir`;
- загружать frozen rule из артефактов выбранного run;
- применять rule без re-fit;
- выпускать `time;signal` для MT4;
- по флагу копировать результат в оба MT4 каталога.

### 2. Production Entry Point

Нужен более короткий operational path, чем ручная передача `--seed-dir`.

Рекомендуемый вариант:

- расширить существующий exporter режимом `--production`;
- в этом режиме CLI сам читает production manifest;
- ручной `--seed-dir` остаётся доступным для explicit fallback/debug сценариев.

Это лучше отдельного второго CLI, потому что:

- не плодит почти идентичные инструменты;
- сохраняет одну точку логики;
- делает production path коротким, но не скрывает underlying frozen artifacts.

### 3. Baseline Backup Path

Baseline path не удаляется, но его статус понижается:

- не “текущий основной winner”;
- а “backup / legacy execution path”.

Это должно быть отражено в:

- `docs/MT/ml_signal_integration.md`
- `API/README.md`
- `CONTEXT_HANDOFF.md`
- stage reports / wiki synthesis при необходимости

## CLI Design

Рекомендуемый интерфейс:

```bash
./.venv/bin/python -m API.export_entry_path_v1_quantile_signals --production --output MT/tester/files/ml_signals.csv --copy-to-mt4
```

Поведение:

- `--production` использует зафиксированный production manifest;
- `--seed-dir` остаётся как explicit override;
- одновременно требовать `--production` и `--seed-dir` нельзя;
- `--split` в production mode можно не указывать, если он уже задан в manifest;
- `--output` остаётся обязательным и в production mode.

Рекомендуемое правило интерфейса:

- production mode должен быть коротким и явным;
- debug mode должен оставаться явным и не смешиваться с production implicit selection.

## Data Flow

Production flow после этапа должен выглядеть так:

1. Production manifest выбирает canonical frozen quantile run.
2. Exporter читает:
   - manifest;
   - `entry_path_v1_quantile_filter_selected_rule.json`;
   - predictions нужного split.
3. Exporter применяет frozen winner.
4. Exporter пишет `time;signal`.
5. CSV копируется в:
   - `MT/tester/files/ml_signals.csv`
   - `MT/MQL4/Files/ml_signals.csv`
6. MT4 исполняет его через текущий `iSignal=3`.

MQL side не меняется:

- `ML_HoldBars=24`
- `ML_AllowReversal=0`
- `ML_UseScoreFilter=0`

## Error Handling

Production mode должен падать с понятной ошибкой, если:

- production manifest отсутствует;
- manifest указывает на несуществующий `seed_dir`;
- отсутствует rule JSON;
- отсутствует prediction CSV нужного split;
- manifest и frozen rule противоречат друг другу по expected rule или split;
- одновременно переданы `--production` и `--seed-dir`.

CLI не должен молча переключаться на baseline path.

## Testing

Нужны тесты на:

1. корректный выбор production source через manifest;
2. отказ при конфликте `--production` и `--seed-dir`;
3. отказ при битом manifest;
4. корректный export `time;signal` в production mode;
5. сохранение старого explicit mode через `--seed-dir`.

Отдельно полезен smoke test:

- production command выпускает `ml_signals.csv` без ручного указания `seed_dir`.

## Documentation Impact

Нужно обновить:

- `docs/MT/ml_signal_integration.md`
- `API/README.md`
- `MODULE_INDEX.md`
- `CONTEXT_HANDOFF.md` после завершения этапа

Если по факту изменится operational recommendation по tester-config, обновить также:

- `docs/MT/trading_strategy.md`

## Success Criteria

Этап считается успешным, если:

- quantile path описан как официальный рекомендуемый production export path;
- есть одна каноническая production команда без ручного выбора seed;
- baseline path остаётся доступным, но явно обозначен как backup / legacy;
- exporter behaviour полностью остаётся frozen и reproducible;
- код и docs не оставляют неоднозначности, какой именно execution mode сейчас считается основным.

## Locked Decisions

- production manifest хранится вне конкретного `seed_dir`, как отдельный operational artifact;
- production mode требует явный `--output`, чтобы exporter не делал скрытых записей по умолчанию;
- для записи сразу в оба MT4 каталога используется только явный `--copy-to-mt4`.
