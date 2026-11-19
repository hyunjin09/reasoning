"""All empirical figure categories, including explicit unavailable-state panels."""
import textwrap
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, sha
from scripts.stage7a.export_analysis import load_completed
from scripts.stage7a.render_schemas import save
from visual_reasoning.stage7a.reporting import certified
from visual_reasoning.stage7a.statistics import collapse_groups


STATE_NAMES = ['FAITHFUL_READ', 'PRIOR_FILL', 'WRONG_SOURCE_READ', 'STALE_SOURCE_READ',
               'SOURCE_COUPLED_EXTRACTION_ERROR', 'DOWNSTREAM_INTEGRATION_ERROR', 'UNRESOLVED']
SHORT = ['Faithful', 'Prior fill', 'Wrong source', 'Stale source', 'Extraction', 'Integration', 'Unresolved']
COLORS = {'T': '#287d82', 'X': '#b74d43', 'I': '#859199', 'G': '#b18e42'}


def empty(ax, message='Unavailable in this frozen cohort', width=72):
    ax.axis('off')
    ax.text(.5, .5, textwrap.fill(message, width), ha='center', va='center', transform=ax.transAxes,
            fontsize=12, color='#65727b', linespacing=1.6)


def finish(fig, title, subtitle):
    fig.suptitle(title, x=.06, ha='left', fontsize=16, fontweight='bold', color='#20313b')
    fig.text(.06, .02, subtitle, fontsize=8, color='#65727b')
    fig.tight_layout(rect=(.02, .065, .98, .92))


def bars(ax, names, values, title, ylabel):
    selected = [(n, v) for n, v in zip(names, values) if v is not None]
    if not selected:
        empty(ax, title+' — no available measurements')
        return
    names, values = zip(*selected)
    ax.bar(names, values, color=[COLORS.get(n.split('_')[0], '#287d82') for n in names])
    ax.axhline(0, color='#8b949a', lw=.8)
    ax.set(title=title, ylabel=ylabel)
    ax.tick_params(axis='x', labelrotation=30)


def main():
    entries, metrics, states, _ = load_completed()
    confirm = [e for e in entries if e['split'] == 'confirmation' and e['readout_type'] == 'V'
               and e['reviewed_claim']['demand'] == 'singleton']
    artifacts, panels = {}, {}
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    def emit(fig, number, stem, title, subtitle, provenance):
        finish(fig, title, subtitle)
        artifacts.update(save(fig, f'{number:02d}_'+stem))
        panels[str(number)] = provenance
    def representative(state):
        candidates = [e for e in entries if states[e['id']]['state'] == state and certified(states[e['id']])]
        return next(iter(sorted(candidates, key=lambda e: (e['split'] != 'confirmation', e['id']))), None)
    examples = [(3, 'FAITHFUL_READ', 'faithful_target_counterfactual'), (4, 'PRIOR_FILL', 'prior_fill'),
                (5, 'WRONG_SOURCE_READ', 'wrong_source_error_suppression'),
                (6, 'WRONG_SOURCE_READ', 'wrong_source_counterfactual'),
                (7, 'STALE_SOURCE_READ', 'stale_source'),
                (8, 'SOURCE_COUPLED_EXTRACTION_ERROR', 'extraction_error'),
                (9, 'DOWNSTREAM_INTEGRATION_ERROR', 'integration_error')]
    for number, state, stem in examples:
        fig, axes = plt.subplots(1, 3, figsize=(14, 5.2))
        e = representative(state)
        if e is None:
            for ax in axes: ax.axis('off')
            empty(axes[1], state.replace('_', ' ')+': no Tier1/strong Tier2 example. No trace is promoted to fill this figure category.')
            provenance = dict(status='UNAVAILABLE', state=state)
            subtitle = 'Absent certified examples are a result of this finite cohort; they do not show the state is absent in general.'
        else:
            m = metrics[e['id']]
            path = e['row'].get('image_path')
            if path:
                assert sha(path) == e['row']['image_sha256']
                pixels = plt.imread(path)
                axes[0].imshow(pixels)
                source_boxes = []
                for role, physical in [('T', e['physical_demanded_source']), ('X', e['physical_alternative_source'])]:
                    field = e['row']['fields'].get(physical)
                    if field:
                        x0, y0, x1, y1 = field['roi']
                        source_boxes.append((x0, y0, x1, y1))
                        axes[0].add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fill=False, color=COLORS[role], lw=2))
                        axes[0].annotate(role, xy=(x0, (y0+y1)/2), xytext=(-12, 0),
                                         textcoords='offset points', color=COLORS[role],
                                         fontsize=10, ha='right', va='center')
                if source_boxes:
                    # Keep the horizontal row labels while showing the source
                    # band at a legible scale on tall document pages.
                    height, width = pixels.shape[:2]
                    top = max(0, min(b[1] for b in source_boxes)-.075*height)
                    bottom = min(height, max(b[3] for b in source_boxes)+.075*height)
                    left = max(0, min(b[0] for b in source_boxes)-.30*width) if width >= 800 else 0
                    right = min(width, max(b[2] for b in source_boxes)+.10*width) if width >= 800 else width
                    axes[0].set(xlim=(left, right), ylim=(bottom, top))
                axes[0].axis('off')
                axes[0].set_title(e['base_id']+' / '+e['condition']+'\nNative source context', fontsize=10)
            else:
                empty(axes[0], 'No image input')
            if number == 4:
                pairs = {k: v['JS_nats'] for k, v in m['distribution_similarity'].items()
                         if set(k.split('__')) <= {'mask', 'unrelated', 'no_image'}}
                bars(axes[1], list(pairs), list(pairs.values()), 'Fixed-prefix availability', 'JS (nats)')
            else:
                key = 'VSD' if e['reviewed_claim']['locally_correct'] else 'EP_margin'
                names = [s+'_W2' for s in ('T', 'X', 'I', 'G')]
                bars(axes[1], names, [m['source_effects'].get(s, {}).get(key) for s in names], 'Source suppression', key+' (nats)')
            role = 'X' if number in (5, 6, 7) else 'T'
            s = m['semantic_effects'].get(role)
            if s:
                bars(axes[2], ['Native', 'Render sham', 'Semantic edit'],
                     [s[k] for k in ('native_contrast', 'sham_contrast', 'semantic_contrast')],
                     role+' source followability', 'logP(edited value) − logP(original)')
            else:
                empty(axes[2], 'Source-semantic contrast unavailable; see matched native and suppression evidence.')
            quote = e['reviewed_claim']['quote']
            if number == 9:
                quote += ' | Later: '+e['downstream_review'].get('error_quote', '')
            subtitle = e['split']+' example · '+textwrap.shorten(quote, width=175)+'\nLexicographically first certified confirmation example; discovery fallback is labeled. Full quote and effects are in figure index.'
            provenance = dict(status='OBSERVED', id=e['id'], split=e['split'], reviewed_claim=e['reviewed_claim'],
                              downstream=e['downstream_review'], metric_path='causal/'+e['split']+'_event_metrics.jsonl')
        emit(fig, number, stem, state.replace('_', ' ').title(), subtitle, provenance)

    def grouped_plot(number, stem, title, getter, ylabel):
        fig, ax = plt.subplots(figsize=(12, 5.3))
        counts = {}
        for index, state in enumerate(STATE_NAMES):
            selected = [e for e in confirm if states[e['id']]['state'] == state]
            counts[state] = len(selected)
            for offset, role in [(-.15, 'T'), (.15, 'X')]:
                rows = [dict(base_id=e['base_id'], group_id=e['group_id'], value=getter(metrics[e['id']], role)) for e in selected]
                values = list(collapse_groups(rows).values())
                if values:
                    jitter = np.linspace(-.07, .07, len(values))
                    ax.scatter(index+offset+jitter, values, s=25, color=COLORS[role], alpha=.7,
                               label=role if index == 0 else None)
        ax.axhline(0, color='#8b949a', lw=.8)
        ax.set(xticks=range(7), xticklabels=[n+'\nN='+str(counts[s]) for n, s in zip(SHORT, STATE_NAMES)], ylabel=ylabel)
        ax.legend(handles=[plt.Line2D([], [], marker='o', ls='', color=COLORS[r], label=r) for r in ('T', 'X')])
        emit(fig, number, stem, title, 'Confirmation only · each point is an image-family mean; N labels count nested singleton V events. State-selected plots are descriptive.', dict(split='confirmation', counts=counts))
    grouped_plot(10, 'source_vsd_by_state', 'Target and alternative source effects',
                 lambda m, s: m['source_effects'].get(s+'_W2', {}).get('VSD'), 'VSD (nats)')
    grouped_plot(11, 'error_promoting_effects', 'Error-oriented source effects',
                 lambda m, s: m['source_effects'].get(s+'_W2', {}).get('EP_margin') if not m['local_correctness'] else None,
                 'Actual wrong-minus-correct token margin effect (nats)')
    grouped_plot(13, 'counterfactual_followability', 'Semantic followability beyond render sham',
                 lambda m, s: m['semantic_effects'].get(s, {}).get('net_semantic_beyond_sham'), 'Semantic edit − sham contrast (nats)')

    fig, ax = plt.subplots(figsize=(10, 5.3))
    pairs = [('mask', 'unrelated'), ('mask', 'no_image'), ('unrelated', 'no_image')]
    for i, (a, b) in enumerate(pairs):
        rows = []
        for e in confirm:
            for key, value in metrics[e['id']]['distribution_similarity'].items():
                if set(key.split('__')) == {a, b}:
                    rows.append(dict(base_id=e['base_id'], group_id=e['group_id'], value=value['JS_nats']))
        values = list(collapse_groups(rows).values())
        if values: ax.scatter(i+np.linspace(-.12, .12, len(values)), values, color='#287d82', s=25)
    ax.axhline(read_json(OUT/'config/discovery_thresholds.json')['prior_js_max'], ls='--', color='#b74d43', label='Frozen discovery ceiling')
    ax.set(xticks=range(3), xticklabels=[a+' / '+b for a, b in pairs], ylabel='JS divergence (nats)')
    ax.legend()
    emit(fig, 12, 'availability_similarity', 'Masked, unrelated, and no-image similarity',
         'Confirmation · fixed native prefixes; native behavioral convergence and visual necessity are separate requirements.', dict(split='confirmation'))

    matrix = read_json(OUT/'analysis/correctness_faithfulness_matrix.json')
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, key in zip(axes, ('local_correct', 'final_correct')):
        rows = [r for r in matrix['rows'] if r['split'] == 'confirmation']
        values = np.array([[sum(r['source_fidelity'] == fidelity and r[key] is value for r in rows)
                           for value in (True, False, None)] for fidelity in ('demanded_source', 'other_or_no_source', 'unresolved')])
        ax.imshow(values, cmap='Blues', aspect='auto')
        for (i, j), count in np.ndenumerate(values):
            ax.text(j, i, str(count), ha='center', va='center', color='white' if count > values.max()/2 else '#20313b')
        ax.set(xticks=range(3), xticklabels=['Correct', 'Wrong', 'Unknown'], yticks=range(3),
               yticklabels=['Demanded source', 'Other / no source', 'Unresolved'], title=key.replace('_', ' ').title())
    emit(fig, 14, 'correctness_faithfulness', 'Correctness and causal source fidelity',
         'Confirmation · raw nested event counts, not independent samples. Source fidelity can coexist with wrong extraction; unknown final truth remains unknown.', dict(split='confirmation'))

    summary = read_json(OUT/'labels/faithfulness_metrics.json')['confirmation']['by_condition']
    for number, stem, title, names in [
        (15, 'demand_source_consistency', 'Demand–source consistency by condition', ['demand_source_consistency']),
        (16, 'grounded_evidence_rate', 'Grounded evidence rate by condition', ['grounded_evidence_rate']),
        (17, 'stress_state_rates', 'Wrong-source and prior-fill yields under controlled stress', ['wrong_source_read_rate', 'prior_fill_rate'])]:
        fig, ax = plt.subplots(figsize=(11, 5.2))
        conditions = list(summary)
        for index, name in enumerate(names):
            for i, condition in enumerate(conditions):
                r = summary[condition]['rates'][name]['certified_lower_bound_all_claims']
                if r['mean'] is None: continue
                x = i+.18*(index-(len(names)-1)/2)
                ci = r['ci95']
                ax.errorbar(x, r['mean'], yerr=None if ci is None else [[max(0, r['mean']-ci[0])], [max(0, ci[1]-r['mean'])]],
                            fmt='o', capsize=3, color=['#287d82', '#b74d43'][index], label=name.replace('_', ' ') if i == 0 else None)
        ax.set(xticks=range(len(conditions)), xticklabels=conditions, ylim=(-.04, 1.04), ylabel='Certified fraction (family-weighted)')
        for i, condition in enumerate(conditions):
            if all(summary[condition]['rates'][name]['certified_lower_bound_all_claims']['mean'] is None for name in names):
                ax.text(i, .06, 'N/A\nNo eligible claims', ha='center', va='bottom', fontsize=8, color='#65727b')
        ax.legend(fontsize=8)
        emit(fig, number, stem, title, 'Confirmation · certification lower bounds among all singleton V claims; unresolved retained. 95% image-family bootstrap; controlled sample, not prevalence.', dict(split='confirmation'))

    passive = {r['id']: r['features'] for r in read_jsonl(OUT/'passive/source_specific_features.jsonl')}
    keys = [layer+'.T_minus_X.mean_'+key for layer in ('28', '29')
            for key in ('qk_cosine', 'attention_mass', 'alpha_v_norm', 'post_wo_norm')]
    discovery = [e for e in entries if e['split'] == 'discovery' and e['readout_type'] == 'V']
    heat = np.full((7, len(keys)), np.nan)
    for j, key in enumerate(keys):
        reference = list(collapse_groups([dict(base_id=e['base_id'], group_id=e['group_id'], value=passive[e['id']].get(key)) for e in discovery]).values())
        if len(reference) < 2 or np.std(reference) == 0: continue
        for i, state in enumerate(STATE_NAMES):
            values = list(collapse_groups([dict(base_id=e['base_id'], group_id=e['group_id'], value=passive[e['id']].get(key))
                                           for e in confirm if states[e['id']]['state'] == state]).values())
            if values: heat[i, j] = (np.mean(values)-np.mean(reference))/np.std(reference)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    if np.isfinite(heat).any():
        plot = ax.imshow(np.ma.masked_invalid(heat), cmap='RdBu_r', vmin=-3, vmax=3, aspect='auto')
        ax.set(yticks=range(7), yticklabels=SHORT, xticks=range(len(keys)), xticklabels=[k.replace('.T_minus_X.mean_', '\nT−X ') for k in keys])
        ax.tick_params(axis='x', labelrotation=30)
        for i in range(len(STATE_NAMES)):
            if not np.isfinite(heat[i]).any():
                ax.text((len(keys)-1)/2, i, 'N/A — no eligible measurements', ha='center', va='center', fontsize=9, color='#65727b')
        fig.colorbar(plot, ax=ax, label='Discovery-standardized family mean')
    else: empty(ax, 'No available source-specific T−X comparisons')
    emit(fig, 18, 'passive_source_signatures', 'Source-specific passive signatures', 'Confirmation · fixed layers and aggregate features. Discovery-only scaling; descriptive state-selected means, not causal evidence.', dict(features=keys, split='confirmation'))

    probes = read_json(OUT/'monitor_feasibility/probe_results.json')
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    for ax, (task, folds) in zip(axes.flat, probes.items()):
        selected = [(name, r) for name, r in folds['primary'].items() if r['status'] == 'ESTIMATED_FEASIBILITY_ONLY']
        if not selected: empty(ax, task.replace('_', ' ')+' — insufficient classes or independent families', width=38)
        else:
            ax.barh([n.replace('_', ' ') for n, _ in selected], [r['metrics']['balanced_accuracy'] for _, r in selected], color='#287d82')
            ax.axvline(.5, color='#8b949a', ls='--')
            ax.set(xlim=(0, 1), title=task.replace('_', ' '), xlabel='Balanced accuracy')
    emit(fig, 19, 'probe_feasibility', 'Held-out probe feasibility by feature family', 'Discovery training → confirmation testing; primary source-specific family declared in advance. Matched and purged evaluations are in the full report; oracle is secondary.', dict(source='monitor_feasibility/probe_results.json'))

    readiness = read_json(OUT/'analysis/intervention_readiness.json')
    fig, ax = plt.subplots(figsize=(12, 5.5))
    rows = readiness['states']
    tests = ['sufficient_fresh_events', 'causal_direction_coherent', 'failure_readout_oriented', 'clear_corrective_prediction', 'matched_faithful_controls']
    values = np.array([[float(r['checks'][key] is True) for key in tests] for r in rows.values()])
    ax.imshow(values, cmap='Greens', vmin=0, vmax=1, aspect='auto')
    for (i, j), value in np.ndenumerate(values):
        raw_value = list(rows.values())[i]['checks'][tests[j]]
        ax.text(j, i, 'PASS' if raw_value is True else 'NO' if raw_value is False else 'UNKNOWN', ha='center', va='center', fontsize=8,
                color='white' if raw_value is True else '#20313b')
    ax.set(yticks=range(len(rows)), yticklabels=[s.replace('_', ' ').title() for s in rows],
           xticks=range(len(tests)), xticklabels=[k.replace('_', '\n') for k in tests])
    emit(fig, 20, 'intervention_readiness', 'Intervention readiness by causal state', 'Assessment only: Stage7A ran no corrective decoding, rollback, sink intervention or monitor-guided intervention.', dict(source='analysis/intervention_readiness.json'))

    data = read_json(OUT/'analysis/dataset_robustness.json')['datasets']
    fig, ax = plt.subplots(figsize=(12, 5.5))
    bottom = np.zeros(len(data))
    for state, label in zip(STATE_NAMES, SHORT):
        values = np.array([d['confirmation']['yields'][state]['events'] for d in data.values()])
        ax.bar(list(data), values, bottom=bottom, label=label)
        bottom += values
    ax.set(ylabel='Nested confirmation V events')
    ax.legend(fontsize=8, bbox_to_anchor=(1.02, 1), loc='upper left')
    emit(fig, 21, 'dataset_state_yields', 'Dataset-stratified causal state yields', 'Raw event yields, not natural prevalence or independent sample counts. No accepted MathVerse images; C1 is predominantly TabMWP tables.', dict(split='confirmation'))
    schemas = read_json(OUT/'analysis/figures/schema_artifacts.json')
    artifacts.update(schemas['artifacts'])
    for number in (1, 2, 22): panels[str(number)] = dict(status='SCHEMATIC_ONLY')
    assert set(panels) == {str(i) for i in range(1, 23)}
    write_json(OUT/'analysis/figures/figure_index.json', dict(completed=True, categories=panels, artifacts=artifacts,
               code_sha256=sha(__file__), example_selection='First lexicographic certified confirmation event; labeled discovery fallback; never select largest effect'), freeze=True)
    print('All22 figure categories accounted for; absent certified classes explicitly unavailable.')


if __name__ == '__main__':
    main()
