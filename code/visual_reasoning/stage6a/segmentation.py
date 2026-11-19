"""Attention-independent spans using original incremental token pieces."""
import bisect
import re


def segment_native(tokens):
    pieces=[r['decoded_token'] for r in tokens];raw=''.join(pieces)
    offsets=[0]
    for piece in pieces:offsets.append(offsets[-1]+len(piece))
    marker=raw.find('</think>');regions=[]
    start=len('<think>') if raw.startswith('<think>') else 0
    if marker>=0:
        regions=[('reasoning',start,marker),('final',marker+len('</think>'),len(raw))]
    else:regions=[('reasoning',start,len(raw))]
    result=[]
    for section,char_start,char_end in regions:
        text=raw[char_start:char_end]
        if '\n' in text.strip():pattern=r'\n+'
        elif re.search(r'[.!?]\s+',text):pattern=r'[.!?]\s+'
        else:pattern=r';\s*'
        cuts=[char_start+m.end() for m in re.finditer(pattern,text)]+[char_end]
        left=bisect.bisect_left(offsets,char_start)
        for desired in cuts:
            right=min(len(tokens),bisect.bisect_left(offsets,desired))
            if right<=left:continue
            span_text=''.join(pieces[left:right])
            if span_text.strip() and span_text.strip()!='<|im_end|>':
                result.append(dict(span_id=f'S{len(result):04}',section=section,
                    token_start=left,token_end=right,char_start=offsets[left],char_end=offsets[right],
                    text=span_text,normalized_token_progress=left/max(1,len(tokens)),
                    boundary_expanded_to_native_token=offsets[right]!=desired,
                    segmentation_rule='newline' if pattern==r'\n+' else 'sentence' if pattern==r'[.!?]\s+' else 'semicolon',
                    native_token_ids=[r['token_id'] for r in tokens[left:right]]))
            left=right
    return result
