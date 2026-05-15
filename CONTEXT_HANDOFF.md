# Context Handoff

Дата: 2026-05-15.

## Текущий этап

Завершён эксперимент `entry-path-fractal-level-direct-direction` (Task E из плана
`2026-05-15-entry-path-fractal-level-direct-direction.md`). Результат: standalone
validation winner не найден. Все 3-class SELL/SKIP/BUY конфигурации не прошли
gate (PF < 1.15).

Следующий этап: итеративное улучшение direct-direction по плану
`docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md`.

## Git

Локальная ветка: `entry-path-all-rows-spec`.

Не трогать `AGENTS.md` без явной просьбы пользователя.

## Что уже сделано

### Direct-direction fractal-level (завершён, без winner)

Созданы файлы:

- `ML/fractal_level_feature_builder.py` — парсинг фракталов, аудит, nearest_k признаки
- `ML/entry_path_direct_direction_targets.py` — BUY/SELL target families A/C/D
- `ML/benchmark_entry_path_fractal_level_direct_direction.py` — benchmark runner
- `tests/test_fractal_level_feature_builder.py`
- `tests/test_entry_path_direct_direction_targets.py`
- `tests/test_benchmark_entry_path_fractal_level_direct_direction.py`

Артефакты в `ML/reports/entry_path_v1_fractal_level_direct_direction/`.

#### Исправленный баг: двойная нормализация ATR

`up_*/dn_*` в `Nero_*_labeled.csv` уже ATR-нормализованы через `normalize_rowwise()`.
Первоначально `build_buy_sell_fav_adv()` делил их на ATR ещё раз — median вместо ~0.1.
Исправлено: теперь `up_*/dn_*` используются напрямую, пороги пересчитаны
(A: `stop_n=0.2, take_y=0.3`; C: `take_x=0.5, adverse_y=0.3`).

После исправления все три target family прошли frequency gate.

#### Результаты nearest_k4 (97 features), RandomForest, Target D

| Threshold | Trades | PF | Seq PF | BUY/SELL | Gate fail |
|-----------|--------|-----|--------|----------|-----------|
| 0.1 | 9415 | 1.11 | 1.15 | 3656/5759 | PF < 1.15 |
| 0.3 | 9280 | 1.11 | 0.99 | 3583/5697 | PF < 1.15 |
| 0.4 | 227 | 1.17 | 1.10 | 83/144 | overfitting_risk |
| 0.5+ | 0 | — | — | — | — |

Для Target A и C: PF ≈ 1.0 при низких threshold, degrade при высоких.
Все модели дают вероятности BUY/SELL ≈ 1/3 (едва выше random).
Top feature importance плоская (~0.004–0.005). Для Target A `fractal0_direction` = 17.3%.

#### Ключевой вывод

3-class SELL/SKIP/BUY на fractal-level признаках с RandomForest не даёт
торгового преимущества без score-фильтра. Direction signal слишком слаб.

### Утверждённый план улучшений

Файл: `docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md`

Эксперименты (все на train/validation, frozen test один раз в конце):

| # | Эксперимент | Суть |
|---|-------------|------|
| E0 | Feature Ablation | k=4/6/8/16, geometry_only vs с Up/Dn |
| E1 | Binary BUY/SELL модели | Две бинарных HGB, margin rule |
| E2 | HGB + LR 3-class | HistGradientBoosting + LogisticRegression контроль |
| E3 | Zone Features (Input A) | Агрегация фракталов по ценовым зонам |
| E4 | Target Grid A/C/D | Параметрические сетки для всех трёх family |
| E5 | Score Direction | HGB direction resolver на score-filtered universe |
| E6 | Sequence Features | Условный: только если E0-E3 дают PF 1.05–1.15 |

Порядок: E0 → E1 → E2 → E3 → E4 → E5 → E6(conditional).

Критические правила (из рецензии):
- Один frozen test после выбора общего validation winner, не после каждого эксперимента
- `signal != 0` — только diagnostic, не production gate (в E5)
- Ambiguous BUY+SELL rows остаются positive для обеих моделей (E1)
- `features / validation_candidates >= 0.20` — skip config (E3)
- Sparsity gates: `major-year min BUY/SELL >= 10`, `ambiguous_rate <= 0.20` (E4)
- HGB: `compute_sample_weight("balanced", y)` + permutation importance (E2)

## Открытые вопросы

1. Production watcher `entry_path_v1_live_safe + A @ 7.5%` на M5 — не проверен
   после рефакторинга. Вопрос отложен до завершения direct-direction исследований.

2. Задержка входа ticket `1581716381` (65 мин) — не исследована.

3. `requote ERROR-138` — не проверена обработка в новом коде.

## Следующий шаг

Начать выполнение плана с Experiment 0: Feature Ablation.

```bash
# E0: k variants
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage validation-matrix --k 6
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage validation-matrix --k 8
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage validation-matrix --k 16
.venv/bin/python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage validation-matrix --k 4 --geometry-only
```

Новый агент должен прочитать AGENTS.md → CONTEXT_HANDOFF.md → план.