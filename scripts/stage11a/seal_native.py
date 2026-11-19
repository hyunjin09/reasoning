"""Merge raw native annotations only after blind same-trace adjudication."""
from scripts.stage11a.common import ROOT,load,save,sha,now
from scripts.stage11a.review_validation import validate_native

packet=load(ROOT/'packets/native_adjudication.json');final=load(ROOT/'annotations/native_adjudication.json')
assert final['sealed'] and final['probe_outputs_opened'] is False and final['mode_correctness_opened'] is False
assert final['packet_sha256']==sha(ROOT/'packets/native_adjudication.json')
adjudicated={r['packet_id']:r for r in final['rows']}
assert len(adjudicated)==len(final['rows'])
assert set(adjudicated)=={r['packet_id'] for r in packet['rows']}
for request in packet['rows']:
    r=adjudicated[request['packet_id']]
    assert r['packet_sha256']==sha(request['packet'])
    validate_native(r,load(request['packet']))
merged={}
for w in ['main','b','a']:
    p=ROOT/'annotations'/f'native_{w}.json';assert sha(p)==packet['sources_sha256'][w]
    merged.update({r['packet_id']:r for r in load(p)['rows']})
merged.update(adjudicated)
save(ROOT/'annotations/native_final.json',dict(at=now(),sealed=True,probe_outputs_opened=False,mode_correctness_opened=False,
    sources_sha256={str(p):sha(p) for p in [ROOT/'annotations/native_a.json',ROOT/'annotations/native_b.json',ROOT/'annotations/native_main.json',ROOT/'annotations/native_adjudication.json']},
    rows=list(merged.values())))
print('NATIVE_SEALED',len(merged),'annotations')
