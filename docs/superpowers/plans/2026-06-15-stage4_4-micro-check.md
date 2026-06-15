# Stage 4.4 Diagnostic Micro-Check — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking. Do not commit unless the user explicitly asks.

**Goal:** Выполнить три быстрых диагностических проверки перед стартом Stage 5.0 Transformer, не открывая test и не выбирая нового winner. Проверить: (1) даёт ли ослабление breach-фильтра рост PF; (2) уступает ли fav-based TP фиксированному TP; (3) работает ли breach сам по себе без fav-фильтров. Все результаты — `DIAGNOSTIC_ONLY`: данные те же, где исторически выбран Stage 4 winner.

**Architecture:** Один diagnostic runner переиспользует расширенный симулятор из `diagnose_stage4_3.py` (`simulate_trades` с параметрами `tp_policy`, `tp_policy_value`, `skip_min_fav`, `skip_min_rr`) и инфраструктуру данных/моделей из `diagnose_stage4_gap.py` (split, features, model training) на фиксированных Stage 4.2 обученных моделях. Нового model selection не проводится; допускается детерминированное переобучение Stage 4.2-моделей с теми же параметрами, split и seed, если готовый кэш отсутствует. Результат — один JSON с тремя блоками экспериментов. Каждый блок содержит yearly PF, block bootstrap (size=15, 500 iter) и permutation test.

**Tech Stack:** Python 3.10+, pandas, numpy, XGBoost, scikit-learn. Использовать `~/git/SoSimple/.venv/bin/python`.

**Source:** `docs/audit/next.md:38-52`

---

## Source Of Truth

План реализует диагностические гипотезы из:

- `docs/audit/next.md` — предлагаемый план исследований после Stage 4.3
- `docs/reports/2026-06-15-stage4_3-diagnostics.md` — Stage 4.3 post-mortem (fav/breach diagnostics, oracle regimes)
- `ML/baseline/diagnose_stage4_3.py` — расширенный симулятор с `tp_policy`, `skip_min_fav`, `skip_min_rr` и helper-функции (метрики, bootstrap, loss attribution)
- `ML/baseline/diagnose_stage4_gap.py` — загрузка данных, split, feature profiles, обучение моделей (XGBoost breach, RF fav)

Не использовать данные за пределами val_eval (≥2019). Нового model selection нет: модели те же, что в Stage 4.2; допускается детерминированное переобучение с теми же параметрами, split и seed, если готовый кэш отсутствует.

## Жёсткие Границы

Stage 4.4:

- не открывает test;
- не выбирает нового winner;
- не меняет модель (используются обученные Stage 4.2 XGBoost breach + RF fav; допускается детерминированное переобучение с теми же параметрами, split и seed при отсутствии кэша — см. Task 1 Step 4);
- не меняет train/val split (train ≤2016, val_stop 2017-2018, val_eval ≥2019);
- не запускает grid search как candidate selection;
- не повышает verdict Stage 4;
- не доказывает прибыльность.

Разрешено:

- варьировать пороги входа (p) и TP-политику на одних и тех же обученных моделях;
- сравнить breach-only entry + fixed TP с текущим baseline;
- зафиксировать, уступает ли fav-based TP фиксированному TP;
- сформулировать гипотезы для Stage 5.0 (нужно ли учить fav как цену TP или достаточно как фильтр).

Запрещено интерпретировать:

- лучшую ячейку как торговое правило;
- любой PF > 1.15 как PASS;
- результаты как доказательство, что breach работает без fav.

## Out Of Scope

Не входит в этот план:

- Trailing stop (вынесен в отдельный план Stage 4.5);
- Transformer Stage 5.0 (отдельный план);
- Feature-engineering для fav (Вектор C);
- Relax p=0.6 или другие значения кроме p=0.5 (p=0.5 — заранее зафиксированный одиночный тест);
- Grid search TP-политик (только R ∈ {0.5, 0.7, 1.0});
- Test/frozen evaluation;
- MT4/tester parity.

## Search Budget Disclosure

Отчёт Stage 4.4 обязан явно указать количество диагностических проверок:

| Эксперимент | Вариантов | diagnostic_cells |
|-------------|:---------:|:----------------:|
| Relax breach (p=0.5) | 1 | 1 |
| Fixed TP (R ∈ {0.5, 0.7, 1.0}) с текущим breach+fav-фильтром | 3 | 3 |
| Breach-only entry (no fav, no min_rr) + Fixed TP (R ∈ {0.5, 0.7, 1.0}) | 1 breach × 3 TP | 3 |
| Baseline (Stage 4.2, для сравнения) | 1 | 1 |
| **Итого** | | **8** |

Каждая diagnostic_cell получает block bootstrap (500 iter, size=15) и yearly PF. Дополнительно для ячеек с breach-фильтром (baseline, relax breach, breach-only) выполняется permutation test: переставляется только `predict_break`, остальные параметры (pred_fav, TP-политика) фиксированы. Permutation повторяет полный цикл входного фильтра и симуляции 500 раз. Суммарно:

| Тип проверки | Ячеек | Повторов | Всего запусков |
|-------------|:-----:|:--------:|:--------------:|
| diagnostic_cells | 8 | 1 | 8 |
| block bootstrap (per cell) | 8 | 500 | 4000 (симуляция resampled сделок) |
| permutation test (breach-ячейки: baseline, relax, 3×breach-only) | 5 | 500 | 2500 (полный цикл симуляции) |
| **negative_control_runs всего** | | | **6500** |

Оценка проводится на одном и том же `val_eval` (≥2019), где исторически выбран Stage 4 winner. Любая diagnostic_cell с PF > 1.15 помечается как `hypothesis_only`.

## Файлы

| Файл | Действие | Назначение |
|---|---|---|
| `ML/baseline/diagnose_stage4_4.py` | Create | Единый diagnostic runner Stage 4.4 |
| `ML/reports/stage4_4_micro_check.json` | Generate | Structured artifact диагностики |
| `docs/reports/2026-06-15-stage4_4-micro-check.md` | Create | Канонический отчёт Stage 4.4 |
| `MODULE_INDEX.md` | Modify | Добавить новый ML-модуль |

Документационные файлы `CHANGELOG.md` и `CONTEXT_HANDOFF.md` обновлять только если пользователь явно закрывает этап.

## Общая Реализация

`diagnose_stage4_4.py` переиспользует инфраструктуру `diagnose_stage4_gap.py`:

- split: train `<=2016`, val_stop `2017-2018`, val_eval `>=2019`;
- early stopping: только `val_stop`;
- target: `sell_H6_off05`;
- feature profile breach: `base_raw_plus_time`;
- fav model: RF fav как в Stage 4.2;
- обученные модели: загружаются/обучаются идентично Stage 4.2 (XGBoost breach с `val_stop` early stopping, RF fav на train);
- OHLC convention: OHLC=Bid;
- spread: canonical `0.20`;
- entry: Open следующего бара;
- exit: first-touch SL/TP/TIMEOUT, ambiguous bar = SL;
- block bootstrap: block size 15, seed fixed.

**Главное требование:** все 8 ячеек (1 baseline + 7 экспериментальных) симулируются от одного и того же aligned trade frame с `trade_id`/`row_index`, чтобы можно было сравнить, какие сделки добавляются/исключаются при изменении порогов.

**Конвенция имён порогов:**

- `p` — порог `predict_break`: сделка входит, если `predict_break < p` (низкий риск пробоя = вход)
- `min_fav` — минимальное `pred_fav` (в ATR): сделка входит, если `pred_fav >= min_fav`
- `min_rr` — минимальный `pred_fav / stop_val`: сделка входит, если `pred_fav / stop_val >= min_rr`
- `tp_fraction` — доля `pred_fav` для TP: `tp_val = pred_fav * tp_fraction`
- `tp_fixed_R` — для fixed TP: `tp_val = stop_val * R`

**Baseline (Stage 4.2):** `p=0.4`, `min_fav=0.3`, `min_rr=1.0`, `tp_fraction=0.4`.

**Relax breach:** `p=0.5`, остальные параметры как в baseline.

**Fixed TP c breach+fav фильтром:** `p=0.4`, `min_fav=0.3`, `min_rr=1.0`, но вместо `tp_fraction` используется `tp_fixed_R ∈ {0.5, 0.7, 1.0}`.

**Breach-only entry + Fixed TP:** `p=0.4`, без `min_fav` и `min_rr` (все eligible строки, прошедшие breach-фильтр, входят), `tp_fixed_R ∈ {0.5, 0.7, 1.0}`.

---

### Task 1: Diagnostic Runner Skeleton

**Files:**
- Create: `ML/baseline/diagnose_stage4_4.py`

- [ ] **Step 1: Создать file header**

Header описывает:
- входы: `DATA/Nero_XAUUSD_*_labeled.csv`, `DATA/XAUUSD_H1_OHLC.csv`;
- выход: `ML/reports/stage4_4_micro_check.json`;
- статус: `DIAGNOSTIC_ONLY`;
- запрет: no test, no winner selection, no new model training.

- [ ] **Step 2: Импортировать инфраструктуру из правильных источников**

Из `ML/baseline/diagnose_stage4_gap.py` (загрузка данных, split, features, model training):
- `load_splits`;
- `profile_base_raw`, `profile_base_raw_plus_time`;
- `compute_entry_prices`;
- `train_xgb_breach`;
- `train_rf_fav`.

Из `ML/baseline/diagnose_stage4_3.py` (расширенный симулятор и helper-функции):
- `simulate_trades` — поддерживает `tp_policy`, `tp_policy_value`, `skip_min_fav`, `skip_min_rr`. Это единственная версия, способная реализовать Experiment 2/3 без дублирования логики;
- `resolve_tp_val`;
- `compute_trade_metrics`;
- `compute_yearly_metrics`;
- `loss_attribution`;
- `block_bootstrap_pf`.

**Почему не `diagnose_stage4_gap.py::simulate_trades`:** та версия не поддерживает `tp_policy`/`fixed_r`/`skip_min_fav`/`skip_min_rr`. Experiment 2 (fixed TP) и Experiment 3 (breach-only) нельзя корректно реализовать без этих параметров.

- [ ] **Step 3: Добавить CLI**

```bash
--train DATA/Nero_XAUUSD_train_labeled.csv
--val DATA/Nero_XAUUSD_validation_labeled.csv
--ohlc DATA/XAUUSD_H1_OHLC.csv
--output ML/reports/stage4_4_micro_check.json
--spread 0.20
--seed 42
```

- [ ] **Step 4: Загрузить или детерминированно переобучить модели**

Нового model selection нет. Допускается детерминированное переобучение Stage 4.2-моделей с теми же параметрами, split и seed, если готовый кэш отсутствует:

- XGBoost breach: `train_xgb_breach` на train (≤2016), early stopping на val_stop (2017-2018), фиксированный seed, те же гиперпараметры что в Stage 4.2;
- RF fav: `train_rf_fav` на train, фиксированный seed.

Если обученные модели уже есть в кэше (pickle/joblib) от Stage 4.2/4.3 — загрузить их, не переобучая. Убедиться, что Breach AUC на val_eval = 0.6674 (Stage 4.2 baseline). Если AUC отличается более чем на 0.001 — ошибка в данных или параметрах, исправить до продолжения.

- [ ] **Step 5: Построить единый полный val_eval/eligible frame**

**Критически важно:** `simulate_trades` из `diagnose_stage4_3.py` обращается к `entry_prices[i]`, `breach_proba[i]`, `fav_pred[i]` по порядковому индексу `i` внутри цикла `df.iterrows()`. Поэтому нельзя предварительно фильтровать `df` без синхронной фильтрации параллельных массивов.

**Правильный подход:** для всех 8 ячеек используется один и тот же полный `df` (все val_eval строки) и те же полные массивы `entry_prices`, `breach_proba`, `fav_pred`. Фильтры (`p`, `min_fav_val`, `min_rr`, `skip_min_fav`, `skip_min_rr`) и TP-политика (`tp_policy`, `tp_policy_value`) передаются как параметры в `simulate_trades`, который применяет их внутри цикла.

Для построения полного val_eval/eligible frame:
- Загрузить val_eval df (≥2019);
- Вычислить `entry_prices` через `compute_entry_prices` на всём df;
- Вычислить `breach_proba` и `fav_pred` на всём df через обученные модели;
- Все три массива имеют длину `len(df)` и индексируются синхронно с `df.iterrows()`.

Для сравнения сделок между ячейками: каждая сделка в `return_details=True` содержит `row_index` (из `df`), `trade_id`, `candidate_id` (если есть). Стабильный `row_index` позволяет сопоставить сделки между разными конфигурациями.

- [ ] **Step 6: Верификация baseline**

Запустить симуляцию с baseline-параметрами (`p=0.4`, `min_fav=0.3`, `min_rr=1.0`, `tp_fraction=0.4`) и сверить:
- PF = 1.015;
- n_trades = 503;
- BS median = 0.996, BS p05 = 0.837.

Если baseline не воспроизводится — ошибка в aligned frame или симуляции, исправить до продолжения.

---

### Task 2: Experiment 1 — Relax Breach Filter

**Files:**
- Modify: `ML/baseline/diagnose_stage4_4.py`

- [ ] **Step 1: Relax breach p=0.5**

Вызвать `simulate_trades` на полном val_eval/eligible frame с параметрами:
```python
simulate_trades(df_val, entry_prices, breach_proba, fav_pred, ohlc, times, time_idx,
                side='sell', h=6, stop_offset=0.5,
                p=0.5, min_fav_val=0.3, min_rr=1.0, tp_fraction=0.4,
                cap=5.0, spread=0.20, return_details=True,
                tp_policy='fav_fraction', tp_policy_value=0.4,
                skip_min_fav=False, skip_min_rr=False)
```

Фильтр `predict_break < 0.5` применяется внутри симулятора. Остальные параметры идентичны baseline.

- [ ] **Step 2: Считать метрики**

Для полученного списка сделок:
- `pf`, `n_trades`, `trades_per_year`;
- yearly PF, TP%/SL%/TIMEOUT% per year;
- block bootstrap (500 iter, size=15): median, p05, p95;
- permutation test: переставляется только `predict_break` (массив `breach_proba` перемешивается случайно, `pred_fav` и TP-политика фиксированы), затем повторяется полный цикл `simulate_trades` с `p=0.5`. Сохранить perm median, perm max, долю перестановок PF ≥ наблюдаемого.

- [ ] **Step 3: Сравнить с baseline**

Сохранить delta по всем метрикам относительно baseline:
- ΔPF, Δn_trades, ΔBS_p05;
- Какие сделки добавились (были исключены при p=0.4, вошли при p=0.5) — сравнить по `row_index`;
- Какие сделки исчезли (нет — порог ослабляется, не ужесточается);
- Oracle-диагностика добавленных строк: сколько из них oracle-безопасны (`breach_flag_true==0`), сколько oracle-плохие (`breach_flag_true==1`).

---

### Task 3: Experiment 2 — Fixed TP (fav-based entry filter остаётся)

**Files:**
- Modify: `ML/baseline/diagnose_stage4_4.py`

- [ ] **Step 1: Fixed TP сетка**

Для каждого R ∈ {0.5, 0.7, 1.0} вызвать `simulate_trades` на полном val_eval/eligible frame:
```python
simulate_trades(df_val, entry_prices, breach_proba, fav_pred, ohlc, times, time_idx,
                side='sell', h=6, stop_offset=0.5,
                p=0.4, min_fav_val=0.3, min_rr=1.0, tp_fraction=0.4,
                cap=5.0, spread=0.20, return_details=True,
                tp_policy='fixed_r', tp_policy_value=R,
                skip_min_fav=False, skip_min_rr=False)
```

Входной фильтр идентичен baseline (`p=0.4`, `min_fav_val=0.3`, `min_rr=1.0`). Отличие только в `tp_policy='fixed_r'` и `tp_policy_value=R` — TP вычисляется как `stop_val * R` вместо `pred_fav * 0.4`. SL всегда `stop_val`.

- [ ] **Step 2: Посчитать метрики**

Для каждого R: те же метрики что в Task 2 Step 2, плюс:
- actual RR distribution (mean, median, p05/p95);
- avg win в ATR и R;
- avg loss в ATR и R;
- сравнение с baseline TP-распределением.

Permutation test для fixed TP: переставляется только `predict_break`, TP-политика (fixed_r) остаётся как есть. Это диагностирует вклад breach-ранжирования, а не исправляет множественное тестирование.

- [ ] **Step 3: Сравнить с baseline**

Для каждого R: ΔPF, Δn_trades, ΔBS_p05, разница в avg win/loss.

---

### Task 4: Experiment 3 — Breach-Only Entry + Fixed TP

**Files:**
- Modify: `ML/baseline/diagnose_stage4_4.py`

- [ ] **Step 1: Breach-only + Fixed TP сетка**

Для каждого R ∈ {0.5, 0.7, 1.0} вызвать `simulate_trades` на полном val_eval/eligible frame:
```python
simulate_trades(df_val, entry_prices, breach_proba, fav_pred, ohlc, times, time_idx,
                side='sell', h=6, stop_offset=0.5,
                p=0.4, min_fav_val=0.3, min_rr=1.0, tp_fraction=0.4,
                cap=5.0, spread=0.20, return_details=True,
                tp_policy='fixed_r', tp_policy_value=R,
                skip_min_fav=True, skip_min_rr=True)
```

Ключевое отличие: `skip_min_fav=True` и `skip_min_rr=True` — входной фильтр только `predict_break < 0.4`, без fav-порогов. TP: `stop_val * R`.

- [ ] **Step 2: Метрики и сравнение**

Те же метрики что в Task 3, плюс:
- Сравнение с baseline: какие сделки добавились (прошедшие breach, но отсеянные fav-фильтром) — сравнить по `row_index`;
- Oracle-диагностика добавленных строк: сколько из них oracle-безопасны, сколько oracle-плохие;
- Сравнение с Experiment 2 (breach+fav фильтр + тот же R): изолированный вклад fav-фильтра.

---

### Task 5: JSON Output And Report

**Files:**
- Generate: `ML/reports/stage4_4_micro_check.json`
- Create: `docs/reports/2026-06-15-stage4_4-micro-check.md`

- [ ] **Step 1: JSON schema**

```json
{
  "status": "DIAGNOSTIC_ONLY",
  "source": "docs/audit/next.md",
  "config": {
    "target": "sell_H6_off05",
    "split": "train<=2016, val_stop 2017-2018, val_eval>=2019",
    "spread": 0.20,
    "breach_auc_val_eval": 0.0,
    "bootstrap_iter": 500,
    "bootstrap_block_size": 15
  },
  "search_budget": {
    "relax_breach_cells": 1,
    "fixed_tp_cells": 3,
    "breach_only_cells": 3,
    "baseline_cells": 1,
    "total_cells": 8
  },
  "baseline": {},
  "experiment_1_relax_breach": {},
  "experiment_2_fixed_tp": [],
  "experiment_3_breach_only": [],
  "comparison_summary": {},
  "interpretation_guards": [
    "DIAGNOSTIC_ONLY: no test opened, no winner selected, Stage 4 verdict unchanged",
    "All cells evaluated on same val_eval where Stage 4 winner was historically selected",
    "hypothesis_only cells require separate clean val_select/val_eval protocol"
  ]
}
```

- [ ] **Step 2: Report sections**

Отчёт должен содержать:
- Context (зачем Stage 4.4, что уже известно из Stage 4.3);
- Methodology and split;
- Search budget disclosure;
- Baseline sanity check (воспроизведение Stage 4.2 PF=1.015, n=503);
- Experiment 1: Relax breach p=0.5 — результаты, сравнение с baseline, oracle-диагностика добавленных строк;
- Experiment 2: Fixed TP — результаты, сравнение с baseline;
- Experiment 3: Breach-only entry + Fixed TP — результаты, сравнение с baseline и Experiment 2;
- Comparison summary: таблица всех 8 ячеек;
- What can and cannot be concluded;
- Implications for Stage 5.0 Transformer design (fav как фильтр vs fav как цена TP);
- Related artifacts.

- [ ] **Step 3: Explicit non-conclusions**

В отчёте обязательно написать:
- Stage 4.4 не выбирает winner;
- test не открыт;
- лучшая ячейка не является торговым правилом;
- трейлинг не проверялся;
- Stage 4 verdict не меняется;
- результаты не доказывают, что breach работает без fav — только диагностика на исторических данных.

---

### Task 6: Docs, Index, Wiki, Smoke Tests

**Files:**
- Create: `docs/ML/diagnose_stage4_4.py.md`
- Create: `tests/test_diagnose_stage4_4.py` (smoke-тесты)
- Modify: `MODULE_INDEX.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/log.md`
- Regenerate: `wiki/REPO_integrity.md`

- [ ] **Step 1: Module docs**

Создать короткую страницу: назначение, входы, выходы, команда запуска, статус `DIAGNOSTIC_ONLY`, ограничения интерпретации.

- [ ] **Step 2: Smoke-тесты**

Минимальный набор smoke-тестов (не полный TDD, но проверка критической логики):
- `test_fixed_tp_uses_stop_val_times_R`: `resolve_tp_val('fixed_r', 0.5, pred_fav=2.0, stop_val=1.2)` → `0.6`;
- `test_skip_min_fav_increases_universe`: симуляция с `skip_min_fav=True` даёт не меньше сделок, чем с `skip_min_fav=False`;
- `test_baseline_reproduces`: smoke-проверка, что baseline-запуск не падает и возвращает n_trades > 0.

- [ ] **Step 3: MODULE_INDEX**

Добавить `ML/baseline/diagnose_stage4_4.py` в раздел ML.

- [ ] **Step 4: Wiki — обновить research-страницу**

Добавить секцию Stage 4.4 в `wiki/research/fractal-stop-research.md` (по аналогии с существующими Stage 4.3 и другими):
- цель (diagnostic micro-check перед Transformer);
- ключевые результаты (будут заполнены после выполнения);
- ссылка на канонический отчёт.

- [ ] **Step 5: Wiki — записать в log**

Добавить запись в `wiki/log.md` о создании плана Stage 4.4.

- [ ] **Step 6: Wiki integrity**

```bash
~/git/SoSimple/.venv/bin/python wiki/wiki.py generate
~/git/SoSimple/.venv/bin/python wiki/wiki.py verify
```

---

## Верификация

```bash
# Run smoke tests
~/git/SoSimple/.venv/bin/python -m pytest tests/test_diagnose_stage4_4.py -q

# Run diagnostic
~/git/SoSimple/.venv/bin/python -m ML.baseline.diagnose_stage4_4 \
  --output ML/reports/stage4_4_micro_check.json

# Verify JSON schema
~/git/SoSimple/.venv/bin/python - <<'PY'
import json
from pathlib import Path

p = Path("ML/reports/stage4_4_micro_check.json")
d = json.loads(p.read_text())
required = [
    "status", "config", "search_budget", "baseline",
    "experiment_1_relax_breach", "experiment_2_fixed_tp",
    "experiment_3_breach_only", "comparison_summary",
    "interpretation_guards",
]
for key in required:
    assert key in d, f"missing {key}"
assert d["status"] == "DIAGNOSTIC_ONLY"
assert abs(d["baseline"]["pf"] - 1.015) < 0.001, f"baseline PF mismatch: {d['baseline']['pf']}"
assert d["baseline"]["n_trades"] == 503
assert len(d["experiment_2_fixed_tp"]) == 3
assert len(d["experiment_3_breach_only"]) == 3
print("Stage 4.4 JSON OK")
PY

# Verify whitespace
git diff --check -- ML/baseline/diagnose_stage4_4.py \
  docs/reports/2026-06-15-stage4_4-micro-check.md \
  MODULE_INDEX.md

# Wiki integrity
~/git/SoSimple/.venv/bin/python wiki/wiki.py verify
```

Expected:
- smoke tests PASS;
- diagnostic script exits 0;
- baseline PF≈1.015 (допуск ±0.001), n=503;
- JSON contains all required sections;
- `status == DIAGNOSTIC_ONLY`;
- 3 fixed TP cells in experiment_2, 3 breach-only cells in experiment_3;
- `git diff --check` has no whitespace errors;
- wiki verify OK.

## Acceptance Criteria

- Stage 4.4 report отвечает на три вопроса:
  1. Улучшает ли p=0.5 PF относительно p=0.4, и какой ценой (сколько oracle-плохих строк добавляется)?
  2. Уступает ли fav-based TP фиксированному TP при том же входном фильтре?
  3. Работает ли breach без fav-фильтра лучше или хуже baseline?
- Baseline воспроизводит Stage 4.2 (PF=1.015, n=503).
- Каждая ячейка имеет block bootstrap и permutation test.
- Все результаты помечены `DIAGNOSTIC_ONLY`.
- Ни одна ячейка не объявлена winner.
- Test не открыт.
- Search budget раскрыт.
- Новый модуль задокументирован и проиндексирован.

## После Выполнения

Если Stage 4.4 показывает, что fixed TP не хуже fav-based TP:
- Stage 5.0 Transformer может фокусироваться на breach-классификации + fav как фильтр входа (без использования fav как цены TP).

Если Stage 4.4 показывает, что breach-only entry + fixed TP существенно лучше baseline:
- Это гипотеза для Stage 4.5 (clean val_select/val_eval протокол с breach-only + fixed TP + trailing stop);
- fav-based TP может быть исключён из Stage 5.0 дизайна.

Если Stage 4.4 не показывает устойчивых улучшений ни в одном эксперименте:
- Подтверждает вывод Stage 4.3: проблема в качестве моделей, а не в порогах/TP-политике;
- Stage 5.0 Transformer остаётся приоритетным направлением без изменений дизайна.

В любом случае: следующий шаг — план Stage 5.0 Transformer для Fractal Stop (из `docs/audit/next.md`, Вектор A).
