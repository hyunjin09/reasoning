"""Evidence-specific source-switch metrics."""

from __future__ import annotations

import math
from typing import Any


def normalize_by_evidence_gap(effect: float, evidence_gap: float) -> float | None:
    """Return an unclipped secondary ratio only for a positive finite gap."""

    gap = float(evidence_gap)
    value = float(effect)
    if not math.isfinite(gap) or not math.isfinite(value) or gap <= 0.0:
        return None
    return value / gap


def switch_metrics(
    *, d_oo: float, d_oc: float, d_cc: float, d_co: float, d_os: float
) -> dict[str, Any]:
    o_to_c = float(d_oo) - float(d_oc)
    c_to_o = float(d_co) - float(d_cc)
    o_to_sham = float(d_oo) - float(d_os)
    return {
        "D_OO": float(d_oo),
        "D_OC": float(d_oc),
        "D_CC": float(d_cc),
        "D_CO": float(d_co),
        "D_OS": float(d_os),
        "S_O_to_C": o_to_c,
        "S_C_to_O": c_to_o,
        "BRI": (o_to_c + c_to_o) / 2.0,
        "S_O_to_Sham": o_to_sham,
        "O_to_C_source_consistent": o_to_c > 0.0,
        "C_to_O_source_consistent": c_to_o > 0.0,
        "bidirectionally_source_consistent": o_to_c > 0.0 and c_to_o > 0.0,
    }
