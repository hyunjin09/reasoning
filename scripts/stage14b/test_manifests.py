import unittest
from collections import Counter
from scripts.stage14b.common import *
from scripts.stage14b.protocol import VERSIONS

class FrozenManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main=all_tasks('main');cls.confirm=all_tasks('confirmatory');cls.pre=all_tasks('preflight')
    def test_all_native_ids_and_unique_calls(self):
        self.assertEqual(len(self.main),17536)
        self.assertEqual(len({t['task_id'] for t in self.main+self.confirm+self.pre}),27160)
        native=[t for t in self.main if t['phase']=='native']
        self.assertEqual(Counter(t['model_key'] for t in native),{'I':3040,'T':3040})
        self.assertEqual(len({t['item_id'] for t in native}),3040)
    def test_evidence_is_exact_image_free_and_paired(self):
        expected={r['item_id']:r['text'] for r in stage14a('mathvision_equal_evidence_renderings')['rows']}
        rows=[t for t in self.main if t['phase']=='equal']
        self.assertEqual(len(rows),2000)
        for t in rows:
            self.assertIsNone(t['image']);self.assertEqual(t['prompt'],expected[t['item_id']])
        pairs={}
        for t in self.main:pairs.setdefault((t['identity'],t['condition'],t['replicate']),[]).append(t)
        for pair in pairs.values():
            self.assertEqual(len(pair),2)
            self.assertEqual(pair[0]['prompt'],pair[1]['prompt']);self.assertEqual(pair[0]['seed'],pair[1]['seed'])
    def test_native_mathverse_prompts_and_modality(self):
        expected={(r['family_id'],r['version']):r for r in stage14a('mathverse_variant_mapping')['rows']}
        for t in self.main:
            if t['phase']!='mathverse':continue
            r=expected[t['family_id'],t['source_version']]
            self.assertEqual(t['prompt'],r['query_wo'])
            self.assertEqual(bool(t['image']),t['source_version']!='Text Only')
    def test_confirm_only_frozen_subsets_new_seeds(self):
        mv={r['item_id'] for r in stage14a('mathvision_confirm300_manifest')['rows']}
        verse={r['family_id'] for r in stage14a('mathverse_confirm300_manifest')['rows']}
        self.assertEqual(len(self.confirm),9600)
        self.assertEqual({t['replicate'] for t in self.confirm},{1,2})
        for t in self.confirm:
            self.assertTrue(t['item_id'] in mv if t['identity'].startswith('mv:') else t['family_id'] in verse)
    def test_clean_layer_is_source_only(self):
        self.assertEqual(len(load(ROOT/'audit/source_clean_layer.json')['clean_families']),350)
        self.assertFalse(load(ROOT/'audit/technical_selection.json')['model_outcomes_used'])

if __name__=='__main__':unittest.main()
