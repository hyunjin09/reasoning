"""Represent confirmed interrupted inputs as missing; never invent raw output."""
from scripts.stage12ws.common import ROOT, load, save, sha, now
from scripts.stage12ws import review

def packet(task, disposition):
    folder=ROOT/'generations'/task['task_id']
    assert not (folder/'generation.json').exists() and not (folder/'result.json').exists()
    assert sha(disposition['input_path'])==disposition['input_sha256']
    assert load(disposition['input_path'])['task']==task
    return dict(at=now(),task=task,raw='',tokens=None,cap_hit=None,
                finish_reason='INTERRUPTED_NO_OUTPUT',extraction=None,
                checks={'frozen_input_unchanged':True,'no_output_receipt':True},
                technical_missing=True,disposition=disposition,
                review_scope='No continuation exists. Empty review display is not a generated response; EOS, token count and cap status are unknown.')

def register():
    tasks={t['task_id']:t for t in review.tasks('phaseC')}
    for d in load(ROOT/'audit/phaseC_interrupted_dispositions_v1.json')['rows']:
        tid=d['task_id'];value=packet(tasks[tid],d)
        save(ROOT/'audit/review_packets'/f'{tid}.json',value)
        review.record(tid,False,None,'Confirmed prepared input without a generated output after the original job cleared; technical missingness, no retry.',ambiguous=True)
    save(ROOT/'audit/interrupted_registration_v1.json',dict(at=now(),n=4,raw_generation_files_created=0,
        original_scoring_uses_missing_value=True,source='audit/phaseC_interrupted_dispositions_v1.json'))

if __name__=='__main__':register()
