from __future__ import annotations

from scripts.stage3c4.run_scoring import arms_for_mode


def test_validation_single_layer_uses_each_frozen_target_layer() -> None:
    arms = arms_for_mode(
        mode="validation",
        current=20,
        target_layer=28,
        layers={"L0": [28, 29], "L4": list(range(36)), "L2": list(range(24, 36))},
        temporal={"T0": 0, "T4": 4},
        interactions={},
    )

    assert arms[0]["layers"] == [28]
