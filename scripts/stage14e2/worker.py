"""Matched reader-mode diagnostic. No final-answer scoring or source references."""
import hashlib
import traceback
from scripts.stage14e2.common import P, load, rows, save, sha, now
from scripts.stage14e2.engine import Engine
from scripts.stage14e2.contracts import parse_readout
from scripts.stage14d1.contracts import safe_payload


def run(path):
    m = load(path)
    for file, digest in load(m['seal'])['files'].items():
        assert sha(file) == digest, file
    families = {r['item_id']: safe_payload(r) for r in rows(m['families_path'])}
    definitions = load(m['tasks_path'])['rows']
    work = [t for t in definitions if t['item_id'] in m['families']]
    engine = Engine(m)
    try:
        repeats = []
        for rep in ['a', 'b']:
            repeats.append(engine.calls([dict(id=i+'_replay_'+rep, row=families[i],
                kind='solver', cap=64, condition='technical_native') for i in ['107', '33']], width=1))
        gates = [dict(item_id=i,
            same_tokens=repeats[0][i+'_replay_a']['generated_token_ids']==repeats[1][i+'_replay_b']['generated_token_ids'],
            same_input=repeats[0][i+'_replay_a']['prompt_token_ids']==repeats[1][i+'_replay_b']['prompt_token_ids'])
            for i in ['107', '33']]
        save(engine.root/'technical_gate.json', gates)
        assert all(r['same_tokens'] and r['same_input'] for r in gates)
        tasks, logical = [], []
        for t in work:
            row = families[t['item_id']]
            if t['status'] == 'ABSENT_ORIGINAL_TARGET':
                logical.append(dict(t, generation_path=None, family_id=row['family_id']))
                continue
            assert t['cap'] == 8192 and t['helper_mode'] in ['compact', 'thinking']
            assert t['images'] == ([] if t['condition']=='T_N' else [row['image']])
            tasks.append(dict(id=t['item_id']+'_'+t['condition'], row=row, kind='helper',
                cap=t['cap'], helper_mode=t['helper_mode'], prompt=t['prompt'],
                images=t['images'], condition=t['condition'], oracle=t['diagnostic_oracle_target']))
            logical.append(dict(t, family_id=row['family_id'],
                generation_path=str(engine.root/(t['item_id']+'_'+t['condition'])/'generation.json')))
        # Every family/condition is predetermined; no output-dependent ordering.
        tasks.sort(key=lambda t: hashlib.sha256(('stage14e2-read-order-v1|'+t['id']).encode()).hexdigest())
        save(engine.root/'read_execution_manifest.json', dict(at=now(), rows=logical,
            physical_count=len(tasks), solver_width=1, frozen_before_readout=True))
        generated = engine.calls(tasks, width=1)
        parsed = []
        for t in tasks:
            g = generated[t['id']]
            parsed.append(dict(item_id=t['row']['item_id'], condition=t['condition'],
                generation_path=g['generation_path'], generation_sha256=sha(g['generation_path']),
                **parse_readout(g['raw_decoded_response'], t['helper_mode'], g['cap_hit'])))
        save(engine.root/'parsed_readouts.json', dict(at=now(), rows=parsed))
        save(engine.root/'result.json', dict(at=now(), status='COMPLETED',
            families=len(m['families']), logical_readouts=len(logical), physical_readouts=len(tasks),
            physical_calls=engine.count))
    except BaseException as exc:
        save(engine.root/'failure.json', dict(at=now(), error=repr(exc),
            traceback=traceback.format_exc(), completed=engine.count))
        raise
    finally:
        engine.budget_check()
