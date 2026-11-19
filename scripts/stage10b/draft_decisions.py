"""Make an explicitly UNREVIEWED adjudication worksheet from sealed raw passes."""
from scripts.stage10b.common import ROOT,load,save,now


def category(reason):
    if 'SHORT' in reason:return 'TRACE_TOO_SHORT'
    if any(x in reason for x in ('UNRESOLVED','NO_RESOLVED','NO_EARLIER')):return 'NO_RESOLVED_VISUAL_A'
    if any(x in reason for x in ('CONTINUOUS','INTERVAL','INVENTORY')):return 'NO_TEXT_INTERVAL'
    if any(x in reason for x in ('AMBIGUOUS','PARTIAL')):return 'TARGET_AMBIGUOUS'
    if any(x in reason for x in ('TEXTUALIZED','GIVEN','FRONT_LOADED')):return 'B_ALREADY_TEXTUALIZED'
    return 'NO_NEW_REQUIRED_DEMAND'


def main():
    packet=load(ROOT/'audit/semantic_adjudication_packet.json');groups=[];source=[]
    for p in packet['pairs']:
        raw=[p[k] for k in ('a','b') if p[k]];chosen=raw[0]
        groups.append(dict(pair_id=p['pair_id'],annotation_ids=[e['annotation_event_id'] for e in raw],
                           selected_id=chosen['annotation_event_id'],overrides={},reason='UNREVIEWED',
                           source_pair_same=None))
        if len(raw)==2:source.append(dict(pair_id=p['pair_id'],same_source_fact=None,reason='UNREVIEWED'))
    trajectories=[]
    for r in packet['rows']:
        a,b=r['a'],r['b'];reason=a.get('negative_reason') or b.get('negative_reason') or 'SEMANTIC_CANDIDATE'
        trajectories.append(dict(trajectory_id=r['trajectory_id'],negative_category=category(reason),
                                  reason='UNREVIEWED',raw_negative_reason_a=a.get('negative_reason'),raw_negative_reason_b=b.get('negative_reason')))
    save(ROOT/'audit/semantic_adjudication_worksheet.json',dict(at=now(),review_complete=False,routing_opened=False,
         event_groups=groups,proposed_pair_source_review=source,trajectories=trajectories,
         warning='Draft worksheet only. Every source match and potential C1–C4 positive requires main review before a semantic seal.'))
    print('UNREVIEWED WORKSHEET',len(groups),'event groups',flush=True)


if __name__=='__main__':main()
