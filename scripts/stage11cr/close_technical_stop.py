"""Required transparent closure only for a sealed R3 technical STOP."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scripts.stage11cr.common import ROOT,OLD,ARMS,load,save,sha,now,verify_frozen


def main():
    cfg=verify_frozen();r3=load(ROOT/'stage11cr_nonprimary_validation.json')
    assert r3['gate']['status']=='STOP' and r3['pass'] is False
    resource=load(ROOT/'stage11cr_resource_accounting.json')
    assert resource['all_stage_allocations_released'] and resource['allocated_gpu_hours_observed']<=9
    split=load(OLD/'stage11c_primary_split.json');rows=[]
    for family in split['primary']:
        for arm in ARMS:
            rows.append(dict(family_id=family['family_id'],item_id=family['item_id'],arm=arm,
                condition='native',status='NOT_RUN',correct=None,committed_final=None,
                reason='NONPRIMARY_COMPLETION_VALIDITY_STOP'))
    p=ROOT/'stage11cr_native_td_results.parquet';assert not p.exists();pd.DataFrame(rows).to_parquet(p,index=False)
    for name in ['native_validity_gate','native_performance_gate']:
        save(ROOT/f'stage11cr_{name}.json',dict(at=now(),status='NOT_EVALUATED',
            reason='R3 completion validation failed before scientific native rerun.',n_executed=0,n_planned=160))
    save(ROOT/'stage11cr_primary_inference.json',dict(at=now(),status='NOT_ESTIMATED',P1=None,P2=None,P3=None,
        closure_fraction=None,claim3_supported=False,cohort_unchanged=True,
        reason='Technical STOP before native/oracle rerun; no scientific null or mechanism localization.'))
    figure_dir=ROOT/'figures';figure_dir.mkdir(exist_ok=True)
    labels=['Stage11C\nfirst16/arm','Historical\nselected6/arm','Replayed\nselected6/arm','Nonprimary\n12/arm']
    fig,axes=plt.subplots(1,2,figsize=(12,4.7));x=np.arange(4);width=.34
    for i,arm in enumerate(ARMS):
        old_caps=16 if arm=='thinking' else 15;old_missing=16 if arm=='thinking' else 10
        stat=r3['gate']['arms'][arm]
        values=[[old_caps/16,0,0,stat['caps']/12],[old_missing/16,0,0,(12-stat['finals'])/12]]
        for ax,y in zip(axes,values):
            bars=ax.bar(x+(i-.5)*width,np.array(y)*100,width,label=arm.replace('instruct_direct','Direct').title())
            ax.bar_label(bars,labels=[f'{v*100:.0f}%' for v in y],padding=3,fontsize=9)
    for ax,title in zip(axes,['Cap-hit rate','No committed final']):
        ax.set_xticks(x,labels,fontsize=9);ax.set_ylim(0,113);ax.set_ylabel('% of calls');ax.set_title(title)
        ax.spines[['top','right']].set_visible(False)
    axes[0].legend(loc='upper right');fig.suptitle('Historical replay succeeds; independent completion gate controls rerun',fontsize=12)
    fig.tight_layout()
    for ext in ['png','pdf']:fig.savefig(figure_dir/f'figure_r1_technical_reproduction.{ext}',dpi=180)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,3));ax.axis('off')
    ax.text(.5,.74,'P1 / P2 / P3: NOT ESTIMATED',ha='center',fontsize=18,weight='bold')
    ax.text(.5,.43,'Nonprimary completion-validity STOP before native and oracle rerun',ha='center',fontsize=12)
    ax.text(.5,.19,'80 primary + 40 reserve preserved; no outcome imputation or mechanism claim',ha='center',fontsize=11)
    for ext in ['png','pdf']:fig.savefig(figure_dir/f'figure_r4_localization_not_estimated.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)
    t,d=[r3['gate']['arms'][a] for a in ARMS]
    report=f'''# Stage11C-R — technical repair reproduced; nonprimary gate STOP

Stage11C-R restored the historical execution recipe but did not establish a completion-valid regime for the unchanged Stage11C assay. The prescribed nonprimary gate failed before any primary or oracle rerun. P1/P2/P3 remain unestimated. This is not a scientific null or evidence for an upstream/downstream mechanism.

## Reconstruction and repair
Two historical execution sources were audited: Stage9A and Stage8B-v2. Both used the same pinned2B checkpoints/native image format and sampled decoding at temperature1.0,top-p.95,top-k20,repetition penalty1.0, with eager language/SDPA vision attention and a common40960 generated-token budget. Stage11C forced greedy decoding, used SDPA language attention and4096/8192 caps. Historical per-call RNG/rope reset and wrapper differences were recorded; unrecorded TF32/default-cache fields remain UNKNOWN.

All12 fixed known-good cases (six Thinking/six Direct, no primary overlap) reproduced their full historical token sequences exactly. All reached EOS and a committed final without cap hits. Prompt tokens, image tensors and chat templates match exactly. No historical logits were available. Reproduction does not certify answer correctness.

The fixed two-case SDPA diagnostic isolated sampling: both greedy calls repeated and capped at8192; restoring historical sampling reached EOS and terminal answers in both. This supports a decoding contribution on those cases, not a universal root-cause claim. SDPA sampled traces differ from the historical eager traces; the exact historical protocol wins the predeclared selection priority. No accuracy or T-D gap selected the repair.

The initial local specification unnecessarily proposed4096/8192 cap selection. Before any nonprimary/primary output, a versioned correction applied approved plan section12: use the recovered common40960 historical budget. Initial spec/config and hashes remain preserved, with the correction in stage11cr_cap_protocol_amendment_v1.md. There was no longer-cap search or mode-specific cap.

## Fixed nonprimary validation
The original12 Stage11C technical cases and original item seeds were rerun in both modes under the single repaired historical protocol. None came from the80 primary or opened40 reserve. No correctness scoring occurred.

| Arm | Calls | Cap hits | Committed final | Repetition pathology |
|---|---:|---:|---:|---:|
| Thinking |12|{t['caps']}|{t['finals']}|{t['loops']}|
| Direct |12|{d['caps']}|{d['finals']}|{d['loops']}|

Total cap rate {r3['gate']['total_cap_rate']:.1%}. Required: total<15%,each arm<20%,each committed-final>=75%,no severe repetition imbalance. The sealed gate is STOP. The twelve-case pool was not replaced, decoding was not tuned further, and no new benchmark/model search was launched.

All {sum(bool(row.get('exact_token_identity')) for row in r3['rows'])}/24 validation generations also match their historical token sequences exactly, including capped outputs. Reproducing the implementation therefore does not establish completion validity for this frozen assay. Direct cap rate {d['caps']/12:.1%} and final rate {d['finals']/12:.1%} are reported independently; capped guesses were inspected for retraction rather than automatically treated as missing finals.

## Scientific design preserved
All120 eligible families,80 primary/40 reserve, E* and sufficiency judgments, neutral24/CoT48/native-state32 subsets, endpoints and statistical rules are unchanged. All160 repaired native conditions are explicitly NOT_RUN (correctness unknown), not incorrect. Oracle, neutral, CoT, reserve and downstream annotation did not run. Original Stage11C generations remain separate invalid-run evidence and are not pooled.

Figures: R1 documents technical completion and repair; R4 explicitly records unestimated localization. R2/R3/R5 are omitted because their required scientific branches did not execute. Raw generations, input hashes, literal completion reviews, Slurm receipts and the full discrepancy matrix are retained.

## Resources and limitations
Total allocated {resource['allocated_gpu_hours_observed']:.6f} GPU-hours across {len(resource['jobs'])} finite Slurm jobs; all GPUs released, hard 9 GPU-hour limit respected. The original nonprimary <0.5 GPU-hour planning estimate was contradicted by the recovered historical recipe (5.0803 GPU-hour historical forecast); this was disclosed before launch. Actual accounting includes startup, diagnostics and any failed/partial attempts. No downloads or global environment changes. Reviews are by the execution agent, not independent human annotation. Known-good selection used historical completion only. No correctness scoring or accuracy-based protocol selection occurred; historical metadata was available, so this is not a claim of fully blinded review.

## Recommendation
Close the Thinking-performance mechanism branch and finalize the paper around Claims 1 and 2.

STOP. No recommended follow-on action was executed.
'''
    (ROOT/'stage11cr_summary.md').write_text(report)
    print('TECHNICAL_STOP_ARTIFACTS_WRITTEN')


if __name__=='__main__':main()
