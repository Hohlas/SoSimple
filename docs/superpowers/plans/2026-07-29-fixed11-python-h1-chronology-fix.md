# Fixed11 Python H1 Chronology Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Исправить Python-симуляцию fixed11 так, чтобы ML-exit признаки были доступны строго на момент решения, а внутри H1-бара симулятор восстанавливал единый порядок событий `limit fill -> SL/TP/MLClose/timeout` по M5 и не терял фактическое время исполнения лимитки.

**Architecture:** Сначала исправляется контракт ML-exit признаков: input-признаки должны описывать только уже известное состояние открытой позиции, а будущие поля остаются только target/diagnostic. Для текущего H1-only ML-exit контракта строки `bars_since_fill=0` не являются рабочими ML-решениями: без отдельного post-fill decision timestamp их нужно исключить из train/score rows или оставить только как diagnostic rows с `ml_exit_eligible=False`. Затем H1 остаётся источником `signal_time`, split и ML-решений, а M5 используется только после H1-сигнала как execution-уточнение: найти первый M5-блок, где лимитка реально могла исполниться, и затем проверять только события, которые могли произойти после этого fill. Вход и выход в одном H1-баре разрешены, если порядок внутри часа доказан M5; старые locked-test артефакты не перезаписываются, новый контракт пишется отдельным output-prefix и получает максимум `DIAGNOSTIC_ONLY`, пока не пройдёт отдельная freeze/parity цепочка.

**Tech Stack:** `./.venv/bin/python`, pandas, pytest, CSV/JSON, `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, `docs/reports/`.

## Global Constraints

- Работать на текущей ветке, не делать `git push` без явной просьбы пользователя.
- Не запускать полный suite `./.venv/bin/python -m pytest tests/ -q`.
- Использовать только точечные проверки: `tests/test_fractal0_entry_exit_grid.py` и `tests/test_fractal0_fixed11_rich_entry_locked_test.py`, плюс команды rerun из плана.
- Не менять retained rules, cutoffs, profiles, models, targets, filters, stop policy, entry rule, exit rule, spread или MQL4-код в этом плане.
- H1 остаётся source of truth для признаков, split, `signal_time`, `decision_time` и обучения.
- M5 нельзя использовать как ML-признак, фильтр выбора сделок, источник нового winner или способ подбора threshold.
- Новый execution contract должен быть явно отделён от старого: старые artifacts `ML/reports/fractal0_fixed11_rich_entry_locked_test*` не перезаписывать.
- Новый output-prefix для диагностического rerun: `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix`.
- Максимальный вердикт результата этого плана: `DIAGNOSTIC_ONLY`, потому что меняются ML-exit feature contract и execution convention после уже открытого locked_test.
- Неизвестное, которое план не может закрыть сам: точный live bid/ask источник и полная эквивалентность M5 tester-history реальному исполнению. Это должно остаться limitation в отчёте.

---

## Root Cause

Проблема не в самом факте `fill_time == exit_time` на H1. Это нормальная ситуация, если лимитка исполнилась, например, в `10:10`, а стоп или `MLClose` сработал в `10:15` внутри того же часа.

Подтверждённые причины старой ошибки в Python-симуляторе:

- `ML/baseline/benchmark_fractal0_entry_exit_grid.py::build_entry_rows(...)` ищет исполнение лимитки по H1 OHLC и сохраняет только H1 `fill_time`;
- `ML/baseline/benchmark_fractal0_entry_exit_grid.py::simulate_trade(...)` начинает жизнь сделки с `fill_index` H1-бара и не знает фактическое M5-время входа;
- `ML/baseline/benchmark_fractal0_entry_exit_grid.py::_resolve_same_bar_with_execution_ohlc(...)` использует M5 только для спорного порядка TP/SL, но не для времени fill и не для общего порядка событий внутри H1.
- `ML/baseline/benchmark_fractal0_entry_exit_grid.py::build_exit_decision_rows(...)` строит первую строку ML-exit с `idx = fill_index`, то есть `bars_since_fill = 0`, и при этом заполняет position-state признаки.

Следствие: симулятор знает “в каком H1-баре была исполнена лимитка”, но не знает “в какой M5-свече внутри этого H1-бара”. Поэтому он может считать сделку существующей с начала H1-бара и обработать выход, который фактически был раньше M5-fill.

Отдельный критичный риск: признаки ML-exit с суффиксом `_before_decision` должны быть известны до момента решения. При `bars_since_fill = 0` H1-бар fill ещё не закрыт в момент внутрибаравого исполнения лимитки. Поэтому `unrealized_pnl_r_before_decision`, `max_favorable_r_before_decision` и `max_adverse_r_before_decision` не имеют честного рабочего значения для ML-решения в начале этого же H1-бара. Нулевые значения лучше, чем использование закрытого H1-бара, но рабочий контракт этого плана строже: без отдельного post-fill decision timestamp строки `bars_since_fill=0` должны быть исключены из ML-exit train/score rows или оставлены только как diagnostic rows с `ml_exit_eligible=False`; `simulate_trade(...)` не должен использовать ML score для `i=0`.

Текущий код также смешивает названия признаков и будущих полей:

- `future_favorable_r_3` — максимальное благоприятное движение за следующие до 3 H1-бара после `decision_time`; это будущая величина, она может быть target/diagnostic, но не input-признак.
- `future_adverse_r_3` — максимальное неблагоприятное движение за следующие до 3 H1-бара; это будущая величина, она может быть target/diagnostic, но не input-признак.
- `hold_3_pnl_r` — результат удержания позиции до конца окна до 3 H1-баров; это будущий исход, он может быть target/diagnostic, но не input-признак.
- `close_now_pnl_r` в текущем коде звучит как “известно сейчас”, но при решении на H1-open закрытие текущего H1-бара ещё неизвестно. Если поле остаётся для target construction, его роль должна быть явно записана как `target_or_diagnostic_only`; предпочтительное новое имя в артефактах/отчёте — `decision_bar_close_pnl_r_for_target`.
- Любое поле, рассчитанное из этих величин или из будущих `high/low/close`, запрещено использовать как input ML-exit.

Для каждого exit decision должен быть согласован единый порядок:

```text
feature_time <= decision_time <= execution_time
```

Это означает:

- признаки берутся только из уже известных баров;
- ML-решение имеет понятный момент принятия;
- закрытие сделки происходит не раньше момента, когда это решение могло быть принято.

Текущий код требует отдельной проверки, потому что `build_exit_decision_rows(...)` пишет `first_exit_execution_time = idx + 1`, а `simulate_trade(...)` при `ML_CLOSE` закрывает по `bar["close"]` текущего `idx`. План должен привести эти два места к одному контракту. Важно: `idx + 1` означает первый исполнимый момент после того, как решение по закрытому H1-бару `idx` стало известно. В live это не ожидание ещё одного полного часа после появления сигнала, а немедленное закрытие на текущем рынке после расчёта ML-сигнала; в H1-бэктесте ближайшее приближение этого момента — open следующего H1-бара.

Исполнитель обязан сначала проверить и исправить feature contract ML-exit. Если окажется, что `max_favorable_r_before_decision` или `max_adverse_r_before_decision` фактически считаются из будущего окна, их нужно либо пересчитать только по прошлым барам после fill, либо убрать из `EXIT_FEATURE_COLUMNS_BASE`. Нельзя переходить к прибыльному rerun, пока этот контракт не имеет `PASS` или явного `DIAGNOSTIC_ONLY`.

Исправление должно устранять именно потерю внутрибаравой хронологии:

```text
H1 signal -> first eligible H1 bar -> first M5 limit touch -> events at/after that M5 time only
```

Запрещено исправлять это только отдельным симптомным условием вида “если ML-close раньше fill, пропустить”. Такой guard допустим как следствие общей модели порядка событий, но не как основное исправление.

---

## Methodology Map

- `docs/methodology/README.md`: если момент торгового решения или execution contract не доказан, результат не выше `DIAGNOSTIC_ONLY`.
- `docs/methodology/01-raw-data-inventory.md`: H1/M5 source, CSV contract, provider, timezone, price convention и статус M5 как `execution_ordering_only`.
- `docs/methodology/03-feature-contract-leakage.md`: зафиксировать `decision_time`; не допустить, чтобы M5 стал feature source или candidate filter.
- `docs/methodology/06-temporal-split.md`: old locked_test нельзя использовать для нового выбора; новый rerun только диагностический.
- `docs/methodology/10-frozen-test-oos.md`: смена `entry_price`, ML-exit feature contract, fill policy или execution convention после freeze понижает статус до `DIAGNOSTIC_ONLY` или требует нового цикла.
- `docs/methodology/12-backtest-costs.md`: симулятор сделок должен иметь синтетические тесты на edge cases; M5 допустим только для порядка исполнения внутри H1.
- `docs/methodology/13-export-mt4-parity.md`: Python fixed contract должен быть затем сверяем с MT4 по `signal_time + direction`, open/fill/close reasons и missing opens.
- `docs/methodology/16-reporting-audit.md`: отчёт обязан содержать команды, paths, hashes, invalidated assumptions, limitations, raw rows/signals/trades и запреты интерпретации.

---

### Task 0: Audit And Fix ML-Exit Feature Contract

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Modify: `tests/test_fractal0_entry_exit_grid.py`
- Read: `docs/methodology/03-feature-contract-leakage.md`

**Interfaces:**
- Consumes: current `EXIT_FEATURE_COLUMNS_BASE`, `build_exit_decision_rows(...)`, `build_exit_targets(...)`, `exit_feature_columns(...)`.
- Produces:
  - ML-exit input features that are available at `decision_time`;
  - explicit separation between future target fields and input fields;
  - tests proving `bars_since_fill=0` is not a working ML-exit decision under the current H1-only timestamp contract.

**Applicable Methodology:**
- `docs/methodology/03-feature-contract-leakage.md`: target/future-derived fields must not enter model input; every feature needs a known availability moment.
- `docs/methodology/12-backtest-costs.md`: backtest decisions must match data available at the simulated decision moment.

**Mandatory Checks:**
- `future_favorable_r_3`, `future_adverse_r_3`, `hold_3_pnl_r`, `close_now_pnl_r` and every target column are absent from `exit_feature_columns(...)`.
- `max_favorable_r_before_decision` and `max_adverse_r_before_decision` are not computed from `idx+1:idx+4` future bars.
- At `bars_since_fill=0`, if no post-fill decision timestamp exists yet, the row must not be used for ML-exit train/score. Preferred implementation: do not emit `bars_since_fill=0` rows from `build_exit_decision_rows(...)`; acceptable diagnostic alternative: emit them with `ml_exit_eligible=False` and filter them before train/score/map.
- `_score_map_for_entries(...)` must not create key `0` for the current contract.
- `simulate_trade(...)` must not use ML score for `i=0`.
- ML-close timing must satisfy `feature_time <= decision_time <= execution_time`. If `build_exit_decision_rows(...)` says `first_exit_execution_time = idx + 1`, then `simulate_trade(...)` cannot close that ML decision on current `idx` close. This is immediate execution after the signal becomes available, represented in H1 OHLC as next-bar open.
- If a field cannot be proven live-safe at `decision_time`, remove it from `EXIT_FEATURE_COLUMNS_BASE` or mark the rerun `DIAGNOSTIC_ONLY`; do not silently keep it as input.

**Completion Criterion:**
- Targeted tests pass and the ML-exit feature contract is explicit: future fields are targets/diagnostics only, input fields are available at the simulated decision time, and `bars_since_fill=0` cannot drive ML-close.

- [ ] **Step 1: Add test that future-derived columns are not ML-exit inputs**

Add this test near `test_exit_features_do_not_include_future_or_target_columns` in `tests/test_fractal0_entry_exit_grid.py`:

```python
def test_exit_features_exclude_future_derived_decision_fields():
    cols = set(runner.exit_feature_columns("M1_frozen_movement_top5"))

    forbidden = {
        "future_favorable_r_3",
        "future_adverse_r_3",
        "hold_3_pnl_r",
        "close_now_pnl_r",
        "target_exit_opposite_any",
        "target_exit_opposite_strong",
        "target_exit_hold_close",
        "target_exit_movement_exhaustion",
    }

    assert cols.isdisjoint(forbidden)
```

- [ ] **Step 2: Add failing test that `bars_since_fill=0` is not emitted as a working ML-exit row**

Add this test after Step 1:

```python
def test_exit_decision_rows_start_after_fill_bar_without_post_fill_decision_timestamp():
    trades = pd.DataFrame(
        [
            {
                "position_id": "p1",
                "side": "BUY",
                "fill_index": 0,
                "fill_time": pd.Timestamp("2021-01-01 10:00"),
                "entry_effective_price": 100.0,
                "r_value": 1.0,
                "ATR": 2.0,
            }
        ]
    )
    bars = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00", "2021-01-01 12:00", "2021-01-01 13:00"]),
            "open": [100.0, 100.0, 100.0, 100.0],
            "high": [105.0, 101.0, 101.0, 101.0],
            "low": [95.0, 99.0, 99.0, 99.0],
            "close": [104.0, 100.0, 100.0, 100.0],
        }
    )

    decisions = runner.build_exit_decision_rows(trades, bars)

    assert 0 not in set(decisions["bars_since_fill"])
    first = decisions.iloc[0]
    assert first["bars_since_fill"] == 1
    assert first["decision_time"] == pd.Timestamp("2021-01-01 11:00")
    assert first["first_exit_execution_time"] == pd.Timestamp("2021-01-01 12:00")
```

This test encodes the rule in plain terms: at the fill H1 timestamp, without a separate post-fill decision timestamp, there is no honest working ML-exit decision yet. The first ML-exit decision row starts only after the fill H1 bar has completed.

- [ ] **Step 3: Add failing test that score map cannot contain key 0**

Add this test after Step 2:

```python
def test_score_map_excludes_bars_since_fill_zero():
    entries = pd.DataFrame(
        [
            {
                "position_id": "p1",
                "filled": True,
                "side": "BUY",
                "fill_index": 0,
            }
        ]
    )
    scored_decisions = pd.DataFrame(
        [
            {
                "position_id": "p1",
                "bars_since_fill": 0,
                "ml_exit_eligible": False,
                "score_target_exit_opposite_any_M0_no_mask": 0.99,
            },
            {
                "position_id": "p1",
                "bars_since_fill": 1,
                "ml_exit_eligible": True,
                "score_target_exit_opposite_any_M0_no_mask": 0.75,
            },
        ]
    )

    score_map = runner._score_map_for_entries(
        entries,
        pd.DataFrame(),
        scored_decisions,
        {"family": "ml_opposite_any"},
        "M0_no_mask",
    )

    assert score_map["p1"] == {1: 0.75}
```

- [ ] **Step 4: Run the new feature-contract tests and confirm expected failure**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_entry_exit_grid.py::test_exit_features_exclude_future_derived_decision_fields \
  tests/test_fractal0_entry_exit_grid.py::test_exit_decision_rows_start_after_fill_bar_without_post_fill_decision_timestamp \
  tests/test_fractal0_entry_exit_grid.py::test_score_map_excludes_bars_since_fill_zero \
  -q
```

Expected:

```text
At least test_exit_decision_rows_start_after_fill_bar_without_post_fill_decision_timestamp and test_score_map_excludes_bars_since_fill_zero fail against current code, because build_exit_decision_rows currently emits bars_since_fill=0 and _score_map_for_entries currently keeps key 0.
```

- [ ] **Step 5: Fix `build_exit_decision_rows(...)` so working ML-exit rows start after fill H1**

In `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, keep future fields for target construction, but emit only working rows that can satisfy the timing contract.

Change the loop start from:

```python
        for idx in range(fill, last_decision):
```

to:

```python
        for idx in range(fill + 1, last_decision):
```

Inside the loop compute input features from already elapsed bars only. Because the first working row is `idx = fill + 1`, the fill H1 bar is not used as a position-state feature source. The current decision bar `idx` is allowed only under this explicit contract: decision is made after H1 bar `idx` is complete, and execution is no earlier than H1 bar `idx + 1`.

```python
            bars_since_fill = idx - fill
            known_start = fill + 1
            known_end = idx + 1
            close_now = _pnl_r(side, entry_price, closes[idx], r_value)
            if side == "BUY":
                favorable_before = (float(np.nanmax(highs[known_start:known_end])) - entry_price) / r_value
                adverse_before = (entry_price - float(np.nanmin(lows[known_start:known_end]))) / r_value
            else:
                favorable_before = (entry_price - float(np.nanmin(lows[known_start:known_end]))) / r_value
                adverse_before = (float(np.nanmax(highs[known_start:known_end])) - entry_price) / r_value
            favorable_before = max(0.0, float(favorable_before))
            adverse_before = max(0.0, float(adverse_before))
```

Keep target/diagnostic future fields separate:

```python
            future_start = idx + 1
            future_end = min(idx + 4, len(ohlc))
```

When appending the row, use:

```python
                    "bars_since_fill": bars_since_fill,
                    "ml_exit_eligible": True,
                    "unrealized_pnl_r_before_decision": close_now,
                    "max_favorable_r_before_decision": favorable_before,
                    "max_adverse_r_before_decision": adverse_before,
```

Do not remove `future_favorable_r_3`, `future_adverse_r_3`, `close_now_pnl_r` or `hold_3_pnl_r` from decision rows; they are still needed for `build_exit_targets(...)`. The rule is that they must not be returned by `exit_feature_columns(...)`.

If touching artifact column names is low-risk for this runner, add a duplicate diagnostic alias:

```python
                    "decision_bar_close_pnl_r_for_target": close_now,
```

Then keep `close_now_pnl_r` only for backward compatibility with `build_exit_targets(...)` and document its role as target/diagnostic, not input.

- [ ] **Step 6: Filter ineligible score rows before building score maps**

In `_score_map_for_entries(...)`, before grouping, filter scored decisions:

```python
    eligible = scored_decisions.copy()
    if "ml_exit_eligible" in eligible.columns:
        eligible = eligible.loc[eligible["ml_exit_eligible"].astype(bool)].copy()
    eligible = eligible.loc[pd.to_numeric(eligible["bars_since_fill"], errors="coerce") > 0].copy()
```

Then change:

```python
    for position_id, group in scored_decisions.groupby("position_id"):
```

to:

```python
    for position_id, group in eligible.groupby("position_id"):
```

- [ ] **Step 7: Run feature-contract tests**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_entry_exit_grid.py::test_exit_features_exclude_future_derived_decision_fields \
  tests/test_fractal0_entry_exit_grid.py::test_exit_decision_rows_start_after_fill_bar_without_post_fill_decision_timestamp \
  tests/test_fractal0_entry_exit_grid.py::test_score_map_excludes_bars_since_fill_zero \
  tests/test_fractal0_entry_exit_grid.py::test_exit_features_do_not_include_future_or_target_columns \
  -q
```

Expected:

```text
4 passed
```

- [ ] **Step 8: Record the feature-contract decision in the new JSON/report**

Later report and JSON tasks must include:

```text
ml_exit_feature_contract_status = PASS
bars_since_fill_0_ml_exit_policy = excluded_until_post_fill_decision_timestamp_exists
ml_exit_timing_contract = feature_time <= decision_time <= execution_time
future_exit_fields_role = target_or_diagnostic_only
close_now_pnl_r_role = target_or_diagnostic_only_backward_compatibility_name
```

If Step 5 cannot pass without removing `max_favorable_r_before_decision` or `max_adverse_r_before_decision` from `EXIT_FEATURE_COLUMNS_BASE`, remove only the unsafe fields and record:

```text
ml_exit_feature_contract_status = PASS_WITH_REDUCED_FEATURE_SET
removed_ml_exit_features = [...]
```

---

### Task 1: Add Failing Chronology Tests

**Files:**
- Modify: `tests/test_fractal0_entry_exit_grid.py`
- Read: `docs/methodology/12-backtest-costs.md`
- Read: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`

**Interfaces:**
- Consumes: current `build_entry_rows(...)`, `simulate_trade(...)`, `build_exit_decision_rows(...)`.
- Produces: failing tests that define the corrected chronology contract.

**Applicable Methodology:**
- `docs/methodology/12-backtest-costs.md`: synthetic simulator tests before using backtest metrics for verdict.
- `docs/methodology/03-feature-contract-leakage.md`: M5 is not an input feature; it only refines execution timing.

**Mandatory Checks:**
- Test shows that M5 fill timestamp is later than H1 bar open when the limit is first touched at `10:10`.
- Test shows that ML exit at H1 `10:00` is not processed as a valid event before actual M5 fill at `10:10`.
- Test shows that same-H1 SL after M5 fill is still allowed if SL is touched after fill.
- Test shows that same-H1 entry+exit remains legal when the exit touch is chronologically after fill.
- Test shows that fill and SL/TP in the same M5 candle are marked ambiguous and resolved by a documented fallback.

**Completion Criterion:**
- New targeted tests fail against current code for the expected reason: current code has no M5 fill timestamp and cannot build a full inside-H1 event order.

- [ ] **Step 1: Add test for first M5 fill timestamp**

Add this test near the existing limit-fill tests in `tests/test_fractal0_entry_exit_grid.py`:

```python
def test_limit_fill_records_first_execution_ohlc_timestamp_inside_h1():
    rows = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 08:00"]),
            "fractal0": [":".join(["0", "100.0", "1"] + ["0"] * 20)],
            "ATR": [1.0],
            "split": ["locked_test"],
            "split_row_id": [7],
        }
    )
    h1 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 09:00", "2021-01-01 10:00", "2021-01-01 11:00"]),
            "open": [100.0, 100.2, 101.0],
            "high": [100.4, 101.2, 102.0],
            "low": [99.6, 99.8, 100.0],
            "close": [100.1, 100.8, 101.5],
        }
    )
    m5 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 10:05", "2021-01-01 10:10"]),
            "open": [100.0, 100.4, 100.7],
            "high": [100.3, 100.6, 101.2],
            "low": [99.8, 100.2, 100.6],
            "close": [100.2, 100.5, 101.0],
        }
    )
    entry_rule = {"entry_id": "E3_open_pullback_1_0atr", "entry_mode": "open_pullback", "pullback_atr": 1.0, "lag_bars": 2}
    policy = {"stop_policy_id": "S2", "family": "fractal0_buffer_entry_floor", "fractal0_buffer_atr": 0.5, "entry_floor_atr": 2.0}

    entries = runner.build_entry_rows(rows, h1, entry_rule, spread=0.2, stop_policy=policy, execution_ohlc=m5)

    assert bool(entries.loc[0, "filled"]) is True
    assert entries.loc[0, "side"] == "SELL"
    assert entries.loc[0, "limit_price"] == 101.0
    assert entries.loc[0, "fill_index"] == 1
    assert entries.loc[0, "fill_time"] == pd.Timestamp("2021-01-01 10:00")
    assert entries.loc[0, "fill_execution_time"] == pd.Timestamp("2021-01-01 10:10")
```

- [ ] **Step 2: Add test that same-H1 ML decision before fill is not a valid post-fill event**

Add this test near `test_ml_exit_does_not_count_hypothetical_fixed_tp_as_same_bar_ambiguity`:

```python
def test_ml_exit_on_h1_open_is_not_processed_before_m5_fill_in_same_h1():
    entry = {
        "side": "SELL",
        "fill_index": 0,
        "fill_time": pd.Timestamp("2021-01-01 10:00"),
        "fill_execution_time": pd.Timestamp("2021-01-01 10:10"),
        "entry_effective_price": 101.0,
        "entry_bid_equivalent": 101.0,
        "protective_stop_price": 105.0,
        "r_value": 4.0,
        "atr": 2.0,
    }
    h1 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00"]),
            "open": [100.0, 100.2],
            "high": [101.2, 100.4],
            "low": [99.0, 99.4],
            "close": [100.5, 99.7],
        }
    )
    ml_scores = {0: 1.0, 1: 0.0}

    result = runner.simulate_trade(
        entry,
        h1,
        {"family": "ml_opposite_any", "prob_threshold": 0.55, "hold_bars": 1},
        spread=0.2,
        ml_scores=ml_scores,
    )

    assert result["close_reason"] == "TIME"
    assert result["exit_time"] == "2021-01-01 11:00:00"
```

- [ ] **Step 3: Add test that same-H1 SL after M5 fill is still valid**

Add this test after Step 2:

```python
def test_same_h1_stop_after_m5_fill_is_valid_when_touch_is_after_fill():
    entry = {
        "side": "BUY",
        "fill_index": 0,
        "fill_time": pd.Timestamp("2021-01-01 10:00"),
        "fill_execution_time": pd.Timestamp("2021-01-01 10:10"),
        "entry_effective_price": 100.2,
        "entry_bid_equivalent": 100.0,
        "protective_stop_price": 99.0,
        "r_value": 1.2,
        "atr": 2.0,
    }
    h1 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00"]),
            "open": [100.0],
            "high": [100.4],
            "low": [98.8],
            "close": [99.2],
        }
    )
    m5 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 10:05", "2021-01-01 10:10", "2021-01-01 10:15"]),
            "open": [100.0, 100.1, 100.2, 99.8],
            "high": [100.3, 100.2, 100.3, 100.0],
            "low": [99.5, 99.4, 100.0, 98.8],
            "close": [100.1, 100.0, 100.1, 99.0],
        }
    )

    result = runner.simulate_trade(
        entry,
        h1,
        {"family": "ml_opposite_any", "prob_threshold": 0.55},
        spread=0.2,
        execution_ohlc=m5,
    )

    assert result["close_reason"] == "SL"
    assert result["exit_time"] == "2021-01-01 10:15:00"
```

- [ ] **Step 4: Add test for fill-M5 candle double-touch fallback**

Add this test after Step 3:

```python
def test_fill_m5_candle_stop_touch_is_marked_ambiguous_and_resolves_sl_first():
    entry = {
        "side": "BUY",
        "fill_index": 0,
        "fill_time": pd.Timestamp("2021-01-01 10:00"),
        "fill_execution_time": pd.Timestamp("2021-01-01 10:10"),
        "fill_execution_confirmed": True,
        "entry_effective_price": 100.2,
        "entry_bid_equivalent": 100.0,
        "protective_stop_price": 99.0,
        "r_value": 1.2,
        "atr": 2.0,
    }
    h1 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00"]),
            "open": [100.0],
            "high": [100.5],
            "low": [98.8],
            "close": [99.5],
        }
    )
    m5 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 10:05", "2021-01-01 10:10"]),
            "open": [100.0, 100.1, 100.3],
            "high": [100.3, 100.2, 100.4],
            "low": [99.5, 99.4, 98.8],
            "close": [100.1, 100.0, 99.0],
        }
    )

    result = runner.simulate_trade(
        entry,
        h1,
        {"family": "ml_opposite_any", "prob_threshold": 0.55},
        spread=0.2,
        execution_ohlc=m5,
    )

    assert result["close_reason"] == "SL"
    assert result["ambiguous"] is True
    assert result["exit_time"] == "2021-01-01 10:10:00"
```

- [ ] **Step 5: Run targeted tests and confirm expected failure**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_entry_exit_grid.py::test_limit_fill_records_first_execution_ohlc_timestamp_inside_h1 \
  tests/test_fractal0_entry_exit_grid.py::test_ml_exit_on_h1_open_is_not_processed_before_m5_fill_in_same_h1 \
  tests/test_fractal0_entry_exit_grid.py::test_same_h1_stop_after_m5_fill_is_valid_when_touch_is_after_fill \
  tests/test_fractal0_entry_exit_grid.py::test_fill_m5_candle_stop_touch_is_marked_ambiguous_and_resolves_sl_first \
  -q
```

Expected:

```text
At least one test fails because build_entry_rows has no execution_ohlc argument and simulate_trade has no single inside-H1 event order based on actual M5 fill time.
```

---

### Task 2: Implement Inside-H1 Event Ordering

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Modify: `tests/test_fractal0_entry_exit_grid.py`

**Interfaces:**
- Consumes: tests from Task 1.
- Produces:
  - `build_entry_rows(..., execution_ohlc: pd.DataFrame | None = None) -> pd.DataFrame`
  - entry rows with `fill_execution_time`
  - entry rows with `fill_execution_time_source` and `fill_execution_confirmed`
  - trade rows with `fill_execution_time`
  - simulator that processes same-H1 events only in chronological order after actual M5 fill

**Applicable Methodology:**
- `docs/methodology/12-backtest-costs.md`: simulator edge cases must be covered by synthetic tests.
- `docs/methodology/03-feature-contract-leakage.md`: M5 use must be after signal/fill only and not become model input.

**Mandatory Checks:**
- Existing tests for spread, fixed TP, SL, timeout and M5 same-bar TP/SL still pass.
- New tests from Task 1 pass.
- Same-H1 entry+exit is not globally banned.
- The implementation fixes the missing inside-H1 order source; it is not only a one-off `ML_CLOSE` guard.
- ML-close score, decision and execution are synchronized: no score key `0`, no ML close before `first_exit_execution_time`, no current-bar close if the decision contract says next-bar execution.
- No changes to grid definitions, rule selection, score cutoffs or MQL4 files.

**Completion Criterion:**
- Targeted tests pass and code exposes `fill_execution_time` in entries/trades; same-H1 event handling starts from actual M5 fill time without changing selected rules.

- [ ] **Step 1: Add helper for M5 window lookup and first limit touch**

In `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, add helpers near `_resolve_same_bar_with_execution_ohlc(...)`:

```python
def _execution_window_for_h1_bar(execution_ohlc: pd.DataFrame | None, h1_time: pd.Timestamp) -> pd.DataFrame:
    if execution_ohlc is None or execution_ohlc.empty or "time" not in execution_ohlc.columns:
        return pd.DataFrame()
    start = pd.Timestamp(h1_time)
    if "_h1_time" in execution_ohlc.columns and execution_ohlc.index.name == "_h1_time":
        try:
            window = execution_ohlc.loc[start]
            if isinstance(window, pd.Series):
                window = window.to_frame().T
            return window.reset_index(drop=True)
        except KeyError:
            return pd.DataFrame()
    end = start + pd.Timedelta(hours=1)
    return execution_ohlc.loc[(execution_ohlc["time"] >= start) & (execution_ohlc["time"] < end)].reset_index(drop=True)


def _first_limit_touch_execution_time(
    side: str,
    h1_time: pd.Timestamp,
    limit_price: float,
    spread: float,
    execution_ohlc: pd.DataFrame | None,
) -> pd.Timestamp | pd.NaT:
    window = _execution_window_for_h1_bar(execution_ohlc, h1_time)
    if window.empty:
        return pd.NaT
    for _, bar in window.iterrows():
        low_bid = float(bar["low"])
        high_bid = float(bar["high"])
        if side == "BUY" and low_bid + float(spread) <= float(limit_price):
            return pd.Timestamp(bar["time"])
        if side == "SELL" and high_bid >= float(limit_price):
            return pd.Timestamp(bar["time"])
    return pd.NaT
```

- [ ] **Step 2: Reuse window helper inside `_resolve_same_bar_with_execution_ohlc`**

Replace the local window-building block in `_resolve_same_bar_with_execution_ohlc(...)` with:

```python
    window = _execution_window_for_h1_bar(execution_ohlc, start)
    if window.empty:
        return None
```

Keep the existing stop/TP loop after this block.

- [ ] **Step 3: Extend `build_entry_rows` signature and fill result**

Change the function definition to:

```python
def build_entry_rows(
    rows: pd.DataFrame,
    ohlc: pd.DataFrame,
    entry_rule: dict[str, object],
    spread: float,
    stop_policy: dict[str, object] | None = None,
    execution_ohlc: pd.DataFrame | None = None,
) -> pd.DataFrame:
```

Initialize `fill` with the new fields:

```python
        fill = {
            "filled": False,
            "fill_index": None,
            "fill_time": pd.NaT,
            "fill_execution_time": pd.NaT,
            "fill_execution_time_source": "not_filled",
            "fill_execution_confirmed": False,
            "entry_effective_price": np.nan,
            "entry_bid_equivalent": np.nan,
        }
```

When BUY fills, set:

```python
                    "fill_execution_time": _first_limit_touch_execution_time(
                        side,
                        pd.Timestamp(ohlc_times[pos]),
                        float(limit_price),
                        float(spread),
                        execution_ohlc,
                    ),
```

When SELL fills, set the same `fill_execution_time` call.

After the fill loop, set the source explicitly. Do not silently replace missing M5 touch with H1 open:

```python
        if fill["filled"]:
            if execution_ohlc is None:
                fill["fill_execution_time"] = fill["fill_time"]
                fill["fill_execution_time_source"] = "h1_no_execution_ohlc"
                fill["fill_execution_confirmed"] = False
            elif pd.isna(fill.get("fill_execution_time")):
                fill["fill_execution_time_source"] = "missing_m5_touch"
                fill["fill_execution_confirmed"] = False
            else:
                fill["fill_execution_time_source"] = "m5_touch"
                fill["fill_execution_confirmed"] = True
```

- [ ] **Step 4: Pass execution_ohlc to all entry builders, including the base grid cache**

In `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, change:

```python
entries = base.build_entry_rows(splits[split], ohlc, entry_rule, active_spread, stop_policy)
```

to:

```python
entries = base.build_entry_rows(splits[split], ohlc, entry_rule, active_spread, stop_policy, execution_ohlc)
```

In `ML/baseline/benchmark_fractal0_entry_quality_filter.py`, change the fixed11/current-history paths that currently call:

```python
entries = base.build_entry_rows(rows, ohlc, _entry_rule(), active_spread, stop_policy)
```

to:

```python
entries = base.build_entry_rows(rows, ohlc, _entry_rule(), active_spread, stop_policy, execution_ohlc)
```

Do not change unrelated exploratory paths unless the call now fails because of the signature.

In `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, extend `_entry_cache_for_spread(...)` with an optional `execution_ohlc` parameter:

```python
def _entry_cache_for_spread(
    splits: dict[str, pd.DataFrame],
    ohlc: pd.DataFrame,
    spread: float,
    frozen_scores: pd.DataFrame,
    stop_policies: list[dict[str, object]] | None = None,
    entries: list[dict[str, object]] | None = None,
    masks: list[dict[str, object]] | None = None,
    execution_ohlc: pd.DataFrame | None = None,
) -> tuple[dict[tuple[str, str, str, str], pd.DataFrame], dict[str, object]]:
```

Inside `_entry_cache_for_spread(...)`, change:

```python
entry_rows = build_entry_rows(rows, ohlc, entry, spread, stop_policy)
```

to:

```python
entry_rows = build_entry_rows(rows, ohlc, entry, spread, stop_policy, execution_ohlc)
```

In `run_matrix(...)`, pass `execution_ohlc` to both cache builders:

```python
canonical_entry_cache, cache_report = _entry_cache_for_spread(
    splits, ohlc, CONFIG.canonical_spread, frozen_scores, active_stop_policies, active_entries, active_masks, execution_ohlc
)
```

```python
stress_entry_cache, _ = _entry_cache_for_spread(
    {"val_eval": splits["val_eval"]}, ohlc, CONFIG.stress_spread, frozen_scores, active_stop_policies, active_entries, active_masks, execution_ohlc
)
```

Update the monkeypatch test in `tests/test_fractal0_entry_exit_grid.py` so the fake accepts the new parameter:

```python
def fake_build_entry_rows(rows, ohlc, entry, spread, stop_policy=None, execution_ohlc=None):
    out = rows.copy()
    out["filled"] = [True, False, True]
    return out
```

- [ ] **Step 5: Preserve `fill_execution_time` in trade rows**

In `_simulate_entries(...)`, add this field to the output row:

```python
"fill_execution_time": entry_dict.get("fill_execution_time"),
"fill_execution_time_source": entry_dict.get("fill_execution_time_source"),
"fill_execution_confirmed": entry_dict.get("fill_execution_confirmed"),
```

Place it near `position_id`, `split_row_id`, `entry_id`.

- [ ] **Step 6: Add an inside-H1 event lower bound to `simulate_trade`**

Inside `simulate_trade(...)`, derive the factual earliest event time for the fill H1 bar. This is the root fix: every same-H1 exit check must know whether it is allowed to look at the full H1 bar or only at M5 bars after actual fill.

```python
        decision_time = pd.Timestamp(bar.get("time", pd.NaT))
        fill_execution_time = pd.Timestamp(entry.get("fill_execution_time", entry.get("fill_time", pd.NaT)))
        fill_execution_confirmed = bool(entry.get("fill_execution_confirmed", False))
        fill_h1_time = pd.Timestamp(entry.get("fill_time", pd.NaT))
        same_h1_as_fill = pd.notna(fill_h1_time) and decision_time == fill_h1_time
        earliest_event_time = fill_execution_time if same_h1_as_fill and fill_execution_confirmed and pd.notna(fill_execution_time) else None
        fill_h1_missing_m5_touch = same_h1_as_fill and not fill_execution_confirmed
```

Do not return from `simulate_trade(...)` on any same-H1 condition until same-H1 SL/TP and ML-close have been evaluated against this lower bound.

- [ ] **Step 7: Resolve same-H1 SL/TP only from M5 bars at or after fill**

In `_resolve_same_bar_with_execution_ohlc(...)`, support a lower bound inside the H1 bar. Change the signature to:

```python
def _resolve_same_bar_with_execution_ohlc(
    side: str,
    h1_bar: pd.Series,
    execution_ohlc: pd.DataFrame | None,
    spread: float,
    stop: float,
    tp: float,
    not_before: pd.Timestamp | None = None,
) -> tuple[str, pd.Series, bool] | None:
```

After the `window.empty` check, add:

```python
    if not_before is not None and pd.notna(not_before):
        window = window.loc[pd.to_datetime(window["time"]) >= pd.Timestamp(not_before)].reset_index(drop=True)
        if window.empty:
            return None
```

Before the existing `if ambiguous:` block in `simulate_trade(...)`, add a same-fill-H1 refinement:

```python
        if fill_h1_missing_m5_touch:
            stop_hit = False
            tp_hit = False
        if same_h1_as_fill and (stop_hit or tp_hit) and execution_ohlc is not None:
            resolved = _resolve_same_bar_with_execution_ohlc(
                side,
                bar,
                execution_ohlc,
                spread,
                stop,
                tp,
                earliest_event_time,
            )
            if resolved is not None:
                reason, resolved_bar, still_ambiguous = resolved
                price = stop if reason == "SL" else tp
                if pd.Timestamp(resolved_bar.get("time", pd.NaT)) == earliest_event_time:
                    still_ambiguous = True
                return _trade_result(reason, side, entry_price, price, r_value, i, resolved_bar, still_ambiguous)
            stop_hit = False
            tp_hit = False
```

Keep the existing `if ambiguous:` block for non-fill H1 bars, but pass `None` as `not_before` there:

```python
resolved = _resolve_same_bar_with_execution_ohlc(side, bar, execution_ohlc, spread, stop, tp, None)
```

- [ ] **Step 8: Do not allow fill-H1 ML-close under the current H1-only ML-exit timestamp contract**

Keep ML-close as an H1 decision event, but make it part of the same event-ordering model. In the current code, `build_exit_decision_rows(...)` stores `decision_time` as H1 timestamp and `first_exit_execution_time = idx + 1`, while `simulate_trade(...)` closes `ML_CLOSE` at current `bar["close"]`. This is inconsistent. The fixed contract is:

```text
score key k means: decision is made after H1 bar k is known, and the first executable close is the next H1 bar.
```

Therefore `simulate_trade(...)` must never use score key `0`, and when score key `i` triggers `ML_CLOSE`, it must close at the first executable moment after the signal is available. In H1 OHLC backtest this is represented as the next H1 bar open, not current `i` close. In live MT4 this corresponds to closing immediately after Python writes the signal, without waiting for another full H1 bar.

Change the ML-close block in `simulate_trade(...)` to use this predicate:

```python
        ml_decision_is_after_fill = i > 0 and not same_h1_as_fill
        ml_execution_pos = i + 1
        can_execute_ml_close = ml_execution_pos < len(bars)
        if (
            ml_decision_is_after_fill
            and can_execute_ml_close
            and (str(exit_rule.get("family", "")).startswith("ml") or exit_rule.get("family") == "fixed_sl_ml_profit_exit")
        ):
            score = (ml_scores or {}).get(i, 0.0)
            ml_exit_bar = bars.iloc[ml_execution_pos]
            ml_exit_price = float(ml_exit_bar["open"])
            now_r = _pnl_r(side, entry_price, close_price, r_value)
            if score >= float(exit_rule.get("prob_threshold", 1.1)) and (exit_rule.get("family") != "fixed_sl_ml_profit_exit" or now_r >= 0):
                return _trade_result("ML_CLOSE", side, entry_price, ml_exit_price, r_value, ml_execution_pos, ml_exit_bar, False)
```

This is not a global ban on same-H1 entry+exit. SL/TP can still close on the fill H1 if M5 shows the touch at or after fill. Same-H1 `ML_CLOSE` can be reintroduced only after a separate implementation adds a real post-fill ML decision timestamp inside H1, proves its feature availability and tests it explicitly.

- [ ] **Step 9: Add machine-readable execution contract to JSON writers**

In `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, extend the artifact near `execution_contract`:

```python
        "execution_ohlc_usage": "limit_fill_timestamp_and_same_h1_post_fill_event_order",
        "ml_exit_feature_contract_status": "PASS",
        "bars_since_fill_0_ml_exit_policy": "excluded_until_post_fill_decision_timestamp_exists",
        "ml_exit_timing_contract": "feature_time <= decision_time <= execution_time",
        "future_exit_fields_role": "target_or_diagnostic_only",
        "close_now_pnl_r_role": "target_or_diagnostic_only_backward_compatibility_name",
        "fill_execution_time_contract": {
            "column": "fill_execution_time",
            "source_column": "fill_execution_time_source",
            "confirmed_column": "fill_execution_confirmed",
            "confirmed_source": "m5_touch",
        },
        "same_h1_ml_close_policy": "disabled_on_fill_h1_until_real_post_fill_ml_decision_timestamp_exists",
        "missing_m5_fill_policy": "do_not_process_same_h1_exits_as_confirmed_post_fill_events",
        "fill_m5_double_touch_policy": "SL_first_with_ambiguous_true",
        "execution_chronology_counts": {
            "fill_execution_time_source": trades_df.get("fill_execution_time_source", pd.Series(dtype=object)).fillna("missing").value_counts().to_dict() if not trades_df.empty else {},
            "fill_execution_confirmed": int(trades_df.get("fill_execution_confirmed", pd.Series(dtype=bool)).astype(bool).sum()) if not trades_df.empty else 0,
            "same_h1_fill_exit": int((pd.to_datetime(trades_df.get("fill_time"), errors="coerce") == pd.to_datetime(trades_df.get("exit_time"), errors="coerce")).sum()) if not trades_df.empty else 0,
            "same_h1_ml_close": int(((pd.to_datetime(trades_df.get("fill_time"), errors="coerce") == pd.to_datetime(trades_df.get("exit_time"), errors="coerce")) & trades_df.get("close_reason", pd.Series(dtype=object)).eq("ML_CLOSE")).sum()) if not trades_df.empty else 0,
            "ambiguous": int(trades_df.get("ambiguous", pd.Series(dtype=bool)).astype(bool).sum()) if not trades_df.empty else 0,
        },
```

In `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, update the JSON writer value from:

```python
"execution_ohlc_usage": "resolve_same_h1_bar_tp_sl_order_only" if config.execution_ohlc_path else None
```

to:

```python
"execution_ohlc_usage": "limit_fill_timestamp_and_same_h1_post_fill_event_order" if config.execution_ohlc_path else None
```

- [ ] **Step 10: Run targeted simulator tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected:

```text
All tests in tests/test_fractal0_entry_exit_grid.py pass.
```

- [ ] **Step 11: Run fixed11 wrapper smoke tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_rich_entry_locked_test.py -q
```

Expected:

```text
All tests in tests/test_fractal0_fixed11_rich_entry_locked_test.py pass.
```

---

### Task 3: Diagnostic Fixed11 Rerun With Corrected Chronology

**Files:**
- Read: `ML/reports/leaderboard_closure_audit_rules.csv`
- Read: `ML/reports/fractal0_stop_grid_m5.json`
- Read: `DATA/Nero_XAUUSD_test_labeled.csv`
- Read: `DATA/XAUUSD_H1_OHLC.csv`
- Read: `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`
- Create: `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json`
- Create: `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix_trades.csv`
- Create: `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix_summary.csv`
- Create: `ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json`

**Interfaces:**
- Consumes: corrected simulator from Task 2.
- Produces: diagnostic artifact for reporting and later MT4 export decision.

**Applicable Methodology:**
- `docs/methodology/06-temporal-split.md`: old locked_test is already opened; no new selection.
- `docs/methodology/10-frozen-test-oos.md`: changed execution convention means no candidate verdict from this rerun.
- `docs/methodology/12-backtest-costs.md`: report PnL/PF only as diagnostic.

**Mandatory Checks:**
- Command uses output-prefix ending `_h1_chronology_fix`.
- JSON top-level `verdict`/`decision` must be patched or generated as `DIAGNOSTIC_ONLY`, not `candidate_check_required`.
- Selection CSV must not be readable as a fresh candidate verdict; add `allowed_max_verdict=DIAGNOSTIC_ONLY` and diagnostic decision labels.
- Compare old current-history rerun to chronology-fix rerun: total trades, `hold_bars=0`, same-H1 fill/exit, PnL, PF, close reasons, fill confirmation sources and ambiguous counts.
- Report and JSON must state that the rerun changed both ML-exit feature contract and execution convention; old fixed11 metrics/cutoffs are not the same frozen verification chain.

**Completion Criterion:**
- New JSON/CSV artifacts exist, include hashes and show whether `hold_bars=0` and impossible same-H1 ML exits decreased.

- [ ] **Step 1: Run fixed11 diagnostic rerun**

Run:

```bash
./.venv/bin/python ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py \
  --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv \
  --source-artifact ML/reports/fractal0_stop_grid_m5.json \
  --locked-test-path DATA/Nero_XAUUSD_test_labeled.csv \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --output-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix
```

Expected:

```text
Command exits 0 and writes *_h1_chronology_fix.json plus summary/trades/yearly/side/selection CSV files.
```

- [ ] **Step 2: Force diagnostic verdict if runner still emits candidate wording**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

p = Path("ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["original_runner_verdict"] = d.get("verdict")
d["verdict"] = "DIAGNOSTIC_ONLY"
d["decision"] = "FIXED11_H1_CHRONOLOGY_FIX_DIAGNOSTIC_ONLY"
d["allowed_max_verdict"] = "DIAGNOSTIC_ONLY"
d["diagnostic_reason"] = "ML-exit feature contract and execution convention changed after fixed11 locked_test; rerun is for simulator chronology validation, not candidate selection"
d.setdefault("execution_ohlc_usage", "limit_fill_timestamp_and_same_h1_post_fill_event_order")
d.setdefault("ml_exit_feature_contract_status", "PASS")
d.setdefault("bars_since_fill_0_ml_exit_policy", "excluded_until_post_fill_decision_timestamp_exists")
d.setdefault("ml_exit_timing_contract", "feature_time <= decision_time <= execution_time")
d.setdefault("future_exit_fields_role", "target_or_diagnostic_only")
d.setdefault("close_now_pnl_r_role", "target_or_diagnostic_only_backward_compatibility_name")
d.setdefault("same_h1_ml_close_policy", "disabled_on_fill_h1_until_real_post_fill_ml_decision_timestamp_exists")
d.setdefault("missing_m5_fill_policy", "do_not_process_same_h1_exits_as_confirmed_post_fill_events")
d.setdefault("fill_m5_double_touch_policy", "SL_first_with_ambiguous_true")
p.write_text(json.dumps(d, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

selection_path = Path("ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix_selection.csv")
if selection_path.exists():
    import pandas as pd
    selection = pd.read_csv(selection_path, sep=";")
    selection["legacy_gate_decision"] = selection["decision"]
    selection["decision"] = selection["decision"].map({
        "KEEP_CANDIDATE": "DIAGNOSTIC_GATE_PASSED",
        "REJECT": "DIAGNOSTIC_GATE_FAILED",
    }).fillna(selection["decision"])
    selection["allowed_max_verdict"] = "DIAGNOSTIC_ONLY"
    selection["decision_reason"] = "ML-exit feature contract and execution convention changed after fixed11 locked_test; gate is diagnostic only"
    selection.to_csv(selection_path, sep=";", index=False)
print("diagnostic_verdict_ok")
PY
```

Expected:

```text
diagnostic_verdict_ok
```

- [ ] **Step 3: Build comparison artifact**

Run:

```bash
./.venv/bin/python - <<'PY'
import hashlib
import json
from pathlib import Path

import pandas as pd

old_prefix = Path("ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history")
new_prefix = Path("ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def metrics(prefix: Path) -> dict:
    summary = pd.read_csv(prefix.with_name(prefix.name + "_summary.csv"), sep=";")
    trades = pd.read_csv(prefix.with_name(prefix.name + "_trades.csv"), sep=";")
    hold = pd.to_numeric(trades["hold_bars"], errors="coerce")
    fill_time = pd.to_datetime(trades["fill_time"], errors="coerce")
    fill_exec = pd.to_datetime(trades.get("fill_execution_time"), errors="coerce") if "fill_execution_time" in trades else pd.Series(pd.NaT, index=trades.index)
    exit_time = pd.to_datetime(trades["exit_time"], errors="coerce")
    pnl = pd.to_numeric(trades["pnl_r"], errors="coerce")
    source = trades.get("fill_execution_time_source", pd.Series("absent", index=trades.index)).fillna("missing")
    confirmed = trades.get("fill_execution_confirmed", pd.Series(False, index=trades.index)).astype(bool)
    ambiguous = trades.get("ambiguous", pd.Series(False, index=trades.index)).astype(bool)
    return {
        "summary_rows": int(len(summary)),
        "trades": int(len(trades)),
        "pnl_r_sum": float(pnl.sum()),
        "pf_min": float(pd.to_numeric(summary["pf"], errors="coerce").min()),
        "pf_max": float(pd.to_numeric(summary["pf"], errors="coerce").max()),
        "hold_bars_0": int((hold == 0).sum()),
        "same_h1_fill_exit": int((fill_time == exit_time).sum()),
        "fill_execution_after_h1_open": int((fill_exec > fill_time).sum()) if "fill_execution_time" in trades else None,
        "fill_execution_confirmed": int(confirmed.sum()),
        "fill_execution_time_source_counts": source.value_counts().to_dict(),
        "ambiguous_count": int(ambiguous.sum()),
        "same_h1_ml_close": int(((fill_time == exit_time) & trades["close_reason"].eq("ML_CLOSE")).sum()),
        "close_reason_counts": trades["close_reason"].value_counts().to_dict(),
    }

out = {
    "status": "DIAGNOSTIC_ONLY",
    "old_current_history_prefix": str(old_prefix),
    "new_h1_chronology_fix_prefix": str(new_prefix),
    "hashes": {
        "old_json": sha(old_prefix.with_suffix(".json")),
        "old_trades": sha(old_prefix.with_name(old_prefix.name + "_trades.csv")),
        "new_json": sha(new_prefix.with_suffix(".json")),
        "new_trades": sha(new_prefix.with_name(new_prefix.name + "_trades.csv")),
    },
    "old_current_history": metrics(old_prefix),
    "new_h1_chronology_fix": metrics(new_prefix),
}
Path("ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2, default=str) + "\n",
    encoding="utf-8",
)
print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
PY
```

Expected:

```text
JSON printed with old_current_history and new_h1_chronology_fix sections.
```

- [ ] **Step 4: Verify no old artifacts were overwritten**

Run:

```bash
git diff -- ML/reports/fractal0_fixed11_rich_entry_locked_test.json \
  ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv \
  ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json \
  ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv
```

Expected:

```text
No diff for old locked-test/current-history artifacts.
```

---

### Task 4: Report, Roadmap And Handoff

**Files:**
- Create: `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`
- Modify: `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md` only if the new report is added to wiki navigation.

**Interfaces:**
- Consumes: comparison artifact from Task 3.
- Produces: project memory that tells the next agent exactly what changed and what still blocks MT4 parity.

**Applicable Methodology:**
- `docs/methodology/16-reporting-audit.md`: report commands, hashes, artifacts, limitations, invalidated assumptions, split disclosure and next step.
- `docs/methodology/13-export-mt4-parity.md`: do not call this MT4 parity; list what MT4 reconciliation still must prove.

**Mandatory Checks:**
- Previous fill-chronology report must be corrected only if it contains conclusions superseded by the new code; do not delete useful historical evidence.
- New report must include `Stage Level` and `Changed Files`.
- New report must include `allowed_max_verdict=DIAGNOSTIC_ONLY`.
- New report must state that M5 was not used as ML input.
- New report must state that old fixed11 metrics/cutoffs are invalidated as the same frozen chain because ML-exit feature contract changed.
- Changelog/handoff/wiki must not claim production readiness or MT4 parity.

**Completion Criterion:**
- Report and project context identify the next narrow step: export corrected fixed11 signals/trades and run MT4 slot parity, or reject if chronology-fix destroys the edge.

- [ ] **Step 1: Write the new report**

Create `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md` with these required sections:

```markdown
# Fixed11 Python H1 Chronology Fix

> **Дата**: 2026-07-29
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Goal**: Проверить corrected Python execution contract, где M5 уточняет фактическое время fill внутри H1, а все выходы обрабатываются только в хронологически допустимом порядке после fill.

## Context

## Stage Level

## Methodology

## Changed Files

## What Changed

Include:

```text
ML-exit feature contract changed:
- bars_since_fill=0 is excluded from working ML-exit train/score rows;
- future exit fields remain target/diagnostic only;
- ML_CLOSE execution is aligned with first_exit_execution_time.
```

## What Did Not Change

## Commands

## Artifacts

## Results

## Chronology Checks

## Limitations

## Invalidated Assumptions

## Next Step

## Related Materials
```

Fill the sections from:

- `ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json`;
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json`;
- `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`;
- methodology files listed in this plan.

- [ ] **Step 2: Update old chronology report only for superseded wording**

In `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`, add a short note near the top:

```markdown
> **Superseded follow-up**: проблема, описанная здесь, исправляется отдельным Python execution-contract планом `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md` и отчётом `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`. Этот документ остаётся исходным аудитом причины, но его старые выводы о следующих шагах не должны читаться как финальный статус после chronology-fix rerun.
```

- [ ] **Step 3: Update roadmap, changelog, handoff and wiki**

Make minimal updates:

- `docs/superpowers/roadmap.md`: replace “next step is chronology-fix plan” with the actual post-rerun next step.
- `CHANGELOG.md`: add one top entry with report/artifact paths and `DIAGNOSTIC_ONLY`.
- `CONTEXT_HANDOFF.md`: add current status, what to read first, and what not to claim.
- `wiki/research/fractal-stop-research.md`: add one numbered summary entry for the chronology fix.
- `wiki/index.md`: add the new report only if this wiki index lists reports manually.

- [ ] **Step 4: Verify report/artifact consistency**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

report = Path("docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md").read_text(encoding="utf-8")
comparison = json.loads(Path("ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json").read_text(encoding="utf-8"))
artifact = json.loads(Path("ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json").read_text(encoding="utf-8"))

assert "DIAGNOSTIC_ONLY" in report
assert "MT4 parity" in report or "MT4" in report
assert artifact["verdict"] == "DIAGNOSTIC_ONLY"
assert artifact["allowed_max_verdict"] == "DIAGNOSTIC_ONLY"
for value in [
    str(comparison["new_h1_chronology_fix"]["trades"]),
    str(comparison["new_h1_chronology_fix"]["hold_bars_0"]),
    str(round(comparison["new_h1_chronology_fix"]["pnl_r_sum"], 6)),
]:
    assert value in report, value
print("report_consistency_ok")
PY
```

Expected:

```text
report_consistency_ok
```

- [ ] **Step 5: Final targeted verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py tests/test_fractal0_fixed11_rich_entry_locked_test.py -q
```

Expected:

```text
All targeted tests pass.
```

Run:

```bash
git status --short --untracked-files=all
```

Expected:

```text
Only files from this plan are changed or created.
```

---

## Self-Review

- Spec coverage: план покрывает исправление Python-хронологии внутри H1, M5 fill timestamp, общую event-ordering модель после фактического fill, diagnostic rerun, отчётность и дальнейший MT4 parity шаг.
- Methodology coverage: для каждого этапа указаны применимые методики, обязательные проверки и критерий завершения.
- Placeholder scan: намеренно не используются `TBD`, `TODO`, “add tests” без кода или неуказанные пути.
- Type consistency: новые интерфейсы используют существующие pandas types и добавляют колонки `fill_execution_time`, `fill_execution_time_source`, `fill_execution_confirmed`.
- Scope check: MQL4 live/tester правки, новый model selection и новый retained-subset export не входят в этот план; они должны идти отдельным планом после результатов diagnostic rerun.
