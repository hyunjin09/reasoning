"""Finalize reviewed sources, temporal evidence, CF layouts and factorials once."""
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image
from transformers import AutoProcessor
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,sha
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage5a.annotation import temporal_annotation


def main():
    if (OUT/'cohort/cohort_freeze_complete.json').exists():raise RuntimeError('Already frozen')
    config=read_json(OUT/'config/stage5a_config.json')
    cf_ids=set(read_json(OUT/'audit/cf_feasibility_review.json')['feasible_base_ids'])
    decisions={(r['base'],r['source']):r for r in read_jsonl(OUT/'counterfactual_assets/manual_review.jsonl')}
    proposals={(r['base'],r['source']):r for r in read_jsonl(OUT/'counterfactual_assets/proposals.jsonl')}
    temporal=read_json(OUT/'cohort/review/temporal_review_ledger.json')
    controls=read_json(OUT/'cohort/review/irrelevant_control_review.json')
    by_control={(r['base'],tuple(r['local_positions'])):r for r in controls['nonwhite_group_reviews']}
    processor=AutoProcessor.from_pretrained(config['model_checkpoint'],local_files_only=True)
    dataset={str(r['sample_index']):r for r in load_mathverse_rows(Path(config['dataset_root']))}
    completed=[]
    for item in read_jsonl(OUT/'cohort/provisional_natural.jsonl'):
        path=ROOT/item['metadata_path'];m=read_json(path);base=m['base']
        if m.get('final_asset_review_complete'):
            completed.append(m);continue
        prep,native_meta=prepare_custom_image(processor,dataset[m['example_id']],Path(m['source_image']),device='cpu')
        for key in ('prompt_token_ids','visual_token_indices','image_grid_thw'):
            assert native_meta[key]==m['prompt_metadata'][key],(base,key)
        visual=m['prompt_metadata']['visual_token_indices'];maps={k:set(v) for k,v in m['roi_mapping'].items()}
        m['condition_source_edits']={'O':[]};m['cf_assets']={};m['factorial_conditions']={}
        if base in cf_ids:
            for source in m['facts']:
                key=(base,source)
                if not decisions.get(key,{}).get('passed'):continue
                p=proposals[key]
                assert p['sha256']==decisions[key]['image_sha256']
                for kind,short in [('semantic','C'),('sham','S')]:
                    name=f'{short}_{source}';image_path=ROOT/p['paths'][kind]
                    assert sha(image_path)==p['sha256'][kind]
                    inputs,observed=prepare_custom_image(processor,dataset[m['example_id']],image_path,device='cpu')
                    for field in ('prompt_token_ids','visual_token_indices','image_grid_thw'):
                        assert observed[field]==native_meta[field],(base,source,field)
                    changed=(inputs['pixel_values']!=prep['pixel_values']).any(dim=1)
                    assert len(changed)==len(visual)*4
                    touched=changed.reshape(len(visual),4).any(dim=1).nonzero().flatten().tolist()
                    maps[source].update(touched)
                    m['paths'][name]=p['paths'][kind];m['image_sha256'][name]=p['sha256'][kind]
                    m['condition_source_edits'][name]=[source]
                    del inputs
                m['cf_assets'][source]={'proposal':str((OUT/f'counterfactual_assets/{base}/{source}/proposal.json').relative_to(ROOT)),
                    'semantic_condition':f'C_{source}','sham_condition':f'S_{source}',
                    'manual_review':decisions[key],'edit_roi':p['audit']['edit_roi'],'layout_exact':True}
            pairs=set()
            for e in m['events']:
                if not e['cf_semantics_eligible'] or e['source'] not in m['cf_assets']:continue
                for role in ('X','M'):
                    others=e['source_identities'].get(role,[])
                    if len(others)==1 and others[0] in m['cf_assets'] and others[0]!=e['source']:
                        pairs.add(tuple(sorted([e['source'],others[0]])))
            original=np.asarray(Image.open(m['source_image']).convert('RGB'))
            for first,second in sorted(pairs):
                one=np.asarray(Image.open(ROOT/m['paths']['C_'+first]).convert('RGB'))
                two=np.asarray(Image.open(ROOT/m['paths']['C_'+second]).convert('RGB'))
                changed_one=np.any(one!=original,axis=2);changed_two=np.any(two!=original,axis=2)
                if np.any(changed_one & changed_two):continue
                combined=original.copy();combined[changed_one]=one[changed_one];combined[changed_two]=two[changed_two]
                name=f'J_{first}_{second}';image_path=OUT/'counterfactual_assets'/base/(name+'.png')
                Image.fromarray(combined).save(image_path)
                inputs,observed=prepare_custom_image(processor,dataset[m['example_id']],image_path,device='cpu')
                assert all(observed[k]==native_meta[k] for k in ('prompt_token_ids','visual_token_indices','image_grid_thw'))
                m['paths'][name]=str(image_path.relative_to(ROOT));m['image_sha256'][name]=sha(image_path)
                m['condition_source_edits'][name]=[first,second]
                m['factorial_conditions'][name]={'sources':[first,second],'outside_union_exact':bool(np.array_equal(combined[~(changed_one|changed_two)],original[~(changed_one|changed_two)])),
                                               'first_equals_independent':bool(np.array_equal(combined[changed_one],one[changed_one])),
                                               'second_equals_independent':bool(np.array_equal(combined[changed_two],two[changed_two]))}
                assert all(v for k,v in m['factorial_conditions'][name].items() if k!='sources')
                del inputs
        m['roi_mapping']={k:sorted(v) for k,v in maps.items()}
        m['source_mapping_method']+='; union with measured resized patch support for every accepted semantic/sham edit before freezing'
        for e in m['events']:
            if e['event_id'] in temporal:
                e['temporal_review']=temporal[e['event_id']]
                e.update(temporal_annotation(e,e['history_before_ed_text']))
            for role,identities in e['source_identities'].items():
                local=sorted(set().union(*(maps[k] for k in identities)))
                e['local_source_groups'][role]=local;e['source_groups'][role]=[visual[k] for k in local]
            groups=e['source_groups'];local=e['local_source_groups']
            if 'X' in groups and set(groups['X']) & set(groups['T']):
                e['source_overlap']['X_T_after_resize']=sorted(set(groups['X']) & set(groups['T']))
                e['excluded_source_groups']={'X':groups.pop('X')};local.pop('X')
            e['independent_source_contrasts']={k:not bool(set(groups[k]) & set(groups['T'])) for k in ('M','X') if k in groups}
            alternate=groups.get('X',groups.get('M'));alternate_local=local.get('X',local.get('M'))
            if alternate is not None:
                groups['joint']=sorted(set(groups['T'])|set(alternate));local['joint']=sorted(set(local['T'])|set(alternate_local))
            control=e.get('irrelevant_mapping',{});control_pass=False;reason='No frozen candidate control'
            if 'I' in groups:
                audit=by_control.get((base,tuple(local['I'])))
                control_pass=control.get('mean_darkness',1)<=1e-8 or bool(audit and audit['passed'])
                reason='Manual irrelevance not established' if not control_pass else 'validated background control'
                source_union=set().union(*(set(groups[k]) for k in ('T','M','X') if k in groups))
                if len(groups['I'])!=len(groups['T']) or set(groups['I']) & source_union:
                    control_pass=False;reason='Resized image-patch support changes control cardinality or independence'
                if not control_pass:
                    e['excluded_I_group']=groups.pop('I');e['excluded_I_local']=local.pop('I')
            e['irrelevant_control_validated']=control_pass;e['irrelevant_control_final_review']=reason
            e['cf_validated']=bool(base in cf_ids and e['cf_semantics_eligible'] and e['source'] in m['cf_assets'])
            e['cf_conditions']=[]
            if e['cf_validated']:
                s=e['source'];e['cf_conditions']=['O',f'C_{s}',f'S_{s}']
                for name,factor in m['factorial_conditions'].items():
                    if s in factor['sources']:
                        other=next(k for k in factor['sources'] if k!=s)
                        e['cf_conditions']+=['C_'+other,'S_'+other,name]
                e['cf_conditions']=list(dict.fromkeys(e['cf_conditions']))
            e['previous_source_roi']=next((role for role in ('X','M') if e.get('previous_source') in e['source_identities'].get(role,[]) and e['independent_source_contrasts'].get(role)),None)
            e['prior_groundtruth_availability']='unresolved; prior_explicit_availability records the source-associated native premise, not a guarantee of correct extraction'
        assert base not in cf_ids or any(e['cf_validated'] for e in m['events']),base
        m['cf_reviewed']=base in cf_ids;m['final_asset_review_complete']=True
        m['final_review_provenance']={str(p.relative_to(ROOT)):sha(p) for p in [OUT/'cohort/review/temporal_review_ledger.json',OUT/'cohort/review/irrelevant_control_review.json',OUT/'counterfactual_assets/manual_review.jsonl']}
        write_json(path,m);completed.append(m)
        print(f'finalized base={base} CF={base in cf_ids} conditions={len(m["paths"])}',flush=True)
        del prep
    atlas=[r for r in completed if r['atlas_selected']]
    write_json(OUT/'audit/final_asset_review.json',{'natural':len(completed),'atlas':len(atlas),'atlas_events':sum(len(r['events']) for r in atlas),
        'cf_bases':sum(r['cf_reviewed'] for r in atlas),'cf_events':sum(e['cf_validated'] for r in atlas for e in r['events']),
        'independent_I_events':sum(e['irrelevant_control_validated'] for r in atlas for e in r['events']),
        'temporal_resolved':dict(Counter(e['temporal_role'] for r in atlas for e in r['events'] if not e['temporal_unresolved'])),
        'temporal_unresolved':sum(e['temporal_unresolved'] for r in atlas for e in r['events']),
        'before_causal_scoring':True,'layout_exact':True,'counterfactual_minimum_met':sum(r['cf_reviewed'] for r in atlas)>=48})


if __name__=='__main__':main()
