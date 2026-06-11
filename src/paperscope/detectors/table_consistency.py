"""Table consistency — does the paper's own arithmetic check out?

  * a row/column labelled total/sum equals the sum of its parts
  * a set of percentages adds to ~100
  * a number stated in the prose matches the same cell in the table

axis = data_integrity, output = verdict, distribution = OPEN. (This is the
TerrOcc-style catch.) Upstream PDF/table extraction is a separate concern;
this operates on already-parsed structures.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..types import Axis, Evidence, Finding, OutputType, Severity


@dataclass
class Table:
    table_id: str
    # column name -> list of numeric cell values (parts only, excluding the total)
    columns: Dict[str, List[float]]
    # column name -> the reported total for that column, if the table states one
    reported_totals: Dict[str, float] = field(default_factory=dict)


@dataclass
class TextNumberClaim:
    """A number asserted in prose that should match a table cell."""
    value: float
    table_id: str
    column: str
    row_index: int
    location: Optional[str] = None


def _check_totals(t: Table, abs_tol: float) -> List[Finding]:
    out = []
    for col, total in t.reported_totals.items():
        parts = t.columns.get(col, [])
        s = sum(parts)
        if abs(s - total) > abs_tol:
            out.append(
                Finding(
                    detector="table_consistency",
                    axis=Axis.DATA_INTEGRITY,
                    output_type=OutputType.VERDICT,
                    severity=Severity.HIGH,
                    message=f"{t.table_id} column '{col}': parts sum to {s}, "
                            f"but total {total} is reported",
                    evidence=Evidence(
                        claim="column total does not equal the sum of its parts",
                        expected=str(s),
                        reported=str(total),
                    ),
                    location=t.table_id,
                )
            )
    return out


def _check_percentages(t: Table, label_hint: str, tol: float) -> List[Finding]:
    out = []
    for col, vals in t.columns.items():
        if label_hint.lower() in col.lower() and vals:
            s = sum(vals)
            if abs(s - 100.0) > tol:
                out.append(
                    Finding(
                        detector="table_consistency",
                        axis=Axis.DATA_INTEGRITY,
                        output_type=OutputType.VERDICT,
                        severity=Severity.MEDIUM,
                        message=f"{t.table_id} column '{col}': percentages sum to "
                                f"{s:.2f}, not 100",
                        evidence=Evidence(
                            claim="percentage column does not sum to 100",
                            expected="100", reported=f"{s:.2f}",
                        ),
                        location=t.table_id,
                    )
                )
    return out


def run(
    tables: List[Table],
    text_claims: Optional[List[TextNumberClaim]] = None,
    abs_tol: float = 1e-6,
    pct_tol: float = 0.5,
    pct_label_hint: str = "%",
) -> List[Finding]:
    findings: List[Finding] = []
    by_id = {t.table_id: t for t in tables}
    for t in tables:
        findings += _check_totals(t, abs_tol)
        findings += _check_percentages(t, pct_label_hint, pct_tol)

    for c in text_claims or []:
        t = by_id.get(c.table_id)
        if not t or c.column not in t.columns:
            continue
        col = t.columns[c.column]
        if c.row_index >= len(col):
            continue
        cell = col[c.row_index]
        if abs(cell - c.value) > abs_tol:
            findings.append(
                Finding(
                    detector="table_consistency",
                    axis=Axis.DATA_INTEGRITY,
                    output_type=OutputType.VERDICT,
                    severity=Severity.MEDIUM,
                    message=f"prose states {c.value} but {c.table_id}[{c.column}]"
                            f"[{c.row_index}] = {cell}",
                    evidence=Evidence(
                        claim="number in text does not match the table cell",
                        expected=str(cell), reported=str(c.value),
                    ),
                    location=c.location or c.table_id,
                )
            )
    return findings
