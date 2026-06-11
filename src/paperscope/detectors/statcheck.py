"""statcheck — recompute the p-value from a reported test statistic and df,
flag where the reported p is inconsistent.

axis = data_integrity, output = verdict, distribution = OPEN.
(Evading it means reporting mutually consistent numbers — i.e. honest work —
so publishing the rule gives a fabricator no cheap escape.)

Implements t, F, chi2, r, z. Mirrors the public statcheck method
(Nuijten & Epskamp). Parsing stats out of a PDF is upstream; this takes the
already-extracted ReportedStat records.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from scipy import stats

from ..types import Axis, Evidence, Finding, OutputType, Severity

_GROSS_ALPHA = 0.05  # "gross" inconsistency = recomputed p crosses .05 vs reported


@dataclass
class ReportedStat:
    test: str                       # "t" | "F" | "chi2" | "r" | "z"
    value: float                    # the reported statistic
    df1: Optional[float] = None     # df (t, chi2); numerator df (F); N for r
    df2: Optional[float] = None     # denominator df (F)
    reported_p: float = None        # p as printed in the paper
    tail: int = 2                   # 1 or 2 tailed
    location: Optional[str] = None


def _recompute_p(s: ReportedStat) -> Optional[float]:
    t = s.test.lower()
    v = abs(s.value)
    if t == "t":
        p = stats.t.sf(v, s.df1) * (2 if s.tail == 2 else 1)
    elif t == "f":
        p = stats.f.sf(s.value, s.df1, s.df2)        # F is one-sided by nature
    elif t in ("chi2", "x2", "χ2"):
        p = stats.chi2.sf(s.value, s.df1)
    elif t == "z":
        p = stats.norm.sf(v) * (2 if s.tail == 2 else 1)
    elif t == "r":
        # convert r to t with df = N - 2 (df1 carries N here)
        n = s.df1
        if n is None or n <= 2:
            return None
        tt = v * ((n - 2) ** 0.5) / ((1 - v ** 2) ** 0.5)
        p = stats.t.sf(tt, n - 2) * (2 if s.tail == 2 else 1)
    else:
        return None
    return min(p, 1.0)


def run(stats_in: List[ReportedStat], rel_tol: float = 0.10) -> List[Finding]:
    findings: List[Finding] = []
    for s in stats_in:
        recomputed = _recompute_p(s)
        if recomputed is None or s.reported_p is None:
            continue
        # tolerance is relative — the paper's p is usually rounded
        consistent = abs(recomputed - s.reported_p) <= max(rel_tol * s.reported_p, 0.005)
        if consistent:
            continue
        gross = (recomputed < _GROSS_ALPHA) != (s.reported_p < _GROSS_ALPHA)
        findings.append(
            Finding(
                detector="statcheck",
                axis=Axis.DATA_INTEGRITY,
                output_type=OutputType.VERDICT,
                severity=Severity.HIGH if gross else Severity.MEDIUM,
                message=(
                    f"{s.test}={s.value} (df={s.df1}"
                    f"{','+str(s.df2) if s.df2 else ''}) implies p≈{recomputed:.4f}, "
                    f"but p={s.reported_p} was reported"
                    + (" — crosses the .05 boundary" if gross else "")
                ),
                evidence=Evidence(
                    claim="reported p-value inconsistent with reported test statistic",
                    expected=f"p≈{recomputed:.4f}",
                    reported=f"p={s.reported_p}",
                    detail={"gross": gross},
                ),
                location=s.location,
            )
        )
    return findings
