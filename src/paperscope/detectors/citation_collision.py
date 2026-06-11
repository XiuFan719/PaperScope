"""Citation name-collision — the same method/baseline name is cited as two
different references (e.g. 'FedDyn [1]' in related work but 'FedDyn [14]' in the
result tables, where [1] and [14] are unrelated papers).

axis = data_integrity, output = verdict, distribution = OPEN, NO network needed.
This is a verifiable inconsistency: one label demonstrably maps to two ref ids.
It catches misattributed baselines and copy-paste citation errors that the
live-resolution check (Crossref/OpenAlex) would miss, because both refs exist.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional

from ..types import Axis, Evidence, Finding, OutputType, Severity


@dataclass
class CitationUsage:
    label: str                      # method/name as written, e.g. "FedDyn"
    ref_id: str                     # bracket key, e.g. "1" or "14"
    location: Optional[str] = None


def run(usages: List[CitationUsage]) -> List[Finding]:
    by_label = defaultdict(set)
    where = defaultdict(set)
    for u in usages:
        by_label[u.label].add(u.ref_id)
        if u.location:
            where[u.label].add(u.location)

    findings: List[Finding] = []
    for label, ids in by_label.items():
        if len(ids) < 2:
            continue
        ids_sorted = sorted(ids, key=lambda x: (len(x), x))
        findings.append(
            Finding(
                detector="citation_collision",
                axis=Axis.DATA_INTEGRITY,
                output_type=OutputType.VERDICT,
                severity=Severity.MEDIUM,
                message=f"'{label}' is cited as both "
                        f"{' and '.join('['+i+']' for i in ids_sorted)} "
                        f"— same name, different references",
                evidence=Evidence(
                    claim="one method label maps to multiple distinct references",
                    reported=f"{label} → {sorted(ids)}",
                    detail={"locations": sorted(where[label])},
                ),
            )
        )
    return findings
