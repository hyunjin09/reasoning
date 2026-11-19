"""Append immutable manually adjudicated source batches; never auto-accept QC."""
from pathlib import Path
from datetime import datetime, timezone
import json


def line_atom(orders):
    text=('The blue and red paths each join left, middle, and right vertices with straight segments, sharing those three horizontal positions. '
          +'; '.join(f'At the {p} vertex blue is {v} red' for p,v in zip(['left','middle','right'],orders))+'.')
    return dict(text=text,atom_type='structured_layout',structured_subfact_count=5,source_object='two-polyline plot',source_ROI='corresponding left/middle/right vertices and connecting segments',unit='vertical order',minimality='Topology and raw vertex orders precede the intersection calculation; no intersection points/count are enumerated.')


def atom(text,n,source,unit='native units'):
    return dict(text=text,atom_type='structured_layout' if n>1 else 'scalar_relation',structured_subfact_count=n if n>1 else None,source_object=source,source_ROI='task-critical source fields only',unit=unit,minimality='Only task-critical directly observed source fields; no derived quantities or final answer.')


def record_batch(start,end,decisions):
    rows=[json.loads(l) for l in Path('outputs/stage14c/source/cohort_manifest.jsonl').read_text().splitlines()]
    assert set(decisions)==set(range(start,end))
    records=[]
    allowed={'ELIGIBLE','TEXT_SUFFICIENT','ANSWER_LEAKAGE_UNAVOIDABLE','NO_DEFENSIBLE_ESTAR','AMBIGUOUS_SOURCE','UNDERSPECIFIED','SOURCE_CONTRADICTION','GOLD_CONFLICT','CORRUPT'}
    for rank in range(start,end):
        label,reason,atoms=decisions[rank];assert label in allowed
        assert (label=='ELIGIBLE')==bool(atoms);assert len(atoms)<=4
        r=rows[rank];records.append(dict(review_rank=rank,family_id=r['family_id'],item_id=r['item_id'],benchmark=r['benchmark'],image_sha256=r['image_sha256'],label=label,rationale=reason,evidence_atoms=atoms,source_review_images=[f'outputs/stage14c/source/review_images/ranks_{rank//20*20}_{min(rank//20*20+19,len(rows)-1)}.png'],reviewer='main_agent',review_method='visual source + native question; no evaluated-model output',review_version=1,provisional_eligibility=label=='ELIGIBLE',second_review_status='PENDING' if atoms else 'NOT_REQUIRED_FOR_ESTAR_EXCLUSION',model_outcomes_used=False))
    p=Path('outputs/stage14c/source/primary_reviews')/f'ranks_{start:04d}_{end-1:04d}_v1.json'
    with p.open('x') as f:json.dump(dict(at=datetime.now(timezone.utc).isoformat(),rows=records,native_rows_replaced=0,E_star_QC_complete=False),f,indent=2,ensure_ascii=False);f.write('\n')
    print(f'{start}–{end-1}: {len(records)} reviewed; {sum(bool(r["evidence_atoms"]) for r in records)} provisional, no final QC passes yet.')
