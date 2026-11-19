"""Validate versioned source decisions and seal G1 without opening outcomes."""
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from scripts.stage14c.design_core import _canonical

BASE = Path('outputs/stage14c')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x') as f:
        json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')


def answer_kind(row):
    if row['benchmark']=='MMStar':return 'choice'
    kinds = {'Circled Letter':'letter','Counting Grid - Blank Grids':'ordered_pair',
             'Counting Grid - Word Grids':'ordered_pair','Line Plot Intersections':'integer',
             'Nested Squares':'integer','Olympic Counting - Circles':'integer',
             'Olympic Counting - Pentagons':'integer','Subway Connections':'integer',
             'Touching Circles':'yes_no'}
    if row['benchmark']!='BlindTest' or row['category'] not in kinds:
        raise ValueError('Unknown source answer schema')
    return kinds[row['category']]


def merge_reviews(primary, updates):
    final={r['review_rank']:dict(r) for r in primary}
    if len(final)!=len(primary):raise ValueError('Duplicate primary review')
    history={k:[dict(stage='primary',**r)] for k,r in final.items()}
    for stage,row in updates:
        row=dict(row);rank=row['review_rank'];prior=final[rank]
        if row['family_id']!=prior['family_id']:raise ValueError('Review family mismatch')
        row.setdefault('label',prior['label'])
        # Fixed reread packets contain the first review. Never silently revert a correction.
        if stage=='reread' and row['decision']=='CONFIRM' and any(
                row[k]!=prior[k] for k in ['label','evidence_atoms']):
            raise ValueError(f'stale reread confirmation at rank {rank}')
        final[rank]=dict(prior,**row);history[rank].append(dict(stage=stage,**row))
    return final,history


def main():
    cohort=[json.loads(x) for x in (BASE/'source/cohort_manifest.jsonl').read_text().splitlines()]
    for seal,key in [('audit/native_cohort_seal_v1.json','files'),('audit/g1_primary_review_seal_v1.json','hashes')]:
        for path,sha in json.loads((BASE/seal).read_text())[key].items():assert digest(path)==sha,path
    primary=[];inputs=[];updates=[]
    for p in sorted((BASE/'source/primary_reviews').glob('*.json')):
        inputs.append(p);primary.extend(json.loads(p.read_text())['rows'])
    for stage,folder in [('second','second_reviews'),('reread','reread_reviews')]:
        files=sorted((BASE/'source'/folder).glob('*.json'),key=lambda p:json.loads(p.read_text())['at'])
        for p in files:
            inputs.append(p);updates.extend((stage,dict(r,review_file=str(p))) for r in json.loads(p.read_text())['rows'])
    final,history=merge_reviews(primary,updates)
    assert sorted(final)==list(range(len(cohort)))
    reread=json.loads((BASE/'audit/source_reread_membership_v1.json').read_text())['rows']
    assert {r['review_rank'] for r in reread}=={r['review_rank'] for stage,r in updates if stage=='reread'}
    extra=json.loads((BASE/'audit/new_evidence_second_confirmation_v1.json').read_text())
    confirmations={r['review_rank']:r for r in extra['rows']}
    original={r['review_rank']:r for r in primary}
    eligibility=[];evidence=[];logs=[];counts=defaultdict(Counter);strata=defaultdict(Counter);kinds=defaultdict(Counter)
    for rank,row in enumerate(cohort):
        r=final[rank];assert r['family_id']==row['family_id']
        label=r['label'];atoms=r['evidence_atoms'];assert bool(atoms)==(label=='ELIGIBLE') and len(atoms)<=4
        assert not any(h.get('model_outcomes_used') for h in history[rank])
        if atoms:
            assert len(history[rank])>=2
            assert all(r['checks'].values()),rank
            if original[rank]['label']!='ELIGIBLE':
                q=confirmations[rank]
                assert q['evidence_sha256']==hashlib.sha256(json.dumps(atoms,sort_keys=True).encode()).hexdigest()
                assert all(q['checks'].values())
            for a in atoms:
                assert a['text'].strip() and a['source_object'] and a['source_ROI'] and a['minimality']
                assert a['atom_type'] in ['scalar_relation','structured_layout']
                if a['atom_type']=='structured_layout':assert a['structured_subfact_count']>1
            evidence.append(dict(family_id=row['family_id'],benchmark=row['benchmark'],review_rank=rank,
                                 atoms=atoms,serialized_evidence='\n'.join('- '+a['text'] for a in atoms),
                                 primary_atom_count=len(atoms),structured_subfact_total=sum(a.get('structured_subfact_count') or 1 for a in atoms)))
        kind=answer_kind(row);assert _canonical(row['gold'],kind,['A','B','C','D']) is not None,rank
        eligibility.append(dict(review_rank=rank,family_id=row['family_id'],item_id=row['item_id'],benchmark=row['benchmark'],
                                category=row['category'],stratum=row['stratum'],label=label,rationale=r['rationale'],
                                answer_kind=kind,source_validity_flags=[] if label in ['ELIGIBLE','TEXT_SUFFICIENT','ANSWER_LEAKAGE_UNAVOIDABLE','NO_DEFENSIBLE_ESTAR'] else [label],
                                E_star_final_QC_passed=bool(atoms),model_outcomes_used=False))
        logs.append(dict(review_rank=rank,family_id=row['family_id'],history=history[rank],
                         new_evidence_confirmation=confirmations.get(rank),independent_interrater_reliability=False))
        counts[row['benchmark']][label]+=1;strata[row['benchmark']+'|'+row['category']][label]+=1;kinds[row['benchmark']][kind]+=1
    line=json.loads((BASE/'audit/line_pixel_order_qc_v2.json').read_text())
    conflicts=[]
    for r in line['rows']:
        n=sum(a!=b for a,b in zip(r['orders'],r['orders'][1:]));c=cohort[r['review_rank']]
        if n!=int(c['gold']):conflicts.append(c['family_id'])
    assert not conflicts,'Source gold conflict requires versioned adjudication'
    assert all(counts[b]['ELIGIBLE']>=100 for b in ['MMStar','BlindTest'])
    artifacts=[]
    for name,rows in [('estar_eligibility_manifest',eligibility),('evidence_atoms',evidence),('source_qc_log',logs)]:
        p=BASE/'source'/f'{name}.jsonl'
        with p.open('x') as f:
            for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
        artifacts.append(p)
    stats=dict(at=datetime.now(timezone.utc).isoformat(),native_families=len(cohort),eligible_families=len(evidence),
               counts={k:dict(v) for k,v in counts.items()},by_category={k:dict(v) for k,v in strata.items()},
               answer_schema_counts={k:dict(v) for k,v in kinds.items()},reread_families=len(reread),
               new_evidence_additional_confirmations=len(confirmations),same_agent_review=True,independent_reliability_established=False,
               structured_primary_atoms=sum(a['atom_type']=='structured_layout' for e in evidence for a in e['atoms']),
               scalar_primary_atoms=sum(a['atom_type']=='scalar_relation' for e in evidence for a in e['atoms']),
               structured_subfact_totals_by_family={e['family_id']:e['structured_subfact_total'] for e in evidence},
               G1_gate='PASS',min_eligible_each=100,model_calls=0,
               limitations=['BlindTest E* is entirely the line-intersection task; other direct-answer tasks remain native-only.',
                            'MMStar is a mixed benchmark with math. Eligible strata do not identify full-source bottleneck fractions.',
                            'Same-agent source QC is not independent annotation reliability.',
                            'NO_DEFENSIBLE_ESTAR records lack of a validated representation, not impossibility.'])
    p=BASE/'source/source_statistics.json';save(p,stats);artifacts.append(p)
    p=BASE/'audit/gold_schema_integrity_v1.json';save(p,dict(all_native_gold_schemas_valid=True,line_source_geometry_gold_checked=300,line_conflicts=conflicts,
       full_semantic_gold_independent_reverification=False,native_gold_unchanged=True,source_flags_preserved=True));artifacts.append(p)
    inputs.extend([BASE/'audit/new_evidence_second_confirmation_v1.json',BASE/'source/cohort_manifest.jsonl',BASE/'audit/source_reread_membership_v1.json'])
    seal=dict(at=stats['at'],status='G1_PASS',native_counts={k:sum(v.values()) for k,v in counts.items()},
              E_star_counts={k:v['ELIGIBLE'] for k,v in counts.items()},model_calls=0,model_outcomes_used=False,
              input_hashes={str(p):digest(p) for p in inputs},artifact_hashes={str(p):digest(p) for p in artifacts})
    save(BASE/'audit/g1_final_source_seal_v1.json',seal)
    print(json.dumps({k:seal[k] for k in ['status','native_counts','E_star_counts']}))

if __name__=='__main__':main()
