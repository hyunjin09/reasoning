"""Stable group assignment; no model-derived inputs."""
import hashlib


def connected_groups(ids, links):
    parent={key:key for key in ids}
    def root(key):
        while parent[key]!=key:
            parent[key]=parent[parent[key]];key=parent[key]
        return key
    for left,right in links:
        if left not in parent or right not in parent:continue
        a,b=root(left),root(right)
        parent[max(a,b)]=min(a,b)
    groups={}
    for key in sorted(parent):groups.setdefault(root(key),[]).append(key)
    return list(groups.values())


def assign_split(group_id,seed=60972,discovery_fraction=1/3):
    value=int(hashlib.sha256(f'{seed}:{group_id}'.encode()).hexdigest()[:16],16)/2**64
    return 'discovery' if value<discovery_fraction else 'confirmation'


def extension_assignments(prior, new_ids, links, overlap_ids=None):
    """Append prospective images without reassigning any acquired source family.

    A new image bridging existing folds remains in prevalence accounting but is
    excluded from split-dependent analysis. Existing identities never change.
    """
    overlap_ids=overlap_ids or {}
    edges=list(links)
    ids=set(prior)|set(new_ids)|set(overlap_ids)|{key for edge in edges for key in edge}
    existing_groups={}
    for key,row in prior.items():existing_groups.setdefault(row['group_id'],[]).append(key)
    for members in existing_groups.values():edges.extend((members[0],key) for key in members[1:])
    result={};fresh=set(new_ids)
    for members in connected_groups(ids,edges):
        new_members=fresh.intersection(members)
        if not new_members:continue
        group_ids=sorted({prior[k]['group_id'] for k in members if k in prior})
        folds={prior[k]['split'] for k in members if k in prior}
        overlaps={overlap_ids[k] for k in members if k in overlap_ids}
        group_id=group_ids[0] if len(group_ids)==1 else 'source_group_'+hashlib.sha256('|'.join(members).encode()).hexdigest()[:16]
        if overlaps:split='excluded_'+('historical' if 'historical' in overlaps else 'validation')+'_overlap'
        elif len(folds)>1:split='excluded_cross_fold_bridge'
        elif folds:split=next(iter(folds))
        else:split=assign_split(group_id)
        for key in new_members:result[key]=dict(group_id=group_id,split=split,linked_existing_group_ids=group_ids)
    assert set(result)==fresh
    return result
