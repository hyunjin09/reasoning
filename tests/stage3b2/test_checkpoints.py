from visual_reasoning.stage3b2.checkpoints import build_switch_schedule


def test_switch_schedule_includes_generation_start_ed_and_deduplicates() -> None:
    rows = build_switch_schedule(16)
    indices = [row["switch_generated_index"] for row in rows]

    assert indices == sorted(set(indices))
    assert indices[0] == 0
    assert indices[-1] == 16
    assert next(row for row in rows if row["switch_generated_index"] == 16)["labels"] == ["Ed"]
    assert all(0 <= row["switch_generated_index"] <= 16 for row in rows)


def test_switch_schedule_maps_relative_and_progress_coordinates() -> None:
    rows = build_switch_schedule(100)
    by_index = {row["switch_generated_index"]: row for row in rows}

    assert "Ed_minus_64" in by_index[36]["labels"]
    assert "progress_25" in by_index[25]["labels"]
    assert "Ed_minus_1" in by_index[99]["labels"]
    assert by_index[100]["tokens_before_ed"] == 0
