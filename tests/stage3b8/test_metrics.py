from visual_reasoning.stage3b8.metrics import value_restoration_metrics


def test_value_restoration_metric_is_bidirectional_and_sham_controlled() -> None:
    row = value_restoration_metrics(
        recipient_scores={
            "O": {"O": 4.0, "O_sham": 3.8, "C": 1.0, "C_sham": 1.2},
            "C": {"O": 3.0, "O_sham": 2.8, "C": 0.0, "C_sham": 0.2},
        }
    )
    assert row["BVR_O"] == 2.8
    assert row["BVR_C"] == 2.8
    assert row["BVR"] == 2.8
    assert abs(row["sham_effect"] - 0.2) < 1e-12
    assert row["bidirectionally_source_consistent"] is True
