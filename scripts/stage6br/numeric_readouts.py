"""Literal-only numeric contrasts; expressions require a separate readout."""
from decimal import Decimal, InvalidOperation


def literal_decimal(value):
    try:
        parsed = Decimal(str(value))
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() else None


def select_numeric_foil(truth, counterfactual, alternatives):
    value = literal_decimal(truth)
    if value is None:
        raise ValueError('NONLITERAL_SOURCE_VALUE')
    for candidate in [counterfactual, *alternatives]:
        parsed = literal_decimal(candidate)
        if parsed is not None and parsed != value:
            return str(candidate)
    return str(value + 2)
