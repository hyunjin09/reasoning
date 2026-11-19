"""Focused CPU checks for scientific bookkeeping and missing-data boundaries."""
import unittest
import numpy as np
from visual_reasoning.stage8b.block0 import episodes, review_indices, phase, geometry, completion, trajectory_metrics, phase_metrics
from visual_reasoning.stage8b.transfer import reasoning_length


class Block0Tests(unittest.TestCase):
    def test_gap_is_intervening_inactive_tokens(self):
        r = np.array([.8, .1, .1, .1, .1, .9, .1, .1, .1, .1, .1, .8])
        self.assertEqual([(e['start_token'], e['end_token']) for e in episodes(r, 4)], [(0, 5), (11, 11)])
        self.assertEqual(len(episodes(r, 0)), 3)
        self.assertEqual(len(episodes(r, 8)), 1)
        e = episodes(r, 4)[0]
        self.assertEqual(e['duration'], 6)
        self.assertEqual(e['following_gap'], 5)
        self.assertEqual(e['active_tokens'], 2)

    def test_missing_never_bridges(self):
        self.assertEqual(len(episodes([np.nan, .8, np.nan, .9], 4)), 2)
        self.assertEqual(episodes([np.nan, .1], 4), [])

    def test_coordinates_and_scope(self):
        self.assertEqual(phase([0, .2499, .25, .5, .75, 1]).tolist(), [1, 1, 2, 3, 4, 4])
        self.assertEqual(reasoning_length(['a', 'b', '</think>', 'c']), 2)
        self.assertEqual(reasoning_length(['a', 'b']), 2)

    def test_membership_is_temporal_only(self):
        rows = [{'normalized_midpoint': p} for p in [.1, .25, .75, .9]]
        self.assertEqual(review_indices(rows), [0, 1, 3])
        self.assertEqual(review_indices(rows[:3]), [0, 1, 2])
        self.assertEqual(review_indices([]), [])

    def test_geometry_missing_and_closed_path(self):
        g, d = geometry([[np.nan, 0], [0, 0], [3, 4], [0, 0]])
        self.assertEqual(g['path_length'], 10)
        self.assertEqual(g['valid_transitions'], 2)
        self.assertEqual(g['net_displacement'], 0)
        self.assertEqual(g['first_valid_token'], 1)
        self.assertEqual(g['tortuosity'], 1e13)
        self.assertTrue(np.isnan(d[0]))
        h, _ = geometry([[0, 0], [np.nan, 1], [3, 4]])
        self.assertIsNone(h['path_length'])
        self.assertEqual(h['net_displacement'], 5)

    def test_cap_priority_is_independent_of_answer(self):
        r = dict(at_length_cap=True, normal_eos=False, completion='other abnormal stop', tokens=40960)
        self.assertEqual(completion(r, 'a</think>42')['completion'], 'capped')
        self.assertEqual(completion(r, 'a')['abnormal_stop_subtype'], 'cap_without_think')

    def test_episode_density_and_phase_accounting(self):
        import pandas as pd
        scores = np.array([np.nan, .8, .1, .1, .1, .1, .1, .9])
        es = episodes(scores, 4)
        m = trajectory_metrics(scores, es, generated_tokens=10, post_think_tokens=1)
        self.assertEqual(m['retrieval_density'], 250)
        self.assertEqual(m['active_token_fraction'], .25)
        self.assertEqual(m['late_episode_fraction_gt_0.75'], .5)
        table = pd.DataFrame(dict(phase=phase(np.arange(8)/8), R=scores,
            active_retrieval=scores > .5478025980771918, qk_visual_nonvisual=0.,
            visual_mass=1., visual_concentration=.5))
        rows = phase_metrics(table, es, {'raw':np.array([np.nan,1,1,1,1,1,1])})
        self.assertEqual(sum(r['token_count'] for r in rows), 8)
        self.assertEqual(sum(r['retrieval_episode_count'] for r in rows), 2)
        self.assertEqual(sum(r['raw_movement_transitions'] for r in rows), 3)


if __name__ == '__main__':
    unittest.main()
