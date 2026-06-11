"""statistical_anomaly — domain-general 'lazy fabrication' tells on numeric
columns, the part of the Geng-Tongxue methodology that survives outside
biomedical NHST (so it works on ML accuracy tables where statcheck/GRIM idle).

All findings are FLAG-level (heuristic, false-positive-prone) and feed the
integrity axis at low weight; thresholds come from rules.yaml so they stay
tunable/private. Nothing here ever produces a fraud VERDICT on its own.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import List, Optional

from ..config import load_rules
from ..types import Axis, Evidence, Finding, OutputType, Severity


@dataclass
class NumberColumn:
    name: str                       # e.g. "Table 2 GQA column"
    values: List[float]
    location: Optional[str] = None


def _decimals(v: float) -> int:
    s = repr(float(v))
    return len(s.split(".")[1]) if "." in s and not s.endswith(".0") else 0


def _last_digit(v: float) -> Optional[int]:
    d = _decimals(v)
    return int(round(v * 10 ** d)) % 10 if d else None


def run(columns: List[NumberColumn], cfg: dict | None = None) -> List[Finding]:
    c = (cfg or load_rules())["statistical_anomaly"]
    findings: List[Finding] = []

    def flag(sev, msg, ev, loc):
        findings.append(Finding(detector="statistical_anomaly",
                                axis=Axis.DATA_INTEGRITY, output_type=OutputType.FLAG,
                                severity=sev, message=msg, evidence=ev, location=loc))

    pooled_digits: List[int] = []
    for col in columns:
        vals = col.values
        # 1. near-perfect arithmetic progression (too regular to be measured)
        if len(vals) >= c["constant_diff_min_len"]:
            diffs = {round(vals[i + 1] - vals[i], 6) for i in range(len(vals) - 1)}
            if len(diffs) == 1 and next(iter(diffs)) != 0:
                step = next(iter(diffs))
                flag(Severity.MEDIUM,
                     f"column '{col.name}' is an exact arithmetic progression "
                     f"(constant step {step}) — verify it is measured, not generated",
                     Evidence(claim="suspiciously regular sequence", reported=str(vals)),
                     col.location)
        # 3. precision outlier within the column
        decs = [_decimals(v) for v in vals]
        if decs:
            base = sorted(decs)[len(decs) // 2]  # median precision
            for v, d in zip(vals, decs):
                if d - base >= c["precision_extra_places"]:
                    flag(Severity.LOW,
                         f"value {v} in '{col.name}' is reported to far more "
                         f"decimals ({d}) than its column (~{base}) — verify",
                         Evidence(claim="precision inconsistent with column", reported=str(v)),
                         col.location)
                    break
        pooled_digits += [d for d in (_last_digit(v) for v in vals) if d is not None]

    # 2. terminal-digit uniformity across all pooled decimals
    if len(pooled_digits) >= c["terminal_digit_min_sample"]:
        freq = Counter(pooled_digits)
        digit, count = freq.most_common(1)[0]
        share = count / len(pooled_digits)
        if share > c["terminal_digit_max_share"]:
            flag(Severity.MEDIUM,
                 f"last decimal digit '{digit}' covers {share:.0%} of "
                 f"{len(pooled_digits)} values (expected ~10%) — non-random "
                 f"terminal digits can indicate hand-entered/fabricated numbers",
                 Evidence(claim="terminal-digit distribution far from uniform",
                          reported=f"digit {digit}: {count}/{len(pooled_digits)}"),
                 None)
    return findings
