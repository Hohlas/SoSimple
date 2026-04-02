# Layered Context & Stage Reporting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a layered context workflow for SoSimple by adding `docs/reports/`, formalizing when stage reports are required, tightening the roles of `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `.claude/memory/`, and adding a manual `stage-reporting` skill.

**Architecture:** Roll out the process in four layers. First, create the new report home and migrate the freshest completed stage into it so the workflow has a real example. Second, update project policy in `AGENTS.md` and align `CHANGELOG.md` with report-first closure. Third, shrink `CONTEXT_HANDOFF.md` into a stable baton-pass document and refresh stale memory files so they only hold durable knowledge. Fourth, add a reusable local skill for future manual stage closing. Verification is documentation-focused: file existence, structure checks, and targeted grep review rather than automated tests.

**Tech Stack:** Markdown, repo policy files, local Codex skills

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `docs/reports/README.md` | Create | Explain what belongs in `docs/reports/`, naming rules, and report template |
| `docs/reports/2026-04-01-signal-research-variant-2.md` | Create | First canonical stage report using the just-completed Variant 2 research |
| `CHANGELOG.md` | Modify | Point the latest Variant 2 changelog entry to the new canonical report path |
| `AGENTS.md` | Modify | Formalize report criteria, sync rules, commit policy, and add `docs/reports/` to project structure |
| `CONTEXT_HANDOFF.md` | Modify | Convert from long narrative into short stable handoff format |
| `.claude/memory/MEMORY.md` | Modify | Keep only current memory index entries and update descriptions to match new roles |
| `.claude/memory/project_ml_status.md` | Modify | Refresh stale project status to current Phase B / Variant 2 reality and durable guidance |
| `.claude/memory/feedback_ml_approach.md` | Modify | Update commit rule to controlled stage-close policy while preserving “no push without request” |
| `.codex/skills/stage-reporting/SKILL.md` | Create | Manual workflow for stage closure: report + changelog + handoff + optional commit |

### Notes

- `docs/DATA_FLOW.md` is intentionally **not** part of the initial write set unless rollout work reveals an actual pipeline description mismatch. This process changes context management, not the data pipeline itself.
- No product code changes are expected.
- No commit step is included because current repo policy still requires an explicit user request for `git commit`.

---

### Task 1: Create `docs/reports/` and dogfood the workflow with the latest completed stage

**Files:**
- Create: `docs/reports/README.md`
- Create: `docs/reports/2026-04-01-signal-research-variant-2.md`
- Read: `docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md`
- Read: `docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md`
- Read: `CHANGELOG.md`

- [ ] **Step 1: Draft the `docs/reports/README.md` contract**

Write `docs/reports/README.md` with a short policy and one reusable template:

````md
# Reports

Подробные отчёты по завершённым этапам проекта со значимыми изменениями.

## Когда писать report
- Изменилось поведение кода, влияющее на результаты, сигналы, торговую логику, CLI или формат данных
- Добавлен или заметно расширен инструмент/исследовательский сценарий
- Получены новые результаты с практическими выводами
- Исправлен баг, меняющий интерпретацию результатов
- Завершён отдельный этап плана/spec, после которого работу удобно передавать дальше

## Именование
- `YYYY-MM-DD-topic.md`
- Использовать ISO-дату

## Минимальная структура
1. Заголовок этапа
2. Дата
3. Статус
4. Цель этапа
5. Контекст
6. Что было сделано
7. Какие файлы изменены
8. Как проверяли
9. Результаты
10. Выводы
11. Ограничения / что не решено
12. Что делать дальше
13. Связанные материалы

## Template

```md
# Stage Title

> **Дата**: YYYY-MM-DD
> **Статус**: Completed
> **Цель**: ...
> **Связанный plan/spec**: ...
> **Связанный commit**: pending
```
````

- [ ] **Step 2: Write the first canonical report for Variant 2**

Create `docs/reports/2026-04-01-signal-research-variant-2.md` by adapting the existing findings into the new standard. Keep the facts already established and keep the structure below:

```md
# Signal Research Variant 2

> **Дата**: 2026-04-01
> **Статус**: Completed
> **Цель**: Завершить торгово-ориентированное исследование ML-сигналов по OHLC до перехода к Variant 3
> **Связанный plan/spec**:
> - `docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md`
> - `docs/superpowers/plans/2026-04-01-signal-research-variant-2.md`
> **Связанный commit**: pending

## Контекст
- Production branch already used the 10-target `regression_updn` model, but PF improvement was blocked by weak monetization of the signal.
- Variant 2 was started to study real OHLC path behavior before modifying EA entry logic.
- The research was run on the OOS period `2022-07-18` — `2026-03-20`.

## Что было сделано
- расширен `API/signal_research.py` до Variant 2
- добавлены path-dependent барьерные таблицы
- добавлены pullback/amplitude/regime секции
- исправлен баг `ratio_bin -> ALL`

## Какие файлы изменены
- `API/signal_research.py`
- `tests/test_signal_research.py`
- `CHANGELOG.md`

## Как проверяли
- `python -m pytest tests/test_signal_research.py -q`
- `python -m API.signal_research --test-only`

## Результаты
- OOS: `2603` сигналов
- ранний adverse move: `adv_1=5.6`, `adv_3=8.8`, `adv_6=12.2`
- лучший base setup: `12H / SL=5 / TP=50 / PF=1.05`
- лучший ratio bucket: `4-5`, убыточный bucket: `3-4`
- `BUY PF_12=1.35`, `SELL PF_12=0.95`
- `ATR Q4 PF_12=1.23`

## Выводы
- Сигнал даёт слабый положительный drift, а не сильный мгновенный импульс.
- Ранний adverse move типичен, поэтому timing входа важнее, чем дополнительная подгонка direction filter.
- Бакет `ratio_12=3-4` нужно считать опасной зоной, а `4-5` — приоритетной подгруппой для следующего исследования.

## Ограничения / что не решено
- Variant 2 не сравнивает готовые алгоритмы входа `market` vs `limit` vs `delayed`.
- Полученные выводы ещё не доказывают, что limit entry лучше market entry.
- SELL слабее BUY на текущем OOS, но это может быть следствием бычьего режима, а не структурной проблемы модели.

## Что делать дальше
- Variant 3: compare `market`, `pullback`, `delayed`, `cancel-window`

## Связанные материалы
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md`
```

- [ ] **Step 3: Verify both report files exist and are readable**

Run:

```bash
cd /home/hohla/git/SoSimple && ls docs/reports && sed -n '1,80p' docs/reports/README.md && sed -n '1,120p' docs/reports/2026-04-01-signal-research-variant-2.md
```

Expected:
- `README.md` is present
- `2026-04-01-signal-research-variant-2.md` is present
- the report header contains date, status, goal, linked plan/spec, and `Связанный commit`

---

### Task 2: Update project policy in `AGENTS.md` and align the latest changelog entry

**Files:**
- Modify: `AGENTS.md`
- Modify: `CHANGELOG.md`
- Read: `docs/superpowers/specs/2026-04-02-layered-context-stage-reporting-design.md`

- [ ] **Step 1: Update `AGENTS.md` rules for reports, handoff, memory, and commit policy**

Apply these policy changes in `AGENTS.md`:

```md
### Обязательные правила
- Не делать `git push` без явной просьбы пользователя.
- `git commit` разрешён при закрытии значимого этапа, если пользователь явно попросил commit или явно запросил workflow закрытия этапа.

### Документация и CHANGELOG
- При завершении значимого этапа сначала создавать подробный `docs/reports/YYYY-MM-DD-topic.md`, затем обновлять `CHANGELOG.md`.
- `CONTEXT_HANDOFF.md` обновлять, если изменились current stage, next step, read-first файлы или риски.
- `.claude/memory/` обновлять только для долгоживущих знаний и правил.
- Подробный `report` обязателен, если выполнено хотя бы одно:
  - изменено поведение кода, влияющее на результаты/сигналы/торговую логику/CLI/формат данных;
  - добавлен или заметно расширен инструмент/исследовательский сценарий;
  - получены новые результаты с практическими выводами;
  - исправлен баг, меняющий интерпретацию результатов;
  - завершён отдельный этап плана/spec, после которого работу удобно передавать дальше.
- Если нужно обновить `CHANGELOG.md`, почти наверняка нужен и `report`.
- Если изменился `next step` в `CONTEXT_HANDOFF.md`, почти наверняка нужен и `report`.
```

Also update the project tree snippet so `docs/reports/` appears under `docs/`.

- [ ] **Step 2: Repoint the latest Variant 2 changelog entry to the canonical report**

Replace the current “Подробные исследовательские выводы” link in the top `2026-04-01` Variant 2 entry so it points to:

```md
Подробный отчёт: [docs/reports/2026-04-01-signal-research-variant-2.md](docs/reports/2026-04-01-signal-research-variant-2.md)
```

If the old ad hoc findings file is still worth keeping, leave it referenced from the report itself instead of from `CHANGELOG.md`.

- [ ] **Step 3: Verify the policy text and changelog link**

Run:

```bash
cd /home/hohla/git/SoSimple && rg -n "docs/reports|Подробный отчёт|git commit|CONTEXT_HANDOFF|.claude/memory" AGENTS.md CHANGELOG.md
```

Expected:
- `AGENTS.md` mentions `docs/reports/`
- `AGENTS.md` contains the controlled commit rule
- `CHANGELOG.md` top entry points to `docs/reports/2026-04-01-signal-research-variant-2.md`

---

### Task 3: Rewrite `CONTEXT_HANDOFF.md` into stable baton-pass format and refresh stale memory files

**Files:**
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `.claude/memory/MEMORY.md`
- Modify: `.claude/memory/project_ml_status.md`
- Modify: `.claude/memory/feedback_ml_approach.md`
- Read: `docs/reports/2026-04-01-signal-research-variant-2.md`

- [ ] **Step 1: Rewrite `CONTEXT_HANDOFF.md` into the new short format**

Replace the long narrative with a concise current-state document:

```md
# Context Handoff

## Current Stage
- Phase B research continues after completion of Signal Research Variant 2

## Last Completed Stage
- Signal Research Variant 2 completed on 2026-04-01

## Next Step
- Design and run Variant 3 entry-scenario research: `market`, `pullback`, `delayed`, `cancel-window`

## Read First
- `AGENTS.md`
- `docs/reports/2026-04-01-signal-research-variant-2.md`
- `docs/superpowers/specs/2026-03-27-pf-improvement-design.md`
- `docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md`
- `API/signal_research.py`

## Open Risks
- Variant 2 confirms pullback is common, but does not yet prove limit entry is superior
- SELL weakness may be regime-specific, not model-wide
- `ratio_12=3-4` remains a dangerous bucket

## Latest Report
- `docs/reports/2026-04-01-signal-research-variant-2.md`
```

- [ ] **Step 2: Refresh `.claude/memory/MEMORY.md` and `project_ml_status.md`**

Update the memory layer so it reflects durable knowledge only:

```md
# Memory Index

| File | Type | Description |
|------|------|-------------|
| [user_profile.md](user_profile.md) | user | Профиль пользователя и устойчивые предпочтения |
| [project_ml_status.md](project_ml_status.md) | project | Долгоживущий статус ML-подхода, production модели и текущего исследовательского направления |
| [feedback_ml_approach.md](feedback_ml_approach.md) | feedback | Ограничения и правила по ML/процессу |
```

Refresh `project_ml_status.md` so it no longer points to stale triple-barrier retrain as the active next step. Keep only durable facts such as:

```md
### Production модель
- `regression_updn`, 10 таргетов, Transformer checkpoint in production

### Актуальное исследовательское направление
- current focus is PF improvement via signal monetization, entry logic, filtering, and SL/TP research

### Устойчивые выводы
- ratio bucket `3-4` is weak
- short-horizon directional filters are not useful in simple ratio-threshold form
- path-dependent OHLC analysis is required before EA logic changes
```

- [ ] **Step 3: Update `feedback_ml_approach.md` to the new commit policy**

Replace the old git rule with:

```md
**Не делать git push без явной просьбы.**
**Why:** Пользователь контролирует публикацию изменений.
**How to apply:** Любой `git push` запрещён без отдельного запроса.

**git commit делать только по явной просьбе пользователя или в явно запрошенном workflow закрытия этапа.**
**Why:** Пользователь хочет контролировать историю, но допускает stage-closing commits.
**How to apply:** Если пользователь просит `закрыть этап` или `сделать commit`, можно включать commit в closure workflow.
```

- [ ] **Step 4: Verify handoff and memory roles**

Run:

```bash
cd /home/hohla/git/SoSimple && sed -n '1,120p' CONTEXT_HANDOFF.md && sed -n '1,120p' .claude/memory/MEMORY.md && sed -n '1,220p' .claude/memory/project_ml_status.md && sed -n '1,120p' .claude/memory/feedback_ml_approach.md
```

Expected:
- `CONTEXT_HANDOFF.md` is short and sectioned
- `project_ml_status.md` no longer sends agents to obsolete triple-barrier retrain as the default next step
- memory files now contain durable guidance rather than current handoff

---

### Task 4: Add the manual `stage-reporting` skill

**Files:**
- Create: `.codex/skills/stage-reporting/SKILL.md`
- Read: `.codex/skills/update-docs-on-code-change/SKILL.md`
- Read: `AGENTS.md`

- [ ] **Step 1: Write the `stage-reporting` skill metadata and trigger description**

Create `.codex/skills/stage-reporting/SKILL.md` with frontmatter like:

```md
---
name: stage-reporting
description: Run explicitly when user requests: stage report, закрой этап, подготовь отчет этапа, обнови changelog и handoff, close stage
---
```

- [ ] **Step 2: Add the stage-closing workflow instructions**

The skill body should include:

```md
# Stage Reporting

## Когда использовать
- Пользователь явно просит закрыть этап
- Пользователь просит подготовить отчёт этапа
- Пользователь просит синхронизировать `report`, `CHANGELOG`, `CONTEXT_HANDOFF`

## Что считать значимым этапом
- изменено поведение кода, влияющее на результаты/сигналы/торговую логику/CLI/формат данных
- получены новые экспериментальные результаты с выводами
- исправлен баг, меняющий интерпретацию результатов
- завершён отдельный этап плана/spec

## Workflow
1. Определи тему и дату stage report
2. Создай или обнови `docs/reports/YYYY-MM-DD-topic.md`
3. Обнови `CHANGELOG.md` короткой записью со ссылкой на report
4. Проверь, нужен ли update `CONTEXT_HANDOFF.md`
5. Обнови `.claude/memory/` только если появился долгоживущий вывод
6. Если пользователь явно просит commit, свяжи report с commit hash после коммита

## Правила
- `report` = полный итог
- `CHANGELOG` = короткая история
- `handoff` = текущее состояние
- `memory` = долгоживущие знания
- Не делать `git push` без явной просьбы пользователя
```

- [ ] **Step 3: Verify the skill is discoverable and readable**

Run:

```bash
cd /home/hohla/git/SoSimple && sed -n '1,220p' .codex/skills/stage-reporting/SKILL.md
```

Expected:
- frontmatter contains `name: stage-reporting`
- trigger phrases include both Russian and English forms
- workflow explicitly covers `report -> changelog -> handoff -> optional memory -> optional commit`

---

### Task 5: Final rollout verification

**Files:**
- Verify: `docs/reports/README.md`
- Verify: `docs/reports/2026-04-01-signal-research-variant-2.md`
- Verify: `AGENTS.md`
- Verify: `CHANGELOG.md`
- Verify: `CONTEXT_HANDOFF.md`
- Verify: `.claude/memory/MEMORY.md`
- Verify: `.claude/memory/project_ml_status.md`
- Verify: `.claude/memory/feedback_ml_approach.md`
- Verify: `.codex/skills/stage-reporting/SKILL.md`

- [ ] **Step 1: Run a targeted grep audit for the new workflow**

Run:

```bash
cd /home/hohla/git/SoSimple && rg -n "docs/reports|stage-reporting|Current Stage|Latest Report|Подробный отчёт|git push|закрыть этап" AGENTS.md CHANGELOG.md CONTEXT_HANDOFF.md .claude/memory .codex/skills docs/reports
```

Expected:
- every new workflow concept appears in the right file
- the report path appears in both `docs/reports/` and `CHANGELOG.md`
- `stage-reporting` appears only in the skill file and where intentionally referenced

- [ ] **Step 2: Review git diff for accidental spillover**

Run:

```bash
cd /home/hohla/git/SoSimple && git diff -- AGENTS.md CHANGELOG.md CONTEXT_HANDOFF.md .claude/memory docs/reports .codex/skills/stage-reporting
```

Expected:
- only process/documentation/context files changed
- no product code files were touched

- [ ] **Step 3: Summarize residual risks**

Record the following in the final implementation handoff if still true:

```md
- Existing ad hoc files like `docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md` remain as historical supporting material and are not automatically migrated.
- `docs/DATA_FLOW.md` was intentionally left unchanged unless rollout exposed a real pipeline mismatch.
- Future stage reports should prefer `docs/reports/` even when there is also a spec/findings file elsewhere.
```

---

## Self-Review

- Spec coverage: the plan covers all accepted rollout pieces from the approved spec: `docs/reports/`, `AGENTS.md`, `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `.claude/memory/`, controlled commit policy, and the manual `stage-reporting` skill.
- Placeholder scan: no `TODO`/`TBD` actions remain; each task points to exact files and verification commands.
- Type consistency: the chosen skill name is consistently `stage-reporting`; the canonical report path is consistently `docs/reports/2026-04-01-signal-research-variant-2.md`.
