"""Report the pre-scoring stop without fabricating gated downstream results."""
import os
os.environ['MPLCONFIGDIR'] = 'outputs/stage6br/analysis/matplotlib_cache'

import ast
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.stage6b.common import ROOT, read_json, sha, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from scripts.stage6br.interval_review_io import load_reviews


def main():
    gate = read_json(OUT/'audit/panel_gate.json')
    assert gate['status'] == 'STOP_REPAIR_INSUFFICIENT'
    protected = read_json(OUT/'audit/protected_inputs.json')
    unchanged = {p:sha(Path(p)) == digest for p,digest in protected.items()}
    assert all(unchanged.values())
    python_files = sorted((ROOT/'scripts/stage6br').rglob('*.py'))
    for p in python_files:
        ast.parse(p.read_text(),filename=str(p))
    reviews = load_reviews()
    local = defaultdict(list)
    names = ['value_readouts','binding_readouts','claim_value_readouts',
             'ordinary_binding_readouts','role_confirmation_readouts']
    counts = {}
    for name in names:
        values = list(rows(OUT/f'annotation_repair/{name}.jsonl'))
        counts[name] = len(values)
        for r in values:
            local[(r['event_id'],r['span_id'])].append(r['id'])
    ledger=[]
    for r in rows(OUT/'review/candidate_universe.jsonl'):
        anchors = local.get((r['event_id'],r['span_id']),[])
        ledger.append(r | {'review_status':'LOCAL_READOUTS_AVAILABLE_WHOLE_SPAN_NOT_CERTIFIED' if anchors else 'NOT_FULLY_REVIEWED_BEFORE_GATE_STOP',
                           'local_readout_ids':anchors,'full_span_demand_sources':None,
                           'null_reason':'Whole-span set-valued demand was not certified; null is not NONE_VISUAL.',
                           'terminal_status':'STOP_REPAIR_INSUFFICIENT'})
    write_jsonl(OUT/'annotation_repair/candidate_accounting_at_stop.jsonl',ledger,freeze=True)
    coverage={'candidate_spans_accounted':len(ledger),
              'candidate_flags':Counter(t for r in ledger for t in r['candidate_types']),
              'readout_candidates':counts,'interval_decisions':Counter(r['verdict'] for r in reviews.values()),
              'full_interval_context_reviews':sum(r['entire_native_interval_reviewed'] for r in reviews.values()),
              'exclusion_witness_reviews':sum(not r['entire_native_interval_reviewed'] for r in reviews.values()),
              'full_section12_reannotation_completed':False,
              'early_stop_reason':'Even assuming all unfinished constructed candidates valid, fewer than64 matched holds are possible.',
              'unreviewed_is_not_a_semantic_negative_label':True}
    write_json(OUT/'audit/annotation_coverage_at_stop.json',coverage,freeze=True)
    gated={'status':'NOT_EXECUTED_PANEL_GATE_FAILED','gate':'audit/panel_gate.json',
           'gpu_model_loads':0,'gpu_scored_events':0,'causal_states_classified':0,
           'refresh_panel_selected':False,'failure_enriched_panel_selected':False,
           'full_error_readout_context_certification_completed':False,
           'discovery_numeric_dominance_margin_fit':False,'pca_refit':False,
           'w2_w8_scoring_performed':False,'mechanical_gpu_validation_performed':False,
           'rescue_or_sink_intervention_performed':False}
    write_json(OUT/'audit/gated_execution_status.json',gated,freeze=True)
    write_json(OUT/'audit/final_input_integrity.json',{'status':'PASS','protected_inputs':unchanged,
        'ast_files':len(python_files),'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in python_files}},freeze=True)

    figures=OUT/'analysis/figures';figures.mkdir(parents=True,exist_ok=True)
    def save(fig,name):
        for ext in ('svg','pdf'):
            fig.savefig(figures/(name+'.'+ext),bbox_inches='tight')
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,3.2));ax.axis('off')
    ax.set_title('Demand ontology and examples — definitions, not state frequencies',pad=18)
    table=ax.table(cellText=[['SINGLETON','{A}','Cylinder radius6'],['COMPOUND','{A,T}','Volume uses radius6 and height8'],
        ['NONE_VISUAL','{}','Affirmatively no visual-source demand'],['UNRESOLVED','unknown','Source or geometric role not established']],
        colLabels=['Demand','Set','Meaning'],loc='center',colWidths=[.2,.14,.66],cellLoc='left')
    table.auto_set_font_size(False);table.set_fontsize(11);table.scale(1,2)
    save(fig,'ontology_examples')
    fig,ax=plt.subplots(figsize=(10,3.8));ax.axis('off')
    ax.set_title('Readout separation: mathverse_645 — image diameter3, native radius3')
    text='V: radius1.5 versus radius3\n\nB: diameter3 versus radius3 — literal3 held fixed\n\nE: logP(native wrong radius3), and wrong-minus-correct preference\n\nNo source-suppression effects were measured in Stage6BR.'
    ax.text(.02,.86,text,va='top',fontsize=12,transform=ax.transAxes)
    save(fig,'readout_examples')
    fig,ax=plt.subplots(figsize=(9,3.8))
    labels=['Reviewed stable intervals\n(before matching)','Optimistic matched-hold\ncapacity','Required matched\nholds']
    values=[coverage['interval_decisions']['ACCEPTED_T0'],gate['maximum_possible_matched_holds'],64]
    bars=ax.bar(labels,values,color=['#397993','#d78633','#555555'])
    ax.bar_label(bars,padding=3);ax.set_ylim(0,76);ax.set_ylabel('Intervals')
    ax.set_title('Panel stop: even optimistic capacity is below the minimum')
    fig.text(.5,-.02,'Capacity assumes every unfinished endpoint and unreviewed/reopened hold is valid.',ha='center',fontsize=9)
    save(fig,'panel_gate')
    fig,ax=plt.subplots(figsize=(9,3));ax.axis('off');ax.set_title('Conceptual interpretation — all four classes remain unmeasured')
    table=ax.table(cellText=[['Stable / aligned','Healthy hold','Fixation / stale state'],
                             ['Moves','Wandering candidate','Healthy switch if aligned']],
                   colLabels=['Causal source state','Stable demand','Changed demand'],loc='center',cellLoc='center')
    table.auto_set_font_size(False);table.set_fontsize(11);table.scale(1,2)
    save(fig,'conceptual_states')
    categories=['Repaired demand-state ontology','Single vs compound demand examples','Value/binding/error readout examples',
        'Transition/hold panel construction','Source-state change T1 vs T0','Demanded-source causal margin',
        'Healthy holds','Healthy switches','Wandering','Fixation/stale states','Delayed switches/latency',
        'Refresh classifications','Error-oriented source effects','Numeric-correct/binding-wrong examples',
        'Dynamic-state frequencies','Dynamic states vs correctness','Path length by dynamic class',
        'Tortuosity by dynamic class','Demand coupling vs path length','vSTREAM dynamic overlay',
        'Per-dataset dynamic contrasts','Value vs binding causal sensitivity','Rescue readiness','Conceptual figure']
    available={1:'ontology_examples',2:'ontology_examples',3:'readout_examples',4:'panel_gate',14:'readout_examples',24:'conceptual_states'}
    lines=['# Stage6BR figure status','', 'Four standalone figures cover six descriptive/conceptual categories. The other categories were gated off; no causal-state results are implied.','', '| # | Category | Artifact/status |','|---|---|---|']
    for i,name in enumerate(categories,1):
        status=f'[SVG]({available[i]}.svg) / [PDF]({available[i]}.pdf); descriptive or conceptual' if i in available else 'NOT EXECUTED — panel gate failed'
        lines.append(f'| {i} | {name} | {status} |')
    (figures/'index.md').write_text('\n'.join(lines)+'\n')
    summaries=OUT/'summaries';summaries.mkdir(exist_ok=True)
    recommendation='STOP — report the current repair as insufficient under section39. Do not proceed to dynamic inference or rescue from this panel.'
    (summaries/'next_stage_recommendation.md').write_text('# Stage6BR recommendation\n\n'+recommendation+'\n\nThis is an identification boundary. It does not establish that healthy retrieval dominates or that failures are rare. No next stage was started.\n')
    criteria=[]
    for i in range(1,22):
        if i in {9,10}:
            status='PREDECLARED_NOT_EXECUTED'
        elif i in {11,13,14,15,16,17,18}:
            status='GATED_NOT_EVALUATED'
        elif i in {3,4,5}:
            status='CANDIDATE_LEVEL_ONLY_FULL_PANEL_NOT_CERTIFIED'
        else:
            status='PASS_STOP_PATH' if i in {6,7} else 'PASS'
        criteria.append({'criterion':i,'status':status})
    write_json(summaries/'stage6br_acceptance.json',{
        'status':'STOP_PATH_DOCUMENTED_NOT_FULL21_OF21_PASS','criteria':criteria,
        'full_plan_experiment_completed':False,'section39_stop_applied':True,
        'full_section12_annotation_incomplete_at_early_gate':True,
        'exactly_one_recommendation':recommendation},freeze=True)
    summary=f'''# Stage6BR — STOP_REPAIR_INSUFFICIENT

The frozen constructed readout/interval pool can supply at most **{gate['maximum_possible_matched_holds']} matched stable-demand holds**, below the plan's minimum **64**. This is an optimistic upper bound: every unfinished transition endpoint, unreviewed/reopened hold and binding context is assumed valid. Further adjudication of this pool cannot make it pass.

The project matching algorithm and SciPy independently agree. A vertex-cover certificate of the same size covers every compatible transition–hold edge. The stop uses the unambiguous hold-count requirement, not a stricter interpretation of the plan's48-base wording.

Evidence: [gate](../audit/panel_gate.json), [certificate](../audit/panel_gate_vertex_cover.json), [complete compatibility graph](../audit/panel_gate_graph.json).

## Work completed

- Preserved109 C1 bases,1199 native traces, the47/62 discovery/confirmation split and16 protected inputs. No dataset download or package installation.
- Exported672 blind packets covering1385 source-transition,3683 hold,377 refresh and97 wrong-claim flags. These flags overlap and are not accepted panel counts.
- Reviewed950 source-linked quote records and4079 direct-assertion proposals. Retained1366 local assertions; parent scope and whole-span demand were not thereby certified.
- Froze1983 V candidates,33 full-claim B/error candidates,16 paired claim-V candidates,89 ordinary B candidates and30 native role confirmations. Candidate status does not certify ERROR_VALID or causal error promotion.
- Recorded220 interval decisions:44 accepted stable intervals,119 demand-change exclusions,50 unresolved-geometry exclusions,one insufficient readout andsix reopened cases. Of these,201 received full interval/context review;19 were excluded by explicit counterexample witnesses. These are targeted review counts, not prevalence estimates.
- Applied frozen matching rules without attention, QK, alphaV, VSD, PCA or causal outcomes. Compatible readout alternatives share the same underlying interval unit and cannot multiply hold count.

## Validity repairs and limits

Exact token histories were preserved. Repairs address expression-valued numeric foils, arithmetic-operand misassociation, signed-loss magnitude and correct derived radii. Conditional assertions must retain their antecedents; a true conditional does not become an error because its hypothetical value differs from the image.

Six chord-based hold exclusions were reopened because CE13.5 is supplied in the question. They are counted as valid in the final optimistic bound. They are not silently retained as evidence of visual demand changes. New visual geometry remains distinct from arithmetic using a question-provided number.

The bound applies to this **constructed candidate pool and frozen matching rules**, not every possible readout in C1. Matching requires the same split and condition, constrained progress and a token-gap ratio at most2. Full section12 re-annotation of every original transition and wrong-claim anchor was not completed after the early gate became decisive. The [candidate ledger](../annotation_repair/candidate_accounting_at_stop.jsonl) preserves that incomplete scope explicitly. This is not a claim of21/21 full technical completion.

## Gated work and GPU status

No Stage6BR CUDA model load, mechanics, W2/W8 scoring, causal classification, activity-margin fit, refresh/failure panel, statistics or PCA reanalysis ran. BF16/W2/W8 remain predeclared protocols. [Execution status](../audit/gated_execution_status.json) and [acceptance](stage6br_acceptance.json) distinguish the stop path from full execution. Four descriptive/conceptual figures are indexed against all24 requested categories; effect-dependent categories are explicitly gated off.

Slurm111485 started on node06 in tmux10 at13:02:27 KST on September10, with one RTX A6000,4 CPUs and14G host RAM. The allocation has a September13 13:02:27 KST end time. Only a read-only device check ran; no additional allocation was requested or the existing allocation released. Check live Slurm state before future use.

## One recommendation

{recommendation}

No inference about wandering, fixation, failure rarity or healthy-retrieval dominance is supported by this stopped repair. Repaired inspected confirmation traces remain non-fresh. No next stage was started.
'''
    (summaries/'stage6br_summary.md').write_text(summary)
    print({'status':'STOP_REPORT_WRITTEN','protected_inputs_unchanged':len(unchanged),
           'ast_files':len(python_files),'readout_candidates':counts,'coverage':coverage['interval_decisions'],
           'figures':4})


if __name__=='__main__':
    main()
