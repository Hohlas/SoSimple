from pathlib import Path

import joblib
import numpy as np
from sklearn.isotonic import IsotonicRegression


def fit_tb_probability_calibrator(
    y_pred_proba: np.ndarray,
    y_true: np.ndarray,
    target_names: list[str],
) -> dict:
    y_pred = np.asarray(y_pred_proba, dtype=np.float64)
    y_true = np.asarray(y_true, dtype=np.float64)

    calibrators = []
    stats = []

    for i, name in enumerate(target_names):
        x = np.clip(y_pred[:, i], 0.0, 1.0)
        y = np.where(y_true[:, i] == 1.0, 1.0, 0.0)

        if np.unique(y).size < 2 or np.unique(x).size < 2:
            calibrators.append(None)
            stats.append({
                'target': name,
                'method': 'identity',
                'samples': int(len(y)),
                'positives': int(y.sum()),
            })
            continue

        calibrator = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds='clip')
        calibrator.fit(x, y)
        calibrators.append(calibrator)
        stats.append({
            'target': name,
            'method': 'isotonic',
            'samples': int(len(y)),
            'positives': int(y.sum()),
        })

    return {
        'method': 'isotonic_per_target',
        'target_names': list(target_names),
        'calibrators': calibrators,
        'stats': stats,
    }


def apply_tb_probability_calibration(
    y_pred_proba: np.ndarray,
    calibrator_bundle: dict,
) -> np.ndarray:
    proba = np.asarray(y_pred_proba, dtype=np.float64)
    original_shape = proba.shape
    squeeze_back = proba.ndim == 1
    if squeeze_back:
        proba = proba.reshape(-1, 1)

    calibrated = np.empty_like(proba, dtype=np.float64)
    calibrators = calibrator_bundle.get('calibrators', [])

    for i in range(proba.shape[1]):
        col = np.clip(proba[:, i], 0.0, 1.0)
        calibrator = calibrators[i] if i < len(calibrators) else None
        calibrated[:, i] = calibrator.transform(col) if calibrator is not None else col

    if squeeze_back:
        return calibrated.reshape(original_shape)
    return calibrated


def save_tb_probability_calibrator(calibrator_bundle: dict, path: str | Path) -> None:
    joblib.dump(calibrator_bundle, Path(path))


def load_tb_probability_calibrator(path: str | Path) -> dict:
    return joblib.load(Path(path))
