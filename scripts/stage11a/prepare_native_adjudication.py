"""Validate blind native review receipts and expose only same-trace disagreements."""
from scripts.stage11a.common import ROOT,load,save,sha,now
from scripts.stage11a.protocol import order

def main():
    assignment=load(ROOT/'audit/native_reviewer_assignment_v2.json')
    reviews={w:load(ROOT/'annotations'/f'native_{w}.json') for w in ['a','b','main']}
    by={};packets={}
    for w,d in reviews.items():
        from pathlib import Path
        assign_path=Path(assignment['assignments'][w]);assigned=load(assign_path)
        assert d['sealed'] and d['assignment_sha256']==sha(assign_path)
        assert d['probe_outputs_opened'] is False and d['mode_correctness_opened'] is False
        assert len(d['rows'])==len({r['packet_id'] for r in d['rows']})==len(assigned['rows'])
        by[w]={r['packet_id']:r for r in d['rows']}
        assert set(by[w])=={r['packet_id'] for r in assigned['rows']}
        for a in assigned['rows']:
            r=by[w][a['packet_id']];p=load(a['packet']);packets[a['packet_id']]=p
            assert r['packet_sha256']==a['packet_sha256']==sha(a['packet'])
            assert r['coverage_complete'] and r['state'] in ['N0','N1','N2','N3','N4','N5'] and r['reason']
            assert {f['fact_id'] for f in r['facts']}=={f['fact_id'] for f in p['facts']}
            for f in r['facts']:
                assert f['status'] in ['CORRECT','WRONG','MISSING','CONFLICTING','UNCERTAIN'] and f['reason']
                for q in f.get('quotes',[]):assert q and q in p['reasoning_text'],(w,a['packet_id'],q)
            for q in r.get('evidence_quotes',[]):assert q and q in p['reasoning_text'],(w,a['packet_id'],q)
            for name in ['first_evidence_token','first_sufficient_token']:
                if r.get(name) is not None:assert 0<=r[name]<=p['reasoning_tokens'],(w,a['packet_id'],name)
    shared=set(by['a'])&set(by['b']);different={i for i in shared if by['a'][i]['state']!=by['b'][i]['state']}
    allids=set().union(*(set(rr) for rr in by.values()))
    audited=sorted(shared-different,key=order)[:6]+sorted(allids-shared,key=order)[:6]
    requests=[]
    for i in sorted(different|set(audited),key=order):
        requests.append(dict(packet_id=i,packet=f'{ROOT}/packets/native/{i}.json',reason='state_disagreement' if i in different else 'fixed_hash_quality_audit',
            reviews={w:by[w][i] for w in by if i in by[w]}))
    save(ROOT/'packets/native_adjudication.json',dict(at=now(),rows=requests,disagreement_packet_ids=sorted(different),
        sources_sha256={w:sha(ROOT/'annotations'/f'native_{w}.json') for w in reviews},model_correctness_opened=False,probe_outputs_opened=False))
    print('NATIVE_VALIDATED',len(packets),'packets',len(different),'state disagreements;',len(audited),'fixed hash audit packets')

if __name__=='__main__':main()
