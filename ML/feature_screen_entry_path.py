from __future__ import annotations

import pandas as pd
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression


def rank_features_by_mutual_information(
    frame: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    task: str = 'regression',
) -> pd.DataFrame:
    x = frame[feature_cols].astype(float)
    y = frame[target_col].astype(float)
    if task == 'classification':
        scores = mutual_info_classif(x, y, discrete_features=False, random_state=42)
    else:
        scores = mutual_info_regression(x, y, discrete_features=False, random_state=42)
    return pd.DataFrame({'feature': feature_cols, 'mi_score': scores}).sort_values(
        ['mi_score', 'feature'],
        ascending=[False, True],
    ).reset_index(drop=True)
