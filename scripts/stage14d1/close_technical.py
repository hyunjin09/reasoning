"""Export a failed technical stage without manufacturing scientific outcomes."""
import csv
from scripts.stage14d1.common import *
from scripts.stage14d1.contracts import ARMS, parse_record as parse_v1
from scripts.stage14d1.contracts_v2 import parse_record as parse_compact

def jsonlines(path, records):
    with Path(path).open('x') as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False)+'\n')

def csvfile(path, records):
    with Path(path).open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

def close():
    stop = load(P/'audit/technical_gate_v3_stop.json')
    assert not stop['pass_gate'] and not stop['main_pilot_launched']
    resource = load(P/'audit/resource_accounting_final.json')
    assert all(r['status'].startswith(('COMPLETED', 'CANCELLED')) for r in resource['jobs'])
    families = {r['item_id']:r for r in rows(P/'inference/families.jsonl')}
    physical, queries, reads, continuations = [], [], [], []
    for version in ['technical', 'technical_v2', 'technical_v3']:
        root = P/'raw'/version
        parser = parse_v1 if version == 'technical' else parse_compact
        for path in sorted(root.glob('*/input.json')):
            inp = load(path)
            generated = path.parent/'generation.json'
            done = generated.exists()
            record = dict(version=version, phase='TECHNICAL_ONLY', request_id=inp['id'],
                          family_id=inp['family_id'], item_id=inp['id'].split('_')[0], kind=inp['kind'],
                          status='COMPLETED' if done else 'INTERRUPTED_RUNTIME_GATE',
                          input_path=str(path), input_sha256=sha(path),
                          generation_path=str(generated) if done else None,
                          generation_sha256=sha(generated) if done else None,
                          job_id=inp['job'], scientific_analysis_eligible=False)
            physical.append(record)
            if inp['kind']=='query':
                raw=load(generated)['raw_decoded_response'] if done else None
                queries.append(dict(record, query=parser(raw) if raw else None, address=None,
                                    address_status='NOT_ATTEMPTED',
                                    interpretation=('No committed query' if version=='technical' else
                                                    'Schema-order branch mismatch; not valid targeting evidence' if version=='technical_v2' else
                                                    'Interrupted before committed query; no targeting inference')))
            elif inp['kind']=='read':
                raw=load(generated)['raw_decoded_response'] if done else None
                reads.append(dict(record, readout=parser(raw) if raw else None,
                                  source_correctness=None, source_review_status='NOT_ADJUDICATED_RUNTIME_STOP',
                                  note='Physical technical read; not a paired scientific endpoint'))
        for path in sorted((P/'data'/f'{version}_state').glob('*.json')):
            state=load(path)
            for arm,cid in state['continuations'].items():
                gen=root/cid/'generation.json'
                continuations.append(dict(version=version, phase='TECHNICAL_ONLY',
                    item_id=state['item_id'], family_id=state['family_id'], arm=arm,
                    physical_request_id=cid, is_alias=cid != state['item_id']+'_'+arm,
                    generation_path=str(gen) if gen.exists() else None,
                    answer=None, correctness=None, status='NOT_SCORED_TECHNICAL_CAP256',
                    scientific_analysis_eligible=False))
    jsonlines(P/'data/physical_request_inventory.jsonl',physical)
    jsonlines(P/'data/query_and_roi_predictions.jsonl',queries)
    jsonlines(P/'data/paired_readouts.jsonl',reads)
    jsonlines(P/'data/paired_continuations.jsonl',continuations)
    source_records=rows(P/'data/selected_family_target_manifest.jsonl')
    target_rows=[];answer_rows=[]
    for r in source_records:
        target_rows.append(dict(family_id=r['family_id'], item_id=r['item_id'],
                               status='P2_NOT_RUN_RUNTIME_GATE', query_validity=None,
                               address_correctness=None, readout_correctness=None))
        for arm in ARMS:
            answer_rows.append(dict(family_id=r['family_id'], item_id=r['item_id'], arm=arm,
                status='P2_NOT_RUN_RUNTIME_GATE', native_correct=None, intervention_correct=None,
                wrong_to_correct=None, correct_to_wrong=None, scientific_GPU_hours=0))
    csvfile(P/'analysis/target_selection_and_readout.csv',target_rows)
    csvfile(P/'analysis/answer_transitions_and_costs.csv',answer_rows)
    save(P/'analysis/paired_bootstrap.json',dict(at=now(),status='NOT_ESTIMABLE_P2_NOT_RUN',
         independent_families_analyzed=0, families_frozen=72, planned_draws=4000,
         planned_seed=20261019, estimates=None, confidence_intervals=None,
         reason='Failed exact replay gate before scientific pilot; technical caps cannot supply answer outcomes'))
    save(P/'analysis/coverage.json',dict(at=now(),planned_families=72, planned_arm_slots=432,
         technical_families=8, main_families_run=0, main_arm_slots_run=0,
         physical_input_receipts=len(physical), completed_physical_calls=sum(r['status']=='COMPLETED' for r in physical),
         interrupted_requests=sum(r['status']!='COMPLETED' for r in physical),
         completed_queries_by_version={v:sum(q['version']==v and q['status']=='COMPLETED' for q in queries) for v in ['technical','technical_v2','technical_v3']},
         physical_LOCATE_calls=0, physical_reads=len(reads), logical_technical_continuation_slots=len(continuations),
         semantic_query_adjudications=0, source_readout_adjudications=0,
         original_source_images_inspected=8, answer_accuracy_computed=False,
         total_allocated_GPU_hours=resource['total_allocated_GPU_hours']))
    print('Exported technical evidence and explicit not-run scientific tables.')

if __name__=='__main__':
    close()
