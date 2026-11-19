"""Plot completed causal yields with native and output-blind structural context.

Figures9 and13–20 are descriptive views of named completed pilots. Repeated
events are not independent bases; captured yield is not population prevalence.
"""
import argparse
from collections import Counter
from copy import deepcopy
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.native_report_v2 import identity, verify_hashes
from scripts.stage7a_bench.render_native_v2 import report_rows
from scripts.stage7a_bench.pilot_yield_v2 import STATES, UNFAITHFUL

OUT = ROOT / 'outputs/stage7a_bench_v2'


def report_row(result, native, structural, *, native_condition='image_present'):
    if (result.get('status') != 'COMPLETED_PILOT_YIELD_ONLY' or
            result.get('thresholds_retuned') is not False or
            result.get('primary_benchmark_selected') is not False or
            result['benchmark'] != native['benchmark']):
        raise ValueError('Completed, unchanged-definition pilot yield required')
    conditions = {r['condition']:r for r in report_rows(native)}
    if native_condition not in ('image_present','photo','screenshot') or native_condition not in conditions:
        raise ValueError('Explicit available visual-condition native context required')
    n = result['native_frozen_bases']
    if type(n) is not int or n < 200 or n != len(native['analysis_family_map']):
        raise ValueError('Frozen native-base denominator differs')
    states = result['state_counts']
    if set(states) != set(STATES):
        raise ValueError('Every inherited state must remain explicit')
    for state in states.values():
        keys = ('events','native_bases','source_families','certified_events',
                'certified_native_bases','certified_source_families')
        if (any(type(state.get(k)) is not int or state[k] < 0 for k in keys) or
                not state['source_families'] <= state['native_bases'] <= state['events'] or
                not state['certified_source_families'] <= state['certified_native_bases'] <= state['certified_events'] or
                any(state['certified_'+k] > state[k] for k in ('events','native_bases','source_families'))):
            raise ValueError('Invalid raw or certified state counts')
    if (sum(s['events'] for s in states.values()) != result['pilot']['events'] or
            sum(s['certified_events'] for s in states.values()) != result['certified_events'] or
            result['certified_events']+result['uncertified_events'] != result['pilot']['events'] or
            sum(states[k]['certified_events'] for k in UNFAITHFUL) != result['strong_unfaithful']['events'] or
            states['FAITHFUL_READ']['certified_events'] != result['strong_faithful']['events']):
        raise ValueError('State totals disagree with completed pilot')
    rates = {}
    for key, count in (
        ('unfaithful_events', result['strong_unfaithful']['events']),
        ('unfaithful_bases', result['strong_unfaithful']['native_bases']),
        ('faithful_events', result['strong_faithful']['events'])):
        value = result['strong_'+key+'_per_100_frozen_native_bases']
        if type(value) not in (int,float) or not math.isfinite(value) or not math.isclose(value, 100*count/n):
            raise ValueError('Captured yield disagrees with frozen denominator')
        rates[key+'_per_100'] = value
    for name in ('strong_unfaithful','strong_faithful','pilot'):
        counts = result[name]
        if (any(type(counts[k]) is not int or counts[k] < 0 for k in ('events','native_bases','source_families')) or
                not counts['source_families'] <= counts['native_bases'] <= min(counts['events'], n)):
            raise ValueError('Invalid unique-base or family count')
    source = [r for r in structural if r['benchmark'] == result['benchmark']]
    if (len(source) != 64 or len({r['example_id'] for r in source}) != 64 or
            any(r.get('model_outputs_read') is not False or r['source_score'] not in
                ('S0','S1','S2','S3','S4') for r in source)):
        raise ValueError('Complete independent output-blind structural audit required')
    distribution = Counter(r['source_score'] for r in source)
    local = distribution['S3']+distribution['S4']
    efficiency = result['efficiency']
    for field in ('certified_events_per_scientific_gpu_hour','certified_events_per_accounted_gpu_hour'):
        if type(efficiency[field]) not in (int,float) or not math.isfinite(efficiency[field]) or efficiency[field] < 0:
            raise ValueError('Invalid measured efficiency')
    return dict(benchmark=result['benchmark'], run_id=result['run_id'], frozen_bases=n,
        pilot=deepcopy(result['pilot']), states=deepcopy(states), **rates,
        strong_unfaithful=deepcopy(result['strong_unfaithful']), strong_faithful=deepcopy(result['strong_faithful']),
        certified_events=result['certified_events'], uncertified_events=result['uncertified_events'],
        candidate_anomaly_events=result['candidate_anomaly_events'],
        state_events_per_100={k:100*v['certified_events']/n for k,v in states.items()},
        native_condition=native_condition, native_accuracy=conditions[native_condition]['metrics']['final'],
        source_identifiability=dict(numerator=local, denominator=64, value=local/64),
        efficiency=deepcopy(efficiency), complete_pipeline_gpu_hours=efficiency['complete_pipeline_gpu_hours'],
        annotation_minutes_per_strong_failure=result['annotation_minutes_per_strong_failure'])


def render(request_path):
    request_path = (ROOT/request_path).resolve()
    if not request_path.is_relative_to(OUT/'analysis/causal_figure_requests'):
        raise ValueError('Use an active causal figure request')
    request = read_json(request_path)
    name = identity(request['figure_batch_id'])
    hashes = {str(request_path.relative_to(ROOT)):sha(request_path)}

    def ref(reference, directory, *, lines=False):
        path = (ROOT/reference['path']).resolve()
        if not path.is_relative_to(OUT/directory):
            raise ValueError('Figure source outside required stage directory')
        digest = sha(path)
        if digest != reference['sha256']:
            raise ValueError('Figure source changed')
        key = str(path.relative_to(ROOT))
        if key in hashes and hashes[key] != digest:
            raise ValueError('Conflicting figure provenance')
        hashes[key] = digest
        return read_jsonl(path) if lines else read_json(path)

    structural = ref(request['source_identifiability'], 'structural_audit', lines=True)
    rows, seen = [], set()
    for pair in request['reports']:
        result = ref(pair['pilot_yield'], 'causal_pilot/reports')
        native = ref(pair['native_report'], 'native_screen/reports')
        if result['source_sha256'].get(pair['native_report']['path']) != pair['native_report']['sha256']:
            raise ValueError('Causal yield and plotted native report differ')
        if result['benchmark'] in seen:
            raise ValueError('Duplicate benchmark pilot')
        seen.add(result['benchmark'])
        for mapping in (result['source_sha256'], native['artifact_sha256']):
            for key, value in mapping.items():
                if key in hashes and hashes[key] != value:
                    raise ValueError('Conflicting figure provenance')
                hashes[key] = value
        rows.append(report_row(result, native, structural,
                               native_condition=pair.get('native_condition','image_present')))
    if not rows:
        raise ValueError('At least one completed pilot required')
    verify_hashes(hashes)
    dest = OUT/'analysis/figures/causal_batches'/name
    if dest.exists():
        raise FileExistsError('Preserve the previous causal figure batch')
    dest.mkdir(parents=True)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'svg.fonttype':'none', 'pdf.fonttype':42})
    figures = []
    scope = ('Named completed pilots only; certification uses unchanged Stage7A rules.\n'
             'Captured yield is not population prevalence. Unresolved and untested cases are not proven absent states.')

    def save(fig, number, slug, title, caption):
        files = {}
        fig.text(.02, .025, caption, fontsize=8.5, color='#516473')
        for extension in ('png','pdf','svg'):
            path = dest/f'{number:02d}_{slug}.{extension}'
            fig.savefig(path, dpi=160, bbox_inches='tight')
            files[extension] = dict(path=str(path.relative_to(ROOT)), sha256=sha(path))
        plt.close(fig)
        figures.append(dict(figure_number=number, title=title, files=files, caption=caption))

    labels = [r['benchmark']+f"\n{r['pilot']['events']} pilot events / {r['frozen_bases']} frozen bases" for r in rows]

    def dots(number, slug, title, series, xlabel, caption):
        fig, ax = plt.subplots(figsize=(13, max(3.8, 1.5+len(rows)*.9)))
        xmax = max(1, max(getter(r)[0] for _,getter in series for r in rows)*1.18)
        colors = ['#387ea3','#af6945','#7f6ca1']
        for j,(label,getter) in enumerate(series):
            for i,row in enumerate(rows):
                value, denominator = getter(row)
                y = i+(j-(len(series)-1)/2)*.3
                ax.scatter(value, y, color=colors[j], s=45)
                ax.text(1.04*xmax, y, label+': '+denominator, va='center', fontsize=8.5, color=colors[j])
        ax.set(yticks=range(len(rows)), yticklabels=labels, xlim=(-.03*xmax,1.9*xmax), xlabel=xlabel)
        ax.set_xticks([xmax*k/4 for k in range(5)])
        ax.set_ylim(len(rows)-.6,-.6)
        ax.spines[['top','right','left']].set_visible(False)
        ax.spines['bottom'].set_bounds(0,xmax)
        ax.tick_params(axis='y',length=0)
        ax.grid(axis='x',alpha=.18)
        ax.set_title(title,loc='left',fontweight='bold',pad=18)
        fig.subplots_adjust(left=.27,right=.98,top=.80,bottom=.25)
        save(fig,number,slug,title,scope+'\n'+caption)

    dots(9,'certified_faithful_yield','Certified faithful-read yield',[
        ('Certified faithful',lambda r:(r['faithful_events_per_100'],f"{r['strong_faithful']['events']} events / {r['frozen_bases']} bases"))],
        'Certified faithful events per 100 frozen native bases','Weak Tier2 faithful states are not counted as certified controls.')
    fig, ax = plt.subplots(figsize=(14,max(4.6,2+len(rows)*.8)))
    raw = [[r['states'][s]['events'] for s in STATES] for r in rows]
    ax.imshow(raw,aspect='auto',cmap='Blues',vmin=0,vmax=max(1,max(max(a) for a in raw)))
    names = ['Faithful','Prior fill','Wrong source','Stale source','Extraction\nerror','Integration\nerror','Source\nanomaly','Unresolved']
    for i,row in enumerate(rows):
        for j,state in enumerate(STATES):
            cell = row['states'][state]
            ax.text(j,i,f"{cell['events']} / {cell['certified_events']}",ha='center',va='center',
                    color='white' if cell['events'] > max(1,max(max(a) for a in raw))*.6 else '#182d3b')
    ax.set(xticks=range(8),xticklabels=names,yticks=range(len(rows)),yticklabels=labels)
    ax.set_title('Causal pilot states: raw / certified events',loc='left',fontweight='bold',pad=18)
    fig.subplots_adjust(left=.25,right=.99,top=.78,bottom=.28)
    save(fig,13,'causal_state_counts','Causal pilot state counts',scope+'\nCell color shows raw count. Candidate-only anomaly flags remain in the manifest; they are not promoted to state labels.')
    dots(14,'strong_unfaithful_yield','Captured strong unfaithful yield',[
        ('Events',lambda r:(r['unfaithful_events_per_100'],f"{r['strong_unfaithful']['events']} / {r['frozen_bases']}")),
        ('Unique bases',lambda r:(r['unfaithful_bases_per_100'],f"{r['strong_unfaithful']['native_bases']} / {r['frozen_bases']}"))],
        'Per 100 frozen native bases','Repeated events share bases/families. The legacy aggregate includes downstream integration; source-failure subtotals are reported separately.')
    for number,slug,title,state in [(15,'wrong_source_yield','Certified wrong-source yield','WRONG_SOURCE_READ'),
                                    (16,'prior_fill_yield','Certified prior-fill yield','PRIOR_FILL')]:
        dots(number,slug,title,[(title,lambda r,s=state:(r['state_events_per_100'][s],
            f"{r['states'][s]['certified_events']} events / {r['frozen_bases']} bases"))],
            'Certified events per 100 frozen native bases',
            ('All selected events have intact target sources; no absent-image PRIOR_FILL certificate was tested. Zero is captured yield only.'
             if state == 'PRIOR_FILL' else 'Zero certified events does not rule out the state in missing-control or untested cases.'))
    dots(17,'extraction_integration_yield','Extraction and integration error yield',[
        (label,lambda r,s=state:(r['state_events_per_100'][s],f"{r['states'][s]['certified_events']} events / {r['frozen_bases']} bases"))
        for label,state in [('Extraction','SOURCE_COUPLED_EXTRACTION_ERROR'),('Integration','DOWNSTREAM_INTEGRATION_ERROR')]],
        'Certified events per 100 frozen native bases','Extraction and integration remain separate. Separately eligible integration review covers one MathWild event; other pilots lack that coverage.')
    dots(18,'causal_efficiency','Certified causal events per GPU-hour',[
        ('Pilot science',lambda r:(r['efficiency']['certified_events_per_scientific_gpu_hour'],
            f"{r['certified_events']} / {r['efficiency']['scientific_gpu_seconds']/3600:.3f} h")),
        ('Accounted total',lambda r:(r['efficiency']['certified_events_per_accounted_gpu_hour'],
            f"{r['certified_events']} / {r['efficiency']['accounted_gpu_hours']:.3f} h"))],
        'Certified events per measured GPU-hour','Accounted total adds native generation and mechanics. MMLong sums one-GPU worker times including peer wait; full overhead/annotation is unmeasured.')
    for number,slug,title in [(19,'accuracy_vs_causal_yield','Native accuracy and captured causal failure yield'),
                              (20,'identifiability_vs_causal_yield','Source identifiability and captured causal failure yield')]:
        fig, ax = plt.subplots(figsize=(14,5.5))
        unknown = []
        for row_index, row in enumerate(rows):
            metric = row['native_accuracy'] if number == 19 else row['source_identifiability']
            if metric['value'] is None:
                unknown.append(row['benchmark']+': accuracy unadjudicated')
                continue
            y = row['unfaithful_events_per_100']
            ax.scatter(100*metric['value'],y,s=180,color='#387ea3')
            ax.text(100*metric['value'],y,str(row_index+1),ha='center',va='center',fontsize=8,color='white')
            note = f"{row['benchmark']} ({metric['numerator']}/{metric['denominator']})"
            if number == 19:
                note = (f"{row['benchmark']}\n{metric['numerator']}/{metric['denominator']} / "
                        f"{row['native_condition']}\n{metric['unknown']} unknown")
            fig.text(.70,.75-row_index*.115,f'{row_index+1}. '+note,va='top',fontsize=9.5,color='#182d3b')
        top = max(1,max(r['unfaithful_events_per_100'] for r in rows)*1.5)
        ax.set(xlim=(-5,105),ylim=(-.05*top,top),xticks=[0,25,50,75,100],
            xlabel='Named visual-condition final accuracy (%)' if number == 19 else 'Output-blind S3/S4 audit share (%)',
            ylabel='Certified unfaithful events per 100 frozen native bases')
        ax.set_title(title,loc='left',fontweight='bold',pad=18)
        ax.spines[['top','right']].set_visible(False)
        ax.grid(alpha=.18)
        fig.subplots_adjust(left=.10,right=.65,top=.80,bottom=.25)
        save(fig,number,slug,title,scope+'\n'+('; '.join(unknown) if unknown else
            'Point labels retain separate denominators. Structural feasibility and final accuracy are not causal certification.'))
    verify_hashes(hashes)
    write_json(dest/'manifest.json',dict(status='RENDERED_PENDING_VISUAL_REVIEW',figure_batch_id=name,
        rows=rows,figures=figures,source_sha256=hashes,renderer_sha256=sha(ROOT/'scripts/stage7a_bench/render_causal_v4.py'),
        complete_sweep_claimed=False,population_prevalence_estimated=False,primary_benchmark_selected=False))
    return dest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--request',required=True)
    print(render(parser.parse_args().request))
