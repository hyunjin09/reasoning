from copy import deepcopy
import json

import pytest

from scripts.stage7a_bench import causal_run_v2 as runner
from scripts.stage7a.common import sha


def install(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(runner, 'OUT', tmp_path / 'outputs/stage7a_bench_v2')
    folder = runner.OUT / 'causal_pilot/raw/mechanics'
    folder.mkdir(parents=True)
    entry = dict(id='selected', native_input={'prompt_token_count':12},
        event={'history_before_ed_token_ids':[1]*8}, source_groups={'T':[1], 'X':[2], 'G':[1,2]},
        w2_sources=['T','X','G'], w8_sources=['T','X'])
    expected_arms = ['N','T_W2','X_W2','G_W2','T_W8','X_W8']
    checks = dict(canonical_native_exact=True, unhooked_exact=True,
        noop_exact=True, suppression_repeat_exact=True, all_finite=True)
    checks.update({key+'_canonical_exact':True for key in expected_arms[1:]})
    result = dict(id='selected', complete=True, source_assay_mechanics=True,
        passive_features_collected=False, checks=checks,
        arms={key:{'finite':True} for key in expected_arms}, controls={})
    prefix = dict(passed=True, id='selected', actual_gpu_validation=True,
        model_layers=36, model_attention_heads=32, model_hidden_size=2560,
        parameter_dtype='torch.bfloat16', all_layer_kv_exact=True,
        logits_exact=True, rope_exact=True, prepared_input_unchanged=True)
    refs = {}
    for key, value in [('prefix',prefix),('event',result),('distributions',{'fake':'file-integrity fixture'})]:
        p = folder / (key+'.json');p.write_text(json.dumps(value))
        refs[key] = dict(path=str(p.relative_to(tmp_path)),sha256=sha(p))
    signature = {'pilot':{'path':'frozen.json','sha256':'frozen'},'dependencies':{'worker':'hash'}}
    cert = dict(status='PASS_ACTUAL_4B_CAUSAL_MECHANICS',execution_signature=signature,
        mechanics_entry_id='selected', artifacts=refs)
    return cert, signature, entry, folder


def test_certificate_requires_actual_gpu_prefix_and_all_source_mechanics(tmp_path, monkeypatch):
    cert, signature, entry, _ = install(tmp_path, monkeypatch)
    assert runner.validate_mechanics(cert, signature, [entry]) == 'selected'


@pytest.mark.parametrize('fault', ['pilot', 'prefix_hash', 'cpu', 'head_count',
    'missing_w8', 'failed_check', 'no_mechanics', 'changed_distribution', 'not_selected'])
def test_invalid_or_inapplicable_mechanics_cannot_unlock_scoring(tmp_path, monkeypatch, fault):
    cert, signature, entry, folder = install(tmp_path, monkeypatch)
    if fault == 'pilot': signature = {'pilot':'changed'}
    if fault == 'prefix_hash': (folder/'prefix.json').write_text('{}')
    if fault == 'changed_distribution': (folder/'distributions.json').write_text('{}')
    if fault == 'not_selected': entry['id']='other'
    if fault in ('cpu','head_count'):
        p=folder/'prefix.json'; value=json.loads(p.read_text())
        value['actual_gpu_validation' if fault=='cpu' else 'model_attention_heads']=False if fault=='cpu' else 4
        p.write_text(json.dumps(value));cert['artifacts']['prefix']['sha256']=sha(p)
    if fault in ('missing_w8','failed_check','no_mechanics'):
        p=folder/'event.json';value=json.loads(p.read_text())
        if fault=='missing_w8':del value['arms']['X_W8']
        if fault=='failed_check':value['checks']['noop_exact']=False
        if fault=='no_mechanics':value['source_assay_mechanics']=False
        p.write_text(json.dumps(value));cert['artifacts']['event']['sha256']=sha(p)
    with pytest.raises(ValueError): runner.validate_mechanics(cert, signature, [entry])


def test_mechanics_choice_uses_only_frozen_input_cost_and_identity():
    a=dict(id='a',native_input={'prompt_token_count':50},event={'history_before_ed_token_ids':[1]*20})
    b=dict(id='b',native_input={'prompt_token_count':10},event={'history_before_ed_token_ids':[1]*8})
    original=deepcopy([a,b])
    assert runner.mechanics_entry([a,b])['id']=='b'
    assert [a,b]==original
