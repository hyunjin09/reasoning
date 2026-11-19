import pytest

from visual_reasoning.stage8a.localization import select_late_window, joint_window_gate


def profile(family, values):
    return {"family_id": family, "results": [
        {"layers": [l], "semantic_minus_sham": values[l]} for l in range(28)]}


def test_discovery_free_layer_selection_uses_calibration_families_and_earlier_tie():
    records = [profile(str(f), [0.]*14+[1.]*14) for f in range(4)]
    result = select_late_window(records)
    assert result["selected_layers"] == [14, 15, 16, 17]
    assert result["ranked_windows"][0]["family_median"] == 4.
    assert result["family_count"] == 4


def test_incomplete_profile_and_duplicate_family_cannot_inflate_evidence():
    records = [profile(str(f), [0.]*28) for f in range(4)]
    records[0]["results"].pop()
    with pytest.raises(ValueError):
        select_late_window(records)
    duplicate = profile("same", [0.]*28)
    with pytest.raises(ValueError):
        select_late_window([duplicate]*4)


def test_joint_gate_requires_signed_family_coverage_and_positive_median():
    def records(effects):
        return [{"family_id": str(i), "results": [{"layers": [14,15,16,17],
                 "semantic_minus_sham": v, "target_relative_vsd": -.1}]} for i,v in enumerate(effects)]
    gate = joint_window_gate(records([1., 1., 1., -1.]), [14,15,16,17])
    assert gate["visual_transfer_supported"]
    assert not gate["target_selectivity_supported"]
    assert not joint_window_gate(records([1., 1., -1., -1.]), [14,15,16,17])["visual_transfer_supported"]
