"""Regression over all four evaluated papers + escalation unit checks.

Expected: SAM ~0, Dialogue ~0, SDGFed moderate, PICT critical.
    PYTHONPATH=src python tests/test_regression.py
"""
from paperscope import Report
from paperscope.detectors import (
    citation_collision, duplicate_blocks, internal_refs, llm_residue,
    numeric_consistency as nc, table_consistency, template_residue,
)
from paperscope.types import Axis, Evidence, Finding, OutputType, Severity


def sam():
    f = []
    f += table_consistency.run([table_consistency.Table(
        "data-engine", {"masks_M": [4.3, 5.9]}, {"masks_M": 10.2})])
    body = "\n".join([f"see Fig. {i}.\nFigure {i}: c." for i in range(1, 9)]
                     + ["see appendix Table 4 for more details."])
    f += internal_refs.run(body)
    f += llm_residue.run("hallucinates small disconnected components.")
    return Report(f)


def dialogue():
    f = []
    f += table_consistency.run([
        table_consistency.Table("g1", {"x": [57.77, 14.32]}, {"x": 72.09}),
        table_consistency.Table("g2", {"x": [72.09, 5.94]}, {"x": 78.03}),
        table_consistency.Table("g3", {"x": [60.02, 5.66]}, {"x": 65.67})],
        abs_tol=0.02)
    f += citation_collision.run([nc_u(m, r) for m, r in [
        ("PlugIR", "10"), ("PlugIR", "10"), ("BRI", "10"), ("ChatIR", "11")]])
    f += template_residue.run("ACM ISBN 978-1-4503-XXXX-X/2026/11 "
                              "https://doi.org/XXXXXXX.XXXXXXX MM '26, Rio de Janeiro.")
    return Report(f)


def nc_u(m, r):
    return citation_collision.CitationUsage(m, r)


def sdgfed():
    f = []
    f += table_consistency.run(
        [table_consistency.Table("T1-DEAP", {"SDGFed": [24.26]})],
        [table_consistency.TextNumberClaim(64.45, "T1-DEAP", "SDGFed", 0,
            location="4.6 calls Table 7 DEAP; its best 64.45 is CREMA-D's")])
    f += duplicate_blocks.run([[v] for v in
        [12.81, 37.17, 37.25, 28.65, 37.17, 22.59, 33.30, 37.69, 37.33, 38.36]],
        table_id="T1 MGEED")
    f += citation_collision.run([nc_u("FedDyn", "1"), nc_u("FedDyn", "14"),
                                 nc_u("FedAvg", "21")])
    f += template_residue.run(
        "Make sure to enter the correct conference title. 978-1-4503-XXXX-X "
        "Unpublished working draft. Not for distribution. Woodstock, NY. "
        "revised 12 March 2009; accepted 5 June 2009")
    return Report(f)


def pict():
    f = []
    f += nc.run([
        nc.NumericClaim("SDS", "Qwen7B base", 2.38, "Table 3"),
        nc.NumericClaim("SDS", "Qwen7B base", 1.78, "Fig 3"),
        nc.NumericClaim("Silhouette", "Qwen7B base", 0.31, "Table 3"),
        nc.NumericClaim("Silhouette", "Qwen7B base", 0.18, "Fig 3"),
        nc.NumericClaim("Silhouette", "Qwen7B PICT", 0.67, "Table 3"),
        nc.NumericClaim("Silhouette", "Qwen7B PICT", 0.71, "Fig 3"),
        nc.NumericClaim("model count", "paper", 8, "abstract"),
        nc.NumericClaim("model count", "paper", 6, "Table 2"),
    ])
    f.append(Finding(detector="reading_layer", axis=Axis.DATA_INTEGRITY,
        output_type=OutputType.VERDICT, severity=Severity.HIGH,
        message="Base models (LLaVA-1.5-7B, Qwen-VL-7B) differ from all "
                "experimental models (Qwen2.5-VL, InternVL-2.5)",
        evidence=Evidence(claim="methodology vs experiment model mismatch",
                          reported="§3.4 base models", expected="Table 2 models")))
    f += template_residue.run("Make sure to enter the correct conference title. "
                              "978-x-xxxx-xxxx-x/YYYY/MM https://doi.org/XXXXXXX.XXXXXXX")
    return Report(f)


for name, r in [("SAM", sam()), ("Dialogue", dialogue()),
                ("SDGFed", sdgfed()), ("PICT", pict())]:
    ig, fm = r.integrity, r.format
    print(f"{name:10s} integrity={ig.index:3d}% ({ig.label.split(' —')[0]:8s})"
          f"  format={fm.index:3d}%")

# escalation invariants
assert nc.run([nc.NumericClaim("a", "b", 1.0), nc.NumericClaim("a", "b", 1.5)])[0].severity \
    == Severity.LOW, "single conflict must stay low"
three = nc.run([nc.NumericClaim(m, "s", 1.0, "p") for m in "xyz"]
               + [nc.NumericClaim(m, "s", 2.0, "q") for m in "xyz"])
assert all(x.output_type == OutputType.VERDICT for x in three), "3+ must be verdicts"
print("\nescalation invariants: OK")
