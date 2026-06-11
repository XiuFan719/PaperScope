"""citation_title_match — does the method name cited as "Name [N]" actually
appear in reference [N]'s title? Pure OFFLINE (uses the paper's own ref list);
no network, no RAG.

Catches mis-numbered citations (e.g. 'LoRA [13]' where [13] is GLIP). Unlike a
reverse-collision check it compares against the actual title, so it does NOT
false-flag one paper legitimately cited under two contribution names
(e.g. a ref that is both 'PlugIR' and 'BRI').

axis = data_integrity, output = verdict (the ref list makes it re-derivable).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from ..types import Axis, Evidence, Finding, OutputType, Severity

_STOP = {"the", "and", "for", "via", "with", "from", "based", "using", "model",
         "models", "learning", "networks", "network", "neural"}


def _tokens(s: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9]+", s.lower()) if len(t) >= 3 and t not in _STOP]


def _acronym_matches(label: str, title: str) -> bool:
    letters = re.sub(r"[^a-z]", "", label.lower())
    if len(letters) < 2:
        return False
    initials = "".join(w[0] for w in re.findall(r"[A-Za-z]+", title)).lower()
    return letters in initials


@dataclass
class CitationRef:
    label: str                  # method/work name as written, e.g. "LoRA"
    ref_id: str                 # the bracket number, e.g. "13"
    ref_title: str              # title of reference [ref_id] in the bibliography
    location: Optional[str] = None


def run(refs: List[CitationRef]) -> List[Finding]:
    findings: List[Finding] = []
    for r in refs:
        title = r.ref_title.lower()
        toks = _tokens(r.label)
        token_hit = any(t in title for t in toks)
        if token_hit or _acronym_matches(r.label, r.ref_title):
            continue
        findings.append(Finding(
            detector="citation_title_match", axis=Axis.DATA_INTEGRITY,
            output_type=OutputType.VERDICT, severity=Severity.MEDIUM,
            message=f"'{r.label}' is cited as [{r.ref_id}], but reference "
                    f"[{r.ref_id}] is titled \"{r.ref_title}\" — the name does "
                    f"not match the referenced work",
            evidence=Evidence(claim="citation label does not match the referenced title",
                              reported=f"{r.label} [{r.ref_id}]",
                              expected=f"[{r.ref_id}] = {r.ref_title}"),
            location=r.location))
    return findings
