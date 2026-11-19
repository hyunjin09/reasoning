"""Verify and reuse helpers, never technical-length solver completions."""
from copy import deepcopy
from pathlib import Path
from scripts.stage14d1_pilot.common import load, sha


def load_reusable_state(path, row, protocol_digest, helper_allowlist=None):
    path=Path(path)
    state=load(path)
    root=path.parent.parent
    if load(root/'environment.json')['runtime_sha256'] != protocol_digest:
        raise ValueError('Mixed helper protocol')
    if any(state[k] != row[k] for k in ('family_id','item_id')):
        raise ValueError('Wrong acquisition family')
    paths=[state['query_generation'],state['locator_generation']]
    paths += [v['generation_path'] for v in state['readouts'].values()]
    for ref in set(p for p in paths if p):
        p=Path(ref)
        if p.parent.parent != root:
            if not helper_allowlist or helper_allowlist.get(str(p)) != sha(p):
                raise ValueError('Helper receipt outside original attempt without frozen compatibility proof')
            if p.parent.name not in {row['item_id']+suffix for suffix in ('_query','_G_read','_Q_read','_QI_read')}:
                raise ValueError('Changed component cannot be reused from previous protocol')
        receipt=load(p.parent/'result.json');inp=load(p.parent/'input.json')
        if sha(p) != receipt['generation_sha256'] or sha(p.parent/'input.json') != receipt['input_sha256']:
            raise ValueError('Tampered helper receipt')
        if inp['kind'] not in ('query','locate','read') or inp['cap'] != 2048:
            raise ValueError('Not a final-protocol helper receipt')
        if any(inp[k] != row[k] for k in ('family_id','item_id','seed','prefix_sha256')):
            raise ValueError('Helper source identity mismatch')
    result=deepcopy(state)
    result.pop('continuation_paths',None)
    result.pop('logical_continuations',None)
    result['reused_acquisition_state']=str(path)
    result['reused_acquisition_sha256']=sha(path)
    return result
