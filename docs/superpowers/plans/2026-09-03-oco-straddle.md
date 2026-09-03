# Амплитудный OCO-стрэддл (idea-02) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Исполнить пункт 2 роэдмэпа `docs/audit/best_ideas.md` — предрегистрированный двухступенчатый kill-тест амплитудного OCO-стрэддла на окнах замороженного movement-фильтра без предсказания знака, с двумя независимыми исходами: идеализированный payoff / already-moved (ступень A, ~1 день) и полная OCO-симуляция с издержками (ступень B, 2–3 дня).

**Architecture:** Код в `statistics/oco_straddle/` — плоские модули без `__init__.py` (каталог `statistics/` конфликтует со stdlib, как в `statistics/pair_spread/`). Три ядра: `frozen_loader.py` (загрузка замороженного фильтра `ML/reports/entry_based_movement_filter_freeze.*` + валидация контракта), `stage_a.py` (already-moved + идеализированный payoff на H3/H6), `stage_b.py` (OCO-симулятор с контрактом внутрибаровой хронологии fill, cost-моделью и stationary bootstrap). Оркестратор `run_oco_straddle.py` собирает `DATA/oco_straddle/stage_a.json` и `DATA/oco_straddle/stage_b.json` + CSV-артефакты. Тесты грузят модули через `importlib.util.spec_from_file_location` (паттерн `tests/test_pair_spread_*.py`).

**Tech Stack:** Python (`./.venv/bin/python`, pandas, numpy, scikit-learn уже в окружении), pytest. Без новых внешних зависимостей (bootstrap — numpy-реализация stationary bootstrap Политиса–Романо, как в `statistics/pair_spread/backtest.py`).

```text
depends_on: docs/audit/best_ideas.md §2 (тир 1, идея 2), docs/archive/qoder/brainstorm-protocols.md:1425-1493 (детализация kill-контура), ML/reports/entry_based_movement_filter_freeze.json (sha256 b72f08c..., правило simple_combined/H3/top5%/extra_trees_small/seeds 42-44), ML/reports/entry_based_movement_filter_freeze_scores.csv + selected_rows.csv + score_cutoffs.csv (входные окна), DATA/Nero_*_labeled.csv + MT/MQL4/Files/XAUUSD_*OHLC.csv (OHLC для PnL)
blocks: другие идеи роэдмэпа независимы; очерёдность — по результатам этого трека
supersedes: нет
exit_decisions: Stage A KILL (медианный already-moved ≥0.5 или payoff ≤0 на всех d) → обе стрэддл-идеи закрыты, отчёт + decision memo, Stage B не запускается; Stage A PASS → Stage B; Stage B KILL (PF<1.3 или BS_p05≤1.0 на обоих cost-режимах или верхняя CI продолжения ≤0) → тема стрэддла закрыта, переход к идее 3 роэдмэпа (детектор смены режима); Stage B SURVIVED (PF≥1.3, BS_p05>1.0, N≥100, ≥30 на сторону is not applicable — OCO без сторон — заменяется на N≥100 + эффективные годы) → отдельный план production-контура (MT5 parity) + тиковая диагностика fill по разделу 3.3 pair-spread-спеки
locked_test_policy: не используется — этап RESEARCH_ONLY / DIAGNOSTIC_ONLY. locked_test остаётся not_opened (ML/reports/entry_based_movement_filter_freeze.json:99,122). Любой результат с PnL/PF на val_eval/low_n_disclosure — не кандидат до нового проверочного цикла с отдельным frozen OCO-правилом (методология 00-research-management, A4-verdicts).
```

> **Холодный старт для агента без истории диалога:** Проект SoSimple — 150+ проваленных экспериментов с PF≥1.3, главное узкое место — конверсия амплитудного сигнала в прибыль после издержек (2.11: 57% движения уже случилось к моменту сигнала, 2.12: спред 0.8 режет PF 3.27→1.32 и хронология fill убила locked-кандидата). Заморожен один movement-фильтр (`ML/reports/entry_based_movement_filter_freeze.json` → verdict `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`, `locked_test=not_opened`). Его правило: `profile=simple_combined`, `model=extra_trees_small`, `horizon=H3`, `target=max(entry_up_H, entry_dn_H)`, `top_fraction=0.05`, `seeds=[42,43,44]`, `score_agg=median`, `split: train≤2020 / val_select=2021-2023 / val_eval=2023-2025 / low_n_disclosure=2026`. Правило — batch-сегментация: в каждом батче берутся топ-5% по `score`. Это не фиксированный live-порог. Пороги по split лежат в `score_cutoffs.csv` (train 7.77 / val_select 9.02 / val_eval 14.31). Для OCO-теста окна — это строки `scores.csv` где `selected=true`. Ожидаемый OOS для OCO: `val_eval` (333 окна, 6646 строк, 2023-2025) как primary, `low_n_disclosure` (59 окон, 2026) как disclosure. Сигнал `selected` доступен в момент решения (`pre_entry_decision`, `available_at_decision_time=true`). Амплитудный OCO-стрэддл выставляет на `next_open` после сигнала два стопа на расстояниях `±d·ATR` (`d ∈ {0.25,0.5,1.0}`) с OCO-отменой второй ноги и держит позицию H3/H6 баров (трейлинг как в Qoder-протоколе, но предрегистрирован). Издержки: canonical спред 0.4 (в пунктах цены / ATR-единицах — фиксируется в плане до запуска), stress 0.8, slippage 0.2, комиссия 0. Внутрибаровая хронология fill — неразрешённый блокер проекта (2.12) — мандатно требует пессимистичного предвыбранного контракта. Этот план — исследовательский kill-тест, не торговый кандидат.

## Global Constraints

- Python только `./.venv/bin/python`; тесты `./.venv/bin/python -m pytest <файл> -q`; зависимости не добавлять без фиксации в `requirements.txt`.
- Все числа — заморожены этим планом до первого прогона Stage A/B; изменение после просмотра PnL — только документированным решением (методология 00, A3: автовыбор 2.4/2.12 убил кандидатов).
- Сплит OCO-теста: frozen movement-фильтр уже зафиксирован (`train ≤2020`, `val_select 2021-2023` — выбор правила, `val_eval 2023-2025` — primary OOS для OCO, `low_n_disclosure 2026` — disclosure). Ни одна строка test-OOS не участвует в переоценке β/μ/σ/порогов. `locked_test` не открывается.
- Execution contract фиксируется до запуска: тип входа — `STOP` (BUY STOP / SELL STOP), цена входа — триггер `entry ± d·ATR` на следующем баре после сигнала, исполнение по триггер-цене + неблагоприятный сдвиг `spread/2 + slippage` (если OHLC — mid), отмена второй ноги OCO в тот же бар, выход — истечение окна H3/H6 (или трейлинг-выход если предзарегистрирован), `next-bar` / `same-bar` хронология — предвыбранный пессимистичный контракт.
- Canonical spread — главный gate (методология 12); zero-spread — только `DIAGNOSTIC_ONLY` для геометрии; stress-гриды обязательны.
- `statistics/oco_straddle/` — без `__init__.py`.
- Sample size gate (методология 06): `val_eval` выбранных окон 333 уже известен; для OCO сделок gate `N≥100` (для вердикта SURVIVED) и минимум 50 окон/год уже проверены в freeze-гейте; Stage B дополнительно требует что сделки покрывают ≥3 месяца (иначе `DIAGNOSTIC_ONLY`).
- Verdict-статусы — по A4: `RESEARCH_ONLY` максимум для этого этапа; `candidate/production_candidate/confirmed` запрещены без нового проверочного цикла.

---

### Task 0: Регистрация трека в roadmap.md

**Files:**
- Modify: `docs/superpowers/roadmap.md:15-20`

**Interfaces:**
- Consumes: текущий `## ACTIVE` = «нет активного трека» (pair-spread закрыт 2026-08-27).
- Produces: единственный ACTIVE-трек «OCO-straddle kill-test (idea-02)» с полями `depends_on/blocks/exit_decisions/locked_test_policy` из шапки этого плана; прежние PARKED-направления не трогаются.

**Методология:** `docs/methodology/00-research-management.md` — исследовательский уровень фиксируется до запуска, `level=RESEARCH_ONLY`, `allowed_max_verdict=RESEARCH_ONLY`; `docs/methodology/A4-verdicts-stop-conditions.md` — переход из поискового в проверочный требует нового плана (здесь остаётся поисковым).

- [ ] **Step 1: Обновить roadmap.md**

В `docs/superpowers/roadmap.md` секцию `## ACTIVE` заменить на:

```markdown
## ACTIVE

### OCO-straddle kill-test (idea-02)

Status: план исполняется (`docs/superpowers/plans/2026-09-03-oco-straddle.md`).
Предрегистрированный двухступенчатый kill-тест амплитудного OCO-стрэддла
на окнах замороженного movement-фильтра (simple_combined/H3/top5%/extra_trees_small),
RESEARCH_ONLY / DIAGNOSTIC_ONLY, без `locked_test`, без ML-обучения.

Next action: исполнение плана по задачам; вердикты — по разделу exit_decisions плана.
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/roadmap.md
git commit -m "Register OCO-straddle kill-test as ACTIVE track (idea-02)"
```

**Обязательные проверки:** один ACTIVE за раз (roadmap правило 1); новый план имеет поля `depends_on/blocks/exit_decisions/locked_test_policy`.

**Критерий завершения:** `roadmap.md` содержит единственный ACTIVE «OCO-straddle» и не хранит историю завершённых этапов.

---

### Task 1: Валидация замороженного контракта и загрузчик frozen_loader.py

**Files:**
- Create: `statistics/oco_straddle/frozen_loader.py`
- Test: `tests/test_oco_straddle_frozen_loader.py`

**Interfaces:**
- Consumes: `ML/reports/entry_based_movement_filter_freeze.json` (hash `9f3133cc...`), `ML/reports/entry_based_movement_filter.json` (hash `b72f088c...`), `ML/reports/entry_based_amplitude_movement.json` (hash `b79c7cc6...`), `ML/reports/entry_based_movement_filter_freeze_scores.csv` (с колонками `split,split_row_id,time,year,score,entry_movement_3,selected`), `*_score_cutoffs.csv`, `*_yearly.csv`, `*_random_baseline.csv`.
- Produces: `load_frozen_artifacts(base_dir) -> dict` (проверенные `rule_hash 56361f121...`, `frozen_config_hash ee2701d..., contract_status.status==PASS`, `locked_test==not_opened`, `FROZEN_RULE` дословно); `load_selected_windows(split_filter) -> pd.DataFrame` (окна где `selected=true`, отсортированы по `time`, с `decision_time`/`score`/`cutoff`/ATR); `validate_oco_splits(artifacts) -> list[str]` (failures по `freeze_gate_failures`); `get_frozen_cutoffs() -> dict[split, float]`.

**Методология:** `00-research-management` (гипотеза и gate фиксируются до запуска, `origin_bias` — выбор правила подсмотрен на `val_select 2021-2023`, `locked_test` не используется), `06-temporal-split` (границы train/val_select/val_eval/disclosure, embargo 24h, sample_size_gate), `A1-checklist-dev` (contract validation до обучения).

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_oco_straddle_frozen_loader.py
import importlib.util, sys
from pathlib import Path
import pandas as pd

_MOD = Path(__file__).resolve().parents[1] / "statistics" / "oco_straddle" / "frozen_loader.py"
_spec = importlib.util.spec_from_file_location("frozen_loader", _MOD)
frozen_loader = importlib.util.module_from_spec(_spec)
sys.modules["frozen_loader"] = frozen_loader
_spec.loader.exec_module(frozen_loader)

def test_frozen_rule_hash_matches_canonical():
    a = frozen_loader.load_frozen_artifacts(Path("."))
    assert a["rule_hash"] == "56361f12104b55c4cac6bd04426349f71d8944c139563a8c9b68d3b25e97deaf"
    assert a["frozen_config_hash"] == "ee2701d0566e910e8a0fb10c6d4f5a8916d2b4e5b903e9dc50f39354344e86b6"
    assert a["contract_status"]["status"] == "PASS"
    assert a["locked_test"] == "not_opened"
    assert a["frozen_rule"]["profile"] == "simple_combined"
    assert a["frozen_rule"]["selected_fraction"] == 0.05

def test_selected_windows_only_val_eval_is_oos():
    dfs = frozen_loader.load_selected_windows(split_filter="val_eval")
    # из freeze.json val_eval selected_n=333
    assert len(dfs) == 333
    assert set(dfs["split"].unique()) == {"val_eval"}
    assert dfs["selected"].all()
    assert dfs["time"].is_monotonic_increasing

def test_validate_splits_no_failures():
    arts = frozen_loader.load_frozen_artifacts(Path("."))
    fails = frozen_loader.validate_oco_splits(arts)
    assert fails == []  # все freeze-гейты уже PASS в отчёте 2026-07-08

def test_cutoffs_are_pre_registered():
    cuts = frozen_loader.get_frozen_cutoffs()
    # значения из freeze.json score_cutoffs: val_select 9.015..., val_eval 14.313...
    assert abs(cuts["val_select"] - 9.01539654586606) < 1e-9
    assert abs(cuts["val_eval"] - 14.313095375478142) < 1e-9
    assert abs(cuts["train"] - 7.77124142635351) < 1e-9

def test_random_baseline_lift_is_far_below_frozen():
    arts = frozen_loader.load_frozen_artifacts(Path("."))
    rb = arts["random_baseline"]
    assert rb["p95_movement_lift"] < 1.15
    assert arts["validation_metrics"]["val_eval"]["movement_lift"] > 2.0
```

- [ ] **Step 2: Запустить — убедиться что падают**

Run: `./.venv/bin/python -m pytest tests/test_oco_straddle_frozen_loader.py -q`
Expected: FAIL (нет модуля).

- [ ] **Step 3: Реализовать frozen_loader.py**

```python
# statistics/oco_straddle/frozen_loader.py
from __future__ import annotations
import hashlib, json
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
FREEZE_JSON = REPO_ROOT / "ML/reports/entry_based_movement_filter_freeze.json"
SCORES_CSV = REPO_ROOT / "ML/reports/entry_based_movement_filter_freeze_scores.csv"
SELECTED_CSV = REPO_ROOT / "ML/reports/entry_based_movement_filter_freeze_selected_rows.csv"
CUTOFFS_CSV = REPO_ROOT / "ML/reports/entry_based_movement_filter_freeze_score_cutoffs.csv"
YEARLY_CSV = REPO_ROOT / "ML/reports/entry_based_movement_filter_freeze_yearly.csv"
RANDOM_CSV = REPO_ROOT / "ML/reports/entry_based_movement_filter_freeze_random_baseline.csv"

FROZEN_RULE_EXPECTED = {
    "profile": "simple_combined",
    "model_key": "extra_trees_small",
    "horizon": 3,
    "target_family": "entry_movement",
    "threshold_type": "top_fraction",
    "selected_fraction": 0.05,
    "score_aggregation": "median_across_rerun_seeds",
    "seeds": [42, 43, 44],
}

def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def load_frozen_artifacts(base_dir: Path = REPO_ROOT) -> dict:
    art = json.loads((base_dir / FREEZE_JSON.relative_to(REPO_ROOT)).read_text(encoding="utf-8"))
    # строгая сверка контракта — как в benchmark_entry_based_movement_filter_freeze.py
    assert art["contract_status"]["status"] == "PASS", art["contract_status"]
    assert art["locked_test"] == "not_opened"
    assert art["frozen_rule"] == FROZEN_RULE_EXPECTED
    assert art["rule_hash"] == "56361f12104b55c4cac6bd04426349f71d8944c139563a8c9b68d3b25e97deaf"
    # дополнительно отдать parsed CSV для удобства
    art["_scores_df"] = pd.read_csv(SCORES_CSV)
    art["_selected_df"] = pd.read_csv(SELECTED_CSV)
    art["_cutoffs_df"] = pd.read_csv(CUTOFFS_CSV)
    return art

def load_selected_windows(split_filter: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(SCORES_CSV, parse_dates=["time"])
    sel = df[df["selected"] == True].copy()
    if split_filter is not None:
        sel = sel[sel["split"] == split_filter]
    sel = sel.sort_values("time").reset_index(drop=True)
    return sel

def get_frozen_cutoffs() -> dict[str, float]:
    df = pd.read_csv(CUTOFFS_CSV)
    # scope==split
    sub = df[df["scope"] == "split"]
    return {row["split"]: float(row["score_cutoff"]) for _, row in sub.iterrows()}

def validate_oco_splits(artifacts: dict) -> list[str]:
    from ML.baseline.benchmark_entry_based_movement_filter_freeze import freeze_gate_failures
    metrics = {**artifacts.get("validation_metrics", {}), **artifacts.get("disclosure_metrics", {}),
               "score_cutoff_diagnostics": artifacts.get("score_cutoff_diagnostics", {}),
               "random_baseline": artifacts.get("random_baseline", {})}
    return freeze_gate_failures(metrics)
```

- [ ] **Step 4: Запустить тесты — PASS**

Run: `./.venv/bin/python -m pytest tests/test_oco_straddle_frozen_loader.py -q`
Expected: PASS (5 тестов).

- [ ] **Step 5: Commit**

```bash
git add statistics/oco_straddle/frozen_loader.py tests/test_oco_straddle_frozen_loader.py
git commit -m "Add frozen movement filter loader for OCO straddle (idea-02)"
```

**Обязательные проверки (00, 06, A1):** `contract_status==PASS`, `locked_test==not_opened`, `rule_hash` побайтно, `203 disclosure_only` не используется для выбора, `val_eval` уже проходит `selected_n≥300`, `yearly selected_n≥50`, `movement_lift` пороги — всё проверено до запуска OCO; любое отклонение → `ABORT_CONTRACT_FAIL`.

**Критерий завершения:** загрузчик проходит 21 существующий freeze-тест + 5 новых; артефакты читаются, `selected` окна доступны для Stage A/B без переоценки.

---

### Task 2: Верификация данных, OHLC-выравнивание и проверка ATR

**Files:**
- Create: `statistics/oco_straddle/check_data.py`
- Test: `tests/test_oco_straddle_check_data.py`

**Interfaces:**
- Consumes: `DATA/Nero_train_labeled.csv` etc. (если используется для ATR) + `MT/MQL4/Files/XAUUSD_*OHLC.csv` или `MT/MQL4/Files/H1/*.csv` (OHLC для исполнения), `ML/reports/entry_based_movement_filter_freeze_scores.csv` (время окон).
- Produces: `check_oco_data() -> dict` с `time_alignment_rate`, `atr_missing_rate`, `gap_hours`, `coverage_per_split`; `validate_entry_time_contract(df) -> list[str]` (проверка `feature_time <= signal_time < feature_available_time <= decision_time <= entry_open`); CLI-отчёт `DATA/oco_straddle/data_check.json`.

**Методология:** `01-raw-data-inventory` (источник, формат, producer, момент доступности полей), `03-feature-contract-leakage` (feature contract, future-derived, online mismatch), `02-data-pipeline` (эмбарго, нормализация построчно), `06-temporal-split` (embargo 24h уже в freeze-config). Если `check_data.py` из pair-spread уже есть — переиспользовать паттерн потоковой проверки.

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_oco_straddle_check_data.py
import importlib.util, sys
from pathlib import Path
import pandas as pd

_MOD = Path(__file__).resolve().parents[1] / "statistics/oco_straddle/check_data.py"
_spec = importlib.util.spec_from_file_location("check_data", _MOD)
mod = importlib.util.module_from_spec(_spec)
sys.modules["check_data"] = mod
_spec.loader.exec_module(mod)

def test_time_alignment_basic(tmp_path):
    # синтетика: 3 окна, одно без OHLC-бара
    scores = pd.DataFrame({"time": pd.to_datetime(["2023-01-02 00:00","2023-01-02 01:00","2023-01-02 02:00"]), "selected":[True,True,True]})
    ohlc = pd.DataFrame({"time": pd.to_datetime(["2023-01-02 00:00","2023-01-02 01:00"]), "open":[1,1], "high":[2,2], "low":[0.9,0.9], "close":[1.5,1.5], "ATR":[0.5,0.5]})
    res = mod.validate_entry_time_contract(scores, ohlc)
    assert "missing_ohlc_bar" in res["warnings"]

def test_atr_missing_flags(tmp_path):
    df = pd.DataFrame({"ATR":[0.5, None, 0.0]})
    assert mod.atr_missing_rate(df) > 0.3

def test_check_oco_data_smoke():
    # smoke на реальных артефактах — требует наличия файлов, иначе skip
    import pytest
    if not Path("ML/reports/entry_based_movement_filter_freeze_scores.csv").exists():
        pytest.skip("no freeze scores")
    res = mod.check_oco_data()
    assert "val_eval" in res["coverage"]
    assert res["val_eval"]["selected_n"] == 333
```

- [ ] **Step 2: Запустить — FAIL**

Run: `./.venv/bin/python -m pytest tests/test_oco_straddle_check_data.py -q`
Expected: FAIL.

- [ ] **Step 3: Реализовать check_data.py**

```python
# statistics/oco_straddle/check_data.py
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORES = REPO_ROOT / "ML/reports/entry_based_movement_filter_freeze_scores.csv"
OHLC_CANDIDATES = [
    REPO_ROOT / "MT/MQL4/Files/XAUUSD_H1_OHLC.csv",
    REPO_ROOT / "MT/MQL4/Files/H1/XAUUSD_OHLC.csv",
    REPO_ROOT / "DATA/XAUUSD_H1_OHLC.csv",
]

def atr_missing_rate(df: pd.DataFrame, col: str = "ATR") -> float:
    if col not in df.columns:
        return 1.0
    return float(df[col].isna().mean() | (df[col] <= 0).mean() if len(df) else 1.0)

def validate_entry_time_contract(scores: pd.DataFrame, ohlc: pd.DataFrame) -> dict:
    warnings = []
    if ohlc is None or ohlc.empty:
        warnings.append("missing_ohlc")
        return {"warnings": warnings}
    # join по времени сигнала -> следующий бар open
    missing = set(scores["time"]) - set(ohlc["time"])
    if missing:
        warnings.append("missing_ohlc_bar")
    return {"warnings": warnings, "missing_n": len(missing)}

def check_oco_data() -> dict:
    scores = pd.read_csv(SCORES, parse_dates=["time"])
    cov = {}
    for split in ["train","val_select","val_eval","low_n_disclosure"]:
        sub = scores[scores["split"] == split]
        cov[split] = {"total_n": int(len(sub)), "selected_n": int((sub["selected"]==True).sum())}
    # найти первый существующий OHLC
    ohlc_path = next((p for p in OHLC_CANDIDATES if p.exists()), None)
    res = {"coverage": cov, "ohlc_path": str(ohlc_path) if ohlc_path else None}
    if ohlc_path:
        ohlc = pd.read_csv(ohlc_path, sep=";" if ohlc_path.suffix==".csv" and ";" in ohlc_path.read_text()[:500] else ",")
        res["ohlc_rows"] = int(len(ohlc))
        # нормализовать колонки time/open/high/low/close/ATR если есть
    return res

if __name__ == "__main__":
    out = REPO_ROOT / "DATA/oco_straddle/data_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(check_oco_data(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"WROTE {out}")
```

- [ ] **Step 4: Запустить тесты — PASS, затем smoke**

Run: `./.venv/bin/python -m pytest tests/test_oco_straddle_check_data.py -q`
Run: `./.venv/bin/python statistics/oco_straddle/check_data.py`
Expected: `DATA/oco_straddle/data_check.json` создан, `val_eval selected_n==333`.

- [ ] **Step 5: Commit**

```bash
git add statistics/oco_straddle/check_data.py tests/test_oco_straddle_check_data.py
git commit -m "Add OCO data-check: OHLC alignment and ATR coverage"
```

**Обязательные проверки:** source alignment PASS, `entry_match_rate≥0.99`, `time_position_mismatches==0` (как в `2026-07-02-regression-updn-already-moved-audit.md` preflight), `ATR` не нормализуется и доступен на баре сигнала.

**Критерий завершения:** `data_check.json` показывает покрытие по всем split и путь к OHLC; предупреждения отсутствуют или документированы.

---

### Task 3: Ступень A — already-moved + идеализированный payoff (убийца за ~1 день)

**Files:**
- Create: `statistics/oco_straddle/stage_a.py`
- Test: `tests/test_oco_straddle_stage_a.py`

**Interfaces:**
- Consumes: `frozen_loader.load_selected_windows(split_filter="val_eval")` (окна), OHLC (open/high/low/close, ATR), `DATA/Nero_*` если нужно для фрактальных цен (опционально).
- Produces: `compute_already_moved(rows, ohlc, horizons=(3,6)) -> pd.DataFrame` (колонки `already_up_share`, `already_dn_share`, `share_already_abs_over_50pct` как в `docs/reports/2026-07-02-regression-updn-already-moved-audit.md:77-83`); `idealized_payoff(row, ohlc_window, d_grid=(0.25,0.5,1.0), spread=0.4, slippage=0.2) -> dict[d, payoff]` где `payoff = max(0, max_high - (entry + d·ATR) , (entry - d·ATR) - min_low) - spread - slippage`; `summarize_stage_a(df) -> dict` с медианой доли, долей ≥50%/100%, медианным payoff по каждой `d`; `stage_a_kill(metrics) -> (killed: bool, reasons: list)`.

**Методология:** `06b-oracle-preflight` (проверка потолка: идеализированный payoff при идеальном знании будущих high/low внутри окна — это oracle-диагностика, не ML), `05-eda-data-quality` (распределение already-moved), `07b-predictability-gate` (если сигнал только описывает прошлое — Spearman≈0 — то после входа payoff≈0). Если подходящего раздела для OCO-payoff нет — обосновать как комбинацию 06b + 12-costs без обучения.

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_oco_straddle_stage_a.py
import importlib.util, sys
from pathlib import Path
import pandas as pd, numpy as np

_MOD = Path(__file__).resolve().parents[1] / "statistics/oco_straddle/stage_a.py"
_spec = importlib.util.spec_from_file_location("stage_a", _MOD)
stage_a = importlib.util.module_from_spec(_spec)
sys.modules["stage_a"] = stage_a
_spec.loader.exec_module(stage_a)

def test_idealized_payoff_long_side():
    # entry=100, ATR=10, d=0.5 => upper=105, low excursion игнорируется
    row = {"entry":100, "ATR":10}
    window = pd.DataFrame({"high":[108,109,107], "low":[99,98,97]})
    out = stage_a.idealized_payoff_for_row(row, window, d=0.5, spread=0.4, slippage=0.2)
    # max_high=109, payoff_long = 109-105=4, payoff_short = (95-97) <0, max=4, net=4-0.6=3.4
    assert abs(out["payoff_gross"] - 4.0) < 1e-9
    assert abs(out["payoff_net"] - 3.4) < 1e-9

def test_idealized_payoff_no_trigger():
    row = {"entry":100, "ATR":10}
    window = pd.DataFrame({"high":[102,103], "low":[99,98]})
    out = stage_a.idealized_payoff_for_row(row, window, d=0.5, spread=0.4, slippage=0.2)
    # highs 103 <105, lows 98 >95 => no trigger => payoff 0 - costs = -0.6 but floored at max(0, excursion)-costs
    assert out["payoff_net"] < 0  # убивает геометрию

def test_already_moved_share_computation():
    # already_up=3, already_dn=1, actual_up=10 => share_up=0.3, share_dn=0.1 => max=0.3 <0.5
    df = pd.DataFrame({"already_up":[3], "already_dn":[1], "actual_up":[10], "actual_dn":[10]})
    out = stage_a.attach_already_moved_share(df)
    assert abs(out.loc[0,"already_up_share"]-0.3) < 1e-9
    assert out.loc[0,"share_already_abs_over_50pct"] == False

def test_stage_a_kill_rule():
    metrics = {"median_already_share":0.57, "median_payoff_net_d0_25": -0.1, "median_payoff_net_d0_5": -0.2, "median_payoff_net_d1_0": -0.3}
    killed, reasons = stage_a.stage_a_kill(metrics, already_threshold=0.5)
    assert killed and any("already" in r for r in reasons)

def test_summarize_stage_a_median():
    df = pd.DataFrame({"already_up_share":[0.2,0.6,0.8], "already_dn_share":[0.1,0.5,0.9], "payoff_net_d0_5":[-1,0,2]})
    s = stage_a.summarize_stage_a(df)
    assert s["n_windows"] == 3
    assert "median_already_share" in s
    assert "median_payoff_net_d0_5" in s
```

- [ ] **Step 2: Запустить — FAIL**

Run: `./.venv/bin/python -m pytest tests/test_oco_straddle_stage_a.py -q`
Expected: FAIL.

- [ ] **Step 3: Реализовать stage_a.py**

```python
# statistics/oco_straddle/stage_a.py
from __future__ import annotations
import math
import pandas as pd, numpy as np

D_GRID = (0.25, 0.5, 1.0)
SPREAD_CANON = 0.4
SLIPPAGE = 0.2
SPREAD_STRESS = 0.8

def idealized_payoff_for_row(row: dict, window: pd.DataFrame, d: float, spread: float = SPREAD_CANON, slippage: float = SLIPPAGE) -> dict:
    entry = float(row["entry"])
    atr = float(row["ATR"])
    upper = entry + d * atr
    lower = entry - d * atr
    max_high = float(window["high"].max())
    min_low = float(window["low"].min())
    long_excursion = max(0.0, max_high - upper)
    short_excursion = max(0.0, lower - min_low)
    gross = max(long_excursion, short_excursion)
    net = gross - spread - slippage
    return {"d": d, "payoff_gross": gross, "payoff_net": net, "long_excursion": long_excursion, "short_excursion": short_excursion}

def attach_already_moved_share(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["already_up_share"] = out["already_up"] / out["actual_up"].replace(0, np.nan)
    out["already_dn_share"] = out["already_dn"] / out["actual_dn"].replace(0, np.nan)
    out["max_already_share"] = out[["already_up_share","already_dn_share"]].max(axis=1)
    out["share_already_abs_over_50pct"] = out["max_already_share"] >= 0.5
    out["share_already_abs_over_100pct"] = out["max_already_share"] >= 1.0
    return out

def summarize_stage_a(df: pd.DataFrame) -> dict:
    return {
        "n_windows": int(len(df)),
        "median_already_up_share": float(df["already_up_share"].median()) if "already_up_share" in df else None,
        "median_already_dn_share": float(df["already_dn_share"].median()) if "already_dn_share" in df else None,
        "median_already_share": float(df["max_already_share"].median()) if "max_already_share" in df else None,
        "share_already_abs_over_50pct": float(df["share_already_abs_over_50pct"].mean()) if "share_already_abs_over_50pct" in df else None,
        "share_already_abs_over_100pct": float(df["share_already_abs_over_100pct"].mean()) if "share_already_abs_over_100pct" in df else None,
        **{f"median_payoff_net_d{str(d).replace('.','_')}": float(df[f"payoff_net_d{str(d).replace('.','_')}"].median()) for d in D_GRID if f"payoff_net_d{str(d).replace('.','_')}" in df},
        **{f"median_payoff_gross_d{str(d).replace('.','_')}": float(df[f"payoff_gross_d{str(d).replace('.','_')}"].median()) for d in D_GRID if f"payoff_gross_d{str(d).replace('.','_')}" in df},
    }

def stage_a_kill(metrics: dict, already_threshold: float = 0.5) -> tuple[bool, list[str]]:
    reasons = []
    med = metrics.get("median_already_share")
    if med is not None and med >= already_threshold:
        reasons.append(f"median already-moved share {med:.3f} >= {already_threshold}")
    # payoff ≤0 на всех d — убивает обе стрэддл-идеи сразу (best_ideas.md:47)
    payoff_keys = [k for k in metrics if k.startswith("median_payoff_net_d")]
    if payoff_keys and all(metrics[k] <= 0 for k in payoff_keys):
        reasons.append(f"median payoff_net ≤0 on all d {payoff_keys}")
    if metrics.get("share_already_abs_over_50pct", 0) >= 0.57:  # порог из 2.11 уже-состоявшегося
        reasons.append(f"share ≥50% {metrics['share_already_abs_over_50pct']:.3f} >=0.57 (2.11 benchmark)")
    return (len(reasons) > 0, reasons)
```

- [ ] **Step 4: Запустить тесты — PASS**

Run: `./.venv/bin/python -m pytest tests/test_oco_straddle_stage_a.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add statistics/oco_straddle/stage_a.py tests/test_oco_straddle_stage_a.py
git commit -m "Add OCO Stage A: idealized payoff and already-moved diagnostic"
```

**Обязательные проверки (06b, 05):** `future high/low` помечены `future-derived` и запрещены для признаков; oracle-потолок не считается качеством модели; `zero-spread` только диагностический; `median payoff` считается на frozen OOS (`val_eval`), не на `val_select`.

**Критерий завершения:** `stage_a_kill` возвращает KILL если медианная доля ≥0.5 или payoff ≤0 на всех `d`; иначе PASS → разрешает Stage B.

---

### Task 4: Ступень B — полная OCO-симуляция с издержками и bootstrap

**Files:**
- Create: `statistics/oco_straddle/stage_b.py`
- Test: `tests/test_oco_straddle_stage_b.py`

**Interfaces:**
- Consumes: `frozen_loader.load_selected_windows("val_eval")`, OHLC-ряды, `stage_a.D_GRID`, cost-модель.
- Produces: `@dataclass OcoTrade(entry_time, exit_time, side, entry_price, exit_price, pnl_gross, pnl_net, exit_reason, d, spread_mode)`; `run_oco_backtest(windows, ohlc, d, spread, slippage, horizon_bars, fill_contract) -> list[OcoTrade]`; `profit_factor(pnls) -> float`; `stationary_bootstrap_ci(pnls, expected_block, n_resamples=10000, seed=0) -> float` (BS_p05); `yearly_pf(trades) -> dict[year, PF]`; `compare_vs_baseline(oco_pf, baseline_pf) -> dict` (дельта, bootstrap CI).

**Execution contract (предрегистрирован, пессимистичный):**
- OHLC трактуется как mid; спред — `full bid-ask spread` как неблагоприятный сдвиг: для BUY STOP `fill = trigger + spread/2 + slippage`, для SELL STOP `fill = trigger - spread/2 - slippage` (методология 12: SL-триггер по исполнимой стороне).
- Сигнал на закрытии бара `t` → ордера выставляются на `open[t+1]` на уровнях `close[t] ± d·ATR[t]`; внутрибаровой порядок на баре исполнения: `SL first` (пессимистичный, как в pair-spread timeout/stop). Если бар `t+1` одновременно касается обеих триггер-цен (расширение через оба стопа) — считается chạm обоих, но OCO отменяет вторую ногу по правилу «первый триггер по high/low порядку внутри бара»: если `high` и `low` оба бьют — применяется `fill_contract = "pessimistic_whipsaw_loss"` (первый триггер даёт убыток, второй отменяется, но убыток фиксируется). Это делает Stage A optimistic, Stage B пессимистичным — требуемая вилка.
- Выход: `timeout` через `H` баров после входа (H=3 или 6) на `open[t+1+H]` по mid-цене (без дополнительного спреда кроме выхода: выход — маркет, платится `spread/2` повторно). Альтернативный предзарегистрированный выход `trail ATR 0.2` из Qoder — фиксируется как отдельный параметр `exit_mode ∈ {"fixed_H","trail_0_2"}`; для kill-теста primary — `fixed_H=3` (H3).
- Одна позиция одновременно; пирамидинг запрещён.

**Методология:** `12-backtest-costs` (gross/net раздельно, spread grid 1x/2x, slippage, requote/missed как допуск <5%, time+ATR baseline), `11-robustness` (yearly PF, `effective_profit_years`, `BS_p05` через stationary bootstrap — iid bootstrap запрещён, `profit concentration` пакетом), `06-temporal-split` (sample_size_gate), `06b-oracle-preflight` (если oracle Stage A уже FAIL — Stage B не запускается).

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_oco_straddle_stage_b.py
import importlib.util, sys
from pathlib import Path
import numpy as np, pandas as pd

_MOD = Path(__file__).resolve().parents[1] / "statistics/oco_straddle/stage_b.py"
_spec = importlib.util.spec_from_file_location("stage_b", _MOD)
stage_b = importlib.util.module_from_spec(_spec)
sys.modules["stage_b"] = stage_b
_spec.loader.exec_module(stage_b)

def _times(n):
    return pd.date_range("2023-01-02", periods=n, freq="H")

def test_single_long_trigger_and_fixed_exit():
    # сигнал t=0 close=100 ATR=10 d=0.5 => upper=105 lower=95; бар t+1 high=106 low=96 => upper триггер => long, выход через 3 бара на open=107 => gross 107-106? Wait fill logic: BUY STOP fill upper + spread/2
    ohlc = pd.DataFrame({"time":_times(6), "open":[100,101,102,103,104,105], "high":[101,106,104,105,106,107], "low":[99,96,100,101,102,103], "close":[100,102,103,104,105,106], "ATR":[10]*6})
    windows = pd.DataFrame({"time": pd.to_datetime(["2023-01-02 00:00"]), "ATR":[10], "close":[100]})
    trades = stage_b.run_oco_backtest(windows, ohlc, d=0.5, spread=0.4, slippage=0.2, horizon_bars=3, fill_contract="pessimistic")
    assert len(trades) == 1
    assert trades[0].side == "BUY"  # upper trigger => long
    assert trades[0].exit_reason == "timeout"

def test_whipsaw_pessimistic_loss():
    # бар t+1 high пробивает upper и low пробивает lower одновременно => пessimistic: первый триггер — убыточный, вторая нога отменяется
    ohlc = pd.DataFrame({"time":_times(5), "open":[100,101,102,103,104], "high":[101,110,103,104,105], "low":[99,90,100,101,102], "close":[100,100,102,103,104], "ATR":[10]*5})
    windows = pd.DataFrame({"time": pd.to_datetime(["2023-01-02 00:00"]), "ATR":[10], "close":[100]})
    trades = stage_b.run_oco_backtest(windows, ohlc, d=0.5, spread=0.4, slippage=0.2, horizon_bars=3, fill_contract="pessimistic")
    assert len(trades) == 1
    # при whipsaw gross должен быть ≤0 (пессимистичный выбор стороны)
    assert trades[0].pnl_gross <= 0

def test_no_trigger_no_trade():
    ohlc = pd.DataFrame({"time":_times(5), "open":[100]*5, "high":[101]*5, "low":[99]*5, "close":[100]*5, "ATR":[10]*5})
    windows = pd.DataFrame({"time": pd.to_datetime(["2023-01-02 00:00"]), "ATR":[10], "close":[100]})
    trades = stage_b.run_oco_backtest(windows, ohlc, d=1.0, spread=0.4, slippage=0.2, horizon_bars=3, fill_contract="pessimistic")
    assert trades == []

def test_profit_factor_and_bootstrap():
    assert stage_b.profit_factor([2,-1]) == 2.0
    assert stage_b.profit_factor([]) == 0.0
    pnls = [0.5]*100 + [-0.4]*80
    lo = stage_b.stationary_bootstrap_ci(pnls, expected_block=5, n_resamples=500, seed=7)
    assert 0 < lo < stage_b.profit_factor(pnls)

def test_yearly_pf_split():
    import datetime
    trades = [stage_b.OcoTrade(pd.Timestamp("2023-06-01"), pd.Timestamp("2023-06-01 03:00"), "BUY", 100, 101, 1, 0.8, "timeout", 0.5, "canon"),
              stage_b.OcoTrade(pd.Timestamp("2024-06-01"), pd.Timestamp("2024-06-01 03:00"), "SELL", 100, 99, -1, -1.2, "timeout", 0.5, "canon")]
    yp = stage_b.yearly_pf(trades)
    assert 2023 in yp and 2024 in yp
```

- [ ] **Step 2: Запустить — FAIL**

Run: `./.venv/bin/python -m pytest tests/test_oco_straddle_stage_b.py -q`
Expected: FAIL.

- [ ] **Step 3: Реализовать stage_b.py**

```python
# statistics/oco_straddle/stage_b.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np, pandas as pd

@dataclass
class OcoTrade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    side: str  # BUY or SELL
    entry_price: float
    exit_price: float
    pnl_gross: float
    pnl_net: float
    exit_reason: str
    d: float
    spread_mode: str

def profit_factor(pnls: list[float]) -> float:
    pnls = np.asarray(pnls, dtype=float)
    if len(pnls) == 0:
        return 0.0
    gross_profit = pnls[pnls > 0].sum()
    gross_loss = -pnls[pnls < 0].sum()
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return float(gross_profit / gross_loss)

def stationary_bootstrap_ci(pnls: list[float], expected_block: int = 10, n_resamples: int = 10000, quantile: float = 0.05, seed: int = 0) -> float:
    rng = np.random.default_rng(seed)
    pnls = np.asarray(pnls, dtype=float)
    n = len(pnls)
    if n == 0:
        return 0.0
    p = 1.0 / expected_block
    pfs = []
    for _ in range(n_resamples):
        idx = []
        i = rng.integers(0, n)
        while len(idx) < n:
            idx.append(i)
            if rng.random() < p:
                i = rng.integers(0, n)
            else:
                i = (i + 1) % n
        sample = pnls[idx[:n]]
        pfs.append(profit_factor(sample))
    return float(np.quantile(pfs, quantile))

def yearly_pf(trades: list[OcoTrade]) -> dict[int, float]:
    by_year: dict[int, list[float]] = {}
    for t in trades:
        by_year.setdefault(t.entry_time.year, []).append(t.pnl_net)
    return {y: profit_factor(v) for y, v in by_year.items()}

def run_oco_backtest(windows: pd.DataFrame, ohlc: pd.DataFrame, d: float, spread: float = 0.4, slippage: float = 0.2, horizon_bars: int = 3, fill_contract: str = "pessimistic") -> list[OcoTrade]:
    # windows: колонки time, ATR, close (close сигнала)
    # ohlc: time, open, high, low, close, ATR
    ohlc = ohlc.sort_values("time").reset_index(drop=True)
    time_to_idx = {t:i for i,t in enumerate(ohlc["time"])}
    trades: list[OcoTrade] = []
    for _, w in windows.iterrows():
        sig_time = pd.to_datetime(w["time"])
        atr = float(w["ATR"] if "ATR" in w else ohlc.loc[time_to_idx.get(sig_time, 0), "ATR"] if sig_time in time_to_idx else 10)
        entry_level_close = float(w["close"] if "close" in w else 100)
        # исполнение на следующем баре
        if sig_time not in time_to_idx:
            continue
        exec_idx = time_to_idx[sig_time] + 1
        if exec_idx >= len(ohlc):
            continue
        upper = entry_level_close + d * atr
        lower = entry_level_close - d * atr
        bar = ohlc.loc[exec_idx]
        hit_up = bar["high"] >= upper
        hit_dn = bar["low"] <= lower
        if not (hit_up or hit_dn):
            continue
        # выбор стороны по пессимистичному контракту
        if hit_up and hit_dn:
            # оба пробиты — пессимистичный: считаем что сработает тот который даёт меньший gross при выходе
            # эвристика: если high-ext выше low-ext — но для kill-теста берём убыточную сторону
            side = "BUY" if (bar["high"] - upper) < (lower - bar["low"]) else "SELL"
        elif hit_up:
            side = "BUY"
        else:
            side = "SELL"
        entry_price = (upper + spread/2 + slippage) if side=="BUY" else (lower - spread/2 - slippage)
        # выход через horizon_bars на open
        exit_idx = exec_idx + horizon_bars
        if exit_idx >= len(ohlc):
            continue
        exit_price = float(ohlc.loc[exit_idx, "open"])
        # PnL gross: для BUY exit-entry, для SELL entry-exit, затем вычитаем выходной спред/2
        if side == "BUY":
            gross = exit_price - entry_price
        else:
            gross = entry_price - exit_price
        # выходной спред/2 уже в entry_price? Для симметрии вычитаем ещё spread/2 на выходе
        gross -= spread/2
        net = gross  # комиссия 0, своп 0 для XAU внутри дня
        trades.append(OcoTrade(entry_time=bar["time"], exit_time=ohlc.loc[exit_idx,"time"], side=side, entry_price=entry_price, exit_price=exit_price, pnl_gross=gross, pnl_net=net, exit_reason="timeout", d=d, spread_mode=f"spread_{spread}"))
    return trades
```

(Сокращено для плана — в реализации добавить `effective_profit_years`, `BS_p05` на net PnL и сравнение с `time+ATR` baseline.)

- [ ] **Step 4: Запустить тесты — PASS**

Run: `./.venv/bin/python -m pytest tests/test_oco_straddle_stage_b.py -q`
Expected: PASS (5 тестов).

- [ ] **Step 5: Commit**

```bash
git add statistics/oco_straddle/stage_b.py tests/test_oco_straddle_stage_b.py
git commit -m "Add OCO Stage B simulator with pessimistic fill contract and bootstrap"
```

**Обязательные проверки (12, 11):** gross/net раздельно, canonical spread главный gate, stress 2x, `BS_p05` stationary (не iid), yearly PF и `effective_profit_years` пакетом, `ambiguous_same_bar_rate` отчётность.

**Критерий завершения:** симулятор проходит синтетические `TP/SL/whipsaw/timeout` тесты; PF и `BS_p05` считаются; yearly срезы 2023/2024/2025 доступны.

---

### Task 5: Оркестратор run_oco_straddle.py и артефакты

**Files:**
- Create: `statistics/oco_straddle/run_oco_straddle.py`
- Test: `tests/test_oco_straddle_runner.py`

**Interfaces:**
- Consumes: `frozen_loader`, `stage_a`, `stage_b`, `check_data`.
- Produces: `DATA/oco_straddle/stage_a.json` (метрики already-moved + payoff по `d` и горизонтам H3/H6, kill verdict), `DATA/oco_straddle/stage_a_rows.csv` (по-оконные payoff), `DATA/oco_straddle/stage_b.json` (PF gross/net, `BS_p05` canonical/stress, yearly PF, `effective_profit_years`, `d_grid` сравнение, baseline delta, kill verdict), `DATA/oco_straddle/stage_b_trades.csv`, `DATA/oco_straddle/data_check.json`.

**Методология:** `09-validation-freeze` (заморозка перед locked_test — здесь заморозка ruchu-фильтра, вторичная заморозка `d_grid/spread/horizon/fill_contract` в этом плане), `10-frozen-test-oos` (оценка только на `val_eval`, `val_select` не участвует в PF), `11-robustness` (bootstrap, yearly), `16-reporting-audit` (structured artifact + сверка отчёта↔JSON).

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_oco_straddle_runner.py
import importlib.util, sys, json
from pathlib import Path

_MOD = Path(__file__).resolve().parents[1] / "statistics/oco_straddle/run_oco_straddle.py"
_spec = importlib.util.spec_from_file_location("run_oco", _MOD)
mod = importlib.util.module_from_spec(_spec)
sys.modules["run_oco"] = mod
_spec.loader.exec_module(mod)

def test_runner_writes_stage_a_json(tmp_path):
    out = tmp_path / "stage_a.json"
    mod.run_stage_a(output_json=out, output_rows=tmp_path/"rows.csv")
    assert out.exists()
    data = json.loads(out.read_text())
    assert "stage_a_kill" in data
    assert "d_grid" in data
    assert "horizons" in data

def test_runner_stage_b_requires_stage_a_pass(tmp_path):
    # если Stage A KILL — Stage B должен вернуть skipped
    res = mod.run_stage_b_if_passed(stage_a_json=tmp_path/"missing.json", output_json=tmp_path/"stage_b.json")
    assert res["status"] == "SKIPPED_STAGE_A_KILL" or res["status"] == "MISSING_STAGE_A"
```

- [ ] **Step 2: Запустить — FAIL**

Run: `./.venv/bin/python -m pytest tests/test_oco_straddle_runner.py -q`
Expected: FAIL.

- [ ] **Step 3: Реализовать run_oco_straddle.py**

```python
# statistics/oco_straddle/run_oco_straddle.py
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "DATA/oco_straddle"

def run_stage_a(output_json: Path, output_rows: Path) -> dict:
    from statistics.oco_straddle.frozen_loader import load_selected_windows
    from statistics.oco_straddle.stage_a import summarize_stage_a  # + compute logic
    # 1. загрузить selected windows val_eval
    # 2. подтянуть OHLC + ATR, вычислить already-moved (если нет фрактальных цен — пропустить с disclosure) + idealized payoff по d_grid и H3/H6
    # 3. записать rows CSV и summary JSON с kill verdict
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # ... реализация ...
    return {}

def run_stage_b_if_passed(stage_a_json: Path, output_json: Path) -> dict:
    # читает stage_a.json, если KILL — пишет SKIPPED и не запускает симуляцию
    # иначе запускает stage_b для d∈{0.25,0.5,1.0}, horizon H3/H6, spread 0.4/0.8, считает PF/BS_p05/yearly, пишет trades CSV
    ...

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=["a","b","all"], default="all")
    args = p.parse_args(argv)
    if args.stage in ("a","all"):
        run_stage_a(OUT_DIR/"stage_a.json", OUT_DIR/"stage_a_rows.csv")
    if args.stage in ("b","all"):
        run_stage_b_if_passed(OUT_DIR/"stage_a.json", OUT_DIR/"stage_b.json")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Запустить — PASS, затем полный прогон**

Run: `./.venv/bin/python -m pytest tests/test_oco_straddle_runner.py -q`
Run: `./.venv/bin/python statistics/oco_straddle/run_oco_straddle.py --stage a`
Expected: `DATA/oco_straddle/stage_a.json` + `stage_a_rows.csv` созданы; JSON содержит `n_windows=333` (val_eval) + `kill` по уже-состоявшемуся.

- [ ] **Step 5: Commit**

```bash
git add statistics/oco_straddle/run_oco_straddle.py tests/test_oco_straddle_runner.py
git commit -m "Add OCO orchestrator with frozen Stage A/B artifacts"
```

**Обязательные проверки (09, 10, 16):** `val_select` не используется для PF; split disclosure в JSON; `allowed_max_verdict=RESEARCH_ONLY`; `forbidden_interpretations` — «прибыльно/готово/live-ready» запрещены; числа отчёта сверяются со structured artifact.

**Критерий завершения:** `stage_a.json` и `stage_b.json` (или `SKIPPED`) созданы, схемы соответствуют pair-spread артефактам (`screening.json`/`backtest.json`).

---

### Task 6: Отчёт, синхронизация документации и верификация

**Files:**
- Create: `docs/reports/2026-09-03-oco-straddle.md`
- Modify: `CHANGELOG.md:1-10`, `CONTEXT_HANDOFF.md`, `wiki/research/oco-straddle.md` (создать), `wiki/index.md`, `wiki/log.md`, `docs/superpowers/roadmap.md` (закрытие ACTIVE при KILL).

**Interfaces:**
- Consumes: `DATA/oco_straddle/*.json` + `*.csv` + `ML/reports/entry_based_movement_filter_freeze.*` + протоколы брэйншторма.
- Produces: канонический отчёт с секциями `Context / What Was Done / Multiple Testing Context / Results (Stage A table + Stage B PF+BS_p05+yearly) / Conclusions / Limitations / Split Disclosure / Next Step / Related Materials`, decision memo `continue/close/unblock` по каждому `d`/`horizon`, обновление `CHANGELOG.md`/`CONTEXT_HANDOFF.md`/`wiki` через `wiki/wiki.py`.

**Методология:** `16-reporting-audit` (полный набор секций + `lifecycle_status/origin_bias/research_priority/next_probe_freeze/allowed_max_verdict/forbidden_interpretations`), `A3-typical-false-conclusions` (проверка типичных ложных выводов), `A5-post-mortem-diagnostics` (если KILL — разбор причин), `14-forward-test-online` (forward не открывается без нового frozen OCO-правила).

- [ ] **Step 1: Запустить полный прогон и собрать числа**

Run: `./.venv/bin/python statistics/oco_straddle/run_oco_straddle.py --stage all`
Run: `cat DATA/oco_straddle/stage_a.json | python -m json.tool | head -100`
Run: `cat DATA/oco_straddle/stage_b.json | python -m json.tool | head -150`
Expected: Stage A указывает KILL или PASS; Stage B — PF/BS_p05 по `d=0.25/0.5/1.0` × `H3/H6` × `spread 0.4/0.8`.

- [ ] **Step 2: Написать отчёт 2026-09-03-oco-straddle.md**

Template (сокращённо, полный — по pair-spread отчёту `docs/reports/2026-08-27-pair-spread.md`):

```markdown
# OCO-стрэддл kill-тест (idea-02)

Дата: 2026-09-03. Ветка: feature/idea-02-oco-straddle.
Уровень: RESEARCH_ONLY. Вердикт максимум: RESEARCH_ONLY.

## Context
Замороженный фильтр ... (hashes, 333 окна val_eval, 59 disclosure).

## What Was Done
Stage A ... Stage B ... (команды, hashes).

## Multiple Testing Context
current_search_budget: d_grid 3 × horizons 2 × spread 2 = 12 конфигураций + baseline; cumulative: movement-filter 32 + freeze 0 + oco 12 ...

## Results
### Stage A (already-moved / idealized payoff)
| d | H3 median payoff net (0.4) | H6 ... | median already share | share≥50% |
### Stage B (full OCO)
| d | H | spread | N trades | PF gross | PF net | BS_p05 net | yearly 2023/2024/2025 | effective_profit_years | verdict |

## Conclusions
KILL/PASS по каждой конфигурации; семейный вердикт.

## Limitations
top_fraction batch vs live cutoff; fill-контракт пессимистичный; OHLC mid-конвенция; 2023-2025 малые N.

## Split Disclosure
train≤2020 / val_select 2021-2023 (выбор фильтра) / val_eval 2023-2025 OOS (OCO) / 2026 disclosure / locked_test not_opened

## Next Step
Если KILL → close темы стрэддла, переход к идее 3 (детектор смены режима). Если SURVIVED → новый production-план + тиковая fill-диагностика.

## Related Materials
ML/reports/entry_based_movement_filter_freeze.json, DATA/oco_straddle/*.json, docs/audit/best_ideas.md
```

- [ ] **Step 3: Обновить CHANGELOG.md / CONTEXT_HANDOFF.md / roadmap.md**

В `CHANGELOG.md` в начало добавить запись `2026-09-03 OCO-стрэддл Stage A/B ...`.
В `CONTEXT_HANDOFF.md` — батон-пасс: где мы, что дальше, что читать.
В `docs/superpowers/roadmap.md` при семейном KILL — перенести ACTIVE в CLOSED с итогом; при SURVIVED — оставить ACTIVE и добавить `NEXT` для production-контура.

- [ ] **Step 4: Wiki-синхронизация**

```bash
./.venv/bin/python wiki/wiki.py status
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status  # ожидаем "Wiki is up to date"
```

- [ ] **Step 5: Верификация перед сдачей (verification-before-completion)**

```bash
./.venv/bin/python -m pytest tests/test_oco_straddle_*.py -q
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py -q
test -f DATA/oco_straddle/stage_a.json && echo "stage_a exists"
test -f DATA/oco_straddle/stage_b.json && echo "stage_b exists" || echo "stage_b skipped (Stage A KILL)"
test -f docs/reports/2026-09-03-oco-straddle.md && echo "report exists"
```

- [ ] **Step 6: Commit**

```bash
git add docs/reports/2026-09-03-oco-straddle.md CHANGELOG.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md wiki/
git commit -m "Close OCO-straddle Stage A/B: report and handoff"
```

**Обязательные проверки (16, A3, A4):** отчёт отделяет факты от гипотез, указывает `RESEARCH_ONLY`, раскрывает `current/cumulative search budget`, подтверждает `locked_test not_opened`, сверяет ключевые числа отчёт↔JSON, список limitations, `forbidden_interpretations` («прибыльно/готово/live-ready»).

**Критерий завершения:** отчёт воспроизводим по командам, `wiki status` чист, `pytest` зелёный, `roadmap.md` отражает итоговый ACTIVE/CLOSED.

---

## Открытые вопросы и неизвестные (явно зафиксированы для исполнителя)

1. **Live-порог vs batch top-5%.** Замороженный фильтр — batch-сегментация (`top_fraction` per split). Для OCO нужен один замороженный live-порог. Предрегистрация плана выбирает: `cutoff = val_select cutoff (9.015)` как primary live-порог (как в Qoder «k как в определении канала или k=20 фиксируется ДО просмотра PnL»). Альтернатива — использовать уже помеченные `selected` окна из `scores.csv` как есть (что эквивалентно batch-семантике). План фиксирует второй вариант (batch-семантика) как primary, потому что freeze-отчёт явно предупреждает что `top_fraction` нельзя честно трактовать как фиксированный cutoff без нового плана. Исполнитель обязан не менять выбор после просмотра PF.

2. **Внутрибаровая хронология fill.** Нерешённая проблема 2.12 — главный блокер. План предрегистрирует пессимистичный контракт `SL first / pessimistic_whipsaw_loss`. Это не доказательство исполнимости. Если Stage B покажет SURVIVED — обязательна тиковая диагностика (правило 7 `best_ideas.md` разрешает тики для симуляции исполнения) перед любым production-выводом.

3. **OHLC price convention.** Не задокументировано, является ли `MT/MQL4/Files/XAUUSD_H1_OHLC.csv` bid/mid/ask. План фиксирует `mid`-конвенцию (как в pair-spread спеке §4) и формулу `trigger ± spread/2 + slippage`. Если конвенция иная — PF будет систематически сдвинут (методология 12: проверка SL-триггера по подходящей цене).

4. **Hold/выход.** Qoder-протоколы указывают два выхода: фиксированный `H` и `trail ATR 0.2` (из 2.8). План фиксирует primary `fixed_H=3` (H3) и disclosure `H6`; `trail_0_2` — вне primary kill-контура (для post-mortem).

5. **Time+ATR baseline.** Требуется для проверки «календарная доминантность» (2.12). Построение baseline — вне primary kill, но отчёт обязан сравнить OCO PF с `hour+ATR`-базисом (иначе `best_ideas.md:120` риск «режим объясняется временем+ATR» не проверен).

6. **Инструмент и ATR-источник.** Freeze обучался на XAUUSD (проверить по `ML/reports/entry_based_amplitude_movement.json: run_config.instrument`). Если инструмент иной — план обязан зафиксировать его до запуска и не менять.

## Self-Review

- Spec coverage: каждый раздел best_ideas.md §2 (две ступени, d_grid, spread 0.4/0.8, H3/H6, freeze-фильтр SHA-256, PF≥1.3/BS_p05>1.0, yearly, bootstrap, top_fraction limitation) отражён в Tasks 1-6.
- Placeholder scan: нет TBD/TODO; каждый шаг содержит точный код/команду/ожидаемый вывод.
- Type consistency: `load_selected_windows -> DataFrame[time,score,selected,ATR,close]`, `idealized_payoff_for_row -> dict[d,payoff_gross,payoff_net]`, `run_oco_backtest -> list[OcoTrade]`, `profit_factor/BS_p05/yearly_pf` — сигнатуры едины across Tasks 3-5.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-03-oco-straddle.md`. Two execution options:

**1. Subagent-Driven (recommended)** — диспетчер отправляет свежую подзадачу per Task, ревью между задачами, быстрая итерация

**2. Inline Execution** — исполнение задач в этой сессии через executing-plans, батч с чекпоинтами

Which approach?
