# =============================================================================
# Файл: fractal_level_feature_builder.py
# Назначение: Live-safe аудит и признаки уровня вокруг fractal0 для entry path.
# Обновлён: 2026-05-15
# Входные данные:
#   - DATA/Nero_*_labeled.csv (откуда: processing/label_main.py)
# Выходные данные:
#   - Признаки уровня и JSON-аудит (куда: ML/reports/entry_path_v1_fractal_level_signal/)
# Использование:
#   from ML.fractal_level_feature_builder import parse_fractal, audit_fractal_rows
# Примечания:
#   - Offline target columns не используются для доказательства live-safe признаков.
# =============================================================================

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


FRACTAL_FIELDS = {
    "time": 0,
    "price": 1,
    "direction": 2,
    "front": 3,
    "back": 4,
    "strong": 5,
    "break": 6,
    "reverse": 7,
    "power": 8,
    "count": 9,
    "impulse": 10,
    "up_12": 11,
    "dn_12": 12,
    "up_24": 13,
    "dn_24": 14,
    "up_48": 15,
    "dn_48": 16,
    "up_3": 17,
    "dn_3": 18,
    "up_6": 19,
    "dn_6": 20,
    "fractal_atr": 21,
}

_INT_FIELDS = {"direction", "strong", "break", "count"}
_UPDN_FIELDS = ("up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48")


def parse_fractal(fractal_str: object) -> dict[str, Any] | None:
    """Парсит строку фрактала в словарь с 22 полями."""
    if pd.isna(fractal_str) or fractal_str == "":
        return None

    parts = str(fractal_str).split(":")
    if len(parts) < 7:
        return None

    parsed: dict[str, Any] = {}
    try:
        for name, pos in FRACTAL_FIELDS.items():
            if pos >= len(parts) or parts[pos] == "":
                parsed[name] = 0 if name in _INT_FIELDS else 0.0
                continue
            if name == "time":
                try:
                    parsed[name] = int(float(parts[pos]))
                except ValueError:
                    parsed[name] = parts[pos]
            elif name in _INT_FIELDS:
                parsed[name] = int(float(parts[pos]))
            else:
                parsed[name] = float(parts[pos])
    except (TypeError, ValueError):
        return None

    if len(parts) < 22:
        parsed["fractal_atr"] = float(parts[17]) if len(parts) > 17 else 0.0
        for name in ("up_3", "dn_3", "up_6", "dn_6"):
            parsed[name] = 0.0

    return parsed


def parse_row_time(value: object) -> pd.Timestamp | None:
    """Парсит `time` строки Nero.csv как UTC-naive timestamp."""
    if pd.isna(value):
        return None
    parsed = pd.to_datetime(str(value), format="%Y.%m.%d %H:%M", errors="coerce")
    if pd.isna(parsed):
        return None
    return pd.Timestamp(parsed).tz_localize(None)


def parse_fractal_time(value: object) -> pd.Timestamp | None:
    """Парсит время фрактала, если формат доказуемо совпадает с row time."""
    if pd.isna(value):
        return None
    text = str(value)
    if _is_numeric_text(text):
        parsed = pd.to_datetime(float(text), unit="s", errors="coerce")
        if pd.isna(parsed):
            return None
        return pd.Timestamp(parsed).tz_localize(None)
    parsed = pd.to_datetime(text, format="%Y.%m.%d %H:%M", errors="coerce")
    if pd.isna(parsed):
        return None
    return pd.Timestamp(parsed).tz_localize(None)


def fractal_columns_in_order(columns: list[str] | pd.Index) -> list[str]:
    """Возвращает fractalN-колонки в числовом порядке."""
    names = [str(name) for name in columns if str(name).startswith("fractal")]

    def suffix(name: str) -> int:
        try:
            return int(name.replace("fractal", "", 1))
        except ValueError:
            return 10**9

    return sorted(names, key=suffix)


def audit_fractal_rows(frame: pd.DataFrame) -> dict[str, int | float]:
    """Проверяет live-safe инварианты текущей строки фракталов."""
    fractal_columns = fractal_columns_in_order(frame.columns)
    row_count = int(len(frame))
    missing_invalid_fractal0_rows = 0
    future_fractal_rows = 0
    unknown_time_format_rows = 0
    fractal0_updn_nonzero_rows = 0
    old_updn_nonzero_rows = 0
    sort_violation_rows = 0

    row_times = pd.to_datetime(frame["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    row_seconds_values = row_times.to_numpy(dtype="datetime64[s]").astype("int64").astype("float64")
    row_seconds_values[row_times.isna().to_numpy()] = np.nan
    fractal_values = frame[fractal_columns].astype(str).to_numpy()
    fractal0_pos = fractal_columns.index("fractal0") if "fractal0" in fractal_columns else None

    for row_pos in range(row_count):
        row_seconds = row_seconds_values[row_pos]
        if np.isnan(row_seconds):
            row_seconds = None
        row_has_future = False
        row_has_unknown = False
        previous_numeric_time: float | None = None
        old_updn_nonzero = False

        fractal0_parts = _split_fractal_fast(fractal_values[row_pos, fractal0_pos]) if fractal0_pos is not None else None
        if fractal0_parts is None:
            missing_invalid_fractal0_rows += 1
        elif _parts_have_updn(fractal0_parts):
            fractal0_updn_nonzero_rows += 1

        for col_pos, col in enumerate(fractal_columns):
            parts = _split_fractal_fast(fractal_values[row_pos, col_pos])
            if parts is None:
                continue

            numeric_time = _numeric_or_none(parts[0])
            if numeric_time is not None:
                if row_seconds is not None and numeric_time > row_seconds:
                    row_has_future = True
            else:
                comparable = parse_fractal_time(parts[0])
                if comparable is not None and row_seconds is not None:
                    if float(comparable.timestamp()) > float(row_seconds):
                        row_has_future = True
                else:
                    row_has_unknown = True

            if numeric_time is not None:
                if previous_numeric_time is not None and numeric_time > previous_numeric_time:
                    sort_violation_rows += 1
                    previous_numeric_time = None
                elif previous_numeric_time is not None:
                    previous_numeric_time = numeric_time
                else:
                    previous_numeric_time = numeric_time

            if col != "fractal0" and _parts_have_updn(parts):
                old_updn_nonzero = True

        if row_has_future:
            future_fractal_rows += 1
        if row_has_unknown:
            unknown_time_format_rows += 1
        if old_updn_nonzero:
            old_updn_nonzero_rows += 1

    return {
        "row_count": row_count,
        "missing_invalid_fractal0_rows": missing_invalid_fractal0_rows,
        "future_fractal_rows": future_fractal_rows,
        "unknown_time_format_rows": unknown_time_format_rows,
        "fractal0_updn_nonzero_rows": fractal0_updn_nonzero_rows,
        "old_updn_nonzero_rows": old_updn_nonzero_rows,
        "old_updn_nonzero_share": float(old_updn_nonzero_rows / row_count) if row_count else 0.0,
        "sort_violation_rows": sort_violation_rows,
        "fractal0_exists_after_preprocessing_rows": row_count - missing_invalid_fractal0_rows,
    }


ATR_ZONE_BOUNDS = [0.00, 0.25, 0.50, 1.00, 2.00, 4.00]


def build_zone_features(
    frame: pd.DataFrame,
    *,
    atr_zone_bounds: list[float] | None = None,
    include_updn: bool = True,
    raw_price_frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Строит zone-признаки: агрегация фракталов по ценовым зонам относительно fractal0.price."""
    bounds = atr_zone_bounds if atr_zone_bounds is not None else ATR_ZONE_BOUNDS
    zone_count = (len(bounds) - 1) * 2 + 1
    zone_names = []
    for i in range(len(bounds) - 1):
        zone_names.append(f"zone_{2*i}_above_{bounds[i]:.2f}_{bounds[i+1]:.2f}")
        zone_names.append(f"zone_{2*i+1}_below_{bounds[i]:.2f}_{bounds[i+1]:.2f}")
    zone_names.append("zone_10_far")

    zone_agg_fields = [
        "count", "direction_sum", "direction_abs_sum",
        "strong_count", "break_count",
        "power_sum", "power_max",
        "impulse_sum", "impulse_max",
    ]
    if include_updn:
        zone_agg_fields.extend(["up_24_sum", "dn_24_sum"])

    global_fields = [
        "fractals_above_count", "fractals_below_count",
        "fractal0_price_rank", "total_count",
        "closest_above_distance_atr", "closest_below_distance_atr",
    ]
    all_columns = []
    for zname in zone_names:
        for field in zone_agg_fields:
            all_columns.append(f"{zname}_{field}")
    all_columns.extend(global_fields)

    out_rows: list[dict[str, float | int]] = []
    fractal_columns = fractal_columns_in_order(frame.columns)
    raw_frame = raw_price_frame if raw_price_frame is not None else frame
    for row_pos, (_, row) in enumerate(frame.iterrows()):
        raw_row = raw_frame.iloc[row_pos] if row_pos < len(raw_frame) else row
        row_features: dict[str, float | int] = {}
        atr = _safe_float(row.get("ATR"), default=0.0)
        if atr <= 0:
            atr = 1.0
        fractal0 = parse_fractal(row.get("fractal0", ""))
        raw_fractal0 = parse_fractal(raw_row.get("fractal0", ""))
        base_price = float(raw_fractal0.get("price", 0.0)) if raw_fractal0 else (float(fractal0.get("price", 0.0)) if fractal0 else 0.0)
        row_features["fractal0_price_rank"] = 0.0

        zone_data: dict[str, dict[str, float]] = {zname: {f: 0.0 for f in zone_agg_fields} for zname in zone_names}

        above_count = 0
        below_count = 0
        total_count = 0
        closest_above = float("inf")
        closest_below = float("inf")

        for col in fractal_columns:
            parsed = parse_fractal(row.get(col, ""))
            if parsed is None:
                continue
            source_index = _fractal_index(col)
            if source_index == 0:
                continue
            raw_parsed = parse_fractal(raw_row.get(col, "")) or parsed
            price = float(raw_parsed.get("price", 0.0) or 0.0)
            direction = float(parsed.get("direction", 0) or 0)
            distance_atr = (price - base_price) / atr
            abs_distance = abs(distance_atr)

            if price > base_price:
                above_count += 1
                closest_above = min(closest_above, abs_distance)
            else:
                below_count += 1
                closest_below = min(closest_below, abs_distance)
            total_count += 1

            if abs_distance > bounds[-1]:
                zone = "zone_10_far"
            else:
                zone = None
                for i in range(len(bounds) - 1):
                    if bounds[i] <= abs_distance < bounds[i + 1]:
                        if distance_atr >= 0:
                            zone = zone_names[2 * i]
                        else:
                            zone = zone_names[2 * i + 1]
                        break
                if zone is None:
                    zone = "zone_10_far"

            zone_data[zone]["count"] += 1
            zone_data[zone]["direction_sum"] += direction
            zone_data[zone]["direction_abs_sum"] += abs(direction)
            zone_data[zone]["strong_count"] += float(parsed.get("strong", 0) or 0)
            zone_data[zone]["break_count"] += float(parsed.get("break", 0) or 0)
            zone_data[zone]["power_sum"] += float(parsed.get("power", 0) or 0)
            zone_data[zone]["power_max"] = max(zone_data[zone]["power_max"], float(parsed.get("power", 0) or 0))
            zone_data[zone]["impulse_sum"] += float(parsed.get("impulse", 0) or 0)
            zone_data[zone]["impulse_max"] = max(zone_data[zone]["impulse_max"], float(parsed.get("impulse", 0) or 0))
            if include_updn:
                zone_data[zone]["up_24_sum"] += float(parsed.get("up_24", 0) or 0)
                zone_data[zone]["dn_24_sum"] += float(parsed.get("dn_24", 0) or 0)

        if total_count > 0:
            row_features["fractal0_price_rank"] = float(below_count / max(total_count - 1, 1))
        row_features["fractals_above_count"] = int(above_count)
        row_features["fractals_below_count"] = int(below_count)
        row_features["total_count"] = int(total_count)
        row_features["closest_above_distance_atr"] = float(closest_above) if closest_above != float("inf") else 0.0
        row_features["closest_below_distance_atr"] = float(closest_below) if closest_below != float("inf") else 0.0

        for zname in zone_names:
            for field in zone_agg_fields:
                row_features[f"{zname}_{field}"] = zone_data[zname][field]

        out_rows.append(row_features)

    result = pd.DataFrame(out_rows, index=frame.index)
    for col in all_columns:
        if col not in result.columns:
            result[col] = 0.0
    return result.reindex(columns=all_columns).fillna(0.0)


def build_fractal_level_features(
    frame: pd.DataFrame,
    *,
    input_family: str = "nearest_k",
    k: int = 16,
    geometry_only: bool = False,
    raw_price_frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Строит model inputs из текущей строки фракталов."""
    if input_family == "nearest_k":
        return _build_nearest_k_features(frame, k=k, geometry_only=geometry_only, raw_price_frame=raw_price_frame)
    if input_family == "zones":
        return build_zone_features(frame, include_updn=not geometry_only, raw_price_frame=raw_price_frame)
    if input_family == "zones_plus_nearest_k":
        zone_df = build_zone_features(frame, include_updn=not geometry_only, raw_price_frame=raw_price_frame)
        nearest_df = _build_nearest_k_features(frame, k=k, geometry_only=geometry_only, raw_price_frame=raw_price_frame)
        shared_cols = set(zone_df.columns) & set(nearest_df.columns)
        next_cols = nearest_df[[c for c in nearest_df.columns if c not in shared_cols]]
        return pd.concat([zone_df, next_cols], axis=1)
    raise ValueError(f"unsupported input_family: {input_family}")


def _build_nearest_k_features(
    frame: pd.DataFrame,
    *,
    k: int,
    geometry_only: bool = False,
    raw_price_frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    fractal_columns = fractal_columns_in_order(frame.columns)
    raw_frame = raw_price_frame if raw_price_frame is not None else frame
    out_rows: list[dict[str, float | int]] = []
    for row_pos, (_, row) in enumerate(frame.iterrows()):
        raw_row = raw_frame.iloc[row_pos] if row_pos < len(raw_frame) else row
        row_features: dict[str, float | int] = {}
        atr = _safe_float(row.get("ATR"), default=0.0)
        if atr <= 0:
            atr = 1.0
        fractal0 = parse_fractal(row.get("fractal0", ""))
        raw_fractal0 = parse_fractal(raw_row.get("fractal0", ""))
        base_price = float(raw_fractal0.get("price", 0.0)) if raw_fractal0 else (float(fractal0.get("price", 0.0)) if fractal0 else 0.0)
        base_direction = int(fractal0.get("direction", 0)) if fractal0 else 0
        row_features["atr"] = float(atr)
        row_features["fractal0_direction"] = int(base_direction)
        row_features["fractal0_price_rank"] = 0.0

        candidates = []
        prices = []
        for col in fractal_columns:
            parsed = parse_fractal(row.get(col, ""))
            if parsed is None:
                continue
            source_index = _fractal_index(col)
            if source_index == 0:
                raw_parsed = parse_fractal(raw_row.get(col, "")) or parsed
                prices.append(float(raw_parsed.get("price", 0.0) or 0.0))
                continue
            raw_parsed = parse_fractal(raw_row.get(col, "")) or parsed
            price = float(raw_parsed.get("price", 0.0) or 0.0)
            raw_distance = (price - base_price) / atr
            candidates.append((abs(raw_distance), source_index, raw_distance, parsed))
            prices.append(price)

        if prices:
            below = sum(price < base_price for price in prices)
            row_features["fractal0_price_rank"] = float(below / max(len(prices) - 1, 1))
            row_features["fractals_above_count"] = int(sum(price > base_price for price in prices))
            row_features["fractals_below_count"] = int(below)
        else:
            row_features["fractals_above_count"] = 0
            row_features["fractals_below_count"] = 0

        candidates.sort(key=lambda item: (item[0], item[1]))
        for slot in range(int(k)):
            prefix = f"nearest_{slot:02d}"
            if slot >= len(candidates):
                _fill_nearest_slot(row_features, prefix, valid=0, geometry_only=geometry_only)
                continue
            _, source_index, raw_distance, parsed = candidates[slot]
            include_updn = (not geometry_only) and (source_index != 0)
            _fill_nearest_slot(
                row_features,
                prefix,
                valid=1,
                source_index=source_index,
                raw_distance_atr=raw_distance,
                parsed=parsed,
                include_updn=include_updn,
                geometry_only=geometry_only,
            )
        out_rows.append(row_features)
    return pd.DataFrame(out_rows, index=frame.index).fillna(0.0)


def _fill_nearest_slot(
    row_features: dict[str, float | int],
    prefix: str,
    *,
    valid: int,
    source_index: int = 0,
    raw_distance_atr: float = 0.0,
    parsed: dict[str, Any] | None = None,
    include_updn: bool = False,
    geometry_only: bool = False,
) -> None:
    parsed = parsed or {}
    row_features[f"{prefix}_valid"] = int(valid)
    row_features[f"{prefix}_source_index"] = int(source_index)
    row_features[f"{prefix}_raw_distance_atr"] = float(raw_distance_atr)
    row_features[f"{prefix}_abs_distance_atr"] = abs(float(raw_distance_atr))
    for field in ("direction", "front", "back", "strong", "break", "reverse", "power", "count", "impulse", "fractal_atr"):
        row_features[f"{prefix}_{field}"] = float(parsed.get(field, 0.0) or 0.0)
    if not geometry_only:
        for field in _UPDN_FIELDS:
            row_features[f"{prefix}_{field}"] = float(parsed.get(field, 0.0) or 0.0) if include_updn else 0.0


def _fractal_index(column: str) -> int:
    try:
        return int(str(column).replace("fractal", "", 1))
    except ValueError:
        return 10**9


def _safe_float(value: object, *, default: float) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def build_feature_contract(fractal_count: int = 100) -> list[dict[str, Any]]:
    """Возвращает manifest live-safe/diagnostic признаков для feature-audit."""
    entries: list[dict[str, Any]] = [
        {
            "name": "time",
            "source_column": "time",
            "source_type": "current_row_meta",
            "available_at": "current_row",
            "live_safe": True,
            "normalization": "none",
            "model_input": False,
        },
        {
            "name": "ATR",
            "source_column": "ATR",
            "source_type": "current_row_meta",
            "available_at": "current_row",
            "live_safe": True,
            "normalization": "none",
            "model_input": True,
        },
    ]

    for idx in range(fractal_count):
        for field in FRACTAL_FIELDS:
            source_column = f"fractal{idx}"
            name = f"fractal{idx}_{field}"
            is_fractal0_updn = idx == 0 and field in _UPDN_FIELDS
            is_old_updn = idx > 0 and field in _UPDN_FIELDS
            is_price = idx == 0 and field == "price"
            model_input = idx > 0 or field in {"direction", "price"}
            if is_fractal0_updn:
                model_input = False
            source_type = "target_only" if is_fractal0_updn else "current_row_fractal"
            available_at = "target_only" if is_fractal0_updn else "current_row"
            if is_old_updn:
                available_at = "historical_fractal_state"
            entries.append(
                {
                    "name": name,
                    "source_column": source_column,
                    "source_type": source_type,
                    "available_at": available_at,
                    "live_safe": True,
                    "normalization": "raw_price_distance_over_raw_atr" if field == "price" and not is_price else "none",
                    "model_input": bool(model_input),
                }
            )

    for name in ("up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48", "fav_*", "adv_*", "trail_*"):
        entries.append(
            {
                "name": name,
                "source_column": name,
                "source_type": "target_only",
                "available_at": "target_only",
                "live_safe": False,
                "normalization": "none",
                "model_input": False,
            }
        )

    for name in ("signal", "predict", "ret_*"):
        entries.append(
            {
                "name": name,
                "source_column": name,
                "source_type": "diagnostic_only",
                "available_at": "diagnostic_only",
                "live_safe": False,
                "normalization": "none",
                "model_input": False,
            }
        )

    return entries


def fit_feature_normalizer(train_features: pd.DataFrame) -> dict[str, Any]:
    """Fit train-only mean/std stats for continuous feature columns."""
    stats: dict[str, Any] = {"method": "zscore_train_frozen", "columns": {}}
    for column in train_features.columns:
        if _normalizer_excluded_column(str(column)):
            continue
        values = pd.to_numeric(train_features[column], errors="coerce").fillna(0.0).astype(float)
        mean = float(values.mean())
        std = float(values.std(ddof=0))
        if std <= 1e-12:
            std = 1.0
        stats["columns"][str(column)] = {"mean": mean, "std": std}
    return stats


def apply_feature_normalizer(features: pd.DataFrame, stats: dict[str, Any]) -> pd.DataFrame:
    """Apply frozen train stats to a feature frame."""
    out = features.copy()
    for column, values in stats.get("columns", {}).items():
        if column not in out.columns:
            continue
        mean = float(values.get("mean", 0.0))
        std = float(values.get("std", 1.0)) or 1.0
        out[column] = (pd.to_numeric(out[column], errors="coerce").fillna(0.0).astype(float) - mean) / std
    return out


def _normalizer_excluded_column(column: str) -> bool:
    return column.endswith("_valid") or column.endswith("_source_index")


def _is_numeric_text(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


def _numeric_or_none(value: object) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _timestamp_seconds(value: pd.Timestamp | None) -> float | None:
    if value is None:
        return None
    return float(value.timestamp())


def _split_fractal_fast(value: object) -> list[str] | None:
    if pd.isna(value) or value == "":
        return None
    parts = str(value).split(":")
    if len(parts) < 7:
        return None
    return parts


def _parts_have_updn(parts: list[str]) -> bool:
    for pos in (11, 12, 13, 14, 15, 16, 17, 18, 19, 20):
        if pos >= len(parts):
            continue
        try:
            if float(parts[pos]) != 0.0:
                return True
        except ValueError:
            continue
    return False
