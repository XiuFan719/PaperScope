"""LLM scaffolding residue — leftover chatbot strings and unfilled placeholders
that have genuinely appeared in published papers.

axis = AUTHORSHIP (NOT data_integrity), output = FLAG, distribution = OPEN.

This is the ONLY authorship-axis detector in v1, and it is deliberately
flag-only: it answers "was an LLM in the loop?", which is NOT the same question
as "is this fraudulent?". It must never, on its own, drive a fraud verdict.
Open-sourcing it costs nothing — hiding it would only teach people to delete
the obvious strings, which is fine.
"""
from __future__ import annotations

import re
from typing import List

from ..types import Axis, Evidence, Finding, OutputType, Severity

# (pattern, human-readable label, severity)
_PATTERNS = [
    (r"as an ai language model", "chatbot self-reference", Severity.HIGH),
    (r"as a large language model", "chatbot self-reference", Severity.HIGH),
    (r"i'?m sorry,? but i (?:can'?t|cannot)", "refusal boilerplate", Severity.HIGH),
    (r"i (?:can'?t|cannot) (?:provide|assist|help with)", "refusal boilerplate", Severity.MEDIUM),
    (r"certainly[!,]? here(?:'s| is) (?:the|a|your)", "assistant preamble", Severity.MEDIUM),
    (r"here is the (?:revised|rewritten|requested) [a-z ]+ you requested", "assistant preamble", Severity.MEDIUM),
    (r"regenerate response", "UI artifact", Severity.HIGH),
    (r"knowledge cutoff", "model self-reference", Severity.MEDIUM),
    (r"\[insert [^\]]+\]", "unfilled placeholder", Severity.HIGH),
    (r"\[citation needed\]", "unfilled placeholder", Severity.MEDIUM),
    (r"\[(?:author|year|reference)s?\]", "unfilled placeholder", Severity.MEDIUM),
    (r"\bTODO\b|\bFIXME\b|\bXXX\b", "draft marker", Severity.LOW),
]
_COMPILED = [(re.compile(p, re.IGNORECASE), label, sev) for p, label, sev in _PATTERNS]


def run(text: str) -> List[Finding]:
    findings: List[Finding] = []
    for rx, label, sev in _COMPILED:
        m = rx.search(text)
        if not m:
            continue
        snippet = m.group(0)
        findings.append(
            Finding(
                detector="llm_residue",
                axis=Axis.AUTHORSHIP,
                output_type=OutputType.FLAG,
                severity=sev,
                message=f"{label} present: {snippet!r} "
                        f"(AI-assisted authorship signal — NOT evidence of fraud)",
                evidence=Evidence(claim="leftover LLM/template string", reported=snippet),
            )
        )
    return findings
