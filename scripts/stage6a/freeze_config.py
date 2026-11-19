from datetime import datetime, timezone
import json
from scripts.stage6a.inventory import ROOT, OUT, sha


def main():
    old=json.loads((ROOT/'outputs/stage5a/config/stage5a_config.json').read_text())
    plan=ROOT/'plan/stage6a_dedicated_alignment_mirage_retrieval_dynamics_cohort_plan.md'
    configs={
      'stage6a_config':dict(frozen_at=datetime.now(timezone.utc).isoformat(),source_plan=str(plan.relative_to(ROOT)),source_plan_sha256=sha(plan),
          model_checkpoint=old['model_checkpoint'],locked_generation_protocol=old['locked_generation_protocol'],
          runtime={**old['runtime'],'slurm_allocation':'109385','node':'node03'},
          native_execution='unchanged cached generate_once; streaming replay <=2048 with allocator release',
          scope='cohort construction and minimum diagnostics only',no_full_causal_analysis=True,no_pca=True,no_rescue=True),
      'dataset_priority':dict(order=['MathVerse','MathVision','MathVista','DocVQA','POPE','COCO2014','COCO2017','GQA'],
          selected_coco='COCO2014 val2014',downloads=False,external_roots_read_only=True),
      'cohort_rules':dict(seed=60971,C1=dict(target=120,minimum=90,preferred_per_dataset=40,minimum_per_available_stratum=24,min_cf_and_mask=72,min_mean_conditions=3),
          C2=dict(target_families=32,cells_per_family=4,target_per_cell=32,min_per_cell=24,min_events=96),
          C3=dict(target_families=160,minimum=120,target_present=80,target_absent=80,min_present_occlusion=50,min_absent=50),
          C4=dict(seed=60974,initial=600,ceiling=1000,case_control_target_each=100,case_control_min_each=60),
          membership_allowed=['dataset identity','semantic validity','ground truth','ROI editability','prompt validity','native interpretability'],
          membership_forbidden=['attention','VSD','counterfactual effect magnitude','QK','alphaV','sink','confidence','PCA','trajectory geometry'],
          correctness_selection='C4 separate explicitly balanced atlas only',mechanics_families=12,pilot_families=24),
      'split_rules':dict(seed=60972,discovery_fraction=1/3,confirmation_fraction=2/3,
          group_keys=['underlying image identity','exact decoded hash','perceptual duplicate group','question/template family'],
          mechanics_and_pilot='excluded from fresh confirmation',historical='separate; excluded from fresh confirmation',
          future_pca='fit all centering/scaling/bases on discovery only; no fitting in Stage6A'),
      'prompt_factorial_rules':dict(cells={'AR':[True,True],'A_only':[True,False],'R_only':[False,True],'Neither':[False,False]},
          axes=['semantic alignment to focal ROI','demand for focal ROI'],same_image_preferred=True,
          other_needed_source_explicit=True,natural_wording=True,author_before_generation=True,
          unmatched_properties_must_be_recorded=['length','difficulty','answer length','reasoning depth']),
      'stress_condition_rules':dict(C1=['intact','counterfactual','mild','strong','mask','sham_mild','sham_strong','sham_mask','aligned_distractor_if_valid','unrelated','no_image'],
          C3=['intact','strong','mask','sham','unrelated','no_image'],
          preserve_image_dimensions=True,preserve_non_target_geometry=True,
          c1_mask_scope='target numeric/text detail, not entire entity',
          sham='same mask shape/area/operation at reviewed irrelevant background',
          no_image='text-only chat without visual placeholders',unrelated='fresh image prefill, no donor KV reuse'),
      'trace_segmentation_rules':dict(priority=['newline thinking step','sentence','semicolon or major clause'],
          offsets='zero-based half-open native token indices plus exact decoded character offsets',
          unicode='incremental native decoding; no retokenization',attention_independent=True,
          final_answer_separate=True),
      'annotation_ontology':dict(demand=['demanded_sources','mentioned_sources','previous_demand','demand_changed','prior_explicit_access','first_reuse_refresh','unresolved'],
          correctness=['local_visual_correctness','local_reasoning_correctness','final_answer_correctness','object_hallucination_presence'],
          hallucination='absent COCO-category claims with frozen synonym normalization; attributes/relations separate',
          future_anchors=['demand_transition','matched_no_transition','wrong_claim','refresh','stress_high_risk'],
          dynamics_phenotypes='prospective semantic candidates only; no causal classification in Stage6A')}
    for name,data in configs.items():
        p=OUT/'config'/f'{name}.json'
        if p.exists():raise FileExistsError(p)
        p.write_text(json.dumps(data,indent=2)+'\n')
    print('Frozen eight Stage6A configuration files.')


if __name__=='__main__':main()
