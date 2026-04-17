# Take/Skip Trailing Stop Design

> **Date**: 2026-04-17
> **Status**: Draft approved for implementation
> **Goal**: Проверить, даёт ли бинарная постановка `take / skip` для trailing-stop exits более рабочий trading selection layer, чем regression/quantile targets.

## Background

Предыдущие этапы проверили `trailing_stop_target_v1` и `trailing_stop_target_quantile_v1`.

Результат отрицательный:

- `trailing_stop_target_v1`: лучший validation candidate `seq20 + trail_48_pnl_atr_x3`, `PF=0.4206`;
- `trailing_stop_target_quantile_v1`: лучший validation candidate `seq20 + x3`, `PF=0.1750`;
- ни один вариант не достиг мягкого порога `PF >= 1.0`.

При этом trading decision бинарный: вход либо берём, либо пропускаем. Поэтому следующий трек должен напрямую учить это решение, а не предсказывать непрерывный PnL и потом косвенно строить selection layer.

## Target Definition

Для каждого trailing-stop параметра `X`:

```text
take_48_xN = 1, если trail_48_pnl_atr_xN >= 0.5
take_48_xN = 0, иначе
```

Где:

- `trail_48_pnl_atr_xN` — уже используемый исполнимый trailing-stop outcome за 48 баров;
- `N` — значение `X`;
- threshold `0.5 ATR` выбран как минимально полезный буфер, чтобы не считать почти нулевую сделку хорошей.

Первичная сетка:

```text
X = 2, 3, 4, 6, 8
```

`X=3` сохраняется как лучший центр предыдущей статистики. `X=4/6/8` добавляются для проверки гипотезы, что более широкий трейлинг может дать более чистые take/skip labels.

## Model Task

Новый task:

```text
take_skip_trailing_stop_v1
```

Модель должна выдавать multi-label logits/probabilities:

```text
take_48_x2
take_48_x3
take_48_x4
take_48_x6
take_48_x8
```

Это не mutually-exclusive classes: одна и та же строка может быть хорошей для `X=8`, но плохой для `X=2`, или наоборот. Поэтому используется independent binary classification per `X`.

Loss:

```text
BCEWithLogitsLoss
```

Если class imbalance окажется сильным, runner может включать `pos_weight`, рассчитанный по train split. Первый implementation должен поддерживать `pos_weight`, но benchmark verdict должен быть основан только на validation/test, не на train metrics.

Primary ML metrics:

- per-target ROC-AUC, если в split есть оба класса;
- per-target PR-AUC, если в split есть положительный класс;
- per-target positive rate;
- average BCE loss.

## Benchmark

Benchmark работает только на prediction exports и не переобучает модель.

Для каждого target `take_48_xN`:

1. На validation строится grid по predicted probability.
2. Candidate выбирается только на validation.
3. Выбранный frozen candidate применяется к test.

Candidate families:

```text
prob_ge_threshold
top_k_probability
```

Начальная сетка:

```text
thresholds = 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95
top_k = 0.5%, 1%, 2%, 3%, 5%, 7.5%, 10%
```

Trading PnL для candidate считается не по binary label, а по исходному continuous outcome:

```text
true_trail_48_pnl_atr_xN
```

Это принципиально: модель обучается классифицировать хорошие входы, но benchmark измеряет реальный PnL выбранных сделок.

Benchmark metrics:

- `trades`;
- `trades_per_year`;
- `gross_profit`;
- `gross_loss`;
- `PF`;
- `negative_year_slices`;
- `profit_concentration_top_10`;
- `ulcer_index_atr`;
- `max_drawdown_atr`;
- `positive_rate_selected`.

Selection gate for first wave:

```text
min_pf = 1.0
min_trades_per_year = 6
```

`PF >= 1.0` — мягкий диагностический порог, не production gate.

## Matrix

Планируемая training matrix:

```text
seq_len = 20, 50, 100
X = 2, 3, 4, 6, 8
```

Так как task multi-label, один training run на `seq_len` покрывает все `X`. Полная матрица:

```text
3 runs:
transformer_seq20
transformer_seq50
transformer_seq100
```

Каждый run экспортирует probabilities и true outcomes для всех `X`.

## Remote Training Workflow

Локально выполняется:

- implementation;
- unit tests;
- smoke run;
- report/runner wiring;
- commit.

Перед тяжёлым обучением agent останавливается и даёт явный сигнал:

```text
Код готов к удалённому обучению. Нужно push, pull на сервере и запуск команды ниже.
```

Сервер выполняет:

```bash
git pull
MPLCONFIGDIR=/tmp/matplotlib /path/to/.venv/bin/python \
  -m ML.run_take_skip_trailing_stop_matrix \
  --output-dir ML/reports/take_skip_trailing_stop_matrix \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

После обучения сервер должен вернуть в git:

- `summary.json`;
- `manifest.json`;
- `final_verdict.json`;
- `validation_grid.csv`;
- prediction CSV, если нужен повторный benchmark без переобучения;
- checkpoint только если есть полезный winner или нужен дальнейший анализ.

Локально после `git pull` выполняется analysis report и решение по следующему этапу.

## Non-Goals

- Не делать production integration.
- Не менять MT4 execution.
- Не запускать полный training matrix локально.
- Не добавлять новый сложный position management.
- Не подбирать `0.5 ATR` threshold по validation в этом этапе.

## Success Criteria

Минимальный успех research stage:

- хотя бы один validation candidate имеет `PF >= 1.0`;
- candidate не держится на одной сделке;
- `trades_per_year >= 6`;
- test frozen check не разваливается катастрофически.

Сильный успех:

- validation `PF >= 1.2`;
- `negative_year_slices <= 1`;
- test `PF >= 1.0`;
- profit concentration не указывает на один случайный outlier.

Если ни один candidate не достигает `PF >= 1.0`, regression/quantile/trailing-stop family считается исчерпанной в текущем виде, и следующий трек должен менять feature/label family, а не расширять ту же матрицу.
