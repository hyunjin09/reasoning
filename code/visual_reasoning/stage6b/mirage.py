"""Strict semantic mirage labels; correctness is deliberately not an input."""


def classify(intact,stress,sham,cf,render_sham_effect,mechanical,rule):
    floor=rule['effect_floor'];fraction=rule['collapse_fraction']
    semantic=cf>floor+abs(render_sham_effect)
    baseline=intact['vsd']>floor and intact['margin']>floor
    engagement={k:stress[k]>=rule['engagement_retention']*intact[k]
                and stress[k]>=threshold for k,threshold in rule['absolute_engagement'].items()}
    collapse=baseline and abs(stress['vsd'])<=max(floor,fraction*intact['vsd']) and stress['margin']<=fraction*intact['margin']
    specific=baseline and sham['vsd']>=rule['sham_grounding_retention']*intact['vsd'] and sham['vsd']-stress['vsd']>floor and sham['margin']-stress['margin']>floor
    return {'strict_mirage':bool(semantic and collapse and specific and any(engagement.values()) and mechanical),
            'semantic_followability':bool(semantic),'grounded_intact':bool(baseline),
            'grounding_collapsed':bool(collapse),'engagement_retained':engagement,
            'target_specific_collapse':bool(specific),'mechanically_verified':bool(mechanical)}
