from visual_reasoning.stage3b8.evaluation import evaluate_mathverse_response


def test_free_response_ground_truth_drops_latex_unit_power():
    result = evaluate_mathverse_response(
        r"Therefore, the final answer is $\boxed{113.10}$.",
        r"Volume $=113.10 \mathrm{~cm}^{3}$",
    )
    assert result["correct"] is True
    assert result["normalized_ground_truth"] == "113.100000000000"


def test_free_response_ground_truth_drops_plain_unit_power():
    result = evaluate_mathverse_response(
        r"Therefore, $\boxed{1520.53}$.",
        r"Surface Area $=1520.53 \mathrm{cm}^2$",
    )
    assert result["correct"] is True


def test_free_response_unit_attached_directly_to_number_is_removed():
    result = evaluate_mathverse_response(
        "**Final Answer:**\n1690",
        "$1690cm^2$",
    )
    assert result["correct"] is True


def test_free_response_cubic_units_prose_is_removed():
    result = evaluate_mathverse_response(
        "### Final Answer:\n$$\\boxed{452.389}$$",
        "Volume $=452.389$ cubic units",
    )
    assert result["correct"] is True


def test_free_response_final_answer_on_following_line_is_extracted():
    result = evaluate_mathverse_response(
        "**Final Answer**\n33.51",
        "Volume $=33.51 \\mathrm{~cm}^{3}$",
    )
    assert result["correct"] is True


def test_free_response_final_value_marker_is_extracted():
    result = evaluate_mathverse_response(
        "Thus the area is **216**.\n\nFinal value: 216",
        "216.\\mathrm{cm}^2",
    )
    assert result["correct"] is True


def test_latex_text_unit_with_space_before_brace_is_removed():
    result = evaluate_mathverse_response(
        r"Therefore, $\boxed{8128.50}$.",
        r"8128.50 \text { units }^2",
    )
    assert result["correct"] is True
