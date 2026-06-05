import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from ML.entry_path_feature_bank import FEATURE_BANK_COLUMNS, build_entry_path_feature_bank
from ML.lib_pic_feature_profiles import LIB_PIC_FEATURE_PROFILES, build_lib_pic_feature_profile


ENTRY_PATH_TARGET = 'entry_path_v1'
ENTRY_PATH_ALLOWED_SEQUENCE_LENGTHS = (20, 50, 100)
ENTRY_PATH_MODEL_NAMES = ('transformer', 'entry_path_dual_stream')
ENTRY_PATH_DEFAULT_FEATURE_PROFILE = 'entry_path_v1'
ENTRY_PATH_LIVE_SAFE_FEATURE_PROFILE = 'entry_path_v1_live_safe'
ENTRY_PATH_BUILTIN_FEATURE_PROFILES = (ENTRY_PATH_DEFAULT_FEATURE_PROFILE, ENTRY_PATH_LIVE_SAFE_FEATURE_PROFILE)
ENTRY_PATH_FEATURE_PROFILES = (*ENTRY_PATH_BUILTIN_FEATURE_PROFILES, *LIB_PIC_FEATURE_PROFILES)
ENTRY_PATH_RET_TARGETS = ['ret_6_dir_atr', 'ret_12_dir_atr', 'ret_24_dir_atr']
ENTRY_PATH_PATH_REG_TARGETS = [
    'fav_6_atr',
    'adv_6_atr',
    'fav_12_atr',
    'adv_12_atr',
    'fav_24_atr',
    'adv_24_atr',
]
ENTRY_PATH_CLASS_TARGET = 'path_6_class'
ENTRY_PATH_V1_BASE_FEATURE_COLUMNS = [
    'session_hour',
    'weekday',
]
ENTRY_PATH_V1_WINDOW_FEATURE_COLUMNS = list(FEATURE_BANK_COLUMNS)
ENTRY_PATH_V1_FEATURE_COLUMNS = ENTRY_PATH_V1_BASE_FEATURE_COLUMNS + ENTRY_PATH_V1_WINDOW_FEATURE_COLUMNS
ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS = list(ENTRY_PATH_V1_FEATURE_COLUMNS)
ENTRY_PATH_REG_TARGETS = ENTRY_PATH_RET_TARGETS + ENTRY_PATH_PATH_REG_TARGETS
ENTRY_PATH_CLASS_MAP = {-1: 0, 0: 1, 1: 2}
ENTRY_PATH_INV_CLASS_MAP = {value: key for key, value in ENTRY_PATH_CLASS_MAP.items()}


def split_entry_path_targets(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    y_reg = df[ENTRY_PATH_REG_TARGETS].values.astype(np.float32)
    y_cls_raw = df[ENTRY_PATH_CLASS_TARGET].values.astype(np.int64)
    unknown = sorted({int(label) for label in y_cls_raw if int(label) not in ENTRY_PATH_CLASS_MAP})
    if unknown:
        raise ValueError(f'Unsupported {ENTRY_PATH_CLASS_TARGET} values: {unknown}')
    y_cls = np.array([ENTRY_PATH_CLASS_MAP[int(label)] for label in y_cls_raw], dtype=np.int64)
    return y_reg, y_cls


def validate_entry_path_feature_profile(feature_profile: str) -> None:
    """Проверяет имя профиля инженерных признаков для `entry_path_v1`."""
    if feature_profile not in ENTRY_PATH_FEATURE_PROFILES:
        available = ', '.join(ENTRY_PATH_FEATURE_PROFILES)
        raise ValueError(f'unknown entry_path feature profile: {feature_profile}. Available: {available}')


def split_entry_path_features(
    df: pd.DataFrame,
    feature_profile: str = ENTRY_PATH_DEFAULT_FEATURE_PROFILE,
    seq_len: int = 100,
) -> np.ndarray:
    validate_entry_path_feature_profile(feature_profile)
    if feature_profile not in ENTRY_PATH_BUILTIN_FEATURE_PROFILES:
        return build_lib_pic_feature_profile(df, profile=feature_profile, seq_len=seq_len).to_numpy(dtype=np.float32)

    feature_frame = df
    if any(column not in feature_frame.columns for column in ENTRY_PATH_V1_WINDOW_FEATURE_COLUMNS):
        feature_frame = build_entry_path_feature_bank(feature_frame)
    feature_columns = (
        ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS
        if feature_profile == ENTRY_PATH_LIVE_SAFE_FEATURE_PROFILE
        else ENTRY_PATH_V1_FEATURE_COLUMNS
    )
    return (
        feature_frame.reindex(columns=feature_columns)
        .apply(pd.to_numeric, errors='coerce')
        .fillna(0.0)
        .values.astype(np.float32)
    )


def build_entry_path_model(model_name: str, model_kwargs: dict | None = None):
    allowed_keys = {
        'input_features',
        'engineered_feature_dim',
        'd_model',
        'nhead',
        'num_layers',
        'dim_feedforward',
        'dropout',
    }
    kwargs = {key: value for key, value in (model_kwargs or {}).items() if key in allowed_keys}
    if model_name == 'transformer':
        from ML.models.entry_path_transformer import EntryPathTransformer

        return EntryPathTransformer(**kwargs)
    if model_name == 'entry_path_dual_stream':
        from ML.models.entry_path_dual_stream_transformer import EntryPathDualStreamTransformer

        return EntryPathDualStreamTransformer(**kwargs)
    available = ', '.join(ENTRY_PATH_MODEL_NAMES)
    raise ValueError(f"Модель '{model_name}' не поддерживается для {ENTRY_PATH_TARGET}. Доступны: {available}")


def build_entry_path_export_frame(
    times: np.ndarray,
    signals: np.ndarray,
    pred_ret: np.ndarray,
    pred_path_reg: np.ndarray,
    pred_path_cls: np.ndarray,
    true_reg: np.ndarray | None = None,
    true_cls: np.ndarray | None = None,
) -> pd.DataFrame:
    n_rows = len(times)
    if len(signals) != n_rows:
        raise ValueError('signals must have the same length as times')
    if pred_ret.ndim != 2 or pred_ret.shape[1] != len(ENTRY_PATH_RET_TARGETS):
        raise ValueError(f'pred_ret must have shape (n, {len(ENTRY_PATH_RET_TARGETS)})')
    if pred_path_reg.ndim != 2 or pred_path_reg.shape[1] != len(ENTRY_PATH_PATH_REG_TARGETS):
        raise ValueError(f'pred_path_reg must have shape (n, {len(ENTRY_PATH_PATH_REG_TARGETS)})')
    if pred_path_cls.ndim != 2 or pred_path_cls.shape[1] != len(ENTRY_PATH_CLASS_MAP):
        raise ValueError(f'pred_path_cls must have shape (n, {len(ENTRY_PATH_CLASS_MAP)})')
    if len(pred_ret) != n_rows or len(pred_path_reg) != n_rows or len(pred_path_cls) != n_rows:
        raise ValueError('times, pred_ret, pred_path_reg, and pred_path_cls must have the same row count')

    frame = pd.DataFrame({
        'time': times,
        'signal': signals,
    })

    for idx, column in enumerate(ENTRY_PATH_RET_TARGETS):
        frame[f'pred_{column}'] = pred_ret[:, idx]

    for idx, column in enumerate(ENTRY_PATH_PATH_REG_TARGETS):
        frame[f'pred_{column}'] = pred_path_reg[:, idx]

    frame['pred_path_6_class'] = np.array(
        [ENTRY_PATH_INV_CLASS_MAP[int(label)] for label in pred_path_cls.argmax(axis=1)],
        dtype=np.int64,
    )
    frame['pred_path_6_prob_neg'] = pred_path_cls[:, 0]
    frame['pred_path_6_prob_flat'] = pred_path_cls[:, 1]
    frame['pred_path_6_prob_pos'] = pred_path_cls[:, 2]

    if true_reg is not None:
        if true_reg.ndim != 2 or true_reg.shape[1] != len(ENTRY_PATH_REG_TARGETS):
            raise ValueError(f'true_reg must have shape (n, {len(ENTRY_PATH_REG_TARGETS)})')
        if len(true_reg) != n_rows:
            raise ValueError('true_reg must have the same row count as times')
        for idx, column in enumerate(ENTRY_PATH_REG_TARGETS):
            frame[f'true_{column}'] = true_reg[:, idx]

    if true_cls is not None:
        if len(true_cls) != n_rows:
            raise ValueError('true_cls must have the same row count as times')
        unknown_true = sorted({int(label) for label in true_cls if int(label) not in ENTRY_PATH_INV_CLASS_MAP})
        if unknown_true:
            raise ValueError(f'Unsupported true_cls values: {unknown_true}')
        frame['true_path_6_class'] = np.array(
            [ENTRY_PATH_INV_CLASS_MAP[int(label)] for label in true_cls],
            dtype=np.int64,
        )

    return frame


def _safe_pearson(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 2 or len(y_pred) < 2:
        return 0.0
    if np.allclose(y_true, y_true[0]) or np.allclose(y_pred, y_pred[0]):
        return 0.0
    value = np.corrcoef(y_true, y_pred)[0, 1]
    if not np.isfinite(value):
        return 0.0
    return float(value)


def build_entry_path_report_markdown(
    frame: pd.DataFrame,
    model_name: str,
    artifact_name: str,
    split_label: str = 'Test',
    checkpoint_epoch: int | None = None,
    checkpoint_metric_name: str | None = None,
    checkpoint_metric_value: float | None = None,
) -> str:
    row_count = int(len(frame))
    required_true_cols = {f'true_{name}' for name in ENTRY_PATH_REG_TARGETS} | {'true_path_6_class'}
    checkpoint_lines = []
    if checkpoint_epoch is not None:
        checkpoint_lines.append(f'**Checkpoint epoch**: {checkpoint_epoch}')
    if checkpoint_metric_name is not None and checkpoint_metric_value is not None:
        checkpoint_lines.append(f'**Best val {checkpoint_metric_name}**: {checkpoint_metric_value:.4f}')

    if not required_true_cols.issubset(frame.columns):
        lines = [
            '# Entry Path v1 Test Set Evaluation',
            '',
            f'**Модель**: {model_name}',
            f'**Набор**: {split_label} ({row_count} строк)',
        ]
        if checkpoint_lines:
            lines.extend(['', *checkpoint_lines])
        lines.extend([
            '',
            '## Summary',
            '',
            f'- row_count: **{row_count}**',
            '- ret_pearson_r: **N/A**',
            '- path_reg_pearson_r: **N/A**',
            '- path_cls_f1_macro: **N/A**',
            '',
            '## Artifacts',
            '',
            f'- Predictions CSV: `{artifact_name}`',
            '',
            '## Notes',
            '',
            '- В этом CSV нет true entry_path_v1 колонок, поэтому метрики недоступны.',
        ])
        return '\n'.join(lines)

    active_frame = frame[frame['signal'] != 0].copy()

    def compute_trade_summary(trades: pd.DataFrame) -> dict[str, float | int]:
        if trades.empty:
            return {
                'trades_per_year': 0.0,
                'pf': 0.0,
                'profit_concentration_top_10': 1.0,
                'negative_year_slices': 0,
            }
        pnl = trades['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        gross_profit = float(pnl[pnl > 0].sum())
        gross_loss = float(-pnl[pnl < 0].sum())
        pf = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0.0
        top_k = max(1, int(np.ceil(len(pnl) * 0.1)))
        positive_sorted = np.sort(pnl[pnl > 0])[::-1]
        profit_concentration = 1.0
        if gross_profit > 0 and len(positive_sorted) > 0:
            profit_concentration = float(positive_sorted[:top_k].sum() / gross_profit)

        trade_times = pd.to_datetime(trades['time'], format='%Y.%m.%d %H:%M', errors='coerce')
        valid_years = trade_times.dt.year.dropna()
        if len(valid_years) == 0:
            trades_per_year = float(len(trades))
            negative_year_slices = 0
        else:
            year_count = max(1, int(valid_years.nunique()))
            trades_per_year = float(len(trades) / year_count)
            yearly = pd.DataFrame({'year': trade_times.dt.year, 'pnl': pnl}).dropna(subset=['year'])
            year_pf = yearly.groupby('year')['pnl'].apply(
                lambda series: (
                    float(series[series > 0].sum()) / float(-series[series < 0].sum())
                    if float(-series[series < 0].sum()) > 0
                    else float('inf') if float(series[series > 0].sum()) > 0 else 0.0
                )
            )
            negative_year_slices = int((year_pf < 1.0).sum())
        return {
            'trades_per_year': trades_per_year,
            'pf': pf,
            'profit_concentration_top_10': profit_concentration,
            'negative_year_slices': negative_year_slices,
        }

    active_trade_summary = compute_trade_summary(active_frame)

    ret_rows = []
    path_reg_rows = []

    for name in ENTRY_PATH_RET_TARGETS:
        y_true = frame[f'true_{name}'].to_numpy(dtype=np.float64)
        y_pred = frame[f'pred_{name}'].to_numpy(dtype=np.float64)
        ret_rows.append({
            'name': name,
            'pearson_r': _safe_pearson(y_true, y_pred),
            'mae': float(np.mean(np.abs(y_pred - y_true))),
        })

    for name in ENTRY_PATH_PATH_REG_TARGETS:
        y_true = frame[f'true_{name}'].to_numpy(dtype=np.float64)
        y_pred = frame[f'pred_{name}'].to_numpy(dtype=np.float64)
        path_reg_rows.append({
            'name': name,
            'pearson_r': _safe_pearson(y_true, y_pred),
            'mae': float(np.mean(np.abs(y_pred - y_true))),
        })

    y_true_cls = frame['true_path_6_class'].to_numpy(dtype=np.int64)
    y_pred_cls = frame['pred_path_6_class'].to_numpy(dtype=np.int64)
    class_labels = [-1, 0, 1]
    class_f1 = f1_score(y_true_cls, y_pred_cls, labels=class_labels, average=None, zero_division=0)
    path_cls_f1_macro = float(
        f1_score(y_true_cls, y_pred_cls, labels=class_labels, average='macro', zero_division=0)
    )

    ret_pearson_r = float(np.mean([row['pearson_r'] for row in ret_rows]))
    path_reg_pearson_r = float(np.mean([row['pearson_r'] for row in path_reg_rows]))

    n_slice = max(1, int(row_count * 0.1))
    sorted_frame = frame.sort_values('pred_ret_24_dir_atr')
    bottom_slice = sorted_frame.head(n_slice)
    top_slice = sorted_frame.tail(n_slice)

    def slice_row(label: str, slice_df: pd.DataFrame) -> dict[str, float | int | str]:
        true_ret = slice_df['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        return {
            'label': label,
            'rows': int(len(slice_df)),
            'mean_true_ret_24': float(np.mean(true_ret)),
            'positive_share': float(np.mean(true_ret > 0)),
        }

    slice_rows = [
        slice_row('Bottom 10%', bottom_slice),
        slice_row('Top 10%', top_slice),
    ]

    active_lines = []
    if len(active_frame) > 0:
        active_ret_rows = []
        for name in ENTRY_PATH_RET_TARGETS:
            y_true = active_frame[f'true_{name}'].to_numpy(dtype=np.float64)
            y_pred = active_frame[f'pred_{name}'].to_numpy(dtype=np.float64)
            active_ret_rows.append({
                'name': name,
                'pearson_r': _safe_pearson(y_true, y_pred),
                'mae': float(np.mean(np.abs(y_pred - y_true))),
            })

        active_ret_pearson_r = float(np.mean([row['pearson_r'] for row in active_ret_rows]))
        active_y_true_cls = active_frame['true_path_6_class'].to_numpy(dtype=np.int64)
        active_y_pred_cls = active_frame['pred_path_6_class'].to_numpy(dtype=np.int64)
        active_class_f1 = f1_score(
            active_y_true_cls,
            active_y_pred_cls,
            labels=class_labels,
            average=None,
            zero_division=0,
        )
        active_path_cls_f1_macro = float(
            f1_score(
                active_y_true_cls,
                active_y_pred_cls,
                labels=class_labels,
                average='macro',
                zero_division=0,
            )
        )
        active_sorted = active_frame.sort_values('pred_ret_24_dir_atr')
        active_n_slice = max(1, int(len(active_frame) * 0.1))
        active_slice_rows = [
            slice_row('Bottom 10%', active_sorted.head(active_n_slice)),
            slice_row('Top 10%', active_sorted.tail(active_n_slice)),
        ]

        active_lines.extend([
            '',
            '## Active Trades Only',
            '',
            f'- active_rows: **{len(active_frame)}**',
            f'- active_ret_pearson_r: **{active_ret_pearson_r:.4f}**',
            f'- active_path_cls_f1_macro: **{active_path_cls_f1_macro:.4f}**',
            f"- trades_per_year: **{active_trade_summary['trades_per_year']:.2f}**",
            f"- PF: **{active_trade_summary['pf']:.4f}**",
            f"- profit_concentration_top_10: **{active_trade_summary['profit_concentration_top_10']:.4f}**",
            f"- negative_year_slices: **{active_trade_summary['negative_year_slices']}**",
            '',
            '| Target | Pearson r | MAE |',
            '|--------|-----------|-----|',
        ])
        for row in active_ret_rows:
            active_lines.append(f"| {row['name']} | {row['pearson_r']:.4f} | {row['mae']:.4f} |")

        active_lines.extend([
            '',
            '## Active Path Class',
            '',
            '| Class | F1 |',
            '|-------|----|',
        ])
        for label, f1_value in zip(class_labels, active_class_f1):
            active_lines.append(f'| {label} | {float(f1_value):.4f} |')

        active_lines.extend([
            '',
            '## Active Slice: pred_ret_24_dir_atr',
            '',
            '| Slice | Rows | mean true_ret_24_dir_atr | positive share |',
            '|-------|------|--------------------------|----------------|',
        ])
        for row in active_slice_rows:
            active_lines.append(
                f"| {row['label']} | {row['rows']} | {row['mean_true_ret_24']:.4f} | {row['positive_share']:.1%} |"
            )

    lines = [
        '# Entry Path v1 Test Set Evaluation',
        '',
        f'**Модель**: {model_name}',
        f'**Набор**: {split_label} ({row_count} строк)',
    ]
    if checkpoint_lines:
        lines.extend(['', *checkpoint_lines])
    lines.extend([
        '',
        '## Summary',
        '',
        f'- row_count: **{row_count}**',
        f'- ret_pearson_r: **{ret_pearson_r:.4f}**',
        f'- path_reg_pearson_r: **{path_reg_pearson_r:.4f}**',
        f'- path_cls_f1_macro: **{path_cls_f1_macro:.4f}**',
        '',
        '## Return Targets',
        '',
        '| Target | Pearson r | MAE |',
        '|--------|-----------|-----|',
    ])
    for row in ret_rows:
        lines.append(f"| {row['name']} | {row['pearson_r']:.4f} | {row['mae']:.4f} |")

    lines.extend([
        '',
        '## Path Targets',
        '',
        '| Target | Pearson r | MAE |',
        '|--------|-----------|-----|',
    ])
    for row in path_reg_rows:
        lines.append(f"| {row['name']} | {row['pearson_r']:.4f} | {row['mae']:.4f} |")

    lines.extend([
        '',
        '## Path Class',
        '',
        '| Class | F1 |',
        '|-------|----|',
    ])
    for label, f1_value in zip(class_labels, class_f1):
        lines.append(f'| {label} | {float(f1_value):.4f} |')

    lines.extend([
        '',
        '## Slice: pred_ret_24_dir_atr',
        '',
        '| Slice | Rows | mean true_ret_24_dir_atr | positive share |',
        '|-------|------|--------------------------|----------------|',
    ])
    for row in slice_rows:
        lines.append(
            f"| {row['label']} | {row['rows']} | {row['mean_true_ret_24']:.4f} | {row['positive_share']:.1%} |"
        )

    lines.extend([
        '',
        '## Artifacts',
        '',
        f'- Predictions CSV: `{artifact_name}`',
    ])
    lines.extend(active_lines)
    return '\n'.join(lines)
