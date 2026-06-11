"""Duplicate value blocks — identical rows/blocks that should not be identical
(a common artefact of copy-pasted fabricated spreadsheets).

axis = data_integrity, output = verdict, distribution = OPEN.
"""
from __future__ import annotations

from typing import List, Optional, Sequence

from ..types import Axis, Evidence, Finding, OutputType, Severity

Row = Sequence[float]


def run(
    rows: List[Row],
    min_block: int = 2,
    table_id: Optional[str] = None,
) -> List[Finding]:
    """Find runs of >= min_block consecutive identical rows, and non-adjacent
    exact duplicate rows. Real numeric data almost never repeats whole rows."""
    findings: List[Finding] = []
    keyed = [tuple(round(x, 10) for x in r) for r in rows]

    # consecutive identical runs
    i = 0
    while i < len(keyed):
        j = i + 1
        while j < len(keyed) and keyed[j] == keyed[i]:
            j += 1
        run_len = j - i
        if run_len >= min_block:
            findings.append(
                Finding(
                    detector="duplicate_blocks",
                    axis=Axis.DATA_INTEGRITY,
                    output_type=OutputType.VERDICT,
                    severity=Severity.MEDIUM,
                    message=f"rows {i}–{j-1} are identical ({run_len} consecutive)",
                    evidence=Evidence(
                        claim="consecutive table rows are exact duplicates",
                        reported=str(list(keyed[i])),
                        detail={"start": i, "end": j - 1, "count": run_len},
                    ),
                    location=table_id,
                )
            )
        i = j

    # non-adjacent exact duplicates (only flag values that look like real data,
    # i.e. with a fractional part, to avoid noise on small integer cells)
    seen = {}
    for idx, k in enumerate(keyed):
        nontrivial = any(abs(x - round(x)) > 1e-9 for x in k)
        if nontrivial and k in seen:
            findings.append(
                Finding(
                    detector="duplicate_blocks",
                    axis=Axis.DATA_INTEGRITY,
                    output_type=OutputType.FLAG,
                    severity=Severity.LOW,
                    message=f"row {idx} duplicates row {seen[k]} exactly",
                    evidence=Evidence(
                        claim="non-adjacent identical data rows",
                        reported=str(list(k)),
                        detail={"rows": [seen[k], idx]},
                    ),
                    location=table_id,
                )
            )
        seen.setdefault(k, idx)
    return findings
