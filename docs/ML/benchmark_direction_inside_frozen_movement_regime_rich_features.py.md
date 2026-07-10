# benchmark_direction_inside_frozen_movement_regime_rich_features.py

`ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
задаёт контракт новой проверки направления внутри frozen movement-mask.

## Назначение

Модуль должен проверять direction-сигнал внутри уже замороженной movement-mask,
но с двумя важными исправлениями относительно старого runner-а:

- direction-модель обучается на полном `train`, а не только на строках
  `frozen_selected=True`;
- frozen-mask используется только для оценочных срезов после обучения.

Текущая реализация закрывает контрактный слой, feature/target helpers, базовые
fit/evaluation helpers, selection/verdict, запись артефактов и подключение к
реальным split/freeze артефактам. Runner поддерживает heartbeat, progress JSON,
resume после остановки и явное управление числом потоков для параллельных
моделей.

## Входы

- entry-based split-ы из существующих baseline runners;
- frozen movement scores с обязательными колонками `split`, `split_row_id`,
  `selected`;
- target-колонки `entry_log_ratio_H`, `entry_up_H`, `entry_dn_H` для
  горизонтов `3`, `6`, `12`, `24`;
- narrow replication mode дополнительно проверяет H9 через preflight:
  `entry_log_ratio_9`, `entry_up_9`, `entry_dn_9` должны существовать во всех
  рабочих split-ах, иначе H9 помечается как `SKIPPED_MISSING_TARGET_COLUMNS`.

## Выходы

- `ML/reports/direction_inside_frozen_movement_regime_rich_features.json`;
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_metrics.csv`;
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_rows.csv`.

Narrow replication mode пишет отдельные файлы:

- `ML/reports/direction_inside_frozen_movement_regime_narrow_replication.json`;
- `ML/reports/direction_inside_frozen_movement_regime_narrow_replication_metrics.csv`;
- `ML/reports/direction_inside_frozen_movement_regime_narrow_replication_rows.csv`.

JSON содержит:

- `started_at`, `finished_at`, общий `elapsed_sec`;
- `progress.done_runs`, `progress.total_runs`, `completed_keys`;
- `threading.requested_threads`, `threading.effective_threads`;
- per-run `elapsed_sec`, `resume_key`, `threading`;
- `selection`, `winner`, `contract_status`, `verdict`.

## Feature Profiles

- `simple_combined` — старый простой контроль;
- `nearest_k60`;
- `nearest_k80` — exploratory-only, не может сам создать положительный verdict;
- `corridor_5atr`;
- `all100`.

Запрещены входные признаки `score`, `selected`, `frozen_selected`,
top-level future target columns (`entry_up_*`, `entry_dn_*`,
`entry_log_ratio_*`) и постобработочные target/label/outcome family.

## Target Families

- `entry_log_ratio`;
- `entry_up_dn_delta`;
- `entry_up_dn_classifier`.

`build_direction_targets()` раскрывает нейтральные строки dead-zone и tie rows.
Метрики направления должны исключать нейтральные/tie строки, но сами строки
остаются раскрытыми.

## CLI

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --threads 24 \
  --resume
```

По умолчанию включён `--resume`. Повторный запуск пропускает завершённые
ключи `profile/seed/model/Hhorizon/target_family` и продолжает с оставшихся
run-ов. Для чистого полного прогона:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --threads 24 \
  --no-resume
```

CLI создаёт артефакты с `verdict = ABORT_CONTRACT_FAIL`, если scores-файл
отсутствует. Если `ML/reports/entry_based_movement_filter_freeze_scores.csv`
есть, CLI строит реальные metrics/rows.

Ограниченный smoke на реальных данных:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --profiles simple_combined \
  --horizons 3 \
  --target-families entry_log_ratio \
  --model-keys extra_trees \
  --threads 24 \
  --no-resume
```

## Narrow Replication Mode

Проверочный режим для заранее зафиксированной матрицы
`nearest_k60 / extra_trees / entry_log_ratio`:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --replication-mode narrow \
  --threads 24 \
  --no-resume
```

По умолчанию режим фиксирует:

- horizons: `H3`, `H6`, `H9`;
- seeds: `41`, `42`, `43`, `44`, `45`;
- `H3` как primary horizon;
- `H6` и `H9` как secondary robustness horizons.

Для короткого smoke:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --replication-mode narrow \
  --replication-seeds 41 \
  --horizons 3 \
  --threads 24 \
  --output-prefix ML/reports/direction_inside_frozen_movement_regime_narrow_replication_smoke \
  --no-resume
```

Обычный режим без `--replication-mode narrow` не принимает `--horizons 9`.
H9 разрешён только в narrow mode и только через target preflight.

JSON narrow mode содержит `target_preflight`, `replication_summary`,
`replication_verdict`, `time_diagnostics`,
`replication_search_budget_planned`, `replication_search_budget_executed` и
`cumulative_search_budget_disclosed`.

Verdict rules:

- `DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY`: H3 contract `PASS`,
  `failed_runs=0`, at least `3/5` H3 seeds with `val_eval_inside_mask >= 0.52`,
  H3 median `val_eval_inside_mask >= 0.525`, at least `3/5` seeds with the same
  positive sign on `val_select` and `val_eval`, and secondary horizons are not
  contradictory;
- `DIRECTION_REPLICATION_INCONCLUSIVE`: H3 is above chance but misses one
  positive criterion, or secondary robustness contradicts;
- `REJECT_DIRECTION_REPLICATION`: H3 median `val_eval_inside_mask < 0.515` or
  fewer than `2/5` H3 seeds are above `0.52`.

## Threading / Resume / Progress

- default threads: `24`;
- `ExtraTreesClassifier`: `n_jobs=24`;
- `XGBoost`: `n_jobs=24`, JSON также раскрывает `nthread=24` и
  `xgb_threads=24`;
- `HistGradientBoostingClassifier`: `n_jobs` не поддерживается estimator-ом,
  это явно записывается как `not_supported_by_estimator`;
- JSON и CSV сохраняются после каждого завершённого run;
- heartbeat печатает загрузку split/scores, start, preflight, run start/end,
  `done_runs/total_runs`, `elapsed`, `ETA`.

## Последний полный результат

Full grid `5 x 4 x 3 x 4 = 240` завершён:

- `verdict = DIRECTION_REPLICATION_REQUIRED`;
- `contract_status = PASS`;
- `progress.done_runs = 240`, `progress.total_runs = 240`;
- `failed_runs = 0`;
- winner: `nearest_k60|H3|entry_log_ratio|extra_trees`;
- `val_select_inside_mask balanced_accuracy = 0.570170`;
- `val_eval_inside_mask balanced_accuracy = 0.529056`;
- metrics CSV: `1440` data rows;
- rows CSV: `3,469,440` data rows.

Интерпретация: найден слабый direction-effect внутри frozen movement-mask,
который требует заранее зафиксированной репликации. Это не trading candidate.

Narrow replication `nearest_k60 / extra_trees / entry_log_ratio` завершена
2026-07-10:

- `verdict = REJECT_DIRECTION_REPLICATION`;
- `contract_status = PASS`;
- `progress.done_runs = 10`, `progress.total_runs = 10`;
- H9 skipped by preflight: `SKIPPED_MISSING_TARGET_COLUMNS`;
- H3 median `val_eval_inside_mask balanced_accuracy = 0.499080`;
- H3 seeds with `val_eval_inside_mask >= 0.52`: `2/5`;
- H6 median `val_eval_inside_mask balanced_accuracy = 0.528590`, but H6 was
  secondary robustness and cannot replace failed H3.

## Тесты

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Тесты покрывают row identity join, full-train policy, feature denylist,
target construction, H9 preflight, narrow replication config/job builder,
seed aggregation, verdict rules, time diagnostics, CLI-флаги, resume-пропуск,
progress JSON, очистку legacy resume rows и передачу thread count в модели.
