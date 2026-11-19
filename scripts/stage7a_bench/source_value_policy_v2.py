"""Deterministic natural-source numeric replacement, independent of model output.

This supplies a candidate literal only. Domain plausibility, redundant visual
encodings, edit isolation and a matched sham still require source review.
Unsupported literals or bounds failures have no automatic fallback.
"""
from decimal import Decimal
import re


def numeric_replacement(value, *, lower, upper):
    if not isinstance(value, str) or not re.fullmatch(
            r'[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?', value, flags=re.ASCII):
        raise ValueError('Expected an exact printed numeric literal without units or exponent')
    changed = value[:-1] + str((int(value[-1]) + 5) % 10)
    original, replacement = (Decimal(v.replace(',', '')) for v in (value, changed))
    low = Decimal(lower) if lower is not None else None
    high = Decimal(upper) if upper is not None else None
    if (any(v is not None and not v.is_finite() for v in (low, high)) or
            low is not None and high is not None and low > high or
            any(low is not None and v < low or high is not None and v > high
                for v in (original, replacement))):
        raise ValueError('Source truth or fixed replacement violates independently reviewed bounds')
    return changed
