"""Close the bounded study with measured claims, figures and explicit stop records."""
import os,shutil
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage10a.common import ROOT,load,save,sha,now
from scripts.stage10a.account import main as account


def estimate(r,scale=1):
    return f"{r['point']*scale:.2f} [{r['ci95'][0]*scale:.2f}, {r['ci95'][1]*scale:.2f}]"


def figures(a,b,c):
    dest=ROOT/'figures';dest.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
    def finish(fig,name):
        for suffix in ('png','pdf'):
            p=dest/f'{name}.{suffix}';assert not p.exists();fig.savefig(p,bbox_inches='tight')
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,3));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    labels=['Image / visual\nevidence','Self-generated\ncount statement','Downstream\nanswer']
    for x,label in zip([.15,.5,.85],labels):
        ax.text(x,.60,label,ha='center',va='center',bbox=dict(boxstyle='round,pad=.6',fc='#eaf1f8',ec='#537393'))
    for x,y in [(.28,.38),(.62,.73)]:ax.annotate('',(y,.60),(x,.60),arrowprops=dict(arrowstyle='->',lw=2,color='#537393'))
    ax.text(.5,.20,'Tested causal pathway; a full perceptual-to-textual handoff is NOT established.\nImage-off: cached visual state retained. Text-only: fresh cache, no image state.',ha='center',va='center')
    ax.set_title('Stage10A: causal text influence versus a perceptual handoff',pad=18)
    finish(fig,'figure1_handoff_schematic')
    fig,axes=plt.subplots(1,2,figsize=(10,4));x=np.arange(3);anchors=('pre','emit','post')
    for ax,condition,field,cifield,title in [(axes[0],'text_only','accuracy','accuracy_ci95','Fresh text-only sufficiency'),
        (axes[1],'image_off','damage','damage_ci95','Future direct-image-access necessity')]:
        y=np.array([a[condition][field][t] for t in anchors])*100;ci=np.array([a[condition][cifield][t] for t in anchors])*100
        ax.errorbar(x,y,yerr=np.array([y-ci[:,0],ci[:,1]-y]),fmt='o-',capsize=5,color='#2563a6',lw=2)
        ax.set_xticks(x,anchors);ax.set_title(title);ax.set_ylabel('Accuracy (%)' if field=='accuracy' else 'FULL − image-off (percentage points)')
        ax.set_ylim((0,105) if field=='accuracy' else (-15,40));ax.axhline(0,color='gray',lw=.7)
    fig.suptitle('24 independent images; paired image bootstrap, 4,000 draws')
    fig.tight_layout();finish(fig,'figure2_necessity_sufficiency')
    fig,ax=plt.subplots(figsize=(9,4.7));conditions=('original','counterfactual','delete','sham');x=np.arange(4);bottom=np.zeros(4)
    categories=[('follow_original','Original count','#507daa'),('follow_counterfactual','Edited count','#c96b36'),
        ('other','Other valid answer','#98a69a'),('unscorable','No final answer','#c5c5c5')]
    for key,label,color in categories:
        values=[]
        for cond in conditions:
            r=b['completion'][cond];n=r[key] if key!='other' else r['n']-r['follow_original']-r['follow_counterfactual']-r['unscorable']
            values.append(n/24*100)
        ax.bar(x,values,bottom=bottom,label=label,color=color);bottom+=values
    ax.set_xticks(x,['Original','Counterfactual','Delete','Sham']);ax.set_ylabel('Final-answer outcome (%)');ax.set_ylim(0,105)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.13),ncol=2,frameon=False)
    ax.set_title('Editing the emitted count redirects13/24 answers\nOriginal/sham:0/24 edited-count answers; CF:8/24 missing finals')
    finish(fig,'figure3_counterfactual_text_control')
    fig,ax=plt.subplots(figsize=(8,4.5));values=[c[k]['point'] for k in ('E_image','E_text','text_minus_image')]
    intervals=np.array([c[k]['ci95'] for k in ('E_image','E_text','text_minus_image')]);x=np.arange(3)
    ax.bar(x,values,color=['#507daa','#c96b36','#7972a0'],width=.55)
    ax.errorbar(x,values,yerr=np.array([np.array(values)-intervals[:,0],intervals[:,1]-np.array(values)]),fmt='none',ecolor='black',capsize=5)
    ax.axhline(0,color='gray',lw=.8);ax.set_xticks(x,['Image effect','Text effect','Text − image']);ax.set_ylim(-2.1,2.1)
    ax.set_ylabel('Effect on signed count-following score');ax.set_title('Post-anchor source × text test:12 independent images')
    ax.text(.5,-.21,'Pre not measured: the selected fact had not yet been emitted.\nLater native recounts remain unchanged; no dominance reversal is measured.',transform=ax.transAxes,ha='center',va='top')
    finish(fig,'figure4_image_text_dominance')


def main():
    assert os.environ.get('SLURM_JOB_ID')
    a=load(ROOT/'audit/gate_a_inference.json');b=load(ROOT/'audit/gate_b_inference.json');c=load(ROOT/'audit/dominance_v2_inference.json')
    assert a['gate_a_pass'] and b['gate_b_pass'] and b['H3_supported'] and not a['H1_supported']
    required=ROOT/'stage10a_text_edit_results.parquet';assert not required.exists()
    shutil.copyfile(ROOT/'stage10a_text_counterfactual_results.parquet',required)
    for name,reason in [('stage10a_reserve_extension.json','H1 point is zero; the reserve cannot rescue a null component.'),
        ('stage10a_mathvision_bridge.json','The full controlled handoff pattern is not established.')]:
        save(ROOT/name,dict(at=now(),status='not_run',gate_pass=False,reason=reason,additional_gpu_hours=0))
    account();resources=load(ROOT/'stage10a_resource_accounting.json')
    facts=load(ROOT/'audit/fact_truth_after_selection.json');selected=load(ROOT/'stage10a_event_selection.json')
    primary=set(selected['primary_ids']);correct_facts=sum(r['fact_correct'] for r in facts['rows'] if r['query_id'] in primary)
    ar=load(ROOT/'audit/gate_a_scored.json')['rows'];ix={(r['query_id'],r['condition'],r['anchor']):r for r in ar}
    gains=[q for q in primary if ix[q,'text_only','post']['correct'] and not ix[q,'text_only','pre']['correct']]
    completion_rescues=sum(ix[q,'text_only','pre']['unscorable'] for q in gains)
    save(ROOT/'audit/completion_interpretation.json',dict(at=now(),text_sufficiency_improved_images=sorted(gains),
        improved_from_missing_pre_final=completion_rescues,improved_from_valid_wrong_pre_final=len(gains)-completion_rescues,
        counterfactual_missing_finals=b['completion']['counterfactual']['unscorable'],
        interpretation='Bounded final correctness includes completion. Missing finals are not semantic read errors; no cap or anchor rescue.'))
    inference=dict(at=now(),status='complete_stop',outcome='C',primary_images=24,reserve_images=8,dominance_images=12,
        H1_supported=False,H2_supported=a['H2_supported'],H3_supported=b['H3_supported'],full_handoff_supported=False,
        gate_a_pass=True,gate_b_pass=True,post_text_dominance_supported=c['post_text_dominance_supported'],
        visual_necessity_decrease=a['image_off']['post_minus_pre'],text_sufficiency_increase=a['text_only']['post_minus_pre'],
        counterfactual_minus_original=b['cf_minus_original'],counterfactual_minus_sham=b['cf_minus_sham'],
        counterfactual_minus_delete=b['cf_minus_delete'],delete_minus_sham_accuracy=b['delete_minus_sham_accuracy'],
        post_E_text=c['E_text'],post_E_image=c['E_image'],post_text_minus_image=c['text_minus_image'],pre_dominance_measured=False,
        independent_unit='image',bootstrap_draws=4000,seed=920260927,all_examples_missing_final_incorrect=True,
        semantic_score_definition='I(final follows edited count) - I(final follows original emitted count); other/missing=0; effects are score units, not percentage points.',
        supported_claim='At the emission anchor, changing the selected self-generated fact causally redirects fresh image-free continuations. A perceptual-to-textual handoff and phase termination are not established.',
        recommendation='Retain causal text-carrier influence as a bounded result alongside native visual-use findings; do not promote a perceptual-to-textual phase-handoff claim.',
        no_follow_on_launched=True,source_inference_sha256={str(ROOT/'audit'/p):sha(ROOT/'audit'/p) for p in ('gate_a_inference.json','gate_b_inference.json','dominance_v2_inference.json')},
        limitations=['Controlled24-image counting task; one native4B Thinking model; BF16 greedy512 total-token budget.',
            'Pre already contains object descriptions; cached image-off retains latent visual state.',
            'Ten primary post anchors contain option binding; subgroup without binding is reported.',
            'Four selected emitted facts are incorrect; the20 correct-fact stratum separately supports text influence.',
            'Eight counterfactual text continuations have no final answer; actual edited-count following is13/24.',
            'Post2x2 edits only the selected first fact; later original-value recounts remain intact.',
            'No pre2x2, reserve, MathVision bridge or CoT comparison; no claimed dominance reversal.'])
    save(ROOT/'stage10a_primary_inference.json',inference);figures(a,b,c)
    table=[]
    for anchor in ('pre','emit','post'):
        t=a['completion']['text_only/'+anchor];v=a['completion']['image_off/'+anchor]
        table.append(f"| {anchor} | {t['correct']}/24 | {v['correct']}/24 | {t['unscorable']}/24 | {v['unscorable']}/24 |")
    edit_table=[]
    for cond,r in b['completion'].items():edit_table.append(f"| {cond} | {r['follow_original']} | {r['follow_counterfactual']} | {r['correct']} | {r['unscorable']} |")
    dominance_table=[]
    for cond,r in c['completion'].items():dominance_table.append(f"| {cond} | {r['follow_original']} | {r['follow_counterfactual']} | {r['correct_current_image']} | {r['unscorable']} |")
    manual=sum(sum(r['requires_manual'] for r in load(ROOT/f'audit/{stage}_review_packet.json')['rows']) for stage in ('gate_a','gate_b','dominance_v2'))
    report=f'''# Stage10A — causal perceptual-to-textual handoff

Completed / STOP at {now()}. **Outcome C: causal text influence, without a demonstrated perceptual handoff or phase termination.**

Changing the emitted count redirects13/24 fresh image-free continuations toward the edited value, compared with0/24 original and sham continuations. Text-only sufficiency improves, but visual-access necessity does not decrease across the frozen anchors. Thus the full handoff claim fails, regardless of the downstream2×2 result.

## Frozen design and execution

Reuse all32 source images and64 native Stage9A.5 FULL traces unchanged. Gold-free semantic review sealed32 eligible events; deterministic hash selection retained24 independent images (12 color/12 shape) and8 reserve. First explicit count, pre/emit/post anchors and analysis rules were frozen before interventions. Correctness did not select the primary cohort; {correct_facts}/24 emitted facts are source-correct. The20 correct-fact stratum is reported separately.

Qwen3-VL-4B-Thinking revision1de27d8c51f12e819435303b9e84c4e25ba8401e; BF16, TF32 off, greedy, native Thinking template/DeepStack,512 total generated tokens including replayed prefix. Fresh text-only replay copies no image/cache/hidden state. Image-off preserves the original prefix/cache and masks future generated-query→image-key access in all36 decoder layers, beginning with the correct first future query. All24 native prefixes match saved tokens.

Gate A:144 continuations. Gate B:96 logical conditions,72 new and24 exact original reuses. Post2×2:48 new continuations on12 correct-fact/no-option-binding images (six per attribute), selected without intervention-effect ranking. Total:288 logical rows,264 unique new scientific continuations. Independent unit=image; equal weight;4,000 paired bootstrap draws, seed920260927. All intervals below are95% percentile intervals.

## Sufficiency and necessity

| Anchor | Text-only correct | Image-off correct | Text-only no final | Image-off no final |
|---|---:|---:|---:|---:|
{chr(10).join(table)}

Selected native FULL accuracy:20/24. **H2 post−pre: {estimate(a['text_only']['post_minus_pre'],100)} percentage points. H1 necessity decrease: {estimate(a['image_off']['post_minus_pre'],100)} percentage points.** Gate A opens via H2 alone under the frozen "if neither" rule. H1 is unsupported.

The four H2 gains comprise {completion_rescues} cases improving from a missing pre final and {len(gains)-completion_rescues} from a valid wrong pre final. This is bounded final-answer performance, not a pure local visual-read accuracy measure. Excluding the10 post anchors with option binding leaves14 images: H2 {estimate(a['without_post_option_binding']['text_only']['post_minus_pre'],100)}pp. Color H2 {estimate(a['by_attribute']['color']['text_only']['post_minus_pre'],100)}pp; shape H2 {estimate(a['by_attribute']['shape']['text_only']['post_minus_pre'],100)}pp. The descriptive subgroup intervals do not establish an attribute difference.

Pre-text already contains object inventories, and image-off retains prior image-derived state. Zero necessity decrease therefore does not rule out an earlier or latent transfer. No anchor was moved after this result.

## Emission-anchor text causality

Original is an exact reuse. Counterfactual changes only the selected count to the next valid1–5 value. Deletion removes that fact clause; sham preserves its meaning. Earlier inventories/arithmetic remain unchanged, even when they contradict the changed count. Singleton edits include documented grammatical agreement.

| Condition | Follow original count | Follow edited count | Source-correct | No final |
|---|---:|---:|---:|---:|
{chr(10).join(edit_table)}

Signed semantic score: +1 for the edited count, −1 for the original emitted count,0 for other/missing answers. These contrasts are **score units, not accuracy percentage points**:

- CF−original: {estimate(b['cf_minus_original'])}.
- CF−sham: {estimate(b['cf_minus_sham'])}.
- CF−delete: {estimate(b['cf_minus_delete'])}.
- Delete−sham source accuracy: {estimate(b['delete_minus_sham_accuracy'],100)}pp.

Both directional thresholds, perturbation-noise contrast, deletion criterion and attribute-direction checks pass. Correct-fact stratum (20 images), CF−sham: {estimate(b['correct_emitted_fact_stratum']['cf_minus_sham'])}. Color: {estimate(b['by_attribute']['color']['cf_minus_sham'])}; shape: {estimate(b['by_attribute']['shape']['cf_minus_sham'])}. H3 and Gate B pass. Eight CF outputs fail to close reasoning at512; actual13/24 edited-count answers establish directional following separately from that completion loss. No scratchpad candidate was promoted into the final channel and no cap was increased.

## Post-anchor image × text dominance

Fresh multimodal caches are recomputed consistently for all four conditions. I1 changes one source object's asked attribute, and T1 edits only the first selected fact. Later native recounts retain their original values. All original rerenders are pixel-identical. Twelve sources and48 conditions were frozen before2×2 science. A pre-science geometry review corrected image007's square-orientation candidate; v1 images/manifests and the unchanged-runtime technical checks remain preserved, with v2 linkage recorded.

| Condition | Follow original count | Follow edited count | Correct for current image | No final |
|---|---:|---:|---:|---:|
{chr(10).join(dominance_table)}

Factorial average text effect: **{estimate(c['E_text'])}**. Image effect: **{estimate(c['E_image'])}**. Text−image: **{estimate(c['text_minus_image'])}**. Frozen post-text-dominance criterion: **{'PASS' if c['post_text_dominance_supported'] else 'NOT SUPPORTED'}**. Later unchanged recounts limit this to the selected first fact within the post prefix; it does not compare all textual carriers jointly against vision.

No pre2×2 was run because the selected fact did not yet exist in pre text. No dominance reversal is measured. No downstream log-prob assay was collected; the selected primary answer-following endpoint and deletion/sham controls are complete.

## Validation, resources and stop

Sixteen focused CPU tests pass. Eight actual-model Gate-A validation cases pass after one text-processor schema repair; two disjoint image+prefix cases exactly match cached native continuations. The geometry repair reuses these technical results because runtime and technical inputs are unchanged. Raw final-answer review was sealed before joining source gold; {manual} logical ambiguous/unclosed outputs received manual decisions. Literal/raw extraction sensitivities are retained in inference JSON. The independent audit checks coverage, all source and receipt hashes, paired arithmetic/bootstrap, image-free versus cached state semantics, and native final-channel scoring.

Actual Slurm allocation: **{resources['allocated_gpu_hours']:.3f} GPU-hours**, including technical work, one failed preflight, hashing/loading and workers that found no remaining bundles; continuation generation {resources['generation_gpu_hours']:.3f} GPU-hours. Peak concurrent GPUs:{resources['observed_peak_gpus']}, authorized ceiling8. All GPU jobs are terminal and resources released. Source annotations:32 native events,24 text edits,12 source edits; human/agent annotation wall time was not timed. No new dataset/model download.

The8-image precision reserve and MathVision bridge were **not run**: H1 is zero, so their gates fail. No CoT comparison, Stage10B, new anchor, new fact search, cap rescue or next experiment was launched.

**One recommendation:** {inference['recommendation']}

## Evidence and figures

- [Primary inference](stage10a_primary_inference.json), [resource accounting](stage10a_resource_accounting.json), [event selection](stage10a_event_selection.json).
- [Gate A](audit/gate_a_inference.json), [Gate B](audit/gate_b_inference.json), [post2×2](audit/dominance_v2_inference.json), [source repair](audit/source_geometry_repair.json).
- [Independent final audit](audit/final_validation.json); all11 requested artifacts are present, with explicit optional-not-run records.
- [Figure1: tested pathway](figures/figure1_handoff_schematic.png); [Figure2: necessity/sufficiency](figures/figure2_necessity_sufficiency.png); [Figure3: text control](figures/figure3_counterfactual_text_control.png); [Figure4: post dominance](figures/figure4_image_text_dominance.png). PDF companions are included.
'''
    path=ROOT/'stage10a_summary.md';assert not path.exists();path.write_text(report)
    print('STAGE10A_COMPLETE_OUTCOME_C',resources['allocated_gpu_hours'],'GPU-hours',flush=True)


if __name__=='__main__':main()
