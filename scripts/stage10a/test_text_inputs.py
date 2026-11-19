from types import SimpleNamespace
import pytest
import torch
from scripts.stage10a.runtime import text_inputs


def setup(monkeypatch,types):
    native_tensor=torch.tensor
    prepared={'input_ids':native_tensor([[1,2,3]]),'attention_mask':native_tensor([[1,1,1]]),
              'mm_token_type_ids':native_tensor([types])}
    processor=SimpleNamespace(apply_chat_template=lambda *a,**k:prepared,
                              tokenizer=SimpleNamespace(decode=lambda *a,**k:'<think>\n'))
    model=SimpleNamespace(config=SimpleNamespace(image_token_id=90,video_token_id=91))
    monkeypatch.setattr(torch,'tensor',lambda data,**kw:native_tensor(data,**dict(kw,device='cpu')))
    return processor,model


def test_native_processor_zero_modality_field_is_preserved(monkeypatch):
    p,m=setup(monkeypatch,[0,0,0]);prepared,meta=text_inputs(p,m,{'prompt':'Count.'},[4,5])
    assert prepared['input_ids'].tolist()==[[1,2,3,4,5]]
    assert prepared['mm_token_type_ids'].tolist()==[[0,0,0,0,0]]
    assert not meta['image_present'] and not meta['original_cache_copied']


def test_nontext_modality_metadata_cannot_enter_fresh_replay(monkeypatch):
    p,m=setup(monkeypatch,[0,1,0])
    with pytest.raises(AssertionError):text_inputs(p,m,{'prompt':'Count.'},[4,5])
