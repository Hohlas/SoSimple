# Аудит плана `time_only` robustness audit

Аудируемый документ: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`

Дата аудита: 2026-07-23

Итоговый статус: `REVISE_PLAN_BEFORE_EXECUTION`

Короткий вывод: направление выбрано правильно, потому что текущий normalized winner действительно `time_only / linear / target_entry_ev_regression / top30`, `locked_test=not_opened`, fixed `val_eval` даёт `n_trades=660`, `PF=4.0268`, `BS_p05=3.3955`. Но план нельзя исполнять как есть: в нём есть методические и реализационные несоответствия, которые могут создать ложное ощущение устойчивости.

## Проверенные источники

- `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`
- `docs/superpowers/roadmap.md`
- `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- `docs/methodology/README.md`
- `docs/methodology/09-validation-freeze.md`
- `docs/methodology/11-robustness.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/methodology/A4-verdicts-stop-conditions.md`
- `docs/README.md`
- `docs/reports/README.md`
- `ML/README.md`
- `tests/README.md`
- `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `ML/reports/fractal0_rich_entry_quality_normalized.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_trades.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_scores.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_artifact_auto_check.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_split_manifest.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_selected_score_diagnostics.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_winner_yearly.csv`

Навигация: использованы `knowledge-rag` и `graphify`; выводы ниже подтверждены первичными файлами.

## Подтверждённые факты

- Источник fixed rule существует: `ML/reports/fractal0_rich_entry_quality_normalized.json`.
- В JSON: `locked_test=not_opened`, `feature_contract_variant=normalized_atr_unit`.
- В JSON `selected_winner_val_eval`:
  - `stop_policy_id=S2_fractal0_buffer_0_5_entry_floor_2`
  - `entry_id=E3_open_pullback_1_0atr`
  - `mask_id=M0_no_mask`
  - `exit_id=X2_ml_opposite_any_p0_50`
  - `profile_id=time_only`
  - `model_id=linear`
  - `target_id=target_entry_ev_regression`
  - `filter_id=top30`
  - `score_cutoff_on_val_select=-0.026718184259660646`
  - `spread=0.2`
  - `n_trades=660`, `PF=4.026757702884287`, `BS_p05=3.3954600158428163`
  - `pf_without_best_year=3.5464977763184877`, `effective_profit_years=1.9922337231982863`, `n_years=2`
- `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv` содержит ровно одну строку fixed `val_eval` для этого правила.
- `ML/reports/fractal0_rich_entry_quality_normalized_trades.csv` содержит для fixed `val_eval/top30` 660 сделок; для того же `time_only/linear/target_entry_ev_regression` есть отдельные top40/top50 trade-строки.
- `ML/reports/fractal0_rich_entry_quality_normalized_scores.csv` содержит 4732 score-строки на `val_eval` для каждой top30/top40/top50 записи, то есть score есть для всех planned rows, но PnL в `trades.csv` сохранён только после конкретного фильтра.
- `ML/reports/fractal0_rich_entry_quality_normalized_artifact_auto_check.json` существует и имеет `overall_status=PASS`.

## Замечания

### 1. Критично: planned `block_bootstrap` фактически будет не блочным

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, строки 559-560; `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, строки 645-655; `docs/methodology/11-robustness.md`, строки 39-40 и 94-106.

Суть проблемы: план предлагает вызвать `base.block_bootstrap_pf(..., block_size=20)`, но существующая функция `block_bootstrap_pf` не использует `block_size` и делает случайную выборку отдельных сделок через `rng.choice(pnl, size=len(pnl), replace=True)`. Это обычный независимый bootstrap, а не block bootstrap.

Доказательство: `ML/baseline/benchmark_fractal0_entry_exit_grid.py:645-655` содержит параметр `block_size`, но в теле функции нет построения последовательных блоков. Методика требует учитывать временную зависимость сделок и при необходимости использовать block bootstrap вместо iid bootstrap: `docs/methodology/11-robustness.md:39-40`.

Почему это важно: `BS_p05` может быть завышен, если соседние сделки принадлежат одному рыночному режиму. Для robustness-аудита это центральная метрика, поэтому ошибка прямо влияет на итоговое решение.

Рекомендуемое исправление: реализовать отдельную функцию настоящего блочного bootstrap для этого аудита или исправить helper. В JSON явно писать `bootstrap_method=sequential_block`, `block_size`, `n_bootstrap`, `seed`. Добавить тест, который проверяет, что выборка собирается из последовательных блоков, а не из отдельных сделок.

### 2. Критично: fixed rule contract неполный

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, строки 17-32 и 160-215.

Суть проблемы: в Global Constraints fixed rule включает `S2/E3/M0/X2`, `profile`, `model`, `target`, `filter` и cutoff. Но `FixedRule` в предлагаемом коде хранит только `profile_id`, `model_id`, `target_id`, `filter_id`, `score_cutoff_on_val_select`. Проверка не защищает `stop_policy_id`, `entry_id`, `mask_id`, `exit_id`, `spread`, `split` и convention исполнения.

Доказательство: planned `FixedRule` объявлен в строках 160-166 только с пятью полями. Реальный `selected_winner_val_eval` в `ML/reports/fractal0_rich_entry_quality_normalized.json` содержит также `stop_policy_id`, `entry_id`, `mask_id`, `exit_id`, `spread`. Методика freeze требует сохранять rule JSON, threshold и execution contract: `docs/methodology/09-validation-freeze.md:35-37`.

Почему это важно: аудит может пройти `PASS` для того же `time_only/top30`, но на другой stop/entry/exit/spread механике. Тогда это уже не robustness текущего winner.

Рекомендуемое исправление: расширить `FixedRule` полями `stop_policy_id`, `entry_id`, `mask_id`, `exit_id`, `spread`, `entry_filter_score_col`. Проверять и `selected_winner`, и `selected_winner_val_eval`. В ошибке показывать expected/actual по каждому полю.

### 3. Критично: требование `UNKNOWN` при сломанном контракте не реализовано предлагаемым кодом

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, строки 31-34 и 604-607.

Суть проблемы: план требует, чтобы при другом winner или `locked_test != not_opened` audit завершался `UNKNOWN` и exit code `1`. Но предлагаемый `main()` просто вызывает `run_audit()`. При ошибке `verify_fixed_rule_contract()` будет необработанный `ValueError`, без structured JSON с `UNKNOWN_ARTIFACT_CONTRACT`.

Доказательство: строки 212-214 выбрасывают `ValueError`; строки 604-607 не ловят исключение и не записывают UNKNOWN artifact.

Почему это важно: следующий агент или автопроверка не получит нормальный машинный артефакт причины отказа. Это ломает воспроизводимость и отчётность.

Рекомендуемое исправление: в `run_audit()` или `main()` ловить contract error, записывать JSON с `status=UNKNOWN`, `decision=UNKNOWN_ARTIFACT_CONTRACT`, `locked_test=<actual>`, `contract_errors=[...]`, затем завершаться кодом `1`.

### 4. Критично: cutoff sensitivity нельзя честно расширить ниже fixed cutoff из сохранённых top30 trades

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, строки 421-436; `ML/baseline/benchmark_fractal0_entry_quality_filter.py`, строки 1987-2008.

Суть проблемы: план предлагает считать sensitivity по offsets `[-0.02, -0.01, 0.0, 0.01, 0.02]`, но использует `fixed_trades` только для `filter_id=top30`. Если cutoff ослабить, нужны сделки, которые не вошли в top30. Их PnL нет в `top30` trade-строках.

Доказательство: producer сохраняет trades только после `selected_eval = apply_entry_filter(...)`, затем `_simulate_for_filter(selected_entries, ...)`: `ML/baseline/benchmark_fractal0_entry_quality_filter.py:1987-2008`. В артефактах `top30` fixed `val_eval` имеет 660 trades, а top40/top50 представлены отдельными rows; произвольный более мягкий cutoff не восстановить только из top30 trades.

Почему это важно: отрицательные offsets дадут ложную устойчивость, потому что фактически не смогут добавить пропущенные сделки. Это делает таблицу cutoff sensitivity асимметричной и методически неверной.

Рекомендуемое исправление: один из вариантов:
- считать только ужесточение cutoff внутри top30 и явно назвать это `stricter_cutoff_within_selected_top30`;
- использовать уже сохранённые top40/top50 как discrete top-k sensitivity без нового cutoff;
- добавить отдельный diagnostic rerun, который симулирует все val_eval entries один раз без entry filter, но это уже надо явно описать как новую симуляцию без переобучения и без нового selection.

### 5. Важно: заявлен spread-stress, но в плане нет реализации и артефакта

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, строки 42-46, 60-69, 542-590; `docs/methodology/11-robustness.md`, строки 94-106.

Суть проблемы: File Structure обещает `spread-stress`, а методика robustness требует PF при stress-spread или увеличенных costs. Но список новых artifacts не содержит `time_only_robustness_audit_spread_stress.csv`, а код в Task 3 не считает stress-spread.

Доказательство: строки 60-69 перечисляют только yearly, quarterly, side, year_side, score_shift, cutoff_sensitivity, calendar_baselines. В коде строк 542-590 сохраняются те же файлы, без spread/cost stress.

Почему это важно: итоговое решение `TIME_ONLY_ROBUSTNESS_PASS_FOR_NEXT_PROBE_DESIGN` будет выглядеть как полный robustness PASS, хотя один из ключевых stress checks не выполнен.

Рекомендуемое исправление: добавить `_spread_stress.csv` и JSON-блок `spread_stress`. Если пересимуляция stress-spread невозможна из текущих artifacts, явно пометить `stress_costs_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS` и не разрешать PASS выше `REGIME_REFORMULATION_REQUIRED` без отдельного stress-прогона.

### 6. Важно: `calendar_baselines` не являются календарными baseline без ML

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, строки 45, 488-501 и 762-766; `docs/superpowers/roadmap.md`, строки 160-168.

Суть проблемы: roadmap требует сравнение с простыми календарными правилами без ML. Предложенная функция `calendar_baselines()` берёт `fixed_trades` уже выбранного ML-rule и группирует их по месяцу/кварталу. Это срез выбранных ML-сделок, а не baseline без ML.

Доказательство: `calendar_baselines()` в плане фильтрует `scores` и `trades` по fixed rule, делает merge по `position_id`, затем groupby month/quarter. Она не строит правило вида "торговать все сигналы в этот час/день/месяц" и не сравнивает с no-ML выборкой.

Почему это важно: если `time_only` winner является календарным фильтром, нужно понять, добавляет ли ML-модель что-то поверх простого календарного расписания. Текущий план этого не проверит.

Рекомендуемое исправление: добавить отдельный artifact `time_only_robustness_audit_calendar_no_ml_baselines.csv`: для тех же `S2/E3/M0/X2` и canonical spread сравнить fixed ML top30 с простыми правилами по `session_hour`, `weekday`, `hour+weekday`, месяц/квартал. Если PnL всех входов без фильтра недоступен, явно указать ограничение и не называть текущую группировку baseline.

### 7. Важно: план не включает sequential simulation при ограничении числа позиций

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, Task 2-4; `docs/methodology/11-robustness.md`, строки 17-20 и 46-53.

Суть проблемы: методика robustness требует проверить sequential simulation при ограничении числа позиций. План считает независимые trade metrics по сохранённым сделкам, но не проверяет, что будет при пересечении сделок и лимите одновременных позиций.

Доказательство: в интерфейсах Task 2-4 нет функции или artifact для sequential simulation/position constraint. Методика указывает эту проверку отдельным шагом: `docs/methodology/11-robustness.md:19`.

Почему это важно: высокая aggregate PF может быть недостижима в реальном исполнении, если сделки перекрываются и не все могли быть открыты одновременно. Методика прямо предупреждает, что SeqPF должен быть diagnostic для position-constraint анализа.

Рекомендуемое исправление: добавить diagnostic artifact `time_only_robustness_audit_sequential.csv` или явно зафиксировать `sequential_position_constraint_status=NOT_RUN` в JSON/report и не использовать это как полный robustness PASS.

### 8. Важно: decision gates не проверяют per-side PF и не раскрывают основу порогов

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, строки 504-532; `docs/methodology/11-robustness.md`, строки 48-53.

Суть проблемы: `robustness_decision()` проверяет per-side `mean_pnl_r > 0` и `n_trades >= 30`, но не проверяет per-side PF. Также пороги `side_sample >= 30` и `cutoff n_trades >= 300` не обоснованы в плане.

Доказательство: строки 519-524 содержат только side mean, side sample и cutoff sample. Методика требует не скрывать side-specific failure balance metric: `docs/methodology/11-robustness.md:51`.

Почему это важно: сторона может иметь положительный средний PnL на редких больших выигрышах и плохой PF/просадку. Тогда side-specific weakness будет пропущена.

Рекомендуемое исправление: добавить side gates: `min_side_pf`, `min_side_bs_p05` или хотя бы `min_side_pf >= 1.0`, `side_n_trades` как warning на коротком окне, `side_max_drawdown_r`. Пороги записать в JSON как `decision_gate_config`.

### 9. Важно: `score_cutoff_on_val_select` противоречит roadmap для следующего one-rule probe

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, строка 28; `docs/superpowers/roadmap.md`, строки 128-140; `ML/reports/fractal0_rich_entry_quality_normalized.json`.

Суть проблемы: текущий план аудита использует cutoff `-0.026718184259660646`, и это соответствует normalized JSON. Но roadmap в разделе следующего `time_only` one-rule replication/probe всё ещё содержит `score_cutoff_on_val_select=-0.026392849103777025`.

Доказательство: `docs/superpowers/roadmap.md:139` указывает `-0.026392849103777025`; JSON и artifact auto-check содержат `-0.026718184259660646`.

Почему это важно: после robustness-аудита следующий frozen/probe может стартовать с другим cutoff, чем audited rule. Это нарушит traceability.

Рекомендуемое исправление: перед закрытием этапа обновить roadmap: в следующем one-rule probe использовать cutoff из `ML/reports/fractal0_rich_entry_quality_normalized.json` или явно объяснить, почему roadmap хранит старый cutoff и что он superseded.

### 10. Важно: загрузка CSV целиком противоречит локальному правилу работы с большими CSV

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, строки 178-190; `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`, строка 460.

Суть проблемы: `_csv(path)` делает `pd.read_csv(path, sep=";")` без `usecols`, `nrows` или chunking. При этом прошлый отчёт явно предупреждает, что `scores.csv` и `trades.csv` большие и их надо читать с `usecols`, `nrows` или chunks.

Доказательство: planned code строк 178-190 загружает целиком summary, trades и scores. `docs/reports/...normalized-rerun.md:460` говорит читать большие CSV через `usecols`, `nrows` или chunks.

Почему это важно: аудит может стать медленным и нестабильным по памяти, хотя ему нужны ограниченные колонки.

Рекомендуемое исправление: в `load_normalized_artifacts()` читать `summary`, `trades`, `scores` с `usecols` под конкретные функции. Для агрегатов по fixed rule можно читать chunk-ами и фильтровать по `profile/model/target/filter/split`.

### 11. Улучшение: отчётный шаблон неполный относительно методики отчётности

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, строки 730-810; `docs/methodology/16-reporting-audit.md`, строки 18-30 и 64-104; `docs/reports/README.md`.

Суть проблемы: planned report содержит Context, What Was Done, Results, Interpretation, Next Step, Artifacts, Verification. Но методика требует также уровень этапа, Multiple Testing Context, Changed Files, Conclusions, Limitations / Open Questions, Split Disclosure, Related Materials и research-first disclosure.

Доказательство: `docs/methodology/16-reporting-audit.md:18-30` перечисляет обязательные секции; строки 64-86 требуют research-first disclosure для исследовательских отчётов с PnL/PF.

Почему это важно: robustness-аудит будет показывать PF/PnL и может породить следующий probe. Без explicit disclosure легко неправильно повысить статус до кандидата.

Рекомендуемое исправление: расширить шаблон отчёта:
- добавить `Уровень этапа: проверочный audit поверх validation artifacts, not locked_test`;
- добавить `Multiple Testing Context`: это no-new-search audit одного правила, но origin bias идёт из broad normalized search;
- добавить `Split Disclosure`;
- добавить `Limitations / Open Questions`;
- добавить `forbidden_interpretations` рядом с PF/PnL;
- добавить `Changed Files` и `Related Materials`.

### 12. Улучшение: новый скрипт требует отдельной документации, а не только ссылки в старой странице

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, строки 55-56 и 831-842; `docs/README.md`, строки 20-23.

Суть проблемы: план создаёт новый модуль `ML/baseline/audit_time_only_robustness.py`, но предлагает только добавить короткую секцию в `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`.

Доказательство: `docs/README.md:22` требует для нового или изменённого модуля обновить связанную страницу в `docs/` и строку в `MODULE_INDEX.md`.

Почему это важно: следующий агент может искать документацию по новому скрипту и не найти отдельный контракт запуска, входы, выходы и ограничения.

Рекомендуемое исправление: создать `docs/ML/audit_time_only_robustness.py.md` с назначением, входами, выходами, командой запуска, ограничениями и ссылкой на normalized source artifacts. В старой странице оставить только cross-link.

### 13. Вопрос: multi-seed и provider drift сознательно исключены или отложены?

Место: `docs/superpowers/plans/2026-07-23-time-only-robustness-audit.md`, весь план; `docs/methodology/11-robustness.md`, строки 20-23 и 108-112.

Суть проблемы: методика robustness включает multi-seed и provider drift. План ограничен одним saved normalized run и одним инструментом. Это может быть допустимо для первого audit-slice, но должно быть явно названо ограничением.

Доказательство: `docs/methodology/11-robustness.md:21-23` требует multi-seed и provider drift в полном robustness-контуре. План их не реализует.

Почему это важно: итоговое решение может быть прочитано как полный robustness PASS, хотя это только validation-slice audit.

Рекомендуемое исправление: в Goal/Global Constraints добавить: `scope=validation_artifact_robustness_slice`, `multi_seed_status=NOT_RUN`, `provider_drift_status=NOT_RUN`, `locked_test_status=not_opened`. В decision wording избегать слова `PASS`, если stress/multi-seed/provider не выполнены; лучше `TIME_ONLY_ROBUSTNESS_SLICE_OK_FOR_NEXT_PROBE_DESIGN`.

## С чем не согласен

1. Не согласен с тем, что предложенный `block_bootstrap_pf` можно использовать как block bootstrap. По коду это независимая перестановка отдельных сделок.

2. Не согласен с тем, что current fixed rule contract защищён достаточно. Без `S2/E3/M0/X2` и `spread=0.2` это не контракт текущего winner.

3. Не согласен с тем, что cutoff sensitivity можно считать симметрично вокруг cutoff из top30 trades. Ослабление cutoff требует PnL для сделок ниже top30, а текущий saved `top30` trade artifact их не содержит.

4. Не согласен с названием `calendar_baselines` для текущей реализации. Это календарные срезы ML-selected trades, а не baseline без ML.

5. Не согласен с возможностью `TIME_ONLY_ROBUSTNESS_PASS_FOR_NEXT_PROBE_DESIGN`, если spread/cost stress не выполнен или явно не помечен как deferred.

## Что добавить перед исполнением

1. Полный `FixedRule`:
   `stop_policy_id`, `entry_id`, `mask_id`, `exit_id`, `spread`, `profile_id`, `model_id`, `target_id`, `filter_id`, `entry_filter_score_col`, `score_cutoff_on_val_select`.

2. Настоящий block bootstrap или честное переименование текущей оценки в iid bootstrap с понижением статуса.

3. Отдельный `spread_stress` artifact или явный `NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`.

4. Честную cutoff/top-k sensitivity:
   - stricter cutoff inside top30;
   - top30/top40/top50 fixed artifacts;
   - или новая пересимуляция all-entry val_eval без нового selection.

5. Простые calendar no-ML baselines, если цель - проверить, не является ли `time_only` просто календарным фильтром.

6. Sequential position-constraint diagnostic или явное `NOT_RUN`.

7. Decision gate config в JSON: пороги для side PF, side N, concentration, bootstrap, stress costs, cutoff fragility.

8. Полный report template по `docs/methodology/16-reporting-audit.md`.

9. Синхронизацию cutoff в `docs/superpowers/roadmap.md` перед выбором следующего one-rule probe.

10. Отдельную docs-страницу для нового скрипта `docs/ML/audit_time_only_robustness.py.md`.

## Рекомендуемый статус плана

`REVISE_PLAN_BEFORE_EXECUTION`.

План годится как направление, но перед запуском нужно исправить минимум пункты 1-6 из раздела замечаний. Иначе результат может быть воспроизводимым технически, но методически слабым: он не докажет устойчивость `time_only`, а только создаст ещё один набор диагностических срезов.
