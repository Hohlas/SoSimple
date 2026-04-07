# Validation-First Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Перенести весь подбор логики входа/выхода на `validation`, заморозить `test` как одноразовую финальную проверку и убрать эффект “победителей на маленьком N”.

**Architecture:** MT4-совместимый `ml_signals.csv` остаётся без изменений. Для исследований добавляется отдельный каталог сигналов с полем `source_split`, после чего `signal_research`, `signal_quality_research` и `signal_path_atlas` переходят на общий модуль разбиения выборок и поддержку двух режимов: `validation_research` и `test_final`. Финальная проверка читается из заранее сохранённого JSON-описания правила, чтобы `test` больше не участвовал в поиске.

**Tech Stack:** Python 3.11+, pandas, numpy, pytest, JSON

---

### Task 0: Re-anchor the current stop point from Archetype × Filter Bridge

**Files:**
- Modify: `API/signal_quality_research.py`
- Modify: `API/generate_signals.py`
- Modify: `tests/test_signal_quality_research.py`

- [ ] **Step 1: Write the failing test for bridge baseline registration**

```python
# tests/test_signal_quality_research.py
import API.signal_quality_research as sqr


def test_bridge_baselines_include_fav_filter_and_ratio_benchmark():
    rules = sqr.build_bridge_baselines()
    names = [rule['name'] for rule in rules]
    assert 'fav3_market_baseline' in names
    assert 'ratio3_pullback_benchmark' in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q`
Expected: FAIL with `AttributeError: module 'API.signal_quality_research' has no attribute 'build_bridge_baselines'`

- [ ] **Step 3: Register the current bridge winner and the benchmark candidate**

```python
# API/signal_quality_research.py
def build_bridge_baselines() -> list[dict]:
    return [
        {
            'name': 'fav3_market_baseline',
            'filters': [{'feature': 'fav_3_vs_12', 'op': '<=', 'value': 0.653}],
            'entry_mode': 'market',
        },
        {
            'name': 'ratio3_pullback_benchmark',
            'filters': [{'feature': 'ratio_3_vs_12', 'op': '>', 'value': 4.751}],
            'entry_mode': 'pullback_1atr',
        },
    ]
```

- [ ] **Step 4: Seed the first validation search with replicated spread features**

```python
# API/signal_quality_research.py
BRIDGE_SEARCH_FEATURES = [
    'fav_3_vs_12',
    'spread_3_vs_12',
    'spread_6_vs_24',
    'spread_12_vs_48',
    'ratio_12_vs_48',
]
```

- [ ] **Step 5: Run the bridge baseline smoke check**

Run: `./.venv/bin/python -m API.signal_quality_research --split-profile validation_research`
Expected: first printed table includes `fav3_market_baseline` as the frozen baseline and `ratio3_pullback_benchmark` as benchmark only


### Task 1: Research-only каталог сигналов с меткой источника

**Files:**
- Modify: `API/generate_signals.py`
- Create: `tests/test_generate_signals_research.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_generate_signals_research.py
import pandas as pd
import API.generate_signals as gs


def test_build_research_catalog_keeps_source_split():
    train = pd.DataFrame({'time': ['2024.01.01 00:00'], 'signal': [1]})
    val = pd.DataFrame({'time': ['2025.01.01 00:00'], 'signal': [-1]})
    test = pd.DataFrame({'time': ['2026.01.01 00:00'], 'signal': [0]})

    out = gs.build_research_catalog([
        ('train', train),
        ('validation', val),
        ('test', test),
    ])

    assert out['source_split'].tolist() == ['train', 'validation', 'test']
    assert out['time'].tolist() == ['2024.01.01 00:00', '2025.01.01 00:00', '2026.01.01 00:00']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_generate_signals_research.py -q`
Expected: FAIL with `AttributeError: module 'API.generate_signals' has no attribute 'build_research_catalog'`

- [ ] **Step 3: Add research catalog builder**

```python
# API/generate_signals.py
def build_research_catalog(named_frames: list[tuple[str, pd.DataFrame]]) -> pd.DataFrame:
    chunks = []
    for split_name, frame in named_frames:
        chunk = frame.copy()
        chunk['source_split'] = split_name
        chunks.append(chunk)
    out = pd.concat(chunks, ignore_index=True)
    out = out.sort_values('time').reset_index(drop=True)
    return out
```

- [ ] **Step 4: Export the catalog alongside MT4 CSV**

```python
# API/generate_signals.py
catalog_path = REPORTS_DIR / 'ml_signals_research.csv'
catalog = build_research_catalog([
    ('train', train_df),
    ('validation', val_df),
    ('test', test_df),
])
catalog.to_csv(catalog_path, sep=';', index=False)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_generate_signals_research.py -q`
Expected: PASS


### Task 2: Общий модуль split-профилей для исследований

**Files:**
- Create: `API/research_split_profiles.py`
- Modify: `API/signal_research.py`
- Modify: `API/signal_quality_research.py`
- Modify: `API/signal_path_atlas.py`
- Modify: `tests/test_signal_research.py`
- Modify: `tests/test_signal_quality_research.py`
- Modify: `tests/test_signal_path_atlas.py`

- [ ] **Step 1: Write the failing tests for split profiles**

```python
# tests/test_signal_quality_research.py
from API import research_split_profiles as rsp


def test_validation_research_profile_uses_only_validation_rows():
    assert rsp.get_profile('validation_research')['research_split'] == 'validation'
    assert rsp.get_profile('validation_research')['confirm_split'] == 'test'


def test_test_final_profile_is_read_only():
    profile = rsp.get_profile('test_final')
    assert profile['search_enabled'] is False
    assert profile['research_split'] == 'test'
```

- [ ] **Step 2: Run targeted tests to verify they fail**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q`
Expected: FAIL with `ImportError` for `research_split_profiles`

- [ ] **Step 3: Implement the shared profile helper**

```python
# API/research_split_profiles.py
PROFILES = {
    'validation_research': {
        'research_split': 'validation',
        'confirm_split': 'test',
        'search_enabled': True,
    },
    'test_final': {
        'research_split': 'test',
        'confirm_split': None,
        'search_enabled': False,
    },
}


def get_profile(name: str) -> dict:
    if name not in PROFILES:
        raise ValueError(f'Unknown split profile: {name}')
    return dict(PROFILES[name])
```

- [ ] **Step 4: Wire all research CLIs to the shared profile**

```python
# API/signal_quality_research.py
from API.research_split_profiles import get_profile

parser.add_argument(
    '--split-profile',
    choices=['validation_research', 'test_final'],
    default='validation_research',
)

profile = get_profile(args.split_profile)
```

- [ ] **Step 5: Replace hard-coded discovery/holdout semantics where needed**

```python
# API/signal_research.py
if args.split_profile == 'validation_research':
    frame = frame[frame['source_split'] == 'validation'].copy()
else:
    frame = frame[frame['source_split'] == 'test'].copy()
```

- [ ] **Step 6: Run the updated test suite**

Run: `./.venv/bin/python -m pytest tests/test_signal_research.py tests/test_signal_quality_research.py tests/test_signal_path_atlas.py -q`
Expected: PASS


### Task 3: Правила входа/выхода только на validation + жёсткие пороги поддержки

**Files:**
- Create: `API/final_rule_check.py`
- Modify: `API/signal_quality_research.py`
- Modify: `API/signal_research.py`
- Create: `tests/test_final_rule_check.py`

- [ ] **Step 1: Write the failing test for frozen rule evaluation**

```python
# tests/test_final_rule_check.py
from API.final_rule_check import apply_rule_frame
import pandas as pd


def test_apply_rule_frame_filters_on_explicit_threshold():
    frame = pd.DataFrame({
        'ratio_12': [2.0, 3.2, 5.0],
        'fav_3_vs_12': [0.80, 0.60, 0.50],
    })
    rule = {
        'filters': [
            {'feature': 'ratio_12', 'op': '>=', 'value': 3.0},
            {'feature': 'fav_3_vs_12', 'op': '<=', 'value': 0.65},
        ]
    }
    out = apply_rule_frame(frame, rule)
    assert len(out) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_final_rule_check.py -q`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement explicit frozen-rule runner**

```python
# API/final_rule_check.py
OPS = {
    '>=': lambda s, v: s >= v,
    '<=': lambda s, v: s <= v,
}


def apply_rule_frame(frame: pd.DataFrame, rule: dict) -> pd.DataFrame:
    mask = pd.Series(True, index=frame.index)
    for cond in rule['filters']:
        mask &= OPS[cond['op']](frame[cond['feature']], cond['value'])
    return frame[mask].copy()
```

- [ ] **Step 4: Enforce support gates in validation search**

```python
# API/signal_quality_research.py
MIN_TRADES_VALIDATION = 80
MIN_TRADES_YEAR = 20

if len(filtered) < MIN_TRADES_VALIDATION:
    continue
if any(year_count < MIN_TRADES_YEAR for year_count in yearly_counts.values()):
    continue
```

- [ ] **Step 5: Persist chosen rule as JSON**

```python
rule_path = REPORTS_DIR / 'frozen_validation_rule.json'
rule_path.write_text(json.dumps(rule, ensure_ascii=False, indent=2), 'utf-8')
```

- [ ] **Step 6: Run tests and one smoke command**

Run: `./.venv/bin/python -m pytest tests/test_final_rule_check.py tests/test_signal_quality_research.py -q`
Expected: PASS

Run: `./.venv/bin/python -m API.final_rule_check --rule ML/reports/frozen_validation_rule.json`
Expected: prints one final table on `test`, no rule search


### Task 4: Documentation and operator guardrails

**Files:**
- Modify: `API/README.md`
- Modify: `CONTEXT_HANDOFF.md`

- [ ] **Step 1: Document the new operating mode**

```md
1. Search on `validation_research`
2. Freeze rule JSON
3. Confirm once on `test_final`
4. Do not tune thresholds after reading test results
```

- [ ] **Step 2: Update current handoff to reflect the protocol**

Run: `sed -n '1,120p' CONTEXT_HANDOFF.md`
Expected: enough context to update `Next Step` and `Open Risks`

- [ ] **Step 3: Verify the docs references**

Run: `./.venv/bin/python -m pytest tests/test_signal_research.py tests/test_signal_quality_research.py tests/test_signal_path_atlas.py tests/test_final_rule_check.py -q`
Expected: PASS
