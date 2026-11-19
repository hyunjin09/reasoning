"""Write explicit human/agent source adjudications after visual inspection."""
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path('outputs/stage14c')


def record_packet(stem, corrections=None):
    corrections = corrections or {}
    packet = json.loads((BASE/'source/second_review_packets'/f'{stem}.json').read_text())
    assert set(corrections) <= {v['review_rank'] for v in packet}
    rows = []
    for v in packet:
        prior = v['prior']; correction = corrections.get(v['review_rank'], {})
        label = correction.get('label', prior['label'])
        atoms = correction.get('atoms', prior['evidence_atoms'])
        assert bool(atoms) == (label == 'ELIGIBLE') and len(atoms) <= 4
        rows.append(dict(review_rank=v['review_rank'], family_id=prior['family_id'],
                         label=label, evidence_atoms=atoms,
                         decision='CORRECT' if correction else 'CONFIRM',
                         rationale=correction.get('reason', 'Visual source/question reread confirms the recorded facts and eligibility under the frozen source-only rubric.'),
                         source_packet=str(BASE/'source/second_review_packets'/f'{stem}.png'),
                         reviewer='main_agent', independent_review=False,
                         model_outcomes_used=False,
                         checks=dict(source_accuracy=True, sufficiency=bool(atoms),
                                     minimality=bool(atoms), answer_safe=bool(atoms),
                                     primary_atom_limit=True)))
    target = BASE/'source'/('reread_reviews' if stem.startswith('reread') else 'second_reviews')
    target.mkdir(exist_ok=True)
    with (target/f'{stem}_v1.json').open('x') as f:
        json.dump(dict(at=datetime.now(timezone.utc).isoformat(), rows=rows), f, indent=2, ensure_ascii=False)
    print(stem, 'saved', len(rows), 'review records, corrections', len(corrections))
