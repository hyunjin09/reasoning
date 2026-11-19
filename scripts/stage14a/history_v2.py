"""Repair the v1 identity projection, preserving all original audit evidence.

Only identity/provenance projections leave the parser. Native answer, correctness,
text and tensor/token payload fields are never interpreted or returned.
"""
import json
import re
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import pyarrow.parquet as pq
from scripts.stage14a.common import ROOT, Path, load, save, sha, now
from scripts.stage14a.history import kind as old_kind

ID_KEYS={'item_id','source_item_id','mathvision_id','problem_id','problem_index','family_id','source_family_id','trajectory_id','base_id','example_id','event_id'}
ID_LISTS={'item_ids','source_item_ids','mathvision_ids','family_ids','selected_ids','technical_ids','base_ids','trajectory_ids','event_ids'}
TAGS={'dataset','benchmark','source_dataset','image','image_path','original_image','source_image'}
PAYLOAD={'generated_token_ids','prompt_token_ids','prefix_token_ids','token_character_offsets','token_ids','tokens','attention','attentions','hidden_states','logits','logprobs','full_reasoning_text','reasoning','response','response_text','output_text','raw_decoded_response','answer','gold_answer','correct','is_correct','score','scores'}
PATTERNS={
 'mathverse':re.compile(r'(?:mathverse[_:](?:family_|testmini:)?)([0-9]+)(?![0-9])',re.I),
 'mathvision':re.compile(r'(?:mathvision[_:]|math_vision[_:]|math-vision[_:])([0-9]+)(?![0-9])',re.I)}

def named(value):
    out={'mathvision':set(),'mathverse':set()}
    if not isinstance(value,(str,int)):return out
    s=str(value)
    for ds,pat in PATTERNS.items():out[ds].update(pat.findall(s))
    if 'mathverse/' in s.lower():out['mathverse'].update(re.findall(r'image_([0-9]+)\.(?:png|jpg)',s))
    out['mathvision'].update(re.findall(r'(?:MathVision|mathvision)/([0-9]+)\.(?:jpg|png)',s))
    return out

def identities(data,families,context=None):
    found={'mathvision':set(),'mathverse':set()}
    def walk(x,ctx):
        if isinstance(x,list):
            for v in x:
                if isinstance(v,(dict,list)):walk(v,ctx)
            return
        if not isinstance(x,dict):return
        explicit=set()
        for k in TAGS|ID_KEYS:
            val=x.get(k)
            if not isinstance(val,(str,int)):continue
            s=str(val)
            if k in TAGS:
                if 'mathverse' in s.lower():explicit.add('mathverse')
                elif any(z in s.lower() for z in ('mathvision','math_vision','math-vision')):explicit.add('mathvision')
            z=named(val)
            for ds,ids in z.items():
                if ids:explicit.add(ds);found[ds].update(ids)
            if k in ID_KEYS and s in families:
                found['mathvision'].update(families[s]);explicit.add('mathvision')
        if len(explicit)==1:ctx=next(iter(explicit))
        elif len(explicit)>1:ctx=None
        for k in ID_KEYS:
            val=x.get(k)
            if isinstance(val,(str,int)) and str(val).isdigit() and ctx:found[ctx].add(str(val))
        for k,v in x.items():
            if k in PAYLOAD:continue
            if k in ID_LISTS and isinstance(v,list):
                for val in v:
                    z=named(val)
                    for ds,ids in z.items():found[ds].update(ids)
                    if isinstance(val,(str,int)) and str(val).isdigit() and ctx:found[ctx].add(str(val))
            elif isinstance(v,(dict,list)):walk(v,ctx)
    walk(data,context)
    return found

def artifact_kind(name):
    if name=='outputs/stage11a/v1/audit/e_star_adjudication.json':return 'SOURCE_OR_DESIGN_ARTIFACT'
    if '/packets/' in name and '/stage10b/' in name:return 'TRACE_REVIEW_ARTIFACT'
    if name=='outputs/stage9a/v1/annotations/source_review/causal_selection_reviewed.json':return 'TRACE_REVIEW_ARTIFACT'
    if any(s in name for s in ['/annotations/semantic','/annotations/reaccess','semantic_annotations','reaccess_annotations']):return 'TRACE_REVIEW_ARTIFACT'
    return old_kind(name)

def fixture(name):
    return any(s in name for s in ['pytest','/test_tmp','/test_'])

def main():
    assert __import__('os').environ.get('SLURM_JOB_ID'), 'Long audit uses Slurm CPU allocation.'
    census=load(ROOT/'audit/mathvision_census_source_snapshot.json');verse=load(ROOT/'audit/mathverse_mapping_source_snapshot.json')
    fam={}
    for r in census['aliases']:
        for key in [r['family_id']]+r['inherited_family_ids']:fam[key]=r['member_item_ids']
    valid={'mathvision':{r['item_id'] for r in census['rows']},'mathverse':{r['problem_index'] for r in verse['families']}}
    previous=load(ROOT/'audit/historical_identity_scan.json')
    old={r['path']:r for r in previous['records']}
    paths=sorted(p for p in subprocess.check_output(['rg','--files','--hidden','outputs','reports','runs'],text=True).splitlines() if 'stage14a' not in p)
    paths=[p for p in paths if Path(p).suffix in {'.json','.jsonl','.parquet','.md'}]
    progress=ROOT/'audit/history_v2_file_receipts.jsonl'
    prior={r['path']:r for r in [json.loads(s) for s in progress.read_text().splitlines()]} if progress.exists() else {}
    def one(name):
        if name in prior:return prior[name]
        p=Path(name);stage_match=re.search(r'stage[0-9]+[a-z0-9_]*',name.lower());stage=stage_match.group() if stage_match else 'unclassified'
        r=dict(path=name,stage=stage,kind=artifact_kind(name),mathvision_ids=[],mathverse_ids=[],size=p.stat().st_size)
        if fixture(name):return dict(r,method='explicit_test_fixture_exclusion',error=None)
        ctx='mathvision' if re.match(r'stage(?:9|10|11|12|13)',stage) else None
        pathids=named(name);ids={ds:set(v) for ds,v in pathids.items()}
        if pathids['mathverse']:ctx='mathverse'
        try:
            # Token-only streams contain no item identities; their sibling manifests
            # and source-bearing directory names provide the provenance instead.
            if p.name in {'tokens.jsonl','tokens.json','token_offsets.json','token_character_offsets.json'}:
                method='token_payload_not_interpreted; directory_identity_only'
            elif p.suffix=='.md':
                text=p.read_text()
                ids['mathvision'].update(re.findall(r'(?:MathVision/|mathvision:)([0-9]{1,4})(?:\.jpg|\b)',text))
                ids['mathverse'].update(re.findall(r'mathverse:testmini:([0-9]+)',text));method='explicit_source_reference_only'
            elif p.suffix=='.parquet':
                f=pq.ParquetFile(p);cols=[k for k in f.schema.names if k in ID_KEYS|TAGS|ID_LISTS]
                z=identities(f.read(columns=cols).to_pylist(),fam,ctx)
                for ds in ids:ids[ds].update(z[ds])
                method='identity_column_projection_v2'
            else:
                def add(obj):
                    z=identities(obj,fam,ctx)
                    for ds in ids:ids[ds].update(z[ds])
                if p.suffix=='.json':add(load(p))
                else:
                    with p.open() as f:
                        for line in f:
                            if line.strip():add(json.loads(line))
                method='identity_keys_only_v2'
            for ds in ids:r[ds+'_ids']=sorted(ids[ds]&valid[ds],key=int)
            return dict(r,method=method,error=None)
        except Exception as e:
            # No recovery from actual malformed scientific data is hidden.
            return dict(r,method='unreadable',error=type(e).__name__+': '+str(e)[:160])
    records=[]
    with progress.open('a') as f, ThreadPoolExecutor(max_workers=4) as pool:
        for i,r in enumerate(pool.map(one,paths)):
            records.append(r)
            if r['path'] not in prior:f.write(json.dumps(r,ensure_ascii=False)+'\n')
            if (i+1)%2000==0:f.flush();print('FILES',i+1,'of',len(paths),flush=True)
    matches=[r for r in records if r['mathvision_ids'] or r['mathverse_ids']]
    failures=[r for r in records if r['error']]
    changes=[]
    for r in matches:
        o=old.get(r['path'],{})
        if any(set(r[ds+'_ids'])!=set(o.get(ds+'_ids',[])) for ds in valid) or r['kind']!=o.get('kind'):
            changes.append(dict(path=r['path'],old_projection=o,new_projection=r))
    out=ROOT/'audit/history_v2'
    for ds,groups in [('mathvision',{r['family_id']:r['member_item_ids'] for r in census['aliases']}),('mathverse',{r['family_id']:[r['problem_index']] for r in verse['families']})]:
        by=defaultdict(list)
        for i,r in enumerate(matches):
            for item in r[ds+'_ids']:by[item].append(i)
        rows=[]
        for family,members in sorted(groups.items()):
            indices=sorted({i for m in members for i in by[m]});rr=[matches[i] for i in indices];kinds={r['kind'] for r in rr}
            rows.append(dict(family_id=family,member_item_ids=members,status='HISTORICALLY_EXPOSED' if indices else 'HISTORICALLY_UNTOUCHED',historically_exposed=bool(indices),historical_stages=sorted({r['stage'] for r in rr}),exposure_kinds=sorted(kinds),artifact_indices=indices,direct_item_appearances={m:by[m] for m in members},outcome_inspection_evidence=bool(kinds&{'OUTCOME_INSPECTION_ARTIFACT','TRACE_REVIEW_ARTIFACT'}),technical_exposure_evidence='TECHNICAL_ARTIFACT' in kinds,scientific_generation_evidence='GENERATION_ARTIFACT' in kinds))
        save(out/f'{ds}_historical_exposure.json',dict(at=now(),rows=rows,scan='audit/history_v2/historical_identity_scan.json',outcome_values_inspected=False,meaning='All source-catalog appearances count. Trace/scoring review artifacts conservatively establish recorded behavior/outcome exposure; they do not prove who read an artifact. Unknown provenance remains explicit.',limitations='Unrecorded inspections cannot be detected. Path categories are evidence classes, not correctness judgments.'))
    save(out/'historical_identity_scan.json',dict(at=now(),records=matches,failures=failures,files_examined=len(records),test_fixture_exclusions=sum(r['method']=='explicit_test_fixture_exclusion' for r in records),projection_changes=changes,previous_scan_sha256=sha(ROOT/'audit/historical_identity_scan.json'),code_sha256=sha(__file__),no_model_output_text_or_correctness_values_returned=True))
    print('COMPLETE',len(records),len(matches),'identity artifacts',len(failures),'errors',flush=True)

if __name__=='__main__':main()
