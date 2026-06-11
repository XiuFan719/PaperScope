"""Two-axis report with itemized 0-100 indices.

The headline number is the INTEGRITY index ("造假疑点"). The FORMAT index
(AI-assist / template residue) is reported beside it but is computed from a
disjoint set of findings and is never folded in.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from . import scoring
from .types import Finding


@dataclass
class Report:
    findings: List[Finding]

    @property
    def integrity(self) -> scoring.AxisScore:
        return scoring.integrity_score(self.findings)

    @property
    def format(self) -> scoring.AxisScore:
        return scoring.format_score(self.findings)

    def as_dict(self) -> dict:
        ig, fm = self.integrity, self.format
        return {
            "integrity_index": ig.index,
            "integrity_label": ig.label,
            "integrity_breakdown": ig.items,
            "format_index": fm.index,
            "format_label": fm.label,
            "format_breakdown": fm.items,
            "note": "indices are separate; format never feeds integrity",
        }

    def render(self) -> str:
        ig, fm = self.integrity, self.format
        lines = [
            "=== paperscope report ===",
            "",
            f"数据完整性疑点指数 (integrity): {ig.index}%  — {ig.label}",
        ]
        lines += _render_breakdown(ig)
        lines += [
            "",
            f"格式/AI 辅助痕迹 (format): {fm.index}%  — {fm.label}",
            "  (独立计分，不计入上面的疑点指数)",
        ]
        lines += _render_breakdown(fm)
        lines += [
            "",
            "note: integrity index is a heuristic severity score (every point is "
            "itemized above), not a calibrated probability of fraud.",
        ]
        return "\n".join(lines)


def _render_breakdown(ax: scoring.AxisScore) -> List[str]:
    if not ax.items:
        return ["  命中: (none)"]
    out = ["  命中:"]
    for detector, otype, sev, pts, msg in ax.items:
        out.append(f"   +{pts:>2}  [{otype}/{sev}] {detector}: {msg}")
    out.append(f"  小计 {ax.total_points} 分 → {ax.index}%")
    return out
