"""Freeze the outcome-blind final evidence adjudication, then prepare native packets."""
import os,runpy
from scripts.stage11a.common import ROOT,load,save,sha,now

assert os.environ.get('SLURM_JOB_ID')
for name in ['sufficiency','repair_sufficiency','repair2_sufficiency']:
    for who in ['a','b']:assert load(ROOT/'annotations'/f'{name}_{who}.json')['sealed']
rows={r['item_id']:r for r in load(ROOT/'audit/e_star_proposal.json')['rows']}
for version in [1,2]:rows.update({r['item_id']:r for r in load(ROOT/'audit'/f'e_star_repair_proposal_v{version}.json')['rows']})
save(ROOT/'audit/e_star_adjudication.json',dict(at=now(),sealed=True,model_outcomes_opened=False,rows=list(rows.values()),
    rules='Both independent reviewers must endorse each exact eligible set and leak-free probe before freeze. Prospective minimality/geometry repairs preserved in two versioned packets. Ambiguous task conventions and disputed primitive atomicity are excluded conservatively.',
    atomicity_adjudication={'191':'Mathematically sufficient compact pattern, but reviewers disagree whether it hides independent cardinality and geometry premises. Exclude under strict four-primitive-fact cap; both final checks support conservative exclusion.'},
    source_sha256={str(p):sha(p) for p in [ROOT/'audit/e_star_proposal.json',ROOT/'audit/e_star_repair_proposal_v1.json',ROOT/'audit/e_star_repair_proposal_v2.json']}))
runpy.run_module('scripts.stage11a.seal_evidence',run_name='__main__')
runpy.run_module('scripts.stage11a.prepare_native',run_name='__main__')
