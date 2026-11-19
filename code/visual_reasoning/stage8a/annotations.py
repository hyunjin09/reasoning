"""Explicit occurrence disambiguation for reviewed repeated native reasoning."""
import re

from .events import align_literal_event


def align_reviewed_event(rows,*,quote,value,occurrence=None):
    if occurrence is None:
        return align_literal_event(rows,quote=quote,value=value)
    if not quote or not value or quote.count(value)!=1:
        raise ValueError("Quote must identify exactly one value occurrence")
    if [int(r["token_index"]) for r in rows]!=list(range(len(rows))):
        raise ValueError("Native token indices must be contiguous")
    text="".join(r["decoded_token"] for r in rows)
    starts=[m.start() for m in re.finditer(re.escape(quote),text)]
    if not isinstance(occurrence,int) or not 0<=occurrence<len(starts):
        raise ValueError("Explicit quote occurrence is out of range")
    begin=starts[occurrence]+quote.index(value)
    end=begin+len(value)
    offsets=[]
    cursor=0
    for row in rows:
        stop=cursor+len(row["decoded_token"])
        offsets.append((cursor,stop))
        cursor=stop
    selected=[i for i,(a,b) in enumerate(offsets) if a<end and b>begin]
    if not selected or offsets[selected[0]][0]!=begin or offsets[selected[-1]][1]!=end:
        raise ValueError("Evidence value must end and start at a native token boundary")
    start,stop=selected[0],selected[-1]+1
    if start==0:
        raise ValueError("Event needs a nonempty native reasoning prefix")
    return dict(quote=quote,readout=value,char_start=begin,char_end=end,prefix_length=start,evidence_end_token=stop,
                prefix_token_ids=[int(r["token_id"]) for r in rows[:start]],evidence_token_ids=[int(r["token_id"]) for r in rows[start:stop]],
                history_text=text[:begin],quote_occurrence=occurrence,quote_match_count_in_reviewed_prefix=len(starts))
