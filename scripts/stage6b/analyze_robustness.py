"""Frozen C1 contrasts across datasets and post-label correctness strata."""
from collections import Counter
from scripts.stage6b.common import OUT,SOURCE,read_json,read_jsonl,write_json
from scripts.stage6b.analyze_c1 import grouped,statistics


def safe_stats(bases,rule):
    return {'bases':len(bases),'statistics':statistics(bases,rule) if bases else {},
        'small_group_warning':'Robustness requires the full frozen rule; low cluster count is not cured by treating conditions/spans as independent.'}


def main():
    rows=read_jsonl(OUT/'c1_mirage/fixed_prefix_scores.jsonl');bases=grouped(rows)
    rule=read_json(OUT/'config/mirage_discovery_rule.json')
    datasets=sorted({r['dataset'] for r in rows});output={}
    for split in ['discovery','confirmation']:
        selected={b:c for b,c in bases.items() if c['intact']['split']==split}
        output[split]={'by_dataset':{d:safe_stats({b:c for b,c in selected.items() if c['intact']['dataset']==d},rule) for d in datasets},
            'leave_one_dataset_out':{d:safe_stats({b:c for b,c in selected.items() if c['intact']['dataset']!=d},rule) for d in datasets}}
    write_json(OUT/'analysis/dataset_robustness.json',{'C1':output,'thresholds_refit':False,
        'interpretation':'Dataset and leave-one-out results use the same discovery feature scales and full33contrast Holm family. Inspect independent source-group counts; do not declare broad support from pooled significance alone.'})
    entries={r['base_id']:r for r in read_jsonl(OUT/'c1_mirage/fixed_prefix_manifest.jsonl') if r['condition']=='intact'}
    finals={r['event_id']:r for r in read_jsonl(SOURCE/'traces/controlled_final_correctness.jsonl')}
    strata={}
    for split in ['discovery','confirmation']:
        selected={b:c for b,c in bases.items() if c['intact']['split']==split}
        kinds={'locally_correct':lambda b:entries[b]['event']['reviewed_claim']['local_visual_correctness']=='CORRECT',
            'locally_incorrect':lambda b:entries[b]['event']['reviewed_claim']['local_visual_correctness'].startswith('INCORRECT'),
            'final_correct':lambda b:finals[entries[b]['event_id']]['final_answer_correctness']=='CORRECT',
            'final_incorrect':lambda b:finals[entries[b]['event_id']]['final_answer_correctness']=='INCORRECT'}
        strata[split]={name:safe_stats({b:c for b,c in selected.items() if predicate(b)},rule) for name,predicate in kinds.items()}
    write_json(OUT/'analysis/correctness_stratification.json',{'C1_intact_native_prefix_strata':strata,
        'selection_order':'Strict causal/mirage labels and numerical rules were frozen before correctness stratification.',
        'correctness_limit':'Native intact local geometry and final correctness stratify bases; fixed-prefix stressed candidate preference is a separate output, not a native generated hallucination.',
        'dynamic_correctness_reference':'c1_dynamics/correctness_association.json'})
    source_meta=[r['row'].get('metadata',{}) for r in entries.values()]
    template_keys=sorted({k for m in source_meta for k in m if 'template' in k.lower()})
    write_json(OUT/'analysis/template_robustness.json',{'status':'NOT_IDENTIFIABLE_FROM_FROZEN_METADATA','explicit_template_keys':template_keys,
        'template_family_labels_available':False,'source_group_clustering_already_used':True,
        'metadata_keys_by_dataset':{d:sorted({k for e in entries.values() if e['dataset']==d for k in e['row'].get('metadata',{})}) for d in datasets},
        'reason':'Frozen source metadata supplies dataset/source/subject categories, not validated prompt/diagram template-family IDs. Do not invent template clusters after effects are known; leave-one-template-family inference is unavailable.'})
    print('C1dataset/leave-one-out and post-label correctness strata saved; exact template labels unavailable.')


if __name__=='__main__':main()
