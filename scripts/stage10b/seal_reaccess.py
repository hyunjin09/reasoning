"""Seal independently reviewed C5 and compute raw, not adjudicated, agreement."""
from collections import Counter
from scripts.stage10b.common import ROOT,load,save,sha,now
from scripts.stage10b.protocol import agreement


def acceptable(r):
    return r['raw'] is not None and r['kappa'] is not None and r['raw']>=.8 and r['kappa']>=.6


def main():
    sp=ROOT/'audit/semantic_adjudication_frozen.json';semantic=load(sp)
    rp=ROOT/'audit/reaccess_combined.json';routing=load(rp);by={r['event_id']:r for r in routing['rows']}
    packet=ROOT/'audit/reaccess_review_packet.json';reviews={};paths={}
    for who in 'ab':
        path=ROOT/f'annotations/reaccess_{who}.json';data=load(path)
        assert data['sealed'] and data['packet_sha256']==sha(packet)
        items=data['rows'];reviews[who]={r['event_id']:r for r in items};paths[str(path)]=sha(path)
        assert len(items)==len(by) and set(reviews[who])==set(by)
        assert all(r.get('reason') for r in items)
    differences=[]
    for eventid,r in by.items():
        for who in 'ab':
            q=reviews[who][eventid]
            if any(q[k]!=r[k] for k in ('C5','lag','classification')):
                differences.append(dict(event_id=eventid,reviewer=who,raw={k:q[k] for k in ('C5','lag','classification')},
                                        computed={k:r[k] for k in ('C5','lag','classification')}))
    if differences:
        resolution=load(ROOT/'audit/reaccess_disagreement_resolution.json')
        assert resolution['review_complete'] and resolution['differences']==differences
        assert resolution['outcome']=='Frozen arithmetic verified; retain computed decisions and preserve raw reviews.'
    independent=load(ROOT/'audit/semantic_independent_passes_frozen.json')
    raw={e['annotation_event_id']:e for rows in independent['reviews'].values() for r in rows.values() for e in r['events']}
    matched=[];union=[];onsets=[]
    clean={who:{tid:False for tid in independent['reviews'][who]} for who in 'ab'}
    for e in semantic['events']:
        members={raw[q]['annotator']:raw[q] for q in e['annotation_ids']}
        assert len(members)==len(e['annotation_ids']),'At most one nomination per pass in an adjudicated same-event group'
        union.append([members[who]['prior_availability'] if who in members else 'NOT_NOMINATED' for who in 'ab'])
        if len(members)==2:
            matched.append([members[who]['prior_availability'] for who in 'ab'])
            onsets.append(dict(event_id=e['event_id'],difference=abs(members['a']['onset']-members['b']['onset'])))
        for who,r in members.items():
            if r['semantic_clean'] and reviews[who][e['event_id']]['C5']:clean[who][r['trajectory_id']]=True
    ids=sorted(clean['a']);assert ids==sorted(clean['b'])
    semantic_agree=agreement([any(e['semantic_clean'] for e in independent['reviews']['a'][tid]['events']) for tid in ids],
                              [any(e['semantic_clean'] for e in independent['reviews']['b'][tid]['events']) for tid in ids])
    ma=agreement([x[0] for x in matched],[x[1] for x in matched]);ua=agreement([x[0] for x in union],[x[1] for x in union])
    c5=agreement([reviews['a'][q]['C5'] for q in by],[reviews['b'][q]['C5'] for q in by])
    ca=agreement([clean['a'][tid] for tid in ids],[clean['b'][tid] for tid in ids])
    onset=dict(n=len(onsets),within8=sum(r['difference']<=8 for r in onsets),
               raw=sum(r['difference']<=8 for r in onsets)/len(onsets) if onsets else None,rows=onsets)
    decisions=load(ROOT/'audit/semantic_adjudication_decisions.json');sources=decisions['proposed_pair_source_review']
    expected={p['pair_id'] for p in load(ROOT/'audit/semantic_adjudication_packet.json')['pairs'] if p['automatically_matched']}
    assert {r['pair_id'] for r in sources}==expected and len(sources)==len(expected)
    source=dict(n=len(sources),same=sum(r['same_source_fact'] for r in sources),
                raw=sum(r['same_source_fact'] for r in sources)/len(sources) if sources else None,rows=sources)
    good=acceptable(ma) and acceptable(ca) and onset['raw'] is not None and onset['raw']>=.8 and source['raw'] is not None and source['raw']>=.8
    result=dict(at=now(),semantic_trajectory=semantic_agree,availability_matched=ma,availability_union=ua,C5_event=c5,clean_trajectory=ca,
        onset=onset,source=source,acceptable_for_strong_go=good,
        gate_components=dict(availability=acceptable(ma),clean_status=acceptable(ca),
                             onset=onset['raw'] is not None and onset['raw']>=.8,source=source['raw'] is not None and source['raw']>=.8),
        unmatched_event_groups=sum('NOT_NOMINATED' in x for x in union),routing_disagreements=differences,
        semantic_disagreement_reasons=[dict(event_id=e['event_id'],reason=e['adjudication_reason'],annotation_ids=e['annotation_ids'])
                                      for e in semantic['events']],
        clean_independent_by_trajectory=[dict(trajectory_id=tid,a=clean['a'][tid],b=clean['b'][tid]) for tid in ids],
        reviews_sha256=paths,semantic_sha256=sha(sp),
        limitation='Two independent model-agent review passes, no independent human raters. C5 reviews use shared adjudicated semantic targets; raw semantic decisions remain separate. Source agreement uses all proposed temporal pairs, including source mismatches.')
    save(ROOT/'stage10b_annotation_agreement.json',result)
    save(ROOT/'audit/reaccess_adjudicated.json',dict(at=now(),sealed=True,semantic_sha256=sha(sp),routing_sha256=sha(rp),
        rows=[dict(r,review_a=reviews['a'][q],review_b=reviews['b'][q]) for q,r in by.items()],
        review_source_sha256=paths,disagreement_count=len(differences),new_semantic_labels_after_routing=False))
    print('C5 SEALED',len(by),'events; acceptable agreement',good,flush=True)


if __name__=='__main__':main()
