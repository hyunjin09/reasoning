"""Validate complete dev receipts and prepare the frozen scorer's blind queue."""
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

from visual_reasoning.stage8b.v2_scoring import score_answer
from visual_reasoning.stage8c.analysis_fp32 import summarize, transitions, development_decision
from scripts.stage8c.prepare import save, sha
from scripts.stage8c_v3.prepare import ROOT
from visual_reasoning.stage8b.block0 import episodes


def main():
    cfg=json.loads((ROOT/'audit/dev_config.json').read_text())
    tasks=json.loads(Path(cfg['task_manifest']).read_text())['tasks']
    metadata={r['item_id']:r for r in json.loads((ROOT/'stage8c_v3_dev128_manifest.json').read_text())['rows']}
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
        result=dict(r,**score,reasoning_tokens=reasoning,elapsed_seconds=r['runtime']['elapsed_seconds'],
                    retrieval_episode_count=len(episodes(arrays['retrieval_score'],4)))
        arms[r['gain']][r['item_id']]=result;receipts[str(p)]=sha(p)
        if score['correct'] is None:
            review.append(dict(task_id=r['task_id'],item_id=r['item_id'],gain=r['gain'],
                generation=str(dest/'generation.json'),extraction=score,
                instruction='Extract emitted final answer from response without gold; equivalence adjudication separately. Do not infer answer from benchmark truth.'))
    assert len(tasks)==512 and all(len(x)==128 for x in arms.values())
    summaries={str(g):dict(summarize(a),transitions=None if g==1. else transitions(arms[1.],a)) for g,a in arms.items()}
    for g,a in arms.items():
        summaries[str(g)].update(retrieval_episodes=sum(r['retrieval_episode_count'] for r in a.values()),
            active_gpu_hours=sum(r['elapsed_seconds'] for r in a.values())/3600,
            tokens_per_second=sum(r['tokens'] for r in a.values())/sum(r['elapsed_seconds'] for r in a.values()),
            peak_gpu_allocated_bytes=max(r['runtime']['peak_gpu_allocated_bytes'] for r in a.values()))
    decision=development_decision(arms,metadata)
    report=dict(at=datetime.now(timezone.utc).isoformat(),stage='development',complete_trajectories=512,
         summaries=summaries,rows={str(g):a for g,a in arms.items()},decision=decision,
         blind_extraction_pending=review,receipt_sha256=receipts,
         status='generation_complete_extraction_pending' if review else 'development_scored',
         runtime_sum_seconds=sum(r['elapsed_seconds'] for a in arms.values() for r in a.values()))
    save(ROOT/'stage8c_v3_dev_dose_results.json',report)
    save(ROOT/'audit/dev_blind_extraction_queue.json',dict(rows=review,labels_sealed=False))
    if not review:
        save(ROOT/'stage8c_v3_dose_freeze.json',dict(decision,at=report['at'],
             dev_results_sha256=sha(ROOT/'stage8c_v3_dev_dose_results.json')))
    save(ROOT/'stage8c_v3_runtime_overhead.json',dict(at=report['at'],phase='development',summaries=summaries,
        dtype='float32',definition='Measured elapsed time includes frozen-policy observation and intervention replay in all arms; worker startup/idle excluded from active GPU-hours'))
    save(ROOT/'dev/completed.json',dict(at=report['at'],trajectories=512,decision=decision['status'],
         heldout_launched=False,allocation_can_release=True))
    plot_dev(summaries)
    (ROOT/'stage8c_v3_summary.md').write_text(
        '# Stage8C v3 FP32 development complete\n\n'
        f"512/512 development trajectories collected. Decision: {decision['status']}. "
        f"Blind extraction cases pending: {len(review)}.\n\n"
        'Baseline and gain arms both ran in FP32. The inherited detector is a fixed policy; '
        'no transfer certification or BF16 equivalence is claimed.\n\n'
        'The development allocation is released automatically. Held-out inference has not launched. '
        'Finish any blind extraction, seal the development decision, then follow the approved '
        'conditional continuation or stop rule.\n')
    print(json.dumps(dict(event='dev_complete',trajectories=512,decision=decision['status'],
                        blind_extractions=len(review),summaries=summaries)),flush=True)


def plot_dev(summaries):
    import os
    os.environ['MPLCONFIGDIR']=str(ROOT/'audit/matplotlib_cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    gains=[1.,1.25,1.5,2.]
    fig,axes=plt.subplots(2,2,figsize=(9,6),constrained_layout=True)
    curves=[('Accuracy', [summaries[str(g)]['accuracy'] for g in gains]),
        ('W→C − C→W', [0 if g==1. else summaries[str(g)]['transitions']['WtoC']-summaries[str(g)]['transitions']['CtoW'] for g in gains]),
        ('Cap rate', [summaries[str(g)]['cap_rate'] for g in gains]),
        ('Median reasoning tokens', [summaries[str(g)]['median_reasoning_tokens'] for g in gains])]
    for ax,(label,values) in zip(axes.flat,curves):
        ax.plot(gains,values,'o-');ax.set_xlabel('Visual gain');ax.set_ylabel(label);ax.set_xticks(gains)
    fig.suptitle('FP32 development dose response; extraction status accompanies results')
    (ROOT/'figures').mkdir(exist_ok=True)
    for ext in ['png','pdf']:fig.savefig(ROOT/f'figures/figure1_dev_dose_response.{ext}',dpi=160)
    plt.close(fig)


if __name__=='__main__':main()
