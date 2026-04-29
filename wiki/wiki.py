"""
wiki/wiki.py — LLM Wiki index generator and verifier for SoSimple.

Subcommands:
    generate   Build/refresh wiki/REPO_integrity.md
    verify     Check index integrity against current filesystem
    status     Show wiki coverage gaps and staleness
    search     Search wiki pages (grep-based)
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple


# ─── Config ──────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = Path(__file__).parent
INDEX_FILE = WIKI_DIR / "REPO_integrity.md"

# Directories to skip entirely (relative to REPO_ROOT, use "/" as separator)
IGNORE_DIRS = {
    ".git",
    ".venv", "venv",
    "__pycache__", ".mypy_cache", ".pytest_cache",
    "DATA",              # raw CSV data (not in git, large)
    "ML/checkpoints",    # model weights (.pt)
    "ML/plots",          # generated plots
    "docs/archive",      # archived docs (per AGENTS.md rules)
    "node_modules",      # catches top-level node_modules
    ".github",           # CI config, not relevant to agents
    ".worktrees",        # git worktrees — copies of repo, not source
    ".codex",            # Codex runtime worktrees — copies of repo, not source
    ".claude",
    ".kilo",
    ".knowledge-rag-data",
    ".pytest_cache",
    ".vscode",           # editor config
}

# Directory names that should be skipped wherever they appear in the tree
IGNORE_DIR_NAMES = {"node_modules", "__pycache__", ".mypy_cache", ".pytest_cache"}

# File extensions to include
TRACK_EXTENSIONS = {".py", ".md", ".mqh", ".mq4", ".ipynb"}

# Also include small .json files (configs, experiment results — not data dumps)
JSON_MAX_SIZE = 200 * 1024  # 200 KB

# Skip hashing files larger than this; record "large" instead
MAX_HASH_SIZE = 2 * 1024 * 1024  # 2 MB

# Files to exclude from tracking
IGNORE_FILENAMES = {
    "REPO_integrity.md",  # avoid self-reference
}


# ─── Data type ───────────────────────────────────────────────────────────────

class FileEntry(NamedTuple):
    path: str        # relative to REPO_ROOT, forward slashes
    description: str
    status: str      # emoji status from MODULE_INDEX, or ""
    mtime: float
    size: int
    hash: str        # 8-char hex (blake2b/4-byte digest), or "large"
    category: str


# ─── Utilities ───────────────────────────────────────────────────────────────

def git_short_hash() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def file_hash(path: Path) -> str:
    if path.stat().st_size > MAX_HASH_SIZE:
        return "--------"  # 8 chars, marks files too large to hash
    h = hashlib.blake2b(digest_size=4)
    h.update(path.read_bytes())
    return h.hexdigest()


def fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n}B"
    if n < 1024 ** 2:
        return f"{n // 1024}KB"
    return f"{n // (1024 ** 2)}MB"


def fmt_mtime(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


# ─── MODULE_INDEX parser ─────────────────────────────────────────────────────

def parse_module_index() -> dict[str, tuple[str, str]]:
    """
    Parse MODULE_INDEX.md and return {relative_path: (description, status)}.
    Handles table rows of the form:
        | [name](path) | description | ... | status_emoji |
    """
    index_path = REPO_ROOT / "MODULE_INDEX.md"
    if not index_path.exists():
        return {}

    result: dict[str, tuple[str, str]] = {}
    # Matches: | [anything](path) | first description column |
    row_re = re.compile(r"^\|\s*\[.*?\]\(([^)]+)\)\s*\|\s*([^|]+?)\s*\|")
    status_emojis = ["✅", "🚧", "🏁", "📦", "⚠️"]

    for line in index_path.read_text(encoding="utf-8").splitlines():
        m = row_re.match(line)
        if not m:
            continue
        path = m.group(1).strip()
        desc = m.group(2).strip()
        status = next((e for e in status_emojis if e in line), "")
        result[path] = (desc, status)

    return result


# ─── Categorization ──────────────────────────────────────────────────────────

def categorize(rel: Path) -> str:
    parts = rel.parts
    if not parts:
        return "Other"
    top = parts[0]

    if top == "wiki":
        return "Wiki"
    if top in (".claude", ".codex", ".kilocode"):
        return "Agent Config"
    if top == "tests":
        return "Tests"
    if top == "MT":
        return "MQL"
    if top == "docs":
        if len(parts) > 1 and parts[1] == "reports":
            return "Reports"
        return "Documentation"
    if top == "ML":
        return "ML"
    if top == "processing":
        return "Processing"
    if top == "API":
        return "API"
    if top == "statistics":
        return "Statistics"
    if rel.suffix == ".md" and len(parts) == 1:
        return "Root Docs"
    return "Other"


CATEGORY_ORDER = [
    "Root Docs",
    "Documentation",
    "Reports",
    "ML",
    "Processing",
    "API",
    "Statistics",
    "Tests",
    "MQL",
    "Wiki",
    "Agent Config",
    "Other",
]


# ─── File scanner ────────────────────────────────────────────────────────────

def _should_skip(rel: Path) -> bool:
    """Return True if the file is inside an ignored directory."""
    parts = rel.parts

    # Check prefix-based ignores (exact path prefixes)
    for ignore in IGNORE_DIRS:
        ignore_parts = tuple(ignore.split("/"))
        n = len(ignore_parts)
        if parts[:n] == ignore_parts:
            return True

    # Check name-based ignores (skip if any ancestor dir has this name)
    for part in parts[:-1]:  # exclude the filename itself
        if part in IGNORE_DIR_NAMES:
            return True

    return False


def scan_repo(descriptions: dict[str, tuple[str, str]]) -> list[FileEntry]:
    entries: list[FileEntry] = []

    for abs_path in sorted(REPO_ROOT.rglob("*")):
        if not abs_path.is_file():
            continue

        rel = abs_path.relative_to(REPO_ROOT)
        if _should_skip(rel):
            continue
        if rel.name in IGNORE_FILENAMES:
            continue

        ext = rel.suffix.lower()
        if ext not in TRACK_EXTENSIONS:
            if ext == ".json":
                if abs_path.stat().st_size > JSON_MAX_SIZE:
                    continue
            else:
                continue

        rel_str = "/".join(rel.parts)  # always forward slashes
        stat = abs_path.stat()
        desc, status = descriptions.get(rel_str, ("", ""))

        entries.append(FileEntry(
            path=rel_str,
            description=desc,
            status=status,
            mtime=stat.st_mtime,
            size=stat.st_size,
            hash=file_hash(abs_path),
            category=categorize(rel),
        ))

    return entries


# ─── Index generator ─────────────────────────────────────────────────────────

def _table_rows(entries: list[FileEntry], with_status: bool) -> list[str]:
    if with_status:
        header = "| Path | Description | Status | Modified | Size | Hash |"
        sep    = "|------|-------------|--------|----------|------|------|"
        rows = [
            f"| [{e.path}]({e.path}) | {e.description} | {e.status} "
            f"| {fmt_mtime(e.mtime)} | {fmt_size(e.size)} | `{e.hash}` |"
            for e in entries
        ]
    else:
        header = "| Path | Description | Modified | Size | Hash |"
        sep    = "|------|-------------|----------|------|------|"
        rows = [
            f"| [{e.path}]({e.path}) | {e.description} "
            f"| {fmt_mtime(e.mtime)} | {fmt_size(e.size)} | `{e.hash}` |"
            for e in entries
        ]
    return [header, sep] + rows


WITH_STATUS_CATS = {"ML", "Processing", "API", "Statistics", "Tests", "MQL"}


def generate_index(entries: list[FileEntry]) -> str:
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    commit = git_short_hash()

    lines: list[str] = [
        "# REPO Integrity Map — SoSimple",
        f"> Auto-generated {now} · git `{commit}`",
        f"> Refresh: `python wiki/wiki.py generate`  ·  Verify: `python wiki/wiki.py verify`",
        "",
        "## Agent Access Protocol",
        "",
        "1. Read this file first to get a project map (what exists, where, integrity hash).",
        "2. Run `python wiki/wiki.py verify` to detect files changed since last index.",
        "3. Navigate via paths in the tables; use `wiki/research/` and `wiki/concepts/` for synthesized knowledge.",
        "4. After modifying significant files, run `generate` and commit `REPO_integrity.md`.",
        "",
        f"**Tracked**: {len(entries)} files  ·  **Commit**: `{commit}`  ·  **Generated**: {now}",
        "",
    ]

    by_cat: dict[str, list[FileEntry]] = {}
    for e in entries:
        by_cat.setdefault(e.category, []).append(e)

    for cat in CATEGORY_ORDER:
        if cat not in by_cat:
            continue
        cat_entries = sorted(by_cat[cat], key=lambda e: e.path)
        lines.append(f"## {cat}")
        lines.append("")
        lines.extend(_table_rows(cat_entries, with_status=(cat in WITH_STATUS_CATS)))
        lines.append("")

    return "\n".join(lines) + "\n"


# ─── Verifier ────────────────────────────────────────────────────────────────

def parse_index_hashes() -> dict[str, str]:
    """Parse REPO_integrity.md and return {path: hash} for all tracked entries."""
    if not INDEX_FILE.exists():
        return {}

    result: dict[str, str] = {}
    # Matches table rows: | [text](path) | ... | `8hexchars` | or `--------`
    row_re = re.compile(r"\| \[.*?\]\(([^)]+)\) \|.*`([0-9a-f]{8}|-{8})`")

    for line in INDEX_FILE.read_text(encoding="utf-8").splitlines():
        m = row_re.search(line)
        if m:
            result[m.group(1)] = m.group(2)

    return result


def cmd_verify() -> int:
    indexed = parse_index_hashes()
    if not indexed:
        print("REPO_integrity.md not found or empty. Run: python wiki/wiki.py generate")
        return 1

    descriptions = parse_module_index()
    current = {e.path: e for e in scan_repo(descriptions)}

    changed, added, removed = [], [], []

    for path, old_hash in indexed.items():
        if path not in current:
            removed.append(path)
        elif old_hash != "--------" and current[path].hash != old_hash:
            changed.append(path)

    for path in current:
        if path not in indexed:
            added.append(path)

    if not changed and not added and not removed:
        print("OK — index is up to date.")
        return 0

    if changed:
        print(f"\nChanged ({len(changed)}):")
        for p in sorted(changed):
            print(f"  ~ {p}")
    if added:
        print(f"\nNew (not yet indexed) ({len(added)}):")
        for p in sorted(added):
            print(f"  + {p}")
    if removed:
        print(f"\nRemoved (in index, absent on disk) ({len(removed)}):")
        for p in sorted(removed):
            print(f"  - {p}")

    total = len(changed) + len(added) + len(removed)
    print(f"\n{total} discrepancies. Run: python wiki/wiki.py generate")
    return 1


# ─── Status command ─────────────────────────────────────────────────────────

def cmd_status() -> int:
    """Show wiki coverage gaps and staleness indicators."""
    # 1. Find all reports
    reports_dir = REPO_ROOT / "docs" / "reports"
    all_reports: set[str] = set()
    if reports_dir.exists():
        for f in reports_dir.glob("*.md"):
            if f.name == "README.md":
                continue
            all_reports.add(f"docs/reports/{f.name}")

    # 2. Scan wiki pages for referenced paths
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


# ─── Search command ─────────────────────────────────────────────────────────

def cmd_search(query: str) -> int:
    """Search wiki pages for a query string (case-insensitive grep)."""
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    results: list[tuple[str, int, str]] = []

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


# ─── Generate command ────────────────────────────────────────────────────────

def cmd_generate() -> int:
    descriptions = parse_module_index()
    entries = scan_repo(descriptions)
    content = generate_index(entries)
    INDEX_FILE.write_text(content, encoding="utf-8")
    rel = INDEX_FILE.relative_to(REPO_ROOT)
    print(f"Generated {rel} — {len(entries)} files tracked.")
    return 0


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="LLM Wiki index generator and verifier for SoSimple.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python wiki/wiki.py generate   # build/refresh REPO_integrity.md\n"
            "  python wiki/wiki.py verify     # check integrity against filesystem\n"
            "  python wiki/wiki.py status     # show wiki coverage gaps\n"
            "  python wiki/wiki.py search Q   # search wiki pages for Q"
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("generate", help="Build/refresh wiki/REPO_integrity.md")
    sub.add_parser("verify", help="Check index integrity against current filesystem")
    sub.add_parser("status", help="Show wiki coverage gaps and staleness")
    search_p = sub.add_parser("search", help="Search wiki pages (grep-based)")
    search_p.add_argument("query", help="Search query")

    args = parser.parse_args()
    if args.cmd == "generate":
        sys.exit(cmd_generate())
    elif args.cmd == "verify":
        sys.exit(cmd_verify())
    elif args.cmd == "status":
        sys.exit(cmd_status())
    elif args.cmd == "search":
        sys.exit(cmd_search(args.query))


if __name__ == "__main__":
    main()
