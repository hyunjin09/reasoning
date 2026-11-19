"""Complete historical exclusion, then freeze source-only 96+32 identities."""
import hashlib
import json
import re
from collections import defaultdict,Counter
from pathlib import Path
from scripts.stage12xs.common import ROOT,load,save,sha,now
from scripts.stage12xs.selection import components,choose,order

def main():
    rules=load(ROOT/'audit/exclusion_rules_preselection.json')
    scan=load(ROOT/'audit/historical_manifest_scan.json')
    catalog=Path('outputs/stage8b/v2/cohort/census_manifest_v1.jsonl')
    rows=[json.loads(line) for line in catalog.read_text().splitlines()]
    by={r['item_id']:r for r in rows};assert len(by)==3040
    fm_path=Path('outputs/stage8c_v2/v1/stage8c_v2_family_manifest.json');fm=load(fm_path)
    direct=set(fm['excluded_item_ids'])&by.keys();sources=[]
    for record in scan['rows']:
        ids=record['identified_mathvision_ids']
        if record['path'] in rules['source_catalog_exceptions']:continue
        if ids:
            direct.update(ids);sources.append(dict(path=record['path'],sha256=record['sha256'],item_ids=ids))
    # Actual Stage8B raw example directories supplement the full source catalogs.
    raw_sources=[]
    for p in Path('outputs/stage8b').rglob('native.json'):
        if p.parent.name in by:
            direct.add(p.parent.name);raw_sources.append(dict(path=str(p),sha256=sha(p),item_id=p.parent.name))
    for item in by:
        if fm['item_family'][item] in fm['excluded_families']:direct.add(item)
    tokens={i:set(re.findall(r'[a-z0-9]+',r['question'].lower())) for i,r in by.items()}
    ids=sorted(by,key=int);edges=[]
    for pos,a in enumerate(ids):
        x=tokens[a]
        if len(x)<20:continue
        for b in ids[:pos]:
            y=tokens[b]
            if len(y)<20 or min(len(x),len(y))/max(len(x),len(y))<.45:continue
            common=len(x&y);union=len(x)+len(y)-common
            if common/union>=.45:edges.append(dict(a=a,b=b,jaccard=common/union))
    groups=list(fm['groups'])+[[r['a'],r['b']] for r in edges]
    alias_path=Path('outputs/stage11b/v1/audit/freshness_repair_v2.json')
    prior_edges=load(alias_path)['edges'];groups += [[r['a'],r['b']] for r in prior_edges]
    comp=components(ids,groups);excluded_components={comp[i] for i in direct}
    families=defaultdict(list)
    for i,c in comp.items():families[c].append(i)
    usable=[];excluded=[]
    for c,members in sorted(families.items()):
        previous=sorted({fm['item_family'][i] for i in members})
        family=previous[0] if len(previous)==1 else 'stage12xs_family_'+hashlib.sha256('|'.join(previous).encode()).hexdigest()[:20]
        if c in excluded_components:
            excluded.append(dict(family_id=family,item_ids=sorted(members,key=int),directly_excluded=sorted(set(members)&direct,key=int)));continue
        representative=min(members,key=lambda i:(order(i,'representative'),int(i)))
        r=by[representative]
        usable.append(dict(item_id=representative,family_id=family,member_item_ids=sorted(members,key=int),inherited_family_ids=previous,
            answer_type='multiple_choice' if r['options'] else 'open_ended',level=r['level'],subject=r['subject'],
            question=r['question'],original_question=r['question'],options=r['options'],answer=r['answer'],
            image=r['image'],image_sha256=r['image_sha256'],row_index=r['row_index'],
            source_hash=order(family,'source'),b4_hash=order(family,'b4'),transfer_hash=order(family,'transfer')))
    exclusions=dict(at=now(),frozen=True,prior_manifest_inventory_sha256=sha(ROOT/'audit/historical_manifest_inventory.json'),
        prior_manifest_scan_sha256=sha(ROOT/'audit/historical_manifest_scan.json'),rules_sha256=sha(ROOT/'audit/exclusion_rules_preselection.json'),
        source_hashes={str(fm_path):sha(fm_path),str(alias_path):sha(alias_path),str(catalog):sha(catalog)},sources=sources,
        raw_source_receipts=raw_sources,directly_excluded_item_ids=sorted(direct,key=int),families=excluded,
        n_excluded_families=len(excluded),n_excluded_items=sum(len(f['item_ids']) for f in excluded),
        source_only_alias_edges=edges,n_remaining_families=len(usable),no_scientific_outcomes_used=True,
        conservative_rule='Selected reserve/scientific/technical manifests excluded even when behavioral exposure uncertain; source-only full census catalogs are not exposure.')
    save(ROOT/'stage12xs_historical_exclusion_manifest.json',exclusions)
    initial,reserve=choose(usable);chosen={r['item_id']:r for r in usable}
    assert len(initial)==96 and len(reserve)==32
    for i in initial+reserve:assert sha(chosen[i]['image'])==chosen[i]['image_sha256']
    save(ROOT/'stage12xs_source_candidate_manifest.json',dict(at=now(),frozen=True,exclusion_manifest_sha256=sha(ROOT/'stage12xs_historical_exclusion_manifest.json'),
        selection_rule='SHA256(stage12xs-source-v1|family_id), one source-hash representative per conservative family; no model outcomes.',
        n_eligible_source_families=len(usable),initial_ids=initial,reserve_ids=reserve,rows=[chosen[i] for i in initial+reserve],
        eligibility_pending=True,b4_order=sorted(initial+reserve,key=lambda i:(chosen[i]['b4_hash'],chosen[i]['family_id'])),
        transfer_order=sorted(initial+reserve,key=lambda i:(chosen[i]['transfer_hash'],chosen[i]['family_id']))))
    save(ROOT/'stage12xs_reserve32_manifest.json',dict(at=now(),frozen=True,rows=[chosen[i] for i in reserve],ids=reserve,
        use_rule='Only replace source-only E*-ineligible initial families, in this fixed order, before any generation. Never expand after model outcomes.'))
    save(ROOT/'audit/initial96_annotation_manifest.json',dict(at=now(),frozen=True,rows=[chosen[i] for i in initial],ids=initial,
        note='Final fresh96 manifest awaits E*eligibility and fixed-reserve replacements.'))
    print(dict(excluded_items=exclusions['n_excluded_items'],remaining_families=len(usable),initial96=initial,reserve32=reserve,
        initial_distribution={k:dict(Counter(str(chosen[i][k]) for i in initial)) for k in ['subject','level','answer_type']}))

if __name__=='__main__':main()
