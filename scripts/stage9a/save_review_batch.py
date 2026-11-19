"""Persist explicit agent-reviewed classifications; never infer missing labels."""
import argparse
import json
from datetime import datetime,timezone
from pathlib import Path
from scripts.stage8c.prepare import save,sha

ROOT=Path('outputs/stage9a/v1/annotations/review_work')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('decisions');args=ap.parse_args()
    spec=json.loads(Path(args.decisions).read_text());rows=json.loads((ROOT/'masked_events.json').read_text())
    start,stop=spec['range'];accept=set(spec['accept']);reject={int(k):v for k,v in spec.get('reject',{}).items()};unknown={int(k):v for k,v in spec.get('unknown',{}).items()}
    assert len(accept)+len(reject)+len(unknown)==stop-start
    assert accept|set(reject)|set(unknown)==set(range(start,stop))
    reviewed=[]
    for i in range(start,stop):
        r=rows[i]
        label='accepted' if i in accept else 'rejected' if i in reject else 'unknown'
        reviewed.append(dict(review_index=i,event_id=r['event_id'],packet_id=r['packet_id'],image=r['image'],demand_token=r['demand_token'],
            semantic_label=label,kind='visual_identification_comparison_or_revisit' if label=='accepted' else None,
            reason=reject.get(i,unknown.get(i,'The reviewed paragraph explicitly invokes visual identification, comparison or reconsideration of depicted entities/relations; correctness is not an eligibility condition.')),
            evidence_excerpt=r['excerpt'],source_scope='depicted entities/relations named in excerpt' if label=='accepted' else None,
            local_source_roi=None,causal_eligibility='not_yet_source_readout_reviewed',
            reviewer='Codex main agent, single semantic annotator; not independent human review',
            review_scope='Surrounding paragraph and source contact-sheet image; full excerpt retained. Individual causal ROI/readout validation is separate.',
            outcome_masked=True))
    save(ROOT/f'reviewed_{start:03}_{stop:03}.json',dict(at=datetime.now(timezone.utc).isoformat(),rows=reviewed,
        explicit_decisions=str(Path(args.decisions)),decision_sha256=sha(args.decisions),source_sha256=sha(ROOT/'masked_events.json')))
    print(f'Saved {len(reviewed)} explicit semantic decisions')


if __name__=='__main__':main()
