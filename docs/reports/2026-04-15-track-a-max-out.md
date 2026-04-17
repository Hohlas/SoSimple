# Track A Max-Out Verdict

> **Date**: 2026-04-15 22:20
> **Status**: Completed
> **Goal**: Выжать максимум из Track A через richer feature set, несколько длин истории, bounded модельный sweep и повторный benchmark без ухода в бесконечный перебор
> **Related plan/spec**: `docs/superpowers/specs/2026-04-15-track-a-max-out-design.md`, `docs/superpowers/plans/2026-04-15-track-a-max-out.md`
> **Related commit**: pending

## Context

После `benchmark_v2` стало ясно, что текущий слой отбора почти исчерпан: ни один кандидат не давал `PF > 1` на `validation`, а winner selection почти не менял вывод даже после расширения candidate set. Для проверки оставшегося потенциала Track A был нужен один bounded max-out проход: больше признаков строки, длины истории `20/50/100`, дополнительная модель и повторный benchmark на готовых prediction exports.

## What Was Done

- Добавлен richer feature bank для `entry_path_v1`: row-wise признаки и multi-window summaries по окнам `5/10/20/50/100`.
- Контракт `entry_path_v1` расширен до `46` engineered features и поддержан для `seq_len=20/50/100`.
- Усилен baseline `EntryPathTransformer` и добавлен отдельный `EntryPathDualStreamTransformer`.
- Протянут новый контракт через `ML/data_loader.py`, `ML/train.py`, `ML/evaluate_test.py`, `API/generate_signals.py`.
- Сохранена совместимость соседнего `entry_path_v1_quantile` контура.
- Добавлен bounded orchestrator `ML/run_track_a_max_out_matrix.py` для прогона train → export → `benchmark_v2`.
- Пересобраны engineered caches:
  - `train (43764, 46)`
  - `val (9378, 46)`
  - `test (9378, 46)`
- Выполнен короткий matrix sweep `6 конфигураций x 3 epochs`.
- После short sweep выполнен deeper rerun только для двух лучших конфигураций:
  - `transformer_seq20`
  - `transformer_seq50`
  - budget: `10 epochs`, `patience=4`

## Changed Files

- `ML/entry_path_feature_bank.py`
- `ML/entry_path_task.py`
- `ML/data_loader.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`
- `ML/models/entry_path_transformer.py`
- `ML/models/entry_path_dual_stream_transformer.py`
- `ML/export_entry_path_v1_quantile_predictions.py`
- `ML/benchmark_entry_path_v1_frequency.py`
- `ML/benchmark_entry_path_v2.py`
- `ML/feature_screen_entry_path.py`
- `ML/run_track_a_max_out_matrix.py`
- `tests/test_entry_path_feature_bank.py`
- `tests/test_entry_path_task.py`
- `tests/test_entry_path_model.py`
- `tests/test_entry_path_loader_seq_len.py`
- `tests/test_entry_path_dual_stream_transformer.py`
- `tests/test_entry_path_training.py`
- `tests/test_entry_path_reports.py`
- `tests/test_entry_path_v1_quantile_training.py`
- `tests/test_entry_path_v1_quantile_reports.py`
- `tests/test_feature_screen_entry_path.py`
- `tests/test_benchmark_entry_path_v1_frequency.py`
- `tests/test_benchmark_entry_path_v2.py`
- `tests/test_track_a_max_out_matrix.py`

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_entry_path_feature_bank.py \
  tests/test_entry_path_task.py \
  tests/test_entry_path_model.py \
  tests/test_entry_path_loader_seq_len.py \
  tests/test_entry_path_dual_stream_transformer.py \
  tests/test_entry_path_training.py \
  tests/test_entry_path_v1_quantile_training.py \
  tests/test_entry_path_v1_quantile_reports.py -q
# 33 passed, 15 warnings

/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_track_a_max_out_matrix.py -q
# 2 passed

MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_track_a_max_out_matrix \
  --output-dir ML/reports/track_a_max_out_matrix \
  --epochs 3 \
  --patience 2 \
  --batch-size 256 \
  --min-pf 1.0 \
  --target-trades-per-year 40

MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_track_a_max_out_matrix \
  --output-dir ML/reports/track_a_max_out_matrix_deep \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --target-trades-per-year 40 \
  --configs transformer_seq20 transformer_seq50
```

## Results

### Short Matrix (`6 configs x 3 epochs`)

| Config | Best val `ret_r` | Validation winner | Validation PF | Test PF | Verdict |
|---|---:|---|---:|---:|---|
| `transformer_seq20` | 0.2452 | `ret24_over_adv24` | 0.3394 | 0.5103 | reject |
| `transformer_seq50` | 0.2222 | `ret24_over_adv24` | 0.3391 | 0.5877 | reject |
| `transformer_seq100` | 0.1526 | `ret24_nonflat_confidence` | 0.2335 | 0.3584 | reject |
| `entry_path_dual_stream_seq20` | 0.2248 | `ret24_only` | 0.2758 | 0.5436 | reject |
| `entry_path_dual_stream_seq50` | 0.0758 | `edge12_plus_edge24_w65` | 0.1669 | 0.2135 | reject |
| `entry_path_dual_stream_seq100` | 0.0754 | `fav24_minus_adv24_l10` | 0.1694 | 0.1738 | reject |

Общие свойства short sweep:

- во всех 6 конфигурациях `validation_rows_pf_gt_1 = 0`
- `dual_stream` не обошёл baseline transformer
- `seq_len=100` заметно хуже для обеих моделей
- лучший validation PF остался у обычного transformer на `seq_len=20/50`

### Deeper Rerun (`2 configs x 10 epochs`)

| Config | Best val `ret_r` | Validation winner | Validation PF | Test PF | Validation ulcer | Test ulcer | Verdict |
|---|---:|---|---:|---:|---:|---:|---|
| `transformer_seq20` | 0.2921 | `ret24_over_adv24` | 0.4341 | 0.9438 | 68.61 | 46.11 | reject |
| `transformer_seq50` | 0.2904 | `ret24_over_adv24` | 0.4784 | 0.9212 | 60.10 | 53.92 | reject |

Дельты относительно short sweep:

- `transformer_seq20`
  - `best val ret_r`: `+0.0470`
  - `validation PF`: `+0.0946`
  - `test PF`: `+0.4335`
  - `validation ulcer`: `-8.67`
  - `test ulcer`: `-30.85`
- `transformer_seq50`
  - `best val ret_r`: `+0.0682`
  - `validation PF`: `+0.1393`
  - `test PF`: `+0.3336`
  - `validation ulcer`: `-35.82`
  - `test ulcer`: `-15.90`

Ключевой факт deeper rerun:

- winner не изменился: в обоих случаях остался `ret24_over_adv24`
- даже после улучшения модели `validation_rows_pf_gt_1 = 0`
- лучший validation PF всего этапа: `0.4784` у `transformer_seq50`

## Conclusions

Bounded max-out проход улучшил модельные метрики и торговые числа, но не изменил главный вывод. Track A действительно удалось дожать заметно сильнее, чем в short sweep, однако потолок оказался ниже рабочего уровня: даже лучший candidate не дошёл до `PF > 1` на `validation`.

Это важный отрицательный результат:

- проблема не сводится к слишком короткому обучению
- проблема не решается простым увеличением истории до `100`
- проблема не решается добавлением отдельной `dual_stream` ветки в текущем виде
- selection layer остаётся тем же: `ret24_over_adv24` стабильно "least bad", но не становится рабочим

Практически это означает, что Track A после richer features, bounded model sweep и deeper retrain находится близко к исчерпанию.

## Limitations / Open Questions

- Max-out проход не включал бесконечный перебор архитектур или гиперпараметров; это было сознательное ограничение.
- Feature bank расширял row context и оконные сводки, но не покрывал все мыслимые агрегаты по 100 фракталам.
- Deeper rerun делался только для двух лучших конфигураций из short sweep; теоретически можно тратить ещё budget, но текущие числа не дают для этого сильного основания.
- SHAP stage не запускался, потому что benchmark не прошёл даже мягкий порог `PF > 1`.

## Next Step

Следующий разумный шаг уже не в новом `benchmark_v3` и не в ещё одном похожем retrain для Track A. Нужен переход к изменению самого обучения:

- либо новый target/objective для entry decision,
- либо другой способ постановки задачи входа,
- либо переход к следующему исследовательскому треку вне текущего Track A.

Если Track A всё же продолжать, это должно быть уже отдельным этапом с новым training objective, а не с ещё одной вариацией текущего selection layer.

## Related Materials

- `docs/reports/2026-04-15-entry-path-v1-frequency.md`
- `ML/reports/entry_path_v1_frequency_v2/`
- `ML/reports/track_a_max_out_matrix/`
- `ML/reports/track_a_max_out_matrix_deep/`
- `ML/run_track_a_max_out_matrix.py`
- `docs/superpowers/specs/2026-04-15-track-a-max-out-design.md`
- `docs/superpowers/plans/2026-04-15-track-a-max-out.md`
