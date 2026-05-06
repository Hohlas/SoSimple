# =============================================================================
# Файл: online_causal_preprocessing.py
# Назначение: Live-safe подготовка Nero.csv перед online inference.
# Обновлён: 2026-04-29
# Входные данные:
#   - raw/snapshot Nero.csv (откуда: MT4 или telemetry watcher)
# Выходные данные:
#   - preprocessed CSV с отсортированными и нормализованными фракталами
# Использование:
#   from processing.online_causal_preprocessing import preprocess_online_csv
# Примечания:
#   - Выполняет только causal subset: сортировка фракталов + проверка + rowwise-нормализация.
#   - Не вызывает разметку signal/predict и не использует будущие бары.
# =============================================================================

from __future__ import annotations

from pathlib import Path

import pandas as pd

from processing.fractal_preprocessing import fractal_columns_in_order, sort_fractals_in_dataframe
from processing.normalize import FRACTAL_INDICES, parse_fractal
from processing.normalize import normalize_rowwise


NORMALIZED_VALUE_FIELDS = (
    "price",
    "front",
    "back",
    "break",
    "reverse",
    "power",
    "count",
    "impulse",
    "up_12",
    "dn_12",
    "up_24",
    "dn_24",
    "up_48",
    "dn_48",
)


def _fractal_time(raw: object) -> int | None:
    if pd.isna(raw) or raw == "":
        return None
    parts = str(raw).split(":", 1)
    if not parts:
        return None
    try:
        return int(float(parts[0]))
    except (TypeError, ValueError):
        return None


def validate_fractal_sorting(df: pd.DataFrame) -> dict[str, int]:
    """Validate that every row has fractal times in descending order."""
    fractal_columns = fractal_columns_in_order(df.columns)
    error_rows = 0

    for _, row in df[fractal_columns].iterrows() if fractal_columns else []:
        previous_time: int | None = None
        row_has_error = False
        for column in fractal_columns:
            current_time = _fractal_time(row[column])
            if current_time is None:
                continue
            if previous_time is not None and previous_time < current_time:
                row_has_error = True
                break
            previous_time = current_time
        if row_has_error:
            error_rows += 1

    checked_rows = int(len(df))
    if error_rows:
        raise ValueError(
            "fractal sorting validation failed: "
            f"error_rows={error_rows} checked_rows={checked_rows}"
        )
    return {"checked_rows": checked_rows, "error_rows": error_rows}


def _looks_rowwise_normalized(df: pd.DataFrame) -> bool:
    """Best-effort guard against normalizing an already preprocessed snapshot twice."""
    fractal_columns = fractal_columns_in_order(df.columns)
    if not fractal_columns or df.empty:
        return False

    indices = [FRACTAL_INDICES[name] for name in NORMALIZED_VALUE_FIELDS]
    saw_fractal = False
    for _, row in df[fractal_columns].iterrows():
        for column in fractal_columns:
            parsed = parse_fractal(row[column])
            if parsed is None:
                continue
            saw_fractal = True
            for idx in indices:
                value = parsed[idx]
                if pd.isna(value):
                    continue
                if float(value) < -1e-9 or float(value) > 1.0 + 1e-9:
                    return False

    return saw_fractal


def preprocess_online_frame(df: pd.DataFrame, *, debug: bool = False) -> pd.DataFrame:
    """Apply the live-safe subset of the training preprocessing pipeline.

    This deliberately excludes every labeling step that needs future bars.
    """
    sorted_df = sort_fractals_in_dataframe(df, debug=debug)
    validate_fractal_sorting(sorted_df)
    if sorted_df.empty:
        return sorted_df
    if _looks_rowwise_normalized(sorted_df):
        return sorted_df
    processed = normalize_rowwise(
        sorted_df,
        debug=debug,
        verbose=debug,
        include_predict_in_front_back_pool=False,
    )
    validate_fractal_sorting(processed)
    return processed


def preprocess_online_csv(
    *,
    input_csv: str | Path,
    output_csv: str | Path,
    debug: bool = False,
) -> pd.DataFrame:
    frame = pd.read_csv(Path(input_csv), sep=";")
    processed = preprocess_online_frame(frame, debug=debug)
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    processed.to_csv(output_path, sep=";", index=False)
    return processed
