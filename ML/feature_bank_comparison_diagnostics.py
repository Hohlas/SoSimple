# =============================================================================
# Файл: feature_bank_comparison_diagnostics.py
# Назначение: Bounded comparison full/clean/geometry/path feature-bank variants.
# Обновлён: 2026-04-19
# Входные данные:
#   - DATA/Nero_train_labeled.csv
#   - DATA/Nero_validation_labeled.csv
# Выходные данные:
#   - ML/reports/feature_bank_comparison/summary.csv
#   - ML/reports/feature_bank_comparison/summary.json
#   - ML/reports/feature_bank_comparison/report.md
# Использование:
#   python -m ML.feature_bank_comparison_diagnostics --target trail_24_pnl_atr_x8
# Примечания:
#   - Read-only diagnostic: не запускает обучение нейросети.
# =============================================================================

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from ML.feature_importance_diagnostics import (
    DATA_DIR,
    _directional_accuracy,
    build_grouped_features,
    load_sample,
)
from ML.lib_pic_geometry_feature_bank import GEOMETRY_FEATURE_PREFIX, build_lib_pic_geometry_feature_bank
from ML.lib_pic_path_reaction_feature_bank import PATH_REACTION_FEATURE_PREFIX, build_lib_pic_path_reaction_feature_bank


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / 'ML' / 'reports' / 'feature_bank_comparison'

BASELINE_CLEAN_DROP_GROUPS = ('direction', 'price_position', 'path_long', 'path_short')

VARIANTS = (
    'baseline_full',
    'baseline_clean',
    'baseline_full_path',
    'baseline_clean_path',
    'baseline_clean_geometry_path',
)


@dataclass(frozen=True)
class VariantResult:
    variant: str
    train_rows: int
    validation_rows: int
    feature_count: int
    validation_r2: float
    validation_mae: float
    directional_accuracy: float | None


def _prefixed_columns(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    columns = [column for column in frame.columns if column.startswith(prefix)]
    return frame[columns].replace([np.inf, -np.inf], 0.0).fillna(0.0)


def _validate_variant(variant: str) -> None:
    if variant not in VARIANTS:
        raise ValueError(f'unknown variant: {variant}')


def _clean_baseline_columns(base: pd.DataFrame, groups: dict[str, list[str]]) -> pd.DataFrame:
    drop_columns: set[str] = set()
    for group in BASELINE_CLEAN_DROP_GROUPS:
        drop_columns.update(groups.get(group, []))
    keep_columns = [column for column in base.columns if column not in drop_columns]
    return base[keep_columns].copy()


def build_feature_parts(frame: pd.DataFrame, seq_len: int) -> dict[str, pd.DataFrame]:
    """Строит базовые, geometry и path признаки один раз для всех вариантов."""
    base, groups = build_grouped_features(frame, seq_len=seq_len)
    geometry = build_lib_pic_geometry_feature_bank(frame)
    path = build_lib_pic_path_reaction_feature_bank(frame)
    return {
        'baseline_full': base,
        'baseline_clean': _clean_baseline_columns(base, groups),
        'geometry': _prefixed_columns(geometry, GEOMETRY_FEATURE_PREFIX),
        'path': _prefixed_columns(path, PATH_REACTION_FEATURE_PREFIX),
    }


def assemble_variant_features(parts: dict[str, pd.DataFrame], variant: str) -> pd.DataFrame:
    """Собирает один вариант из заранее построенных feature parts."""
    _validate_variant(variant)
    baseline_key = 'baseline_clean' if variant.startswith('baseline_clean') else 'baseline_full'
    frames = [parts[baseline_key]]
    if variant in ('baseline_full_path', 'baseline_clean_path', 'baseline_clean_geometry_path'):
        frames.append(parts['path'])
    if variant == 'baseline_clean_geometry_path':
        frames.append(parts['geometry'])
    return pd.concat(frames, axis=1).replace([np.inf, -np.inf], 0.0).fillna(0.0)


def build_variant_features(frame: pd.DataFrame, variant: str, seq_len: int) -> pd.DataFrame:
    """Строит признаки для одного comparison-варианта."""
    return assemble_variant_features(build_feature_parts(frame, seq_len=seq_len), variant=variant)


def _fit_score_variant(
    variant: str,
    train_parts: dict[str, pd.DataFrame],
    validation_parts: dict[str, pd.DataFrame],
    train_rows: int,
    validation_rows: int,
    y_train: np.ndarray,
    y_val: np.ndarray,
    n_estimators: int,
    seed: int,
) -> VariantResult:
    x_train = assemble_variant_features(train_parts, variant=variant)
    x_val = assemble_variant_features(validation_parts, variant=variant)
    x_val = x_val.reindex(columns=x_train.columns, fill_value=0.0)

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=8,
        min_samples_leaf=20,
        n_jobs=-1,
        random_state=seed,
    )
    model.fit(x_train, y_train)
    pred = model.predict(x_val)
    return VariantResult(
        variant=variant,
        train_rows=train_rows,
        validation_rows=validation_rows,
        feature_count=len(x_train.columns),
        validation_r2=float(r2_score(y_val, pred)),
        validation_mae=float(mean_absolute_error(y_val, pred)),
        directional_accuracy=_directional_accuracy(y_val, pred),
    )


def run_comparison(
    train_path: Path,
    validation_path: Path,
    target: str,
    output_dir: Path,
    seq_len: int,
    max_train_rows: int,
    max_validation_rows: int,
    chunksize: int,
    n_estimators: int,
    seed: int,
    variants: tuple[str, ...] = VARIANTS,
) -> list[VariantResult]:
    output_dir.mkdir(parents=True, exist_ok=True)
    train = load_sample(train_path, target, seq_len, max_train_rows, chunksize)
    validation = load_sample(validation_path, target, seq_len, max_validation_rows, chunksize)
    train_parts = build_feature_parts(train, seq_len=seq_len)
    validation_parts = build_feature_parts(validation, seq_len=seq_len)
    y_train = pd.to_numeric(train[target], errors='coerce').fillna(0.0).to_numpy(dtype=np.float32)
    y_val = pd.to_numeric(validation[target], errors='coerce').fillna(0.0).to_numpy(dtype=np.float32)

    results = [
        _fit_score_variant(
            variant=variant,
            train_parts=train_parts,
            validation_parts=validation_parts,
            train_rows=len(train),
            validation_rows=len(validation),
            y_train=y_train,
            y_val=y_val,
            n_estimators=n_estimators,
            seed=seed,
        )
        for variant in variants
    ]
    summary = pd.DataFrame([asdict(result) for result in results])
    summary = summary.sort_values(['validation_r2', 'directional_accuracy'], ascending=False).reset_index(drop=True)
    summary.to_csv(output_dir / 'summary.csv', index=False)
    payload = {
        'target': target,
        'seq_len': seq_len,
        'max_train_rows': max_train_rows,
        'max_validation_rows': max_validation_rows,
        'n_estimators': n_estimators,
        'seed': seed,
        'train_path': str(train_path),
        'validation_path': str(validation_path),
        'results': summary.to_dict(orient='records'),
    }
    (output_dir / 'summary.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    write_report(output_dir / 'report.md', payload, summary)
    return results


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return '_empty_'
    text_frame = frame.copy()
    for column in text_frame.columns:
        text_frame[column] = text_frame[column].map(
            lambda value: f'{value:.6f}' if isinstance(value, float) else str(value)
        )
    columns = list(text_frame.columns)
    lines = [
        '| ' + ' | '.join(columns) + ' |',
        '| ' + ' | '.join(['---'] * len(columns)) + ' |',
    ]
    for row in text_frame.itertuples(index=False, name=None):
        lines.append('| ' + ' | '.join(str(value) for value in row) + ' |')
    return '\n'.join(lines)


def write_report(path: Path, payload: dict, summary: pd.DataFrame) -> None:
    lines = [
        '# Feature Bank Comparison Diagnostics',
        '',
        '## Scope',
        '',
        'Read-only comparison of current baseline features against geometry/path feature banks.',
        'No neural-network training and no MT4/lib_PIC changes.',
        '',
        '## Configuration',
        '',
        f'- Target: `{payload["target"]}`',
        f'- seq_len: `{payload["seq_len"]}`',
        f'- Train rows: `{payload["max_train_rows"]}`',
        f'- Validation rows: `{payload["max_validation_rows"]}`',
        f'- RandomForest trees: `{payload["n_estimators"]}`',
        '',
        '## Results',
        '',
        _markdown_table(summary),
        '',
        '## Interpretation',
        '',
        f'- `baseline_clean` removes raw groups: `{", ".join(BASELINE_CLEAN_DROP_GROUPS)}`.',
        '- `baseline_full_path` adds the path-reaction bank to the full baseline.',
        '- `baseline_clean_path` adds the path-reaction bank to the cleaned baseline.',
        '- `baseline_clean_geometry_path` adds both banks to the cleaned baseline.',
        '- This is a feature diagnostic, not a trading verdict.',
    ]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Compare clean/full feature-bank variants on existing labeled CSV.')
    parser.add_argument('--train', type=Path, default=DATA_DIR / 'Nero_train_labeled.csv')
    parser.add_argument('--validation', type=Path, default=DATA_DIR / 'Nero_validation_labeled.csv')
    parser.add_argument('--target', default='trail_24_pnl_atr_x8')
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument('--seq-len', type=int, default=20)
    parser.add_argument('--max-train-rows', type=int, default=12000)
    parser.add_argument('--max-validation-rows', type=int, default=6000)
    parser.add_argument('--chunksize', type=int, default=5000)
    parser.add_argument('--n-estimators', type=int, default=80)
    parser.add_argument('--seed', type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_comparison(
        train_path=args.train,
        validation_path=args.validation,
        target=args.target,
        output_dir=args.output_dir,
        seq_len=args.seq_len,
        max_train_rows=args.max_train_rows,
        max_validation_rows=args.max_validation_rows,
        chunksize=args.chunksize,
        n_estimators=args.n_estimators,
        seed=args.seed,
    )
    print(json.dumps([asdict(result) for result in results], indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
