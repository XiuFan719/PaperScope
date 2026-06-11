"""paperscope — academic-integrity screening core.

Two axes, scored separately and never summed:
  * data_integrity (造假轴) — verdict-grade, auditable, open-source
  * authorship      (AI 辅助轴) — flag-only, never a fraud verdict on its own
"""
from .report import Report
from .types import Axis, Evidence, Finding, OutputType, Severity

__all__ = ["Report", "Finding", "Evidence", "Axis", "OutputType", "Severity"]
__version__ = "0.1.0"
