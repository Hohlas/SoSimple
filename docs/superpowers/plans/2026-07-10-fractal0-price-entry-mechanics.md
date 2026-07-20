# Fractal0 Price Entry Mechanics Oracle-Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, есть ли диагностический потолок движения после исполнимого входа через возврат цены к зоне около `fractal0_price`.

**Architecture:** Этап делает только oracle-preflight механики входа. Он не обучает модель, не выбирает торговую систему и не считает PnL/PF, потому что выход из сделки не задан. Runner строит fill/no-fill, targets от фактической цены исполнения и отчёт по `oracle_favorable_move_after_cost` / adverse move; если результат проходит gate, итоговый verdict не выше `research_only`, а lifecycle переходит в `research_hypothesis` для отдельного probe-плана.

**Tech Stack:** Python 3.10+, pandas, numpy, pytest, существующий `benchmark_next_open_entry_updn_foundation.py` для загрузки OHLC/split, `./.venv/bin/python`.

## Global Constraints

- Работать в текущей ветке; worktree запрещён.
- Использовать `./.venv/bin/python`.
- `locked_test` не открывать.
- Уровень этапа: поисковый.
- `verdict` при хорошем результате: не выше `research_only`.
- `lifecycle_status` при хорошем результате: `research_hypothesis`.
- `allowed_max_verdict`: `research_only`.
- Начальный `lifecycle_status`: `research_scan`.
- `origin_bias`: `post_mortem`, потому что ветка возникла после отказа `next open`.
- `research_priority`: `high`, причина — старый Up/Dn signal силён от `fractal0_price`, а `next open` отклонён.
- Не использовать `signal` как сторону сделки; направление сделки берётся как `direction = -fractal0.dir` согласно `docs/methodology/03-feature-contract-leakage.md`.
- Если side contract по реальным строкам не проходит sanity-check, результат не может подняться выше `diagnostic_only`.
- Не использовать старые `up_*/dn_*` от `fractal0_price` как торговую разметку.
- Новые targets считать только от фактической достижимой цены исполнения.
- Этап не имеет exit contract сделки; значит запрещены слова PnL, PF, profitable/tradable/live-ready в выводах этапа.
- Spread `0.00` разрешён только как отладочный diagnostic и не участвует в gate.
- ML-обучение не входит в этот план. Если oracle-preflight проходит, следующий шаг — отдельный frozen probe-plan.
- После Python-изменений запускать `./.venv/bin/python -m pytest tests/ -q`.

---

## Research Protocol

Гипотеза:

```text
Сигнал Up/Dn может быть полезен не для немедленного входа на next open, а для
входа через возврат цены к зоне около fractal0_price после первого времени,
когда live-контур мог выставить ордер.
```

### Execution Contract

```text
entry_mechanics = [retest_zone]
entry_price_modes = [limit_at_fractal0, zone_edge]
zone_width_atr = [0.00, 0.25, 0.50]
max_fill_lag_bars = [3, 6]
horizons = [3, 6, 12]
spread_values = [0.00, 0.20, 0.40]
side_rule = candidate_signal_from_fractal0_direction
fractal0.direction == -1 -> BUY
fractal0.direction == 1 -> SELL
first_order_eligible_bar_offset = 1
```

Смысл `first_order_eligible_bar_offset = 1`: если `signal_time` попадает перед
первым доступным OHLC-баром, fill-поиск начинается не с этого первого бара, а
со следующего полного бара. Это консервативно учитывает запись строки, чтение
watcher-ом, preprocessing/inference и отправку ордера. Если позднее будет
доказан более ранний runtime, это новый execution contract.

Правила цены входа:

- `limit_at_fractal0`: fill есть только если OHLC-бар реально пересёк сам
  `fractal0_price`; `entry_price = fractal0_price`.
- `zone_edge`: fill есть если OHLC-бар пересёк зону
  `[fractal0_price - zone_width_atr * ATR, fractal0_price + zone_width_atr * ATR]`.
  Если сам `fractal0_price` недостижим внутри бара, `entry_price` равен
  достижимому краю зоны. Это не даёт широкой зоне бесплатный идеальный вход в
  центр.

### Target Contract

Этап не моделирует выход сделки. Он считает только движение внутри окна после
fill:

```text
target_entry_up_h = max(high[fill_bar : fill_bar + h] - entry_price, 0)
target_entry_dn_h = max(entry_price - low[fill_bar : fill_bar + h], 0)
target_entry_log_ratio_h = log1p(target_entry_up_h) - log1p(target_entry_dn_h)
oracle_favorable_move_after_cost:
  BUY  = target_entry_up_h - spread
  SELL = target_entry_dn_h - spread
oracle_adverse_move:
  BUY  = target_entry_dn_h
  SELL = target_entry_up_h
```

Это MFE/MAE oracle, где MFE — максимальное благоприятное движение, MAE —
максимальное неблагоприятное движение внутри окна. Это не PnL и не PF, потому
что неизвестно, что было раньше: благоприятное или неблагоприятное движение, и
нет TP/SL/timeout выхода.

Future-derived поля:

```text
target_entry_up_*
target_entry_dn_*
target_entry_log_ratio_*
oracle_favorable_move_after_cost
oracle_adverse_move
```

Эти поля запрещены как input. Feature builders должны использовать allowlist.

### Search Budget

Текущий бюджет:

```text
1 mechanic x 2 entry price modes x 3 zone widths x 2 fill lags
x 3 horizons x 3 spread values = 108 oracle configurations
```

Нижняя оценка уже раскрытого прямого prior search budget:

```text
Regression Up/Dn target foundation: 75
Next-open entry Up/Dn foundation: 1 fixed diagnostic model
Direct lower bound before this plan: 76
Current plan: 108
Cumulative lower bound for this branch: 184
```

В отчёте обязательно добавить ссылки на более широкий related context:
Regression Up/Dn ratio audit, already-moved audit, entry-based searches,
direction-inside-mask full grid and narrow replication. Если точный
накопленный бюджет широкой ветки не восстановлен, поле
`cumulative_search_budget_status` должно быть `lower_bound_disclosed`, а итог
не может быть выше `research_only`.

### Gate

Gate не использует `spread=0.00`. Gate выбирает правило только на `train_core`
и проверяет выбранное правило на `val_stop`. `diagnostic_holdout` и
`low_n_disclosure` остаются disclosure-only.

Минимальные условия для `verdict=research_only` и
`lifecycle_status=research_hypothesis`:

```text
side_contract_status: PASS
min_filled_events_total_train_core: 300
min_filled_events_total_val_stop: 150
min_filled_events_per_year_val_stop: 30
min_years_or_windows_val_stop: 3
max_no_fill_rate_val_stop: 0.70
canonical_spread_value: 0.20
stress_spread_value: 0.40
canonical_favorable_to_adverse_ratio_min: 1.05
stress_favorable_to_adverse_ratio_min: 0.95
ratio_without_best_year_min: 0.95
buy_sell_or_direction_group_disclosure: required
fill_lag_bucket_disclosure: required
zone_width_disclosure: required
horizon_disclosure: required
dummy_or_simple_rule_comparison: required
```

Если gate не проходит, итоговый verdict: `diagnostic_only`, lifecycle:
`exploratory_result` или `research_scan` с закрытием текущей механики.

---

## Files

**Create**

- `ML/baseline/benchmark_fractal0_price_entry_mechanics.py` — runner oracle-preflight для retest-zone entry.
- `tests/test_fractal0_price_entry_mechanics.py` — тесты parsing, side mapping, first eligible time, fill, target, oracle metrics, gate.
- `docs/ML/benchmark_fractal0_price_entry_mechanics.py.md` — описание runner-а и команд запуска.
- `docs/reports/2026-07-10-fractal0-price-entry-mechanics.md` — итоговый отчёт после полного прогона.

**Modify**

- `docs/superpowers/roadmap.md` — после завершения этапа заменить текущий пункт результатом.
- `CONTEXT_HANDOFF.md` — после завершения этапа записать текущую точку.
- `CHANGELOG.md` — после завершения этапа добавить запись, если вывод меняет проектное знание.
- `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md` — после завершения этапа синхронизировать wiki.

**Generated**

- `ML/reports/fractal0_price_entry_mechanics.json`
- `ML/reports/fractal0_price_entry_mechanics_rows.csv`

---

### Task 1: Config, Fractal Parsing, Side Mapping Audit

**Files:**
- Create: `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`
- Create: `tests/test_fractal0_price_entry_mechanics.py`

**Interfaces:**
- Produces: `Fractal0EntryMechanicsConfig`
- Produces: `parse_fractal0(value: object) -> dict | None`
- Produces: `trade_side_from_fractal_direction(direction: object) -> str | None`
- Produces: `fractal0_entry_config() -> dict[str, object]`
- Produces: `audit_side_contract(rows: pd.DataFrame) -> dict`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_fractal0_price_entry_mechanics.py`:

```python
import pandas as pd

import ML.baseline.benchmark_fractal0_price_entry_mechanics as runner


def test_parse_fractal0_extracts_time_price_direction_and_shift():
    value = "1700000000:2030.5:-1:0.1:0.2:0:0:0:0.3:1:0.4:1:2:3:4:5:6:0.7:0.8:0.9:1.0:2.5:2"

    parsed = runner.parse_fractal0(value)

    assert parsed == {
        "time": 1700000000,
        "price": 2030.5,
        "direction": -1,
        "shift": 2,
    }


def test_trade_side_from_fractal_direction_uses_project_contract():
    assert runner.trade_side_from_fractal_direction(-1) == "BUY"
    assert runner.trade_side_from_fractal_direction(1) == "SELL"
    assert runner.trade_side_from_fractal_direction(0) is None
    assert runner.trade_side_from_fractal_direction(float("nan")) is None


def test_fractal0_entry_config_discloses_verdict_lifecycle_and_budget():
    config = runner.fractal0_entry_config()

    assert config["experiment"] == "fractal0_price_entry_mechanics"
    assert config["research_level"] == "search"
    assert config["initial_lifecycle_status"] == "research_scan"
    assert config["lifecycle_if_gate_pass"] == "research_hypothesis"
    assert config["allowed_max_verdict"] == "research_only"
    assert config["verdict_if_gate_pass"] == "research_only"
    assert config["entry_price_modes"] == ["limit_at_fractal0", "zone_edge"]
    assert config["zone_width_atr"] == [0.0, 0.25, 0.5]
    assert config["max_fill_lag_bars"] == [3, 6]
    assert config["horizons"] == [3, 6, 12]
    assert config["spread_values"] == [0.0, 0.2, 0.4]
    assert config["side_rule"] == "direction = -fractal0.dir"
    assert config["current_search_budget"] == 108
    assert config["prior_search_budget_lower_bound"] == 76
    assert config["cumulative_search_budget_lower_bound"] == 184
    assert config["locked_test"] == "not_opened"


def test_audit_side_contract_requires_real_distribution():
    rows = pd.DataFrame({"fractal0_direction": [1, -1, 1, -1]})

    audit = runner.audit_side_contract(rows)

    assert audit["status"] == "PASS"
    assert audit["direction_counts"] == {"-1": 2, "1": 2}
    assert audit["required_before_research_only"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_price_entry_mechanics.py::test_parse_fractal0_extracts_time_price_direction_and_shift -q
```

Expected: FAIL with `ModuleNotFoundError` or missing function.

- [ ] **Step 3: Implement minimal runner skeleton**

Create `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`:

```python
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import math
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ML.baseline import benchmark_next_open_entry_updn_foundation as next_open


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "ML" / "reports"
REPORT_JSON_PATH = REPORTS_DIR / "fractal0_price_entry_mechanics.json"
REPORT_ROWS_PATH = REPORTS_DIR / "fractal0_price_entry_mechanics_rows.csv"


@dataclasses.dataclass(frozen=True)
class Fractal0EntryMechanicsConfig:
    experiment: str = "fractal0_price_entry_mechanics"
    research_level: str = "search"
    initial_lifecycle_status: str = "research_scan"
    lifecycle_if_gate_pass: str = "research_hypothesis"
    origin_bias: str = "post_mortem"
    research_priority: str = "high"
    allowed_max_verdict: str = "research_only"
    verdict_if_gate_pass: str = "research_only"
    verdict_if_gate_fail: str = "diagnostic_only"
    entry_mechanics: tuple[str, ...] = ("retest_zone",)
    entry_price_modes: tuple[str, ...] = ("limit_at_fractal0", "zone_edge")
    zone_width_atr: tuple[float, ...] = (0.0, 0.25, 0.5)
    max_fill_lag_bars: tuple[int, ...] = (3, 6)
    horizons: tuple[int, ...] = (3, 6, 12)
    spread_values: tuple[float, ...] = (0.0, 0.2, 0.4)
    side_rule: str = "direction = -fractal0.dir"
    first_order_eligible_bar_offset: int = 1
    primary_selection_split: str = "train_core"
    primary_eval_split: str = "val_stop"
    disclosure_splits: tuple[str, ...] = ("diagnostic_holdout", "low_n_disclosure")
    min_filled_events_total_train_core: int = 300
    min_filled_events_total_val_stop: int = 150
    min_filled_events_per_year_val_stop: int = 30
    min_years_or_windows_val_stop: int = 3
    max_no_fill_rate_val_stop: float = 0.70
    canonical_spread: float = 0.2
    stress_spread: float = 0.4
    canonical_favorable_to_adverse_ratio_min: float = 1.05
    stress_favorable_to_adverse_ratio_min: float = 0.95
    ratio_without_best_year_min: float = 0.95
    prior_search_budget_lower_bound: int = 76


CONFIG = Fractal0EntryMechanicsConfig()


def parse_fractal0(value: object) -> dict | None:
    parts = str(value).split(":")
    if len(parts) < 23:
        return None
    try:
        return {
            "time": int(float(parts[0])),
            "price": float(parts[1]),
            "direction": int(float(parts[2])),
            "shift": int(float(parts[22])),
        }
    except (TypeError, ValueError):
        return None


def trade_side_from_fractal_direction(direction: object) -> str | None:
    try:
        value = float(direction)
    except (TypeError, ValueError):
        return None
    if math.isnan(value) or value == 0:
        return None
    return "SELL" if value > 0 else "BUY"


def _current_search_budget() -> int:
    return (
        len(CONFIG.entry_mechanics)
        * len(CONFIG.entry_price_modes)
        * len(CONFIG.zone_width_atr)
        * len(CONFIG.max_fill_lag_bars)
        * len(CONFIG.horizons)
        * len(CONFIG.spread_values)
    )


def fractal0_entry_config() -> dict[str, object]:
    config = dataclasses.asdict(CONFIG)
    for key in (
        "entry_mechanics",
        "entry_price_modes",
        "zone_width_atr",
        "max_fill_lag_bars",
        "horizons",
        "spread_values",
        "disclosure_splits",
    ):
        config[key] = list(config[key])
    current = _current_search_budget()
    config["current_search_budget"] = current
    config["cumulative_search_budget_status"] = "lower_bound_disclosed"
    config["cumulative_search_budget_lower_bound"] = CONFIG.prior_search_budget_lower_bound + current
    config["locked_test"] = "not_opened"
    return config


def audit_side_contract(rows: pd.DataFrame) -> dict:
    directions = pd.to_numeric(rows.get("fractal0_direction"), errors="coerce").dropna().astype(int)
    counts = {str(key): int(value) for key, value in directions.value_counts().sort_index().items()}
    return {
        "status": "PASS" if set(counts).issubset({"-1", "1"}) and counts else "FAIL",
        "direction_counts": counts,
        "required_before_research_only": True,
        "side_rule": CONFIG.side_rule,
        "note": "Project contract: direction = -fractal0.dir; -1 -> BUY, 1 -> SELL.",
    }
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_price_entry_mechanics.py -q
```

Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_fractal0_price_entry_mechanics.py tests/test_fractal0_price_entry_mechanics.py
git commit -m "Add fractal0 entry mechanics oracle config"
```

---

### Task 2: First Eligible Time, Fill Resolver, Entry-Based Targets

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`
- Modify: `tests/test_fractal0_price_entry_mechanics.py`

**Interfaces:**
- Consumes: `parse_fractal0`, `trade_side_from_fractal_direction`, `Fractal0EntryMechanicsConfig`
- Produces: `first_order_eligible_index(signal_time, ohlc, offset) -> int | None`
- Produces: `resolve_retest_zone_fill(...) -> dict`
- Produces: `compute_future_updn_from_fill(...) -> tuple[float, float]`
- Produces: `build_retest_rows(...) -> pd.DataFrame`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_fractal0_price_entry_mechanics.py`:

```python
def _ohlc_frame():
    return runner.next_open.prepare_ohlc(pd.DataFrame({
        "time": [
            "2021.01.01 10:00",
            "2021.01.01 11:00",
            "2021.01.01 12:00",
            "2021.01.01 13:00",
            "2021.01.01 14:00",
        ],
        "open": [101.0, 102.0, 100.5, 103.0, 104.0],
        "high": [102.0, 103.0, 101.0, 106.0, 105.0],
        "low": [100.0, 101.0, 99.75, 102.0, 103.0],
    }))


def test_first_order_eligible_index_skips_first_bar_after_signal_time():
    ohlc = _ohlc_frame()

    idx = runner.first_order_eligible_index(
        signal_time=pd.Timestamp("2021-01-01 10:00"),
        ohlc=ohlc,
        offset=1,
    )

    assert idx == 2


def test_limit_at_fractal0_requires_level_cross():
    fill = runner.resolve_retest_zone_fill(
        signal_time=pd.Timestamp("2021-01-01 10:00"),
        fractal0_price=100.0,
        atr=2.0,
        zone_width_atr=0.25,
        max_fill_lag_bars=3,
        entry_price_mode="limit_at_fractal0",
        ohlc=_ohlc_frame(),
    )

    assert fill["filled"] is True
    assert fill["fill_time"] == pd.Timestamp("2021-01-01 12:00")
    assert fill["entry_price"] == 100.0


def test_zone_edge_uses_reachable_edge_when_center_not_crossed():
    fill = runner.resolve_retest_zone_fill(
        signal_time=pd.Timestamp("2021-01-01 10:00"),
        fractal0_price=100.0,
        atr=2.0,
        zone_width_atr=0.25,
        max_fill_lag_bars=3,
        entry_price_mode="zone_edge",
        ohlc=_ohlc_frame(),
    )

    assert fill["filled"] is True
    assert fill["entry_price"] == 100.0

    edge_fill = runner.resolve_retest_zone_fill(
        signal_time=pd.Timestamp("2021-01-01 10:00"),
        fractal0_price=99.5,
        atr=2.0,
        zone_width_atr=0.25,
        max_fill_lag_bars=3,
        entry_price_mode="zone_edge",
        ohlc=_ohlc_frame(),
    )

    assert edge_fill["filled"] is True
    assert edge_fill["entry_price"] == 100.0


def test_compute_future_updn_from_fill_uses_fill_price_and_horizon():
    up, dn = runner.compute_future_updn_from_fill(
        fill_index=2,
        horizon=2,
        ohlc=_ohlc_frame(),
        entry_price=100.0,
    )

    assert up == 6.0
    assert dn == 0.25


def test_build_retest_rows_adds_fill_and_target_columns_without_trade_exit():
    rows = pd.DataFrame({
        "time": ["2021.01.01 10:00"],
        "ATR": [2.0],
        "fractal0": ["1609491600:100.0:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.0:2"],
    })

    out = runner.build_retest_rows(
        rows,
        _ohlc_frame(),
        zone_width_atr=0.25,
        max_fill_lag_bars=3,
        entry_price_mode="limit_at_fractal0",
        horizons=(1, 2),
    )

    assert out.loc[0, "side"] == "SELL"
    assert bool(out.loc[0, "filled"]) is True
    assert out.loc[0, "target_entry_up_1"] == 1.0
    assert out.loc[0, "target_entry_dn_1"] == 0.25
    assert out.loc[0, "target_entry_up_2"] == 6.0
    assert out.loc[0, "target_entry_dn_2"] == 0.25
    assert "pnl_price" not in out.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_price_entry_mechanics.py::test_first_order_eligible_index_skips_first_bar_after_signal_time -q
```

Expected: FAIL with missing `first_order_eligible_index`.

- [ ] **Step 3: Implement fill and target helpers**

Append to `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`:

```python
def parse_project_time(value: object) -> pd.Timestamp:
    return next_open.parse_project_time(value)


def _safe_float(value: object) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out


def first_order_eligible_index(signal_time: pd.Timestamp, ohlc: pd.DataFrame, offset: int) -> int | None:
    if pd.isna(signal_time):
        return None
    times = ohlc["parsed_time"].to_numpy()
    first_after_signal = int(times.searchsorted(signal_time.to_datetime64(), side="right"))
    idx = first_after_signal + int(offset)
    return idx if idx < len(ohlc) else None


def _reachable_zone_entry_price(low: float, high: float, center: float, lower: float, upper: float) -> float | None:
    if low <= center <= high:
        return float(center)
    if high < lower or low > upper:
        return None
    reachable_lower = max(low, lower)
    reachable_upper = min(high, upper)
    if reachable_lower > reachable_upper:
        return None
    if high < center:
        return float(reachable_upper)
    if low > center:
        return float(reachable_lower)
    return float(center)


def resolve_retest_zone_fill(
    signal_time: pd.Timestamp,
    fractal0_price: float,
    atr: float,
    zone_width_atr: float,
    max_fill_lag_bars: int,
    entry_price_mode: str,
    ohlc: pd.DataFrame,
) -> dict:
    if pd.isna(signal_time) or not np.isfinite(fractal0_price) or not np.isfinite(atr) or atr <= 0:
        return {"filled": False, "fill_time": pd.NaT, "fill_index": None, "fill_lag_bars": None, "entry_price": np.nan}
    start = first_order_eligible_index(signal_time, ohlc, CONFIG.first_order_eligible_bar_offset)
    if start is None:
        return {"filled": False, "fill_time": pd.NaT, "fill_index": None, "fill_lag_bars": None, "entry_price": np.nan}

    zone_width = float(zone_width_atr) * float(atr)
    center = float(fractal0_price)
    lower = center - zone_width
    upper = center + zone_width
    times = ohlc["parsed_time"].to_numpy()
    end = min(start + int(max_fill_lag_bars), len(ohlc))

    for pos in range(start, end):
        high = float(ohlc.iloc[pos]["high"])
        low = float(ohlc.iloc[pos]["low"])
        entry_price = None
        if entry_price_mode == "limit_at_fractal0":
            entry_price = center if low <= center <= high else None
        elif entry_price_mode == "zone_edge":
            entry_price = _reachable_zone_entry_price(low, high, center, lower, upper)
        else:
            raise ValueError(f"Unknown entry_price_mode: {entry_price_mode}")
        if entry_price is not None:
            return {
                "filled": True,
                "fill_time": pd.Timestamp(times[pos]),
                "fill_index": int(pos),
                "fill_lag_bars": int(pos - start + 1),
                "entry_price": float(entry_price),
            }

    return {"filled": False, "fill_time": pd.NaT, "fill_index": None, "fill_lag_bars": None, "entry_price": np.nan}


def compute_future_updn_from_fill(
    fill_index: int,
    horizon: int,
    ohlc: pd.DataFrame,
    entry_price: float,
) -> tuple[float, float]:
    end = int(fill_index) + int(horizon)
    if end > len(ohlc):
        return np.nan, np.nan
    window = ohlc.iloc[int(fill_index):end]
    up = max(float(window["high"].max()) - float(entry_price), 0.0)
    dn = max(float(entry_price) - float(window["low"].min()), 0.0)
    return float(np.round(up, 10)), float(np.round(dn, 10))


def build_retest_rows(
    df: pd.DataFrame,
    ohlc: pd.DataFrame,
    zone_width_atr: float,
    max_fill_lag_bars: int,
    entry_price_mode: str,
    horizons: tuple[int, ...],
) -> pd.DataFrame:
    out = df.copy().reset_index(drop=True)
    parsed = out["fractal0"].map(parse_fractal0)
    out["signal_time"] = out["time"].map(parse_project_time)
    out["fractal0_price"] = parsed.map(lambda item: item["price"] if item else np.nan)
    out["fractal0_direction"] = parsed.map(lambda item: item["direction"] if item else np.nan)
    out["side_rule"] = CONFIG.side_rule
    out["side"] = out["fractal0_direction"].map(trade_side_from_fractal_direction)
    out["entry_price_mode"] = entry_price_mode
    out["zone_width_atr"] = float(zone_width_atr)
    out["max_fill_lag_bars"] = int(max_fill_lag_bars)
    out["filled"] = False
    out["fill_time"] = pd.NaT
    out["fill_index"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
    out["fill_lag_bars"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
    out["entry_price"] = np.nan

    for horizon in horizons:
        out[f"target_entry_up_{horizon}"] = np.nan
        out[f"target_entry_dn_{horizon}"] = np.nan
        out[f"target_entry_log_ratio_{horizon}"] = np.nan
        out[f"has_full_h{horizon}"] = False

    for idx, row in out.iterrows():
        fill = resolve_retest_zone_fill(
            signal_time=row["signal_time"],
            fractal0_price=_safe_float(row["fractal0_price"]),
            atr=_safe_float(row.get("ATR")),
            zone_width_atr=zone_width_atr,
            max_fill_lag_bars=max_fill_lag_bars,
            entry_price_mode=entry_price_mode,
            ohlc=ohlc,
        )
        out.at[idx, "filled"] = bool(fill["filled"])
        out.at[idx, "fill_time"] = fill["fill_time"]
        out.at[idx, "entry_price"] = fill["entry_price"]
        if fill["fill_index"] is not None:
            out.at[idx, "fill_index"] = int(fill["fill_index"])
            out.at[idx, "fill_lag_bars"] = int(fill["fill_lag_bars"])

        if not fill["filled"]:
            continue
        for horizon in horizons:
            up, dn = compute_future_updn_from_fill(
                fill_index=int(fill["fill_index"]),
                horizon=int(horizon),
                ohlc=ohlc,
                entry_price=float(fill["entry_price"]),
            )
            if not np.isfinite(up) or not np.isfinite(dn):
                continue
            out.at[idx, f"has_full_h{horizon}"] = True
            out.at[idx, f"target_entry_up_{horizon}"] = up
            out.at[idx, f"target_entry_dn_{horizon}"] = dn
            out.at[idx, f"target_entry_log_ratio_{horizon}"] = float(next_open.safe_log_ratio(np.array([up]), np.array([dn]))[0])

    return out
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_price_entry_mechanics.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_fractal0_price_entry_mechanics.py tests/test_fractal0_price_entry_mechanics.py
git commit -m "Add fractal0 retest oracle targets"
```

---

### Task 3: MFE Oracle Metrics And Gate

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`
- Modify: `tests/test_fractal0_price_entry_mechanics.py`

**Interfaces:**
- Consumes: `build_retest_rows`
- Produces: `compute_oracle_mfe_rows(rows, horizon, spread) -> pd.DataFrame`
- Produces: `summarize_mfe_metrics(events) -> dict`
- Produces: `research_gate(selected_train_summary, eval_summary, side_contract_audit) -> dict`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_fractal0_price_entry_mechanics.py`:

```python
def test_compute_oracle_mfe_rows_uses_favorable_and_adverse_not_pnl():
    rows = pd.DataFrame({
        "filled": [True, True],
        "side": ["BUY", "SELL"],
        "target_entry_up_3": [3.0, 1.0],
        "target_entry_dn_3": [1.0, 4.0],
        "time": ["2021.01.01 10:00", "2021.01.02 10:00"],
    })

    events = runner.compute_oracle_mfe_rows(rows, horizon=3, spread=0.2)

    assert events.loc[0, "oracle_favorable_move_after_cost"] == 2.8
    assert events.loc[0, "oracle_adverse_move"] == 1.0
    assert events.loc[1, "oracle_favorable_move_after_cost"] == 3.8
    assert events.loc[1, "oracle_adverse_move"] == 1.0
    assert "pnl_price" not in events.columns
    assert "pf" not in events.columns


def test_summarize_mfe_metrics_reports_ratio_and_no_fill_context():
    events = pd.DataFrame({
        "oracle_favorable_move_after_cost": [2.0, -0.1, 3.0, 0.5],
        "oracle_adverse_move": [1.0, 2.0, 1.0, 0.5],
        "time": pd.to_datetime(["2021-01-01", "2021-02-01", "2022-01-01", "2023-01-01"]),
    })

    summary = runner.summarize_mfe_metrics(events, rows_total=10, rows_filled=4)

    assert summary["filled_events"] == 4
    assert summary["no_fill_rate"] == 0.6
    assert summary["favorable_sum_after_cost"] == 5.4
    assert summary["adverse_sum"] == 4.5
    assert round(summary["favorable_to_adverse_ratio"], 6) == round(5.4 / 4.5, 6)
    assert summary["active_years"] == 3


def test_research_gate_ignores_zero_spread_and_requires_side_contract_pass():
    selected_train = {"spread": 0.2, "favorable_to_adverse_ratio": 1.20, "filled_events": 500}
    eval_summary = {
        "spread": 0.2,
        "filled_events": 200,
        "filled_events_per_year_min": 40,
        "active_years": 3,
        "no_fill_rate": 0.50,
        "favorable_to_adverse_ratio": 1.08,
        "ratio_without_best_year": 1.00,
        "stress_favorable_to_adverse_ratio": 0.96,
    }
    side_contract_audit = {"status": "PASS"}

    gate = runner.research_gate(selected_train, eval_summary, side_contract_audit)

    assert gate["passes"] is True
    assert gate["verdict_if_pass"] == "research_only"
    assert gate["lifecycle_if_pass"] == "research_hypothesis"


def test_research_gate_blocks_failed_side_contract():
    gate = runner.research_gate(
        {"spread": 0.2, "favorable_to_adverse_ratio": 9.0, "filled_events": 999},
        {
            "spread": 0.2,
            "filled_events": 999,
            "filled_events_per_year_min": 999,
            "active_years": 9,
            "no_fill_rate": 0.01,
            "favorable_to_adverse_ratio": 9.0,
            "ratio_without_best_year": 9.0,
            "stress_favorable_to_adverse_ratio": 9.0,
        },
        {"status": "FAIL"},
    )

    assert gate["passes"] is False
    assert gate["checks"]["side_contract_status"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_price_entry_mechanics.py::test_compute_oracle_mfe_rows_uses_favorable_and_adverse_not_pnl -q
```

Expected: FAIL with missing `compute_oracle_mfe_rows`.

- [ ] **Step 3: Implement MFE metrics and gate**

Append to `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`:

```python
def compute_oracle_mfe_rows(rows: pd.DataFrame, horizon: int, spread: float) -> pd.DataFrame:
    active = rows.loc[rows["filled"].astype(bool)].copy()
    up_col = f"target_entry_up_{horizon}"
    dn_col = f"target_entry_dn_{horizon}"
    active = active.loc[active[up_col].notna() & active[dn_col].notna()].copy()
    buy_mask = active["side"] == "BUY"
    sell_mask = active["side"] == "SELL"
    active["oracle_favorable_move_after_cost"] = np.nan
    active["oracle_adverse_move"] = np.nan
    active.loc[buy_mask, "oracle_favorable_move_after_cost"] = pd.to_numeric(active.loc[buy_mask, up_col], errors="coerce") - float(spread)
    active.loc[buy_mask, "oracle_adverse_move"] = pd.to_numeric(active.loc[buy_mask, dn_col], errors="coerce")
    active.loc[sell_mask, "oracle_favorable_move_after_cost"] = pd.to_numeric(active.loc[sell_mask, dn_col], errors="coerce") - float(spread)
    active.loc[sell_mask, "oracle_adverse_move"] = pd.to_numeric(active.loc[sell_mask, up_col], errors="coerce")
    active["horizon"] = int(horizon)
    active["spread"] = float(spread)
    return active.reset_index(drop=True)


def _ratio_without_best_year(events: pd.DataFrame) -> float | None:
    if events.empty:
        return None
    years = pd.to_datetime(events["time"]).dt.year
    yearly = events.groupby(years)["oracle_favorable_move_after_cost"].sum()
    if len(yearly) <= 1:
        return None
    best_year = yearly.idxmax()
    reduced = events.loc[years != best_year]
    return summarize_mfe_metrics(reduced, rows_total=len(reduced), rows_filled=len(reduced))["favorable_to_adverse_ratio"]


def summarize_mfe_metrics(events: pd.DataFrame, rows_total: int, rows_filled: int) -> dict:
    if events.empty:
        return {
            "rows_total": int(rows_total),
            "filled_events": int(rows_filled),
            "no_fill_rate": 1.0 if rows_total else 0.0,
            "favorable_sum_after_cost": 0.0,
            "adverse_sum": 0.0,
            "favorable_to_adverse_ratio": None,
            "active_years": 0,
            "filled_events_per_year_min": 0,
            "ratio_without_best_year": None,
        }
    favorable = pd.to_numeric(events["oracle_favorable_move_after_cost"], errors="coerce").fillna(0.0)
    adverse = pd.to_numeric(events["oracle_adverse_move"], errors="coerce").fillna(0.0)
    favorable_sum = float(favorable.sum())
    adverse_sum = float(adverse.sum())
    years = pd.to_datetime(events["time"]).dt.year
    per_year = events.groupby(years).size()
    return {
        "rows_total": int(rows_total),
        "filled_events": int(rows_filled),
        "no_fill_rate": float(1.0 - rows_filled / rows_total) if rows_total else 0.0,
        "favorable_sum_after_cost": float(np.round(favorable_sum, 10)),
        "adverse_sum": float(np.round(adverse_sum, 10)),
        "favorable_to_adverse_ratio": float(favorable_sum / adverse_sum) if adverse_sum > 0 else None,
        "active_years": int(per_year.size),
        "filled_events_per_year_min": int(per_year.min()) if len(per_year) else 0,
        "ratio_without_best_year": _ratio_without_best_year(events),
    }


def research_gate(selected_train_summary: dict, eval_summary: dict, side_contract_audit: dict) -> dict:
    checks = {
        "side_contract_status": side_contract_audit.get("status") == "PASS",
        "selected_on_train_core": selected_train_summary.get("spread") == CONFIG.canonical_spread,
        "zero_spread_not_gate": eval_summary.get("spread") != 0.0,
        "min_filled_events_total_train_core": selected_train_summary.get("filled_events", 0) >= CONFIG.min_filled_events_total_train_core,
        "min_filled_events_total_val_stop": eval_summary.get("filled_events", 0) >= CONFIG.min_filled_events_total_val_stop,
        "min_filled_events_per_year_val_stop": eval_summary.get("filled_events_per_year_min", 0) >= CONFIG.min_filled_events_per_year_val_stop,
        "min_years_or_windows_val_stop": eval_summary.get("active_years", 0) >= CONFIG.min_years_or_windows_val_stop,
        "max_no_fill_rate_val_stop": eval_summary.get("no_fill_rate", 1.0) <= CONFIG.max_no_fill_rate_val_stop,
        "canonical_favorable_to_adverse_ratio": (
            eval_summary.get("favorable_to_adverse_ratio") is not None
            and eval_summary["favorable_to_adverse_ratio"] >= CONFIG.canonical_favorable_to_adverse_ratio_min
        ),
        "stress_favorable_to_adverse_ratio": (
            eval_summary.get("stress_favorable_to_adverse_ratio") is not None
            and eval_summary["stress_favorable_to_adverse_ratio"] >= CONFIG.stress_favorable_to_adverse_ratio_min
        ),
        "ratio_without_best_year": (
            eval_summary.get("ratio_without_best_year") is not None
            and eval_summary["ratio_without_best_year"] >= CONFIG.ratio_without_best_year_min
        ),
    }
    return {
        "passes": all(checks.values()),
        "checks": checks,
        "verdict_if_pass": CONFIG.verdict_if_gate_pass,
        "lifecycle_if_pass": CONFIG.lifecycle_if_gate_pass,
        "verdict_if_fail": CONFIG.verdict_if_gate_fail,
        "forbidden_terms": ["PnL", "PF", "profitable", "tradable", "live-ready"],
    }
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_price_entry_mechanics.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_fractal0_price_entry_mechanics.py tests/test_fractal0_price_entry_mechanics.py
git commit -m "Add fractal0 MFE oracle gate"
```

---

### Task 4: Full Oracle Runner, Selection Roles, Report Contract

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`
- Modify: `tests/test_fractal0_price_entry_mechanics.py`

**Interfaces:**
- Consumes: Tasks 1-3 helpers
- Produces: `run_fractal0_entry_mechanics(output_path, rows_path) -> dict`
- Produces: CLI flag `--fractal0-entry-mechanics`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_fractal0_price_entry_mechanics.py`:

```python
def test_select_best_rule_uses_train_core_only_and_ignores_zero_spread():
    summary = {
        "train_core": {
            "rule_a_spread_0.0": {"spread": 0.0, "favorable_to_adverse_ratio": 99.0},
            "rule_b_spread_0.2": {"spread": 0.2, "favorable_to_adverse_ratio": 1.10},
            "rule_c_spread_0.2": {"spread": 0.2, "favorable_to_adverse_ratio": 1.20},
        },
        "val_stop": {
            "rule_z_spread_0.2": {"spread": 0.2, "favorable_to_adverse_ratio": 2.00},
        },
    }

    selected = runner.select_best_train_rule(summary)

    assert selected["key"] == "rule_c_spread_0.2"
    assert selected["selection_split"] == "train_core"


def test_validate_report_requires_research_first_fields():
    report = {"experiment": "fractal0_price_entry_mechanics"}

    missing = runner.validate_report(report)

    assert "verdict" in missing
    assert "lifecycle_status" in missing
    assert "allowed_max_verdict" in missing
    assert "cumulative_search_budget_lower_bound" in missing
    assert "target_contract" in missing
    assert "execution_contract" in missing
    assert "forbidden_interpretations" in missing


def test_build_arg_parser_accepts_fractal0_entry_mechanics():
    parser = runner.build_arg_parser()

    args = parser.parse_args(["--fractal0-entry-mechanics"])

    assert args.fractal0_entry_mechanics is True
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_price_entry_mechanics.py::test_select_best_rule_uses_train_core_only_and_ignores_zero_spread -q
```

Expected: FAIL with missing `select_best_train_rule`.

- [ ] **Step 3: Implement runner contract**

Append to `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`:

```python
REPORT_REQUIRED_FIELDS = (
    "experiment",
    "verdict",
    "lifecycle_status",
    "research_level",
    "origin_bias",
    "research_priority",
    "allowed_max_verdict",
    "current_search_budget",
    "cumulative_search_budget_lower_bound",
    "cumulative_search_budget_status",
    "target_contract",
    "execution_contract",
    "forbidden_interpretations",
    "side_contract_audit",
    "oracle_summary",
    "selected_train_rule",
    "research_gate",
)


def validate_report(report: dict) -> list[str]:
    return [field for field in REPORT_REQUIRED_FIELDS if field not in report]


def select_best_train_rule(oracle_summary: dict) -> dict:
    train = oracle_summary.get(CONFIG.primary_selection_split, {})
    candidates = {
        key: value for key, value in train.items()
        if value.get("spread") == CONFIG.canonical_spread
    }
    if not candidates:
        return {"key": None, "selection_split": CONFIG.primary_selection_split, "summary": None}
    key = max(
        candidates,
        key=lambda item: candidates[item].get("favorable_to_adverse_ratio") or -1.0,
    )
    return {"key": key, "selection_split": CONFIG.primary_selection_split, "summary": candidates[key]}


def _rows_output_view(rows: pd.DataFrame) -> pd.DataFrame:
    base_columns = [
        "split_name",
        "time",
        "signal_time",
        "fractal0_price",
        "fractal0_direction",
        "side_rule",
        "side",
        "entry_price_mode",
        "zone_width_atr",
        "max_fill_lag_bars",
        "filled",
        "fill_time",
        "fill_lag_bars",
        "entry_price",
    ]
    target_columns = [
        column for column in rows.columns
        if column.startswith("target_entry_") or column.startswith("has_full_h")
    ]
    return rows.loc[:, [column for column in base_columns + target_columns if column in rows.columns]].copy()


def _rule_key(entry_price_mode: str, zone_width: float, fill_lag: int, horizon: int, spread: float) -> str:
    return (
        f"entry_{entry_price_mode}"
        f"_zone_{zone_width}"
        f"_lag_{fill_lag}"
        f"_h{horizon}"
        f"_spread_{spread}"
    )


def run_fractal0_entry_mechanics(
    output_path: Path = REPORT_JSON_PATH,
    rows_path: Path = REPORT_ROWS_PATH,
) -> dict:
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ohlc = next_open.load_ohlc()
    split_frames = next_open.load_research_splits()

    all_rows = []
    oracle_summary: dict[str, dict] = {}
    side_contract_audit = {"status": "FAIL", "required_before_research_only": True}

    for split_name, frame in split_frames.items():
        split_summary: dict[str, dict] = {}
        for entry_price_mode in CONFIG.entry_price_modes:
            for zone_width in CONFIG.zone_width_atr:
                for fill_lag in CONFIG.max_fill_lag_bars:
                    rebuilt = build_retest_rows(
                        frame,
                        ohlc,
                        zone_width_atr=float(zone_width),
                        max_fill_lag_bars=int(fill_lag),
                        entry_price_mode=entry_price_mode,
                        horizons=CONFIG.horizons,
                    )
                    rebuilt["split_name"] = split_name
                    all_rows.append(_rows_output_view(rebuilt))
                    if split_name == CONFIG.primary_selection_split:
                        side_contract_audit = audit_side_contract(rebuilt)
                    rows_total = len(rebuilt)
                    rows_filled = int(rebuilt["filled"].astype(bool).sum())
                    for horizon in CONFIG.horizons:
                        for spread in CONFIG.spread_values:
                            events = compute_oracle_mfe_rows(rebuilt, horizon=int(horizon), spread=float(spread))
                            key = _rule_key(entry_price_mode, float(zone_width), int(fill_lag), int(horizon), float(spread))
                            summary = summarize_mfe_metrics(events, rows_total=rows_total, rows_filled=rows_filled)
                            summary.update(
                                {
                                    "entry_price_mode": entry_price_mode,
                                    "zone_width_atr": float(zone_width),
                                    "max_fill_lag_bars": int(fill_lag),
                                    "horizon": int(horizon),
                                    "spread": float(spread),
                                    "side_rule": CONFIG.side_rule,
                                    "zero_spread_diagnostic_only": float(spread) == 0.0,
                                }
                            )
                            split_summary[key] = summary
        oracle_summary[split_name] = split_summary

    rows_df = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    rows_df.to_csv(rows_path, sep=";", index=False)
    selected_train_rule = select_best_train_rule(oracle_summary)
    eval_summary = {}
    if selected_train_rule["key"]:
        eval_key = selected_train_rule["key"]
        eval_summary = oracle_summary.get(CONFIG.primary_eval_split, {}).get(eval_key, {})
        stress_key = eval_key.replace(f"_spread_{CONFIG.canonical_spread}", f"_spread_{CONFIG.stress_spread}")
        stress = oracle_summary.get(CONFIG.primary_eval_split, {}).get(stress_key, {})
        eval_summary = dict(eval_summary)
        eval_summary["stress_favorable_to_adverse_ratio"] = stress.get("favorable_to_adverse_ratio")

    gate = research_gate(selected_train_rule.get("summary") or {}, eval_summary, side_contract_audit)
    verdict = gate["verdict_if_pass"] if gate["passes"] else gate["verdict_if_fail"]
    lifecycle = gate["lifecycle_if_pass"] if gate["passes"] else "exploratory_result"
    config = fractal0_entry_config()
    report = {
        "experiment": CONFIG.experiment,
        "verdict": verdict,
        "lifecycle_status": lifecycle,
        "research_level": CONFIG.research_level,
        "origin_bias": CONFIG.origin_bias,
        "research_priority": CONFIG.research_priority,
        "allowed_max_verdict": CONFIG.allowed_max_verdict,
        "current_search_budget": config["current_search_budget"],
        "cumulative_search_budget_lower_bound": config["cumulative_search_budget_lower_bound"],
        "cumulative_search_budget_status": config["cumulative_search_budget_status"],
        "target_contract": {
            "type": "MFE_MAE_after_fill_no_trade_exit",
            "future_derived_fields": [
                "target_entry_up_*",
                "target_entry_dn_*",
                "target_entry_log_ratio_*",
                "oracle_favorable_move_after_cost",
                "oracle_adverse_move",
            ],
            "forbidden_as_input": True,
        },
        "execution_contract": {
            "entry_mechanic": "retest_zone",
            "entry_price_modes": list(CONFIG.entry_price_modes),
            "first_order_eligible_bar_offset": CONFIG.first_order_eligible_bar_offset,
            "exit_contract": "none_in_this_stage",
            "metric_contract": "oracle_favorable_move_after_cost_not_pnl_not_pf",
        },
        "forbidden_interpretations": [
            "PnL",
            "PF",
            "прибыльно",
            "готово",
            "можно запускать",
            "live-ready",
            "tradable",
        ],
        "config": config,
        "preflight": {"ohlc": next_open.preflight_ohlc(ohlc), "locked_test": "not_opened"},
        "side_contract_audit": side_contract_audit,
        "oracle_summary": oracle_summary,
        "selected_train_rule": selected_train_rule,
        "research_gate": gate,
        "rows_path": str(rows_path),
        "started_at": started_at,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    missing = validate_report(report)
    if missing:
        report["verdict"] = "diagnostic_only"
        report["lifecycle_status"] = "exploratory_result"
        report["missing_report_fields"] = missing
    output_path.write_text(json.dumps(report, indent=2, default=str))
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fractal0-entry-mechanics", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.fractal0_entry_mechanics:
        report = run_fractal0_entry_mechanics()
        print({"verdict": report["verdict"], "json": str(REPORT_JSON_PATH), "rows": str(REPORT_ROWS_PATH)})
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_price_entry_mechanics.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Run smoke runner**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_fractal0_price_entry_mechanics.py --fractal0-entry-mechanics
```

Expected:

```text
{'verdict': 'diagnostic_only', 'json': '.../fractal0_price_entry_mechanics.json', 'rows': '.../fractal0_price_entry_mechanics_rows.csv'}
```

Expected verdict is `diagnostic_only` until side mapping is explicitly verified.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_fractal0_price_entry_mechanics.py tests/test_fractal0_price_entry_mechanics.py ML/reports/fractal0_price_entry_mechanics.json ML/reports/fractal0_price_entry_mechanics_rows.csv
git commit -m "Add fractal0 oracle preflight runner"
```

---

### Task 5: Docs, Report, Full Verification

**Files:**
- Create: `docs/ML/benchmark_fractal0_price_entry_mechanics.py.md`
- Create: `docs/reports/2026-07-10-fractal0-price-entry-mechanics.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `CHANGELOG.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes: JSON/CSV generated by Task 4
- Produces: final stage report with research-first disclosure

- [ ] **Step 1: Create module documentation**

Create `docs/ML/benchmark_fractal0_price_entry_mechanics.py.md`:

```markdown
# benchmark_fractal0_price_entry_mechanics.py

## Назначение

Диагностический runner для oracle-preflight входа через возврат цены к зоне
около `fractal0_price`.

## Команда

```bash
./.venv/bin/python ML/baseline/benchmark_fractal0_price_entry_mechanics.py --fractal0-entry-mechanics
```

## Входы

- `DATA/XAUUSD_H1_OHLC.csv`
- `DATA/Nero_XAUUSD_train_labeled.csv`
- `DATA/Nero_XAUUSD_validation_labeled.csv`
- `DATA/Nero_XAUUSD_test_labeled.csv`

## Выходы

- `ML/reports/fractal0_price_entry_mechanics.json`
- `ML/reports/fractal0_price_entry_mechanics_rows.csv`

## Ограничения

- `locked_test` не открывается.
- Verdict не выше `research_only`.
- `research_hypothesis` является lifecycle_status, а не verdict.
- Runner не считает PnL/PF, потому что exit contract не задан.
- `spread=0.00` только отладочный diagnostic и не участвует в gate.
- Сторона берётся из `fractal0.dir`, но polarity должна быть подтверждена
  отдельным sanity-check перед `research_only`.
```

- [ ] **Step 2: Create final report from artifact**

Create `docs/reports/2026-07-10-fractal0-price-entry-mechanics.md` after the full run. Use artifact values, not terminal logs:

```markdown
# Fractal0 Price Entry Mechanics Oracle-Preflight

> **Дата**: 2026-07-10
> **Статус**: Completed
> **Уровень**: поисковый
> **verdict**: точное значение `verdict` из `ML/reports/fractal0_price_entry_mechanics.json`
> **lifecycle_status**: точное значение `lifecycle_status` из `ML/reports/fractal0_price_entry_mechanics.json`
> **origin_bias**: `post_mortem`
> **allowed_max_verdict**: `research_only`

## Context

`next open after signal_time` был отклонён, но старый Up/Dn signal остаётся
сильным относительно `fractal0_price`. Этот этап проверяет другую механику:
вход только после возврата цены к зоне около `fractal0_price`.

## Research-First Disclosure

```text
verdict: exact JSON field report.verdict
lifecycle_status: exact JSON field report.lifecycle_status
origin_bias: post_mortem
research_priority: high
current_search_budget: 108 oracle configurations
cumulative_search_budget_lower_bound: 184
cumulative_search_budget_status: lower_bound_disclosed
next_probe_freeze: none until oracle gate passes
allowed_max_verdict: research_only
forbidden_interpretations: PnL, PF, прибыльно, готово, можно запускать, live-ready, tradable
```

## Execution Contract

- `first_order_eligible_bar_offset = 1`;
- entry price modes: `limit_at_fractal0`, `zone_edge`;
- no-fill сохраняется как отдельный исход;
- `spread=0.00` не участвует в gate;
- exit contract не задан, поэтому этап измеряет MFE/MAE potential, не сделку.

## Target Contract

Future-derived fields:

- `target_entry_up_*`;
- `target_entry_dn_*`;
- `target_entry_log_ratio_*`;
- `oracle_favorable_move_after_cost`;
- `oracle_adverse_move`.

Эти поля запрещены как input.

## Results

Заполнить из `ML/reports/fractal0_price_entry_mechanics.json`:

- selected train rule;
- val_stop result for selected rule;
- stress spread result;
- no-fill rate по годам и сторонам;
- разрезы BUY/SELL, fill lag buckets, zone width, horizon;
- side mapping audit;
- research gate.

## Conclusions

Если gate прошёл: записать `verdict=research_only`,
`lifecycle_status=research_hypothesis`, но не `candidate`.

Если gate не прошёл: записать `verdict=diagnostic_only` и закрыть или снизить
приоритет этой механики.

## Forbidden Interpretations

- нет PnL/PF;
- нет торгового вывода;
- нет `candidate`;
- нет причины открывать `locked_test`;
- нет MT4/live вывода;
- нельзя обучать модель в этом же этапе.
```

- [ ] **Step 3: Update roadmap and handoff**

Update `docs/superpowers/roadmap.md`:

```markdown
Статус: Completed. См. `docs/reports/2026-07-10-fractal0-price-entry-mechanics.md`.
```

Update `CONTEXT_HANDOFF.md` with:

```markdown
## Текущее состояние

Fractal0 price entry mechanics oracle-preflight завершён. Следующий шаг зависит
от `research_gate`:

- если PASS: оформить отдельный frozen probe-plan с зафиксированными
  entry/exit/side/target параметрами;
- если FAIL: закрыть retest-zone механику и решить, переходить ли к H6
  direction-inside-mask зацепке.
```

- [ ] **Step 4: Run verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_price_entry_mechanics.py -q
./.venv/bin/python -m pytest tests/ -q
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
git diff --check
git status --short
```

Expected:

```text
focused tests pass
full tests pass
Wiki is up to date. No gaps found.
git diff --check has no output
only intended files are modified
```

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_fractal0_price_entry_mechanics.py tests/test_fractal0_price_entry_mechanics.py docs/ML/benchmark_fractal0_price_entry_mechanics.py.md docs/reports/2026-07-10-fractal0-price-entry-mechanics.md docs/superpowers/roadmap.md CONTEXT_HANDOFF.md CHANGELOG.md wiki/research/fractal-stop-research.md wiki/index.md wiki/log.md wiki/REPO_integrity.md ML/reports/fractal0_price_entry_mechanics.json ML/reports/fractal0_price_entry_mechanics_rows.csv
git commit -m "Add fractal0 price entry mechanics oracle preflight"
```
