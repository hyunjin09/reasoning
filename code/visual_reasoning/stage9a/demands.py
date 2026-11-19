"""Text-only bounded visual-demand nomination, independent of model measurements."""
import hashlib
import re

PATTERN = re.compile(
    r"\b(?:(?:look(?:ing)?\s+at|from|in|according\s+to|as\s+shown\s+in)\s+"
    r"(?:the\s+)?(?:figure|diagram|image|graph|table|drawing|picture)\b|"
    r"(?:the\s+)?(?:diagram|figure|image|graph|table|drawing|picture)\s+"
    r"(?:shows?|indicates?|depicts?|has|gives?|contains?)\b)", re.I)


def nominate(token_rows, start, end, task_id):
    """Earliest explicit visual mention in each quarter, including empty quarters."""
    import bisect
    pieces=[r["decoded_token"] for r in token_rows]
    text="".join(pieces)
    offsets=[0]
    for piece in pieces:
        offsets.append(offsets[-1]+len(piece))
    candidates={}
    if end<=start:
        return []
    for match in PATTERN.finditer(text,offsets[start],offsets[end]):
        token=bisect.bisect_right(offsets,match.start())-1
        quarter=min(3,int(4*(token-start)/(end-start)))
        if quarter in candidates:
            continue
        lo=max(start,token-96);hi=min(end,token+192)
        # Include full surrounding paragraph, bounded to 512 generated tokens.
        para_start=text.rfind("\n\n",offsets[start],match.start())
        para_end=text.find("\n\n",match.end(),offsets[end])
        if para_start>=0:
            lo=max(start,token-256,min(lo,bisect.bisect_right(offsets,para_start+2)-1))
        if para_end>=0:
            hi=min(end,token+256,max(hi,bisect.bisect_left(offsets,para_end)))
        event_id="d_"+hashlib.sha256(f"stage9a:{task_id}:{token}".encode()).hexdigest()[:20]
        candidates[quarter]=dict(event_id=event_id,demand_token=token,quarter=quarter,
            nomination=match.group(),excerpt_start=lo,excerpt_end=hi,
            excerpt=text[offsets[lo]:offsets[hi]],review_status="pending",
            eligibility_note="Explicit visual mention only; semantic demand/source/readout require review.")
    return list(candidates.values())
