"""Source-oriented Stage 3B.3 causal layer metrics."""

from __future__ import annotations

from typing import Any


def _normalized(value: float, denominator: float) -> float | None:
    denominator = float(denominator)
    if denominator <= 0.0:
        return None
    return float(value) / denominator


def sufficiency_metrics(
    *,
    d_oo: float,
    d_cc: float,
    d_o_to_c: float,
    d_c_to_o: float,
    d_o_to_sham: float,
    all_layer_bri: float,
) -> dict[str, Any]:
    o_to_c = float(d_oo) - float(d_o_to_c)
    c_to_o = float(d_c_to_o) - float(d_cc)
    bws = 0.5 * (o_to_c + c_to_o)
    return {
        "S_W_O_to_C": o_to_c,
        "S_W_C_to_O": c_to_o,
        "BWS": bws,
        "BWS_normalized": _normalized(bws, all_layer_bri),
        "sham_window_shift": float(d_oo) - float(d_o_to_sham),
        "O_to_C_source_consistent": o_to_c > 0.0,
        "C_to_O_source_consistent": c_to_o > 0.0,
        "bidirectionally_source_consistent": o_to_c > 0.0 and c_to_o > 0.0,
    }


def necessity_metrics(
    *,
    d_o_to_c_all: float,
    d_c_to_o_all: float,
    d_o_to_c_except_window: float,
    d_c_to_o_except_window: float,
    d_o_to_sham_all: float,
    d_o_to_sham_except_window: float,
    all_layer_bri: float,
) -> dict[str, Any]:
    original_rescue = float(d_o_to_c_except_window) - float(d_o_to_c_all)
    counterfactual_rescue = float(d_c_to_o_all) - float(d_c_to_o_except_window)
    bwn = 0.5 * (original_rescue + counterfactual_rescue)
    return {
        "N_W_O": original_rescue,
        "N_W_C": counterfactual_rescue,
        "BWN": bwn,
        "BWN_normalized": _normalized(bwn, all_layer_bri),
        "sham_restoration_shift": float(d_o_to_sham_except_window) - float(d_o_to_sham_all),
        "O_restoration_source_consistent": original_rescue > 0.0,
        "C_restoration_source_consistent": counterfactual_rescue > 0.0,
        "bidirectionally_source_consistent": original_rescue > 0.0 and counterfactual_rescue > 0.0,
    }


def activation_patch_metrics(
    *,
    d_oo: float,
    d_cc: float,
    d_o_receive_c: float,
    d_c_receive_o: float,
    d_o_receive_sham: float,
    all_layer_bri: float,
) -> dict[str, Any]:
    o_receive_c = float(d_oo) - float(d_o_receive_c)
    c_receive_o = float(d_c_receive_o) - float(d_cc)
    bap = 0.5 * (o_receive_c + c_receive_o)
    return {
        "A_O_receive_C": o_receive_c,
        "A_C_receive_O": c_receive_o,
        "BAP": bap,
        "BAP_normalized": _normalized(bap, all_layer_bri),
        "sham_activation_shift": float(d_oo) - float(d_o_receive_sham),
        "O_receive_C_source_consistent": o_receive_c > 0.0,
        "C_receive_O_source_consistent": c_receive_o > 0.0,
        "bidirectionally_source_consistent": o_receive_c > 0.0 and c_receive_o > 0.0,
    }
