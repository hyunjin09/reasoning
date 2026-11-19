"""Standalone figures and complete raw-continuation reading copies."""
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path('runs/stage12us/v1/matplotlib').resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scripts.stage12us.common import ROOT,load,now


def savefig(fig,name):
    dest=ROOT/'figures';dest.mkdir(parents=True,exist_ok=True)
    for ext in ['png','pdf']:fig.savefig(dest/f'{name}.{ext}',bbox_inches='tight',dpi=180)
    plt.close(fig)


def figures():
    info=load(ROOT/'stage12us_primary_inference.json');primary=info['primary']
    fig,ax=plt.subplots(figsize=(10,4.8));ax.set_xlim(0,10);ax.set_ylim(0,5);ax.axis('off')
    boxes=[(1.9,3.6,'Successful Thinking\nanswer-safe prefix R_T'),(1.9,1.7,'Failed Instruct-CoT\nanswer-safe prefix R_C'),
           (7.3,3.6,'Thinking target'),(7.3,1.7,'Instruct target')]
    for x,y,t in boxes:ax.text(x,y,t,ha='center',va='center',bbox=dict(boxstyle='round,pad=.6',fc='#e6eef5',ec='#476781'),fontsize=12)
    for y in [3.6,1.7]:
        for ty in [3.6,1.7]:ax.annotate('',xy=(5.9,ty),xytext=(3.8,y),arrowprops=dict(arrowstyle='->',color='#52788d',lw=1.7))
    ax.text(5,.55,'Original question + assistant prefill • no image • 3 fixed seeds\nQuestion-only controls; primary cyclic shuffled-prefix controls',ha='center',fontsize=11)
    ax.set_title('U1 · Externalized state production versus utilization / repair',fontsize=14)
    savefig(fig,'U1_transfer_assay')
    cond=['RT_T','RT_I','RC_I','RC_T','Q_I','Q_T'];labels=['R_T → T','R_T → I','R_C → I','R_C → T','Q → I','Q → T']
    matrix=np.array([[.5 if r['majority'][c] is None else float(r['majority'][c]) for c in cond] for r in primary])
    fig,ax=plt.subplots(figsize=(10,4.8));ax.imshow(matrix,vmin=0,vmax=1,cmap=matplotlib.colors.ListedColormap(['#efd3ce','#dedede','#c7e2d8']))
    for i,r in enumerate(primary):
        for j,c in enumerate(cond):
            vals=r['run_outcomes'][c];wins=sum(v is True for v in vals);missing=sum(v is None for v in vals)
            ax.text(j,i,f'{wins}/3'+(f'\n{missing} missing' if missing else ''),ha='center',va='center',fontsize=10 if missing else 12)
    ax.set_xticks(range(6),labels);ax.set_yticks(range(5),[r['item_id'] for r in primary]);ax.set_ylabel('Frozen B4 family (item ID)')
    ax.set_title('U2 · Correct continuations; green = majority success (≥2/3)')
    savefig(fig,'U2_primary_transfer_matrix')
    names=['PRODUCTION_SUPPORT','UTILIZATION_SUPPORT','REPAIR_SUPPORT','TEXT_NOT_SUFFICIENT']
    support=[[r[k] is True for k in names] for r in primary]
    support=[v+[not any(v)] for v in support]
    fig,ax=plt.subplots(figsize=(10,4.6));ax.imshow(support,vmin=0,vmax=1,aspect='auto',cmap=matplotlib.colors.ListedColormap(['#f2f2f2','#8aaac6']))
    for i,row in enumerate(support):
        for j,v in enumerate(row):ax.text(j,i,'YES' if v else '—',ha='center',va='center')
    ax.set_xticks(range(5),['Production','Utilization','Repair','Text\ninsufficient','Unresolved'],fontsize=10);ax.set_yticks(range(5),[r['item_id'] for r in primary])
    ax.set_title('U3 · Family interpretation under frozen source and control rules')
    savefig(fig,'U3_interpretation_classes')
    source=load(ROOT/'stage12us_prefix_content_audit.json')['rows']
    order={r['item_id']:i for i,r in enumerate(info['primary']+info['secondary'])}
    source=sorted(source,key=lambda r:(order[r['item_id']],r['source']))
    fig,ax=plt.subplots(figsize=(13,7.5));ax.axis('off')
    data=[[r['item_id']+' / '+r['source'],r['evidence_state'].removeprefix('E_'),r['derivation_state'].removeprefix('DERIVATION_'),
          str(r['raw_cut_offset']), 'No / No',str(r['GOLD_VALUE_INCIDENTALLY_PRESENT'])] for r in source]
    table=ax.table(cellText=data,colLabels=['Item / source','Evidence','Derivation','Prefix chars','Final / candidate','Gold incidental'],loc='center',cellLoc='center',colWidths=[.12,.25,.17,.12,.17,.17])
    table.auto_set_font_size(False);table.set_fontsize(9);table.scale(1,1.8)
    ax.set_title('U4 · Source states sealed before transfer outcomes\nCandidate audit uses lexical scans and targeted semantic review; incidental gold is descriptive',pad=22)
    savefig(fig,'U4_source_content_audit')


def reading_copies():
    dest=Path('reports/stage12us/v1');dest.mkdir(parents=True,exist_ok=True)
    index=['# Stage12U-S raw continuations','', 'Each file shows the exact question, links the unchanged canonical prefill, and includes all newly generated text.','']
    for t in load(ROOT/'audit/science_execution.json')['tasks']:
        g=load(ROOT/'generations'/t['task_id']/'generation.json');s=load(ROOT/'audit/first_scores'/f"{t['task_id']}.json")
        prefix=f"[{t['source']} prefix for item{t['source_item_id']}]({Path(t['prefix_path']).resolve()})" if t['prefix_path'] else 'None (question-only)'
        body=f"# {t['task_id']}\n\nTarget: {t['target']}; seed: {t['seed']}; new tokens: {g['tokens']}; stop: {g['finish_reason']}; label: {s['label']}.\n\nPrefix: {prefix}\n\n## Original question\n\n{t['question']}\n\n## Complete newly generated continuation\n\n```text\n{g['raw_decoded_response']}\n```\n"
        (dest/f"{t['task_id']}.md").write_text(body)
        index.append(f"- [{t['task_id']}]({t['task_id']}.md): {s['label']}, {g['tokens']:,} new tokens")
    (dest/'index.md').write_text('\n'.join(index)+'\n')


def summary():
    info=load(ROOT/'stage12us_primary_inference.json');d=load(ROOT/'stage12us_decision.json');res=load(ROOT/'stage12us_resource_accounting.json')
    score=load(ROOT/'stage12us_scoring_review.json');tech=load(ROOT/'stage12us_technical_validation.json')
    scientific=pd.concat([pd.read_parquet(ROOT/f'stage12us_{name}.parquet') for name in
        ['transfer_results','question_only_controls','shuffled_trace_controls']],ignore_index=True)
    adequate_c=sum(r['C_evidence_state'] in ['E_FULL','E_PARTIAL'] and r['C_derivation_state']=='DERIVATION_VALID' for r in info['primary'])
    lines=['# Stage12U-S — Reasoning-state production versus utilization', '',f"Completed {now()}. **{d['decision']}**. Authorized stage ends here; no follow-on launched.",'',
      'Five frozen B4 C−T+ families are the primary targeted cohort; two B1 families are descriptive. Exactly156 scientific calls comprise84 core transfers,42 question-only controls and30 deterministic cyclic shuffled controls. Every family-condition has three fixed seeds; majority success requires at least2/3. Twelve disjoint technical calls passed input/prefix/scoreability checks before science; their correctness was not used.', '',
      'All source traces are reused unchanged. Each canonical prefix ends before its first explicit task-answer candidate, including tentative wrong candidates; only Thinking wrappers are removed. Targets receive the original question plus native assistant prefill without images or extra instructions. Model-specific4B recipes and32768/81920 new-token caps remain frozen.','',
      '## Primary B4 transfer outcomes','',
      '| Item | R_T→T | R_T→I | R_C→I | R_C→T | Q→I | Q→T | Shuffled R_T→I | Shuffled R_C→T |',
      '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    conditions=['RT_T','RT_I','RC_I','RC_T','Q_I','Q_T','ST_I','SC_T']
    for r in info['primary']:
        cells=[]
        for c in conditions:
            vals=r['run_outcomes'][c];missing=sum(v is None for v in vals)
            cells.append(f"{sum(v is True for v in vals)}/3"+(f' ({missing} missing)' if missing else ''))
        lines.append('| '+r['item_id']+' | '+' | '.join(cells)+' |')
    lines+=['','Entries are all-seed correct counts, not best-of-three selection. Normal-stop refusals/no answers remain observed unsuccessful continuations; unfinished pre-answer caps remain technical missingness. Family-majority uncertainty is bounded rather than filled in.','',
      '## Primary endpoints','', '| Endpoint | Success / resolved families | Exact descriptive95% interval | Frozen / missing |','|---|---:|---:|---:|']
    for name,r in info['endpoints'].items():
        lo,hi=r['clopper_pearson_95'];ci=f'[{lo:.3f}, {hi:.3f}]' if lo is not None else 'not estimable'
        lines.append(f"| {name} | {r['successes']}/{r['observed']} | {ci} | {r['frozen']} / {r['missing']} |")
    lines+=['','Exact intervals are descriptive. The independent unit is family; this n5 outcome-selected cohort cannot estimate population prevalence or support asymptotic significance claims.','',
            '## Interpretation and controls','',f"Same-model Thinking-prefix sufficiency: **{d['RT_T_majority_successes']}/5**. Production support: **{d['counts']['PRODUCTION_SUPPORT']}/5**; utilization support: **{d['counts']['UTILIZATION_SUPPORT']}/5**; repair support: **{d['counts']['REPAIR_SUPPORT']}/5**. Text-insufficient items: **{d['counts']['TEXT_NOT_SUFFICIENT']}/5**.",'',
            'Source quality is fixed independently of transfer outcomes. Utilization requires no material evidence error and a valid derivation; repair requires flawed evidence and/or derivation. Question-only success weakens trace-specific interpretation. Shuffled success tests whether relevant content, rather than simply a long prefix, matters; all such outcomes above remain part of the interpretation.','']
    lines += [f"Only {adequate_c}/5 primary CoT prefixes meet the source-quality prerequisite for strong utilization. Thus zero utilization support is not evidence that the checkpoints are equally capable of using an adequate state. Production support establishes useful portability under this transfer assay; it does not certify every intermediate deduction or establish that production is the sole cause of the native advantage.", '']
    for c,r in info['controls'].items():lines.append(f"- {c}: majority success {r['successes']}/{r['observed']} resolved families; {r['missing']} missing.")
    lines+=['','These are checkpoint-specific operating regimes: checkpoint, sampling and output budget differ. No direct hidden-state mechanism or pure Thinking-on/off cause is identified. Failed R_T→T replay does not distinguish omitted multimodal state, early answer-safe cutoff, or stochastic continuation. Historical E*→Instruct failures are preserved single trials, not a newly replicated content-ablation control.','',
      '## Secondary B1 (descriptive)','', '| Item | R_T→T | R_T→I | R_C→I | R_C→T | Q→I | Q→T |','|---|---:|---:|---:|---:|---:|---:|']
    for r in info['secondary']:
        lines.append('| '+r['item_id']+' | '+' | '.join(str(sum(v is True for v in r['run_outcomes'][c]))+'/3' for c in conditions[:6])+' |')
    lines+=['','## Audit and resources','',
      f"Input/prefix receipts verified for all168 calls. Scientific first scoring156; separate-pass QC{score['n_second']}, agreement{sum(r['agreement'] for r in score['reviews'])}/{score['n_second']}. This is same-agent QC, not independent human reliability. Long source-prefix audits combine whole-prefix lexical scanning and targeted semantic/content reading; they are not an exhaustive independent sentence-by-sentence audit. Exact quotes, offsets, candidate scans and full source/target text are preserved.",'',
      f"Scientific continuations: {int(scientific['scoreable'].sum())}/156 scoreable; {int(scientific['cap_hit'].sum())} cap hits and {int((~scientific['scoreable']).sum())} missing. Capped unfinished outputs are not relabeled incorrect. Shuffled continuations sometimes answer the unrelated source task; their emitted final values are scored against the assigned target by the frozen equivalence rule, not credited for source-task correctness. Numeric matches alone do not certify target-directed reasoning.",'',
      f"Allocated compute **{res['allocated_gpu_hours']:.6f} GPU-hours** including technical validation/startup (target<5, hard7). All stage allocations released. No retries, downloads, source regeneration, hidden-state intervention or next experiment.",'',
      'Figures: figures/U1_transfer_assay.png; U2_primary_transfer_matrix.png; U3_interpretation_classes.png; U4_source_content_audit.png (PDF companions). Full response reading index: reports/stage12us/v1/index.md. Machine-readable evidence:16 required named artifacts plus immutable audit/generation receipts.','',
      '## Exactly one recommendation','',d['recommendation'],'','Not launched. STOP.']
    (ROOT/'stage12us_summary.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':figures();reading_copies();summary()
