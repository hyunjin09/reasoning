"""Exact numeral locations within explicitly reviewed native claims."""
import re


def readout_matches(text, readout):
    # A period followed by a digit extends a decimal; a sentence period does not.
    return list(re.finditer(r'(?<![\d.])' + re.escape(readout) + r'(?!\d|\.\d)', text))
