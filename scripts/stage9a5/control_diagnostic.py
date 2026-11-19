"""One bounded diagnostic of the observed control failure, without new inference."""
import os
from scripts.stage9a5.common import ROOT, COT, load, save, sha, now
from scripts.stage9a5.compare import paired_contrast
from scripts.stage9a5.audit import check_contrast


def counts(rows):
    baseline={r['query_id']:r for r in rows if r['policy']=='full'}
    result={}
    for policy in sorted(set(r['policy'] for r in rows)):
        rs=[r for r in rows if r['policy']==policy]
        lost=[r for r in rs if baseline[r['query_id']]['correct'] and not r['correct']]
        gained=[r for r in rs if not baseline[r['query_id']]['correct'] and r['correct']]
        result[policy]=dict(n=len(rs),correct=sum(r['correct'] for r in rs),
            capped=sum(r['at_length_cap'] for r in rs),unscorable=sum(r['option'] is None for r in rs),
            correct_to_wrong=len(lost),wrong_to_correct=len(gained),
            lost_with_no_final=sum(r['option'] is None for r in lost),
            lost_with_valid_wrong_final=sum(r['option'] is not None for r in lost),
            lost_query_ids=[r['query_id'] for r in lost],gained_query_ids=[r['query_id'] for r in gained])
        assert sum(r['correct'] for r in baseline.values())-result[policy]['correct']==len(lost)-len(gained)
    return result


def main():
    assert os.environ.get('SLURM_JOB_ID')
    standard=load(ROOT/'stage9a5_thinking_full_baseline.json')['rows']+load(ROOT/'audit/t1_scored.json')['rows']
    sink=load(ROOT/'audit/sink_scored.json')['rows'];cot=load(COT/'audit/sink_scored.json')['rows']
    paired={p:paired_contrast(sink,cot,p) for p in ('t0','t128')}
    for r in paired.values():check_contrast(sink,cot,r)
    out=dict(at=now(),reason='Standard128 preserves; null-sink128 does not. Verify completion vs valid-answer changes once, without new generation or criterion changes.',
             stage='post-control bounded diagnostic',thinking_standard=counts(standard),thinking_null_sink=counts(sink),
             cot_null_sink=counts(cot),paired_control_contrasts=paired,independent_paired_audit=True,
             cause_status='unknown',interpretation='Counts locate scored damage in completion or answer changes; they do not identify why the intervention changed completion.',
             primary_design_unchanged=True,no_additional_gpu_work=True,
             source_sha256={str(p):sha(p) for p in [ROOT/'audit/t1_scored.json',ROOT/'audit/sink_scored.json',COT/'audit/sink_scored.json']} )
    save(ROOT/'audit/control_completion_diagnostic.json',out)
    print({k:v for k,v in out.items() if k not in ('source_sha256','paired_control_contrasts')},flush=True)
    print('CONTROL128',paired['t128'],flush=True)


if __name__=='__main__':main()
