"""v1 detectors. Each module exposes run(...) -> list[Finding].

Open-source / verdict-grade (data-integrity axis):
    statistical_anomaly,
    statcheck, grim, table_consistency, duplicate_blocks,
    internal_refs, citations
Open-source / flag-only (authorship axis):
    llm_residue

Deferred to v2+ (see module list): grimmer, digit/Benford, too-perfect,
tortured phrases, AI-vocab, punctuation, AI-figure & data-figure forensics.
"""
from . import (  # noqa: F401
    citation_collision,
    citation_title_match,
    citations,
    duplicate_blocks,
    grim,
    internal_refs,
    llm_residue,
    numeric_consistency,
    statcheck,
    table_consistency,
    template_residue,
)
