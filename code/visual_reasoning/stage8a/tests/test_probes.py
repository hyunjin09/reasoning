import numpy as np
import pytest

from visual_reasoning.stage8a.probes import operating_point, grouped_oof, columns


def test_operating_point_uses_strict_greater_than_and_meets_both_constraints():
    y = np.array([0]*5+[1]*5)
    labels = np.array(["M"]*5+["T"]*5)
    score = np.array([.1,.2,.3,.4,.5,.3,.6,.8,.9,.95])
    r = operating_point(y,labels,score)
    assert r["threshold"] == .4
    assert r["recall"] == .8 and r["mention_fpr"] == .2
    assert r["target_met"]
    bad = operating_point(y,labels,np.ones(10)*.5)
    assert not bad["target_met"] and bad["mention_fpr"] == 0


def test_oof_holds_out_whole_families_and_fit_statistics_exclude_test_outliers():
    events = []
    for family in range(10):
        for label in ("T","M"):
            events.append(dict(event_id=f"{family}_{label}",family_id=str(family),split="discovery",label=label,
                prefix_length=10000 if family==9 else 10+family,prompt_length=10))
    prediction,folds = grouped_oof(events,dict(kind="position",C=1.),folds=5)
    assert len(prediction) == len(events) and np.isfinite(prediction).all()
    for fold in folds:
        assert not set(fold["train_families"]) & set(fold["test_families"])
        if "9" in fold["test_families"]:
            assert max(fold["scaler_mean"]) < 4
    events[-1]["split"] = "confirmation"
    with pytest.raises(ValueError,match="discovery"):
        grouped_oof(events,dict(kind="position",C=1.),folds=5)


def test_sink_ablation_adds_only_sink_coordinates_to_the_selected_primary():
    # Adding all concentration/temporal coordinates to a joint primary would
    # confound the intended incremental sink comparison.
    for kind in ("joint", "extended"):
        baseline = columns(dict(kind=kind))
        augmented = columns(dict(kind="sink_secondary", base_kind=kind))
        assert augmented[:len(baseline)] == baseline
        assert set(augmented) - set(baseline) == {"sink_mass", "delta_sink_mass"}
