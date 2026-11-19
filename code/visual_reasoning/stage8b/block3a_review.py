"""Exact text alignment and frozen retrieval matching without source features."""
import numpy as np


def align_read(pieces, judgment, episodes):
    text=''.join(pieces);quote=judgment['quote'];a=judgment['quote_start'];readout=judgment['readout']
    if type(a)!=int or a<0 or text[a:a+len(quote)]!=quote or quote.count(readout)!=1 or not readout:
        raise ValueError('Quote/readout must identify one exact native claim')
    left=a+quote.index(readout);right=left+len(readout)
    ends=np.cumsum([len(p) for p in pieces]);starts=np.r_[0,ends[:-1]]
    indices=np.flatnonzero((starts<right)&(ends>left))
    if not len(indices) or indices[0]==0:
        raise ValueError('No generated predicting query for claim')
    claim=int(indices[0]);candidates=[e for e in episodes if max(0,e['start_token']-16)<=claim<=e['end_token']+128]
    selected=min(candidates,key=lambda e:(abs(e['start_token']-claim),e['start_token'])) if candidates else None
    return dict(claim_char_start=left,claim_char_end=right,claim_start_token=claim,claim_end_token=int(indices[-1]+1),
        predicting_generated_query=claim-1,retrieval_eligible=selected is not None,
        episode_index=selected['episode_index'] if selected else None,
        episode_start=selected['start_token'] if selected else None,episode_end=selected['end_token'] if selected else None)
