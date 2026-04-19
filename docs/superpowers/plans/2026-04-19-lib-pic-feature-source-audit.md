# lib_PIC Feature Source Audit Plan

> **For agentic workers:** REQUIRED: Use `.codex/skills/using-superpowers/SKILL.md` before starting, then use the most specific available superpowers skill for execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Разобрать `lib_PIC.mqh` как источник признаков для ML: понять, какие рыночные состояния он уже считает, что из этого экспортируется в `Nero.csv`, что реально использует Python-модель, и где теряется потенциально полезная информация.

**Architecture:** Это read-only исследовательский этап. Код торговой логики и генерации фракталов не меняется. Результатом должен быть отчёт и точное задание на следующий этап: расширять экспорт из MT4, строить признаки в Python, или менять сам алгоритм `lib_PIC`.

**Tech Stack:** MQL4 (`MT/MQL4/Include/lib_PIC.mqh`, `head_PIC.mqh`), Python data pipeline (`processing/`, `ML/data_loader.py`, `ML/entry_path_feature_bank.py`), документация `docs/DATA_FLOW.md`, `docs/MT/lib_PIC.mqh.md`.

---

## File Structure

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/DATA_FLOW.md`
- `docs/MT/lib_PIC.mqh.md`
- `MT/MQL4/README.md`
- `MT/MQL4/Include/head_PIC.mqh`
- `MT/MQL4/Include/lib_PIC.mqh`
- `processing/label_signals.py`
- `ML/data_loader.py`
- `ML/entry_path_feature_bank.py`

### Files To Create

- `docs/reports/2026-04-19-lib-pic-feature-source-audit.md`

### Files To Modify

- `docs/MT/lib_PIC.mqh.md`
- `docs/DATA_FLOW.md`
- `docs/superpowers/roadmap.md`

### Files To Update At Stage Close

- `docs/reports/2026-04-19-lib-pic-feature-source-audit.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/feature-source-and-lib-pic.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

---

## Acceptance Rules

- Не менять `lib_PIC.mqh` в этом этапе.
- Не менять формат `Nero.csv` в этом этапе.
- Не запускать новое обучение.
- Не открывать большие CSV целиком; для проверки формата использовать только первые строки.
- Документировать только проверенные соответствия: поле в MQL4 -> поле в CSV -> поле в Python.
- Все гипотезы о пользе новых признаков явно помечать как гипотезы до проверки моделью или benchmark.

---

## Task 1: Build the Current Field Map

**Files:**
- Read: `MT/MQL4/Include/head_PIC.mqh`
- Read: `MT/MQL4/Include/lib_PIC.mqh`
- Read: `docs/DATA_FLOW.md`
- Read: `ML/data_loader.py`

- [ ] **Step 1: Map `PICS` fields**

List every important field in `PICS`: price, time, direction, front/back values, strength, break state, trend state, flat/false-break state, touch counts, impulse, ATR, Up/Dn horizons.

- [ ] **Step 2: Map `NERO_CSV_CREATE()` output**

Create a table:

```text
CSV index | CSV name | MQL4 source | Meaning | Used by Python? | Notes
```

- [ ] **Step 3: Map Python features**

For each exported field, record whether it becomes:

- model input;
- target;
- normalization helper;
- ignored field.

- [ ] **Step 4: Record documentation drift**

Record every found mismatch between docs and code, especially field count, horizon count, encoding, and stale comments.

---

## Task 2: Identify Lost Information

**Files:**
- Read: `MT/MQL4/Include/head_PIC.mqh`
- Read: `MT/MQL4/Include/lib_PIC.mqh`
- Read: `ML/data_loader.py`
- Read: `ML/entry_path_feature_bank.py`

- [ ] **Step 1: List computed-but-not-exported fields**

Focus on fields that may describe trade context, not future outcome:

- trend state around the level;
- nearest level distances;
- flat and false-break state;
- touch/bar interaction fields;
- break timing and return timing;
- impulse detail fields;
- target-level fields.

- [ ] **Step 2: Classify leakage risk**

For each candidate field, classify:

- safe input feature;
- unsafe because it can include future information;
- unclear, needs code-path proof.

- [ ] **Step 3: Classify implementation cost**

For each safe candidate, classify:

- Python-only derived feature;
- requires extending `Nero.csv`;
- requires changing `lib_PIC` logic.

---

## Task 3: Design Feature Diagnostics

**Files:**
- Read: `DATA/Nero_train_labeled.csv` only through safe CSV sampling tools.
- Read: `ML/data_loader.py`
- Read: existing benchmark scripts in `ML/`.

- [ ] **Step 1: Define current-feature importance test**

Use at least two approaches:

- permutation importance: shuffle one feature group and measure metric degradation;
- tree-based importance on a cheap model trained on flattened/summarized features.

Optional later method:

- SHAP (feature contribution method) only after a stable small diagnostic model exists.

- [ ] **Step 2: Define feature groups**

Group features by meaning instead of by raw column:

- price/time/position;
- direction and level side;
- front/back geometry;
- strength and count;
- break/reversal/impulse;
- Up/Dn long horizons;
- ATR ratio;
- multi-window summaries.

- [ ] **Step 3: Define decision rules**

Feature expansion is justified only if diagnostics show one of:

- current important groups are too coarse and need detail;
- ignored fields carry independent signal;
- generated summaries improve validation benchmark without worsening concentration/stability.

---

## Task 4: Produce the Audit Report

**Files:**
- Create: `docs/reports/2026-04-19-lib-pic-feature-source-audit.md`

- [ ] **Step 1: Write verified facts**

Include:

- current 22-field fractal format;
- current 20-feature model input;
- fields used as targets, not inputs;
- exact known documentation drift.

- [ ] **Step 2: Write candidate feature backlog**

Split into:

- safe to test in Python first;
- requires `Nero.csv` export extension;
- risky changes to `lib_PIC` internals.

- [ ] **Step 3: Write next-stage recommendation**

Recommend one concrete next stage:

- feature-importance diagnostics on current exported fields; or
- export-extension prototype; or
- new training track with revised inputs.

---

## Task 5: Roadmap Update

**Files:**
- Modify: `docs/superpowers/roadmap.md`

- [ ] **Step 1: Remove completed obsolete items**

Remove roadmap entries that are already completed or superseded by reports.

- [ ] **Step 2: Add current forward path**

Add concise items:

- `lib_PIC` feature-source audit;
- current-feature importance diagnostics;
- feature export/design decision;
- new training track with revised inputs;
- cross-instrument robustness check;
- system correlation/portfolio check.

- [ ] **Step 3: Keep roadmap task-oriented**

Each item must contain:

- context;
- exact task;
- expected output.
