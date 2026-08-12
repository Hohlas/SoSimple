# run_mi_upper_bound.py — runner этапа MI Upper Bound

> **Назначение**: прогоны оценки MI (train/validation), per-feature и групповой разбор, rolling по конкатенации split'ов, графики, JSON-отчёт
> **Тип**: CLI-раннер
> **Отчёт этапа**: `docs/reports/2026-08-11-mi-upper-bound.md`

---

## Запуск

```bash
# Основной прогон (k=5, rolling включён)
.venv/bin/python statistics/run_mi_upper_bound.py

# Robustness по k (без rolling)
.venv/bin/python statistics/run_mi_upper_bound.py --k 10 --no-rolling \
    --output ML/reports/mi_upper_bound_k10.json

# Перестроить графики из сохранённого JSON без пересчёта MI
.venv/bin/python statistics/run_mi_upper_bound.py --replot
```

Запуск из корня проекта; импорт `mi_upper_bound` работает, так как `sys.path[0]` = `statistics/`.

## Входы / выходы

- Входы: `DATA/Nero_{train,validation,test}_labeled.csv`, `DATA/XAUUSD_H1_OHLC.csv`.
- Выходы: `ML/reports/mi_upper_bound.json` (+ `_k10`, `_k15`), `ML/plots/mi_per_feature.png`, `ML/plots/mi_rolling.png` (на rolling-графике границы split'ов отмечены вертикальными линиями).

## Поведение

- Discrete-маска основных оценок: `session_hour` (23 уровня), `weekday` (5 уровней); остальные 40 признаков — continuous.
- Rolling: конкатенация train+validation+test, window=500, step=100, `n_permutations=0`; в JSON — `split_boundaries` и disclosure смешанных окон на стыках.
- Групповой разбор (`FEATURE_GROUPS`): time / strong / break / direction_balance / back / impulse / power / count.
- Конфигурация фиксируется в JSON: `mi_units=bits`, `discrete_features`, формула потолка, контракты таргетов.

## Ограничения

- Permutation-цикл дорог: прогон k=5 ≈ 22 мин, k=10/15 ≈ 30 мин (200 перестановок × 42 признака на 41k строк).
- Rolling считается без discrete-маски (см. `mi_upper_bound.py.md` и Limitations отчёта).
