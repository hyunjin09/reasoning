"""Output-only annotation packets and hash-bound technical gate sealing."""
import argparse
from scripts.stage12b.common import ROOT,load,save,sha,now
from scripts.stage12b.protocol import technical_gate
from scripts.stage11cr.protocol import repetition_metrics

def packet():
    manifest=load(ROOT/'stage12b_frozen_manifest.json');ids=set(manifest['technical_ids']);rows=[]
    for t in manifest['tasks']:
        if t['item_id'] not in ids:continue
        p=ROOT/'generations'/t['task_id']/'generation.json'
        if not (p.parent/'result.json').exists():continue
        g=load(p);assert sha(p)==load(p.parent/'result.json')['generation_sha256']
        rows.append(dict(task_id=t['task_id'],item_id=t['item_id'],arm=t['arm'],answer_type=t['answer_type'],
            raw=g['raw_decoded_response'],tokens=g['tokens'],cap_hit=g['cap_hit'],normal_stop=g['normal_stop'],
            generation_sha256=sha(p),repetition_metrics=repetition_metrics(g['generated_token_ids'])))
    dest=ROOT/'audit/review_packets'/f'{now().replace(":", "")}.json'
    save(dest,dict(at=now(),correctness_opened=False,rows=rows))
    print(dest)
    for r in rows:print(r['task_id'],r['tokens'],r['cap_hit'],r['repetition_metrics'])

def seal(path):
    manifest=load(ROOT/'stage12b_frozen_manifest.json');ids=set(manifest['technical_ids'])
    tasks={t['task_id']:t for t in manifest['tasks'] if t['item_id'] in ids}
    d=load(path);assert d['correctness_opened'] is False
    assert len(d['rows'])==36 and {r['task_id'] for r in d['rows']}==set(tasks)
    rows=[]
    for r in d['rows']:
        t=tasks[r['task_id']];p=ROOT/'generations'/t['task_id']/'generation.json';g=load(p)
        assert r['generation_sha256']==sha(p)==load(p.parent/'result.json')['generation_sha256']
        for k in ['parseable','committed_final','repetition_pathology']:assert isinstance(r[k],bool)
        assert r['quote'] and r['quote'] in g['raw_decoded_response'] and r['reason']
        assert not r['committed_final'] or r['extracted_final']
        assert (g['visual_tokens']==0)==(t['arm']=='O')
        rows.append(dict(r,arm=t['arm'],family_id=t['family_id'],item_id=t['item_id'],tokens=g['tokens'],
            cap_hit=g['cap_hit'],normal_stop=g['normal_stop']))
    gate=technical_gate({a:[r for r in rows if r['arm']==a] for a in 'ENO'})
    save(ROOT/'stage12b_technical_sanity.json',dict(at=now(),correctness_opened=False,
        decisions_sha256=sha(path),decisions_path=path,rows=rows,**gate))
    print(gate)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['packet','seal']);p.add_argument('path',nargs='?');a=p.parse_args()
    packet() if a.action=='packet' else seal(a.path)
