import numpy as np
import pytest
import torch

from visual_reasoning.stage8a.instrumentation import passive_statistics
from visual_reasoning.stage8b.passive import FEATURE_KEYS, passive_tensor, episode_summary, frozen_scores


def test_streaming_features_equal_stage8a_and_do_not_change_inputs():
    g = torch.Generator().manual_seed(7)
    scores = torch.randn(16, 23, generator=g)
    weights = scores.softmax(-1)
    before = (scores.clone(), weights.clone())
    visual = [2, 3, 4, 5, 6]
    expected = passive_statistics(scores, weights, visual=visual, reasoning=list(range(19, 23)))
    actual = passive_tensor(scores, weights, visual=visual, prompt_length=19)
    for i, key in enumerate(FEATURE_KEYS):
        assert torch.equal(actual[:, i], torch.tensor(expected[key])), key
    assert torch.equal(scores, before[0]) and torch.equal(weights, before[1])


def test_first_prediction_is_unavailable_without_reasoning_competitor():
    scores = torch.zeros(2, 6)
    values = passive_tensor(scores, scores.softmax(-1), visual=[1, 2], prompt_length=6)
    assert torch.isnan(values[:, FEATURE_KEYS.index('qk_visual_reasoning')]).all()


def test_episode_count_is_not_active_token_count_and_boundary_is_strict():
    r = episode_summary(np.array([np.nan, .5, .7, .8, .5, .9]), threshold=.5)
    assert r['active_tokens'] == 3 and r['episode_onsets'] == [2, 5]
    assert r['episodes'] == 2 and r['valid_score_tokens'] == 5
    assert r['intervals'] == [3]
    assert episode_summary(np.array([np.nan,.1]),threshold=.5)['first_retrieval'] is None


def test_frozen_predictor_rejects_wrong_feature_order_and_preserves_missing():
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    x=np.array([[.1,-3,-2],[.2,-2,-1],[.6,1,2],[.8,2,3]])
    model=Pipeline([('scale',StandardScaler()),('logistic',LogisticRegression())]).fit(x,[0,0,1,1])
    features=np.zeros((5,len(FEATURE_KEYS)))
    features[1:,:3]=x
    features[0,:3]=np.nan
    score=frozen_scores(features,model,FEATURE_KEYS)
    assert np.isnan(score[0])
    np.testing.assert_array_equal(score[1:],model.predict_proba(x)[:,1])
    with pytest.raises(ValueError,match='feature'):
        frozen_scores(features,model,list(reversed(FEATURE_KEYS)))
