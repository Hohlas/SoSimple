Hi @lyonzin,

Thanks again for maintaining `knowledge-rag`. This is a separate follow-up PR from real-world usage of exact/path-oriented searches in larger mixed documentation/code repositories.

## Summary

Adds a small generic ranking signal for indexed `source` and `filename` metadata. When query terms match the file path or file name, hybrid search gives that candidate a bounded boost before final sorting/reranking. This helps navigational queries surface the most relevant file-oriented chunks without adding project-specific rules or changing the public API.

Closes N/A

## Type of change

- [x] feat - new feature
- [ ] fix - bug fix
- [ ] docs - documentation only
- [ ] refactor - no behavior change
- [ ] perf - performance improvement
- [x] test - adding or improving tests
- [ ] chore - tooling, deps, CI
- [ ] BREAKING CHANGE (explain in Migration section below)

## What changed

- `mcp_server/server.py`: add `_metadata_path_score()` to compute a small bounded boost from query matches in `source` and `filename` metadata.
- `mcp_server/server.py`: add that boost to the fused RRF score before sorting/reranking.
- `tests/test_search.py`: add a deterministic test showing that a filename/path match can lift the more navigationally relevant result.
- `README.md`: add a `### Unreleased` changelog entry.

## Why

For large repositories, users often search by stable file-oriented terms: module names, report names, feature names, or words that appear in paths. BM25 and semantic search only score chunk content, so two chunks with similar content can rank counterintuitively when one of them is clearly a better path/filename match.

This PR keeps the behavior generic. It does not add hardcoded categories, project-specific terms, config assumptions, or new dependencies. The boost is intentionally small and capped so content relevance remains the primary signal.

---

## 7 Pillars Quality Gate

> Mark each item. CI enforces these via the `quality-gate.yml` workflow.

### 1. Security

- [x] No new secrets, tokens, or credentials in the diff (gitleaks will block)
- [x] No new use of `eval`, `exec`, `subprocess shell=True`, `pickle.loads` on untrusted input, or arbitrary deserialization
- [x] New dependencies (if any) reviewed for known CVEs and license compatibility
- [x] Path traversal, command injection, and SSRF surfaces explicitly considered for any new I/O code

### 2. Stability

- [ ] All existing tests still pass on Linux + Windows x Python 3.11/3.12
- [x] New behavior covered by tests; tests are deterministic (no `time.sleep` / network / OS-scheduler dependencies)
- [ ] Coverage does not regress (codecov gate)
- [x] No tests were skipped, deleted, or marked `xfail` to make the PR pass

### 3. Memory leak

- [x] Long-lived objects (orchestrator, watcher, cache) are bounded
- [x] New caches have eviction policy (LRU, TTL, or explicit size limit)
- [x] No new global state that grows unbounded with usage
- [x] If you added a new module that loads heavy resources, consider lazy initialization

### 4. Versatility

- [x] Works on Linux, Windows, macOS (paths, line endings, locale considered)
- [x] Works on Python 3.11, 3.12, 3.13 (no Python-version-specific syntax without fallback)
- [x] No hardcoded paths, locales, or encodings
- [x] If you touched a parser, all 20 supported formats still parse correctly

### 5. Scalability

- [x] No O(n^2) or worse algorithms on user-controlled inputs
- [ ] Benchmark impact considered (run `pytest bench/` locally if you touched search/index/embed)
- [x] If perf regression > 10% in any metric, justification provided below
- [x] Concurrency safety: no new shared mutable state without lock or documented thread confinement

**Performance impact** (required if you touched `mcp_server/server.py`, `mcp_server/ingestion.py`, or `bench/`):

```text
metric          before    after    delta
search p95      N/A       N/A      N/A
index docs/sec  N/A       N/A      N/A
RSS @ 1k docs   N/A       N/A      N/A
```

This adds a small per-candidate metadata scoring calculation during result fusion. It does not add indexing work, model calls, database writes, network I/O, or persistent state. I did not run the benchmark suite locally.

### 6. Versioning

- [ ] If this is user-facing change: bumped version in `pyproject.toml`, `mcp_server/__init__.py`, and `npm/package.json` atomically
- [ ] If this is a breaking change: bumped MAJOR, added migration notes in CHANGELOG, marked `BREAKING CHANGE:` in commit footer
- [x] CHANGELOG updated with entry under `## Unreleased` in README.md
- [x] Public API surface (`mcp_server/server.py` MCP tool decorators) unchanged, OR breaking changes documented

### 7. Quality

- [ ] `ruff check` passes
- [ ] `ruff format --check` passes
- [x] Type hints on new public functions (`mypy --strict` clean for new files)
- [x] Docstrings on new public functions (used by `interrogate`)
- [x] Cyclomatic complexity reasonable (`radon cc --max=C`)
- [x] No dead code (`vulture` would not flag new code)
- [x] PR is reasonably sized (< 500 lines of diff preferred; bigger PRs split or justify)

---

## Migration / Breaking changes

N/A. This is not a breaking change. Existing `search_knowledge` parameters and response schema are unchanged.

## Test plan

- [ ] `pytest tests/ -v` passed locally
- [ ] `pre-commit run --all-files` clean
- [x] Manual smoke test: N/A for external system behavior; the change is covered by a deterministic unit test with fake BM25/collection/cache objects.
- [x] Ran targeted test locally: `.venv/bin/python -m pytest tests/test_search.py -q` -> `23 passed`.
- [x] Ran changelog check locally: `python3 scripts/check_changelog.py --pr-title 'feat: improve search ranking with path metadata' --base-ref origin/master` -> `OK`.

## Documentation

- [x] Updated `README.md` (if user-facing)
- [ ] Updated `docs/` (if applicable)
- [x] Added entry to `## Unreleased` in README CHANGELOG section

## Reviewer checklist

<!-- Do not edit. The reviewer fills this. -->

- [ ] Reviewed line-by-line
- [ ] Verified the 7 pillars CI status checks are green
- [ ] Verified no obvious adversarial implications
- [ ] Approved performance impact

---

By submitting this PR I confirm I read [CONTRIBUTING.md](../CONTRIBUTING.md) and agree to the [Code of Conduct](../CODE_OF_CONDUCT.md).
