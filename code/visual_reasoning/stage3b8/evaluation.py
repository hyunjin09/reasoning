"""Outcome-only MathVerse evaluation for Stage 3B.8 discovery generation.

The historical Stage 0 evaluator intentionally extracts A--E choices.  The
fresh Stage 3B.8 screen also contains free-response numeric items, so those
responses need a separate evaluator.  This module never changes generations;
it only produces an auditable reclassification overlay.
"""

from __future__ import annotations

import math
import re
from typing import Any

import sympy

from visual_reasoning.stage0.analysis import extract_answer


def last_boxed_expression(text: str) -> str | None:
    """Return the last balanced ``\\boxed{...}`` payload."""

    found: list[str] = []
    cursor = 0
    marker = r"\boxed{"
    while True:
        start = text.find(marker, cursor)
        if start < 0:
            break
        payload_start = start + len(marker)
        depth = 1
        end = payload_start
        while end < len(text) and depth:
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
            end += 1
        if depth == 0:
            found.append(text[payload_start : end - 1].strip())
        cursor = start + len(marker)
    return found[-1] if found else None


def _strip_latex_wrappers(value: str) -> str:
    value = value.strip().replace("−", "-").replace("×", "*").replace("÷", "/")
    value = re.sub(
        r"\\(?:mathrm|text|operatorname)\s*\{[^{}]*\}(?:\s*\^\s*\{?\s*[23]\s*\}?)?",
        "",
        value,
    )
    value = re.sub(r"\\(?:left|right|,|;|!|quad|qquad)", "", value)
    value = value.replace("\\,", "").replace("~", "").replace("$", "")
    value = re.sub(r"\^?\\circ\s*T?", "", value, flags=re.IGNORECASE)
    value = re.sub(r"掳\s*T?", "", value, flags=re.IGNORECASE)
    # Ground-truth strings commonly carry a prose/quantity label before '='.
    if "=" in value:
        value = value.rsplit("=", 1)[1]
    value = re.sub(
        r"(?i)(?<![A-Za-z])(?:cm|mm|km|m|degrees?|degree|units?)(?![A-Za-z])"
        r"(?:\s*\^?\s*\{?\s*[23]\s*\}?)?",
        "",
        value,
    )
    value = re.sub(r"(?i)\b(?:square|squared|cubic|cubed)\b", "", value)
    value = value.replace("°", "").strip(" .,:;")
    return value.strip()


def _explicit_final_expression(text: str) -> str | None:
    plain = text.replace("**", "")
    matches = re.findall(
        r"(?:final\s+(?:answer|value)|answer)\s*(?:(?:is|:|=)\s*)?\$*\s*([^\n$]+)",
        plain,
        flags=re.IGNORECASE,
    )
    return matches[-1].strip() if matches else None


def _replace_latex_groups(value: str) -> str:
    fraction = re.compile(r"\\(?:d?frac)\{([^{}]+)\}\{([^{}]+)\}")
    square_root = re.compile(r"\\sqrt\{([^{}]+)\}")
    previous = None
    while value != previous:
        previous = value
        value = fraction.sub(r"((\1)/(\2))", value)
        value = square_root.sub(r"sqrt(\1)", value)
    return value


def _to_sympy(value: str) -> sympy.Expr:
    value = _replace_latex_groups(_strip_latex_wrappers(value))
    value = value.replace("\\pi", "pi").replace("^", "**")
    value = value.replace("{", "(").replace("}", ")")
    value = re.sub(r"\s+", "", value)
    # Explicit multiplication for the compact forms used by MathVerse.
    value = re.sub(r"(?<=\d)(?=(?:sqrt|pi|\())", "*", value)
    value = re.sub(r"(?<=\))(?=(?:\d|sqrt|pi|\())", "*", value)
    value = re.sub(r"(?<=pi)(?=(?:\d|sqrt|\())", "*", value)
    if not value or re.search(r"[^0-9+\-*/().pisqrt]", value):
        raise ValueError(f"Unsupported answer expression: {value!r}")
    return sympy.sympify(value, locals={"pi": sympy.pi, "sqrt": sympy.sqrt})


def evaluate_mathverse_response(response: str, ground_truth: str) -> dict[str, Any]:
    """Evaluate either a multiple-choice or free-response MathVerse answer."""

    ground_truth = ground_truth.strip()
    if re.fullmatch(r"[A-Ea-e]", ground_truth):
        predicted = extract_answer(response)
        return {
            "mode": "multiple_choice",
            "predicted_answer": predicted,
            "ground_truth_answer": ground_truth.upper(),
            "correct": predicted == ground_truth.upper(),
            "evaluation_error": None,
        }

    predicted = last_boxed_expression(response) or _explicit_final_expression(response)
    if predicted is None:
        return {
            "mode": "free_response_symbolic",
            "predicted_answer": None,
            "ground_truth_answer": ground_truth,
            "correct": False,
            "evaluation_error": "no_balanced_boxed_answer",
        }
    try:
        predicted_expr = _to_sympy(predicted)
        truth_expr = _to_sympy(ground_truth)
        difference = sympy.simplify(predicted_expr - truth_expr)
        exact = bool(difference == 0)
        numeric_difference = None
        if not exact:
            numeric_difference = float(abs(sympy.N(difference)))
            scale = max(1.0, abs(float(sympy.N(truth_expr))))
            exact = math.isfinite(numeric_difference) and numeric_difference <= 1e-8 * scale
        return {
            "mode": "free_response_symbolic",
            "predicted_answer": predicted,
            "ground_truth_answer": ground_truth,
            "normalized_predicted": str(predicted_expr),
            "normalized_ground_truth": str(truth_expr),
            "absolute_numeric_difference": numeric_difference,
            "correct": exact,
            "evaluation_error": None,
        }
    except Exception as error:  # retained for manual review, never silently accepted
        return {
            "mode": "free_response_symbolic",
            "predicted_answer": predicted,
            "ground_truth_answer": ground_truth,
            "correct": False,
            "evaluation_error": f"{type(error).__name__}: {error}",
        }
