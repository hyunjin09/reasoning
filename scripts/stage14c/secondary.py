"""Prespecified source-only sensitivities, gated after the primary result seal."""
from collections import defaultdict
from scripts.stage14c.common import *
from scripts.stage14c.analyze import task_panels,public


def main():
    seal=load(ROOT/'audit/primary_analysis_seal.json')
    for p,h in seal['files'].items():assert sha(p)==h,p
    outcomes=rows(ROOT/'scoring/scored_outcomes.jsonl')
    cohort={r['family_id']:r for r in rows(ROOT/'source/cohort_manifest.jsonl')}
    qc={r['family_id']:r for r in rows(ROOT/'source/estar_eligibility_manifest.jsonl')}
    evidence={r['family_id']:r for r in rows(ROOT/'source/evidence_atoms.jsonl')}
    groups=defaultdict(list)
    for r in outcomes:
        if r['benchmark']=='math':continue
        fid=r['family_id'];c=cohort[fid];q=qc[fid];b=r['benchmark']
        fields=dict(category=c['category'],source_stratum=c['stratum'],answer_kind=q['answer_kind'],
                    source_validity='clean_or_no_identified_defect' if not q['source_validity_flags'] else 'source_flagged',
                    known_render_repeats='multiple_source_rows' if len(c['alias_item_ids'])>1 else 'single_source_row')
        if fid in evidence:
            e=evidence[fid]
            fields.update(structured_atom='yes' if any(a['atom_type']=='structured_layout' for a in e['atoms']) else 'no',
                          primary_atom_count=str(e['primary_atom_count']),internal_subfact_count=str(e['structured_subfact_total']))
        for field,value in fields.items():groups[(b,field,value)].append(r)
        if b=='MMStar' and c['category']!='math':groups[(b,'non_math_source_category','yes')].append(r)
    result=[]
    for (b,field,value),data in sorted(groups.items()):
        panels=task_panels(data,b+'|'+field+'|'+value)
        result.append(dict(benchmark=b,field=field,value=value,native_n=len(data),eligible_n=sum('I_E' in r for r in data),
            descriptive_only=True,tiny_stratum=len(data)<20,panels={k:public(v) for k,v in panels.items()}))
    save(ROOT/'analysis/secondary_and_sensitivity.json',dict(at=now(),strata=result,
        interpretation='Source-only strata; no outcome matching. Small strata are descriptive and not independent primary tests.',
        historical_exposure=load(ROOT/'source/source_exposure_audit_g1_v1.json'),
        exposure_limit='Unknown historical per-item exposure cannot be turned into an untouched-vs-exposed comparison. Exact/verified math-anchor overlap was excluded before selection.',
        math_anchor_context_files=['outputs/stage14b/analysis/secondary_results.json','outputs/stage14b/analysis/family_cluster_sensitivity.json','outputs/stage14b/analysis/mathverse_modality_profile.json']))
    save(ROOT/'audit/secondary_analysis_seal.json',dict(at=now(),sha256=sha(ROOT/'analysis/secondary_and_sensitivity.json'),primary_seal_sha256=sha(ROOT/'audit/primary_analysis_seal.json')))
if __name__=='__main__':main()
