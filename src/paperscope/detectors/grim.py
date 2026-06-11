"""GRIM / GRIMMER — is a reported mean (or SD) even arithmetically possible
given the sample size and an integer-valued response scale?

axis = data_integrity, output = verdict, distribution = OPEN.

GRIM (Brown & Heathers): for integer items, the mean must be a multiple of
1/(N*items). A reported mean that no integer sum can round to is impossible.
GRIMMER (Anaya) extends this to variance/SD — left as a stub for v1 because
the search over feasible sums is more involved.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..types import Axis, Evidence, Finding, OutputType, Severity


@dataclass
class ReportedMean:
    mean: float
    n: int
    items: int = 1                  # number of summed integer items per subject
    decimals: Optional[int] = None  # printed precision; inferred if None
    location: Optional[str] = None


def _decimals_of(x: float) -> int:
    s = repr(float(x))
    return len(s.split(".")[1]) if "." in s else 0


def _grim_consistent(mean: float, n: int, items: int, decimals: int) -> bool:
    grid = n * items
    nearest_sum = round(mean * grid)
    achievable = nearest_sum / grid
    return round(achievable, decimals) == round(mean, decimals)


def run(means: List[ReportedMean]) -> List[Finding]:
    findings: List[Finding] = []
    for m in means:
        if m.n <= 0:
            continue
        decimals = m.decimals if m.decimals is not None else _decimals_of(m.mean)
        if decimals == 0:
            continue  # GRIM has no power on integer-reported means
        if _grim_consistent(m.mean, m.n, m.items, decimals):
            continue
        grid = m.n * m.items
        nearest = round(m.mean * grid) / grid
        findings.append(
            Finding(
                detector="grim",
                axis=Axis.DATA_INTEGRITY,
                output_type=OutputType.VERDICT,
                severity=Severity.HIGH,
                message=(
                    f"mean={m.mean} is impossible for N={m.n}"
                    f"{' × '+str(m.items)+' items' if m.items != 1 else ''}: "
                    f"no integer total rounds to it"
                ),
                evidence=Evidence(
                    claim="reported mean not achievable by any integer sum at this N",
                    expected=f"nearest achievable ≈ {round(nearest, decimals)}",
                    reported=f"mean = {m.mean}",
                    detail={"n": m.n, "items": m.items, "decimals": decimals},
                ),
                location=m.location,
            )
        )
    return findings


def run_grimmer(*args, **kwargs) -> List[Finding]:  # noqa: D401
    """GRIMMER (variance/SD feasibility). Deferred to v2."""
    raise NotImplementedError("GRIMMER scheduled for v2 — see module list")
