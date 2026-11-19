"""Identity-only historical inventory. No correctness or generated-text projection."""
import re
import subprocess
from collections import defaultdict
import pyarrow.parquet as pq
from scripts.stage14a.common import ROOT, Path, load, save, sha, now

ID_KEYS={'item_id','source_item_id','mathvision_id','problem_id','problem_index','family_id','source_family_id'}
ID_LISTS={'item_ids','source_item_ids','mathvision_ids','family_ids','selected_ids','technical_ids'}
TAGS={'dataset','benchmark','source_dataset','image','image_path','original_image','source_image'}


def identities(data, mv_families, context=None):
    found={'mathvision':set(),'mathverse':set()}
    def walk(x,ctx):
        if isinstance(x,list):
            for v in x:
                if isinstance(v,(dict,list)): walk(v,ctx)
        elif isinstance(x,dict):
            for k in TAGS:
                v=x.get(k)
                if isinstance(v,str):
                    if 'mathverse' in v.lower(): ctx='mathverse'
                    elif any(z in v.lower() for z in ['mathvision','math_vision','math-vision']): ctx='mathvision'
            for k in ID_KEYS:
                v=x.get(k)
                if not isinstance(v,(str,int)):continue
                s=str(v)
                if s in mv_families:found['mathvision'].update(mv_families[s])
                if s.startswith('mathvision:'):s=s.split(':')[-1];found['mathvision'].add(s)
                elif s.startswith('mathverse:'):s=s.split(':')[-1];found['mathverse'].add(s)
                elif ctx and s.isdigit():found[ctx].add(s)
            for k,v in x.items():
                if k in ID_LISTS and isinstance(v,list) and ctx:
                    found[ctx].update(str(z) for z in v if isinstance(z,(int,str)) and str(z).isdigit())
                elif isinstance(v,(dict,list)):walk(v,ctx)
    walk(data,context)
    return found


def kind(path):
    p=path.lower()
    if any(x in p for x in ['first_score','second_review','adjudicat','scoring','results.parquet','reviewed','review_labels']):
        return 'OUTCOME_INSPECTION_ARTIFACT'
    if any(x in p for x in ['technical','sanity','validation','calibration']):return 'TECHNICAL_ARTIFACT'
    if any(x in p for x in ['/native/','/raw/','/generations/','/generation/','/responses/','/calls/']):return 'GENERATION_ARTIFACT'
    if any(x in p for x in ['census_manifest','family_manifest','inventory','candidate','historical','exclusion_manifest']):return 'SOURCE_CATALOG'
    if any(x in p for x in ['source','annotation','e_star','oracle','eligib','cohort','manifest','selection']):return 'SOURCE_OR_DESIGN_ARTIFACT'
    return 'OTHER_IDENTITY_ARTIFACT'


def main():
    census=load(ROOT/'audit/mathvision_census_source_snapshot.json')
    fam={r['family_id']:r['member_item_ids'] for r in census['aliases']}
    mv_ids={r['item_id'] for r in census['rows']}
    verse=load(ROOT/'audit/mathverse_mapping_source_snapshot.json')
    verse_ids={r['problem_index'] for r in verse['families']}
    old={r['path']:r for r in load('outputs/stage12xs/v1/audit/historical_manifest_scan.json')['rows']}
    paths=subprocess.check_output(['rg','--files','--hidden','outputs','reports','runs'],text=True).splitlines()
    paths=sorted(p for p in paths if 'stage14a' not in p)
    records=[]; failures=[]
    for name in paths:
        p=Path(name)
        if p.suffix not in {'.json','.jsonl','.parquet','.md'}:continue
        stage=re.search(r'stage[0-9]+[a-z0-9_]*',name.lower())
        stage=stage.group() if stage else 'unclassified'
        ctx='mathvision' if re.match(r'stage(?:9|10|11|12|13)',stage) else None
        # Broad prior source manifests include multiple benchmarks: explicit tags override context.
        ids={'mathvision':set(),'mathverse':set()}
        try:
            if name in old and sha(p)==old[name]['sha256']:
                ids['mathvision'].update(old[name]['identified_mathvision_ids'])
                if p.suffix=='.json':
                    ids['mathverse'].update(identities(load(p),fam,None)['mathverse'])
                method='reused_hash_verified_identity_scan'
            elif p.suffix=='.parquet':
                f=pq.ParquetFile(p); cols=[k for k in f.schema.names if k in ID_KEYS|TAGS|ID_LISTS]
                ids=identities(f.read(columns=cols).to_pylist(),fam,ctx);method='identity_column_projection'
            elif p.suffix in {'.json','.jsonl'}:
                if p.suffix=='.json': ids=identities(load(p),fam,ctx)
                else:
                    with p.open() as f:
                        for line in f:
                            if line.strip():
                                z=identities(__import__('json').loads(line),fam,ctx)
                                for ds in ids:ids[ds].update(z[ds])
                method='identity_keys_only'
            else:
                # Explicit source references only, not generic numbers or correctness text.
                text=p.read_text()
                ids['mathvision'].update(re.findall(r'(?:MathVision/|mathvision:)([0-9]{1,4})(?:\.jpg|\b)',text))
                ids['mathverse'].update(re.findall(r'mathverse:testmini:([0-9]+)',text))
                method='explicit_source_reference_only'
            ids['mathvision']&=mv_ids;ids['mathverse']&=verse_ids
            if any(ids.values()): records.append(dict(path=name,stage=stage,kind=kind(name),method=method,
                mathvision_ids=sorted(ids['mathvision'],key=int),mathverse_ids=sorted(ids['mathverse'],key=int)))
        except Exception as e: failures.append(dict(path=name,error=type(e).__name__+': '+str(e)[:160]))
    # Catalog source membership is direct evidence, including all 3040 IDs.
    for ds,valid,groups in [('mathvision',mv_ids,fam),('mathverse',verse_ids,{r['family_id']:[r['problem_index']] for r in verse['families']})]:
        by=defaultdict(list)
        for i,r in enumerate(records):
            for item in r[ds+'_ids']:by[item].append(i)
        rows=[]
        for family,members in sorted(groups.items()):
            indices=sorted({i for m in members for i in by[m]})
            matches=[records[i] for i in indices]
            rows.append(dict(family_id=family,member_item_ids=members,
                status='HISTORICALLY_EXPOSED' if indices else 'HISTORICALLY_UNTOUCHED',
                historically_exposed=bool(indices),historical_stages=sorted({r['stage'] for r in matches}),
                exposure_kinds=sorted({r['kind'] for r in matches}),artifact_indices=indices,
                direct_item_appearances={m:by[m] for m in members},
                outcome_inspection_evidence=any(r['kind']=='OUTCOME_INSPECTION_ARTIFACT' for r in matches)))
        save(ROOT/f'stage14a_{ds}_historical_exposure.json',dict(at=now(),rows=rows,
             meaning='Source catalogs count as appearance. Artifact class is provenance, not correctness. A model output alone does not establish human inspection.',
             limitations='Metadata/path audit cannot prove whether an unrecorded human inspection occurred. OTHER_IDENTITY_ARTIFACT is not assigned a scientific exposure category.',
             outcome_values_inspected=False,scan='audit/historical_identity_scan.json'))
    save(ROOT/'audit/historical_identity_scan.json',dict(at=now(),records=records,failures=failures,
         inventoried_files=len(paths),no_model_output_text_or_correctness_values_returned=True))
    print('HISTORY',len(records),'identity-bearing artifacts',len(failures),'unreadable artifacts')


if __name__=='__main__':main()
