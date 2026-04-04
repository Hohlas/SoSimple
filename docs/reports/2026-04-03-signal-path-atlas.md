# Этап Signal Path Atlas

> **Date**: 2026-04-03
> **Status**: Completed
> **Goal**: Построить и проверить standalone Python-инструмент path atlas, который описывает постсигнальную геометрию цены в ATR-нормированном `discovery/holdout` пространстве без возврата к прямому поиску `PF`-правил.
> **Related plan/spec**: `docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md`, `docs/superpowers/plans/2026-04-03-signal-path-atlas.md`
> **Related commit**: `898bb36`

## Context

Variant 2 и Variant 3 показали, что текущий сигнал лучше описывается как слабый drift с выборочным continuation, а не как чистый impulse edge. Robustness-pass в Variant 3 оставил один узкий execution-кандидат, но его поддержка всё ещё была слишком маленькой для уверенного transportable вывода. Поэтому на этом этапе изменился сам объект исследования: вместо поиска следующего `PF`-winner в Python проект перешёл к условному `path atlas`, который сначала описывает геометрию движения после сигнала, а уже потом позволяет принимать решения об execution.

## What Was Done

- Добавлен новый standalone research entry point: `API/signal_path_atlas.py`
- Реализован фиксированный календарный split:
  - `discovery <= 2024-12-31 23:59:59`
  - `holdout >= 2025-01-01 00:00:00`
- Построен direction-aware ATR-normalized path tensor на горизонте `1..12` баров:
  - `signed_ret_h`
  - `fav_h`
  - `adv_h`
  - first-passage и ordering features
- Добавлены discovery-only conditioning features и feature screen:
  - `ratio_h`
  - `spread_h`
  - short-vs-long derived ratios/spreads
  - fixed cohorts `signal_label`, `ratio_bin_12`, `atr_bucket`
- Добавлены discovery-atlas outputs:
  - global path quantiles
  - first-passage atlas
  - ordering atlas
  - numeric и categorical slices
  - path archetypes
- Добавлен holdout replication layer со структурированными verdicts:
  - `Replicated`
  - `Directionally consistent`
  - `Failed`
  - `Exploratory`
- После review усилена надёжность реализации:
  - ATR bucket edges теперь фиксируются только на discovery, чтобы исключить holdout leakage
  - discovery archetypes с нулевой поддержкой на holdout сохраняются в verdict tables
  - убран crash path в `main()`, если после screening не остаётся live numeric features
  - holdout numeric slice membership стал interval-aware, поэтому повторяющиеся границы бинов больше не дают double-count
  - archetype naming при collapsed/role-collision случаях стал детерминированным и нейтральным
  - CLI/report/export теперь показывают полный atlas surface, а не только его часть

## Changed Files

- `API/signal_path_atlas.py`
- `tests/test_signal_path_atlas.py`
- `API/README.md`
- `docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md`
- `docs/superpowers/plans/2026-04-03-signal-path-atlas.md`

## Verification

- `./.venv/bin/python -m pytest tests/test_signal_path_atlas.py -q`
  - результат: `38 passed`
- `./.venv/bin/python -m API.signal_path_atlas --test-only`
  - результат: успешно завершился
- `rm -rf /tmp/signal_path_atlas && ./.venv/bin/python -m API.signal_path_atlas --test-only --export-dir /tmp/signal_path_atlas`
  - результат: успешно завершился
- Финальный export set, который пишет CLI:
  - `split_summary.csv`
  - `feature_screen.csv`
  - `path_quantiles.csv`
  - `first_passage.csv`
  - `ordering.csv`
  - `numeric_slices.csv`
  - `categorical_slices.csv`
  - `archetype_summary.csv`
  - `holdout_verdicts.csv`
  - `execution_implications.csv`

## Results

- У проекта теперь есть выделенный path-atlas CLI вместо дальнейшего расширения `API/signal_research.py`.
- Atlas contract стал явным и воспроизводимым:
  - discovery artifacts фиксируются до перехода на holdout replication
  - holdout больше не может протекать в ATR bucket construction
  - replication verdicts строятся для numeric slices, fixed cohorts и archetypes
- На текущем `--test-only` verification run split дал:
  - `discovery = 1752`
  - `holdout = 851`
- На текущем atlas smoke run на discovery видны две surviving archetype families:
  - `failure_or_adverse_continuation`
  - `flat_or_noisy_drift`
- Текущий holdout verdict surface больше не даёт немедленной execution-рекомендации:
  - `execution_implications = neither`

## Conclusions

Этот этап успешно увёл проект от прямого поиска `PF`-winner и перевёл его в reusable path-atlas workflow. Главный результат этапа — не новое EA rule, а проверенный исследовательский инструмент, который умеет описывать path geometry, фиксировать discovery artifacts и проверять, реплицируются ли найденные эффекты на holdout. Именно это сейчас является правильной методологической базой для любых будущих решений между `market` и `pullback`.

Главное практическое изменение относительно предыдущего handoff — концептуальное: следующий Python-шаг больше не является узким robustness pass вокруг старого locked winner. Новый default path — сначала читать atlas outputs и определять, какие path claims реально реплицируются, и только потом выводить из этого downstream execution hypotheses.

## Limitations / Open Questions

- `API/signal_path_atlas.py` уже стал довольно крупным single-file research tool; по поддержке он ещё приемлем, но при дальнейшем росте, вероятно, стоит разделить orchestration и analysis helpers.
- Shallow explanation tree уже считается, но пока не вынесен в полноценный report/export artifact.
- Текущая верификация использовала документированный `--test-only` path. Для stage close этого достаточно, но следующий аналитический проход должен уже читать atlas outputs напрямую и превращать их в канонический human research summary.
- Текущее значение `execution_implications = neither` означает, что atlas layer уже построен, но слой исследовательской интерпретации ещё впереди.

## Next Step

Использовать новый atlas tooling, чтобы получить первый канонический path-atlas research readout из frozen tables:

- разобрать global path quantiles, first-passage и ordering как основное описание сигнала;
- выделить только те path claims, которые действительно реплицируются на holdout;
- решить, поддерживает ли replicated cohort/archetype evidence будущий `market`, `pullback`, оба варианта или ни один;
- оставить старый Variant 3 locked winner только как benchmark, а не как главный драйвер следующего этапа.

## Related Materials

- `docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md`
- `docs/superpowers/plans/2026-04-03-signal-path-atlas.md`
- `docs/reports/2026-04-02-signal-research-variant-3.md`
- `docs/reports/2026-04-02-signal-research-variant-3-prep.md`
- `docs/reports/2026-04-01-signal-research-variant-2.md`
- `API/signal_path_atlas.py`
- `tests/test_signal_path_atlas.py`
