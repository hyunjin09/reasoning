"""Expose sealed target-specific measurements to independent second passes."""
from scripts.stage10b.common import ROOT,load,save,sha,now


def main():
    sp=ROOT/'audit/semantic_adjudication_frozen.json';semantic=load(sp)
    assert semantic['sealed'] and not semantic['routing_opened']
    rp=ROOT/'audit/reaccess_combined.json';routing=load(rp)
    assert routing['semantic_sha256']==sha(sp)
    measurements={r['event_id']:r for r in routing['rows']}
    rows=[]
    for event in semantic['events']:
        r=measurements[event['event_id']]
        rows.append(dict(event_id=event['event_id'],trajectory_id=event['trajectory_id'],
            B_fact_required=event['B_fact_required'],B_source=event['B_source'],
            B_onset_quote=event['B_onset_quote'],B_observation_quote=event.get('B_observation_quote'),
            target_roi_normalized=event.get('target_roi_normalized'),
            irrelevant_roi_normalized=event.get('irrelevant_roi_normalized'),
            onset=event['onset'],observation_offset=event.get('observation_offset'),
            detector_compatibility=r.get('detector_compatibility'),coverage_complete=r['coverage_complete'],
            measured_tokens=r['measured_tokens'],target_positions=r.get('target_positions',[]),
            irrelevant_positions=r.get('irrelevant_positions',[]),
            threshold=r.get('threshold',.5478025980771918),measurements=r['rows']))
    save(ROOT/'audit/reaccess_review_packet.json',dict(at=now(),rows=rows,
        semantic_sha256=sha(sp),routing_sha256=sha(rp),
        blinding='Computed C5/lag/classification and other reviewer labels are withheld. Semantic anchors/ROIs are sealed.',
        rule='Offsets0–31; target image mass>=.05 and target/control patch-mean ratio>=1.5 for2 consecutive measured tokens. '
             'Either detector>tau on those2 tokens, or explicit B observation at offset0–31. Missing target=>TARGET_AMBIGUOUS; '
             'missing/incomplete usable measurements with no observed positive=>ROUTING_DATA_MISSING. '
             'Complete data+detector positivity but no selective run=>ATTENTION_ONLY; other complete negative=>NEW_DEMAND_NO_REACCESS.',
        output_schema={'reviewer':'a or b','rows':[{'event_id':'...','C5':False,'lag':None,'classification':'...','reason':'...'}]}))
    print('REACCESS REVIEW PACKET',len(rows),'events',flush=True)


if __name__=='__main__':main()
