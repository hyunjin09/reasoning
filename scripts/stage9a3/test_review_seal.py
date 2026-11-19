import json
import pytest
from scripts.stage9a3 import postprocess
from scripts.stage9a3.prepare import save,sha


def fixture_packet(tmp_path,monkeypatch,text):
    monkeypatch.setattr(postprocess,'ROOT',tmp_path)
    gen=tmp_path/'generation.json';receipt=tmp_path/'result.json'
    save(gen,dict(text=text,tokens=12,normal_eos=True,at_length_cap=False))
    save(receipt,dict(generation_sha256=sha(gen)))
    save(tmp_path/'audit/qwen25_full_review.json',dict(rows=[]))
    save(tmp_path/'audit/qwen25_grid_primary_manifest.json',dict(rows=[dict(query_id='q',policy_id='p',
        execution='run',generation_path=str(gen),result_path=str(receipt))]))
    postprocess.packet('qwen25')
    return json.loads((tmp_path/'audit/qwen25_grid_primary_review_packet.json').read_text())


def test_packet_and_seal_need_no_answer_keys(tmp_path,monkeypatch):
    p=fixture_packet(tmp_path,monkeypatch,'Intermediate steps. {C: 1}')
    assert p['rows'][0]['automatic_option']=='C' and 'answer' not in p['rows'][0]
    postprocess.seal('qwen25')
    r=json.loads((tmp_path/'audit/qwen25_grid_primary_review.json').read_text())
    assert r['sealed'] and r['rows'][0]['option']=='C'


def test_missing_manual_review_blocks_seal(tmp_path,monkeypatch):
    fixture_packet(tmp_path,monkeypatch,'Count is unclear. {A} or {B}')
    with pytest.raises(FileNotFoundError):postprocess.seal('qwen25')
