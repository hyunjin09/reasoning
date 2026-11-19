"""Frozen arm payload and alias rules, independent of scores and model outcomes."""
from scripts.stage14d1.contracts import ARMS, solver_suffix, valid_readout


def continuation_plan(item, readouts):
    physical = {f"{item}_N": ""}
    seen = {"": f"{item}_N"}
    logical = {"N": f"{item}_N"}
    for arm in ARMS[1:]:
        record = readouts.get(arm)
        suffix = solver_suffix(record) if valid_readout(record) else ""
        if suffix not in seen:
            seen[suffix] = f"{item}_{arm}"
            physical[seen[suffix]] = suffix
        logical[arm] = seen[suffix]
    return physical, logical


def read_plan(image, query_valid, address_valid, views):
    physical = {"G": [image]}
    aliases = {}
    if not query_valid:
        return physical, aliases
    physical.update(Q=[], QI=[image])
    if not address_valid:
        aliases.update(QIA="QI", QGL="QI")
        return physical, aliases
    physical["QIA"] = [image]
    if len(views) == 1:
        aliases["QGL"] = "QIA"
    else:
        assert views[0] == image
        physical["QGL"] = views
    return physical, aliases


def remaining_budget(prior, allocated, outstanding):
    value = 57600 - prior - sum(allocated) - sum(outstanding)
    if value < 0:
        raise ValueError("Cumulative 16 GPU-hour reservation exceeded")
    return value
