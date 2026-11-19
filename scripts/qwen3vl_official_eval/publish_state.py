"""Publish compact state only after all evidence and resource checks pass."""
from pathlib import Path
from scripts.qwen3vl_official_eval.common import ROOT, load, now

def main():
    closure=load(ROOT/'audit/closure_validation.json');assert closure['status']=='PASS'
    gate=load(ROOT/'audit/sanity_technical_gate.json')
    resource=load(ROOT/'qwen3vl_official_eval_resource_accounting.json')
    assert resource['all_stage_allocations_released']
    stamp=now();decision=gate['decision']
    d=gate['conditions']['instruct'];t=gate['conditions']['thinking']
    facts=(f"Official fixed12 sanity: Direct {d['finals']}/12 committed finals, {d['caps']} caps, "
           f"{d['pathologies']} repetition pathologies; Thinking {t['finals']}/12 finals, "
           f"{t['caps']} caps, {t['pathologies']} pathologies. "
           f"Allocated {resource['allocated_gpu_hours']:.6f} GPUh; all stage GPUs released.")
    variants=[]
    for v in load(ROOT/'qwen3vl_official_sanity_manifest.json')['ablations']:
        p=ROOT/'annotations'/f"{v['name']}_review.json"
        if p.exists():
            s=load(p)['summary'];variants.append(f"{v['name']}: {s['finals']} finals/{s['caps']} caps/{s['pathologies']} pathologies")
    diagnostics='; '.join(variants) if variants else 'Conditional ablation NOT_RUN.'
    summary=f"**CURRENT — {stamp}: Official Qwen3-VL MathVision technical audit COMPLETE / STOP: {decision}.** {facts} {diagnostics} No accuracy-based selection. Claim3 primary/oracle/CoT/reserve remain NOT_RUN. No follow-on launched. [Report](../outputs/qwen3vl_official_eval/v1/qwen3vl_official_sanity_summary.md) · [Phase](phase_memory/phase_qwen3vl_official_eval_audit.md).\n\nEarlier entries are historical.\n\n"
    for name in ['workflow_state.md','research_plan.md']:
        p=Path('workspace')/name;p.write_text(summary+p.read_text())
    p=Path('workspace/phase_memory/phase_qwen3vl_official_eval_audit.md')
    text=p.read_text()
    start=text.index('## Current State\n');end=text.index('\n## Evidence That Matters',start)
    text=text[:start]+f"## Current State\nComplete / STOP: {decision}. {facts}\n{diagnostics}\nAll requested deliverables and closure checks saved under {ROOT}. No scientific rerun.\n"+text[end:]
    start=text.index('## Failed Attempts and Lessons\n');end=text.index('\n## Open Candidates',start)
    text=text[:start]+"## Failed Attempts and Lessons\nJobs126162/126163 failed before generation due to an overlong Unix socket path. Shortening only project TMPDIR repaired startup; retry126167/126168 used unchanged frozen scientific settings. All failed allocations counted. MathVision-specific recipes differ from root generic Thinking defaults and from the historical project prompt/decoding. Historical token replay alone did not establish official benchmark faithfulness.\n"+text[end:]
    start=text.index('## Open Candidates\n');end=text.index('\n## Next-Step Decision',start)
    text=text[:start]+"## Open Candidates\nNone within this completed action. Any Claim3 scientific rerun requires separate user instruction; do not automatically launch.\n"+text[end:]
    text+=f"\n## Final Result — {stamp}\n{decision}. {facts}\n{diagnostics}\nPreserved Stage11C/11C-R hashes, source commits, canonical input hashes, raw official outputs and technical reviews. Fair native comparison uses each variant's validated intended decoding recipe, not forced identical hyperparameters.\n\n## Next-Step Decision — {stamp}\nSTOP. Return the technical validation result to the user; no new scientific action selected or launched.\n"
    p.write_text(text)
    p=Path('workspace/decision_log.md')
    with p.open('a') as f:
        f.write(f"\n## D125 — {stamp}: Official MathVision baseline audit closed\n{decision}. {facts}\n{diagnostics}\nDirect official recipe includes canonical Hint/Question/Choices, temperature0.7/top-p0.8/presence1.5/cap32768; old recovered recipe used raw question,1.0/.95/presence0/cap40960. Runtime and prompt also differ. Completion-only evidence does not uniquely attribute historical loops. Source/audit/result evidence: outputs/qwen3vl_official_eval/v1/qwen3vl_official_sanity_summary.md. No Claim3 rerun authorized by this result.\n")
    p=Path('reports/index.md');text=p.read_text()
    marker='# Workflow Report Index\n'
    assert text.startswith(marker)
    text=text.replace(marker,marker+f"\nCurrent technical audit: [{decision}](../outputs/qwen3vl_official_eval/v1/qwen3vl_official_sanity_summary.md). {facts} No scientific rerun.\n",1)
    p.write_text(text)
    print('COMPACT_STATE_PUBLISHED',decision)

if __name__=='__main__':main()
