"""Validate manually assigned complete native prefixes and exact claim quotes."""
import argparse
import json
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write
from scripts.stage6a.source_annotations import secondary_sources


def main():
    p=argparse.ArgumentParser();p.add_argument('--start',type=int,required=True);p.add_argument('--remaining-strata',action='store_true');a=p.parse_args()
    stem='c1_semantic_prefix_remaining' if a.remaining_strata else 'c1_semantic_prefix'
    packet=json.loads((OUT/f'review/{stem}_{a.start:03d}.json').read_text())
    decisions=json.loads((OUT/f'review/{stem}_{a.start:03d}_decisions.json').read_text())
    path=OUT/'traces/c1_manual_semantic_prefix.jsonl'
    previous=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
    seen={(r['event_id'],r['span_id']) for r in previous};added=[];secondary=secondary_sources()
    for row in packet:
        key=row['base_id'];labels=decisions[key];assert len(labels)==len(row['spans'])
        valid={'T'}|{s['source_id'] for s in secondary.get(key,[])}
        for span,label in zip(row['spans'],labels):
            assert set(label['demanded_sources'])<=valid
            assert set(label['explicit_visual_claim_sources'])<=set(label['demanded_sources'])
            claims=label.get('source_claims',[])
            assert {c['source_id'] for c in claims}==set(label['explicit_visual_claim_sources'])
            for claim in claims:assert claim['quote'] in span['text']
            identity=(span['event_id'],span['span_id'])
            if identity in seen:continue
            added.append(dict(event_id=span['event_id'],base_id=key,span_id=span['span_id'],
                char_start=span['char_start'],char_end=span['char_end'],text=span['text'],
                **label,semantic_role='REVIEWED_SOURCE_CLAIM' if claims else 'REVIEWED_SOURCE_USE' if label['demanded_sources'] else 'UNRESOLVED' if label['unresolved'] else 'NO_EXPLICIT_MAPPED_NUMERIC_DEMAND',
                annotation_scope='Full first20reasoning-span prefix of all75remaining frozen MathVision/MathVista bases; localized numeric sources only' if a.remaining_strata else 'Full first20reasoning-span prefix of all fixed34MathVerse candidates; localized numeric sources only',
                review_packet=f'review/{stem}_{a.start:03d}.json',attention_or_causal_data_used=False))
    write(path,previous+added);print('Saved',len(added),'manually reviewed source-demand spans')


if __name__=='__main__':main()
