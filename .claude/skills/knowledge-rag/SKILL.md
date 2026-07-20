---
name: knowledge-rag
description: Use when a task needs project memory: prior decisions, reports, wiki pages, plans, research conclusions, or cross-document context; use before broad manual search over docs/wiki/reports.
---

# knowledge-rag

Use `knowledge-rag` as project search, not as a source of truth.

## Workflow

1. Start with `search_knowledge` for semantic project navigation, prior conclusions, cross-document context, and substantive document review.
2. For overview tasks, run 2-4 narrow searches instead of one broad query.
3. Open the original files returned by search before drawing conclusions.
4. If results are empty or noisy, change terms or `hybrid_alpha`.
5. Treat search snippets as pointers only; final claims must come from original files.

## Query mode

Use `hybrid_alpha` by query type:
- `0.0`: exact names, filenames, metrics, functions.
- `0.3`: stable project terms mixed with exact words.
- `0.5`: mixed code/docs questions.
- `1.0`: ideas, hypotheses, conclusions, semantic similarity.

Use `max_results` 5 by default; raise it only when comparing several candidate documents.

## Relationship with other navigation

Use Graphify for relationships and paths between concepts.
Use `knowledge-rag` for finding relevant source documents.
Use `rg` for exact strings, symbols, and follow-up checks after RAG identifies likely sources.
