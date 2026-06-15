# Stage 4.3 Diagnostic-Only Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking. Do not commit unless the user explicitly asks.

**Goal:** Выполнить Stage 4.3 `DIAGNOSTIC_ONLY` для Fractal Stop: понять, где теряется PF между Oracle и Stage 4.2, не выбирая нового winner и не открывая test.

**Architecture:** Один diagnostic runner строит сделки Stage 4.2 winner (`sell_H6_off05`, `p=0.4`, `min_fav=0.3`, `min_rr=1.0`, `tp_fraction=0.4`) и поверх них считает loss attribution, breach/fav buckets, 2D-карту, фактический RR и TP-policy comparison. Результат сохраняется в JSON и отчёт; любые найденные прибыльные зоны имеют статус `DIAGNOSTIC_ONLY`, потому что используются те же данные, где исторически был выбран Stage 4 winner.

**Tech Stack:** Python 3.10+, pandas, numpy, XGBoost, scikit-learn, pytest. Использовать `~/git/SoSimple/.venv/bin/python`.

---

## Source Of Truth

План реализует рекомендации из:

- `docs/audit/2026-06-14-stage4-brainstorm_result_codex.md`
- `docs/reports/2026-06-11-stage4-trade-xgboost.md`
- `ML/reports/stage4_2_diagnostic.json`

Не использовать `docs/audit/2026-06-14-stage4-brainstorm_result_deep.md` как управляющий документ для Stage 4.3. Там есть полезные факты, но часть идей относится к новой механике выхода.

## Жёсткие Границы

Stage 4.3:

- не открывает test;
- не выбирает нового winner;
- не меняет модель;
- не меняет train/val split;
- не запускает grid search торгового правила как candidate selection;
- не повышает verdict Stage 4;
- не доказывает прибыльность.

Разрешено:

- диагностировать, где текущая модель теряет PF;
- показать, есть ли на `val_eval` узкие зоны с лучшим PF;
- сформулировать гипотезы для отдельного Stage 5 или новой механики выхода.

Запрещено интерпретировать:

- лучшую bucket/2D/TP-policy ячейку как торговое правило;
- `atr_02` трейлинг как готовое исправление Stage 4;
- AUC→PF sensitivity как прогноз качества реальной будущей модели.

## Out Of Scope

Не входит в этот план:

- `breach_feature_ablation.py`;
- AUC→PF sensitivity через смешивание с истинными labels;
- Transformer Stage 5.0;
- трейлинг-стоп как новая execution-механика;
- MT4/tester parity;
- test/frozen evaluation.

Эти темы можно вынести в отдельные планы после Stage 4.3.

## Search Budget Disclosure

Отчёт Stage 4.3 обязан явно указать количество диагностических проверок:

- breach buckets: 4;
- fav buckets by `pred_fav`: минимум 5;
- fav buckets by `pred_fav / stop_val`: минимум 5;
- 2D map: 5 × 5 cumulative threshold cells;
- TP-policy variants: все перечисленные в Task 8.
- oracle deviation attribution: 4 model/oracle regimes + error categories from Task 9.

Любая ячейка с PF > 1.15 помечается как `hypothesis_only`, пока не проверена отдельным `val-select`/`val-eval` протоколом или permutation test, повторяющим процесс выбора.

## Файлы

| Файл | Действие | Назначение |
|---|---|---|
| `ML/baseline/diagnose_stage4_3.py` | Create | Единый diagnostic runner Stage 4.3 |
| `tests/test_diagnose_stage4_3.py` | Create | Unit-тесты метрик, bucket logic, TP-policy helpers |
| `ML/reports/stage4_3_diagnostics.json` | Generate | Structured artifact диагностики |
| `docs/reports/2026-06-15-stage4_3-diagnostics.md` | Create | Канонический отчёт Stage 4.3 |
| `MODULE_INDEX.md` | Modify | Добавить новый ML-модуль |
| `docs/ML/diagnose_stage4_3.py.md` | Create | Краткая module-level docs для runner |

Документационные файлы `CHANGELOG.md` и `CONTEXT_HANDOFF.md` обновлять только если пользователь явно закрывает этап или просит синхронизацию после получения результатов.

## Общая Реализация

`diagnose_stage4_3.py` должен переиспользовать инфраструктуру Stage 4.2:

- split: train `<=2016`, val_stop `2017-2018`, val_eval `>=2019`;
- early stopping: только `val_stop`;
- target: `sell_H6_off05`;
- feature profile breach: `base_raw_plus_time`;
- fav model: RF fav как в Stage 4.2;
- OHLC convention: OHLC=Bid;
- spread: canonical `0.20`;
- entry: Open следующего бара;
- exit: first-touch SL/TP/TIMEOUT, ambiguous bar = SL;
- block bootstrap: block size 15, seed fixed.

Главное требование: все метрики считать от одного и того же списка сделок и сохранять идентичные `trade_id`/`row_index` в debug records, чтобы можно было сверить bucket-агрегации с общим PF.

---

### Task 1: Unit Tests For Diagnostic Helpers

**Files:**
- Create: `tests/test_diagnose_stage4_3.py`
- Create: helper functions in `ML/baseline/diagnose_stage4_3.py`

- [ ] **Step 1: Добавить тест PF и yearly PF**

```python
def test_compute_trade_metrics_basic_pf_and_years():
    trades = [
        {"pnl_val": 1.0, "year": 2019, "exit": "TP"},
        {"pnl_val": -0.5, "year": 2019, "exit": "SL"},
        {"pnl_val": 0.2, "year": 2020, "exit": "TIMEOUT"},
        {"pnl_val": -0.3, "year": 2020, "exit": "SL"},
    ]
    out = compute_trade_metrics(trades)
    assert out["n_trades"] == 4
    assert out["pf"] == pytest.approx(1.5)
    assert out["yearly"]["2019"]["pf"] == pytest.approx(2.0)
```

- [ ] **Step 2: Добавить тест loss attribution**

```python
def test_loss_attribution_separates_exit_types_and_ambiguous_sl():
    trades = [
        {"pnl_val": 0.4, "exit": "TP", "ambiguous": 0},
        {"pnl_val": -1.0, "exit": "SL", "ambiguous": 0},
        {"pnl_val": -1.0, "exit": "SL", "ambiguous": 1},
        {"pnl_val": -0.2, "exit": "TIMEOUT", "ambiguous": 0},
    ]
    out = loss_attribution(trades)
    assert out["SL"]["n"] == 2
    assert out["SL"]["ambiguous_sl"] == 1
    assert out["SL"]["breach_fn_non_ambiguous"] == 1
    assert out["TIMEOUT"]["total_pnl"] == pytest.approx(-0.2)
```

Важно: не писать “все SL = breach-FN” как торговый вывод. SL означает, что стоп был пробит в симуляторе; ambiguous-SL может быть следствием конвенции порядка касаний внутри бара.

- [ ] **Step 3: Добавить тест фактического RR**

```python
def test_actual_rr_uses_tp_val_over_stop_val():
    trade = {"tp_val": 0.4, "stop_val": 1.0}
    assert actual_rr(trade) == pytest.approx(0.4)
```

- [ ] **Step 4: Добавить тест fixed TP policy**

```python
def test_fixed_tp_policy_atr_and_r_units():
    assert resolve_tp_val("fixed_atr", 0.5, pred_fav=2.0, stop_val=1.2) == pytest.approx(0.5)
    assert resolve_tp_val("fixed_r", 0.5, pred_fav=2.0, stop_val=1.2) == pytest.approx(0.6)
    assert resolve_tp_val("fav_fraction", 0.4, pred_fav=2.0, stop_val=1.2) == pytest.approx(0.8)
```

- [ ] **Step 5: Запустить failing tests**

Run:

```bash
~/git/SoSimple/.venv/bin/python -m pytest tests/test_diagnose_stage4_3.py -q
```

Expected: FAIL because helpers do not exist yet.

---

### Task 2: Diagnostic Runner Skeleton

**Files:**
- Create: `ML/baseline/diagnose_stage4_3.py`

- [ ] **Step 1: Создать file header**

Header должен описывать:

- входы: `DATA/Nero_XAUUSD_*_labeled.csv`, `DATA/XAUUSD_H1_OHLC.csv`;
- выход: `ML/reports/stage4_3_diagnostics.json`;
- статус: `DIAGNOSTIC_ONLY`;
- запрет: no test, no winner selection.

- [ ] **Step 2: Переиспользовать Stage 4.2 infrastructure**

Импортировать или аккуратно скопировать только необходимые функции из `ML/baseline/diagnose_stage4_gap.py`:

- `load_splits`;
- `profile_base_raw`;
- `profile_base_raw_plus_time`;
- `compute_entry_prices`;
- `parse_trade_fractal0`;
- `simulate_trades`;
- `train_xgb_breach`;
- `train_rf_fav`.

Если функция копируется, в комментарии указать source. Не менять поведение Stage 4.2 симулятора. Существующий `compute_trade_metrics` из Stage 4.2 не использовать как итоговый helper без изменений: он не возвращает yearly-разбивку.

- [ ] **Step 3: Написать новые helper-функции Stage 4.3**

Реализовать функции, которые тестируются в Task 1 и отсутствуют в Stage 4.2:

- `compute_trade_metrics(trades)`: расширенная Stage 4.3 версия, возвращает flat metrics и поле `yearly`;
- `compute_yearly_metrics(trades)`: отдельная функция `dict[str, metrics]`, которую вызывает `compute_trade_metrics`;
- `loss_attribution(trades)`;
- `actual_rr(trade)`;
- `resolve_tp_val(policy, value, pred_fav, stop_val)`.

Требование совместимости: если из Stage 4.2 нужен старый плоский расчёт, скопировать его под приватным именем, например `_compute_trade_metrics_flat()`, а публичная `compute_trade_metrics()` в `diagnose_stage4_3.py` должна соответствовать тестам Stage 4.3.

- [ ] **Step 4: Добавить CLI**

Минимальные параметры:

```bash
--train DATA/Nero_XAUUSD_train_labeled.csv
--val DATA/Nero_XAUUSD_validation_labeled.csv
--ohlc DATA/XAUUSD_H1_OHLC.csv
--output ML/reports/stage4_3_diagnostics.json
--spread 0.20
--seed 42
```

- [ ] **Step 5: Построить aligned trade frame**

Каждая сделка в `return_details=True` должна сохранять:

- `trade_id`;
- source `row_index`;
- `time`;
- `year`;
- `entry_price`;
- `stop_price`;
- `tp_price`;
- `tp_val`;
- `stop_val`;
- `actual_rr = tp_val / stop_val`;
- `pred_break`;
- `breach_flag_true`;
- `pred_fav`;
- `fav_val_true`;
- `fav_error = pred_fav - fav_val_true`;
- `exit`;
- `pnl_val`;
- `pnl_r`;
- `ambiguous`;
- `atr`.

`breach_flag_true` нельзя заменять SL-rate proxy.

- [ ] **Step 6: Пройти unit tests**

Run:

```bash
~/git/SoSimple/.venv/bin/python -m pytest tests/test_diagnose_stage4_3.py -q
```

Expected: PASS.

---

### Task 3: Loss Attribution And Baseline Sanity

**Files:**
- Modify: `ML/baseline/diagnose_stage4_3.py`

- [ ] **Step 1: Считать baseline metrics**

Сохранить:

- PF;
- gross profit/loss;
- trades/year;
- yearly PF;
- TP/SL/TIMEOUT counts;
- ambiguous count;
- win rate;
- avg win/loss in ATR;
- avg win/loss in R.

Ожидаемый sanity target: baseline должен быть близок к Stage 4.2: PF около `1.015`, `503` сделки. Допуск зафиксировать в отчёте, если точное число отличается из-за мелкой разницы реализации.

- [ ] **Step 2: Loss attribution**

Для `TP`, `SL`, `TIMEOUT` считать:

- `n`;
- `total_pnl`;
- `mean_pnl`;
- `gross_profit`;
- `gross_loss`;
- `pct_of_total_gross_loss`;
- `pct_of_total_gross_profit`.

Для `SL` дополнительно:

- `ambiguous_sl`;
- `non_ambiguous_sl`;
- `breach_flag_true_rate`.

- [ ] **Step 3: Yearly loss attribution**

Сохранить ту же декомпозицию по годам. Это нужно, чтобы не принять один хороший год за общий вывод.

---

### Task 4: Breach Buckets

**Files:**
- Modify: `ML/baseline/diagnose_stage4_3.py`

- [ ] **Step 1: Bucket ranges**

Использовать:

```text
[0.00, 0.10)
[0.10, 0.20)
[0.20, 0.30)
[0.30, 0.40)
```

Bucket `[0.40, 0.50)` не включать для списка уже открытых сделок: Stage 4.2 winner входит только при `predict_break < 0.4`, поэтому этот диапазон будет заведомо пустым. Если в будущем нужен анализ всех eligible строк до входного фильтра, это отдельная таблица, не trade bucket.

- [ ] **Step 2: Метрики на bucket**

Для каждой корзины:

- `n`;
- `pf`;
- `bs_p05_block`;
- `trades_per_year`;
- yearly PF;
- actual breach rate from `breach_flag_true`;
- TP/SL/TIMEOUT percentages;
- avg `pred_fav`;
- avg `stop_val`;
- avg actual RR.

Если `n < 30`, пометить bucket как `low_n`.

- [ ] **Step 3: Проверка интерпретации**

Не требовать монотонного PF как PASS. PF может быть немонотонным. Обязательная проверка: actual breach rate должен в среднем расти с `predict_break`; если нет, breach-рейтинг слабый или плохо откалиброван.

---

### Task 5: Fav Buckets And Monotonicity

**Files:**
- Modify: `ML/baseline/diagnose_stage4_3.py`

- [ ] **Step 1: Buckets by `pred_fav`**

Использовать квантильные корзины по сделкам, чтобы избежать пустых диапазонов:

```text
q0-q20, q20-q40, q40-q60, q60-q80, q80-q100
```

- [ ] **Step 2: Buckets by `pred_fav / stop_val`**

Использовать фиксированные корзины:

```text
[1.0, 1.3)
[1.3, 1.5)
[1.5, 2.0)
[2.0, 3.0)
[3.0, +inf)
```

- [ ] **Step 3: Метрики**

Для каждой корзины:

- `n`;
- PF;
- BS_p05 block;
- trades/year;
- yearly PF;
- mean true fav;
- mean predicted fav;
- mean fav error;
- TP/SL/TIMEOUT percentages;
- actual RR distribution.

- [ ] **Step 4: Monotonicity summary**

Сохранить:

- Spearman correlation between `pred_fav` and `fav_val_true`;
- Spearman correlation between `pred_fav / stop_val` and `pnl_val`;
- whether top bucket improves PF vs bottom bucket.

Если fav работает как фильтр, но не как TP-price, это должно быть явно отмечено в отчёте.

---

### Task 6: 2D Map `predict_break × pred_fav/stop_val`

**Files:**
- Modify: `ML/baseline/diagnose_stage4_3.py`

- [ ] **Step 1: Grid**

Rows:

```text
predict_break < 0.15
predict_break < 0.20
predict_break < 0.25
predict_break < 0.30
predict_break < 0.40
```

Columns:

```text
pred_fav / stop_val >= 0.7
>= 1.0
>= 1.3
>= 1.5
>= 2.0
```

Такой формат является cumulative threshold map, а не mutually exclusive histogram. Он отвечает на вопрос: “какой фильтр мог бы быть гипотезой”.

- [ ] **Step 2: Cell metrics**

Каждая строка и каждая колонка — независимый cumulative-фильтр. Одна и та же сделка может попасть в несколько строк и несколько колонок. Например, сделка с `predict_break=0.18` и `pred_fav/stop_val=2.5` попадает во все строки с порогом выше `0.18` и во все колонки `>=0.7`, `>=1.0`, `>=1.3`, `>=1.5`, `>=2.0`. Это не mutually exclusive binning.

В каждой ячейке:

- `n`;
- PF;
- BS_p05 block;
- trades/year;
- yearly PF;
- TP/SL/TIMEOUT;
- actual breach rate;
- avg actual RR.

В JSON для 2D-map добавить:

```json
"cumulative": true
```

- [ ] **Step 3: Hypothesis flags**

Ячейка получает `hypothesis_candidate=true`, если:

- PF > 1.15;
- BS_p05 close to 1.0 or above;
- trades/year >= 30;
- no single year contributes more than 60% of gross profit.

Даже такая ячейка остаётся `DIAGNOSTIC_ONLY`.

---

### Task 7: Actual RR Diagnostics

**Files:**
- Modify: `ML/baseline/diagnose_stage4_3.py`

- [ ] **Step 1: Считать actual RR**

Для каждой сделки:

```text
actual_rr = tp_val / stop_val
```

При текущем Stage 4.2 winner минимальный фактический RR может быть около `0.4`, потому что:

```text
min_rr = pred_fav / stop_val >= 1.0
tp_val = pred_fav * 0.4
```

- [ ] **Step 2: RR buckets**

Считать PF и win/loss по:

```text
[0.0R, 0.4R)
[0.4R, 0.6R)
[0.6R, 0.8R)
[0.8R, 1.0R)
[1.0R, +inf)
```

- [ ] **Step 3: Report fields**

Сохранить:

- mean/median actual RR;
- p05/p95 actual RR;
- avg win in R;
- avg loss in R;
- required win rate for PF=1 at observed avg win/loss.

---

### Task 8: TP Policy Comparison Without New Winner Selection

**Files:**
- Modify: `ML/baseline/diagnose_stage4_3.py`

- [ ] **Step 1: Реализовать TP policy helper**

Поддержать:

```text
fav_fraction: tp_val = pred_fav * fraction
fixed_atr:    tp_val = constant ATR value
fixed_r:      tp_val = stop_val * R_multiple
```

- [ ] **Step 2: Сравнить policies**

Сравнить:

- current: `fav_fraction=0.4`;
- fixed ATR: `0.3`, `0.5`, `0.7`, `1.0`;
- fixed R: `0.3R`, `0.5R`, `0.7R`, `1.0R`, `1.5R`, `2.0R`;
- breach-only entry + fixed TP: убрать `min_fav` и `min_rr`, оставить `predict_break < 0.4`;
- breach + fav-filter entry + fixed TP: оставить `min_fav=0.3`, `min_rr=1.0`, но TP не зависит от fav.

- [ ] **Step 3: Метрики**

Для каждой policy:

- `n`;
- PF;
- BS_p05 block;
- yearly PF;
- trades/year;
- TP/SL/TIMEOUT;
- avg win/loss ATR;
- avg win/loss R;
- actual RR distribution.

- [ ] **Step 4: Interpretation guard**

Добавить в JSON:

```json
"tp_policy_comparison_status": "DIAGNOSTIC_ONLY_not_winner_selection"
```

Если fixed TP лучше текущего TP, вывод должен звучать как гипотеза: fav может быть плохим регулятором цены TP.

---

### Task 9: Oracle Deviation Attribution

**Files:**
- Modify: `ML/baseline/diagnose_stage4_3.py`

Цель: статистически разложить, какие отклонения модельных предсказаний от oracle labels сильнее всего связаны с потерей PF. Этот блок остаётся `DIAGNOSTIC_ONLY`: oracle labels являются будущей информацией и не могут быть торговыми признаками.

- [ ] **Step 1: Построить единую eligible universe**

Создать набор строк до модельных входных фильтров, но после базовой исполнимости сделки:

- правильная сторона `fractal0` для `sell_H6_off05`;
- валидный `entry_price`;
- валидный `stop_val`;
- валидный `breach_flag_true`;
- валидный `fav_val_true`;
- валидный `pred_break`;
- валидный `pred_fav`;
- OHLC-окно H6 доступно.

Каждая строка получает стабильный `candidate_id`. Все model/oracle regimes должны использовать один и тот же universe, чтобы `delta_pnl_val` был сопоставим.

- [ ] **Step 2: Сравнить 4 model/oracle regimes**

Посчитать сделки и метрики для режимов:

| Regime | Breach input | Fav/TP input | Что показывает |
|---|---|---|---|
| `model_breach_model_fav` | `pred_break` | `pred_fav` | текущий Stage 4.2 baseline |
| `oracle_breach_model_fav` | `breach_flag_true` | `pred_fav` | потери из-за breach-фильтра |
| `model_breach_oracle_fav` | `pred_break` | `fav_val_true` | потери из-за fav/TP |
| `oracle_breach_oracle_fav` | `breach_flag_true` | `fav_val_true` | диагностический потолок текущего execution rule |

Oracle breach rule:

```text
enter_breach_oracle = breach_flag_true == 0
```

Oracle fav rule:

```text
fav_for_filters = fav_val_true
tp_val = fav_val_true * tp_fraction
```

Сохранять для каждого режима:

- PF;
- BS_p05 block;
- trades/year;
- yearly PF;
- TP/SL/TIMEOUT;
- gross profit/loss;
- avg win/loss in ATR and R.

- [ ] **Step 3: Ошибки входа относительно oracle**

Для каждой candidate-row классифицировать:

- `entered_model_and_oracle`: модель вошла, oracle breach тоже разрешает;
- `entered_model_but_oracle_breach_blocks`: модель вошла, но oracle breach говорит, что стоп будет пробит;
- `missed_by_model_but_oracle_breach_allows`: модель не вошла, но oracle breach разрешает;
- `blocked_by_both`: модель и oracle breach не входят.

Для каждой категории считать:

- `n`;
- долю от eligible universe;
- simulated PnL при model TP, если сделку принудительно оценить;
- yearly split;
- block bootstrap CI для среднего `pnl_val`.

Важно: `missed_by_model_but_oracle_breach_allows` не является “упущенной прибылью” автоматически, пока fav/TP и издержки не проверены; это diagnostic category.

- [ ] **Step 4: Ошибки fav относительно oracle**

Для строк, где вход разрешён моделью или oracle breach, считать:

- `fav_error = pred_fav - fav_val_true`;
- `tp_error_val = pred_fav * tp_fraction - fav_val_true * tp_fraction`;
- `rr_filter_error`: модельный `pred_fav / stop_val` проходит `min_rr`, а oracle `fav_val_true / stop_val` не проходит, или наоборот;
- `min_fav_error`: модельный `pred_fav` проходит `min_fav`, а oracle `fav_val_true` не проходит, или наоборот.

Категории:

- `fav_overpredict_tp_too_far`;
- `fav_underpredict_tp_too_close`;
- `model_fav_false_accept`;
- `model_fav_false_reject`;
- `fav_near_oracle`.

Для каждой категории считать:

- `n`;
- mean/median `fav_error`;
- PF;
- yearly PF;
- TP/SL/TIMEOUT;
- delta vs baseline PnL where comparable.

- [ ] **Step 5: Delta attribution summary**

Сохранить итоговую таблицу:

```json
"oracle_deviation_attribution": {
  "regimes": {},
  "breach_entry_error_categories": [],
  "fav_error_categories": [],
  "delta_summary": {
    "pf_baseline": 0.0,
    "pf_oracle_breach_model_fav": 0.0,
    "pf_model_breach_oracle_fav": 0.0,
    "pf_oracle_breach_oracle_fav": 0.0,
    "largest_observed_gap": ""
  },
  "status": "DIAGNOSTIC_ONLY_oracle_labels_are_future"
}
```

Интерпретация должна быть осторожной: если `model_breach_oracle_fav` сильно лучше baseline, fav/TP является главным подозреваемым; если `oracle_breach_model_fav` сильно лучше baseline, breach-фильтр является главным подозреваемым. Если оба лучше, но `oracle_breach_oracle_fav` намного выше обоих, проблема во взаимодействии breach и fav.

---

### Task 10: Block Bootstrap And Concentration Helpers

**Files:**
- Modify: `ML/baseline/diagnose_stage4_3.py`
- Test: `tests/test_diagnose_stage4_3.py`

- [ ] **Step 1: Block bootstrap**

Реализовать block bootstrap по последовательности сделок:

- block size: 15;
- iterations: 500 by default;
- seed fixed;
- output: median, p05, p95.

- [ ] **Step 2: Concentration**

Для любой bucket/policy считать:

- gross profit by year;
- max year profit share;
- `profit_concentration_warning=true`, если один год даёт >60% gross profit.

- [ ] **Step 3: Tests**

Добавить тесты на:

- block bootstrap возвращает p05/median/p95;
- concentration flag срабатывает при одном доминирующем годе.

---

### Task 11: JSON Schema And Report

**Files:**
- Generate: `ML/reports/stage4_3_diagnostics.json`
- Create: `docs/reports/2026-06-15-stage4_3-diagnostics.md`

- [ ] **Step 1: JSON top-level**

JSON должен содержать:

```json
{
  "status": "DIAGNOSTIC_ONLY",
  "source": "docs/audit/2026-06-14-stage4-brainstorm_result_codex.md",
  "config": {},
  "search_budget": {},
  "baseline_metrics": {},
  "loss_attribution": {},
  "breach_buckets": [],
  "fav_buckets_pred_fav": [],
  "fav_buckets_pred_fav_over_stop": [],
  "breach_fav_2d_map": {},
  "actual_rr": {},
  "tp_policy_comparison": [],
  "oracle_deviation_attribution": {},
  "interpretation_guards": []
}
```

- [ ] **Step 2: Report sections**

Отчёт должен содержать:

- Context;
- Methodology and split;
- Search budget disclosure;
- Baseline sanity check;
- Loss attribution;
- Breach bucket results;
- Fav bucket results;
- 2D map;
- Actual RR;
- TP policy comparison;
- Oracle deviation attribution;
- What can and cannot be concluded;
- Next hypotheses;
- Related artifacts.

- [ ] **Step 3: Explicit non-conclusions**

В отчёте обязательно написать:

- Stage 4.3 не выбирает winner;
- test не открыт;
- лучшая ячейка не является торговым правилом;
- трейлинг не проверялся как Stage 4.3 candidate;
- Stage 4 verdict не меняется.

---

### Task 12: Docs And Index

**Files:**
- Create: `docs/ML/diagnose_stage4_3.py.md`
- Modify: `MODULE_INDEX.md`
- Generate: `wiki/REPO_integrity.md`

- [ ] **Step 1: Module docs**

Создать короткую страницу:

- назначение;
- входы;
- выходы;
- команда запуска;
- статус `DIAGNOSTIC_ONLY`;
- ограничения интерпретации.

- [ ] **Step 2: MODULE_INDEX**

Добавить `ML/baseline/diagnose_stage4_3.py` в раздел ML.

- [ ] **Step 3: Wiki integrity**

Run:

```bash
~/git/SoSimple/.venv/bin/python wiki/wiki.py generate
~/git/SoSimple/.venv/bin/python wiki/wiki.py verify
```

- [ ] **Step 4: RAG reindex**

Run:

```text
knowledge-rag reindex_documents(force=True)
```

---

## Верификация

Run:

```bash
~/git/SoSimple/.venv/bin/python -m pytest tests/test_diagnose_stage4_3.py -q
~/git/SoSimple/.venv/bin/python -m ML.baseline.diagnose_stage4_3 --output ML/reports/stage4_3_diagnostics.json
~/git/SoSimple/.venv/bin/python - <<'PY'
import json
from pathlib import Path

p = Path("ML/reports/stage4_3_diagnostics.json")
d = json.loads(p.read_text())
required = [
    "status",
    "search_budget",
    "baseline_metrics",
    "loss_attribution",
    "breach_buckets",
    "fav_buckets_pred_fav",
    "fav_buckets_pred_fav_over_stop",
    "breach_fav_2d_map",
    "actual_rr",
    "tp_policy_comparison",
    "oracle_deviation_attribution",
    "interpretation_guards",
]
for key in required:
    assert key in d, f"missing {key}"
assert d["status"] == "DIAGNOSTIC_ONLY"
assert d["baseline_metrics"]["n_trades"] > 0
print("Stage 4.3 JSON OK")
PY
git diff --check -- ML/baseline/diagnose_stage4_3.py tests/test_diagnose_stage4_3.py docs/reports/2026-06-15-stage4_3-diagnostics.md docs/ML/diagnose_stage4_3.py.md MODULE_INDEX.md wiki/REPO_integrity.md
~/git/SoSimple/.venv/bin/python wiki/wiki.py verify
```

Expected:

- pytest PASS;
- diagnostic script exits 0;
- JSON contains all required sections;
- `status == DIAGNOSTIC_ONLY`;
- `git diff --check` has no whitespace errors;
- wiki verify OK.

## Acceptance Criteria

- Stage 4.3 report answers: losses mostly come from breach errors, fav/TP errors, actual RR, or fixed TP design.
- Every promising condition is marked `DIAGNOSTIC_ONLY`.
- No test data used.
- No new winner selected.
- Search budget disclosed.
- Oracle deviation attribution explains which model-vs-oracle deviations are most associated with PF loss.
- Baseline sanity matches Stage 4.2 closely enough to trust diagnostics.
- New module is documented and indexed.

## После Выполнения

Если Stage 4.3 показывает устойчивую diagnostic zone:

- write a new separate plan for a clean `val-select`/`val-eval` candidate cycle;
- do not reuse Stage 4.3 as frozen selection.

Если Stage 4.3 не показывает устойчивой зоны:

- close fixed `breach -> fav -> fixed TP/SL` Stage 4 branch;
- proceed to Stage 5.0 model layer or a separate trailing/partial-exit research plan.
