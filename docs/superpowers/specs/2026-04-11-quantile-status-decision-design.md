# Quantile Status Decision Design

> **Date**: 2026-04-11
> **Status**: Draft
> **Goal**: Определить, может ли `entry_path_v1_quantile` стать parallel execution mode, через research по увеличению N и жёсткий go/no-go gate
> **Supersedes**: `2026-04-11-entry-path-v1-quantile-production-path-design.md` (подход изменён: research-first вместо прямого перевода в production)

## Context

На 2026-04-11 линия `entry_path_v1_quantile` подтверждена по двум осям:

- Multi-seed robustness-pass: `same_rule_count=5`, winner `lb_gt_m` во всех seed, verdict `go_mt4`.
- MT4 parity-check: 8 сделок, PF=58.88, DD=2.85%, reconciliation полный.

Однако **N=8 (MT4) / 20–26 (test по seed)** — слишком мало для production confidence. Текущий winner нельзя переводить в production без увеличения числа сделок и прохождения gate.

## Decision

Принимается подход **Research → Gate → Productionize**:

1. Сначала research по увеличению N (relax filter, multi-seed ensemble).
2. Жёсткий go/no-go gate на frozen test.
3. Production path строится **только** если gate пройден.
4. Если gate не пройден — quantile остаётся research-only, план закрывается отчётом.

Текущий frozen winner `lb_gt_m` **не** выносится в production path до прохождения gate.

## Alternatives Considered

1. **Research → Gate → Productionize (выбран)** — zero wasted engineering, строгая дисциплина. Минус: медленнее.
2. **Productionize текущий + Research параллельно** — infrastructure готова заранее, текущий winner копит track record. Минус: productionize вариант, не прошедший gate.
3. **Research → Productionize только улучшенную версию** — то же что (1), различие в формулировке.

Выбран (1) потому что при N=8 нет оснований давать текущему варианту production status, даже параллельный.

## Go/No-Go Gate

| Критерий | Порог | Как проверяется |
|----------|-------|-----------------|
| N (test) | >= 30 | count trades на frozen test |
| PF (test) | > 2.0 | sum_wins / sum_losses на frozen test |
| negative_year_slices | = 0 | yearly PF по годовым срезам test split (срезы с N < 3 trades исключаются из проверки) |
| multi-seed stability | same winner >= 4/5 seeds | только для relax-варианта |
| MT4 parity | confirmed | trade-level reconciliation после финальных изменений |

Gate применяется на frozen test результате лучшего кандидата. MT4 parity — отдельный финальный шаг после прохождения первых четырёх критериев.

## Architecture

```
Research Stage                    Production Stage
+-----------------------+        +-----------------------+
| 1. Relax filter       |        | 4. Production path    |
| 2. Multi-seed         |--gate->| 5. MQL integration    |
|    ensemble           | N>=30  | 6. MT4 parity-check   |
| 3. Gate evaluation    | PF>2.0 | 7. Docs & freeze      |
|                       | neg=0  |                       |
+-----------------------+        +-----------------------+
         |
         v gate failed
   Verdict: "not ready"
   Plan закрывается
```

## Research Stage

### Вход

- Frozen baseline: `A @ 7.5%` (checkpoint `transformer_entry_path_v1_quantile_best.pt`).
- Текущий quantile winner: `lb_gt_m`.
- 5 seed checkpoints: `seed_{007,017,042,077,123}`.
- Benchmark script: `ML/benchmark_entry_path_v1_quantile_filter.py`.

### Шаг 1 — Relax filter (приоритет выше)

На validation:

- Перебрать все quantile rules из benchmark (не только `lb_gt_m`) — найти правила с N>=30 и PF>2.0.
- Для `lb_gt_m` попробовать ослабленные пороги: `lb > q40`, `lb > q30` и т.д. вместо строгого `lb > median`.
- Winner фиксируется на validation. Один frozen прогон на test.
- Multi-seed check: повторить на 5 seed, проверить `same_winner >= 4/5`.

### Шаг 2 — Multi-seed ensemble (если шаг 1 не дал gate-pass)

- Взять predictions из 5 seed (`007, 017, 042, 077, 123`).
- Два варианта агрегации:
  - **Mean quantile**: усреднить `pred_ret_24_q10` / `pred_ret_24_q90` по seed, применить filter rules.
  - **Majority vote**: сигнал проходит, только если >= 3/5 seed его пропускают.
- Benchmark на validation по тем же правилам. Winner -> frozen test.

### Шаг 3 — Gate evaluation

Применить go/no-go gate к frozen test результату лучшего кандидата (из шага 1 или 2).

- **Gate pass** -> переход к Production Stage.
- **Gate fail** -> отчёт с verdict "not ready", plan закрывается.

### Выход

- `ML/reports/entry_path_v1_quantile_n_boost_result.json`
- Stage report в `docs/reports/`

## Production Stage

Выполняется **только** если gate пройден.

### Шаг 4 — Production export path

- Адаптировать `API/export_entry_path_v1_quantile_signals.py` под winning вариант:
  - Relaxed filter -> обновить правило/порог в exporter.
  - Ensemble -> добавить агрегацию predictions из нескольких seed.
- Выход: `MT/MQL4/Files/ml_signals_quantile.csv` — отдельный файл, не затрагивает `ml_signals.csv`.
- Формат: `time;signal` (совместим с `lib_ML_Signal.mqh`).

### Шаг 5 — MQL integration

- Новый параметр EA: `ML_SignalSource` = `"ml_signals.csv"` (default) / `"ml_signals_quantile.csv"`.
- Никаких изменений в логике `ML_TRADE()` — меняется только загружаемый CSV.
- Baseline `A @ 7.5%` через `ml_signals.csv` остаётся default и не затрагивается.

### Шаг 6 — MT4 parity-check

- Прогон MT4 tester с `ML_SignalSource = ml_signals_quantile.csv`.
- Trade-level reconciliation: MT4 log vs Python predictions.
- Acceptance: `Opened == N_expected`, расхождения объяснимы.

### Шаг 7 — Docs & freeze

- Stage report в `docs/reports/`.
- Обновить `CONTEXT_HANDOFF.md`: quantile = parallel execution mode.
- Обновить `CHANGELOG.md`.
- Wiki ingest.

## Exit Criteria

- **Success**: quantile работает параллельно с baseline в MT4, gate criteria подтверждены, MT4 parity пройден, документация обновлена.
- **Failure**: research не дал кандидата, проходящего gate. Отчёт зафиксирован, quantile = research-only.

## Risks

| Риск | Mitigation |
|------|------------|
| Ослабление фильтра убивает PF | Validation-first: порог подбирается только на validation, test — один frozen прогон |
| Ensemble не увеличивает N (seed видят одни и те же сделки) | Проверяется эмпирически; если overlap > 80%, ensemble бесполезен — фиксируем в отчёте |
| MQL-параметр `ML_SignalSource` ломает существующий контур | Default остаётся `ml_signals.csv`, изменение минимально (только имя файла при загрузке) |
| Low-N природа сохраняется даже после research | Gate N>=30 — минимальный порог; если не пройден, plan честно закрывается |
