# Stage 5.0e — посмертная проверка переобучения Transformer на H6_off05

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Цель:** Локально проверить, была ли слишком большая модель одной из причин провала Transformer на `H6_off05 stop broken`, не открывая заново уже исчерпанную постановку.

**Архитектура:** Добавить отдельный режим `--stage5-0e-small-transformer-check`, который обучает Transformer на заранее заданной малой сетке параметров: 1 профиль × 1 цель × 2 настройки × 3 seed. XGBoost на тех же признаках остаётся главным сравнением. Holdout 2023-2026 только раскрывается, но не участвует в решении.

**Tech Stack:** Python 3.10, PyTorch, pandas, numpy, scikit-learn, xgboost, pytest, текущий `ML/baseline/benchmark_stage5_transformer_breach.py`.

## Уровень исследования

Посмертная диагностика внутри уже закрытой ветки. Stage 5.0d зафиксировал, что постановка `H6_off05 stop broken` на текущих 9 профилях исчерпана; этот план не отменяет это решение. Проверка отвечает только на локальный вопрос: уменьшает ли малая модель признаки переобучения и приближается ли она к XGBoost на том же профиле.

## Гипотеза

В 5.0c Transformer системно уступил XGBoost на тех же признаках. При этом в одном запуске была видна картина переобучения: AUC на `val_stop` сначала росла, затем падала при продолжающемся снижении ошибки на train. Одного такого наблюдения недостаточно для нового исследовательского цикла, но достаточно для короткой посмертной проверки причины провала.

## Замороженные условия

- Цель: только `sell_stop_broken_H6_off05_flag`.
- Профили:
  - `all100_relative_price_time` — лучший sell-профиль по XGBoost в 5.0d.
- Преобразование: `asinh`, параметры fit только на train.
- Seeds: `[42, 77, 123]`.
- Split:
  - train: `year <= 2020`;
  - `val_stop`: 2021-2022;
  - holdout: 2023-2026, только раскрытие.
- Нельзя добавлять новые профили, цели или параметры после просмотра результата.
- Нельзя использовать holdout для выбора победителя.
- Нельзя объявлять Stage 5.0f автоматически. Любой неожиданный сильный результат сначала обсуждается как исключение из уже принятого решения 5.0d.
- Промежуточные commit не делать. Закрытие этапа — через `stage-reporting`.

## Проверяемые настройки

| Имя | d_model | layers | heads | ff | dropout | weight_decay | patience | learning_rate | Зачем |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `current` | 64 | 2 | 4 | 128 | 0.15 | 0.0001 | 8 | 0.001 | Контроль: текущая модель |
| `small_regularized` | 32 | 1 | 2 | 64 | 0.35 | 0.0010 | 3 | 0.0007 | Меньше ёмкость + сильнее ограничение |

`dropout` — случайное отключение части внутренних связей при обучении.  
`weight_decay` — штраф за слишком крупные веса модели.  
`patience` — сколько эпох ждать без улучшения на `val_stop`.

## Критерии решения

Решение делится на два независимых поля.

### `overfit_hypothesis_supported`

`yes`, если `small_regularized` одновременно:

- уменьшает median `overfit_drop_after_best` минимум на `0.01` против `current`;
- не ухудшает median `val_auc` против `current` больше чем на `0.005`;
- имеет разброс `val_auc` между seed не больше `0.02`.

Иначе `no`. Это поле отвечает только на вопрос о переобучении.

### `transformer_reopens_h6_off05`

По умолчанию `no`. Изменить на `review_required` можно только если `small_regularized` одновременно:

- не хуже XGBoost same-profile по median `val_auc`;
- не хуже XGBoost same-profile по median `val_lift_30`;
- выполняет оба условия минимум на 2 из 3 seed;
- имеет разброс `val_auc` между seed не больше `0.02`.

Даже `review_required` не открывает Stage 5.0f автоматически. Он означает только, что нужно отдельно обсудить, достаточно ли результата, чтобы нарушить уже принятое решение 5.0d.

## Ожидаемые артефакты

- `ML/reports/stage5_0e_small_transformer_check.json`
- `docs/reports/2026-06-23-stage5_0e-small-transformer-check.md`
- обновление `CHANGELOG.md`
- обновление `CONTEXT_HANDOFF.md` при закрытии этапа
- wiki ingest при закрытии этапа

---

## Task 1: Зафиксировать настройки 5.0e

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `STAGE5_0E_TARGET`
- Produces: `STAGE5_0E_PROFILE_NAMES`
- Produces: `STAGE5_0E_SEEDS`
- Produces: `STAGE5_0E_MODEL_CONFIGS`
- Produces: `STAGE5_0E_JSON_REPORT_PATH`

- [ ] **Step 1: Add failing test**

```python
def test_stage5_0e_constants_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_0E_TARGET == "sell_stop_broken_H6_off05_flag"
    assert runner.STAGE5_0E_PROFILE_NAMES == [
        "all100_relative_price_time",
    ]
    assert runner.STAGE5_0E_SEEDS == [42, 77, 123]
    assert [cfg["name"] for cfg in runner.STAGE5_0E_MODEL_CONFIGS] == [
        "current",
        "small_regularized",
    ]
    assert runner.STAGE5_0E_MODEL_CONFIGS[1]["d_model"] == 32
    assert runner.STAGE5_0E_MODEL_CONFIGS[1]["dropout"] == 0.35
    assert str(runner.STAGE5_0E_JSON_REPORT_PATH).endswith(
        "stage5_0e_small_transformer_check.json"
    )
```

- [ ] **Step 2: Run failing test**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k test_stage5_0e_constants_are_frozen -q
```

- [ ] **Step 3: Add constants near Stage 5.0d constants**

```python
STAGE5_0E_TARGET = "sell_stop_broken_H6_off05_flag"
STAGE5_0E_PROFILE_NAMES = [
    "all100_relative_price_time",
]
STAGE5_0E_SEEDS = [42, 77, 123]
STAGE5_0E_MODEL_CONFIGS = [
    {
        "name": "current",
        "d_model": 64,
        "nhead": 4,
        "num_layers": 2,
        "dim_feedforward": 128,
        "dropout": 0.15,
        "weight_decay": 1e-4,
        "learning_rate": 1e-3,
        "patience": 8,
    },
    {
        "name": "small_regularized",
        "d_model": 32,
        "nhead": 2,
        "num_layers": 1,
        "dim_feedforward": 64,
        "dropout": 0.35,
        "weight_decay": 1e-3,
        "learning_rate": 7e-4,
        "patience": 3,
    },
]
STAGE5_0E_JSON_REPORT_PATH = REPORTS_DIR / "stage5_0e_small_transformer_check.json"
```

- [ ] **Step 4: Run test again**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k test_stage5_0e_constants_are_frozen -q
```

---

## Task 2: Разрешить Transformer принимать настройки из конфига

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Modify: `train_transformer(..., model_config: dict | None = None)`
- Existing callers must keep current behavior when `model_config is None`.

- [ ] **Step 1: Add failing test**

```python
def test_train_transformer_accepts_model_config(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    captured = {}

    class DummyModel(torch.nn.Module):
        def __init__(self, **kwargs):
            super().__init__()
            captured.update(kwargs)
            self.linear = torch.nn.Linear(1, 1)

        def forward(self, tokens, row_feat, mask):
            return self.linear(tokens[:, :1, :1])

    monkeypatch.setattr(runner, "FractalBreachTransformer", DummyModel)

    tokens = np.random.rand(8, 2, 1).astype(np.float32)
    row = np.random.rand(8, 1).astype(np.float32)
    mask = np.ones((8, 2), dtype=bool)
    y = pd.Series([0, 1, 0, 1, 0, 1, 0, 1])

    runner.train_transformer(
        tokens, row, mask, y,
        tokens, row, mask, y,
        profile={"name": "unit"},
        seed=42,
        device=torch.device("cpu"),
        model_config={
            "d_model": 32,
            "nhead": 2,
            "num_layers": 1,
            "dim_feedforward": 64,
            "dropout": 0.35,
            "weight_decay": 1e-3,
            "learning_rate": 7e-4,
            "patience": 3,
        },
    )

    assert captured["d_model"] == 32
    assert captured["nhead"] == 2
    assert captured["num_layers"] == 1
    assert captured["dim_feedforward"] == 64
    assert captured["dropout"] == 0.35
```

- [ ] **Step 2: Run failing test**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k test_train_transformer_accepts_model_config -q
```

- [ ] **Step 3: Implement config fallback**

Inside `train_transformer`:

```python
cfg = model_config or {
    "d_model": D_MODEL,
    "nhead": NHEAD,
    "num_layers": NUM_LAYERS,
    "dim_feedforward": DIM_FEEDFORWARD,
    "dropout": DROPOUT,
    "weight_decay": WEIGHT_DECAY,
    "learning_rate": LEARNING_RATE,
    "patience": EARLY_STOPPING_PATIENCE,
}
```

Use `cfg[...]` when creating `FractalBreachTransformer`, `AdamW`, and early stopping patience.

- [ ] **Step 4: Return richer history**

Add to returned history:

```python
"best_epoch": int(np.argmax(val_aucs) + 1),
"last_val_auc": float(val_aucs[-1]),
"overfit_drop_after_best": float(max(val_aucs) - val_aucs[-1]),
"model_config": cfg,
```

- [ ] **Step 5: Run focused and full tests**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k "train_transformer or stage5_0e" -q
./.venv/bin/python -m pytest tests/ -q
```

---

## Task 3: Добавить runner Stage 5.0e

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `run_stage5_0e_small_transformer_check(sell_splits, seed, device, output_path=STAGE5_0E_JSON_REPORT_PATH) -> dict`

- [ ] **Step 1: Add failing test**

```python
def test_stage5_0e_runner_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(12, 100)

    monkeypatch.setattr(runner, "STAGE5_0E_PROFILE_NAMES", ["all100_relative_price_time"])
    monkeypatch.setattr(runner, "STAGE5_0E_SEEDS", [42])
    monkeypatch.setattr(runner, "STAGE5_0E_MODEL_CONFIGS", [
        {
            "name": "small_regularized",
            "d_model": 32,
            "nhead": 2,
            "num_layers": 1,
            "dim_feedforward": 64,
            "dropout": 0.35,
            "weight_decay": 1e-3,
            "learning_rate": 7e-4,
            "patience": 3,
        }
    ])
    monkeypatch.setattr(runner, "verify_breach_labels_against_ohlc", lambda *a, **k: {"status": "PASS"})
    monkeypatch.setattr(runner, "label_sanity_check", lambda *a, **k: {"status": "PASS"})
    monkeypatch.setattr(runner, "compute_xgb_same_profile_baseline", lambda *a, **k: {
        "val": {"auc": 0.67, "lift_30": 0.52},
        "holdout": {"auc": 0.64, "lift_30": 0.55},
    })
    monkeypatch.setattr(runner, "_train_and_eval_profile", lambda *a, **k: {
        "profile": "all100_relative_price_time",
        "target": runner.STAGE5_0E_TARGET,
        "val": {"auc": 0.668, "lift_30": 0.53},
        "holdout": {"auc": 0.64, "lift_30": 0.56},
        "history": {"best_epoch": 4, "overfit_drop_after_best": 0.002},
    })

    report = runner.run_stage5_0e_small_transformer_check(
        (df, df, df),
        seed=42,
        device=torch.device("cpu"),
        output_path=tmp_path / "stage5_0e.json",
    )

    assert report["stage"] == "5.0e_small_transformer_overfit_check"
    assert report["holdout_used_for_decision"] is False
    assert report["target"] == runner.STAGE5_0E_TARGET
    assert report["decision"]["status"] == "DIAGNOSTIC_ONLY"
    assert report["decision"]["overfit_hypothesis_supported"] in {"yes", "no"}
    assert report["decision"]["transformer_reopens_h6_off05"] in {"no", "review_required"}
    assert (tmp_path / "stage5_0e.json").exists()
```

- [ ] **Step 2: Run failing test**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k test_stage5_0e_runner_writes_json -q
```

- [ ] **Step 3: Implement runner**

Runner must:

- run OHLC verification and label sanity for sell;
- loop over 1 profile;
- compute XGBoost same-profile once per profile;
- train Transformer for each config × seed;
- store per-run `val`, `holdout`, `history`, `model_config`;
- compute median `val_auc`, median `val_lift_30`, seed spread;
- compare only on `val_stop`;
- set `holdout_used_for_decision=false`.

- [ ] **Step 4: Implement decision helper**

Add `stage5_0e_overfit_decision(report: dict) -> dict`:

```python
overfit_hypothesis_supported = "yes" if small_regularized:
    median_overfit_drop_after_best <= current_median_overfit_drop_after_best - 0.01
    and median_val_auc >= current_median_val_auc - 0.005
    and seed_spread <= 0.02
else "no"

transformer_reopens_h6_off05 = "review_required" if small_regularized:
    median_val_auc >= xgb_val_auc
    and median_val_lift_30 <= xgb_val_lift_30
    and per_seed_xgb_auc_and_lift_pass_count >= 2
    and seed_spread <= 0.02
else "no"
```

Return:

```python
{
    "status": "DIAGNOSTIC_ONLY",
    "overfit_hypothesis_supported": "yes" | "no",
    "transformer_reopens_h6_off05": "no" | "review_required",
    "best_profile": ...,
    "best_config": ...,
    "reason": "...",
    "next_step": "...",
}
```

- [ ] **Step 5: Run focused and full tests**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k "stage5_0e or train_transformer" -q
./.venv/bin/python -m pytest tests/ -q
```

---

## Task 4: Добавить CLI и запустить эксперимент

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`
- Create: `ML/reports/stage5_0e_small_transformer_check.json`

- [ ] **Step 1: Add failing CLI test**

```python
def test_stage5_0e_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-0e-small-transformer-check"])
    assert args.stage5_0e_small_transformer_check is True
```

- [ ] **Step 2: Add parser argument**

```python
parser.add_argument(
    "--stage5-0e-small-transformer-check",
    action="store_true",
    help="Stage 5.0e: проверка меньшего Transformer против переобучения",
)
```

- [ ] **Step 3: Add main branch**

After Stage 5.0d branch:

```python
if args.stage5_0e_small_transformer_check:
    sell_splits = load_splits(target_col=STAGE5_0E_TARGET)
    report = run_stage5_0e_small_transformer_check(
        sell_splits,
        seed=args.seed,
        device=device,
        output_path=STAGE5_0E_JSON_REPORT_PATH,
    )
    print(json.dumps(report["decision"], indent=2))
    return
```

- [ ] **Step 4: Run tests**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k "stage5_0e or train_transformer" -q
./.venv/bin/python -m pytest tests/ -q
```

- [ ] **Step 5: Run experiment**

```bash
./.venv/bin/python ML/baseline/benchmark_stage5_transformer_breach.py --stage5-0e-small-transformer-check
```

Expected:

- creates `ML/reports/stage5_0e_small_transformer_check.json`;
- trains 1 profile × 2 configs × 3 seeds = 6 Transformer runs;
- computes 1 XGBoost same-profile comparison;
- does not use holdout for decision.

---

## Task 5: Написать отчёт и закрыть этап

**Files:**
- Create: `docs/reports/2026-06-23-stage5_0e-small-transformer-check.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: wiki files through `wiki/wiki.py`

- [ ] **Step 1: Read JSON**

```bash
./.venv/bin/python -m json.tool ML/reports/stage5_0e_small_transformer_check.json >/tmp/stage5_0e_check.json
```

- [ ] **Step 2: Write report**

Report must include:

- hypothesis;
- frozen profiles/configs/seeds;
- XGBoost comparison on same features;
- median AUC/lift by profile and config;
- seed spread;
- overfit drop after best epoch;
- holdout disclosure only;
- decision: `DIAGNOSTIC_ONLY`;
- `overfit_hypothesis_supported`;
- `transformer_reopens_h6_off05`;
- next step.

- [ ] **Step 3: Update `CHANGELOG.md`**

Add one short entry near the top with:

- date;
- artifact paths;
- decision;
- key metric table summary;
- `overfit_hypothesis_supported`;
- `transformer_reopens_h6_off05`;
- подтверждение, что H6_off05 остаётся закрытым, если нет отдельного решения пользователя.

- [ ] **Step 4: Update `CONTEXT_HANDOFF.md`**

Add current state and next action.

- [ ] **Step 5: Run docs/code checks**

```bash
./.venv/bin/python -m pytest tests/ -q
wiki/wiki.py status
wiki/wiki.py generate
```

- [ ] **Step 6: Do not commit until user approves**

Show:

```bash
git status --short
```

Then ask user whether to close the stage through `stage-reporting`.
