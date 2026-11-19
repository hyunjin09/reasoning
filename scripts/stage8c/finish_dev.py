"""Validate complete dev receipts and prepare the frozen scorer's blind queue."""
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

from visual_reasoning.stage8b.v2_scoring import score_answer
from visual_reasoning.stage8c.analysis import summarize, transitions, development_decision
from scripts.stage8c.prepare import ROOT, save, sha


def main():
    cfg=json.loads((ROOT/'audit/dev_config.json').read_text())
    tasks=json.loads(Path(cfg['task_manifest']).read_text())['tasks']
    metadata={r['item_id']:r for r in json.loads((ROOT/'stage8c_v2_dev128_manifest.json').read_text())['rows']}
    arms={g:{} for g in (1.,1.25,1.5,2.)};review=[];receipts={}
    for task in tasks:
        dest=ROOT/'dev'/'examples'/task['task_id'];p=dest/'result.json'
        r=json.loads(p.read_text());assert r['task_id']==task['task_id']
        assert r['seed']==task['input']['seed'] and r['gain']==task['gain']
        for name,expected in r['provenance_sha256'].items():assert sha(name)==expected,name
        gen=json.loads((dest/'generation.json').read_text())
        assert gen['generation_parameters']['seed']==r['seed']
        row=metadata[r['item_id']];text=gen['raw_decoded_response']
        score=score_answer(text,row)
        pieces=[json.loads(line)['decoded_token'] for line in (dest/'tokens.jsonl').read_text().splitlines()]
        assert ''.join(pieces)==text and len(pieces)==r['tokens']
        boundary=text.find('</think>')
        reasoning=int(np.searchsorted(np.cumsum([len(t) for t in pieces]),boundary,side='right')) if boundary>=0 else len(pieces)
        arrays=np.load(dest/'passive.npz');assert len(arrays['retrieval_score'])==len(pieces)
        result=dict(r,**score,reasoning_tokens=reasoning,elapsed_seconds=r['runtime']['elapsed_seconds'])
        arms[r['gain']][r['item_id']]=result;receipts[str(p)]=sha(p)
        if score['correct'] is None:
            review.append(dict(task_id=r['task_id'],item_id=r['item_id'],gain=r['gain'],
                generation=str(dest/'generation.json'),extraction=score,
                instruction='Extract emitted final answer from response without gold; equivalence adjudication separately. Do not infer answer from benchmark truth.'))
    assert len(tasks)==512 and all(len(x)==128 for x in arms.values())
    summaries={str(g):dict(summarize(a),transitions=None if g==1. else transitions(arms[1.],a)) for g,a in arms.items()}
    decision=development_decision(arms,metadata)
    report=dict(at=datetime.now(timezone.utc).isoformat(),stage='development',complete_trajectories=512,
         summaries=summaries,rows={str(g):a for g,a in arms.items()},decision=decision,
         blind_extraction_pending=review,receipt_sha256=receipts,
         status='generation_complete_extraction_pending' if review else 'development_scored',
         runtime_sum_seconds=sum(r['elapsed_seconds'] for a in arms.values() for r in a.values()))
    save(ROOT/'stage8c_v2_dev_dose_results.json',report)
    save(ROOT/'audit/dev_blind_extraction_queue.json',dict(rows=review,labels_sealed=False))
    if not review:
        save(ROOT/'stage8c_v2_dose_freeze.json',dict(decision,at=report['at'],
             dev_results_sha256=sha(ROOT/'stage8c_v2_dev_dose_results.json')))
    save(ROOT/'dev/completed.json',dict(at=report['at'],trajectories=512,decision=decision['status'],
         heldout_launched=False,allocation_can_release=True))
    print(json.dumps(dict(event='dev_complete',trajectories=512,decision=decision['status'],
                        blind_extractions=len(review),summaries=summaries)),flush=True)


if __name__=='__main__':main()
