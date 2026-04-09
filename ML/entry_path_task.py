import numpy as np
import pandas as pd
from sklearn.metrics import f1_score


ENTRY_PATH_TARGET = 'entry_path_v1'
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

    active_frame = frame[frame['signal'] != 0].copy()
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
