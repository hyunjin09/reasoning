"""Signed, length-normalized evidence readouts for the frozen source controls."""
import math


def summarize_control_scores(raw):
    required = {"native", "self", "semantic", "sham", "target_off", "irrelevant_off"}
    if not required.issubset(raw):
        raise ValueError("Missing required control")
    means = {}
    for arm, candidates in raw.items():
        if set(candidates) != {"original", "counterfactual"}:
            raise ValueError("Both oriented readouts are required")
        means[arm] = {}
        for candidate, values in candidates.items():
            if not values or not all(math.isfinite(v) for v in values):
                raise ValueError("Empty or nonfinite readout is unavailable")
            means[arm][candidate] = sum(values)/len(values)
    if raw["self"] != raw["native"]:
        raise ValueError("Self control must reproduce the native readout exactly")
    if ("roi_semantic" in raw) != ("roi_sham" in raw):
        raise ValueError("ROI semantic and sham must be paired")
    margins = {arm: m["counterfactual"]-m["original"] for arm, m in means.items()}
    effects = {arm: margin-margins["native"] for arm, margin in margins.items() if arm != "native"}
    target = means["native"]["original"]-means["target_off"]["original"]
    irrelevant = means["native"]["original"]-means["irrelevant_off"]["original"]
    return dict(token_log_probabilities=raw, mean_log_probabilities=means,
                cf_minus_original_margin=margins, margin_shifts=effects,
                semantic_minus_sham=effects["semantic"]-effects["sham"],
                roi_semantic_minus_sham=effects["roi_semantic"]-effects["roi_sham"] if "roi_semantic" in effects else None,
                target_off_ce_effect=target, irrelevant_off_ce_effect=irrelevant,
                target_relative_vsd=target-irrelevant)
