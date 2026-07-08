---
name: knowledge-rag
description: Use RAG search across project docs, code, wiki, reports, and cross-document context when grep is too narrow or the answer depends on accumulated project knowledge; find candidate sources first, then verify original files.
---

# knowledge-rag

Use `knowledge-rag` as project search, not as a source of truth.

## Workflow

1. Use before broad manual search when the exact source is unknown.
2. Search candidates with `search_knowledge`.
3. For overview tasks, run 2-4 narrow searches instead of one broad query.
4. Open the original files returned by search before drawing conclusions.
5. If results are empty or noisy, change terms or `hybrid_alpha`.
6. Treat search snippets as pointers only; final claims must come from original files.

Do not use when the exact file or symbol is already known; read or grep that source directly.

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
Use `rg` after sources are known or when matching exact code text.
