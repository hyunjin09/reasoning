"""Prepare masked literal-extraction packets without reading gold or accuracy."""
import argparse
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage8b.v2_scoring import extract_answer

MAIN = Path('outputs/stage9a_dynamics/amendment_v1')
BASE = Path('outputs/stage9a/v1')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def main(root):
    assert os.environ.get('SLURM_JOB_ID'), 'Full extraction runs as CPU Slurm'
    tasks = {r['task_id']: r for r in json.loads((root/'audit/tasks.json').read_text())['rows']}
    # The native review contains literal decisions only, not correctness/gold.
    native_review = json.loads((BASE/'annotations/answer_extraction_review_frozen.json').read_text())
    packet_to_task = {r['packet_id']: r['task_id'] for r in json.loads((BASE/'annotations/packet_index.json').read_text())['rows']}
    native_answers = {packet_to_task[r['packet_id']]: r for r in native_review['rows']}
    # Options were already displayed during the native masked review.
    native_packets = json.loads((BASE/'annotations/answer_extraction_packets.json').read_text())['rows']
    options = {packet_to_task[r['packet_id']]: r['options'] for r in native_packets}
    records = []; groups = {}; sources = {}; reused = []
    expected = {r['result_key'] for r in json.loads((root/'audit/interventions.json').read_text())['rows'] if r['execution']=='run'}
    for key in sorted(expected):
        directory = root/'rollouts/results'/key
        receipt = json.loads((directory/'result.json').read_text())
        task = receipt['task_id']; generation = json.loads((directory/'generation.json').read_text())
        text = generation['raw_decoded_response']; extraction = extract_answer(text, options[task])
        source = dict(result_key=key, task_id=task, generation=str(directory/'generation.json'),
                      generation_sha256=sha(directory/'generation.json'), receipt_sha256=sha(directory/'result.json'))
        if receipt['identical_native']:
            old = json.loads((Path(tasks[task]['native_dir'])/'generation.json').read_text())
            assert generation['generated_token_ids']==old['generated_token_ids']
            reused.append(dict(source, reviewed_answer=native_answers[task]['reviewed_answer'],
                               raw_extraction=extraction, review_source='sealed_exact_native_token_identity'))
            continue
        span = extraction['span']
        context = text[max(0,span[0]-220):min(len(text),span[1]+150)] if span else text[-1100:]
        display = dict(extraction=extraction, options=options[task], extraction_context=context,
                       tail=text[-1100:], normal_eos=receipt['normal_eos'], at_length_cap=receipt['at_length_cap'])
        # Absolute offsets do not change literal review context; retain them per result.
        signature = dict(display, extraction={k:v for k,v in extraction.items() if k!='span'})
        packet = 'a_'+hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()[:24]
        groups.setdefault(packet, dict(packet_id=packet, **display))
        sources.setdefault(packet, []).append(source)
        records.append(dict(source, packet_id=packet, raw_extraction=extraction))
    packets = [dict(review_index=i, **groups[key]) for i,key in enumerate(sorted(groups))]
    out = root/'annotations';out.mkdir(exist_ok=True)
    save(out/'answer_packets.json', dict(rows=packets, masking='No arm/condition IDs, gold, correctness or causal scores. Writing style may reveal arm. Single annotator.'))
    save(out/'answer_packet_index.json', dict(rows=records, sources_by_packet=sources, exact_native_reuse=reused))
    save(out/'answer_preparation.json', dict(at=datetime.now(timezone.utc).isoformat(), expected=len(expected),
        exact_native_reuse=len(reused), needs_review_results=len(records), unique_review_packets=len(packets),
        methods=dict(Counter(p['extraction']['method'] for p in packets)),
        native_review_sha256=sha(BASE/'annotations/answer_extraction_review_frozen.json'),
        packets_sha256=sha(out/'answer_packets.json'), index_sha256=sha(out/'answer_packet_index.json'),
        gold_or_accuracy_accessed=False, slurm_job_id=os.environ['SLURM_JOB_ID']))
    print(json.dumps(dict(total=len(expected), exact_native=len(reused), results_to_review=len(records), packets=len(packets))))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(MAIN));args=ap.parse_args();main(Path(args.root))
