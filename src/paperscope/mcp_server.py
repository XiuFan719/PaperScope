"""MCP server — the client-agnostic exposure layer.

Every tool here is a THIN wrapper that converts JSON-ish input into the core
library's typed records, calls the detector, and serialises the Findings. No
detection logic lives in this file — the library is the single source of truth,
so the MCP server and any future skill/web frontend can never drift apart.

Run:  python -m paperscope.mcp_server   (requires the `mcp` package)
"""
from __future__ import annotations

from typing import List

from .detectors import (
    citation_collision,
    citation_title_match,
    citations,
    duplicate_blocks,
    grim,
    internal_refs,
    llm_residue,
    numeric_consistency,
    statistical_anomaly,
    statcheck,
    table_consistency,
    template_residue,
)
from .report import Report
from .types import Finding

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # keep the library importable without the MCP dependency
    FastMCP = None


def _dump(findings: List[Finding]) -> List[dict]:
    return [f.as_dict() for f in findings]


def build_server():
    if FastMCP is None:
        raise ImportError("install the `mcp` package to run the server")
    mcp = FastMCP("paperscope")

    @mcp.tool()
    def check_statcheck(stats: list[dict]) -> list[dict]:
        """Recompute p-values from reported test statistics; flag inconsistencies.
        Each item: {test, value, df1, df2?, reported_p, tail?, location?}."""
        return _dump(statcheck.run([statcheck.ReportedStat(**s) for s in stats]))

    @mcp.tool()
    def check_grim(means: list[dict]) -> list[dict]:
        """GRIM: is each reported mean arithmetically possible at its N?
        Each item: {mean, n, items?, decimals?, location?}."""
        return _dump(grim.run([grim.ReportedMean(**m) for m in means]))

    @mcp.tool()
    def check_table_consistency(tables: list[dict], text_claims: list[dict] | None = None) -> list[dict]:
        """Column totals, percentages summing to 100, and prose-vs-cell matches."""
        ts = [table_consistency.Table(**t) for t in tables]
        cs = [table_consistency.TextNumberClaim(**c) for c in (text_claims or [])]
        return _dump(table_consistency.run(ts, cs))

    @mcp.tool()
    def check_duplicate_blocks(rows: list[list[float]], table_id: str | None = None) -> list[dict]:
        """Identical row blocks / non-adjacent duplicate data rows."""
        return _dump(duplicate_blocks.run(rows, table_id=table_id))

    @mcp.tool()
    def check_internal_refs(text: str) -> list[dict]:
        """Dangling references to figures/tables/equations that aren't declared."""
        return _dump(internal_refs.run(text))

    @mcp.tool()
    def check_citations(refs: list[dict], live: bool = True) -> list[dict]:
        """Resolve each reference against Crossref/OpenAlex; flag non-existent ones.
        Each item: {raw, doi?, title?, location?}."""
        return _dump(citations.run([citations.Citation(**r) for r in refs], live=live))

    @mcp.tool()
    def check_llm_residue(text: str) -> list[dict]:
        """Leftover chatbot strings / unfilled placeholders. AUTHORSHIP axis,
        flag-only — never on its own evidence of fraud."""
        return _dump(llm_residue.run(text))

    @mcp.tool()
    def check_template_residue(text: str) -> list[dict]:
        """Unfinalized conference/journal template boilerplate. AUTHORSHIP axis,
        low — a formatting signal only, never feeds the integrity index."""
        return _dump(template_residue.run(text))

    @mcp.tool()
    def check_citation_collision(usages: list[dict]) -> list[dict]:
        """Same method label cited as two different references. No network.
        Each item: {label, ref_id, location?}."""
        return _dump(citation_collision.run(
            [citation_collision.CitationUsage(**u) for u in usages]))

    @mcp.tool()
    def check_numeric_consistency(claims: list[dict]) -> list[dict]:
        """Global check: same (metric, subject) reported with different values
        anywhere in the paper. Severity escalates with the number of conflicts
        (1=typo-level flag, >=3=systematic verdict). Each item:
        {metric, subject, value, location?}."""
        return _dump(numeric_consistency.run(
            [numeric_consistency.NumericClaim(**c) for c in claims]))

    @mcp.tool()
    def check_statistical_anomaly(columns: list[dict]) -> list[dict]:
        """Domain-general fabrication tells on numeric columns: arithmetic
        progressions, non-random terminal digits, precision outliers. Each item:
        {name, values:[...], location?}."""
        return _dump(statistical_anomaly.run(
            [statistical_anomaly.NumberColumn(**c) for c in columns]))

    @mcp.tool()
    def check_citation_title_match(refs: list[dict]) -> list[dict]:
        """Offline: does 'Name [N]' match reference [N]'s title? Catches
        mis-numbered citations. Each item: {label, ref_id, ref_title, location?}."""
        return _dump(citation_title_match.run(
            [citation_title_match.CitationRef(**r) for r in refs]))

    @mcp.tool()
    def summarize(findings: list[dict]) -> dict:
        """Aggregate raw findings into the two itemized indices (kept separate)."""
        objs = [_finding_from_dict(d) for d in findings]
        r = Report(objs)
        out = r.as_dict()
        out["rendered"] = r.render()
        return out

    return mcp


def _finding_from_dict(d: dict) -> Finding:
    from .types import Axis, Evidence, OutputType, Severity
    ev = d.get("evidence")
    return Finding(
        detector=d["detector"],
        axis=Axis(d["axis"]),
        output_type=OutputType(d["output_type"]),
        severity=Severity(d["severity"]),
        message=d["message"],
        evidence=Evidence(**ev) if ev else None,
        location=d.get("location"),
    )


def main():
    build_server().run()


if __name__ == "__main__":
    main()
