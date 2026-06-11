"""Internal cross-reference integrity — "as shown in Figure 5" when there is no
Figure 5, references to non-existent tables/equations/sections. AI-assembled
papers frequently leave these dangling.

axis = data_integrity, output = verdict, distribution = OPEN.
v1 works on plain text via regex; a later version should consume the parsed
document structure for fewer false positives.
"""
from __future__ import annotations

import re
from typing import Dict, List, Set

from ..types import Axis, Evidence, Finding, OutputType, Severity

# in-text references, e.g. "Figure 5", "Fig. 3", "Table 2", "Eq. (4)", "Section 3.1"
_REF = re.compile(
    r"\b(Fig(?:ure|\.)?|Table|Tab\.|Eq(?:uation|\.)?|Section|Sec\.)\s*\(?\s*"
    r"(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
# declared anchors, e.g. a caption beginning "Figure 5:" / "Table 2." / "Eq. (4)"
_ANCHOR = re.compile(
    r"(?m)^\s*(Fig(?:ure|\.)?|Table|Tab\.|Eq(?:uation|\.)?)\s*\(?\s*(\d+(?:\.\d+)?)\)?\s*[:.]",
    re.IGNORECASE,
)

# refs explicitly pointing at the appendix/supplement — can't be validated
# against the main text alone, so they must NOT be flagged as dangling.
_APPENDIX_REF = re.compile(
    r"(?:appendix|supplement(?:ary|al)?|supp\.)\s+"
    r"(Fig(?:ure|\.)?|Table|Tab\.|Eq(?:uation|\.)?)\s*\(?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)

# kinds we do NOT verdict on: sections (rarely captioned) and equations
# (declared as bare right-aligned "(N)" tags, not as "Equation N:" captions —
# validating them needs structure-aware parsing, deferred to v2).
_SKIP_KINDS = {"section", "equation"}

_KIND = {"fig": "figure", "tab": "table", "eq": "equation", "sec": "section"}


def _kind(token: str) -> str:
    t = token.lower().rstrip(".")
    for pre, name in _KIND.items():
        if t.startswith(pre):
            return name
    return t


def run(text: str) -> List[Finding]:
    referenced: Set[tuple] = {(_kind(m.group(1)), m.group(2)) for m in _REF.finditer(text)}
    declared: Set[tuple] = {(_kind(m.group(1)), m.group(2)) for m in _ANCHOR.finditer(text)}
    appendix: Set[tuple] = {(_kind(m.group(1)), m.group(2)) for m in _APPENDIX_REF.finditer(text)}

    findings: List[Finding] = []
    for kind, num in sorted(referenced):
        # skip kinds we can't reliably validate, and anything pointing at the
        # appendix/supplement (not present in the main text we were given)
        if kind in _SKIP_KINDS or (kind, num) in appendix:
            continue
        if (kind, num) not in declared:
            findings.append(
                Finding(
                    detector="internal_refs",
                    axis=Axis.DATA_INTEGRITY,
                    output_type=OutputType.VERDICT,
                    severity=Severity.MEDIUM,
                    message=f"text references {kind} {num}, but no such "
                            f"{kind} is declared in the document",
                    evidence=Evidence(
                        claim="dangling internal cross-reference",
                        reported=f"{kind} {num} referenced",
                        expected=f"a declared {kind} {num}",
                    ),
                )
            )
    return findings
