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
реальным split/freeze артефактам. Полный grid может быть тяжёлым; для smoke
можно ограничивать профили, горизонты, target family и модели CLI-флагами.

## Входы

- entry-based split-ы из существующих baseline runners;
- frozen movement scores с обязательными колонками `split`, `split_row_id`,
  `selected`;
- target-колонки `entry_log_ratio_H`, `entry_up_H`, `entry_dn_H` для
  горизонтов `3`, `6`, `12`, `24`.

## Выходы

- `ML/reports/direction_inside_frozen_movement_regime_rich_features.json`;
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_metrics.csv`;
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_rows.csv`.

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
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py
```

Текущий CLI создаёт артефакты с `verdict = ABORT_CONTRACT_FAIL`, если
scores-файл отсутствует. Если `ML/reports/entry_based_movement_filter_freeze_scores.csv`
есть, CLI строит реальные metrics/rows.

Ограниченный smoke на реальных данных:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --profiles simple_combined \
  --horizons 3 \
  --target-families entry_log_ratio \
  --model-keys extra_trees
```

## Тесты

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Тесты покрывают row identity join, full-train policy, feature denylist,
target construction, masked sample-size gate, winner selection и базовый CLI
contract.
