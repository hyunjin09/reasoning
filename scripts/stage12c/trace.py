"""Visible evidence annotations, kept separate from task correctness and rescue."""
import argparse
from scripts.stage12c.common import ROOT,load,save,sha,now


def state(atoms):
    assert atoms and all(a in ['CORRECT','WRONG_OR_CONFLICTING','NOT_EXTERNALIZED'] for a in atoms)
    if 'WRONG_OR_CONFLICTING' in atoms:return 'TRACE_E_WRONG_OR_CONFLICTING'
    if all(a=='CORRECT' for a in atoms):return 'TRACE_E_FULL'
    if 'CORRECT' in atoms:return 'TRACE_E_PARTIAL'
    return 'TRACE_E_NOT_EXTERNALIZED'


def packets():
    assert load(ROOT/'audit/denominator_seal.json')['pass']
    assert not (ROOT/'audit/correctness_opened.json').exists()
    full=load(ROOT/'stage12c_frozen_bottleneck_manifest.json')
    selected={r['item_id'] for r in full['labels'] if r['complete_native_failure']}
    assert len(selected)==26
    facts={r['item_id']:r['facts'] for r in full['rows']}
    for t in full['tasks']:
        if t['item_id'] not in selected:continue
        tid=t['task_id'];g=load(ROOT/'generations'/tid/'generation.json')
        save(ROOT/'audit/trace_packets'/f'{tid}.json',dict(task_id=tid,family_id=t['family_id'],
            facts=facts[t['item_id']],trace=g['raw_decoded_response'],generation_sha256=sha(ROOT/'generations'/tid/'generation.json')))


def record(tid,codes,reason,quotes):
    p=ROOT/'audit/trace_packets'/f'{tid}.json';packet=load(p)
    atoms=[{'C':'CORRECT','I':'WRONG_OR_CONFLICTING','U':'NOT_EXTERNALIZED'}[c] for c in codes]
    assert len(atoms)==len(packet['facts'])
    assert all(q in packet['trace'] for q in quotes), 'Evidence quotes must occur verbatim'
    save(ROOT/'audit/trace_annotations'/f'{tid}.json',dict(at=now(),task_id=tid,family_id=packet['family_id'],
        atom_states=atoms,state=state(atoms),reason=reason,quotes=quotes,packet_sha256=sha(p),
        scope='Visible facts before final commitment; no correctness or paired outcomes in annotation packet'))


def show(tid,start=0,end=None):
    p=load(ROOT/'audit/trace_packets'/f'{tid}.json')
    print(tid,p['family_id'])
    for f in p['facts']:print(f['fact_id'],f['probe_request'],'E*:',f['gold_value'])
    print(p['trace'][start:end])


def seal():
    packets=list((ROOT/'audit/trace_packets').glob('*.json'));assert len(packets)==52
    annotations=[ROOT/'audit/trace_annotations'/p.name for p in packets]
    for p,a in zip(packets,annotations):assert load(a)['packet_sha256']==sha(p)
    save(ROOT/'audit/trace_seal.json',dict(at=now(),task_correctness_opened=False,
        annotation_hashes={str(p):sha(p) for p in annotations}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['packets','seal']);a=p.parse_args()
    packets() if a.action=='packets' else seal()
