import pytest

from visual_reasoning.stage8a.assays import summarize_control_scores


def score_fixture():
    return {
        "native": {"original": [-.2, -.4], "counterfactual": [-1., -1.2]},
        "self": {"original": [-.2, -.4], "counterfactual": [-1., -1.2]},
        "semantic": {"original": [-1., -1.], "counterfactual": [-.1, -.3]},
        "sham": {"original": [-.25, -.45], "counterfactual": [-.95, -1.15]},
        "target_off": {"original": [-.8, -1.], "counterfactual": [-.5, -.7]},
        "irrelevant_off": {"original": [-.3, -.5], "counterfactual": [-1., -1.2]},
    }


def test_semantic_shift_and_source_removal_have_distinct_correct_orientations():
    result = summarize_control_scores(score_fixture())
    assert result["margin_shifts"]["self"] == 0
    assert result["semantic_minus_sham"] == pytest.approx(1.5)
    assert result["target_off_ce_effect"] == pytest.approx(.6)
    assert result["irrelevant_off_ce_effect"] == pytest.approx(.1)
    assert result["target_relative_vsd"] == pytest.approx(.5)
    assert result["roi_semantic_minus_sham"] is None


def test_missing_or_nonfinite_readout_is_not_a_zero_effect():
    raw = score_fixture()
    raw["semantic"]["counterfactual"] = []
    with pytest.raises(ValueError):
        summarize_control_scores(raw)
    raw = score_fixture()
    raw["sham"]["original"][0] = float("nan")
    with pytest.raises(ValueError):
        summarize_control_scores(raw)
