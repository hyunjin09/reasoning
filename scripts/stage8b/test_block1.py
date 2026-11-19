import unittest
import numpy as np
from visual_reasoning.stage8b.block1_statistics import ItemBootstrap, joint_intervals


class Block1StatisticsTests(unittest.TestCase):
    def test_bootstrap_is_item_stratified_and_deterministic(self):
        g=np.array([0,0,0,1,1,1]);a=ItemBootstrap(g,resamples=32);b=ItemBootstrap(g,resamples=32)
        np.testing.assert_array_equal(a.weights,b.weights)
        np.testing.assert_array_equal(a.weights[:,:3].sum(1),3)
        raw,draws=a.raw([1,2,3,4,5,6])
        self.assertEqual(raw['mean_difference'],3)
        self.assertEqual(raw['group0']['median'],2)
        self.assertEqual(len(draws),32)

    def test_adjustment_recovers_known_coefficient_with_redundant_nuisance(self):
        g=np.tile([0,1],20);x=np.arange(40)/40
        y=7+3*g+4*x;d=np.column_stack([np.ones(40),x,x,np.zeros(40)])
        got,draws=ItemBootstrap(g,resamples=32).adjusted(y,d)
        self.assertAlmostEqual(got['coefficient'],3,places=9)
        np.testing.assert_allclose(draws,3,atol=1e-9)

    def test_confound_only_raw_difference_disappears(self):
        g=np.repeat([0,1],20);x=np.arange(40)/40;y=2+5*x
        engine=ItemBootstrap(g,resamples=32);raw,_=engine.raw(y)
        adjusted,_=engine.adjusted(y,np.column_stack([np.ones(40),x]))
        self.assertGreater(raw['mean_difference'],2)
        self.assertAlmostEqual(adjusted['coefficient'],0,places=9)

    def test_missing_is_not_zero_and_unidentified_effect_is_null(self):
        g=np.array([0,0,0,1,1,1]);engine=ItemBootstrap(g,resamples=32)
        raw,_=engine.raw([np.nan,2,4,6,8,np.nan])
        self.assertEqual(raw['group0']['mean'],3)
        self.assertEqual(raw['group0']['missing'],1)
        bad,_=engine.adjusted(np.arange(6),np.column_stack([np.ones(6),g]))
        self.assertFalse(bad['estimable'])

    def test_family_interval_handles_correlated_metrics(self):
        rng=np.random.default_rng(1);a=rng.normal(1,.1,4000)
        ci=joint_intervals({'a':dict(point=1,samples=a),'b':dict(point=2,samples=2*a)})
        np.testing.assert_allclose(np.array(ci['metrics']['a']['ci95_simultaneous'])*2,ci['metrics']['b']['ci95_simultaneous'])

    def test_interval_additions_and_matching_caliper(self):
        import pandas as pd
        from visual_reasoning.stage8b.block1_data import interval_additions,matched_pairs
        row=interval_additions(pd.DataFrame(dict(episode_index=[0,1,2,3],preceding_gap=[np.nan,8,40,80])))
        self.assertAlmostEqual(row['short_gap_fraction'],1/3)
        expected=(np.std([8,40,80])-np.mean([8,40,80]))/(np.std([8,40,80])+np.mean([8,40,80]))
        self.assertAlmostEqual(row['burstiness'],expected)
        short=interval_additions(pd.DataFrame(dict(episode_index=[0,1],preceding_gap=[np.nan,10])))
        self.assertTrue(np.isnan(short['burstiness']))
        f=pd.DataFrame(dict(item_id=['a','b','c','d'],order=range(4),benchmark_label=['correct','correct','wrong','wrong'],
            completion='normal completed',subject_group='algebra',answer_format='open',
            reasoning_tokens=[100,200,110,10000],log_question_length=3.))
        pairs=matched_pairs(f);self.assertEqual(len(pairs),1)
        self.assertEqual((pairs[0]['correct_id'],pairs[0]['wrong_id']),('a','c'))


if __name__=='__main__':unittest.main()
