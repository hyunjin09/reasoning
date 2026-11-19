"""Materialize explicit main-adjudication decisions without any passive access."""
from scripts.stage10b.common import ROOT,load,save,sha,now
from scripts.stage10b.annotation_io import normalize


def main():
    ip=ROOT/'audit/semantic_independent_passes_frozen.json';independent=load(ip)
    dp=ROOT/'audit/semantic_adjudication_decisions.json';decisions=load(dp)
    assert decisions['review_complete'] and not decisions['routing_opened']
    raw={e['annotation_event_id']:e for reviews in independent['reviews'].values() for r in reviews.values() for e in r['events']}
    used=[];events=[]
    for index,d in enumerate(decisions['event_groups']):
        ids=d['annotation_ids'];assert ids and d['selected_id'] in ids and d['reason']
        assert all(x in raw for x in ids);used.extend(ids)
        e=dict(raw[d['selected_id']]);e.update(d.get('overrides',{}))
        e['semantic_clean']=all(e[c] for c in ('C1','C2','C3','C4'))
        # Recompute character/token spans from final exact quotes, never inherited stale spans.
        r=normalize(dict(trajectory_id=e['trajectory_id'],coverage='main adjudication',events=[e]),'adjudicated')
        e=r['events'][0];e.update(event_id=f'event_{index:04d}',annotation_ids=ids,adjudication_reason=d['reason'],
                               source_pair_same=d.get('source_pair_same'),packet_sha256=r['packet_sha256'])
        assert e['intervening_tokens']>=0
        if e['semantic_clean'] and e.get('observation_offset') is not None:
            assert e['observation_offset']>=0,(e['event_id'],'Observation precedes ABSENT demand; inspect exact quote.')
        events.append(e)
    assert len(used)==len(set(used)) and set(used)==set(raw),'Every independent annotation event must be preserved exactly once'
    trajectories=decisions['trajectories'];ids=[r['trajectory_id'] for r in trajectories]
    expected=set(independent['reviews']['a'])
    assert set(ids)==expected and len(ids)==len(expected)
    for r in trajectories:
        own=[e for e in events if e['trajectory_id']==r['trajectory_id']]
        assert r['reason']
        if not any(e['semantic_clean'] for e in own):assert r['negative_category']
    save(ROOT/'audit/semantic_adjudication_frozen.json',dict(at=now(),sealed=True,routing_opened=False,
        independent_passes_sha256=sha(ip),decisions_sha256=sha(dp),events=events,trajectories=trajectories,
        main_review_notes_sha256=sha(ROOT/'audit/main_semantic_review_notes.md'),
        matching_note='Explicit main-reviewed source/fact grouping. Raw independent annotation IDs retained.',
        conditions_unchanged=True,new_semantic_labels_after_routing=False))
    print('SEMANTIC ADJUDICATION SEALED',len(events),'events;',len({e['trajectory_id'] for e in events if e['semantic_clean']}),'C1–C4 trajectories',flush=True)


if __name__=='__main__':main()
