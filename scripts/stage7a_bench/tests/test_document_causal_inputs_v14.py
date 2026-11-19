import pytest
import torch
from scripts.stage7a_bench.document_causal_inputs_v14 import execution_pixels


def test_native_execution_cast_and_record_are_exact():
    x=torch.tensor([1.23456,-2.87654],dtype=torch.float32);ids=torch.tensor([[4,5]])
    data={'pixel_values':x,'input_ids':ids};meta={'prompt':'p'}
    batch,actual=execution_pixels(data,meta)
    assert torch.equal(batch['pixel_values'],x.to(torch.bfloat16))
    assert batch['input_ids'] is ids
    assert actual==dict(prompt='p',execution_pixel_values_dtype='torch.bfloat16',execution_prefill_chunk_size=2048,execution_query_chunk_size=64,execution_pixel_cast='Exact canonical vision-input cast moved before generation; image content and preprocessing unchanged')


def test_cast_rejects_unexpected_precision_instead_of_silently_accepting():
    with pytest.raises(ValueError):execution_pixels({'pixel_values':torch.ones(1,dtype=torch.float64)},{})
