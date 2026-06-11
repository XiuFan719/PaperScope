"""Smoke test: feed a deliberately-broken mini-paper through every v1 detector
and print the two-axis report. Run:

    PYTHONPATH=src python tests/test_smoke.py
"""
from paperscope import Report
from paperscope.detectors import (
    duplicate_blocks,
    grim,
    internal_refs,
    llm_residue,
    statcheck,
    table_consistency,
)

findings = []

# 1) statcheck — t(48)=2.10 cannot give p<.001
findings += statcheck.run([
    statcheck.ReportedStat(test="t", value=2.10, df1=48, reported_p=0.0009, location="§4.2"),
    statcheck.ReportedStat(test="F", value=4.5, df1=2, df2=60, reported_p=0.015),  # consistent-ish
])

# 2) GRIM — mean 3.17 impossible for N=10 on a 1-item integer scale
findings += grim.run([
    grim.ReportedMean(mean=3.17, n=10, location="Table 1"),
    grim.ReportedMean(mean=3.20, n=10),  # achievable -> no finding
])

# 3) table consistency — parts don't sum to the reported total
findings += table_consistency.run(
    tables=[table_consistency.Table(
        table_id="Table 2",
        columns={"count": [10.0, 20.0, 30.0], "pct": [33.0, 33.0, 33.0]},
        reported_totals={"count": 70.0},  # actual sum = 60
    )],
)

# 4) duplicate blocks — three identical fabricated rows
findings += duplicate_blocks.run(
    [[1.23, 4.56], [1.23, 4.56], [1.23, 4.56], [7.89, 0.12]],
    table_id="Table 3",
)

# 5) internal refs — text cites Figure 9 that is never declared
findings += internal_refs.run(
    "As shown in Figure 9 the effect holds (see also Figure 1).\n"
    "Figure 1: overview of the method.\n"
)

# 6) llm residue — authorship axis, flag only
findings += llm_residue.run(
    "Certainly! Here is the revised abstract you requested. As an AI language "
    "model, I note that [insert citation] supports this."
)

report = Report(findings)
print(report.render())
print()
print("ASSERTIONS:")
print("  integrity index > 0:", report.integrity.index > 0)
print("  format index > 0:", report.format.index > 0)
print("  integrity label:", report.integrity.label)
