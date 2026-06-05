# =============================================================================
# Файл: feature_importance_diagnostics.py
# Назначение: Диагностика важности групп текущих признаков Nero/fractal CSV.
# Обновлён: 2026-04-19
# Входные данные:
#   - DATA/Nero_train_labeled.csv
#   - DATA/Nero_validation_labeled.csv
# Выходные данные:
#   - ML/reports/current_feature_importance/group_importance.csv
#   - ML/reports/current_feature_importance/feature_importance.csv
#   - ML/reports/current_feature_importance/summary.json
#   - ML/reports/current_feature_importance/report.md
# Использование:
#   python -m ML.feature_importance_diagnostics --target trail_24_pnl_atr_x8
# Примечания:
#   - Read-only diagnostic: не запускает обучение нейросети.
#   - CSV читается чанками; большие файлы целиком в контекст не выводятся.
# =============================================================================

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'DATA'
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / 'ML' / 'reports' / 'current_feature_importance'

CSV_SEP = ';'
FRACTAL_SEP = ':'
N_FRACTALS = 100

FRACTAL_FIELD_INDEX = {
    'time': 0,
    'price': 1,
    'direction': 2,
    'front': 3,
    'back': 4,
    'strong': 5,
    'break': 6,
    'reverse': 7,
    'power': 8,
    'count': 9,
    'impulse': 10,
    'up_12': 11,
    'dn_12': 12,
    'up_24': 13,
    'dn_24': 14,
    'up_48': 15,
    'dn_48': 16,
    'up_3': 17,
    'dn_3': 18,
    'up_6': 19,
    'dn_6': 20,
    'fractal_atr': 21,
    'shift': 22,
}

GROUP_FIELDS = {
    'price_position': ('price',),
    'direction': ('direction',),
    'geometry': ('front', 'back', 'reverse'),
    'strength': ('strong', 'power', 'count'),
    'break_impulse': ('break', 'impulse'),
    'path_long': ('up_12', 'dn_12', 'up_24', 'dn_24', 'up_48', 'dn_48'),
    'path_short': ('up_3', 'dn_3', 'up_6', 'dn_6'),
    'atr': ('fractal_atr',),
}

ROW_FEATURE_GROUP = 'row_context'
WINDOWS = (5, 10, 20, 50, 100)
AGGREGATIONS = ('mean', 'std', 'max', 'last')


@dataclass(frozen=True)
class DiagnosticResult:
    target: str
    train_rows: int
    validation_rows: int
    feature_count: int
    baseline_r2: float
    baseline_mae: float
    directional_accuracy: float | None


def _fractal_columns(seq_len: int) -> list[str]:
    return [f'fractal{i}' for i in range(seq_len)]


def _required_columns(seq_len: int, target: str) -> list[str]:
    columns = ['time', 'ATR', target]
    for optional in ('session_hour', 'weekday'):
        columns.append(optional)
    columns.extend(_fractal_columns(seq_len))
    return columns


def load_sample(path: Path, target: str, seq_len: int, max_rows: int, chunksize: int) -> pd.DataFrame:
    """Читает хвостовую выборку CSV чанками, не загружая лишние колонки."""
    header = pd.read_csv(path, sep=CSV_SEP, nrows=0).columns.tolist()
    usecols = [column for column in _required_columns(seq_len, target) if column in header]
    missing = [column for column in (target, *_fractal_columns(seq_len)) if column not in header]
    if missing:
        raise ValueError(f'{path} missing required columns: {missing[:5]}')

    buffer = pd.DataFrame()
    for chunk in pd.read_csv(path, sep=CSV_SEP, usecols=usecols, chunksize=chunksize, low_memory=False):
        chunk = chunk.dropna(subset=[target])
        if chunk.empty:
            continue
        buffer = pd.concat([buffer, chunk], ignore_index=True)
        if len(buffer) > max_rows:
            buffer = buffer.tail(max_rows).reset_index(drop=True)

    if buffer.empty:
        raise ValueError(f'{path} produced no rows for target={target}')
    return buffer.reset_index(drop=True)


def _split_fractal_series(series: pd.Series) -> pd.DataFrame:
    split = series.fillna('').astype(str).str.split(FRACTAL_SEP, expand=True)
    if split.shape[1] < 22:
        for column in range(split.shape[1], 22):
            split[column] = np.nan
    return split.iloc[:, :22]


def _field_matrix(frame: pd.DataFrame, seq_len: int, field: str) -> np.ndarray:
    idx = FRACTAL_FIELD_INDEX[field]
    columns = []
    for fractal_col in _fractal_columns(seq_len):
        split = _split_fractal_series(frame[fractal_col])
        values = pd.to_numeric(split[idx], errors='coerce').fillna(0.0).to_numpy(dtype=np.float32)
        columns.append(values)
    return np.column_stack(columns)


def _aggregate_matrix(matrix: np.ndarray, window: int, field: str) -> dict[str, np.ndarray]:
    chunk = matrix[:, :window]
    out: dict[str, np.ndarray] = {}
    if 'mean' in AGGREGATIONS:
        out[f'{field}_mean_w{window}'] = np.mean(chunk, axis=1)
    if 'std' in AGGREGATIONS:
        out[f'{field}_std_w{window}'] = np.std(chunk, axis=1)
    if 'max' in AGGREGATIONS:
        out[f'{field}_max_w{window}'] = np.max(chunk, axis=1)
    if 'last' in AGGREGATIONS:
        out[f'{field}_last_w{window}'] = chunk[:, 0]
    return out


def build_grouped_features(frame: pd.DataFrame, seq_len: int = 100) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Строит компактные признаки по смысловым группам текущего fractal CSV."""
    features: dict[str, np.ndarray] = {}
    groups: dict[str, list[str]] = {}

    max_window = min(seq_len, max(WINDOWS))
    windows = tuple(window for window in WINDOWS if window <= max_window)

    field_cache: dict[str, np.ndarray] = {}
    for group, fields in GROUP_FIELDS.items():
        groups[group] = []
        for field in fields:
            matrix = field_cache.setdefault(field, _field_matrix(frame, seq_len, field))
            for window in windows:
                for name, values in _aggregate_matrix(matrix, window, field).items():
                    features[name] = values
                    groups[group].append(name)

    row_features = {}
    if 'ATR' in frame.columns:
        row_features['row_atr'] = pd.to_numeric(frame['ATR'], errors='coerce').fillna(0.0).to_numpy(dtype=np.float32)
    if 'session_hour' in frame.columns:
        hour = pd.to_numeric(frame['session_hour'], errors='coerce').fillna(0.0).to_numpy(dtype=np.float32)
        row_features['row_hour_sin'] = np.sin(2 * np.pi * hour / 24.0)
        row_features['row_hour_cos'] = np.cos(2 * np.pi * hour / 24.0)
    if 'weekday' in frame.columns:
        weekday = pd.to_numeric(frame['weekday'], errors='coerce').fillna(0.0).to_numpy(dtype=np.float32)
        row_features['row_weekday_sin'] = np.sin(2 * np.pi * weekday / 7.0)
        row_features['row_weekday_cos'] = np.cos(2 * np.pi * weekday / 7.0)
    for column in ():
        if column in frame.columns:
            row_features[f'row_{column}'] = pd.to_numeric(frame[column], errors='coerce').fillna(0.0).to_numpy(dtype=np.float32)

    if row_features:
        groups[ROW_FEATURE_GROUP] = []
        for name, values in row_features.items():
            features[name] = values
            groups[ROW_FEATURE_GROUP].append(name)

    feature_frame = pd.DataFrame(features, index=frame.index).replace([np.inf, -np.inf], 0.0).fillna(0.0)
    return feature_frame, groups


def _directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    mask = y_true != 0
    if not np.any(mask):
        return None
    return float(np.mean(np.sign(y_true[mask]) == np.sign(y_pred[mask])))


def _group_feature_importance(model: RandomForestRegressor, feature_names: Iterable[str], groups: dict[str, list[str]]) -> pd.DataFrame:
    raw = pd.Series(model.feature_importances_, index=list(feature_names), dtype=float)
    rows = []
    for group, columns in groups.items():
        present = [column for column in columns if column in raw.index]
        rows.append(
            {
                'group': group,
                'feature_count': len(present),
                'model_importance_sum': float(raw[present].sum()) if present else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values('model_importance_sum', ascending=False).reset_index(drop=True)


def _permutation_group_importance(
    model: RandomForestRegressor,
    x_val: pd.DataFrame,
    y_val: np.ndarray,
    groups: dict[str, list[str]],
    seed: int,
) -> pd.DataFrame:
    baseline_pred = model.predict(x_val)
    baseline_r2 = r2_score(y_val, baseline_pred)
    baseline_mae = mean_absolute_error(y_val, baseline_pred)
    rng = np.random.default_rng(seed)
    rows = []
    for group, columns in groups.items():
        present = [column for column in columns if column in x_val.columns]
        if not present:
            continue
        shuffled = x_val.copy()
        order = rng.permutation(len(shuffled))
        shuffled.loc[:, present] = shuffled.loc[shuffled.index[order], present].to_numpy()
        pred = model.predict(shuffled)
        perm_r2 = r2_score(y_val, pred)
        perm_mae = mean_absolute_error(y_val, pred)
        rows.append(
            {
                'group': group,
                'feature_count': len(present),
                'r2_drop': float(baseline_r2 - perm_r2),
                'mae_increase': float(perm_mae - baseline_mae),
                'permuted_r2': float(perm_r2),
                'permuted_mae': float(perm_mae),
            }
        )
    return pd.DataFrame(rows).sort_values(['r2_drop', 'mae_increase'], ascending=False).reset_index(drop=True)


def run_diagnostics(
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
) -> DiagnosticResult:
    output_dir.mkdir(parents=True, exist_ok=True)

    train = load_sample(train_path, target, seq_len, max_train_rows, chunksize)
    validation = load_sample(validation_path, target, seq_len, max_validation_rows, chunksize)

    x_train, groups = build_grouped_features(train, seq_len=seq_len)
    x_val, _ = build_grouped_features(validation, seq_len=seq_len)
    x_val = x_val.reindex(columns=x_train.columns, fill_value=0.0)

    y_train = pd.to_numeric(train[target], errors='coerce').fillna(0.0).to_numpy(dtype=np.float32)
    y_val = pd.to_numeric(validation[target], errors='coerce').fillna(0.0).to_numpy(dtype=np.float32)

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=8,
        min_samples_leaf=20,
        n_jobs=-1,
        random_state=seed,
    )
    model.fit(x_train, y_train)

    pred = model.predict(x_val)
    baseline_r2 = float(r2_score(y_val, pred))
    baseline_mae = float(mean_absolute_error(y_val, pred))
    dir_acc = _directional_accuracy(y_val, pred)

    group_model = _group_feature_importance(model, x_train.columns, groups)
    group_perm = _permutation_group_importance(model, x_val, y_val, groups, seed=seed + 1)
    group_report = group_perm.merge(group_model, on=['group', 'feature_count'], how='left')
    group_report.to_csv(output_dir / 'group_importance.csv', index=False)

    feature_report = pd.DataFrame(
        {
            'feature': x_val.columns,
            'model_importance': model.feature_importances_,
            'group': [
                next((group for group, columns in groups.items() if column in columns), 'unknown')
                for column in x_val.columns
            ],
        }
    ).sort_values('model_importance', ascending=False)
    feature_report.to_csv(output_dir / 'feature_importance.csv', index=False)

    result = DiagnosticResult(
        target=target,
        train_rows=len(train),
        validation_rows=len(validation),
        feature_count=len(x_train.columns),
        baseline_r2=baseline_r2,
        baseline_mae=baseline_mae,
        directional_accuracy=dir_acc,
    )
    summary = {
        **result.__dict__,
        'seq_len': seq_len,
        'max_train_rows': max_train_rows,
        'max_validation_rows': max_validation_rows,
        'n_estimators': n_estimators,
        'seed': seed,
        'train_path': str(train_path),
        'validation_path': str(validation_path),
    }
    (output_dir / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    write_markdown_report(output_dir / 'report.md', result, group_report, feature_report.head(25), summary)
    return result


def write_markdown_report(
    path: Path,
    result: DiagnosticResult,
    group_report: pd.DataFrame,
    top_features: pd.DataFrame,
    summary: dict,
) -> None:
    dir_acc = 'n/a' if result.directional_accuracy is None else f'{result.directional_accuracy:.4f}'
    lines = [
        '# Current Feature Importance Diagnostics',
        '',
        '## Scope',
        '',
        'Read-only diagnostic over existing labeled CSV exports. No neural-network training and no `lib_PIC` changes.',
        '',
        '## Configuration',
        '',
        f'- Target: `{result.target}`',
        f'- Train rows: `{result.train_rows}`',
        f'- Validation rows: `{result.validation_rows}`',
        f'- Feature count: `{result.feature_count}`',
        f'- seq_len: `{summary["seq_len"]}`',
        f'- RandomForest trees: `{summary["n_estimators"]}`',
        '',
        '## Baseline',
        '',
        f'- Validation R2: `{result.baseline_r2:.6f}`',
        f'- Validation MAE: `{result.baseline_mae:.6f}`',
        f'- Directional accuracy: `{dir_acc}`',
        '',
        '## Group Importance',
        '',
        _markdown_table(group_report),
        '',
        '## Top Individual Features',
        '',
        _markdown_table(top_features),
        '',
        '## Interpretation Rules',
        '',
        '- `r2_drop` shows how much validation R2 falls when the whole group is shuffled.',
        '- `mae_increase` shows how much validation error grows when the whole group is shuffled.',
        '- This is not a trading verdict. It only shows which current input groups are useful for the chosen target.',
    ]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def _markdown_table(frame: pd.DataFrame) -> str:
    """Рендерит небольшую markdown-таблицу без зависимости от tabulate."""
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Current feature importance diagnostics for Nero fractal CSV.')
    parser.add_argument('--train', type=Path, default=DATA_DIR / 'Nero_train_labeled.csv')
    parser.add_argument('--validation', type=Path, default=DATA_DIR / 'Nero_validation_labeled.csv')
    parser.add_argument('--target', default='trail_24_pnl_atr_x8')
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument('--seq-len', type=int, default=100)
    parser.add_argument('--max-train-rows', type=int, default=20000)
    parser.add_argument('--max-validation-rows', type=int, default=10000)
    parser.add_argument('--chunksize', type=int, default=5000)
    parser.add_argument('--n-estimators', type=int, default=200)
    parser.add_argument('--seed', type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_diagnostics(
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
    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
