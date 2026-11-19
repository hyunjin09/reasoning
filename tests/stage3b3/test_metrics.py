import pytest

from visual_reasoning.stage3b3.metrics import (
    activation_patch_metrics,
    necessity_metrics,
    sufficiency_metrics,
)


def test_sufficiency_metric_is_source_oriented_in_both_directions() -> None:
    result = sufficiency_metrics(
        d_oo=4.0,
        d_cc=-4.0,
        d_o_to_c=1.0,
        d_c_to_o=-1.0,
        d_o_to_sham=3.8,
        all_layer_bri=8.0,
    )

    assert result["S_W_O_to_C"] == 3.0
    assert result["S_W_C_to_O"] == 3.0
    assert result["BWS"] == 3.0
    assert result["BWS_normalized"] == 0.375
    assert result["sham_window_shift"] == pytest.approx(0.2)


def test_necessity_metric_orients_restoration_toward_recipient_fact() -> None:
    result = necessity_metrics(
        d_o_to_c_all=-4.0,
        d_c_to_o_all=4.0,
        d_o_to_c_except_window=-1.0,
        d_c_to_o_except_window=1.0,
        d_o_to_sham_all=3.8,
        d_o_to_sham_except_window=3.9,
        all_layer_bri=8.0,
    )

    assert result["N_W_O"] == 3.0
    assert result["N_W_C"] == 3.0
    assert result["BWN"] == 3.0
    assert result["BWN_normalized"] == 0.375
    assert abs(result["sham_restoration_shift"] - 0.1) < 1e-12


def test_activation_patch_metric_matches_visual_source_sign_convention() -> None:
    result = activation_patch_metrics(
        d_oo=4.0,
        d_cc=-4.0,
        d_o_receive_c=0.5,
        d_c_receive_o=-0.25,
        d_o_receive_sham=3.9,
        all_layer_bri=8.0,
    )

    assert result["A_O_receive_C"] == 3.5
    assert result["A_C_receive_O"] == 3.75
    assert result["BAP"] == 3.625
    assert result["BAP_normalized"] == 3.625 / 8.0
