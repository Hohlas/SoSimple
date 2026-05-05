from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable


class LiveSafeStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FeatureTrace:
    name: str
    role: str = ""
    source_path: str = ""
    producer: str = ""
    consumer: str = ""
    transformation: str = ""
    availability_time: str = "unknown"
    live_safe_status: LiveSafeStatus = LiveSafeStatus.UNKNOWN
    evidence: str = ""
    notes: str = ""


@dataclass(frozen=True)
class AuditVerdict:
    verdict: str
    reason: str
    failing_features: list[str] = field(default_factory=list)
    unknown_features: list[str] = field(default_factory=list)


def verdict_from_features(features: Iterable[FeatureTrace]) -> AuditVerdict:
    feature_list = list(features)
    failing = [feature.name for feature in feature_list if feature.live_safe_status == LiveSafeStatus.FAIL]
    unknown = [feature.name for feature in feature_list if feature.live_safe_status == LiveSafeStatus.UNKNOWN]

    if failing:
        return AuditVerdict(
            verdict="FAIL",
            reason="Feature contract includes future-derived or otherwise invalid inputs.",
            failing_features=failing,
            unknown_features=unknown,
        )
    if unknown:
        return AuditVerdict(
            verdict="UNKNOWN",
            reason="Feature contract has unresolved source or timing evidence.",
            unknown_features=unknown,
        )
    return AuditVerdict(verdict="PASS", reason="All audited features are live-safe.")


def classify_feature_name(name: str) -> FeatureTrace:
    producer = "unknown"
    transformation = "direct"
    availability_time = "unknown"
    status = LiveSafeStatus.UNKNOWN
    evidence = "docs/ML/ml_leakage_preflight_checklist.md"
    notes = ""
    role = "model_input"

    if name == "predict":
        producer = "processing/label_signals.py"
        transformation = "future-derived label/predict pipeline"
        availability_time = "future_bars"
        status = LiveSafeStatus.FAIL
        notes = "Training predict is derived from future outcome and is not equivalent to live predict=0."
    elif name.startswith("ret_") and name.endswith("_dir_atr"):
        producer = "processing/label_signals.py"
        transformation = "forward return over future hold bars"
        availability_time = "future_bars"
        status = LiveSafeStatus.FAIL
        notes = "Return target is known only after future bars."
    elif name.startswith("fav_") or name.startswith("adv_"):
        producer = "processing/label_signals.py"
        transformation = "forward favorable/adverse excursion over future hold bars"
        availability_time = "future_bars"
        status = LiveSafeStatus.FAIL
        notes = "Path outcome is known only after future bars."
    elif name == "ret_dir_atr_lag1":
        producer = "processing/label_signals.py:add_entry_path_frequency_features"
        transformation = "ret_6_dir_atr.shift(1).fillna(0.0)"
        availability_time = "unknown"
        status = LiveSafeStatus.UNKNOWN
        notes = "Lag does not prove safety because source ret_6_dir_atr is future-derived for its own row."
    elif name in {"session_hour", "weekday", "ATR"}:
        producer = "current row"
        transformation = "current bar metadata/raw ATR"
        availability_time = "current_bar"
        status = LiveSafeStatus.PASS
        notes = "Available from current row if training and online contracts use the same preprocessing."
    elif name in {"range_atr_6", "body_atr_3", "vol_regime_24"}:
        producer = "processing/label_signals.py:add_entry_path_frequency_features"
        transformation = "past rolling/lagged OHLC or ATR feature"
        availability_time = "past_only_history"
        status = LiveSafeStatus.PASS
        notes = "Allowed if source OHLC rolling columns are built without future bars."
    elif name.startswith("row_"):
        producer = "ML/entry_path_feature_bank.py or lib_PIC feature bank"
        transformation = "aggregated parsed fractal window statistic"
        availability_time = "past_only_history"
        status = LiveSafeStatus.PASS
        notes = "Window feature derived from already exported fractal state."
    elif name.startswith("fractal"):
        producer = "ML/data_loader.py:parse_fractals_to_3d"
        transformation = "parsed Nero.csv fractal field"
        availability_time = "unknown"
        status = LiveSafeStatus.UNKNOWN
        notes = "Fractal fields need source/timing trace from lib_PIC before final PASS."

    return FeatureTrace(
        name=name,
        role=role,
        source_path=producer,
        producer=producer,
        consumer="ML model input",
        transformation=transformation,
        availability_time=availability_time,
        live_safe_status=status,
        evidence=evidence,
        notes=notes,
    )
