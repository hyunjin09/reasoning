"""Secondary fixed-adapter scoring, after masked extraction review is sealed."""
import json
from collections import Counter
from pathlib import Path

from scripts.stage8c.prepare import save,sha
from visual_reasoning.stage8b.v2_scoring import score_answer
from visual_reasoning.stage9a.protocol import ARMS
from visual_reasoning.stage9a.statistics import mean_interval,paired

ROOT=Path('outputs/stage9a/v1')


def main():
    review=json.loads((ROOT/'annotations/answer_extraction_review_frozen.json').read_text());assert review['frozen']
    cohort={r['item_id']:r for r in json.loads((ROOT/'stage9a_cohort_manifest.json').read_text())['rows']}
    index={r['packet_id']:r for r in json.loads((ROOT/'annotations/packet_index.json').read_text())['rows']}
    rows=[]
    for r in review['rows']:
        x=index[r['packet_id']];d=Path(x['receipt']).parent;receipt=json.loads((d/'result.json').read_text())
        row=cohort[receipt['item_id']];text=json.loads((d/'generation.json').read_text())['raw_decoded_response']
        raw=score_answer(text,row)
        reviewed=score_answer('' if r['reviewed_answer'] is None else '\\boxed{'+r['reviewed_answer']+'}',row)
        rows.append(dict(task_id=receipt['task_id'],family_id=receipt['family_id'],arm=receipt['arm'],packet_id=r['packet_id'],
            completion=receipt['completion'],answer_format=row['answer_format'],raw_adapter=raw,reviewed=reviewed,
            review_changed=r['changed'],primary={'accuracy_no_credit':float(reviewed['correct'] is True)}))
    summary={}
    for arm in ARMS:
        rr=[r for r in rows if r['arm']==arm];summary[arm]={}
        for mode in ('raw_adapter','reviewed'):
            counts=Counter(r[mode]['benchmark_label'] for r in rr);n=len(rr);scored=counts['correct']+counts['wrong']
            summary[arm][mode]=dict(n=n,correct=counts['correct'],wrong=counts['wrong'],unscorable=counts['unscorable'],
                accuracy_all_examples_no_credit=counts['correct']/n,accuracy_among_scorable=counts['correct']/scored if scored else None,
                accuracy_interval=mean_interval([float(r[mode]['correct'] is True) for r in rr]),
                normal_completed=dict(Counter(r[mode]['benchmark_label'] for r in rr if r['completion']=='normal completed')),
                capped=dict(Counter(r[mode]['benchmark_label'] for r in rr if r['completion']=='capped')))
    out=dict(rows=rows,arms=summary,secondary=True,thinking_minus_cot=paired(rows,'accuracy_no_credit',confidence=.95),
        cot_minus_direct=paired(rows,'accuracy_no_credit',left='instruct_cot',right='instruct_direct',confidence=.95),
        protocol='Unchanged Stage8B v2 local Qwen adapter, tolerance1e-6, with outcome-masked literal answer extraction; no external judge',
        denominator_policy='No-credit fraction uses all128 native examples/arm; unscorable retained separately, not renamed wrong. Scorable-only fraction also reported.',
        extraction_review_sha256=sha(ROOT/'annotations/answer_extraction_review_frozen.json'),
        limitations=['Single Codex annotator, not independent human review','Local bounded numeric equivalence is not a GPT-4o grading fallback','Accuracy cannot certify source-faithfulness or causal visual use'])
    save(ROOT/'stage9a_accuracy_secondary.json',out)
    print('Secondary accuracy artifact saved')


if __name__=='__main__':main()
