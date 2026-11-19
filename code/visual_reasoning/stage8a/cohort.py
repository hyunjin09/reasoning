"""Deterministic input-only grouping, split, and semantic-yield reserve."""
import re


def freeze_cohort(rows, order, calibration_bases, *, per_split=48):
    by_id = {r["base_id"]: r for r in rows}
    if len(by_id) != len(rows) or len(order) != len(set(order)) or set(order) != set(by_id):
        raise ValueError("Unique complete candidate order required")
    if not set(calibration_bases) <= set(by_id):
        raise ValueError("Calibration missing from inventory")
    parent = {b: b for b in by_id}

    def root(b):
        while parent[b] != b:
            parent[b] = parent[parent[b]]
            b = parent[b]
        return b

    owners = {}
    for r in rows:
        question = re.sub(r"\d+(?:\.\d+)?", "<num>", r["question"].lower())
        question = re.sub(r"\s+", " ", question).strip()
        keys = [(k, r.get(k)) for k in ("family_id", "decoded_image_sha256", "rescaled_identity_sha256", "template")]
        keys.append(("numeric_normalized_question", question))
        for k, value in keys:
            if not value:
                continue
            key = k, value
            if key in owners:
                parent[root(r["base_id"])] = root(owners[key])
            owners[key] = r["base_id"]
    groups = {}
    for b in order:
        groups.setdefault(root(b), []).append(b)
    calibration_roots = {root(b) for b in calibration_bases}
    excluded = sorted([b for b in order if root(b) in calibration_roots], key=int)
    representatives, aliases = [], []
    for group, members in groups.items():
        if group in calibration_roots:
            continue
        r = dict(by_id[members[0]])
        r.update(family_id="mathverse_family_"+"_".join(sorted(members, key=int)),
                 known_family_members=sorted(members, key=int))
        representatives.append(r)
        aliases.extend(members[1:])
    if len(representatives) < 2*per_split:
        raise ValueError("Insufficient independent families")
    main, reserve = [], []
    for i, r in enumerate(representatives):
        split = ("discovery", "confirmation")[i % 2]
        r.update(split=split, selection_order=i, reserve=i >= 2*per_split)
        (reserve if r["reserve"] else main).append(r)
    main.sort(key=lambda r: (r["split"] != "discovery", r["selection_order"]))
    return dict(main=main, reserve=reserve, calibration_excluded_bases=excluded,
                alias_excluded_bases=aliases, groups=list(groups.values()),
                grouping_scope="Connected components of known base/family, exact/rescaled pixels, numeric-normalized question, and available template label; not a claim to exhaustive semantic deduplication.")
