from visual_reasoning.stage3b8.evaluation import evaluate_mathverse_response, last_boxed_expression


def test_last_boxed_expression_balances_nested_latex() -> None:
    response = r"work \boxed{4+4\sqrt{3}} then \boxed{\frac{9\sqrt{3}}{2}}"
    assert last_boxed_expression(response) == r"\frac{9\sqrt{3}}{2}"


def test_choice_answer_uses_existing_multiple_choice_semantics() -> None:
    result = evaluate_mathverse_response("Therefore the final answer is B.", "B")
    assert result["correct"] is True
    assert result["predicted_answer"] == "B"
    assert result["mode"] == "multiple_choice"


def test_numeric_mathverse_answer_with_units() -> None:
    result = evaluate_mathverse_response(
        r"Thus the circumference is \boxed{50.27}.",
        r"Circumference $=50.27 \mathrm{~cm}$",
    )
    assert result["correct"] is True
    assert result["predicted_answer"] == "50.27"


def test_symbolic_radical_answer() -> None:
    result = evaluate_mathverse_response(
        r"Hence \boxed{\frac{9\sqrt{3}}{2}}.",
        r"\frac{9\sqrt{3}}{2}",
    )
    assert result["correct"] is True


def test_wrong_symbolic_answer_is_rejected() -> None:
    result = evaluate_mathverse_response(
        r"Hence \boxed{9\sqrt{3}}.",
        r"\frac{9\sqrt{3}}{2}",
    )
    assert result["correct"] is False


def test_degree_ground_truth_suffix_is_normalized() -> None:
    result = evaluate_mathverse_response(r"Therefore \boxed{230}.", r"230 ^\circ T")
    assert result["correct"] is True


def test_explicit_unboxed_final_answer_fallback() -> None:
    result = evaluate_mathverse_response(
        "Reasoning...\n\n**Answer**: 35.7",
        r"Perimeter $=35.7 \mathrm{~mm}$",
    )
    assert result["correct"] is True
