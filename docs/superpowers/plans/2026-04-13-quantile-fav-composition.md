# Composition Track — entry_path_v1_quantile × fav_3_vs_12

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Решить **бинарный вопрос**: даёт ли композиция фильтра `fav_3_vs_12 <= 0.653` поверх production-rule `entry_path_v1_quantile` (`lb_gt_m_q35`) измеримый прирост качества **на тех же данных, на которых quantile уже PASS прошёл n-boost gate**, или композиция — лишнее усложнение и направление надо явно закрыть.

Этот план **не разрабатывает новый production-режим**. Это короткое исследование с заранее зафиксированными gate-критериями: либо composition побеждает по чётко описанным метрикам — и тогда мы открываем отдельный production-плана; либо нет — и тогда мы пишем verdict-отчёт «closed» и фиксируем направление как dead end в roadmap.

**Architecture:** Read-mostly research. Никаких MT4-патчей, никакого нового frozen rule, никаких изменений в `processing/` и `ML/train.py`. Создаётся ровно один новый бенчмарк-скрипт, который **переиспользует существующие функции** из `API/export_entry_path_v1_quantile_signals.py` и `API/signal_path_atlas.py`. Все артефакты под `ML/reports/quantile_fav_composition/`.

**Tech Stack:** Python 3.11, pandas/numpy, pytest, существующие модули `API.export_entry_path_v1_quantile_signals`, `API.signal_path_atlas`, `ML.benchmark_entry_path_v1_quantile_filter`. Никаких новых зависимостей.

**Non-goals:**
- Не переобучать модели (ни baseline regression_updn, ни quantile, ни pred_fav_*).
- Не пересматривать порог `fav_3_vs_12 <= 0.653` — он берётся как есть из [docs/reports/2026-04-04-archetype-filter-bridge.md](../../reports/2026-04-04-archetype-filter-bridge.md).
- Не пересматривать winner `lb_gt_m_q35` или его параметры (m, w, correction).
- Не подключать composition к MT4, не править `MT/MQL4/Files/ml_signals.csv`.
- Не вводить новый production rule до прохождения формального gate (см. Task 6).
- Не оптимизировать порог `fav_3_vs_12` под composition — это будет p-hacking над уже выбранной величиной.
- Не трогать `ratio_3_vs_12` или другие фильтры из Variant 4 — план ровно про `fav_3_vs_12`.

---

## File Structure

### Read First
- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`
- `docs/reports/2026-04-04-archetype-filter-bridge.md` (источник порога 0.653)
- `docs/reports/2026-04-12-quantile-status-decision.md` (production verdict quantile)
- `docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md` (n-boost gate описание)
- `wiki/concepts/signal-archetypes.md`
- `wiki/research/execution-tracks.md`
- `ML/reports/entry_path_v1_quantile_selected_rule.json`

### Existing Inputs (do not modify)
- `API/export_entry_path_v1_quantile_signals.py` — `apply_production_rule`, `load_rule_payload_from_file`, `_resolve_baseline_predictions_path`
- `ML/benchmark_entry_path_v1_quantile_filter.py` — `attach_baseline_score`, `apply_conformal_correction`, `build_rule_mask`
- `API/signal_path_atlas.py` — `pred_fav_3`, `pred_fav_12`, формула `fav_3_vs_12 = pred_fav_3 / pred_fav_12.clip(lower=eps)` (строка ~117)
- `ML/reports/entry_path_v1_quantile_selected_rule.json` — winner `lb_gt_m_q35` + `baseline_threshold` + `baseline_rule_path`
- `ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_{validation,test}_predictions.csv`
- baseline-предсказания `regression_updn`, через `_resolve_baseline_predictions_path`

### Files To Create
- `ML/benchmark_quantile_fav_composition.py` — единственный новый скрипт. Делает join {quantile predictions} × {signal_path_atlas frame с `fav_3_vs_12`} по `(time, signal)` и считает срезы для четырёх режимов:
  - `Q` — только quantile rule (PASS как есть)
  - `F` — только `fav_3_vs_12 <= 0.653` (поверх baseline regression_updn)
  - `Q ∩ F` — пересечение (composition)
  - `B` — baseline regression_updn без фильтров
- `tests/test_benchmark_quantile_fav_composition.py` — unit-тесты на:
  1. Маска пересечения = `mask_quantile & mask_fav` (purely logical).
  2. Никакая строка с `signal == 0` не попадает в выбранные.
  3. Дубликаты `time` обрабатываются так же, как в `apply_production_rule` (preserved до де-дупа, де-дуп тот же — keep first после сортировки по `_abs`).
  4. На синтетическом фрейме из 6 строк ручной перебор совпадает с маской.

### Artefacts To Create During Execution
- `ML/reports/quantile_fav_composition/run_metadata.json`
  - timestamps, commit hash, конфиг входов, версии rule файлов
- `ML/reports/quantile_fav_composition/validation_metrics.json` — N, PF, win_rate, mean_pnl_atr, coverage, gross_profit, gross_loss для всех 4 режимов
- `ML/reports/quantile_fav_composition/test_metrics.json` — то же для test
- `ML/reports/quantile_fav_composition/yearly_breakdown_test.csv` — по годам для всех 4 режимов: year, N, wins, losses, pf
- `ML/reports/quantile_fav_composition/intersection_diagnostic.json` — сколько quantile-сигналов выживают после композиции, сколько fav-сигналов выживают после композиции, размер пересечения, sample bias
- `ML/reports/quantile_fav_composition/n_boost_composition.json` — результат запуска n-boost gate на composition (если N достаточно)
- `docs/reports/2026-04-13-quantile-fav-composition.md` — финальный verdict report (см. Task 7)

### Files To Update At Stage Close
- `CONTEXT_HANDOFF.md` — фикс результата (gate_pass / gate_fail / inconclusive) + ссылка на verdict report
- `CHANGELOG.md` — одна запись `## [2026-04-13] - Composition track verdict (quantile × fav_3_vs_12)` с разделом `### Результаты` и `### Вывод`
- `wiki/research/execution-tracks.md` — добавить ссылку на новый отчёт через wiki skill (`Use skill wiki to ingest`)
- `docs/superpowers/roadmap.md` — пометить пункт «composition» как closed (если verdict отрицательный) или renamed в новый production-плана (если положительный)
- `.claude/memory/project_ml_status.md` — обновить раздел «production stack» если verdict положительный (reminder: проверить актуальность файла перед правкой)

---

## Tasks

### Task 1 — Bootstrap & invariants

- [ ] Step 1.1 — Прочитать все файлы из `Read First`. Зафиксировать в рабочем блокноте: какие splits/seed/baseline rule сейчас используются для quantile production (`seed_007`, validation 2019–2022, test 2023–2026, baseline rule из `baseline_rule_path` поля).
- [ ] Step 1.2 — Открыть `ML/reports/entry_path_v1_quantile_selected_rule.json`, явно записать в рабочий блокнот baseline numbers, против которых будем сравнивать composition:
  - `frozen_test`: N=48, PF≈8.18, win_rate=0.8125, mean_pnl_atr≈2.73
  - `n_boost_gate.verdict = gate_pass`
  - `negative_year_slices = 0`
  - `same_winner_ratio = 1.0`
  - `sequential_summary` (hold_bars=24): N=22, PF≈3.64, win_rate≈0.727
- [ ] Step 1.3 — Удостовериться, что `pred_fav_3` и `pred_fav_12` присутствуют в predictions фрейме quantile (или в baseline regression_updn predictions). Проверить через `pd.read_csv(...).columns`. Если их нет напрямую — обязательно через `API/signal_path_atlas.py` подгрузить.
- [ ] Step 1.4 — STOP gate: если столбцов `pred_fav_3` / `pred_fav_12` нет вообще ни в одном из доступных predictions-фреймов и их пришлось бы перепредсказывать (т.е. потребовался бы новый train/predict цикл) — **остановить план** и поднять решение пользователю. План явно НЕ разрешает retraining; альтернативные планы вне scope.

### Task 2 — Build composition bench script

- [ ] Step 2.1 — Создать `ML/benchmark_quantile_fav_composition.py`. Структура:
  - argparse: `--rule-path` (default `ML/reports/entry_path_v1_quantile_selected_rule.json`), `--seed-dir` (default `ML/reports/entry_path_v1_quantile_robustness/seed_007`), `--fav-threshold` (default `0.653`, **не оптимизировать**), `--output-dir` (default `ML/reports/quantile_fav_composition`)
  - Загрузить quantile predictions для validation и test через те же пути, что использует `export_signals`
  - Загрузить baseline predictions через `_resolve_baseline_predictions_path`
  - Загрузить `fav_3_vs_12` (см. Step 2.2)
  - Применить production rule через `apply_production_rule` — получить `mask_q`
  - Применить fav-фильтр поверх baseline отбора — получить `mask_f`
  - Пересечение — `mask_qf = mask_q & mask_f`
  - Только baseline (без обоих фильтров) — `mask_b = baseline_selected` (тот же что внутри `apply_production_rule`)
- [ ] Step 2.2 — Источник `fav_3_vs_12`: если столбцы `pred_fav_3`/`pred_fav_12` присутствуют прямо в quantile predictions — считать `fav_3_vs_12 = pred_fav_3 / max(pred_fav_12, eps)` локально, eps как в `signal_path_atlas.py`. Иначе подгрузить через `signal_path_atlas` пайплайн (тогда импортировать функцию compute, не дублировать формулу). НЕ копировать число eps вручную, импортировать.
- [ ] Step 2.3 — Вычислить метрики PF / win_rate / N / mean_pnl_atr / coverage / gross_profit / gross_loss для четырёх режимов на validation и test. Использовать ту же функцию агрегации, что и `benchmark_entry_path_v1_quantile_filter` — **не писать свою**. Если функция не вынесена — экспортировать её в helper модуль (минимальный refactor, ОК) и подключить к обоим скриптам.
- [ ] Step 2.4 — Сохранить два файла `validation_metrics.json` и `test_metrics.json` со схемой `{"baseline": {...}, "quantile_only": {...}, "fav_only": {...}, "composition": {...}}`. Внутри каждого режима — те же поля, что в `entry_path_v1_quantile_selected_rule.json.frozen_test`.
- [ ] Step 2.5 — Сохранить `intersection_diagnostic.json`:
  ```json
  {
    "n_quantile": ...,
    "n_fav": ...,
    "n_intersection": ...,
    "intersection_over_quantile": n_int / n_quantile,
    "intersection_over_fav": n_int / n_fav,
    "trades_lost_from_quantile": n_quantile - n_intersection
  }
  ```
- [ ] Step 2.6 — Сохранить `run_metadata.json` (commit hash через `git rev-parse HEAD`, timestamps, конфиг).

### Task 3 — Tests

- [ ] Step 3.1 — Создать `tests/test_benchmark_quantile_fav_composition.py` с unit-тестами из `Files To Create`. Использовать pytest fixtures с маленьким синтетическим DataFrame.
- [ ] Step 3.2 — Тест 1: маска пересечения. Построить два булевых вектора длиной 8, проверить `mask_qf == mask_q & mask_f`.
- [ ] Step 3.3 — Тест 2: ни одна строка с `signal == 0` не попала в выбранные (для baseline, quantile, fav, composition).
- [ ] Step 3.4 — Тест 3: дубликаты по `time` обрабатываются так же, как в `export_signals` production-ветке (проверка через прямой вызов `apply_production_rule` на мини-фрейме с дубликатами).
- [ ] Step 3.5 — Тест 4: ручной перебор. Захардкодить ожидаемые маски для 6-строчного фрейма с явными значениями `pred_ret_24_q10`, `pred_ret_24_q90`, `pred_ret_24_dir_atr`, `pred_fav_3`, `pred_fav_12`, `signal`. Сравнить bit-by-bit.
- [ ] Step 3.6 — Запустить `pytest tests/test_benchmark_quantile_fav_composition.py -x -q`, добиться 4/4 зелёных. Если падает — диагностировать; не глушить.

### Task 4 — Year-by-year breakdown

- [ ] Step 4.1 — В benchmark скрипте добавить расчёт по годам для test split. Для каждого года и каждого из 4 режимов: N, wins, losses, gross_profit, gross_loss, PF (с защитой от деления на 0 — если losses == 0, писать `null` в PF, не `inf`).
- [ ] Step 4.2 — Экспорт `yearly_breakdown_test.csv` со столбцами: `year, mode, N, wins, losses, pf`.
- [ ] Step 4.3 — Записать в рабочий блокнот: сколько years имеют negative_year_slices (PF<1) для composition vs для quantile_only.

### Task 5 — Apply unified gate (n-boost style)

- [ ] Step 5.1 — Воспроизвести n-boost gate из [docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md](../../reports/2026-04-11-entry-path-v1-quantile-robustness.md) для composition режима. Критерии (берём те же, что для quantile production verdict):
  - `N >= 30`
  - `PF > 2.0` на полном test
  - `negative_year_slices == 0`
  - **multi-seed compat:** для composition нет 5-сидового перебора; вместо этого требуем, чтобы composition переигрывал quantile_only по N или PF (см. Task 6 verdict rubric).
- [ ] Step 5.2 — Если в репо уже есть утилита для n-boost gate (см. CONTEXT_HANDOFF и quantile robustness план) — переиспользовать, не дублировать. Если её нет в виде функции — НЕ выносить как часть этого плана; вызвать минимально и сохранить результат вручную в `n_boost_composition.json`.
- [ ] Step 5.3 — Сохранить `n_boost_composition.json` с тем же набором полей: `verdict ∈ {gate_pass, gate_fail, gate_inconclusive}`, `n_trades`, `pf`, `negative_year_slices`, `reasons`.

### Task 6 — Verdict rubric (decision)

Применяется ровно ОДИН раз, после Task 5. Никакого подгона порогов под желаемый исход.

- [ ] Step 6.1 — Зафиксировать рubric в шапке verdict report:
  - **PROMOTE-candidate** (откроется отдельный production план): composition ВСЕ три условия:
    1. `n_boost_composition.verdict == gate_pass`
    2. composition N >= 70% от quantile_only N (т.е. фильтр не выкашивает большую часть сигналов)
    3. composition PF >= 1.15 × quantile_only PF на test
    4. composition negative_year_slices <= quantile_only negative_year_slices
  - **CLOSED — no uplift**: gate_pass, но composition не выполняет (2) или (3) — фильтр режет сделки без proportional прироста PF
  - **CLOSED — gate fail**: composition `gate_fail` — фильтр ломает gate, который quantile_only проходил
  - **INCONCLUSIVE**: composition `gate_inconclusive` (например, N упал < 30) — записать как «недостаточно данных, повторить после forward validation»
- [ ] Step 6.2 — Прогнать рубрику строго по числам из артефактов Task 2/4/5. Записать verdict ∈ {PROMOTE-candidate, CLOSED — no uplift, CLOSED — gate fail, INCONCLUSIVE}.
- [ ] Step 6.3 — STOP-условие: если verdict == PROMOTE-candidate, **не открывать новый production-режим в рамках этого плана**. Завершить план созданием отчёта Task 7 и явной рекомендацией: «открыть отдельный план productization composition». Этот план не претендует на роль productization plan.

### Task 7 — Verdict report & stage close

- [ ] Step 7.1 — Создать `docs/reports/2026-04-13-quantile-fav-composition.md`. Структура:
  - **Дата, статус, цель, источники** (как в `2026-04-12-tb-verdict.md`, `2026-04-12-quantile-status-decision.md`)
  - **Метод** — как именно интерсектились маски, источник `fav_3_vs_12`, какой rule path quantile, какой baseline path
  - **Результаты валидации** — таблица baseline / quantile_only / fav_only / composition, столбцы N, win_rate, PF, mean_pnl_atr
  - **Результаты теста** — та же таблица
  - **Год за годом** — таблица из `yearly_breakdown_test.csv`
  - **Intersection diagnostic** — числа из `intersection_diagnostic.json`
  - **Verdict rubric** — копия рубрики из Task 6.1 + результат
  - **Verdict** — одно из четырёх состояний
  - **Limitations & open questions**
  - **Решение по roadmap** — что делать дальше (закрыть/форвард-валидация/отдельный план)
- [ ] Step 7.2 — Обновить `CONTEXT_HANDOFF.md`: поднять секцию `Current Stage` (новый этап `quantile_fav_composition_verdict`), `Last Completed Stage`, скорректировать `Next Step` под исход, добавить ссылку на отчёт в `Read First`. **Не удалять** существующие разделы про quantile production и TB verdict — они остаются.
- [ ] Step 7.3 — Записать в `CHANGELOG.md` блок:
  ```
  ## [2026-04-13] - Composition track verdict (quantile × fav_3_vs_12)
  ### Результаты
  - <одно предложение с числами baseline / quantile_only / composition: N, PF>
  - n_boost gate composition: <verdict>
  ### Вывод
  - <одно предложение с verdict>
  ```
  Не дублировать содержимое отчёта.
- [ ] Step 7.4 — Через wiki skill (`Use skill wiki, action=ingest, report=docs/reports/2026-04-13-quantile-fav-composition.md`) добавить отчёт в `wiki/research/execution-tracks.md`. Не редактировать `wiki/index.md` вручную — это работа skill-а.
- [ ] Step 7.5 — Обновить `docs/superpowers/roadmap.md`:
  - Если verdict ∈ {CLOSED — no uplift, CLOSED — gate fail}: пометить пункт «composition» как **closed** с одной строкой на причину + ссылкой на отчёт.
  - Если verdict == INCONCLUSIVE: оставить пункт активным с пометкой «awaiting forward validation, не ранее <дата + 2 месяца>».
  - Если verdict == PROMOTE-candidate: пункт переименовать в «open productization plan for composition».
- [ ] Step 7.6 — Обновить `.claude/memory/project_ml_status.md` ТОЛЬКО если verdict == PROMOTE-candidate (новая production-кандидатура). Иначе — не трогать.

### Task 8 — Self-review checklist

- [ ] Step 8.1 — `pytest -x -q tests/test_benchmark_quantile_fav_composition.py` — зелёный.
- [ ] Step 8.2 — Никаких изменений в `processing/`, `ML/train.py`, `MT/`, `API/export_entry_path_v1_quantile_signals.py` (кроме возможного выноса метрик-функции в helper модуль с подключением обратно — если так сделано, это явно отмечено в отчёте Task 7).
- [ ] Step 8.3 — Никакого нового rule JSON в `ML/reports/` рядом с `entry_path_v1_quantile_selected_rule.json`. Composition не получает frozen rule в этом плане.
- [ ] Step 8.4 — Все артефакты под `ML/reports/quantile_fav_composition/` — без раскидывания по дереву.
- [ ] Step 8.5 — `git status` — нет случайно затронутых файлов вне списка `Files To Create` / `Files To Update At Stage Close`.
- [ ] Step 8.6 — Verdict в отчёте указан **до** его повторения в `CHANGELOG.md` / `CONTEXT_HANDOFF.md`. Числа во всех трёх местах совпадают bit-to-bit (один и тот же источник — артефакты Task 2/4/5).
- [ ] Step 8.7 — В отчёте явно зафиксировано, что `fav_3_vs_12 <= 0.653` НЕ оптимизировался под composition. Порог взят из источника 2026-04-04.
- [ ] Step 8.8 — `git commit` — **только** по явной просьбе пользователя.

---

## Safeguards & escalation

- **Escalate to user** если:
  - Шаги 1.4 / 2.2 показывают, что для расчёта `fav_3_vs_12` потребовалось бы переобучение модели предсказания pred_fav_*. Это вне scope.
  - Verdict выходит INCONCLUSIVE с N < 15 на test для composition — данных слишком мало даже для negative-вердикта; нужно решение пользователя, закрывать формально или ждать forward.
  - Числа quantile_only из этого скрипта **расходятся** с числами в `entry_path_v1_quantile_selected_rule.json.frozen_test` более чем на ~1% — это сигнализирует о баге в join/маске; разбираться, не маскировать.
  - Появляется соблазн «попробовать другой порог fav» / «другой rule quantile» / «другой baseline» — STOP, это уже другой план.
- **Don't do**:
  - Не подключать composition к MT4 даже при PROMOTE-candidate. Productization — отдельный план со своим parity test, multi-seed gate, reports artifacts.
  - Не менять `processing/label_signals.py` (label convention — отдельный плана `2026-04-13-label-convention-audit.md`).
  - Не переоптимизировать `m`/`w`/`correction` quantile rule под composition.
  - Не вводить новые столбцы в predictions CSV — composition использует только то, что уже есть.

---

## Definition of Done

План считается выполненным, когда:
1. Существует `docs/reports/2026-04-13-quantile-fav-composition.md` с явным `Verdict ∈ {PROMOTE-candidate, CLOSED — no uplift, CLOSED — gate fail, INCONCLUSIVE}`.
2. Артефакты `ML/reports/quantile_fav_composition/{run_metadata,validation_metrics,test_metrics,intersection_diagnostic,n_boost_composition}.json` и `yearly_breakdown_test.csv` существуют.
3. `tests/test_benchmark_quantile_fav_composition.py` проходит 4/4.
4. `CONTEXT_HANDOFF.md`, `CHANGELOG.md`, `wiki/research/execution-tracks.md`, `docs/superpowers/roadmap.md` отражают результат.
5. Никаких изменений за пределами списка `Files To Create` / `Files To Update At Stage Close`, кроме явно задокументированного minimal helper refactor в Task 2.3.

После этого направление composition либо официально закрыто (CLOSED), либо передано в новый productization-плана (PROMOTE-candidate), либо отложено до forward-данных (INCONCLUSIVE). В любом случае **этот** план не производит production-rule и не трогает MT4.
