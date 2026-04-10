import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from ML.entry_path_task import (
    ENTRY_PATH_CLASS_MAP,
    ENTRY_PATH_INV_CLASS_MAP,
    ENTRY_PATH_PATH_REG_TARGETS,
    ENTRY_PATH_REG_TARGETS,
    ENTRY_PATH_RET_TARGETS,
    build_entry_path_export_frame,
)
from ML.models.entry_path_v1_quantile_transformer import EntryPathV1QuantileTransformer

ENTRY_PATH_V1_QUANTILE_TARGET = 'entry_path_v1_quantile'
ENTRY_PATH_V1_QUANTILE_Q10_COLUMN = 'pred_ret_24_q10'
ENTRY_PATH_V1_QUANTILE_Q90_COLUMN = 'pred_ret_24_q90'


def build_entry_path_v1_quantile_model(model_kwargs: dict | None = None) -> EntryPathV1QuantileTransformer:
    allowed_keys = {
        'input_features',
        'd_model',
        'nhead',
        'num_layers',
        'dim_feedforward',
        'dropout',
    }
    kwargs = {key: value for key, value in (model_kwargs or {}).items() if key in allowed_keys}
    return EntryPathV1QuantileTransformer(**kwargs)


def _safe_pearson(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=np.float64).reshape(-1)
    y_pred = np.asarray(y_pred, dtype=np.float64).reshape(-1)
    if len(y_true) < 2 or len(y_pred) < 2:
        return 0.0
    if np.allclose(y_true, y_true[0]) or np.allclose(y_pred, y_pred[0]):
        return 0.0
    value = np.corrcoef(y_true, y_pred)[0, 1]
    if not np.isfinite(value):
        return 0.0
    return float(value)


def _as_1d(array: np.ndarray) -> np.ndarray:
    return np.asarray(array).reshape(-1)


def _pinball_numpy(y_true: np.ndarray, y_pred: np.ndarray, q: float) -> float:
    y_true = _as_1d(y_true).astype(np.float64)
    y_pred = _as_1d(y_pred).astype(np.float64)
    diff = y_true - y_pred
    return float(np.mean(np.maximum(q * diff, (q - 1.0) * diff)))


def build_entry_path_v1_quantile_export_frame(
    times: np.ndarray,
    signals: np.ndarray,
    pred_ret: np.ndarray,
    pred_path_reg: np.ndarray,
    pred_path_cls: np.ndarray,
    pred_q10: np.ndarray,
    pred_q90: np.ndarray,
    true_reg: np.ndarray | None = None,
    true_cls: np.ndarray | None = None,
) -> pd.DataFrame:
    frame = build_entry_path_export_frame(
        times=times,
        signals=signals,
        pred_ret=pred_ret,
        pred_path_reg=pred_path_reg,
        pred_path_cls=pred_path_cls,
        true_reg=true_reg,
        true_cls=true_cls,
    )

    pred_q10 = _as_1d(pred_q10)
    pred_q90 = _as_1d(pred_q90)
    if len(pred_q10) != len(frame) or len(pred_q90) != len(frame):
        raise ValueError('pred_q10 and pred_q90 must have the same row count as times')

    frame['pred_ret_24_q10'] = pred_q10
    frame['pred_ret_24_q90'] = pred_q90
    return frame


def compute_entry_path_v1_quantile_metrics(
    true_ret: np.ndarray,
    pred_ret24: np.ndarray,
    pred_q10: np.ndarray,
    pred_q90: np.ndarray,
    path_reg_pearson_r: float,
    path_cls_f1_macro: float,
) -> dict[str, float]:
    true_ret = _as_1d(true_ret)
    pred_ret24 = _as_1d(pred_ret24)
    pred_q10 = _as_1d(pred_q10)
    pred_q90 = _as_1d(pred_q90)

    lengths = {len(true_ret), len(pred_ret24), len(pred_q10), len(pred_q90)}
    if len(lengths) != 1:
        raise ValueError('true_ret, pred_ret24, pred_q10, and pred_q90 must have the same length')
    if np.any(pred_q10 > pred_q90):
        raise ValueError('pred_q10 must be <= pred_q90 for all rows')

    lower = np.minimum(pred_q10, pred_q90)
    upper = np.maximum(pred_q10, pred_q90)
    coverage = float(np.mean((true_ret >= lower) & (true_ret <= upper)))
    width = float(np.median(upper - lower))
    ret_pearson_r = _safe_pearson(true_ret, pred_ret24)
    q10_pinball_loss = _pinball_numpy(true_ret, pred_q10, 0.1)
    q90_pinball_loss = _pinball_numpy(true_ret, pred_q90, 0.9)
    coverage_error = abs(coverage - 0.80)
    val_score = float(
        ret_pearson_r
        + 0.25 * float(path_reg_pearson_r)
        + 0.10 * float(path_cls_f1_macro)
        - 0.5 * coverage_error
        - 0.05 * width
    )

    return {
        'ret_pearson_r': ret_pearson_r,
        'interval_coverage': coverage,
        'median_interval_width': width,
        'coverage_error': coverage_error,
        'q10_pinball_loss': q10_pinball_loss,
        'q90_pinball_loss': q90_pinball_loss,
        'val_score': val_score,
    }


def build_entry_path_v1_quantile_report_markdown(
    frame: pd.DataFrame,
    model_name: str,
    artifact_name: str,
    split_label: str = 'Test',
    checkpoint_epoch: int | None = None,
    checkpoint_metric_name: str | None = None,
    checkpoint_metric_value: float | None = None,
) -> str:
    row_count = int(len(frame))
    checkpoint_lines = []
    if checkpoint_epoch is not None:
        checkpoint_lines.append(f'**Checkpoint epoch**: {checkpoint_epoch}')
    if checkpoint_metric_name is not None and checkpoint_metric_value is not None:
        checkpoint_lines.append(f'**Best val {checkpoint_metric_name}**: {checkpoint_metric_value:.4f}')

    required_true_cols = {f'true_{name}' for name in ENTRY_PATH_REG_TARGETS} | {'true_path_6_class'}
    if required_true_cols.issubset(frame.columns):
        true_ret = frame['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        pred_ret24 = frame['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        pred_q10 = frame[ENTRY_PATH_V1_QUANTILE_Q10_COLUMN].to_numpy(dtype=np.float64)
        pred_q90 = frame[ENTRY_PATH_V1_QUANTILE_Q90_COLUMN].to_numpy(dtype=np.float64)
        y_true_cls = frame['true_path_6_class'].to_numpy(dtype=np.int64)
        y_pred_cls = frame['pred_path_6_class'].to_numpy(dtype=np.int64)
        class_labels = [-1, 0, 1]
        metrics = compute_entry_path_v1_quantile_metrics(
            true_ret=true_ret,
            pred_ret24=pred_ret24,
            pred_q10=pred_q10,
            pred_q90=pred_q90,
            path_reg_pearson_r=float(
                np.mean([
                    _safe_pearson(
                        frame[f'true_{name}'].to_numpy(dtype=np.float64),
                        frame[f'pred_{name}'].to_numpy(dtype=np.float64),
                    )
                    for name in ENTRY_PATH_PATH_REG_TARGETS
                ])
            ),
            path_cls_f1_macro=float(
                f1_score(y_true_cls, y_pred_cls, labels=class_labels, average='macro', zero_division=0)
            ),
        )
        summary_lines = [
            f'- row_count: **{row_count}**',
            f"- ret_pearson_r: **{metrics['ret_pearson_r']:.4f}**",
            f"- interval_coverage: **{metrics['interval_coverage']:.4f}**",
            f"- median_interval_width: **{metrics['median_interval_width']:.4f}**",
            f"- q10_pinball_loss: **{metrics['q10_pinball_loss']:.4f}**",
            f"- q90_pinball_loss: **{metrics['q90_pinball_loss']:.4f}**",
            f"- val_score: **{metrics['val_score']:.4f}**",
        ]
    else:
        summary_lines = [
            f'- row_count: **{row_count}**',
            '- ret_pearson_r: **N/A**',
            '- interval_coverage: **N/A**',
            '- median_interval_width: **N/A**',
            '- q10_pinball_loss: **N/A**',
            '- q90_pinball_loss: **N/A**',
            '- val_score: **N/A**',
        ]

    lines = [
        '# Entry Path v1 Quantile Test Set Evaluation',
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
        *summary_lines,
        '',
        '## Artifacts',
        '',
        f'- Predictions CSV: `{artifact_name}`',
    ])
    return '\n'.join(lines)
