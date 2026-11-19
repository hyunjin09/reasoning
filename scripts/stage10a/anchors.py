"""Gold/outcome-independent semantic boundaries and deterministic image selection."""
import hashlib


def locate(text, fact, post):
    pre=text.index(fact);emit=pre+len(fact)
    end=text.index(post,emit)+len(post)
    assert 0<=pre<emit<end<=len(text)
    return dict(pre_char=pre,emit_char=emit,post_char=end)


def choose_cohort(rows):
    assert len({r['image_id'] for r in rows})==len(rows)
    assert len(rows)==32,'Must resolve one eligible event for all32 existing images'
    key=lambda r:hashlib.sha256(('stage10a-v1-920260927:'+r['image_id']).encode()).hexdigest()
    groups={a:sorted([r for r in rows if r['attribute']==a],key=key) for a in ('color','shape')}
    assert all(len(v)>=12 for v in groups.values()),'Balanced primary24 must be feasible'
    primary=sorted(groups['color'][:12]+groups['shape'][:12],key=key)
    reserve=sorted(groups['color'][12:]+groups['shape'][12:],key=key)
    assert len(primary)==24 and len(reserve)==8
    return primary,reserve
