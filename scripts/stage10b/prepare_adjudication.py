"""Semantic disagreement packet only. Refuses incomplete independent passes."""
from scripts.stage10b.common import ROOT,load,save,sha,now
from scripts.stage10b.annotation_io import rows_for,normalize
from scripts.stage10b.protocol import agreement


def main():
    corpus=load(ROOT/'stage10b_corpus_manifest.json');ids=[r['trajectory_id'] for r in corpus['rows'] if r['eligible']]
    reviews={};sources={}
    for who in ('a','b'):
        rows,hashes=rows_for(who);assert set(rows)==set(ids),(who,len(rows),len(ids))
        reviews[who]={q:normalize(rows[q],who) for q in ids};sources.update(hashes)
    pairs=[];all_rows=[]
    for q in ids:
        a,b=reviews['a'][q],reviews['b'][q];used=set();aligned=[]
        for x in a['events']:
            possible=[(abs(x['onset']-y['onset']),i,y) for i,y in enumerate(b['events']) if i not in used and abs(x['onset']-y['onset'])<=64]
            if possible:
                _,index,y=min(possible,key=lambda z:z[0]);used.add(index)
            else:y=None
            aligned.append(dict(a=x,b=y))
        aligned.extend(dict(a=None,b=y) for i,y in enumerate(b['events']) if i not in used)
        for pair in aligned:
            x,y=pair['a'],pair['b'];pair.update(pair_id=f'pair_{len(pairs):04d}',trajectory_id=q,
                automatically_matched=bool(x and y),matching_requires_source_review=True)
            pairs.append(pair)
        all_rows.append(dict(trajectory_id=q,a=a,b=b,pair_ids=[p['pair_id'] for p in aligned],
            any_semantic_clean_a=any(e['semantic_clean'] for e in a['events']),any_semantic_clean_b=any(e['semantic_clean'] for e in b['events'])))
    save(ROOT/'audit/semantic_independent_passes_frozen.json',dict(at=now(),sealed=True,per_event_routing_opened=False,
        annotation_source_sha256=sources,manifest_sha256=sha(ROOT/'stage10b_corpus_manifest.json'),reviews=reviews))
    save(ROOT/'audit/semantic_adjudication_packet.json',dict(at=now(),rows=all_rows,pairs=pairs,
        independent_passes_sha256=sha(ROOT/'audit/semantic_independent_passes_frozen.json'),
        trajectory_semantic_agreement=agreement([r['any_semantic_clean_a'] for r in all_rows],[r['any_semantic_clean_b'] for r in all_rows]),
        note='Onset proximity only proposes matches; main adjudicator must verify same B source/fact before calculating event agreement. No detector/routing revealed.'))
    print('SEMANTIC PASSES SEALED',len(ids),'trajectories',len(pairs),'candidate event pairs',flush=True)


if __name__=='__main__':main()
