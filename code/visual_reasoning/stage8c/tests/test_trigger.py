import numpy as np
from visual_reasoning.stage8b.block0 import episodes
from visual_reasoning.stage8c.trigger import OnlineEpisodes, TAU


def test_gap_four_and_missing_are_exact_offline_equivalent():
    scores = [np.nan, .9, *([.1]*4), .9, *([.1]*5), .9, np.nan, .9, TAU, .9]
    online = OnlineEpisodes()
    observed = [i for i, score in enumerate(scores) if online.step(score)]
    assert observed == [r['start_token'] for r in episodes(scores, 4)] == [1, 12, 14]


def test_streaming_prefix_does_not_need_future():
    rng = np.random.default_rng(13)
    scores = rng.random(200)
    scores[[0, 51, 100]] = np.nan
    online = OnlineEpisodes()
    seen = []
    for i, score in enumerate(scores):
        if online.step(score):
            seen.append(i)
        assert seen == [r['start_token'] for r in episodes(scores[:i+1], 4)]
