# Аудит отчёта `2026-07-23-fractal0-fixed11-internal-closure-rerun.md`

Источник аудита: `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md`.

Проверенные первичные источники:

- `ML/reports/fractal0_fixed11_internal_closure_rerun.json`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_run_matrix.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_stress_cost.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_timezone_rescore.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_calendar_permutation_importance.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_calendar_no_ml_baselines.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_multiseed.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_multiseed_aggregate.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_classification.csv`
- `ML/baseline/fractal0_fixed11_internal_closure_rerun.py`
- `docs/superpowers/plans/2026-07-23-fractal0-fixed11-internal-closure-rerun.md`
- `docs/methodology/00-research-management.md`
- `docs/methodology/09-validation-freeze.md`
- `docs/methodology/11-robustness.md`
- `docs/methodology/12-backtest-costs.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/methodology/A4-verdicts-stop-conditions.md`

Итог: ключевые численные результаты fixed11-отчёта подтверждаются structured artifacts. Stress-cost, timezone rescore, calendar permutation, no-ML calendar baseline и multi-seed действительно имеют `COMPUTED` строки с заявленными row counts/risk flags. Основные проблемы не в числах, а в отчётности: header verdict не синхронизирован с JSON/decision, JSON не содержит часть статусов из research-блока отчёта, а сам отчёт не раскрывает достаточно split/hash/protocol деталей для полной воспроизводимости по `16-reporting-audit.md`.

## Подтверждённые факты

- `ML/reports/fractal0_fixed11_internal_closure_rerun.json`: `status=completed`, `overall_decision=FIXED11_INTERNAL_CLOSURE_RISK_FLAGS_RESEARCH_ONLY`, `locked_test=not_opened`, `allowed_max_verdict=research_only`, `new_winner_selected=False`.
- `run_matrix.csv`: `143` строки: `stress_cost=33`, `timezone_calendar=55`, `multiseed=55`; все строки имеют `locked_test_status=not_opened`, `provider_drift_status=NOT_IN_SCOPE`, `transfer_status=NOT_IN_SCOPE`.
- `classification.csv`: `11` строк, все `INTERNAL_CLOSURE_RISK_FLAGGED`, все `risk_flag=True`, все `new_winner_selected=False`.
- `stress_cost.csv`: `33` строки, все `COMPUTED`; risk flags: `12`; по spread: `0.2` → 11 строк/0 risk/min PF `3.266877`/min `BS_p05=2.833849`/min trades `570`; `0.4` → 11 строк/5 risk/min PF `2.722254`/min `BS_p05=2.081280`/min trades `93`; `0.8` → 11 строк/7 risk/min PF `1.320189`/min `BS_p05=0.655684`/min trades `0`.
- `timezone_rescore.csv`: `55` строк, все `COMPUTED`, `0` risk flags; min PF `2.796834`, min `BS_p05=2.327482`, min trades `378`.
- `calendar_permutation_importance.csv`: `11` строк, все `COMPUTED`, `4` risk flags; `pf_drop_ratio` range `0.201109..0.372653`, median `0.284808`.
- `calendar_no_ml_baselines.csv`: `11` строк, все `COMPUTED`, `11` risk flags; `selected_family=hour` для всех; `baseline_to_ml_pf_ratio` range `0.858790..1.069839`, median `0.978000`; для `movement_plus_time` строк baseline превышает ML PF в 4 случаях.
- `multiseed_aggregate.csv`: `11` строк, все `COMPUTED`, `0` risk flags; везде `computed_seed_count=5` и `passing_seed_count=5`.

## Замечания

### 1. Header verdict конфликтует с decision/status vocabulary

- Важность: важно.
- Место: `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md:3-7`, `18-30`, `79-89`, `119-123`; `ML/reports/fractal0_fixed11_internal_closure_rerun.json`.
- Суть проблемы: header отчёта ставит `Вердикт: DIAGNOSTIC_ONLY`, но research-блок и вывод говорят `lifecycle_status=research_only` / `allowed_max_verdict=research_only`, а JSON содержит `overall_decision=FIXED11_INTERNAL_CLOSURE_RISK_FLAGS_RESEARCH_ONLY` и вообще не содержит top-level `verdict`.
- Доказательство: команда чтения JSON показала `verdict=<MISSING>`, `overall_decision=FIXED11_INTERNAL_CLOSURE_RISK_FLAGS_RESEARCH_ONLY`, `allowed_max_verdict=research_only`. В `docs/methodology/A4-verdicts-stop-conditions.md:1-8` `diagnostic_only` и `research_only` имеют разные значения: diagnostic-only — только отладка pipeline, research-only — сигнал есть, но устойчивости/контракта недостаточно.
- Почему это важно: следующий агент не сможет однозначно понять итог этапа: это только отладочная механика или закрытие исследовательской ветки как risk-flagged `research_only`.
- Рекомендуемое исправление: выбрать один статус и синхронизировать отчёт/JSON. Если итог именно risk-flagged research-only, заменить header на `Вердикт: research_only` и добавить в JSON `verdict=research_only`. Если намеренно `DIAGNOSTIC_ONLY`, объяснить в Conclusions, почему computed fixed rerun не даёт даже `research_only`, и сменить `overall_decision`/текстовые выводы.

### 2. Top-level JSON не содержит статусы provider drift / transfer, которые отчёт заявляет

- Важность: важно.
- Место: отчёт `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md:25-30`; JSON `ML/reports/fractal0_fixed11_internal_closure_rerun.json`; код `ML/baseline/fractal0_fixed11_internal_closure_rerun.py:1500-1558`.
- Суть проблемы: отчёт явно заявляет `provider_drift_status=NOT_IN_SCOPE` и `transfer_status=NOT_IN_SCOPE`, но top-level JSON этих ключей не содержит. Эти статусы есть в `run_matrix.csv`, но не в primary JSON, который отчёт сам называет основным artifact.
- Доказательство: команда чтения JSON показала `provider_drift_status <MISSING>` и `transfer_status <MISSING>`. В коде сборки JSON на строках `1500-1558` есть `locked_test`, `allowed_max_verdict`, `new_winner_selected`, но нет top-level `provider_drift_status` / `transfer_status`.
- Почему это важно: `docs/methodology/16-reporting-audit.md:90-98` требует сверяемости ключевых чисел и статусов отчёт↔structured artifact. Сейчас часть ограничений этапа подтверждается только вторичным CSV, а не primary JSON.
- Рекомендуемое исправление: добавить в JSON top-level поля `provider_drift_status=NOT_IN_SCOPE`, `transfer_status=NOT_IN_SCOPE`, `leaderboard_rule_count=11` и `verdict`. В отчёте указать, что эти поля сверены с JSON.

### 3. Split Disclosure неполный: нет границ split и sample-size gate

- Важность: важно.
- Место: `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md:134-139`.
- Суть проблемы: раздел Split Disclosure перечисляет только роли `train_core`, `val_select`, `val_eval`, `locked_test`, но не показывает временные границы split, raw rows/events/signals/trades и sample-size gate.
- Доказательство: в отчёте строки `134-139` содержат только четыре bullet-пункта. `docs/methodology/16-reporting-audit.md:28` требует границы `train`/`validation`/`locked_test`, роли validation и `sample_size_gate`; строки `90-98` требуют количество raw rows, событий, сигналов и сделок после фильтров по каждому split.
- Почему это важно: без границ split и sample-size gate следующий агент не может проверить, что результаты не смешали роли `val_select`/`val_eval` и что малый N не маскируется агрегатным PF.
- Рекомендуемое исправление: добавить таблицу split boundaries и sample sizes. Минимально можно перенести проверенную таблицу из предыдущего source report: `train_core 2004-07-06 20:00:00..2019-06-20 14:00:00`, `val_select 2019-06-20 16:00:00..2021-03-08 03:00:00`, `val_eval 2021-03-08 05:00:00..2022-12-02 07:00:00`, плюс per-rule `val_select_n_trades`/`val_eval_n_trades` из `leaderboard_closure_audit_rules.csv` или fixed11 summaries.

### 4. Отчёт не раскрывает input hashes, хотя JSON их содержит

- Важность: важно.
- Место: `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md:56-90`, `156-166`; JSON `ML/reports/fractal0_fixed11_internal_closure_rerun.json`.
- Суть проблемы: отчёт указывает команды и primary JSON, но не содержит hash таблицу входов: source normalized JSON/CSV и `source_rules_csv`. При этом JSON содержит `source_rules_csv_sha256`, `source_input_json_sha256`, `source_input_artifact_hashes` и `input_artifact_hashes`.
- Доказательство: команда чтения JSON показала ключи `source_rules_csv_sha256`, `source_input_json_sha256`, `source_input_artifact_hashes`, `input_artifact_hashes`. В отчёте строки `56-90` этих hash не приводят. `docs/methodology/16-reporting-audit.md:31` требует команды, paths, hashes, rules, checkpoints.
- Почему это важно: fixed rerun зависит от сохранённых cutoffs и исходного normalized leaderboard. Без hash в отчёте нельзя быстро понять, какие именно входные artifacts породили результат.
- Рекомендуемое исправление: добавить в Verification или Related Materials таблицу input artifacts с `path`, `sha256`, `size_bytes`: `source_rules_csv`, source normalized JSON, summary/trades/scores из `source_input_artifact_hashes`.

### 5. Главный вывод про calendar dominance подтверждён, но протокол baseline/permutation в отчёте недораскрыт

- Важность: важно.
- Место: `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md:111-121`; код `ML/baseline/fractal0_fixed11_internal_closure_rerun.py:1136-1244`; CSV `ML/reports/fractal0_fixed11_internal_closure_rerun_calendar_no_ml_baselines.csv`.
- Суть проблемы: отчёт правильно пишет, что no-ML hour baseline флагует все 11 правил, но не раскрывает параметры выбора baseline: families, `selection_split`, `evaluation_split`, `bucket_min_trades_val_select`, `bucket_min_pf_val_select`, `bucket_min_bs_p05_val_select`, tie-breaker, `uses_rich_entry_score=False`. Для calendar permutation также не указаны `permutation_repeats`, grouping, seed formula и проверки сохранения row/index/non-calendar features.
- Доказательство: CSV содержит эти поля; код на строках `1136-1244` выбирает buckets на `val_select` с `CALENDAR_BUCKET_MIN_TRADES=30`, `CALENDAR_BASELINE_MIN_PF=1.20`, `CALENDAR_BASELINE_MIN_BS_P05=1.00`, затем применяет к `val_eval`. Отчёт строки `113-115` приводит только итоговые числа.
- Почему это важно: calendar dominance — основной аргумент закрытия ветки. Без протокола выбора baseline этот вывод выглядит сильнее, чем его воспроизводимое описание.
- Рекомендуемое исправление: добавить компактный подраздел `Calendar Diagnostic Protocol` с параметрами из CSV/JSON: families `hour/weekday/hour_weekday`, `selection_split=val_select`, `evaluation_split=val_eval`, min trades/PF/BS gates, tie-breaker, `uses_rich_entry_score=False`, `permutation_repeats=50`, grouping/seed formula и row preservation checks.

### 6. Verification results не имеют ссылочного артефакта

- Важность: улучшение.
- Место: `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md:56-73`.
- Суть проблемы: отчёт заявляет `70 passed` для targeted tests и `1442 passed, 52 warnings` для full suite, но не указывает путь к сохранённому логу или checksum вывода. Команды есть, но observed result нельзя проверить без повторного запуска.
- Доказательство: в Related Materials нет pytest log artifact; JSON содержит метрики эксперимента, но не test log. Я не перезапускал full suite в рамках аудита, чтобы не превращать аудит отчёта в повторную валидацию кода.
- Почему это важно: по `docs/methodology/16-reporting-audit.md:31` отчёт должен давать воспроизводимый след команд/версий/paths/hashes. Для долгого full suite сохранённый лог снижает риск ручной ошибки в переносе числа.
- Рекомендуемое исправление: либо добавить путь к сохранённому verification log, либо явно написать, что test result приведён как console observation и может быть перепроверен командой. Для будущих этапов сохранять `ML/reports/<stage>_verification.log` или аналогичный артефакт.

### 7. Changed Files слишком обобщён

- Важность: улучшение.
- Место: `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md:47-54`.
- Суть проблемы: пункт `this report and sync docs/wiki` скрывает конкретные изменённые файлы. В проекте уже синхронизированы `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `docs/superpowers/roadmap.md`, `MODULE_INDEX.md`, `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`.
- Доказательство: `rg` по sync-файлам показывает ссылки на `fractal0_fixed11_internal_closure_rerun` в `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `docs/superpowers/roadmap.md`, `MODULE_INDEX.md`, `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`. Отчёт строки `49-54` перечисляет только часть и обобщает остальные.
- Почему это важно: следующий агент должен быстро увидеть полный след изменений и понять, какие документы надо проверить при расхождениях.
- Рекомендуемое исправление: заменить `this report and sync docs/wiki` на явный список файлов.

## Что добавить

- Таблицу input artifact hashes из JSON.
- Таблицу split boundaries и rule-level sample sizes.
- Подраздел `Calendar Diagnostic Protocol`.
- Top-level JSON поля `verdict`, `provider_drift_status`, `transfer_status`, `leaderboard_rule_count`.
- Явное объяснение, почему header verdict выбран как `DIAGNOSTIC_ONLY`, если он не будет заменён на `research_only`.

## Команды проверки

```bash
sed -n '1,260p' docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md
sed -n '1,180p' docs/methodology/README.md
sed -n '1,170p' docs/methodology/00-research-management.md
sed -n '1,180p' docs/methodology/09-validation-freeze.md
sed -n '1,180p' docs/methodology/11-robustness.md
sed -n '1,180p' docs/methodology/12-backtest-costs.md
sed -n '1,180p' docs/methodology/16-reporting-audit.md
sed -n '1,120p' docs/methodology/A4-verdicts-stop-conditions.md
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

p = 'ML/reports/fractal0_fixed11_internal_closure_rerun'
data = json.loads(Path(p + '.json').read_text())
for k in ['status', 'verdict', 'decision', 'overall_decision', 'locked_test',
          'locked_test_status', 'allowed_max_verdict', 'provider_drift_status',
          'transfer_status', 'new_winner_selected']:
    print(k, data.get(k, '<MISSING>'))

for suffix in ['_run_matrix.csv', '_stress_cost.csv', '_timezone_rescore.csv',
               '_calendar_permutation_importance.csv',
               '_calendar_no_ml_baselines.csv', '_multiseed.csv',
               '_multiseed_aggregate.csv', '_classification.csv']:
    path = p + suffix
    header = pd.read_csv(path, sep=';', nrows=0).columns.tolist()
    cols = [c for c in ['status', 'decision', 'risk_flag', 'run_group',
                        'spread', 'timezone_shift_hours', 'seed',
                        'rule_id', 'original_rank'] if c in header]
    df = pd.read_csv(path, sep=';', usecols=cols)
    print(path, len(df))
    for c in ['status', 'decision', 'risk_flag', 'run_group']:
        if c in df:
            print(c, df[c].astype(str).value_counts().to_dict())
PY
```

## Ошибки мониторинга

- MCP: `knowledge-rag.search_similar` не нашёл `docs/reports/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md` в индексе. Проверка велась по первичным файлам проекта.
- DOC: исходная попытка прочитать skill-файл `knowledge-rag` по пути `.claude/skills/my/knowledge-rag/SKILL.md` дала `No such file or directory`; фактический путь: `.claude/skills/knowledge-rag/SKILL.md`.
