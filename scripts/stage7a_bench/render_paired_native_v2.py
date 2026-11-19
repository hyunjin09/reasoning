"""Figures10/11/21 from complete native reports, using common paired IDs.

The separate completed Phantom behavioral report retains its own figure and
no-image-only scope. This module consumes image-benchmark native reports.
"""
import argparse
from copy import deepcopy
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.stage7a.common import ROOT, read_json, sha, write_json
from scripts.stage7a_bench.native_report_v2 import identity, verify_hashes
from scripts.stage7a_bench.render_native_v2 import report_rows

OUT = ROOT/'outputs/stage7a_bench_v2'
FIELDS = ('final_accuracy','visual_claim_rate','caveat_rate','unsupported_claim_rate')
DEFINITIONS = {
    10:('image_present','silent_no_image','Image-present and silent no-image behavior'),
    11:('silent_no_image','explicit_guess','Silent no-image and explicit guess behavior'),
    21:('photo','screenshot','Photo and screenshot outcome transitions')}


def select_pair(report,left,right):
    conditions = {r['condition']:r for r in report_rows(report)}
    if left == right or left not in conditions or right not in conditions:
        raise ValueError('Two distinct completed conditions required')
    ordered = sorted((left,right))
    pair = deepcopy(report['paired_conditions']['__'.join(ordered)])
    n = pair['paired_reviewed']
    if (type(n) is not int or n < 0 or len(pair['paired_base_ids']) != n or
            len(set(pair['paired_base_ids'])) != n or pair.get('causal_label') is not None):
        raise ValueError('Invalid common-base count or causal claim')
    if ordered[0] != left:
        for field in FIELDS:
            pair['left_'+field],pair['right_'+field] = pair['right_'+field],pair['left_'+field]
        pair['unpaired_left'],pair['unpaired_right'] = pair['unpaired_right'],pair['unpaired_left']
        for field in ('final_correctness_transitions','screen_class_transitions'):
            pair[field] = {' → '.join(reversed(k.split(' → '))):v for k,v in pair[field].items()}
        for evidence in pair['paired_evidence']:
            for field in ('claims','output_confidence'):
                evidence['left_'+field],evidence['right_'+field] = evidence['right_'+field],evidence['left_'+field]
    for side,condition in (('left',left),('right',right)):
        if (type(pair['unpaired_'+side]) is not int or pair['unpaired_'+side] < 0 or
                pair['unpaired_'+side]+n != conditions[condition]['generated']):
            raise ValueError('Common and unpaired counts differ from complete conditions')
        for field in FIELDS:
            metric = pair[side+'_'+field]
            if (any(type(metric.get(k)) is not int or metric[k] < 0 for k in ('numerator','denominator','unknown')) or
                    metric['numerator'] > metric['denominator'] or metric['denominator']+metric['unknown'] != n):
                raise ValueError('Paired metric must use its own common-base denominator')
            value = metric['value']
            if metric['denominator'] == 0:
                if value is not None:
                    raise ValueError('Unknown paired rate is not zero')
            elif type(value) not in (int,float) or not math.isfinite(value) or not math.isclose(value,metric['numerator']/metric['denominator']):
                raise ValueError('Paired rate disagrees with reviewed counts')
    transitions = pair['final_correctness_transitions']
    expected = {a+' → '+b for a in ('correct','wrong','unknown') for b in ('correct','wrong','unknown')}
    if (not set(transitions) <= expected or any(type(v) is not int or v < 0 for v in transitions.values()) or
            sum(transitions.values()) != n):
        raise ValueError('Final transitions must cover every common reviewed base')
    pair.update(benchmark=report['benchmark'],left_condition=left,right_condition=right)
    return pair


def render(request_path):
    request_path = (ROOT/request_path).resolve()
    if not request_path.is_relative_to(OUT/'analysis/paired_figure_requests'):
        raise ValueError('Use an active paired-figure request')
    request = read_json(request_path)
    name = identity(request['figure_batch_id'])
    hashes = {str(request_path.relative_to(ROOT)):sha(request_path)}
    pairs = {number:[] for number in DEFINITIONS}
    seen = set()
    for reference in request['reports']:
        path = (ROOT/reference['path']).resolve()
        if not path.is_relative_to(OUT/'native_screen/reports') or sha(path) != reference['sha256']:
            raise ValueError('Native report source changed or is outside its report directory')
        report = read_json(path)
        if report['benchmark'] in seen:
            raise ValueError('Duplicate benchmark report')
        seen.add(report['benchmark'])
        hashes[str(path.relative_to(ROOT))] = reference['sha256']
        for key,value in report['artifact_sha256'].items():
            if key in hashes and hashes[key] != value:
                raise ValueError('Conflicting paired-report provenance')
            hashes[key] = value
        report_rows(report)
        for number,(left,right,_) in DEFINITIONS.items():
            if {left,right} <= set(report['conditions']):
                pairs[number].append(select_pair(report,left,right))
    if not any(pairs.values()):
        raise ValueError('No supported complete paired conditions in these reports')
    verify_hashes(hashes)
    dest = OUT/'analysis/figures/paired_batches'/name
    if dest.exists():
        raise FileExistsError('Preserve the previous paired figure batch')
    dest.mkdir(parents=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','pdf.fonttype':42})
    figures = []
    caption = ('Common reviewed question IDs only; different whole-condition sample sizes are not pooled.\n'
               'Behavioral differences and image-absent correctness are not causal PRIOR_FILL or nonvisual certification.')
    for number,rows in pairs.items():
        if not rows:
            continue
        title = DEFINITIONS[number][2]
        if number in (10,11):
            fig,axes = plt.subplots(len(rows),1,figsize=(13,max(4.8,4*len(rows))),squeeze=False)
            labels = ['Final correctness','Visual claim','Caveat / abstention','Unsupported claim']
            for ax,row in zip(axes[:,0],rows):
                for j,side in enumerate(('left','right')):
                    color = ('#387ea3','#af6945')[j]
                    for i,field in enumerate(FIELDS):
                        metric = row[side+'_'+field]
                        y = i+(j-.5)*.3
                        if metric['value'] is not None:
                            ax.scatter(100*metric['value'],y,color=color,s=40)
                        text = 'Unknown' if metric['value'] is None else f"{metric['numerator']}/{metric['denominator']}"
                        ax.text(105,y,f"{row[side+'_condition']}: {text}; {metric['unknown']} unknown",fontsize=8,va='center',color=color)
                ax.set(yticks=range(4),yticklabels=labels,xlim=(-2,205),xticks=[0,25,50,75,100],
                    xlabel='Percent of adjudicated common responses')
                ax.set_ylim(3.6,-.6)
                ax.spines[['top','right','left']].set_visible(False)
                ax.spines['bottom'].set_bounds(0,100)
                ax.grid(axis='x',alpha=.18)
                ax.set_title(row['benchmark']+f" — {row['paired_reviewed']} paired bases; "
                    f"{row['unpaired_left']}/{row['unpaired_right']} unpaired left/right",loc='left',fontsize=10,pad=10)
            fig.suptitle(title,fontweight='bold',x=.24,ha='left')
            fig.subplots_adjust(left=.24,right=.99,top=.82,bottom=.24,hspace=.8)
        else:
            fig,axes = plt.subplots(1,len(rows),figsize=(max(7,5.5*len(rows)),5),squeeze=False)
            categories = ('correct','wrong','unknown')
            for ax,row in zip(axes[0],rows):
                matrix = [[row['final_correctness_transitions'].get(a+' → '+b,0) for b in categories] for a in categories]
                maximum = max(1,max(max(r) for r in matrix))
                ax.imshow(matrix,cmap='Blues',vmin=0,vmax=maximum)
                for i in range(3):
                    for j in range(3):
                        ax.text(j,i,str(matrix[i][j]),ha='center',va='center',color='white' if matrix[i][j] > maximum*.6 else '#182d3b')
                ax.set(xticks=range(3),xticklabels=categories,yticks=range(3),yticklabels=categories,
                    xlabel=row['right_condition'],ylabel=row['left_condition'])
                ax.set_title(row['benchmark']+f" ({row['paired_reviewed']} paired)",fontsize=10)
            fig.suptitle(title,fontweight='bold')
            fig.subplots_adjust(left=.18,right=.97,top=.78,bottom=.27)
        fig.text(.02,.025,caption,fontsize=8.5,color='#516473')
        files = {}
        for extension in ('png','pdf','svg'):
            path = dest/f'{number:02d}_paired_native.{extension}'
            fig.savefig(path,dpi=160,bbox_inches='tight')
            files[extension] = dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
        plt.close(fig)
        figures.append(dict(figure_number=number,title=title,files=files,caption=caption))
    verify_hashes(hashes)
    write_json(dest/'manifest.json',dict(status='RENDERED_PENDING_VISUAL_REVIEW',figure_batch_id=name,
        pairs=pairs,figures=figures,source_sha256=hashes,
        renderer_sha256=sha(ROOT/'scripts/stage7a_bench/render_paired_native_v2.py'),
        causal_states_assigned=False,behavioral_bclean_defined=False,primary_benchmark_selected=False,
        complete_sweep_claimed=False))
    return dest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--request',required=True)
    print(render(parser.parse_args().request))
