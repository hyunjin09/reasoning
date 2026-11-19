"""Apply discovery-fitted probes without refitting on confirmation families."""
import numpy as np

from .probes import inputs, metrics


def frozen_predictions(events, models, discovery_families, primary_kind):
    if not events or any(e["split"] != "confirmation" for e in events):
        raise ValueError("Expected only confirmation events")
    if set(discovery_families) & {e["family_id"] for e in events}:
        raise ValueError("Discovery and confirmation families overlap")
    if len({e["event_id"] for e in events}) != len(events):
        raise ValueError("Duplicate confirmation events")
    if primary_kind not in {"joint", "extended"} or primary_kind not in models:
        raise ValueError("Primary must be the frozen joint passive retrieval rule")
    result = {}
    for kind, frozen in models.items():
        if frozen["spec"]["kind"] != kind:
            raise ValueError("Model and feature specification differ")
        score = frozen["model"].predict_proba(inputs(events, frozen["spec"]))[:, 1]
        if not np.isfinite(score).all() or ((score < 0) | (score > 1)).any():
            raise ValueError("Invalid frozen probabilities")
        threshold = float(frozen["threshold"])
        result[kind] = dict(score=score.tolist(), threshold=threshold,
                            spec=frozen["spec"], metrics=metrics(events, score, threshold))
    return result
