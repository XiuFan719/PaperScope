"""numeric_consistency — global numeric-claim consistency across the WHOLE paper.

Collect (metric, subject) -> value triples from everywhere and flag any single
quantity reported with conflicting values, plus values copy-pasted across many
distinct quantities.

Calibration (the important part): an ISOLATED mismatch is consistent with a
TYPO, not fraud — so one conflict is only a low flag. But a PATTERN is
qualitatively different, so severity ESCALATES with the count:

    1 conflict   -> flag / low      ("likely a typo, not necessarily fraud")
    2 conflicts  -> flag / medium    (sloppy — worth review)
    >= 3          -> verdict / medium (systematic inconsistency across the paper)

Each conflicting quantity is itself a re-derivable fact (verdict-grade once the
pattern threshold is crossed); the per-conflict message states WHY it was
escalated, so the human can see it's a pattern rather than a slip.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional

from ..types import Axis, Evidence, Finding, OutputType, Severity


@dataclass
class NumericClaim:
    metric: str                     # e.g. "SDS", "R@1@R5", "model count"
    subject: str                    # e.g. "Qwen2.5-VL-7B baseline", "paper"
    value: float
    location: Optional[str] = None


def _severity_for(n_conflicts: int):
    if n_conflicts >= 3:
        return OutputType.VERDICT, Severity.MEDIUM
    if n_conflicts == 2:
        return OutputType.FLAG, Severity.MEDIUM
    return OutputType.FLAG, Severity.LOW


def run(claims: List[NumericClaim], tol: float = 0.02,
        repeat_threshold: int = 4) -> List[Finding]:
    by_key = defaultdict(list)                  # (metric, subject) -> [(value, loc)]
    for c in claims:
        by_key[(c.metric, c.subject)].append((c.value, c.location))

    conflicts = [(k, v) for k, v in by_key.items()
                 if max(x for x, _ in v) - min(x for x, _ in v) > tol]

    findings: List[Finding] = []
    otype, sev = _severity_for(len(conflicts))
    if len(conflicts) >= 3:
        note = (f" [part of a {len(conflicts)}-quantity inconsistency pattern — "
                f"systematic, not an isolated typo]")
    elif len(conflicts) == 1:
        note = " [single inconsistency — consistent with a typo, not necessarily fraud]"
    else:
        note = ""

    for (metric, subject), vals in conflicts:
        distinct = sorted({round(v, 4) for v, _ in vals})
        locs = [l for _, l in vals if l]
        findings.append(Finding(
            detector="numeric_consistency",
            axis=Axis.DATA_INTEGRITY,
            output_type=otype, severity=sev,
            message=f"'{metric}' for '{subject}' is reported as {distinct} in "
                    f"different places{note}",
            evidence=Evidence(
                claim="same quantity reported with different values",
                reported=str(distinct), detail={"locations": locs}),
            location="; ".join(locs) if locs else None,
        ))

    # copy-paste check: one exact value standing in for many distinct quantities.
    # Conservative (>= repeat_threshold distinct keys); low severity, FP-prone, so
    # it only nudges the score and is always a flag for human eyes.
    val_to_keys = defaultdict(set)
    for c in claims:
        val_to_keys[round(c.value, 4)].add((c.metric, c.subject))
    for val, keys in sorted(val_to_keys.items()):
        if len(keys) >= repeat_threshold:
            findings.append(Finding(
                detector="numeric_consistency",
                axis=Axis.DATA_INTEGRITY,
                output_type=OutputType.FLAG, severity=Severity.LOW,
                message=f"value {val} is reported for {len(keys)} distinct "
                        f"quantities (possible copy-paste — verify)",
                evidence=Evidence(
                    claim="one value shared across many distinct quantities",
                    reported=f"{val} across {len(keys)} keys"),
            ))
    return findings
