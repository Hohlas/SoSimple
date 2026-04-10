# LLM Wiki Improvements Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Привести реализацию LLM Wiki в полное соответствие с оригинальным методом: Query→Save loop, автоматизация status, поиск (grep + qmd/MCP), frontmatter, переименование WIKI_index, связь docs-скилла с wiki.

**Architecture:** 7 независимых улучшений. Порядок: сначала переименование (п.5, т.к. затрагивает многие файлы), потом wiki.py (п.2, п.3), потом SKILL.md правки (п.1, п.4, п.6), потом frontmatter (п.7), потом qmd/MCP (п.3b).

**Tech Stack:** Python 3, npm/npx, qmd (@tobilu/qmd), MCP protocol, markdown.

---

## File Map

| Action | File | Что меняется |
|--------|------|-------------|
| Rename | `wiki/WIKI_index.md` → `wiki/REPO_integrity.md` | Переименование файла |
| Modify | `wiki/wiki.py` | Rename refs, +status, +search commands |
| Modify | `.codex/skills/wiki/SKILL.md` | Query→Save, удалить правило "мин 2 отчёта", rename refs, связь с docs |
| Modify | `.codex/skills/update-docs-on-code-change/SKILL.md` | +шаг проверки wiki-концептов |
| Modify | `wiki/index.md` | Rename ref |
| Modify | `wiki/log.md` | Rename ref (historical note) |
| Modify | `AGENTS.md` | Rename ref в структуре проекта |
| Modify | `wiki/research/signal-quality-research.md` | +frontmatter |
| Modify | `wiki/research/execution-tracks.md` | +frontmatter |
| Modify | `wiki/concepts/signal-archetypes.md` | +frontmatter |
| Create | `.kilocode/mcp.json` | +qmd MCP server config |

---

### Task 1: Переименование WIKI_index.md → REPO_integrity.md

**Files:**
- Rename: `wiki/WIKI_index.md` → `wiki/REPO_integrity.md`
- Modify: `wiki/wiki.py`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `AGENTS.md`
- Modify: `.codex/skills/wiki/SKILL.md`

- [ ] **Step 1: Переименовать файл**

```bash
cd /home/hohla/git/SoSimple
git mv wiki/WIKI_index.md wiki/REPO_integrity.md
```

- [ ] **Step 2: Обновить wiki/wiki.py — все ссылки на WIKI_index**

Заменить:
- `INDEX_FILE = WIKI_DIR / "WIKI_index.md"` → `INDEX_FILE = WIKI_DIR / "REPO_integrity.md"`
- `"WIKI_index.md"` в `IGNORE_FILENAMES` → `"REPO_integrity.md"`
- Все строки в docstrings/prints/help: `WIKI_index.md` → `REPO_integrity.md`
- Заголовок сгенерированного файла: `# WIKI Index` → `# REPO Integrity Map`

- [ ] **Step 3: Обновить wiki/index.md**

Строка 3: `[WIKI_index.md](WIKI_index.md)` → `[REPO_integrity.md](REPO_integrity.md)`

- [ ] **Step 4: Обновить AGENTS.md**

Строка 96: `├── WIKI_index.md    #   авто-генерированная integrity map репо` → `├── REPO_integrity.md #   авто-генерированная integrity map репо`

- [ ] **Step 5: Обновить .codex/skills/wiki/SKILL.md**

- description в frontmatter: `regenerate WIKI_index.md` → `regenerate REPO_integrity.md`
- Строка 16: `wiki/WIKI_index.md` → `wiki/REPO_integrity.md`
- Строка 34: `├── WIKI_index.md` → `├── REPO_integrity.md`
- Строка 94: `wiki/WIKI_index.md` → `wiki/REPO_integrity.md`

- [ ] **Step 6: Регенерировать integrity map**

```bash
python wiki/wiki.py generate
```

Ожидаемый вывод: `Generated wiki/REPO_integrity.md — NNN files tracked.`

---

### Task 2: wiki.py — команда `status`

**Files:**
- Modify: `wiki/wiki.py`

- [ ] **Step 1: Добавить функцию `cmd_status`**

Логика:
1. Собрать список файлов из `docs/reports/*.md`.
2. Прочитать все wiki-страницы из `wiki/research/` и `wiki/concepts/`, извлечь ссылки на `docs/reports/` и пути к файлам проекта.
3. Сравнить хеши REPO_integrity.md с текущим состоянием (reuse `parse_index_hashes` + `scan_repo`).
4. Вывести три секции:
   - **Uncovered reports**: файлы из `docs/reports/` не упомянутые ни в одной wiki-странице.
   - **Changed since last index**: файлы с изменёнными хешами (из verify logic).
   - **Broken wiki links**: пути, упомянутые в wiki-страницах, но отсутствующие на диске.

```python
def cmd_status() -> int:
    """Show wiki coverage gaps and staleness indicators."""
    # 1. Find all reports
    reports_dir = REPO_ROOT / "docs" / "reports"
    all_reports = set()
    if reports_dir.exists():
        for f in reports_dir.glob("*.md"):
            all_reports.add(f"docs/reports/{f.name}")

    # 2. Scan wiki pages for referenced report paths and file paths
    referenced_reports: set[str] = set()
    wiki_file_refs: set[str] = set()
    link_re = re.compile(r'\[.*?\]\(([^)]+)\)')

    for subdir in ("research", "concepts"):
        wiki_subdir = WIKI_DIR / subdir
        if not wiki_subdir.exists():
            continue
        for page in wiki_subdir.glob("*.md"):
            content = page.read_text(encoding="utf-8")
            for m in link_re.finditer(content):
                target = m.group(1)
                # Resolve relative paths from wiki page location
                resolved = (page.parent / target).resolve()
                try:
                    rel = resolved.relative_to(REPO_ROOT)
                    rel_str = "/".join(rel.parts)
                    wiki_file_refs.add(rel_str)
                    if rel_str.startswith("docs/reports/"):
                        referenced_reports.add(rel_str)
                except ValueError:
                    pass

    # 3. Uncovered reports
    uncovered = sorted(all_reports - referenced_reports)

    # 4. Changed files (reuse verify logic)
    indexed = parse_index_hashes()
    descriptions = parse_module_index()
    current = {e.path: e for e in scan_repo(descriptions)}

    changed = []
    for path, old_hash in indexed.items():
        if path in current and old_hash != "--------" and current[path].hash != old_hash:
            changed.append(path)

    # 5. Broken wiki links
    broken = sorted(ref for ref in wiki_file_refs
                    if not (REPO_ROOT / Path(ref)).exists())

    # Output
    if not uncovered and not changed and not broken:
        print("Wiki is up to date. No gaps found.")
        return 0

    if uncovered:
        print(f"\nUncovered reports ({len(uncovered)}):")
        for r in uncovered:
            print(f"  ? {r}")

    if changed:
        print(f"\nChanged since last index ({len(changed)}):")
        for p in sorted(changed):
            print(f"  ~ {p}")

    if broken:
        print(f"\nBroken wiki links ({len(broken)}):")
        for b in broken:
            print(f"  ! {b}")

    total = len(uncovered) + len(changed) + len(broken)
    print(f"\n{total} items need attention.")
    return 1
```

- [ ] **Step 2: Зарегистрировать команду в CLI**

В функции `main()` добавить:
```python
sub.add_parser("status", help="Show wiki coverage gaps and staleness")
```

И в if/elif блок:
```python
elif args.cmd == "status":
    sys.exit(cmd_status())
```

- [ ] **Step 3: Проверить работу**

```bash
python wiki/wiki.py status
```

---

### Task 3a: wiki.py — команда `search`

**Files:**
- Modify: `wiki/wiki.py`

- [ ] **Step 1: Добавить функцию `cmd_search`**

Grep-based поиск по wiki-страницам (fallback когда qmd недоступен).

```python
def cmd_search(query: str) -> int:
    """Search wiki pages for a query string (case-insensitive grep)."""
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    results: list[tuple[str, int, str]] = []  # (file, line_no, line)

    for subdir in ("research", "concepts"):
        wiki_subdir = WIKI_DIR / subdir
        if not wiki_subdir.exists():
            continue
        for page in sorted(wiki_subdir.glob("*.md")):
            for i, line in enumerate(
                page.read_text(encoding="utf-8").splitlines(), 1
            ):
                if pattern.search(line):
                    rel = page.relative_to(WIKI_DIR)
                    results.append((str(rel), i, line.strip()))

    # Also search index.md and log.md
    for name in ("index.md", "log.md"):
        fp = WIKI_DIR / name
        if fp.exists():
            for i, line in enumerate(
                fp.read_text(encoding="utf-8").splitlines(), 1
            ):
                if pattern.search(line):
                    results.append((name, i, line.strip()))

    if not results:
        print(f"No matches for '{query}' in wiki/")
        return 1

    print(f"Found {len(results)} matches for '{query}':\n")
    for filepath, lineno, line in results:
        print(f"  {filepath}:{lineno}  {line[:120]}")
    return 0
```

- [ ] **Step 2: Зарегистрировать команду в CLI**

```python
search_p = sub.add_parser("search", help="Search wiki pages (grep-based)")
search_p.add_argument("query", help="Search query")
```

И в if/elif:
```python
elif args.cmd == "search":
    sys.exit(cmd_search(args.query))
```

- [ ] **Step 3: Проверить работу**

```bash
python wiki/wiki.py search "архетип"
python wiki/wiki.py search "pullback"
```

---

### Task 3b: Установка qmd и настройка MCP

**Files:**
- Modify: `.kilocode/mcp.json`

- [ ] **Step 1: Установить qmd глобально**

```bash
npm install -g @tobilu/qmd
```

- [ ] **Step 2: Создать qmd collection для wiki**

```bash
qmd collection add /home/hohla/git/SoSimple/wiki --name sosimple-wiki --mask "**/*.md"
```

- [ ] **Step 3: Создать qmd collection для всего проекта (docs + reports)**

```bash
qmd collection add /home/hohla/git/SoSimple/docs --name sosimple-docs --mask "**/*.md"
```

- [ ] **Step 4: Сгенерировать embeddings**

```bash
qmd embed
```

- [ ] **Step 5: Проверить поиск**

```bash
qmd search "signal archetypes"
qmd vsearch "как работает pullback entry"
```

- [ ] **Step 6: Добавить qmd в MCP конфигурацию**

В `.kilocode/mcp.json` добавить запись `qmd`:

```json
{
  "mcpServers": {
    "qmd": {
      "command": "qmd",
      "args": ["mcp"],
      "disabled": false,
      "alwaysAllow": []
    },
    "exa": { "..." },
    "context7": { "..." }
  }
}
```

- [ ] **Step 7: Проверить MCP**

Перезапустить IDE / agent session. Убедиться что qmd tools доступны.

---

### Task 4: Удалить правило "минимум 2 отчёта"

**Files:**
- Modify: `.codex/skills/wiki/SKILL.md`

- [ ] **Step 1: Удалить строку из секции "Правила"**

Удалить:
```
- Не создавать страницу по одному отчёту — минимум 2 связанных отчёта для `research/`, устойчивый инсайт для `concepts/`.
```

Заменить на:
```
- Для `research/`: создавать страницу когда отчёт приносит новое знание. Одиночный отчёт по новому направлению — валидный повод для страницы.
- Для `concepts/`: создавать когда концепт устойчив и подтверждён данными.
```

- [ ] **Step 2: Обновить шаг 3 в Ingest**

Текущий текст:
```
   - **Создать новую**, если отчёт открывает новое направление (≥2 отчётов по теме).
```

Заменить на:
```
   - **Создать новую**, если отчёт открывает новое направление.
```

---

### Task 5: Query → Save loop

**Files:**
- Modify: `.codex/skills/wiki/SKILL.md`

- [ ] **Step 1: Добавить шаг 4 в секцию Query**

После текущего шага 3 добавить:

```markdown
4. Если ответ содержит новый синтез (сравнение, анализ, выявленная связь) — предложи сохранить результат как wiki-страницу через операцию **Save**. Explorations должны компаундиться в wiki, а не теряться в истории чата.
```

---

### Task 6: Связь update-docs-on-code-change с wiki

**Files:**
- Modify: `.codex/skills/update-docs-on-code-change/SKILL.md`

- [ ] **Step 1: Добавить секцию wiki-check**

После секции "Common mistakes" добавить:

```markdown
## Wiki cross-check

После обновления документации проверь, не затронуты ли wiki-концепты:

1. Прочитай `wiki/index.md` — найди wiki-страницы, связанные с изменёнными модулями.
2. Если изменение меняет поведение, интерфейс или выводы, отмеченные в wiki-странице — обнови wiki-страницу или добавь пометку о необходимости ревизии.
3. Запусти `python wiki/wiki.py status` — убедись, что нет broken links.
```

---

### Task 7: Frontmatter для wiki-страниц

**Files:**
- Modify: `wiki/research/signal-quality-research.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify: `wiki/concepts/signal-archetypes.md`
- Modify: `.codex/skills/wiki/SKILL.md`

- [ ] **Step 1: Определить формат frontmatter**

Research pages:
```yaml
---
last_updated: YYYY-MM-DD
sources: N
status: active | completed | stale
---
```

Concept pages:
```yaml
---
last_updated: YYYY-MM-DD
status: confirmed | preliminary | disputed
---
```

- [ ] **Step 2: Добавить frontmatter к signal-quality-research.md**

```yaml
---
last_updated: 2026-04-09
sources: 7
status: completed
---
```

- [ ] **Step 3: Добавить frontmatter к execution-tracks.md**

```yaml
---
last_updated: 2026-04-09
sources: 7
status: active
---
```

- [ ] **Step 4: Добавить frontmatter к signal-archetypes.md**

```yaml
---
last_updated: 2026-04-09
status: confirmed
---
```

- [ ] **Step 5: Обновить шаблоны в SKILL.md**

В шаблон Research добавить frontmatter:
```markdown
---
last_updated: YYYY-MM-DD
sources: N
status: active | completed | stale
---
# Название линии исследования
...
```

В шаблон Concepts:
```markdown
---
last_updated: YYYY-MM-DD
status: confirmed | preliminary | disputed
---
# Название концепта
...
```

---

## Порядок выполнения

1. **Task 1** — переименование (фундамент, затрагивает много файлов)
2. **Task 2** — status command
3. **Task 3a** — search command
4. **Task 4** — удаление правила
5. **Task 5** — Query→Save
6. **Task 6** — docs↔wiki связь
7. **Task 7** — frontmatter
8. **Task 3b** — qmd/MCP (последним, т.к. требует npm install)

## Verification

После всех задач:
```bash
python wiki/wiki.py generate
python wiki/wiki.py verify
python wiki/wiki.py status
python wiki/wiki.py search "архетип"
```
