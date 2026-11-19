"""The predeclared calibration-only window selection and joint confirmation."""
import math
from statistics import median


def _families(records):
    families = [r["family_id"] for r in records]
    if not families or len(set(families)) != len(families):
        raise ValueError("Calibration must have one event per independent family")
    return families


def select_late_window(records):
    families = _families(records)
    if len(families) < 4:
        raise ValueError("At least four calibration families are required")
    profiles = []
    for record in records:
        if len(record["results"]) != 28 or any(len(r["layers"]) != 1 for r in record["results"]):
            raise ValueError("A complete single-layer profile is required")
        profile = {r["layers"][0]: r["semantic_minus_sham"] for r in record["results"]}
        if set(profile) != set(range(28)) or not all(math.isfinite(v) for v in profile.values()):
            raise ValueError("Missing, duplicated or nonfinite layer")
        profiles.append(profile)
    ranked = []
    for start in range(14,25):
        values = [sum(p[l] for l in range(start,start+4)) for p in profiles]
        ranked.append(dict(start=start, layers=list(range(start,start+4)), family_effects=dict(zip(families, values)),
                           family_median=median(values), positive_family_fraction=sum(v>0 for v in values)/len(values)))
    ranked.sort(key=lambda r: (-r["family_median"], r["start"]))
    return dict(selected_layers=ranked[0]["layers"], heads=list(range(16)), family_count=len(families),
                ranked_windows=ranked, selection_scope="calibration_only", joint_confirmation_required=True)


def joint_window_gate(records, selected_layers):
    families = _families(records)
    if any(len(r["results"]) != 1 or r["results"][0]["layers"] != selected_layers for r in records):
        raise ValueError("Joint result differs from the frozen selected window")
    effects = [r["results"][0]["semantic_minus_sham"] for r in records]
    vsd = [r["results"][0]["target_relative_vsd"] for r in records]
    if not all(math.isfinite(v) for v in effects+vsd):
        raise ValueError("Nonfinite causal result")
    n = len(families)
    supported = n >= 4 and median(effects)>0 and 3*sum(v>0 for v in effects)>=2*n
    selective = supported and median(vsd)>0 and 3*sum(v>0 for v in vsd)>=2*n
    return dict(family_count=n, selected_layers=selected_layers,
                family_median_semantic_minus_sham=median(effects), positive_family_fraction=sum(v>0 for v in effects)/n,
                family_median_target_relative_vsd=median(vsd), positive_vsd_fraction=sum(v>0 for v in vsd)/n,
                visual_transfer_supported=supported, target_selectivity_supported=selective,
                scope="Calibration window only; main held-out gates remain untested")
