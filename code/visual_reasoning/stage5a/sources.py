"""Attention-independent source masks, explicit aliases and irrelevant controls."""
import math
import numpy as np
from visual_reasoning.stage3b7.roi import map_changed_pixels_to_tokens, fixed_ring, choose_matched_irrelevant


def source_pixel_mask(fact,shape):
    height,width=shape[:2];mask=np.zeros((height,width),dtype=bool)
    for box in fact.get('roi_boxes',[fact['roi']]):
        x0,y0,x1,y1=map(int,box)
        if not (0<=x0<x1<=width and 0<=y0<y1<=height):
            raise ValueError(f'Source box outside native image: {box} versus {width}x{height}')
        mask[y0:y1,x0:x1]=True
    return mask


def event_groups(event,facts,local_maps,visual,grid,darkness):
    _,rows,cols=grid
    sources=event.get('joint_source_ids',[event['source']])
    t=sorted(set().union(*(set(local_maps[k]) for k in sources)))
    groups={'T':t};aliases={};overlap={};identities={'T':sources}
    m=event.get('mentioned_source',event['source'])
    if m in sources:aliases['M']='T'
    elif m in facts:
        groups['M']=local_maps[m];identities['M']=[m]
    explicit=event.get('alternative_source')
    candidates=([explicit] if explicit else [k for k in facts if k not in sources])
    for x in candidates:
        if x not in facts or x in sources:continue
        if set(local_maps[x])==set(t):
            aliases['X']='T';continue
        if 'M' in groups and set(local_maps[x])==set(groups['M']):
            aliases['X']='M';break
        if set(local_maps[x]) & set(t):
            overlap['excluded_X_'+x]=sorted(set(local_maps[x]) & set(t));continue
        groups['X']=local_maps[x];identities['X']=[x];break
    if 'M' in groups and set(groups['M']) & set(t):
        overlap['M_T']=sorted(set(groups['M']) & set(t))
    all_sources=sorted(set().union(*(set(v) for v in local_maps.values())))
    excluded=fixed_ring(all_sources,merged_rows=rows,merged_cols=cols,radius=1)
    try:
        irrelevant,audit=choose_matched_irrelevant(target_local=t,excluded_local=excluded,darkness_by_cell=darkness)
        # Blank/near-blank controls are conservatively identifiable without guessing
        # whether another diagram component is irrelevant to the current claim.
        if audit['mean_darkness']>.03:raise ValueError('No low-ink irrelevant control under frozen .03 mean-darkness limit')
        if not math.isfinite(audit['distance_from_target_center']):audit['distance_from_target_center']=None
        groups['I']=irrelevant
    except ValueError as error:audit={'unavailable':str(error)}
    alternative=groups.get('X',groups.get('M'))
    if alternative is not None:groups['joint']=sorted(set(t)|set(alternative))
    return {'source_groups':{k:[visual[i] for i in v] for k,v in groups.items()},
            'local_source_groups':groups,'source_identities':identities,'roi_aliases':aliases,
            'source_overlap':overlap,'irrelevant_mapping':audit,
            'alternative_selection':'explicit semantic alternative if supplied; otherwise first independent annotated source in frozen source order',
            'mentioned_source_resolved':m,'demanded_sources':sources}
