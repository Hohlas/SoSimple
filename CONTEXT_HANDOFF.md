# CONTEXT HANDOFF

## Current Active State

- active track: `predictability research / amplitude-ветка` (этап MI Upper Bound закрыт 2026-08-12)
- latest report: `docs/reports/2026-08-11-mi-upper-bound.md`
- latest plan (исполнен): `docs/superpowers/plans/2026-08-11-mi-upper-bound.md`
- latest spec: `docs/superpowers/specs/2026-08-11-mi-upper-bound-design.md`
- MI-артефакты: `ML/reports/mi_upper_bound.json`, `mi_upper_bound_k10.json`, `mi_upper_bound_k15.json`; `ML/plots/mi_per_feature.png`, `mi_rolling.png`; код `statistics/mi_upper_bound.py`, `statistics/run_mi_upper_bound.py`
- MT5-трек отложен: `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md` (исполнен 2026-08-07), `docs/superpowers/plans/2026-08-03-mt5-per-magic-multiplexing.md` (pending; очерёдность: сначала per-magic после closeout — closeout уже исполнен)

## Decision

MI Upper Bound (`research_scan`, `RESEARCH_ONLY`):

- Amplitude следующего бара предсказуема: MI 0.010–0.022 bits, permutation p=0.005 на train и validation; диагностический потолок R² ≈ 0.014–0.030.
- Direction на validation НЕ подтверждена (p=0.229; robustness по k пограничный: p=0.025–0.23); доля класса 0 нестабильна между split'ами (train 3.8%, validation 0.3%).
- Потолок кратно ниже legacy R² 0.084–0.18 → наиболее вероятное объяснение разрыва — leakage future-derived входов legacy-моделей (ретроспектива 2.6); сравнение ориентировочное (другие горизонты/входы).
- Rolling MI 2004–2026 стабилен → regime drift в информации признаков не обнаружен (самостоятельный результат относительно ретроспективы 6.3).
- Принято: фокус следующих веток — amplitude; маргинальный потолок — не строгая joint-граница; fold-CI и rolling — метрики стабильности, в вердикте не участвуют.

MT5 (`DIAGNOSTIC_ONLY`, отложен): single-position policy блокирует 99.2% OPEN_FAILED; fill rate — не причина `BATCH_NO_WINNER`; timing-контракт `feature_time <= time < feature_available_time <= decision_time`; `InpMT5_MaxPositions=1` — канонический режим.

## Current Diagnostic Facts

- MI (k=5, bits): train direction 0.0041 (p=0.005) / amplitude 0.0222 (p=0.005); validation direction 0.0027 (p=0.229) / amplitude 0.0102 (p=0.005).
- Fold-CI на validation смещён вверх (конечновыборочное смещение KSG на фолдах ~898 строк) — только метрика стабильности.
- Топ-признаки: `row_strong_share_*` (оба таргета), `session_hour` важен для amplitude; группа time не доминирует.
- `statistics/data_contract_smoke_check.py` устарел: FAIL по `target_*_H6_val` (колонки нет ни в одном labeled CSV) — отдельная задача на починку.
- MT5: `ML/reports/mt5_execution_loop/batch/batch_summary.json` — `BATCH_NO_WINNER`; `diagnostics/signal_timing_check.json` — 32/32, `bad_files=0`; `diagnostics/position_ordinal_pnl.json` — PF по ordinal для max=64 пилота.

## Do Not Do

- Не трактовать маргинальный MI-потолок как строгую границу R² и не делать торговых выводов из research_only результата («прибыльно», «готово», «можно запускать» запрещены).
- Не строить sign-стратегии на direction по итогам этого этапа; не выбирать k по robustness (k=5 зафиксирован до запуска).
- Не открывать `locked_test` для выбора; не выбирать нового winner из MT5-диагностик; не пускать `latency_bars>0` в дефолтный batch-отбор.

## Next Step

1. MI: probe joint MI (npeet, пониженная размерность, топ-признаки по MI) с замороженными условиями по методологии 00; далее — amplitude-ветка моделей (таргет amplitude, live-safe 42 признака).
2. Починить `statistics/data_contract_smoke_check.py` (устаревшие колонки `target_*_H6_val`).
3. MT5 при возобновлении: план per-magic multiplexing (после исполненного closeout), max verdict `DIAGNOSTIC_ONLY`.

## Verification

- `./.venv/bin/python -m pytest tests/test_mi_upper_bound.py -q` → 8 passed.
- Числа отчёта сверены с JSON-артефактами аудитом 2026-08-12 (расхождение отчёт ↔ артефакт отсутствует).
- Полный `./.venv/bin/python -m pytest tests/ -q` → 1605 passed, 1 failed: `test_mql_telemetry_params_csv_contract.py::test_tester_ini_selects_telemetry_backtest_row` (pre-existing дрейф tester `.ini`: `BackTest=0` вместо `BackTest=2`; к MI-этапу отношения не имеет).
