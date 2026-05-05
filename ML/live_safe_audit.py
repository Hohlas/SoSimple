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
