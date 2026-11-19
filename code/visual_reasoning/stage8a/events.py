"""Exact alignment of manually reviewed semantic events to fresh native tokens."""


def align_literal_event(rows, *, quote, value):
    if not quote or not value or quote.count(value) != 1:
        raise ValueError("Quote must identify exactly one value occurrence")
    if [int(r["token_index"]) for r in rows] != list(range(len(rows))):
        raise ValueError("Native token indices must be contiguous")
    text = "".join(r["decoded_token"] for r in rows)
    if text.count(quote) != 1:
        raise ValueError("Missing or ambiguous reviewed quote")
    begin = text.index(quote) + quote.index(value)
    end = begin + len(value)
    offsets, current = [], 0
    for row in rows:
        stop = current + len(row["decoded_token"])
        offsets.append((current, stop))
        current = stop
    selected = [i for i, (a, b) in enumerate(offsets) if a < end and b > begin]
    if not selected or offsets[selected[0]][0] != begin or offsets[selected[-1]][1] != end:
        raise ValueError("Evidence value must end and start at a native token boundary")
    start, stop = selected[0], selected[-1]+1
    if start == 0:
        raise ValueError("Event needs a nonempty native reasoning prefix")
    return dict(quote=quote, readout=value, char_start=begin, char_end=end,
                prefix_length=start, evidence_end_token=stop,
                prefix_token_ids=[int(r["token_id"]) for r in rows[:start]],
                evidence_token_ids=[int(r["token_id"]) for r in rows[start:stop]],
                history_text=text[:begin])


def divergent_readout(prefix, original, counterfactual):
    """Keep shared literal tokens in native history; score differing suffixes."""
    original, counterfactual = list(original), list(counterfactual)
    if not original or not counterfactual:
        raise ValueError("Both readouts must be nonempty")
    if original == counterfactual:
        raise ValueError("Readouts are identical")
    common = 0
    while common < min(len(original), len(counterfactual)) and original[common] == counterfactual[common]:
        common += 1
    if common == min(len(original), len(counterfactual)):
        raise ValueError("A strict prefix readout needs a separately reviewed terminator")
    return dict(prefix_token_ids=list(prefix)+original[:common], common_bridge_ids=original[:common],
                original_token_ids=original[common:], counterfactual_token_ids=counterfactual[common:])
