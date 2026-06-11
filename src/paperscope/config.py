"""Tunable thresholds live OUTSIDE the detector logic.

The detector *logic* is public (evading it = being honest). These *numbers*
are the part you keep private / rotate, so a fraudster can't tune a fabrication
to sit just under a known line. Override via rules.yaml or $PAPERSCOPE_RULES.
Falls back to these defaults if the file or PyYAML is absent.
"""
from __future__ import annotations

import os

DEFAULTS = {
    "numeric_consistency": {
        "tol": 0.02,
        "repeat_threshold": 4,
    },
    "statistical_anomaly": {
        "constant_diff_min_len": 4,
        "terminal_digit_min_sample": 12,
        "terminal_digit_max_share": 0.6,
        "precision_extra_places": 3,
    },
}


def load_rules(path: str | None = None) -> dict:
    cfg = {k: dict(v) for k, v in DEFAULTS.items()}
    path = path or os.environ.get("PAPERSCOPE_RULES") or \
        os.path.join(os.path.dirname(__file__), "rules.yaml")
    try:
        import yaml  # optional
        with open(path) as f:
            user = yaml.safe_load(f) or {}
        for k, v in (user or {}).items():
            cfg.setdefault(k, {}).update(v or {})
    except Exception:
        pass  # file/lib absent -> defaults
    return cfg
