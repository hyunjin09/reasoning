import numpy as np
import pytest

from visual_reasoning.stage8a.confirmation import frozen_predictions


class PredictOnly:
    def predict_proba(self, values):
        return np.array([[.1, .9], [.8, .2], [.2, .8], [.9, .1]])

    def fit(self, *args, **kwargs):
        raise AssertionError("Confirmation must never refit")


def fixture():
    events = [dict(event_id=str(i), split="confirmation", family_id=f"c{i//2}",
                   label="T" if i % 2 == 0 else "M",
                   features={"median_k4": dict(visual_mass=.2, qk_visual_nonvisual=1., qk_visual_reasoning=2.)})
              for i in range(4)]
    models = {"joint": dict(model=PredictOnly(), threshold=.8,
                             spec=dict(kind="joint", aggregation="median", window=4, C=1.))}
    return events, models


def test_confirmation_uses_frozen_model_and_strict_discovery_threshold():
    events, models = fixture()
    result = frozen_predictions(events, models, ["d0", "d1"], "joint")["joint"]
    assert result["metrics"]["auroc"] == 1.
    assert result["threshold"] == .8
    assert result["metrics"]["recall"] == .5
    assert result["metrics"]["mention_fpr"] == 0.


def test_confirmation_rejects_family_leakage_and_nonconfirmation_inputs():
    events, models = fixture()
    with pytest.raises(ValueError, match="overlap"):
        frozen_predictions(events, models, ["c0"], "joint")
    events[0]["split"] = "discovery"
    with pytest.raises(ValueError, match="confirmation"):
        frozen_predictions(events, models, [], "joint")
