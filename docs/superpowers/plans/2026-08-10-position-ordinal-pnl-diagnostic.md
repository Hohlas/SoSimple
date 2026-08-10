# Position-Ordinal PnL Diagnostic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Определить, деградирует ли PF с ростом порядкового номера одновременно открытой позиции (ordinal) в MT5 max=64 пилоте.

**Architecture:** Загрузить events.csv всех 32 кандидатов из `multipos_pilot/max64/`, найти пары OPEN/CLOSE по ticket, извлечь `open_positions` из OPEN как ordinal. Сгруппировать сделки по ordinal (1, 2, 3, 4, 5+), посчитать PF агрегированно по всем кандидатам. Bootstrap по кандидатам (resampling с заменой) даст доверительные интервалы.

**Tech Stack:** Python 3, pytest, json. Без новых зависимостей.

## Global Constraints

- Максимальный вердикт: `DIAGNOSTIC_ONLY`.
- Не открывать `locked_test`, не выбирать winner, не интерпретировать PF/PnL как прибыльность.
- Не запускать MT5 tester. Использовать только сохранённые артефакты `multipos_pilot/max64/`.
- Все числа отчёта должны сходиться с JSON/CSV артефактами (методология 16).
- Bootstrap: `n_bootstrap=2000`, `seed=42`. Candidate-level resampling (не block bootstrap — см. ограничения).
- Порог группировки: ordinal 1, 2, 3, 4, 5+ (предзадано до анализа).

## Методология

Применимые разделы:

| Раздел | Что даёт |
|--------|----------|
| [A5-post-mortem-diagnostics.md](../../methodology/A5-post-mortem-diagnostics.md) | Шаг 1: декомпозиция PnL по категории (ordinal). Шаг 4: проверка ранжирования (монотонность PF по ordinal). |
| [11-robustness.md](../../methodology/11-robustness.md) | Пункт 3: sequential simulation при ограничении позиций. Пункт 9: candidate-level bootstrap (ресэмплинг кандидатов, не block bootstrap — сделки внутри кандидата зависимы, но кандидаты независимы). |
| [13b-mt5-execution-parity.md](../../methodology/13b-mt5-execution-parity.md) | Описание event log, `open_positions`, `ticket`, OPEN/CLOSE событий. |
| [16-reporting-audit.md](../../methodology/16-reporting-audit.md) | Сверка отчёт ↔ JSON-артефакт, disclosure ограничений. |

Неприменимые разделы:
- 12-backtest-costs: cost model не входит в scope (отдельная задача).
- 09-validation-freeze, 10-frozen-test: нет выбора winner.

Обязательные проверки:
- Декомпозиция по годам для каждого ordinal (A5 шаг 1).
- Bootstrap CI по кандидатам (11-robustness, пункт 9 — candidate-level resampling).
- Disclosure: сколько сделок в каждом ordinal, сколько кандидатов участвует.

Критерий завершения:
- JSON-артефакт сохранён в `ML/reports/mt5_execution_loop/diagnostics/position_ordinal_pnl.json`.
- Все тесты проходят.
- Числа в отчёте (плане) совпадают с JSON.

## File Structure

| Файл | Роль |
|------|------|
| `ML/baseline/position_ordinal_analysis.py` | Загрузка events, парсинг сделок, вычисление PF по ordinal, bootstrap, вывод JSON |
| `tests/test_position_ordinal_analysis.py` | Unit-тесты парсинга, PF, bootstrap, smoke на реальных данных |
| `ML/reports/mt5_execution_loop/diagnostics/position_ordinal_pnl.json` | Выходной артефакт |

---

### Task 1: Парсинг сделок из events.csv

**Files:**
- Create: `ML/baseline/position_ordinal_analysis.py`
- Create: `tests/test_position_ordinal_analysis.py`

**Interfaces:**
- `parse_trades(events_path: str) -> list[dict]` — принимает путь к events.csv, возвращает список сделок.
- Каждая сделка: `{"ticket": str, "side": str, "ordinal": int, "profit": float, "year": int}`.
- `ordinal` = `open_positions` из OPEN-события. Если OPEN не найден — сделка пропускается.
- `year` извлекается из колонки `time` OPEN-события (формат `YYYY.MM.DD HH:MM`).

**Методика:** 13b (event log contract), A5 шаг 1 (декомпозиция).

- [ ] **Step 1: Write failing tests**

```python
# tests/test_position_ordinal_analysis.py
import pytest
from ML.baseline.position_ordinal_analysis import parse_trades


def _write_events(path, lines):
    header = "event;time;ticket;side;profit;open_positions"
    path.write_text(header + "\n" + "\n".join(lines))


def test_parse_trades_matches_open_close_by_ticket(tmp_path):
    p = tmp_path / "events.csv"
    _write_events(p, [
        "OPEN;2021.01.04 11:00;2;SELL;0.0;2",
        "CLOSE;2021.01.04 15:00;2;SELL;-56.9;1",
        "OPEN;2021.01.04 16:00;5;SELL;0.0;2",
        "CLOSE;2021.01.05 03:00;5;SELL;-44.3;1",
    ])
    trades = parse_trades(str(p))
    assert len(trades) == 2
    assert trades[0]["ticket"] == "2"
    assert trades[0]["ordinal"] == 2
    assert trades[0]["profit"] == -56.9
    assert trades[0]["side"] == "SELL"
    assert trades[0]["year"] == 2021
    assert trades[1]["ticket"] == "5"
    assert trades[1]["ordinal"] == 2
    assert trades[1]["profit"] == -44.3
    assert trades[1]["year"] == 2021


def test_parse_trades_skips_close_without_open(tmp_path):
    p = tmp_path / "events.csv"
    _write_events(p, [
        "CLOSE;2021.01.04 15:00;99;BUY;100.0;0",
    ])
    trades = parse_trades(str(p))
    assert trades == []


def test_parse_trades_ignores_non_open_close_events(tmp_path):
    p = tmp_path / "events.csv"
    _write_events(p, [
        "INIT;2021.01.04 01:00;;;-1;0",
        "ORDER_PLACED;2021.01.04 10:00;2;SELL;0.0;1",
        "ML_EVAL;2021.01.04 11:00;2;SELL;0.0;1",
        "OPEN;2021.01.04 11:00;2;SELL;0.0;1",
        "CLOSE;2021.01.04 15:00;2;SELL;-56.9;0",
    ])
    trades = parse_trades(str(p))
    assert len(trades) == 1
    assert trades[0]["ordinal"] == 1
    assert trades[0]["profit"] == -56.9
    assert trades[0]["year"] == 2021


def test_parse_trades_empty_file(tmp_path):
    p = tmp_path / "events.csv"
    _write_events(p, [])
    trades = parse_trades(str(p))
    assert trades == []


def test_parse_trades_extracts_year_from_open_time(tmp_path):
    p = tmp_path / "events.csv"
    _write_events(p, [
        "OPEN;2022.06.15 10:00;1;BUY;0.0;1",
        "CLOSE;2022.06.15 14:00;1;BUY;50.0;0",
    ])
    trades = parse_trades(str(p))
    assert len(trades) == 1
    assert trades[0]["year"] == 2022
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_position_ordinal_analysis.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ML.baseline.position_ordinal_analysis'`

- [ ] **Step 3: Implement parse_trades**

```python
# ML/baseline/position_ordinal_analysis.py
import csv
from pathlib import Path


def parse_trades(events_path):
    opens = {}
    closes = []
    with open(events_path, newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            event = row["event"]
            if event == "OPEN":
                opens[row["ticket"]] = (
                    int(row["open_positions"]),
                    row["side"],
                    int(row["time"][:4]),
                )
            elif event == "CLOSE":
                closes.append(
                    (row["ticket"], float(row["profit"]), row["side"])
                )
    trades = []
    for ticket, profit, side in closes:
        if ticket in opens:
            ordinal, _, year = opens[ticket]
            trades.append({
                "ticket": ticket,
                "side": side,
                "ordinal": ordinal,
                "profit": profit,
                "year": year,
            })
    return trades
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest tests/test_position_ordinal_analysis.py -v`
Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/position_ordinal_analysis.py tests/test_position_ordinal_analysis.py
git commit -m "feat: parse trade ordinals from MT5 max=64 events"
```

---

### Task 2: Вычисление PF по ordinal и по кандидату

**Files:**
- Modify: `ML/baseline/position_ordinal_analysis.py`
- Modify: `tests/test_position_ordinal_analysis.py`

**Interfaces:**
- `compute_pf(profits: list[float]) -> dict` — возвращает `{"pf": float, "n": int, "gross_profit": float, "gross_loss": float}`. PF = inf если gross_loss == 0 и gross_profit > 0; PF = 0.0 если gross_profit == 0.
- `analyze_candidate(trades: list[dict]) -> dict` — группирует сделки по ordinal (1, 2, 3, 4, 5+), считает PF в каждой группе. Возвращает `{"by_ordinal": {str(ordinal): {"pf", "n", "gross_profit", "gross_loss"}}, "n_trades": int}`.

**Методика:** A5 шаг 1 (декомпозиция PnL).

- [ ] **Step 1: Write failing tests**

Добавить в `tests/test_position_ordinal_analysis.py`:

```python
from ML.baseline.position_ordinal_analysis import compute_pf, analyze_candidate


def test_compute_pf_basic():
    result = compute_pf([100.0, -50.0, 200.0, -100.0])
    assert result["pf"] == pytest.approx(1.5)
    assert result["n"] == 4
    assert result["gross_profit"] == pytest.approx(300.0)
    assert result["gross_loss"] == pytest.approx(150.0)


def test_compute_pf_all_losses():
    result = compute_pf([-100.0, -50.0])
    assert result["pf"] == 0.0
    assert result["gross_profit"] == 0.0


def test_compute_pf_all_wins():
    result = compute_pf([100.0, 50.0])
    assert result["pf"] == float("inf")
    assert result["gross_loss"] == 0.0


def test_compute_pf_empty():
    result = compute_pf([])
    assert result["pf"] == 0.0
    assert result["n"] == 0


def test_analyze_candidate_groups_by_ordinal():
    trades = [
        {"ticket": "1", "side": "SELL", "ordinal": 1, "profit": 100.0},
        {"ticket": "2", "side": "SELL", "ordinal": 1, "profit": -50.0},
        {"ticket": "3", "side": "BUY", "ordinal": 2, "profit": 200.0},
        {"ticket": "4", "side": "BUY", "ordinal": 2, "profit": -100.0},
        {"ticket": "5", "side": "SELL", "ordinal": 3, "profit": -80.0},
        {"ticket": "6", "side": "SELL", "ordinal": 5, "profit": 150.0},
        {"ticket": "7", "side": "BUY", "ordinal": 7, "profit": -30.0},
    ]
    result = analyze_candidate(trades)
    assert result["n_trades"] == 7
    assert result["by_ordinal"]["1"]["pf"] == pytest.approx(2.0)
    assert result["by_ordinal"]["1"]["n"] == 2
    assert result["by_ordinal"]["2"]["pf"] == pytest.approx(2.0)
    assert result["by_ordinal"]["2"]["n"] == 2
    assert result["by_ordinal"]["3"]["pf"] == 0.0
    assert result["by_ordinal"]["3"]["n"] == 1
    assert "5+" in result["by_ordinal"]
    assert result["by_ordinal"]["5+"]["n"] == 2
    assert result["by_ordinal"]["5+"]["pf"] == pytest.approx(5.0)
    assert "4" not in result["by_ordinal"]


def test_analyze_candidate_empty():
    result = analyze_candidate([])
    assert result["n_trades"] == 0
    assert result["by_ordinal"] == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_position_ordinal_analysis.py::test_compute_pf_basic -v`
Expected: FAIL — `ImportError: cannot import name 'compute_pf'`

- [ ] **Step 3: Implement compute_pf and analyze_candidate**

Добавить в `ML/baseline/position_ordinal_analysis.py`:

```python
def compute_pf(profits):
    gp = sum(p for p in profits if p > 0)
    gl = abs(sum(p for p in profits if p < 0))
    n = len(profits)
    if gl == 0:
        pf = float("inf") if gp > 0 else 0.0
    elif gp == 0:
        pf = 0.0
    else:
        pf = gp / gl
    return {"pf": pf, "n": n, "gross_profit": gp, "gross_loss": gl}


def analyze_candidate(trades):
    groups = {}
    for t in trades:
        ordinal = t["ordinal"]
        key = "5+" if ordinal >= 5 else str(ordinal)
        groups.setdefault(key, []).append(t["profit"])
    by_ordinal = {}
    for key, profits in groups.items():
        pf_data = compute_pf(profits)
        by_ordinal[key] = pf_data
    return {"by_ordinal": by_ordinal, "n_trades": len(trades)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest tests/test_position_ordinal_analysis.py -v`
Expected: `11 passed` (5 from Task 1 + 6 новых)

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/position_ordinal_analysis.py tests/test_position_ordinal_analysis.py
git commit -m "feat: compute PF by position ordinal per candidate"
```

---

### Task 3: Агрегация, bootstrap и JSON-артефакт

**Files:**
- Modify: `ML/baseline/position_ordinal_analysis.py`
- Modify: `tests/test_position_ordinal_analysis.py`

**Interfaces:**
- `load_all_candidates(max64_dir: str) -> dict[str, list[dict]]` — загружает все кандидаты из каталога, возвращает `{candidate_name: trades}`.
- `aggregate_and_bootstrap(all_trades: dict, n_bootstrap=2000, seed=42) -> dict` — агрегирует PF по ordinal, считает candidate-level bootstrap CI.
- `run(input_dir: str, output_path: str) -> None` — полный пайплайн.

**Методика:** 11-robustness (candidate-level bootstrap), 16-reporting-audit (артефакт ↔ отчёт).

- [ ] **Step 1: Write failing tests**

Добавить в `tests/test_position_ordinal_analysis.py`:

```python
import json
from ML.baseline.position_ordinal_analysis import (
    load_all_candidates,
    aggregate_and_bootstrap,
    run,
)


def test_load_all_candidates(tmp_path):
    for name in ["cand_a", "cand_b"]:
        d = tmp_path / name
        d.mkdir()
        p = d / "events.csv"
        header = "event;time;ticket;side;profit;open_positions"
        p.write_text(header + "\n"
            "OPEN;2021.01.04 11:00;1;SELL;0.0;1\n"
            "CLOSE;2021.01.04 15:00;1;SELL;50.0;0\n")
    result = load_all_candidates(str(tmp_path))
    assert set(result.keys()) == {"cand_a", "cand_b"}
    assert len(result["cand_a"]) == 1
    assert result["cand_a"][0]["ordinal"] == 1


def test_aggregate_and_bootstrap_structure():
    all_trades = {
        "cand_a": [
            {"ticket": "1", "side": "SELL", "ordinal": 1, "profit": 100.0, "year": 2021},
            {"ticket": "2", "side": "SELL", "ordinal": 1, "profit": -50.0, "year": 2022},
            {"ticket": "3", "side": "BUY", "ordinal": 2, "profit": -80.0, "year": 2021},
        ],
        "cand_b": [
            {"ticket": "4", "side": "SELL", "ordinal": 1, "profit": -30.0, "year": 2021},
            {"ticket": "5", "side": "BUY", "ordinal": 2, "profit": 200.0, "year": 2022},
        ],
    }
    result = aggregate_and_bootstrap(all_trades, n_bootstrap=100, seed=42)
    assert "aggregated" in result
    assert "1" in result["aggregated"]
    assert "ci_lower" in result["aggregated"]["1"]
    assert "ci_upper" in result["aggregated"]["1"]
    assert result["n_candidates"] == 2
    assert result["n_total_trades"] == 5
    assert result["bootstrap_config"]["n_bootstrap"] == 100
    assert "by_ordinal_by_year" in result
    assert "2021" in result["by_ordinal_by_year"]["1"]
    assert "2022" in result["by_ordinal_by_year"]["1"]
    assert result["by_ordinal_by_year"]["1"]["2021"]["n"] == 2


def test_run_produces_json(tmp_path):
    cand_dir = tmp_path / "data" / "cand_x"
    cand_dir.mkdir(parents=True)
    header = "event;time;ticket;side;profit;open_positions"
    (cand_dir / "events.csv").write_text(header + "\n"
        "OPEN;2021.01.04 11:00;1;SELL;0.0;1\n"
        "CLOSE;2021.01.04 15:00;1;SELL;100.0;0\n")
    out = tmp_path / "out.json"
    run(str(tmp_path / "data"), str(out))
    assert out.exists()
    data = json.loads(out.read_text())
    assert "aggregated" in data
    assert data["n_candidates"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_position_ordinal_analysis.py::test_load_all_candidates -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement load_all_candidates, aggregate_and_bootstrap, run**

Добавить в `ML/baseline/position_ordinal_analysis.py`:

```python
import json
import os
import random


def load_all_candidates(max64_dir):
    result = {}
    for name in sorted(os.listdir(max64_dir)):
        events_path = os.path.join(max64_dir, name, "events.csv")
        if os.path.isfile(events_path):
            result[name] = parse_trades(events_path)
    return result


def aggregate_and_bootstrap(all_trades, n_bootstrap=2000, seed=42):
    ordinal_keys = ["1", "2", "3", "4", "5+"]
    candidate_names = sorted(all_trades.keys())
    n_candidates = len(candidate_names)

    per_candidate = {}
    for name, trades in all_trades.items():
        per_candidate[name] = analyze_candidate(trades)

    aggregated = {}
    for key in ordinal_keys:
        profits = []
        for name in candidate_names:
            for t in all_trades[name]:
                t_key = "5+" if t["ordinal"] >= 5 else str(t["ordinal"])
                if t_key == key:
                    profits.append(t["profit"])
        if not profits:
            continue
        pf_data = compute_pf(profits)

        ci_values = []
        rng = random.Random(seed)
        for _ in range(n_bootstrap):
            sampled_names = [
                candidate_names[rng.randint(0, n_candidates - 1)]
                for _ in range(n_candidates)
            ]
            boot_profits = []
            for name in sampled_names:
                for t in all_trades[name]:
                    t_key = "5+" if t["ordinal"] >= 5 else str(t["ordinal"])
                    if t_key == key:
                        boot_profits.append(t["profit"])
            if boot_profits:
                bp = compute_pf(boot_profits)
                if bp["pf"] != float("inf"):
                    ci_values.append(bp["pf"])

        ci_values.sort()
        if len(ci_values) >= 20:
            ci_lower = ci_values[int(0.025 * len(ci_values))]
            ci_upper = ci_values[int(0.975 * len(ci_values))]
        else:
            ci_lower = None
            ci_upper = None

        aggregated[key] = {
            **pf_data,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
        }

    n_total = sum(len(t) for t in all_trades.values())

    by_ordinal_by_year = {}
    for key in ordinal_keys:
        year_groups = {}
        for name in candidate_names:
            for t in all_trades[name]:
                t_key = "5+" if t["ordinal"] >= 5 else str(t["ordinal"])
                if t_key == key:
                    year_groups.setdefault(t["year"], []).append(t["profit"])
        if year_groups:
            by_ordinal_by_year[key] = {
                str(y): compute_pf(profits)
                for y, profits in sorted(year_groups.items())
            }

    return {
        "status": "DIAGNOSTIC_ONLY",
        "n_candidates": n_candidates,
        "n_total_trades": n_total,
        "aggregated": aggregated,
        "by_ordinal_by_year": by_ordinal_by_year,
        "per_candidate": per_candidate,
        "bootstrap_config": {
            "n_bootstrap": n_bootstrap,
            "seed": seed,
        },
    }


def run(input_dir, output_path):
    all_trades = load_all_candidates(input_dir)
    result = aggregate_and_bootstrap(all_trades)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
```

Добавить `if __name__` блок:

```python
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Position-ordinal PnL diagnostic for MT5 max=64 pilot"
    )
    parser.add_argument(
        "--input-dir",
        default="ML/reports/mt5_execution_loop/multipos_pilot/max64",
    )
    parser.add_argument(
        "--output",
        default="ML/reports/mt5_execution_loop/diagnostics/position_ordinal_pnl.json",
    )
    args = parser.parse_args()
    run(args.input_dir, args.output)
    print(f"Wrote {args.output}")
```

- [ ] **Step 4: Run all tests**

Run: `./.venv/bin/python -m pytest tests/test_position_ordinal_analysis.py -v`
Expected: `14 passed`

- [ ] **Step 5: Smoke test на реальных данных**

Run: `./.venv/bin/python -m ML.baseline.position_ordinal_analysis`
Expected: `Wrote ML/reports/mt5_execution_loop/diagnostics/position_ordinal_pnl.json`

Проверить структуру:
```bash
./.venv/bin/python -c "
import json
d = json.load(open('ML/reports/mt5_execution_loop/diagnostics/position_ordinal_pnl.json'))
print(f'candidates: {d[\"n_candidates\"]}')
print(f'trades: {d[\"n_total_trades\"]}')
for k in sorted(d['aggregated'].keys()):
    v = d['aggregated'][k]
    ci = f'CI=[{v[\"ci_lower\"]:.3f}, {v[\"ci_upper\"]:.3f}]' if v['ci_lower'] is not None else 'CI=N/A'
    print(f'  ordinal {k}: PF={v[\"pf\"]:.3f} n={v[\"n\"]} {ci}')
"
```

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/position_ordinal_analysis.py tests/test_position_ordinal_analysis.py ML/reports/mt5_execution_loop/diagnostics/position_ordinal_pnl.json
git commit -m "feat: position-ordinal PnL diagnostic with bootstrap CI"
```

---

### Task 4: Отчёт и обновление документации

**Files:**
- Modify: `CONTEXT_HANDOFF.md` — добавить ссылку на артефакт
- Modify: `docs/superpowers/roadmap.md` — обновить статус ACTIVE-трека

**Методика:** 16-reporting-audit (отчёт ↔ артефакт).

- [ ] **Step 1: Проверить числа отчёта против JSON**

```bash
./.venv/bin/python -c "
import json
d = json.load(open('ML/reports/mt5_execution_loop/diagnostics/position_ordinal_pnl.json'))
assert d['status'] == 'DIAGNOSTIC_ONLY'
assert d['n_candidates'] == 32
total_from_agg = sum(v['n'] for v in d['aggregated'].values())
assert total_from_agg == d['n_total_trades'], f'{total_from_agg} != {d[\"n_total_trades\"]}'
for name, pc in d['per_candidate'].items():
    assert pc['n_trades'] >= 0
print('All checks passed')
"
```

Expected: `All checks passed`

- [ ] **Step 2: Обновить CONTEXT_HANDOFF.md**

Добавить в секцию `Current Diagnostic Facts`:

```markdown
- Position-ordinal PnL diagnostic: `ML/reports/mt5_execution_loop/diagnostics/position_ordinal_pnl.json` — PF по ordinal (1, 2, 3, 4, 5+) для 32 кандидатов max=64 пилота, candidate-level bootstrap CI.
```

- [ ] **Step 3: Обновить roadmap.md**

Обновить статус ACTIVE-трека:

```markdown
Status: entry-mechanics probe plan pending. Fill-rate probe completed — fill rate
is NOT the primary cause of BATCH_NO_WINNER. Position-ordinal PnL diagnostic
completed — PF by ordinal analysis in `position_ordinal_pnl.json` (pending
result interpretation).
```

- [ ] **Step 4: Запустить финальные тесты**

```bash
./.venv/bin/python -m pytest tests/test_position_ordinal_analysis.py -v
```

Expected: `14 passed`

- [ ] **Step 5: Commit**

```bash
git add CONTEXT_HANDOFF.md docs/superpowers/roadmap.md
git commit -m "docs: update handoff and roadmap with position-ordinal diagnostic"
```

---

## Ограничения и известные пробелы

1. **Не все позиции имеют OPEN-событие.** 652 из 919 позиций (кандидат `simple_combined_extra_trees_small_12h_thr0.2`) не имеют OPEN-события в polling-потоке (`missing_open_estimate = ORDER_PLACED - OPEN = 950 - 298 = 652`). Причина: polling фиксирует OPEN на H1-баре; если pending order заполняется и/или закрывается до следующего опроса, OPEN не записывается. Из них 37 (4%) — измеренные внутрибарные сделки (`same_h1_count`). Доля позиций с известным ordinal: ~32% (298 из 919).

2. **Нет cost model.** Swap, commission, slippage не вычтены. `order_close_price`, `swap`, `commission` — placeholder (методология 13b: ограничения прототипа).

3. **Bootstrap по кандидатам, не по сделкам.** При 32 кандидатах и малом числе сделок на высоких ordinal (5+: 0-75 сделок на кандидат) CI широкие. Результаты для ordinal 5+ — descriptive, не inferential. Temporal correlation внутри кандидата не учтена (candidate-level resampling, не block bootstrap).

4. **max=64 — диагностический режим.** PF в max=64 не является каноническим результатом. Цель — понять механику деградации, не оценить прибыльность.

5. **Группировка 5+ предзадана.** Порог выбран до анализа на основе распределения: ordinal >= 5 имеет 7.6% сделок (682 из 8934 по 32 кандидатам).

6. **Bootstrap CI исключает inf.** Если все сделки в bootstrap-выборке для ordinal bucket выигрышные, PF=inf и исключается из ci_values. Для ordinal 5+ с малым числом сделок это может занизить верхнюю границу CI.

7. **Ordinal — polling snapshot.** `open_positions` на OPEN-событии — snapshot на H1-баре. Для нескольких fills в одном баре OPEN запишет итоговое количество после всех fills бара, а не количество на момент каждого fill. Ordinal может быть неточным для fills в одном баре.
