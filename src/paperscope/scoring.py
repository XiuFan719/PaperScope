"""Scoring: turn findings into two SEPARATE 0-100 indices with an itemized
breakdown.

  * integrity index  — the "造假疑点" number. Fed ONLY by data_integrity findings.
  * format index     — AI-assist / template residue / formatting. Fed ONLY by
                       authorship findings. NEVER added into the integrity index.

The integrity index is a transparent severity/triage score, not a calibrated
probability of fraud — every point is itemized so a human can audit and reweight.
Saturation (1 - e^-pts/K) means findings accumulate but no single one maxes it.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

from .types import Axis, Finding, OutputType, Severity

# points per (output_type, severity): verdicts (hard, auditable) >> flags (soft)
_PTS = {
    (OutputType.VERDICT, Severity.HIGH): 40,
    (OutputType.VERDICT, Severity.MEDIUM): 20,
    (OutputType.VERDICT, Severity.LOW): 10,
    (OutputType.VERDICT, Severity.INFO): 4,
    (OutputType.FLAG, Severity.HIGH): 12,
    (OutputType.FLAG, Severity.MEDIUM): 6,
    (OutputType.FLAG, Severity.LOW): 3,
    (OutputType.FLAG, Severity.INFO): 1,
}
K_INTEGRITY = 50.0
K_FORMAT = 40.0


def points(f: Finding) -> int:
    return _PTS.get((f.output_type, f.severity), 0)


def _index(pts: float, k: float) -> int:
    return round(100 * (1 - math.exp(-pts / k)))


@dataclass
class AxisScore:
    index: int                 # 0-100
    total_points: int
    label: str
    items: List[tuple]         # (detector, output_type, severity, points, message)


def _integrity_label(idx: int) -> str:
    if idx < 15:
        return "clean — no data-integrity concerns"
    if idx < 40:
        return "minor — worth a glance"
    if idx < 65:
        return "moderate — needs human review"
    if idx < 85:
        return "high — clear data-integrity concerns"
    return "critical"


def _format_label(idx: int) -> str:
    if idx < 15:
        return "little/no AI-assist or template residue"
    if idx < 50:
        return "AI-assist / template residue present (formatting only — NOT fraud)"
    return "heavily templated/AI-assisted draft (formatting only — NOT fraud)"


def _score_axis(findings: List[Finding], k: float, label_fn) -> AxisScore:
    items = sorted(
        ((f.detector, f.output_type.value, f.severity.value, points(f), f.message)
         for f in findings),
        key=lambda t: -t[3],
    )
    total = sum(i[3] for i in items)
    idx = _index(total, k)
    return AxisScore(index=idx, total_points=total, label=label_fn(idx), items=items)


def integrity_score(findings: List[Finding]) -> AxisScore:
    fs = [f for f in findings if f.axis == Axis.DATA_INTEGRITY]
    return _score_axis(fs, K_INTEGRITY, _integrity_label)


def format_score(findings: List[Finding]) -> AxisScore:
    fs = [f for f in findings if f.axis == Axis.AUTHORSHIP]
    return _score_axis(fs, K_FORMAT, _format_label)
