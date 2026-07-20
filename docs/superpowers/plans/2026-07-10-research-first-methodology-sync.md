# Research-First Methodology Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Лаконично синхронизировать существующую ML-методику с research-first подходом из `docs/superpowers/specs/2026-07-10-research-first-methodology-redesign.md`.

**Architecture:** Не добавлять новый большой слой правил. Точечно уточнить уже существующие разделы: поисковый уровень, verdict-статусы, post-mortem, freeze-протокол и reporting. Разделить `verdict`, `lifecycle_status` и `probe_type`, чтобы исследовательские зацепки не путались с `candidate`.

**Tech Stack:** Markdown-документация, project wiki script `./.venv/bin/python wiki/wiki.py`, git.

## Global Constraints

- Не переписывать методику с нуля: implementation должен быть "синхронизация и уточнение", а не "добавить всё заново".
- Не использовать `hypothesis_candidate`; использовать `research_hypothesis`.
- Не делать `cross_instrument_probe` статусом; это `probe_type`.
- `candidate` остаётся только строгим статусом проверочного контура.
- `locked_test` остаётся запрещённым для поиска и выбора.
- Не добавлять единые числовые пороги для всех задач; добавить обязательный шаблон порогов, который заполняется в каждом плане.
- PnL/PF в исследовательском режиме должны иметь рядом `allowed_max_verdict`, причину "не торговый вывод", непройденные проверки и запрещённые слова вывода.
- Документационная правка без продуктового изменения не требует `CHANGELOG.md`.
- После значимых docs/wiki изменений обновить `wiki/REPO_integrity.md`.

---

## Files

- Modify: `docs/methodology/README.md`
  - Роль: точка входа; коротко объясняет два контура методики.
- Modify: `docs/methodology/00-research-management.md`
  - Роль: основной раздел управления исследованием; уже содержит поисковый и проверочный уровни.
- Modify: `docs/methodology/A4-verdicts-stop-conditions.md`
  - Роль: словарь verdict/lifecycle и stop conditions.
- Modify: `docs/methodology/A5-post-mortem-diagnostics.md`
  - Роль: разбор провалов и создание следующих исследовательских гипотез.
- Modify: `docs/methodology/09-validation-freeze.md`
  - Роль: поздний переход к проверочному контуру и заморозке правила.
- Modify: `docs/methodology/16-reporting-audit.md`
  - Роль: обязательные поля отчёта и ограничения интерпретации.
- Modify: `wiki/REPO_integrity.md`
  - Роль: авто-сгенерированная карта репозитория после docs изменений.

---

### Task 1: README + Research Management Sync

**Files:**
- Modify: `docs/methodology/README.md`
- Modify: `docs/methodology/00-research-management.md`

**Interfaces:**
- Consumes: `docs/superpowers/specs/2026-07-10-research-first-methodology-redesign.md`
- Produces: основной словарь research-first контура для следующих задач.

- [ ] **Step 1: Read exact current sections**

Run:

```bash
sed -n '1,120p' docs/methodology/README.md
sed -n '1,120p' docs/methodology/00-research-management.md
```

Expected: увидеть текущий главный принцип в `README.md` и раздел "Уровни исследования" в `00-research-management.md`.

- [ ] **Step 2: Update README with a short two-contour note**

Edit `docs/methodology/README.md` near the opening description. Keep the existing strict quality principle, but add this short clarification:

```markdown
> Research-first уточнение: методика работает в двух контурах. Сначала
> исследовательский контур ищет и ранжирует гипотезы (`research_scan`,
> `exploratory_result`, `research_hypothesis`, `research_only`). Затем
> проверочный контур замораживает одно правило перед `locked_test` и
> `candidate`. Поиск может быть широким, но `locked_test`, PnL/PF и
> trading-выводы остаются только для позднего проверочного контура.
```

Do not remove the existing live-safe principle.

- [ ] **Step 3: Rewrite only the "Уровни исследования" table and nearby explanation**

In `docs/methodology/00-research-management.md`, keep the existing section name. Replace the current two-row table with a compact version that adds lifecycle/probe separation:

```markdown
| Уровень | Цель | Статусы | Максимальный verdict |
|---|---|---|---|
| Поисковый | Найти, описать и ранжировать гипотезы | `research_scan`, `exploratory_result`, `research_hypothesis`, `research_only` | `research_only` |
| Проверочный | Проверить одно заранее замороженное правило | `frozen_rule_for_locked_test`, `candidate`, `production_candidate`, `confirmed` | `confirmed` |
```

Add this paragraph after the table:

```markdown
`verdict` отвечает за итоговую оценку качества, `lifecycle_status` — за место
результата в исследовательском цикле, `probe_type` — за вид следующей проверки
(`cross_instrument_probe`, `walk_forward_probe`, `new_period_probe`,
`cost_stress_probe`). `cross_instrument_probe` не является статусом.
```

- [ ] **Step 4: Add compact research_hypothesis requirements**

In the same section, add a short block after the existing search-budget paragraph:

```markdown
`research_hypothesis` не означает `candidate`. Это зацепка, которая заслуживает
следующей проверки. Перед probe план обязан указать:

- `origin_bias`: где идея была подсмотрена (`horizon`, `seed`, `year`, `side`,
  `instrument`, `threshold`, `post_mortem`);
- `research_priority`: `low`, `medium` или `high` и краткую причину;
- `next_probe_freeze`: инструменты, периоды, горизонт, признаки, target, модель,
  правило, пороги, costs/spread, метрики и `allowed_max_verdict`;
- `continuation_budget`: сколько новых probe-партий разрешено до пересмотра
  ветки.

Если эти поля не заданы до запуска probe, максимальный статус результата —
`exploratory_result`.
```

- [ ] **Step 5: Add minimum-threshold template without global numeric values**

Add the following immediately after Step 4's block:

````markdown
Числовые минимумы задаются в плане конкретной проверки, а не глобально для всех
задач:

```text
min_objects_after_filter:
min_trades_total:
min_trades_per_year:
min_years_or_windows:
min_seeds:
min_buy_sell_coverage:
required_baselines:
required_lower_bound_metric:
```
````

- [ ] **Step 6: Verify Task 1 text is not bloated**

Run:

```bash
rg -n "hypothesis_candidate|cross_instrument_probe.*статус|research_hypothesis|origin_bias|continuation_budget" docs/methodology/README.md docs/methodology/00-research-management.md
```

Expected:
- no `hypothesis_candidate`;
- no statement that `cross_instrument_probe` is a status;
- `research_hypothesis`, `origin_bias`, `continuation_budget` present in `00-research-management.md`.

---

### Task 2: Verdict and Lifecycle Status Sync

**Files:**
- Modify: `docs/methodology/A4-verdicts-stop-conditions.md`

**Interfaces:**
- Consumes: terms added in Task 1.
- Produces: canonical distinction between `verdict`, `lifecycle_status`, and `probe_type`.

- [ ] **Step 1: Read current status tables**

Run:

```bash
sed -n '1,120p' docs/methodology/A4-verdicts-stop-conditions.md
```

Expected: увидеть existing verdict table, lifecycle statuses, relation to research levels.

- [ ] **Step 2: Update lifecycle table only**

In the `Lifecycle-статусы` table:

- keep `exploratory_result`;
- add `research_scan`;
- add `research_hypothesis`;
- keep `frozen_rule_for_locked_test`;
- do not add `cross_instrument_probe` as lifecycle status.

Use these exact meanings:

```markdown
| `research_scan` | Идёт поисковая партия: широкий перебор в заранее описанной области |
| `research_hypothesis` | Исследовательская зацепка готова к отдельному probe-плану, но не является `candidate` |
```

- [ ] **Step 3: Add probe_type note**

After the lifecycle table, add:

```markdown
`probe_type` описывает вид следующей проверки, а не статус результата. Примеры:
`cross_instrument_probe`, `walk_forward_probe`, `new_period_probe`,
`cost_stress_probe`.
```

- [ ] **Step 4: Split stop conditions by contour**

Keep existing strict stop conditions for candidate checks. Add a short research branch rule after them:

```markdown
Для исследовательского контура stop condition не обязан закрывать всё
направление. Он закрывает текущую зацепку или текущую probe-партию, если
исчерпан `continuation_budget`, результат не поднялся выше
`exploratory_result`, эффект держится на одном seed/year/side/instrument,
результат хуже dummy-фона или найден leakage/broken contract.
```

- [ ] **Step 5: Verify forbidden naming**

Run:

```bash
rg -n "hypothesis_candidate|cross_instrument_probe.*\\|.*Статус|candidate.*исследовательск" docs/methodology/A4-verdicts-stop-conditions.md
```

Expected:
- no `hypothesis_candidate`;
- no table row where `cross_instrument_probe` appears as status;
- no sentence that makes `candidate` an exploratory status.

---

### Task 3: Post-Mortem and Freeze Protocol Sync

**Files:**
- Modify: `docs/methodology/A5-post-mortem-diagnostics.md`
- Modify: `docs/methodology/09-validation-freeze.md`

**Interfaces:**
- Consumes: `research_hypothesis`, `origin_bias`, `next_probe_freeze`, `continuation_budget`.
- Produces: clear boundary between post-mortem hypothesis creation and strict frozen rule selection.

- [ ] **Step 1: Read target sections**

Run:

```bash
sed -n '1,80p' docs/methodology/A5-post-mortem-diagnostics.md
sed -n '300,370p' docs/methodology/A5-post-mortem-diagnostics.md
sed -n '1,80p' docs/methodology/09-validation-freeze.md
```

Expected: увидеть role statement for post-mortem, existing output/next-step table, and validation freeze goal.

- [ ] **Step 2: Clarify A5 role**

In the opening role paragraph of `A5-post-mortem-diagnostics.md`, keep "Не выбирать нового winner" but add:

```markdown
Post-mortem может создать `research_hypothesis`, если найденная зона проходит
минимальные условия для следующей проверки. Это не повышает verdict и не
создаёт `candidate`; это только задаёт `origin_bias` и `next_probe_freeze`.
```

- [ ] **Step 3: Add compact hypothesis output schema**

In A5 `### Выход`, add this compact item:

```markdown
9. **Research hypotheses:** список зацепок для следующей проверки:
   `name`, `origin_bias`, `research_priority`, `next_probe_freeze`,
   `allowed_max_verdict`, `continuation_budget`.
```

- [ ] **Step 4: Update A5 next-step table**

In the row for "Есть diagnostic zone", replace "Писать отдельный план..." with:

```markdown
Оформить `research_hypothesis` с `origin_bias`, `research_priority`,
`next_probe_freeze` и `continuation_budget`; не использовать post-mortem как
selection и не повышать verdict.
```

- [ ] **Step 5: Clarify 09 freeze scope**

In `docs/methodology/09-validation-freeze.md`, after `### Цель`, add:

```markdown
Этот раздел относится к позднему проверочному контуру. Он не предназначен для
широкого поиска. Если правило пришло из `research_hypothesis`, его
`origin_bias` сохраняется в отчёте; freeze проверяет одно заранее выбранное
правило, а не стирает историю поиска.
```

- [ ] **Step 6: Verify post-mortem cannot create candidate**

Run:

```bash
rg -n "research_hypothesis|origin_bias|next_probe_freeze|continuation_budget|candidate" docs/methodology/A5-post-mortem-diagnostics.md docs/methodology/09-validation-freeze.md
```

Expected:
- A5 says `research_hypothesis` is not `candidate`;
- 09 says freeze is late confirmatory scope;
- no text says post-mortem can raise verdict.

---

### Task 4: Reporting Fields and PnL/PF Guardrails

**Files:**
- Modify: `docs/methodology/16-reporting-audit.md`

**Interfaces:**
- Consumes: all fields introduced in Tasks 1-3.
- Produces: report requirements that keep research PnL/PF from becoming trading claims.

- [ ] **Step 1: Read reporting file**

Run:

```bash
sed -n '1,220p' docs/methodology/16-reporting-audit.md
```

Expected: увидеть current report/audit requirements and existing disclosure rules.

- [ ] **Step 2: Add compact research report fields**

Add a short subsection near report requirements:

````markdown
### Research-first disclosure

Для исследовательских отчётов добавить компактный блок:

```text
lifecycle_status:
origin_bias:
research_priority:
current_search_budget:
cumulative_search_budget:
next_probe_freeze:
allowed_max_verdict:
forbidden_interpretations:
```
````

- [ ] **Step 3: Add PnL/PF local guardrail**

In the same subsection, add:

```markdown
Если исследовательский отчёт показывает PnL/PF, рядом с таблицей PnL/PF
обязательно указать:

- `allowed_max_verdict`;
- почему это не торговый вывод;
- какие проверки ещё не пройдены;
- запрещённые слова вывода: "прибыльно", "готово", "можно запускать",
  "live-ready", "tradable".
```

- [ ] **Step 4: Verify reporting fields**

Run:

```bash
rg -n "Research-first disclosure|origin_bias|research_priority|next_probe_freeze|allowed_max_verdict|forbidden_interpretations|live-ready|tradable" docs/methodology/16-reporting-audit.md
```

Expected: all listed fields present once in the new compact subsection.

---

### Task 5: Consistency Audit, Wiki Integrity, Commit

**Files:**
- Modify: `wiki/REPO_integrity.md`
- No change expected: `CHANGELOG.md`
- No change expected: `CONTEXT_HANDOFF.md`
- No change expected: `MODULE_INDEX.md`

**Interfaces:**
- Consumes: completed Tasks 1-4.
- Produces: verified docs-only change ready for review.

- [ ] **Step 1: Run naming consistency checks**

Run:

```bash
rg -n "hypothesis_candidate|cross_instrument_probe.*статус|cross_instrument_probe.*Status" docs/methodology
```

Expected: no matches, except historical mentions in reports are acceptable only if they are not in `docs/methodology`.

- [ ] **Step 2: Run candidate-boundary check**

Run:

```bash
rg -n "research_hypothesis.*candidate|candidate.*research_hypothesis|post-mortem.*candidate" docs/methodology
```

Expected: matches must say `research_hypothesis` is not `candidate`, or that post-mortem does not create `candidate`.

- [ ] **Step 3: Run Markdown diff check**

Run:

```bash
git diff --check
```

Expected: no output, exit code 0.

- [ ] **Step 4: Update wiki integrity**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected:
- first command regenerates `wiki/REPO_integrity.md`;
- second command reports wiki up to date or no blocking gaps.

- [ ] **Step 5: Review final diff scope**

Run:

```bash
git status --short
git diff --stat
```

Expected changed files:

```text
docs/methodology/README.md
docs/methodology/00-research-management.md
docs/methodology/A4-verdicts-stop-conditions.md
docs/methodology/A5-post-mortem-diagnostics.md
docs/methodology/09-validation-freeze.md
docs/methodology/16-reporting-audit.md
wiki/REPO_integrity.md
```

Expected unchanged:

```text
CHANGELOG.md
CONTEXT_HANDOFF.md
MODULE_INDEX.md
```

- [ ] **Step 6: Commit**

Run:

```bash
git add docs/methodology/README.md \
  docs/methodology/00-research-management.md \
  docs/methodology/A4-verdicts-stop-conditions.md \
  docs/methodology/A5-post-mortem-diagnostics.md \
  docs/methodology/09-validation-freeze.md \
  docs/methodology/16-reporting-audit.md \
  wiki/REPO_integrity.md
git commit -m "Sync methodology with research-first workflow"
```

Expected: one docs-only commit. Do not run Python tests unless Python files changed.
