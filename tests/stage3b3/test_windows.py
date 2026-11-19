from visual_reasoning.stage3b3.windows import (
    coarse_layer_windows,
    cumulative_layer_windows,
    fine_two_layer_windows,
)


def test_coarse_windows_cover_each_of_36_layers_once() -> None:
    windows = coarse_layer_windows()

    assert [row["name"] for row in windows] == [f"W{index}" for index in range(6)]
    assert [row["layers"] for row in windows] == [list(range(start, start + 6)) for start in range(0, 36, 6)]
    assert sorted(layer for row in windows for layer in row["layers"]) == list(range(36))


def test_cumulative_windows_freeze_lower_prefix_and_upper_suffix_sets() -> None:
    cumulative = cumulative_layer_windows()

    assert cumulative["lower_prefix"][0]["layers"] == list(range(0, 6))
    assert cumulative["lower_prefix"][-1]["layers"] == list(range(36))
    assert cumulative["upper_suffix"][0]["layers"] == list(range(30, 36))
    assert cumulative["upper_suffix"][-1]["layers"] == list(range(36))


def test_fine_windows_are_limited_to_qualifying_coarse_regions_and_neighbors() -> None:
    fine = fine_two_layer_windows(["W2"])

    assert [row["layers"] for row in fine] == [
        [6, 7], [8, 9], [10, 11],
        [12, 13], [14, 15], [16, 17],
        [18, 19], [20, 21], [22, 23],
    ]
    assert all(row["parent_window"] in {"W1", "W2", "W3"} for row in fine)


def test_no_qualifying_coarse_window_produces_no_fine_scan() -> None:
    assert fine_two_layer_windows([]) == []
