from scripts.stage3b2.finalize_smoke import evaluate_smoke


def test_evaluate_smoke_requires_transparency_integrity_and_small_sham() -> None:
    rows = [
        {
            "base_problem_id": str(index),
            "capture_all_layers_valid": True,
            "stage3a_divergent_tail_exact": True,
            "all_checkpoint_switch_audits_valid": True,
            "all_self_switches_exact": True,
            "all_finite": True,
            "ed_O_to_C_deterministic_exact": True,
            "ed_target_switch_effect": 2.0,
            "ed_sham_switch_effect": 0.1,
            "ed_sham_smaller_than_target": True,
            "condition_prompt_visual_layout_exact": True,
        }
        for index in range(3)
    ]

    result = evaluate_smoke(rows)

    assert result["status"] == "PASS"
    assert result["criterion_count"] == 10
