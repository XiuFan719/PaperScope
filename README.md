# paperscope

A deterministic **academic-integrity screening** core, exposed as an **MCP server**.
It flags *data-fabrication* signals (arithmetic/stat consistency, citation checks,
numeric contradictions, lazy-fabrication tells) — and keeps them strictly separate
from *AI-assist / template residue*, which it reports but **never** treats as fraud.

## The one idea that matters: two axes, never summed

- **数据完整性疑点指数 (integrity)** — is the data fabricated? Verdict-grade, auditable.
- **格式/AI 痕迹 (format)** — template residue / AI-assisted writing. Flag-only, **never** fraud.

A paper can be 100% AI-written and perfectly honest. A non-native-English author
using AI to polish is fine. Only the integrity axis carries a fraud signal.

## Install

```bash
pip install -e .
```

(Python ≥ 3.10. Pulls `scipy`, `pyyaml`, `mcp`.)

## Use it from an MCP client (Claude Desktop, Cursor, Cline, …)

Add this to your client's MCP config, then restart the client:

```json
{
  "mcpServers": {
    "paperscope": {
      "command": "paperscope-mcp"
    }
  }
}
```

The 12 detector tools then appear in the client. **How it's meant to work:** the
LLM client reads the PDF and extracts the claims (tables, numbers, citations) —
it is the "front door" — and calls paperscope's tools for the deterministic
ground-truth check. Ask it: *"read this paper and run it through paperscope."*

## Detectors

`statcheck` · `grim` · `table_consistency` · `duplicate_blocks` · `internal_refs`
· `citations` (Crossref/OpenAlex, online) · `citation_collision` ·
`citation_title_match` (offline) · `numeric_consistency` (escalates by pattern:
one mismatch = typo-level, many = systematic) · `statistical_anomaly`
(arithmetic runs, terminal-digit, precision) · `llm_residue` · `template_residue`.

## Anti-gaming: concept public, parameters private

The detector **logic** is open (evading a consistency check = being honest).
The tunable **thresholds** live in `rules.yaml` — keep your real copy out of the
repo (point `$PAPERSCOPE_RULES` elsewhere) and rotate them, so fabrications can't
be tuned to sit just under a known line.

## Scope & honesty

paperscope raises the *cost* of fabrication and catches the *lazy* kind; a careful
fabricator who makes everything consistent can pass the deterministic layer. It is
a **reviewer aid that emits auditable claims**, not an automated gatekeeper.
