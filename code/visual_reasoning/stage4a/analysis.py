"""Within-base source, trigger, and semantic contrasts; frozen nine-test family."""
from visual_reasoning.stage3c8.analysis import inferential_summary, holm_adjust
from visual_reasoning.stage4a.cohort import dynamic_class

EVENTS = ('A1', 'B', 'A2')
FAMILY = ('S_A1','S_B','S_A2','Switch_AB','Refresh_BA','demanded_minus_irrelevant','TS_A1','TS_B','TS_A2')


def source_effects(event_rows, window=2):
    return {e:{x:event_rows[e]['arms']['N']['D']-event_rows[e]['arms'][f'{x}_W{window}']['D']
               for x in ('A','B')} for e in EVENTS}


def primary_contrasts(event_rows, window=2):
    effects = source_effects(event_rows, window)
    result = {**dynamic_class(effects), 'VSD':effects}
    if window == 2 and all('I_W2' in event_rows[e]['arms'] for e in EVENTS):
        i_vsd = {e:event_rows[e]['arms']['N']['D']-event_rows[e]['arms']['I_W2']['D'] for e in EVENTS}
        result['irrelevant_VSD'] = i_vsd
        result['demanded_minus_irrelevant'] = sum(effects[e]['B' if e=='B' else 'A']-i_vsd[e] for e in EVENTS)/3
    if window == 2:
        result['joint_AB'] = {e:event_rows[e]['arms']['N']['D']-event_rows[e]['arms']['AB_W2']['D'] for e in EVENTS}
    return result


def trigger_contrasts(primary, trigger_rows):
    result = {'TE':{}, 'R16_VSD':{}}
    for e in EVENTS:
        arms = trigger_rows[e]['arms']
        under = {x:arms['R16']['D']-arms[f'R16_{x}_W2']['D'] for x in ('A','B')}
        te = {x:primary['VSD'][e][x]-under[x] for x in ('A','B')}
        demanded, other = ('B','A') if e=='B' else ('A','B')
        result['R16_VSD'][e] = under
        result['TE'][e] = te
        result['TS_'+e] = te[demanded]-te[other]
    return result


def primary_family(bases, triggers=None):
    summaries = {}
    for name in FAMILY:
        source = triggers or {} if name.startswith('TS_') else bases
        values = {b:r[name] for b,r in source.items() if name in r}
        summaries[name] = inferential_summary(values)
        summaries[name]['status'] = 'scored' if values else 'gated_unrun'
    adjusted = holm_adjust([summaries[name]['wilcoxon_p'] for name in FAMILY])
    for name, p in zip(FAMILY, adjusted):
        s = summaries[name]; s['holm_p'] = p
        s['robust_positive'] = bool(s['N_unique_bases'] and p<.05 and s['median']>0
            and s['bootstrap_mean_ci95'][0]>0 and s['positive_fraction']>=.75)
    return summaries


def semantic_contrasts(condition_rows):
    result = {}
    for e in EVENTS:
        d = {c:condition_rows[c][e]['arms']['N']['D'] for c in ('OO','AO','OB','AB','A_sham','B_sham')}
        ca = [d['OO']-d['AO'], d['OB']-d['AB']]
        cb = [d['OO']-d['OB'], d['AO']-d['AB']]
        a, b = sum(ca)/2, sum(cb)/2
        demanded, other = (b,a) if e=='B' else (a,b)
        sham = abs(d['OO']-d['B_sham' if e=='B' else 'A_sham'])
        result[e] = {'D':d,'A_effect':a,'B_effect':b,'A_factorial_contexts':ca,'B_factorial_contexts':cb,
                     'demanded_effect':demanded,'other_effect':other,'semantic_selectivity':demanded-other,
                     'demanded_sham_magnitude':sham,'semantic_minus_sham':demanded-sham,
                     'A_sham_signed':d['OO']-d['A_sham'],'B_sham_signed':d['OO']-d['B_sham']}
    return result


def failure_phenotypes(base, floor=.05):
    v = base['VSD']
    return {
        'successful_switch':base['S_A1']>0 and base['S_B']>0 and v['A1']['A']>floor and v['B']['B']>floor,
        'successful_refresh':base['S_B']>0 and base['S_A2']>0 and v['B']['B']>floor and v['A2']['A']>floor,
        'failed_switch_A_dominant':base['S_B']<0 and v['B']['A']>floor,
        'failed_refresh_stale_B':base['S_A2']<0 and v['A2']['B']>floor,
        'tied_retrieval_events':[e for e in EVENTS if v[e]['A']==v[e]['B'] and v[e]['A']>floor],
        'mixed_retrieval_events':[e for e in EVENTS if min(v[e].values())>floor],
        'local_insensitive_events':[e for e in EVENTS if max(v[e].values())<=floor],
        'dynamic_full':base['dynamic'],
    }
