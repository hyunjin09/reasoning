import pytest

from visual_reasoning.stage8a.cohort import freeze_cohort


def row(i, **kw):
    return dict(base_id=str(i), family_id=f"base_{i}", question=f"unique word {chr(65+i)}",
                decoded_image_sha256=f"pixels_{i}", rescaled_identity_sha256=f"scaled_{i}",
                template=None, **kw)


def test_transitive_image_question_aliases_cannot_leak_from_calibration():
    rows = [row(i) for i in range(9)]
    rows[1]["decoded_image_sha256"] = rows[0]["decoded_image_sha256"]
    rows[2]["question"] = rows[1]["question"]
    result = freeze_cohort(rows, [str(i) for i in range(9)], ["0"], per_split=2)
    assert result["calibration_excluded_bases"] == ["0", "1", "2"]
    assert not ({"0", "1", "2"} & {r["base_id"] for r in result["main"]})


def test_balanced_family_disjoint_splits_and_fixed_reserve_without_effects():
    rows = [row(i) for i in range(12)]
    rows[1]["template"] = rows[2]["template"] = "shared_conservative_template"
    order = [str(i) for i in range(12)]
    a = freeze_cohort(rows, order, ["0"], per_split=3)
    assert a == freeze_cohort(rows, order, ["0"], per_split=3)
    assert [r["split"] for r in a["main"]] == ["discovery"]*3+["confirmation"]*3
    chosen = a["main"] + a["reserve"]
    assert len({r["family_id"] for r in chosen}) == len(chosen)
    assert not {r["base_id"] for r in a["main"]} & {r["base_id"] for r in a["reserve"]}
    assert len(a["alias_excluded_bases"]) == 1


def test_insufficient_independent_families_and_incomplete_order_fail():
    rows = [row(i) for i in range(5)]
    with pytest.raises(ValueError, match="independent"):
        freeze_cohort(rows, [str(i) for i in range(5)], ["0"], per_split=3)
    with pytest.raises(ValueError, match="order"):
        freeze_cohort(rows, ["0", "1"], ["0"], per_split=1)
