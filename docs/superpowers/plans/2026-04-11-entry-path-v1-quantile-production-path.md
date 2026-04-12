# Entry Path v1 Quantile Production Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Сделать `entry_path_v1_quantile` официальным production export path для MT4 через один канонический manifest и короткую production-команду, сохранив baseline как backup/legacy path.

**Architecture:** Работа остаётся в одном exporter-е `API/export_entry_path_v1_quantile_signals.py`. Поверх текущего explicit `--seed-dir` добавляется production mode `--production`, который читает отдельный manifest `ML/reports/entry_path_v1_quantile_production_manifest.json`, разрешает активный frozen run и выпускает тот же самый `time;signal` CSV без re-fit. Docs обновляются так, чтобы quantile path был рекомендованным operational путём, а baseline — fallback.

**Tech Stack:** Python 3.12, argparse, json, pathlib, pandas, numpy, pytest

---

## File Map

### Read First
- `AGENTS.md`
- `docs/superpowers/specs/2026-04-11-entry-path-v1-quantile-production-path-design.md`
- `API/export_entry_path_v1_quantile_signals.py`
- `tests/test_export_entry_path_v1_quantile_signals.py`
- `docs/MT/ml_signal_integration.md`
- `API/README.md`
- `MODULE_INDEX.md`

### Files To Create
- `ML/reports/entry_path_v1_quantile_production_manifest.json`
- `docs/superpowers/plans/2026-04-11-entry-path-v1-quantile-production-path.md`

### Files To Modify
- `API/export_entry_path_v1_quantile_signals.py`
- `tests/test_export_entry_path_v1_quantile_signals.py`
- `docs/MT/ml_signal_integration.md`
- `API/README.md`
- `MODULE_INDEX.md`

### Optional File To Modify
- `docs/MT/trading_strategy.md` only if implementation uncovers a new runtime nuance not already documented

---

### Task 1: Add Production Manifest Contract

**Files:**
- Create: `ML/reports/entry_path_v1_quantile_production_manifest.json`
- Modify: `tests/test_export_entry_path_v1_quantile_signals.py`

- [ ] **Step 1: Write the failing tests for production manifest resolution**

Add these tests to `tests/test_export_entry_path_v1_quantile_signals.py`:

```python
def _write_production_manifest(tmp_path: Path, *, seed_dir: Path, split: str = 'test', winner_rule: str = 'lb_gt_m') -> Path:
    manifest_path = tmp_path / 'entry_path_v1_quantile_production_manifest.json'
    manifest_path.write_text(
        json.dumps(
            {
                'seed_dir': str(seed_dir),
                'split': split,
                'winner_rule': winner_rule,
                'hold_bars': 24,
                'allow_reversal': False,
                'output_format': 'time;signal',
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )
    return manifest_path


def test_load_production_manifest_reads_expected_contract(tmp_path):
    seed_dir = _write_seed_dir(tmp_path, split='test')
    manifest_path = _write_production_manifest(tmp_path, seed_dir=seed_dir)

    payload = exporter.load_production_manifest(manifest_path)

    assert payload['seed_dir'] == str(seed_dir)
    assert payload['split'] == 'test'
    assert payload['winner_rule'] == 'lb_gt_m'
    assert payload['hold_bars'] == 24
    assert payload['allow_reversal'] is False
    assert payload['output_format'] == 'time;signal'


def test_resolve_export_request_rejects_production_and_seed_dir_together(tmp_path):
    seed_dir = _write_seed_dir(tmp_path, split='test')
    manifest_path = _write_production_manifest(tmp_path, seed_dir=seed_dir)

    try:
        exporter.resolve_export_request(
            production=True,
            manifest_path=manifest_path,
            seed_dir=seed_dir,
            split='test',
        )
    except ValueError as exc:
        assert 'cannot be used together' in str(exc)
    else:
        raise AssertionError('Expected ValueError for conflicting production/seed-dir inputs')
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_export_entry_path_v1_quantile_signals.py::test_load_production_manifest_reads_expected_contract \
  tests/test_export_entry_path_v1_quantile_signals.py::test_resolve_export_request_rejects_production_and_seed_dir_together \
  -q
```

Expected:
- FAIL with missing `load_production_manifest` / `resolve_export_request`

- [ ] **Step 3: Create the production manifest file with the real frozen source**

Create `ML/reports/entry_path_v1_quantile_production_manifest.json` with this exact content:

```json
{
  "seed_dir": "ML/reports/entry_path_v1_quantile_robustness/seed_123",
  "split": "test",
  "winner_rule": "lb_gt_m",
  "hold_bars": 24,
  "allow_reversal": false,
  "output_format": "time;signal"
}
```

- [ ] **Step 4: Re-run the same tests and keep them failing only on implementation gaps**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_export_entry_path_v1_quantile_signals.py::test_load_production_manifest_reads_expected_contract \
  tests/test_export_entry_path_v1_quantile_signals.py::test_resolve_export_request_rejects_production_and_seed_dir_together \
  -q
```

Expected:
- still FAIL, but only because exporter helpers are not implemented yet

- [ ] **Step 5: Commit the manifest contract and failing tests**

```bash
git add ML/reports/entry_path_v1_quantile_production_manifest.json tests/test_export_entry_path_v1_quantile_signals.py
git commit -m "test: add quantile production manifest contract"
```

---

### Task 2: Implement Production Mode In The Exporter

**Files:**
- Modify: `API/export_entry_path_v1_quantile_signals.py`
- Modify: `tests/test_export_entry_path_v1_quantile_signals.py`

- [ ] **Step 1: Extend the tests with production-mode behavior**

Add these tests:

```python
def test_export_signals_supports_production_manifest(tmp_path):
    seed_dir = _write_seed_dir(tmp_path, split='test')
    manifest_path = _write_production_manifest(tmp_path, seed_dir=seed_dir)
    output_path = tmp_path / 'ml_signals.csv'

    exporter.export_signals(
        output_path=output_path,
        production=True,
        manifest_path=manifest_path,
    )

    out = pd.read_csv(output_path, sep=';')
    assert out['signal'].tolist() == [1, 0, 0, 0]


def test_export_signals_rejects_manifest_rule_mismatch(tmp_path):
    seed_dir = _write_seed_dir(tmp_path, split='test')
    manifest_path = _write_production_manifest(tmp_path, seed_dir=seed_dir, winner_rule='baseline')
    output_path = tmp_path / 'ml_signals.csv'

    try:
        exporter.export_signals(
            output_path=output_path,
            production=True,
            manifest_path=manifest_path,
        )
    except ValueError as exc:
        assert 'winner_rule' in str(exc)
    else:
        raise AssertionError('Expected ValueError for manifest/rule mismatch')


def test_parse_args_accepts_production_mode():
    args = exporter.parse_args([
        '--production',
        '--manifest', 'ML/reports/entry_path_v1_quantile_production_manifest.json',
        '--output', 'MT/tester/files/ml_signals.csv',
    ])

    assert args.production is True
    assert args.seed_dir is None
    assert args.output == 'MT/tester/files/ml_signals.csv'
```

- [ ] **Step 2: Run the full exporter test file and verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py -q
```

Expected:
- FAIL on missing production-mode behavior

- [ ] **Step 3: Implement manifest-aware exporter logic**

Update `API/export_entry_path_v1_quantile_signals.py` to this shape:

```python
RULE_JSON = 'entry_path_v1_quantile_filter_selected_rule.json'
DEFAULT_MANIFEST = Path('ML/reports/entry_path_v1_quantile_production_manifest.json')


def load_production_manifest(path: str | Path) -> dict:
    manifest_path = Path(path)
    return json.loads(manifest_path.read_text(encoding='utf-8'))


def resolve_export_request(
    *,
    production: bool,
    manifest_path: str | Path | None,
    seed_dir: str | Path | None,
    split: str | None,
) -> tuple[Path, str]:
    if production and seed_dir is not None:
        raise ValueError('--production and --seed-dir cannot be used together')
    if production:
        payload = load_production_manifest(manifest_path or DEFAULT_MANIFEST)
        resolved_seed_dir = Path(payload['seed_dir'])
        resolved_split = split or payload['split']
        return resolved_seed_dir, resolved_split
    if seed_dir is None:
        raise ValueError('Either --production or --seed-dir is required')
    return Path(seed_dir), split or 'test'


def validate_manifest_against_rule(manifest: dict, rule_payload: dict) -> None:
    expected_rule = manifest['winner_rule']
    actual_rule = rule_payload['winner']['rule']
    if expected_rule != actual_rule:
        raise ValueError(f"Manifest winner_rule mismatch: {expected_rule} != {actual_rule}")


def export_signals(
    *,
    output_path: str | Path,
    production: bool = False,
    manifest_path: str | Path | None = None,
    seed_dir: str | Path | None = None,
    split: str | None = None,
    copy_to_mt4: bool = False,
) -> Path:
    resolved_seed_dir, resolved_split = resolve_export_request(
        production=production,
        manifest_path=manifest_path,
        seed_dir=seed_dir,
        split=split,
    )
    rule_payload = load_rule_payload(resolved_seed_dir)
    if production:
        manifest = load_production_manifest(manifest_path or DEFAULT_MANIFEST)
        validate_manifest_against_rule(manifest, rule_payload)
    frame = load_prediction_frame(resolved_seed_dir / f'entry_path_v1_quantile_{resolved_split}_predictions.csv')
    selected_mask = apply_frozen_rule(frame, rule_payload)
    export = frame[['time', 'signal']].copy()
    export.loc[~selected_mask, 'signal'] = 0
    ...
```

Update CLI parsing to use an explicit mutually exclusive group:

```python
def parse_args(argv=None):
    parser = argparse.ArgumentParser(description='Export frozen entry_path_v1_quantile signals for MT4.')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--production', action='store_true')
    mode.add_argument('--seed-dir')
    parser.add_argument('--manifest', default=str(DEFAULT_MANIFEST))
    parser.add_argument('--split', choices=['validation', 'test'])
    parser.add_argument('--output', required=True)
    parser.add_argument('--copy-to-mt4', action='store_true')
    return parser.parse_args(argv)
```

- [ ] **Step 4: Run the full exporter test file and verify it passes**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py -q
```

Expected:
- PASS

- [ ] **Step 5: Commit the production-mode exporter**

```bash
git add API/export_entry_path_v1_quantile_signals.py tests/test_export_entry_path_v1_quantile_signals.py ML/reports/entry_path_v1_quantile_production_manifest.json
git commit -m "feat: add production mode for quantile exporter"
```

---

### Task 3: Document Quantile As The Recommended Path

**Files:**
- Modify: `docs/MT/ml_signal_integration.md`
- Modify: `API/README.md`
- Modify: `MODULE_INDEX.md`

- [ ] **Step 1: Update docs with the production command and status change**

Make these edits:

In `docs/MT/ml_signal_integration.md`, replace the quantile command example with:

```bash
./.venv/bin/python -m API.export_entry_path_v1_quantile_signals \
  --production \
  --output MT/tester/files/ml_signals.csv \
  --copy-to-mt4
```

Also add these points in prose:

- `entry_path_v1_quantile` is now the recommended production export path for `iSignal=3`
- baseline score-based path remains available as backup / legacy
- production mode resolves the active frozen source through `ML/reports/entry_path_v1_quantile_production_manifest.json`

In `API/README.md`, add one command block:

```bash
# Recommended production export for MT4
python -m API.export_entry_path_v1_quantile_signals \
  --production \
  --output MT/tester/files/ml_signals.csv \
  --copy-to-mt4
```

In `MODULE_INDEX.md`, update the exporter row description to:

```markdown
| [export_entry_path_v1_quantile_signals.py](API/export_entry_path_v1_quantile_signals.py) | Production/export path for frozen `entry_path_v1_quantile` winner and MT4 parity | production manifest or seed report dir + frozen rule → `ml_signals.csv` | [docs](docs/MT/ml_signal_integration.md) | ✅ |
```

- [ ] **Step 2: Run a focused diff check on the docs**

Run:

```bash
git diff --check -- docs/MT/ml_signal_integration.md API/README.md MODULE_INDEX.md
```

Expected:
- no whitespace or formatting errors

- [ ] **Step 3: Commit the doc promotion**

```bash
git add docs/MT/ml_signal_integration.md API/README.md MODULE_INDEX.md
git commit -m "docs: promote quantile export as production path"
```

---

### Task 4: Verify The Production Flow End-To-End

**Files:**
- Verify: `API/export_entry_path_v1_quantile_signals.py`
- Verify: `ML/reports/entry_path_v1_quantile_production_manifest.json`
- Verify: `MT/tester/files/ml_signals.csv`
- Verify: `MT/MQL4/Files/ml_signals.csv`

- [ ] **Step 1: Run the full test suite for the exporter**

Run:

```bash
./.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py -q
```

Expected:
- PASS

- [ ] **Step 2: Run the production export command**

Run:

```bash
./.venv/bin/python -m API.export_entry_path_v1_quantile_signals \
  --production \
  --output MT/tester/files/ml_signals.csv \
  --copy-to-mt4
```

Expected:
- stdout prints `MT/tester/files/ml_signals.csv`

- [ ] **Step 3: Verify that both MT4 targets received identical content**

Run:

```bash
cmp MT/tester/files/ml_signals.csv MT/MQL4/Files/ml_signals.csv
```

Expected:
- no output, exit code `0`

- [ ] **Step 4: Verify the canonical row and signal counts**

Run:

```bash
./.venv/bin/python - <<'PY'
import pandas as pd
df = pd.read_csv('MT/tester/files/ml_signals.csv', sep=';')
print('rows', len(df))
print('active', int((df['signal'] != 0).sum()))
print('buy', int((df['signal'] == 1).sum()))
print('sell', int((df['signal'] == -1).sum()))
PY
```

Expected:

```text
rows 8872
active 8
buy 4
sell 4
```

- [ ] **Step 5: Commit any remaining production-path changes**

```bash
git add API/export_entry_path_v1_quantile_signals.py tests/test_export_entry_path_v1_quantile_signals.py ML/reports/entry_path_v1_quantile_production_manifest.json docs/MT/ml_signal_integration.md API/README.md MODULE_INDEX.md MT/tester/files/ml_signals.csv MT/MQL4/Files/ml_signals.csv
git commit -m "feat: productize quantile mt4 export path"
```

---

## Self-Review

- Spec coverage:
  - production manifest: covered in Task 1
  - `--production` mode: covered in Task 2
  - baseline preserved as backup/legacy via docs only: covered in Task 3
  - reproducible export verification: covered in Task 4
- Placeholder scan:
  - no `TODO` / `TBD`
  - each code-changing step includes concrete snippets
- Type consistency:
  - `load_production_manifest`, `resolve_export_request`, `validate_manifest_against_rule`, and `export_signals(... production=...)` are named consistently across tasks
