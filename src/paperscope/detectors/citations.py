"""Citation existence — does each reference actually resolve? LLMs routinely
hallucinate plausible-looking references; a DOI/title that resolves to nothing
is a verdict-grade fact.

axis = data_integrity, output = verdict, distribution = OPEN (uses the public
Crossref / OpenAlex APIs).

NOTE: requires outbound network to api.crossref.org / api.openalex.org. Calls
are gated behind live=True so offline tests stay deterministic, and so the
sandbox's egress allow-list is an explicit deployment concern, not a surprise.
"What the cited work actually says vs. what the paper claims" is a separate,
flag-level check deferred to v2.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import List, Optional

from ..types import Axis, Evidence, Finding, OutputType, Severity

_CROSSREF_DOI = "https://api.crossref.org/works/{doi}"
_OPENALEX_SEARCH = "https://api.openalex.org/works?search={q}&per_page=1"


@dataclass
class Citation:
    raw: str
    doi: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None


def _http_json(url: str, timeout: float = 8.0) -> Optional[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "paperscope/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                return None
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _resolves(c: Citation) -> bool:
    if c.doi:
        return _http_json(_CROSSREF_DOI.format(doi=urllib.parse.quote(c.doi))) is not None
    if c.title:
        data = _http_json(_OPENALEX_SEARCH.format(q=urllib.parse.quote(c.title)))
        return bool(data and data.get("results"))
    return False


def run(citations: List[Citation], live: bool = False) -> List[Finding]:
    findings: List[Finding] = []
    if not live:
        return findings  # offline mode: no-op so tests are deterministic
    for c in citations:
        if _resolves(c):
            continue
        findings.append(
            Finding(
                detector="citations",
                axis=Axis.DATA_INTEGRITY,
                output_type=OutputType.VERDICT,
                severity=Severity.HIGH,
                message=f"citation does not resolve in Crossref/OpenAlex: "
                        f"{c.title or c.doi or c.raw[:60]!r}",
                evidence=Evidence(
                    claim="cited reference cannot be found in any index",
                    reported=c.doi or c.title or c.raw,
                ),
                location=c.location,
            )
        )
    return findings
