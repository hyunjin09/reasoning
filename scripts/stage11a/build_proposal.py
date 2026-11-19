"""Common pre-outcome proposal for two independent sufficiency checks, not a seal."""
import copy
from scripts.stage11a.common import ROOT,load,save,sha,now

a_path=ROOT/'annotations/e_star_a.json';b_path=ROOT/'annotations/e_star_b.json'
a=load(a_path);b=load(b_path)
assert a['sealed'] and b['sealed'] and len(a['rows'])==len(b['rows'])==128
aa={r['item_id']:r for r in a['rows']};bb={r['item_id']:r for r in b['rows']}
source=load(ROOT/'packets/evidence_construction.json')['rows']
assert set(aa)==set(bb)=={r['item_id'] for r in source}
prefer_b={'653','1237','2781','1789','2273','1974','2214','1430','1022','2448','2013'}
exclude_a={'31','885','1262','2019'}
rows=[]
for original in source:
    ident=original['item_id'];x,y=aa[ident],bb[ident]
    use_b=ident in prefer_b or (x['eligibility']!='E_STAR_ELIGIBLE' and y['eligibility']=='E_STAR_ELIGIBLE' and ident not in exclude_a)
    selected=copy.deepcopy(y if use_b else x)
    if ident=='2448' and selected['eligibility']=='E_STAR_ELIGIBLE':
        selected['facts'][0]['probe_request']='List all x-coordinates where the graph has height 6.'
        selected['facts'][1]['probe_request']='How many times does the graph meet the horizontal line whose height is the smaller x-coordinate you reported for height 6?'
        selected['facts'][2]['probe_request']='How many times does the graph meet the horizontal line whose height is the larger x-coordinate you reported for height 6?'
    # Reviewers see a shared proposal, but not one another's labels or the selection history.
    selected.update(question=original['question'],image=original['image'],answer=original['answer'],subject=original['subject'],
                    family_id=original['family_id'])
    rows.append(selected)
save(ROOT/'audit/e_star_proposal.json',dict(at=now(),sealed_for_sufficiency_review=True,rows=rows,model_outcomes_opened=False,
    instruction='Check image truth, atomicity/minimality and whether question plus these facts ALONE suffice; do not silently import additional image topology. Review every proposed eligible set and flag any excluded item that has a demonstrably sufficient compact alternative. No native outputs/correctness or other reviewer data.',
    construction_sha256={'a':sha(a_path),'b':sha(b_path)}))
save(ROOT/'audit/proposal_selection_notes.json',dict(at=now(),preferred_b_ids=sorted(prefer_b),retained_a_exclusions=sorted(exclude_a),
    reason='Common pre-outcome proposals preserve the union of plausible compact evidence sets for second independent review. Corrected bird57 from original image;31/885 complete option-mapping exceeds cap (do not provide only the correct option position);2019 order follows triangle inequality;1262 constant horizontal width is text-given. Main image notes remain separate. This is not final eligibility.',
    proposal_sha256=sha(ROOT/'audit/e_star_proposal.json')))
print('COMMON PROPOSAL',len(rows),'proposed eligible',sum(r['eligibility']=='E_STAR_ELIGIBLE' for r in rows))
