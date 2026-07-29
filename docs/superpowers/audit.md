# Аудит отчёта `2026-07-29-fixed11-python-h1-chronology-fix`

Проверяемый файл: `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`

Проверка выполнена по связанным первоисточникам: плану
`docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md`,
методике `docs/methodology`, затронутому коду, тестам и новым
`ML/reports/*_h1_chronology_fix*` артефактам. `knowledge-rag` и `graphify`
использовались только как навигация, выводы ниже подтверждены файлами и
командами.

## Подтверждено

- Ключевые числа отчёта совпадают с
  `ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json` и
  `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json`.
- Hash для двух указанных в отчёте primary artifacts совпадает с `sha256sum`.
- Точечные тесты из отчёта проходят:
  `./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q`
  → `50 passed`;
  `./.venv/bin/python -m pytest tests/test_fractal0_fixed11_rich_entry_locked_test.py -q`
  → `2 passed`.
- Старые locked-test/current-history артефакты не перезаписаны:
  `git diff -- ML/reports/fractal0_fixed11_rich_entry_locked_test.json ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv`
  вернул пустой diff.

---

## 1. Финальный `DIAGNOSTIC_ONLY` не воспроизводится командами из отчёта

- **Важность:** важно
- **Место:** `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`, раздел `Verification`, строки 66-76; раздел `Results`, строка 90
- **Суть проблемы:** отчёт говорит, что после принудительной диагностической маркировки итог стал `verdict=DIAGNOSTIC_ONLY`, но в списке команд указана только runner-команда. Эта команда сама по себе пишет исходный verdict `reject` или `candidate_check_required`, а не финальный diagnostic override.
- **Доказательство:**
  - В отчёте перечислены только две pytest-команды и runner-команда: `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md:70-73`.
  - Код wrapper-а создаёт `selection_df["decision"]` как `KEEP_CANDIDATE` или `REJECT`: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py:256-268`.
  - Код wrapper-а пишет JSON verdict как `candidate_check_required` или `reject`: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py:284-288`.
  - `main()` только печатает этот artifact, отдельного diagnostic override там нет: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py:355-357`.
  - Текущий JSON уже содержит patched поля `verdict=DIAGNOSTIC_ONLY`, `allowed_max_verdict=DIAGNOSTIC_ONLY`, `original_runner_verdict=reject`: команда
    `rg -n "verdict|allowed_max_verdict|original_runner_verdict" ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json`.
- **Почему это важно:** следующий запуск команды из отчёта может перезаписать финальный JSON/selection CSV в недиагностическом виде и сломать hash-и, приведённые в отчёте. Это нарушает требование воспроизводимости из `docs/methodology/16-reporting-audit.md:31` и `docs/methodology/16-reporting-audit.md:106-110`.
- **Рекомендуемое исправление:** добавить в `Verification` точную команду post-processing из плана, которая ставит `DIAGNOSTIC_ONLY` и diagnostic selection columns, либо лучше добавить в wrapper явный флаг вроде `--diagnostic-only --allowed-max-verdict DIAGNOSTIC_ONLY` и обновить отчёт/команды под этот флаг.

---

## 2. `ml_exit_timing_contract` заявлен сильнее, чем доказано текущими колонками

- **Важность:** важно
- **Место:** `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`, строки 23, 34, 108-110
- **Суть проблемы:** отчёт и JSON заявляют `feature_time <= decision_time <= execution_time`, но `decision_time` в `build_exit_decision_rows(...)` хранит timestamp H1-бара, из которого уже берутся `high/low/close`. Если H1 `time` означает начало часа, то эти признаки становятся известны только на следующем H1-open, то есть не к записанному `decision_time`.
- **Доказательство:**
  - M5-окно для H1 строится как `[h1_time, h1_time + 1 hour)`, значит `h1_time` используется как начало H1-бара: `ML/baseline/benchmark_fractal0_entry_exit_grid.py:415-428`.
  - В `build_exit_decision_rows(...)` признаки берутся из `highs/lows/closes[idx]`: `ML/baseline/benchmark_fractal0_entry_exit_grid.py:807-819`.
  - В той же строке `decision_time` пишется как `times[idx]`, а `first_exit_execution_time` как `times[idx + 1]`: `ML/baseline/benchmark_fractal0_entry_exit_grid.py:839-840`.
  - Тест закрепляет именно такую схему: при барах `10:00, 11:00, 12:00` первая строка имеет `decision_time=11:00`, `first_exit_execution_time=12:00`: `tests/test_fractal0_entry_exit_grid.py:502-507` и `tests/test_fractal0_entry_exit_grid.py:553-583`.
  - Методика требует явно зафиксировать open/close бара и момент решения: `docs/methodology/03-feature-contract-leakage.md:46-56`, `docs/methodology/03-feature-contract-leakage.md:81-84`.
- **Почему это важно:** downstream может прочитать `decision_time=11:00` как момент, когда модель уже могла принять решение, хотя признаки H1-бара `11:00-12:00` доступны только после закрытия этого бара. Это создаёт риск ошибки в будущем export/parity и делает JSON-контракт неоднозначным.
- **Рекомендуемое исправление:** либо заменить/дополнить поля на явные `decision_bar_time`, `feature_available_time`, `ml_decision_time`, `first_exit_execution_time`; либо писать `decision_time = times[idx + 1]`, если решение действительно принимается после закрытия бара `idx`. В отчёте уточнить, что текущий `decision_time` является меткой feature bar, а не фактическим временем доступности решения, если сохраняется старое имя.

---

## 3. `Changed Files` неполный относительно фактических изменений этапа

- **Важность:** важно
- **Место:** `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`, строки 58-64
- **Суть проблемы:** раздел перечисляет только пять файлов, но текущий этап фактически изменил больше связанных файлов документации/контекста и создал новые docs/ML/report artifacts.
- **Доказательство:**
  - В отчёте указаны только `benchmark_fractal0_entry_exit_grid.py`, `benchmark_fractal0_entry_quality_filter.py`, `run_fractal0_fixed11_rich_entry_locked_test.py`, `tests/test_fractal0_entry_exit_grid.py`, сам новый report: `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md:58-64`.
  - `git diff --name-only` показывает также `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `MODULE_INDEX.md`, `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`, `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`, `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`, `docs/superpowers/roadmap.md`, `wiki/REPO_integrity.md`, `wiki/index.md`, `wiki/log.md`, `wiki/research/fractal-stop-research.md`.
  - `git ls-files --others --exclude-standard` показывает новые `ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json`, `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json`, `docs/ML/run_fractal0_fixed11_rich_entry_locked_test.py.md`, `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`.
  - Методика отчётности включает `modified files` во входы отчёта: `docs/methodology/16-reporting-audit.md:7-14`.
- **Почему это важно:** следующий агент не увидит полный объём синхронизации контекста и может пропустить связанные изменения в wiki/changelog/module docs.
- **Рекомендуемое исправление:** расширить раздел `Changed Files` или разделить его на `Code/test changes`, `Documentation/context changes`, `Generated artifacts`. Включить все изменённые связанные файлы либо явно написать, что список намеренно показывает только source/test файлы, а остальные перечислены отдельно.

---

## 4. Раздел `Artifacts` пропускает два generated CSV и не даёт hashes для большинства outputs

- **Важность:** улучшение
- **Место:** `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`, строки 78-84
- **Суть проблемы:** wrapper создаёт `_yearly.csv` и `_side.csv`, эти файлы существуют, но в отчёте они не перечислены. Hash-и указаны только для JSON и trades CSV, хотя методика требует фиксировать paths и hashes.
- **Доказательство:**
  - Отчёт перечисляет JSON, trades, summary, selection и comparison: `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md:78-84`.
  - Фактически существуют также `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix_yearly.csv` и `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix_side.csv`: команда `ls -l ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix* ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json`.
  - Код wrapper-а всегда пишет `summary_csv`, `trades_csv`, `yearly_csv`, `side_csv`, `selection_csv`: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py:270-282`.
  - Hash-и для неуказанных/нехешированных файлов по текущей рабочей копии:
    - `summary.csv`: `b9a00b19c19200b4e939829327c12d43d6cc3dec6e1d064a0b725918d0979b66`
    - `selection.csv`: `1ba8896906196b2978d6526ca699dd42f5b002c9a682640c8544aef798cb11a6`
    - `side.csv`: `cc1aa29ac7bc39bd464b66faa8c0c5e67deab0382a527710fafba5be3e8b9ed0`
    - `yearly.csv`: `893ddc92eaf249082587bee5fcd2b3418890a2c5ef33b9dfcc828cdf2942ca6a`
    - `comparison.json`: `65c0a1129d1883fb1f50ac79c4e3468a1fb43dfacaa7e198163aa057dcdb3ef3`
  - Методика требует указывать paths и hashes: `docs/methodology/16-reporting-audit.md:31`; ключевые числа должны сверяться со structured artifact: `docs/methodology/16-reporting-audit.md:96-97`.
- **Почему это важно:** отчёт хуже воспроизводится: часть generated outputs остаётся “невидимой”, а hashes для CSV, по которым можно проверять yearly/side/selection, отсутствуют.
- **Рекомендуемое исправление:** добавить `_yearly.csv` и `_side.csv` в `Artifacts`; добавить sha256 для всех generated outputs или явно обозначить primary/secondary artifacts и дать hash хотя бы для всех файлов, из которых берутся выводы.

---

## 5. Нет раскрытия scaler/normalization для movement-score части wrapper-а

- **Важность:** важно
- **Место:** `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`, разделы `Methodology`, `What Was Done`, `Split Disclosure`; `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json`
- **Суть проблемы:** отчёт корректно говорит, что M5 не стал ML input, но не раскрывает scaler/normalization contract для части, где wrapper заново считает `movement_score` для locked_test.
- **Доказательство:**
  - Wrapper использует `RobustScaler`, fit на train features и transform locked_test features: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py:80`, `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py:98-101`.
  - Затем обучает модель и пишет `movement_score`: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py:104-116`.
  - JSON содержит только краткое поле `movement_score_for_locked_test`, без `normalization_config`, `normalized_feature_distribution_audit` или `scale_contract`: `rg -n "normalization_config|scale_contract|normalized_feature_distribution_audit|movement_score_for_locked_test" ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json`.
  - Методика требует для моделей со scaler/normalization указать `normalization_config`, где fit-ился scaler, audit распределений и `scale_contract`: `docs/methodology/16-reporting-audit.md:33-42`, `docs/methodology/16-reporting-audit.md:98-100`.
- **Почему это важно:** даже при `DIAGNOSTIC_ONLY` следующий агент должен понимать, что отрицательный rerun не вызван скрытым изменением preprocessing/scaler-контракта. Сейчас это можно проверить только через код, а не через отчёт/JSON.
- **Рекомендуемое исправление:** добавить в отчёт и JSON отдельный блок: `movement_score_model_contract`, `normalization_config=RobustScaler fit on train only`, `locked_test_not_used_for_scaler_fit=true`, ссылку на исходный frozen movement protocol или явное объяснение, почему A7/scale audit не применялся в этом debug rerun.

---

## 6. Уровень этапа сформулирован двусмысленно относительно методики

- **Важность:** улучшение
- **Место:** `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`, строки 15-17
- **Суть проблемы:** отчёт называет этап “Проверочный debug/parity этап”. По смыслу это diagnostic rerun после изменения контракта, а не полноценная проверочная candidate-стадия. Формулировка может быть прочитана как confirmatory-проверка, хотя сам отчёт правильно ставит `DIAGNOSTIC_ONLY`.
- **Доказательство:**
  - Строка отчёта: `Проверочный debug/parity этап`: `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md:15-17`.
  - Методика требует явно указать уровень “поисковый / проверочный” и для проверочного уровня указать, что было заморожено до запуска: `docs/methodology/16-reporting-audit.md:18-23`, `docs/methodology/16-reporting-audit.md:90-92`.
  - Методика locked-test говорит, что смена execution convention после freeze делает такой locked_test невалидным как тот же проверочный результат: `docs/methodology/10-frozen-test-oos.md:27-38`, `docs/methodology/10-frozen-test-oos.md:47-54`.
- **Почему это важно:** статус `DIAGNOSTIC_ONLY` выставлен правильно, но слово “проверочный” без уточнения может создать ложное ощущение, что это новый confirmatory locked-test.
- **Рекомендуемое исправление:** заменить на более точное: “Диагностический debug/parity rerun в проверочном контуре; не новый confirmatory locked-test и не candidate evidence”. В `Multiple Testing Context` добавить `lifecycle_status=diagnostic_rerun_after_contract_bugfix`.

---

## 7. `Multiple Testing Context` не раскрывает cumulative budget и изменение fill convention в машинно-читаемом виде

- **Важность:** улучшение
- **Место:** `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`, строки 48-56
- **Суть проблемы:** отчёт указывает, что новых rules/cutoffs/profiles/models/targets/filters/spreads не было, но методика требует current и cumulative search budget с учётом entry/exit policy, spread/fill convention, transforms/scalers и filters. Изменение ML-exit feature contract и fill/execution convention описано текстом, но не раскрыто в самом budget-блоке.
- **Доказательство:**
  - Текущий блок содержит только `fixed rules tested: 11`, `new rules/cutoffs/profiles/models/targets/filters/spreads: 0`, `status: diagnostic rerun`: `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md:48-56`.
  - Методика требует current и cumulative search budget с перечислением моделей, профилей, таргетов, сторон, горизонтов, seed, инструментов, entry/exit policy, spread/fill convention, transforms/scalers, filters и параметров: `docs/methodology/16-reporting-audit.md:18-23`.
  - JSON содержит `current_search_budget`, но там тоже нет явного `changed_fill_convention=true` или ссылки на cumulative budget id: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py:333-335`.
- **Почему это важно:** именно изменение fill/execution convention является причиной `DIAGNOSTIC_ONLY`. Если оно не отражено в budget-блоке, будущий читатель может ошибочно считать rerun тем же frozen-chain экспериментом с нулевым изменением условий.
- **Рекомендуемое исправление:** расширить блок до явного вида:
  `current_search_budget: fixed_rules=11, new_selection=0, changed_ml_exit_feature_contract=true, changed_fill_execution_convention=true, changed_spread=false`;
  `cumulative_search_budget: inherited_from=<fixed11 reports>`;
  `allowed_max_verdict=DIAGNOSTIC_ONLY`.

---

## 8. Для проваленного fixed11 path не указано, выполнен ли post-mortem или почему он отложен

- **Важность:** улучшение
- **Место:** `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`, строки 116-142
- **Суть проблемы:** вывод говорит, что edge исчез и ветку нужно остановить или перевести в post-mortem, но отчёт не фиксирует, выполнен ли post-mortem или почему он не выполнялся в этом этапе.
- **Доказательство:**
  - Вывод: `PF max < 1`, path должен быть остановлен или переведён в post-mortem: `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md:116-118`.
  - Next Step предлагает принять решение между post-mortem и diagnostic-only MT4 parity: `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md:137-142`.
  - Методика требует для `FAIL`/`reject` результата указать, выполнен ли post-mortem, а если нет — причину: `docs/methodology/16-reporting-audit.md:57-62`, `docs/methodology/16-reporting-audit.md:102-104`.
- **Почему это важно:** результат фактически `reject` до diagnostic marking (`original_runner_verdict=reject`) и разрушает старый edge. Без явного post-mortem status следующий шаг остаётся менее определённым.
- **Рекомендуемое исправление:** добавить короткий блок `Post-mortem status`: `not done in this stage; reason: chronology bug explains invalidation, separate A5 post-mortem required only if continuing fixed11 mechanics` либо сразу оформить post-mortem как следующий обязательный документ перед новой исследовательской веткой.

