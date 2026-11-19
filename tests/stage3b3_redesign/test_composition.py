import pytest

from visual_reasoning.stage3b3_redesign.composition import compose_source_layers


def test_compose_source_layers_uses_window_source_only_inside_window() -> None:
    default = [(f"dk{index}", f"dv{index}") for index in range(6)]
    window = [(f"wk{index}", f"wv{index}") for index in range(6)]

    result = compose_source_layers(default, window, selected_layers=[1, 2, 5])

    assert result == [default[0], window[1], window[2], default[3], default[4], window[5]]


def test_compose_source_layers_rejects_mismatched_or_invalid_layers() -> None:
    with pytest.raises(ValueError):
        compose_source_layers([(1, 1)], [(1, 1), (2, 2)], selected_layers=[0])
    with pytest.raises(ValueError):
        compose_source_layers([(1, 1)], [(2, 2)], selected_layers=[1])

