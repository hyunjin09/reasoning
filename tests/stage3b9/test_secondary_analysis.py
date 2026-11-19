from scripts.stage3b9.analyze_secondary import safe_spearman, selected_head_roi_attention


def test_selected_head_roi_attention_uses_only_frozen_heads_and_both_recipients():
    def condition(offset):
        summary = {
            "V_target_mass_per_head": [offset + value for value in (1.0, 2.0, 3.0, 4.0)],
            "V_target_density_per_head": [offset + value for value in (0.1, 0.2, 0.3, 0.4)],
        }
        return {"capture_audits": {"original_candidate": {"recipient_attention_summary": summary}}}

    mass, density = selected_head_roi_attention(
        {"heads": [1, 3], "no_intervention": {"O": condition(0.0), "C": condition(1.0)}}
    )

    assert mass == 3.5
    assert density == 0.8


def test_safe_spearman_reports_exact_monotonic_relation():
    result = safe_spearman([1.0, 2.0, 3.0], [10.0, 20.0, 30.0])
    assert result["n"] == 3
    assert result["rho"] == 1.0
