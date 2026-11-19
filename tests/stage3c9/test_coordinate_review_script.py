from pathlib import Path
import json
import runpy


def test_coordinate_review_outputs_are_stage3c9_scoped() -> None:
    script = Path("scripts/stage3c9/make_coordinate_review_images.py")
    source = script.read_text(encoding="utf-8")

    assert 'OUT = ROOT / "outputs/stage3c9"' in source
    assert "target.relative_to(OUT.resolve())" in source


def test_manual_edit_specs_cover_every_requested_base() -> None:
    namespace = runpy.run_path("scripts/stage3c9/write_manual_edit_specs.py")
    expected = {
        json.loads(line)["base_problem_id"]
        for line in Path("outputs/stage3c9/cohort/work/manual_edit_specs_needed.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        if line.strip()
    }

    assert set(namespace["SPECS"]) == expected
    assert len(namespace["SPECS"]) == 48


def test_edit_repair_specs_are_frozen_without_causal_results() -> None:
    namespace = runpy.run_path("scripts/stage3c9/repair_edits_v2.py")

    assert set(namespace["REPAIRS"]) == {
        "104", "128", "129", "142", "149", "161", "226", "254",
        "331", "353", "363", "425", "675", "743", "752", "762",
    }
    assert namespace["CAUSAL_SCORES_AVAILABLE"] is False
