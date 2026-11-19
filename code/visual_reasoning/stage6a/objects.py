"""Conservative object-claim extraction; preserve uncertainty separately."""
import re


def extract_object_claims(text, aliases):
    inverse={word.lower():category for category,words in aliases.items() for word in words}
    expression=r'(?<!\w)(?:'+'|'.join(re.escape(w) for w in sorted(inverse,key=lambda x:(-len(x),x)))+r')(?!\w)'
    claims=[]
    for match in re.finditer(expression,text,re.I):
        category=inverse[match[0].lower()]
        if category=='orange' and re.match(r'\s+(shirt|jacket|coat|hat|dress|car|truck|bus|vest|wall|color|coloured|colored)\b',text[match.end():],re.I):continue
        prefix=re.split(r'[.!?;,\n]',text[:match.start()])[-1].lower()
        prefix=re.sub(r'not\s+only','',prefix)
        if re.search(r'\b(no|not|without|absent|neither|cannot|can\x27t|don\x27t|doesn\x27t)\b',prefix):assertion='negated'
        elif re.search(r'\b(perhaps|maybe|possibly|could|might|may|if|guess|uncertain|whether)\b',prefix):assertion='uncertain'
        else:assertion='asserted'
        claims.append(dict(category=category,surface=match[0],char_start=match.start(),char_end=match.end(),assertion=assertion))
    return claims
