"""Normalize verbatim semantic annotations without exposing passive signals."""
import bisect
from pathlib import Path
from scripts.stage10b.common import ROOT,load,sha


def rows_for(who):
    rows={};sources={}
    for path in sorted((ROOT/f'annotations/annotator_{who}').glob('batch_*.json')):
        data=load(path);sources[str(path)]=sha(path)
        for row in data['rows']:
            key=row['trajectory_id']
            if key in rows:assert row.get('supersedes') or data.get('supersedes'),f'Duplicate unversioned review:{who}:{key}'
            rows[key]=row
    return rows,sources


def quoted_span(packet,paragraph,quote):
    if paragraph is None or not quote:return None
    p=packet['paragraphs'][paragraph];assert quote in p['text'],(packet['trajectory_id'],paragraph,quote)
    start=p['char_start']+p['text'].index(quote);end=start+len(quote);offsets=packet['token_character_offsets']
    return dict(char_start=start,char_end=end,token_start=bisect.bisect_right(offsets,start)-1,token_end=bisect.bisect_left(offsets,end))


def normalize(row,who):
    packet=load(ROOT/f"packets/{row['trajectory_id']}.json");events=[]
    assert row.get('coverage') and (row.get('negative_reason') or row.get('events'))
    for i,event in enumerate(row.get('events',[])):
        e=dict(event);A=quoted_span(packet,e['A_paragraph'],e['A_resolution_quote']);B=quoted_span(packet,e['B_paragraph'],e['B_onset_quote'])
        observation=quoted_span(packet,e.get('observation_paragraph'),e.get('B_observation_quote'))
        assert B and A and A['char_end']<=B['char_start'],(row['trajectory_id'],e['local_id'])
        assert e['prior_availability'] in ('ABSENT','PARTIAL','SUFFICIENT','AMBIGUOUS')
        assert e['taxonomy'] in ('S1','S2','S3')
        assert e['C4']==(e['prior_availability']=='ABSENT'),(row['trajectory_id'],e['local_id'],'C4')
        assert e['semantic_clean']==all(e[c] for c in ('C1','C2','C3','C4'))
        for key in ('target_roi_normalized','irrelevant_roi_normalized'):
            box=e.get(key)
            if box is not None:assert len(box)==4 and 0<=box[0]<box[2]<=1 and 0<=box[1]<box[3]<=1
        events.append(dict(e,annotator=who,trajectory_id=row['trajectory_id'],A_span=A,B_span=B,observation_span=observation,
            onset=B['token_start'],intervening_tokens=B['token_start']-A['token_end'],
            observation_offset=observation['token_start']-B['token_start'] if observation else None,
            annotation_event_id=f"{who}:{row['trajectory_id']}:{e['local_id']}"))
    return dict(row,events=events,packet_sha256=sha(ROOT/f"packets/{row['trajectory_id']}.json"))
