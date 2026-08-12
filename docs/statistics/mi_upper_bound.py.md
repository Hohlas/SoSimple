# mi_upper_bound.py — KSG-оценка MI и диагностический потолок R²

> **Назначение**: оценка взаимной информации (bits) между live-safe признаками и таргетами следующего бара; диагностический потолок R²
> **Тип**: библиотека (импортируется `run_mi_upper_bound.py` и тестами)
> **Отчёт этапа**: `docs/reports/2026-08-11-mi-upper-bound.md`

---

## Обзор

Ядро этапа MI Upper Bound. Отвечает на вопрос «каков фундаментальный предел предсказуемости XAUUSD H1» через маргинальное MI признаков из `ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS` (42 признака) с таргетами:

- `direction = sign(close[t+1] - open[t+1])` — трёхклассовый {-1, 0, +1}, `mutual_info_classif`;
- `amplitude = |log(close[t+1] / open[t+1])|` — непрерывный, `mutual_info_regression`.

Таргеты строятся джойном с `DATA/XAUUSD_H1_OHLC.csv` (в labeled CSV нет open/close).

Ключевые соглашения:

- sklearn возвращает MI в **nats**; внутри конверсия в **bits** (`/ln(2)`) — формула потолка `R² <= 1 - 2^(-2·I)` верна только для bits;
- `perm_p_value = None` при `n_permutations=0` (не фейковое 1.0) — единственный gate-критерий вердикта;
- `mi_ci_p05/p95` — метрика стабильности по непересекающимся временным фолдам, **не** доверительный интервал точечной оценки (на малых split'ах фолды смещены вверх из-за конечновыборочного смещения KSG) и в вердикте не участвует;
- потолок из среднего маргинального MI — диагностический, не joint MI;
- дедупликация `drop_duplicates('time', keep='last')` — конвенция проекта; потери OHLC-джойна ≤ 5% (assert).

## API

- `load_mi_data(csv_path, ohlc_path)` → dict: `X` (N, 42), `y_direction` (N,), `y_amplitude` (N,), `feature_names`, `time`, `n_dedup_dropped`, `n_join_dropped`;
- `estimate_mi(X, y, k, n_folds, n_permutations, random_state, discrete_target, discrete_mask)` → dict с `mean/max_marginal_mi_bits`, `mi_ci_p05/p95`, `perm_p_value`, `r2_ceiling`, `n_folds_used`;
- `estimate_mi_per_feature(...)` → DataFrame (feature, mi_bits) по убыванию;
- `estimate_rolling_mi(X, y, timestamps, window, step, k, ...)` → временные ряды MI без permutation; **без discrete_mask** (раскрытие в отчёте).

## Запуск

Самостоятельно не запускается — см. `run_mi_upper_bound.py`. Тесты: `tests/test_mi_upper_bound.py`.

## Ограничения

- `statistics/` конфликтует со stdlib-модулем `statistics`; импорт — через `sys.path`/importlib, `__init__.py` не добавлять.
- Joint MI не оценивается; строгая граница — отдельный эксперимент (npeet).
