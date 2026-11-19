import unittest
from scripts.stage14a.history_v2 import identities, artifact_kind

class HistoricalIdentityRepair(unittest.TestCase):
    def test_explicit_family_namespace_overrides_stage_default(self):
        x={'family_id':'mathverse_family_102','item_id':'102','generated_token_ids':[42,13]}
        self.assertEqual(identities(x,{},'mathvision'),{'mathvision':set(),'mathverse':{'102'}})
    def test_trajectory_and_base_ids_without_dataset_tag(self):
        x=[{'trajectory_id':'mathverse_216'},{'base_id':'mathverse_673__intact'}]
        self.assertEqual(identities(x,{}),{'mathvision':set(),'mathverse':{'216','673'}})
    def test_only_identity_fields_not_answers_or_numbers(self):
        x={'trajectory_id':'mathvision_475','answer':'mathverse_102','output_text':'mathvision_202','tokens':[{'token_id':1,'decoded_token':'mathverse_9'}]}
        self.assertEqual(identities(x,{}),{'mathvision':{'475'},'mathverse':set()})
    def test_source_image_identity_and_legacy_family(self):
        x=[{'image':'/data/dataset/MathVerse/images/images_version_5/image_265.png'}, {'family_id':'old_visual_family'}]
        self.assertEqual(identities(x,{'old_visual_family':['17','18']}),{'mathvision':{'17','18'},'mathverse':{'265'}})
    def test_source_adjudication_is_not_outcome_review(self):
        self.assertEqual(artifact_kind('outputs/stage11a/v1/audit/e_star_adjudication.json'),'SOURCE_OR_DESIGN_ARTIFACT')
        self.assertEqual(artifact_kind('outputs/stage10b/v1/packets/mathverse_102.json'),'TRACE_REVIEW_ARTIFACT')

if __name__=='__main__':unittest.main()
