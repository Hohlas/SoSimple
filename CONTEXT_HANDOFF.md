# CONTEXT HANDOFF

## Current Active State

- **active track**: нет — pair-spread kill-test (idea-01) закрыт 2026-08-27 (decision `close`)
- latest report: `docs/reports/2026-08-27-pair-spread.md`
- latest plan (исполнен): `docs/superpowers/plans/2026-08-17-pair-spread.md`
- latest spec: `docs/superpowers/specs/2026-08-17-pair-spread-design.md`
- ветка: `feature/idea-01-pair-spread` (не замёрджена в `main`)
- артефакты: `DATA/pair_spread/screening.json`; код `statistics/pair_spread/{pair_data,screening,backtest,run_pair_spread,check_data}.py` (31 тест PASS)

## Decision

Pair-spread kill-test (`RESEARCH_ONLY`, `close`):

- Все 7 пар-кандидатов (AUDNZD, AUDCAD, NZDCAD, EURGBP, EURCHF, GBPCHF, XAUXAG) убиты на Stage 1 (скрининг на train 2005–2022) по M5 и H1.
- EG-тест (autolag='bic', maxlag=20) уверенно не отвергает H₀ коинтеграции для 6/7 пар (p 0.22–0.88); AUDCAD формально коинтегрирован (p=0.002), но half-life 18 765 M5-баров (~65 суток) и 0.38 эпизода/год делают пару неоперациональной.
- β нестабильна между половинами train: drift 7–332% (GBPCHF — 4.3× рост модуля при сохранении знака; пулированный β полного train противоположен по знаку обеим половинам).
- EURCHF в окне SNB 12.2014–02.2015: структурный сдвиг спреда (диапазон 0.155 log-единиц), но не единственная причина провала EG.
- Stage 2 пропущена (нет ни одного PASS). Decision: **тема парного статистического арбитража данного класса закрыта**.

MT5 (`DIAGNOSTIC_ONLY`, отложен): single-position policy блокирует 99.2% OPEN_FAILED; fill rate — не причина `BATCH_NO_WINNER`; timing-контракт `feature_time <= time < feature_available_time <= decision_time`; `InpMT5_MaxPositions=1` — канонический режим.

MI Upper Bound (закрыт 2026-08-12): amplitude следующего бара предсказуема (MI 0.01–0.02 bits, p=0.005), direction — нет (p=0.229). Фокус следующих веток — amplitude.

## Current Diagnostic Facts

- Screening.json: ни одной PASS-пары по 5 гейтам (EG p, half-life, episodes/year, cost<P75|Δs|, median deviation>cost). Согласованность M5↔H1 по pass/kill полная.
- Episode counts: 1–9 эпизодов за 18 лет на M5 (AUDCAD максимум 9). Это не торговые эпизоды, а макро-режимы.
- XAGUSD брокер отдаёт только с 2008-11-07: train XAUXAG ~14 лет вместо 18 (MIN_TRAIN_YEARS=10 проходит).
- Pragmatic EG: `autolag='bic'`, `maxlag=20` (дефолт AIC с `maxlag~100` на 500k M5-барах считался десятки минут и 40GB RAM). Вердикт от выбора не зависит.
- Pre-existing test failure: `test_mql_telemetry_params_csv_contract.py::test_tester_ini_selects_telemetry_backtest_row` (дрейф tester .ini, к pair-spread отношения не имеет).

## Do Not Do

- Не пытаться «спасти» pair-spread идею пересмотром порогов, окон или состава пар — тема закрыта по предрегистрированному протоколу. Переоткрытие требует нового плана и отдельной идеи.
- Не трактовать AUDCAD EG p=0.002 как намёк на работоспособность: half-life и эпизоды/год убивают пару независимо.
- Не смешивать MI Upper Bound (amplitude PASS, direction FAIL) с pair-spread (оба закрыты независимо).
- Не открывать `locked_test` для нового выбора winner без frozen protocol.
- Не делать торговых выводов из RESEARCH_ONLY/DIAGNOSTIC_ONLY результатов.

## Next Step

1. Определить следующий ACTIVE-трек: идея 2 роэдмэпа (OCO-стрэддл) или другой приоритет (`docs/superpowers/roadmap.md`, секция NEXT_AFTER_MT5_HYGIENE).
2. Опционально: замёрджить `feature/idea-01-pair-spread` в `main` (код стабилен, 31 тест PASS, 13 коммитов опережают `main`).
3. MI: probe joint MI (npeet, пониженная размерность, топ-признаки по MI) с замороженными условиями; далее amplitude-ветка моделей.
4. Починить `statistics/data_contract_smoke_check.py` (устаревшие колонки `target_*_H6_val`).
5. MT5 при возобновлении: план per-magic multiplexing (после исполненного closeout), max verdict `DIAGNOSTIC_ONLY`.

## Verification

- `./.venv/bin/python -m pytest tests/test_pair_spread_*.py -q` → 31 passed.
- Полный `./.venv/bin/python -m pytest tests/ -q` → 1636 passed, 1 failed (pre-existing `test_mql_telemetry_params_csv_contract.py`; к этапу отношения не имеет).
- Stage 1 скрининг воспроизводим: `./.venv/bin/python statistics/pair_spread/run_pair_spread.py --stage 1` → `DATA/pair_spread/screening.json` (12 280 байт).
