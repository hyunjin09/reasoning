"""Reconstruct the exact BF16 pixel execution inputs recorded by native v8/v9."""
import torch
from scripts.stage7a_bench.document_inputs_v2 import prepare_document as raw_document
from scripts.stage7a_bench.document_controls_v11 import prepare_control_condition as raw_control


def execution_pixels(batch,meta):
    if batch['pixel_values'].dtype not in (torch.float32,torch.bfloat16):
        raise ValueError('Unexpected native document pixel dtype')
    batch['pixel_values']=batch['pixel_values'].to(torch.bfloat16)
    meta.update(execution_pixel_values_dtype=str(batch['pixel_values'].dtype),
        execution_prefill_chunk_size=2048,execution_query_chunk_size=64,
        execution_pixel_cast='Exact canonical vision-input cast moved before generation; image content and preprocessing unchanged')
    return batch,meta


def prepare_document(processor,row,device):
    return execution_pixels(*raw_document(processor,row,device))


def prepare_control_condition(processor,row,device):
    batch,meta=raw_control(processor,row,device)
    return execution_pixels(batch,meta) if row.get('document_path') else (batch,meta)
