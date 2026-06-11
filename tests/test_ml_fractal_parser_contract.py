from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ML_DIR = ROOT / "ML"


def _python_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def test_ml_code_does_not_import_label_signals_parse_fractal():
    """ML-код не должен использовать semantic parser из разметки как feature extractor."""
    offenders: list[str] = []

    for path in _python_files(ML_DIR):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        label_signals_aliases: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module not in {"label_signals", "processing.label_signals"}:
                    continue
                imported_names = {alias.name for alias in node.names}
                if "parse_fractal" in imported_names:
                    offenders.append(str(path.relative_to(ROOT)))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in {"label_signals", "processing.label_signals"}:
                        label_signals_aliases.add(alias.asname or alias.name.split(".")[-1])
            elif isinstance(node, ast.Attribute):
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id in label_signals_aliases
                    and node.attr == "parse_fractal"
                ):
                    offenders.append(str(path.relative_to(ROOT)))
                    break

    assert offenders == [], (
        "ML-код должен читать fractal*-поля нормализованных CSV как float-признаки "
        "через ML feature extractor, а не через processing.label_signals.parse_fractal(): "
        + ", ".join(offenders)
    )


def _is_parts_index(node: ast.AST, indexes: set[int]) -> bool:
    if not isinstance(node, ast.Subscript):
        return False
    if not isinstance(node.value, ast.Name) or node.value.id != "parts":
        return False
    index_node = node.slice
    if isinstance(index_node, ast.Constant) and isinstance(index_node.value, int):
        return index_node.value in indexes
    return False


def _casts_parts_index_to_int(node: ast.AST, indexes: set[int]) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Name) or node.func.id != "int":
        return False
    if not node.args:
        return False
    arg = node.args[0]
    if _is_parts_index(arg, indexes):
        return True
    return (
        isinstance(arg, ast.Call)
        and isinstance(arg.func, ast.Name)
        and arg.func.id == "float"
        and bool(arg.args)
        and _is_parts_index(arg.args[0], indexes)
    )


def test_ml_code_does_not_hard_cast_normalized_categorical_fractal_fields():
    """strong/break/count после нормализации являются float-признаками, а не raw int."""
    categorical_indexes = {5, 6, 9}
    offenders: list[str] = []

    for path in _python_files(ML_DIR):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if any(_casts_parts_index_to_int(node, categorical_indexes) for node in ast.walk(tree)):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == [], (
        "ML feature builders не должны превращать нормализованные strong/break/count "
        "обратно в int; такие поля нужно читать как float: "
        + ", ".join(offenders)
    )
