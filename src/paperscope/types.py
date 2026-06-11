"""Shared types for paperscope.

The single most important design decision lives here: every finding is tagged
with an AXIS and an OUTPUT_TYPE, and these are NEVER collapsed into one score.

  axis        -> 造假轴 (data_integrity) vs AI 辅助轴 (authorship)
  output_type -> verdict (硬判定, 被指控方可独立复核) vs flag (软信号, 仅供人工)

A paper can be 100% AI-written and fully honest; it can be 100% human-written
and fully fabricated. Authorship findings must never, on their own, produce a
fraud accusation.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class Axis(str, Enum):
    DATA_INTEGRITY = "data_integrity"   # 造假轴: 数据本身是不是编的
    AUTHORSHIP = "authorship"           # AI 辅助轴: 是不是 AI 写/画的 (≠ 造假)


class OutputType(str, Enum):
    VERDICT = "verdict"   # 硬判定: 可复核的事实 (e.g. 这两个数学上不可能同时成立)
    FLAG = "flag"         # 软信号: 路由到人工复核, 绝不单独定罪


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Evidence:
    """The falsifiable facts behind a finding.

    For a VERDICT this must be concrete enough that the accused author can
    independently re-derive it without trusting our code. That auditability is
    *why* verdict-grade detectors are the ones we open-source.
    """
    claim: str                              # what we assert is wrong
    expected: Optional[str] = None          # what a consistent value would be
    reported: Optional[str] = None          # what the paper actually reported
    detail: dict = field(default_factory=dict)


@dataclass
class Finding:
    detector: str
    axis: Axis
    output_type: OutputType
    severity: Severity
    message: str
    evidence: Optional[Evidence] = None
    location: Optional[str] = None          # page / section / table id, when known

    def as_dict(self) -> dict:
        d = asdict(self)
        d["axis"] = self.axis.value
        d["output_type"] = self.output_type.value
        d["severity"] = self.severity.value
        return d
