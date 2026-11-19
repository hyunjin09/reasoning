"""Direct FP32 execution for Stage8C v3; no transfer or validation cohort."""
from collections import Counter

import torch
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

from visual_reasoning.stage0.modeling import ATTENTION_IMPLEMENTATIONS
from .gain import VisualGain


def load_fp32_runtime(checkpoint, device):
    # FP32 tensor storage alone does not prevent TF32 matrix multiplication.
    torch.set_float32_matmul_precision('highest')
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    processor = AutoProcessor.from_pretrained(checkpoint, local_files_only=True)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        checkpoint, dtype=torch.float32,
        attn_implementation=ATTENTION_IMPLEMENTATIONS,
        local_files_only=True, low_cpu_mem_usage=True,
    ).to(device).eval()
    if any(p.dtype != torch.float32 for p in model.parameters() if p.is_floating_point()):
        raise RuntimeError('Full FP32 model required; no precision fallback')
    return processor, model


def precision_inventory(model):
    return dict(
        parameter_elements_by_dtype=dict(Counter({str(dtype): sum(
            p.numel() for p in model.parameters() if p.dtype == dtype
        ) for dtype in {p.dtype for p in model.parameters()}})),
        floating_buffer_dtypes=sorted({str(b.dtype) for b in model.buffers() if b.is_floating_point()}),
        matmul_precision=torch.get_float32_matmul_precision(),
        cuda_matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,
        cudnn_allow_tf32=torch.backends.cudnn.allow_tf32,
        autocast_enabled=torch.is_autocast_enabled(),
        detector_policy='Frozen Stage8A classifier and threshold; no FP32 transfer certification',
        detector_and_saved_scores='Inherited NumPy/sklearn evaluation may use float64; model path remains FP32',
    )


class FP32VisualGain(VisualGain):
    """Same gain implementation with in-run precision receipts, no audit replay."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.precision_observations = {}

    def attention(self, module, query, key, value, attention_mask, scaling, dropout=0., **kwargs):
        result = super().attention(module, query, key, value, attention_mask,
                                   scaling=scaling, dropout=dropout, **kwargs)
        layer = getattr(module, 'layer_idx', None)
        if layer is not None:
            phase = 'prefill' if query.shape[2] > 1 else self.mode
            record = dict(query=str(query.dtype), key=str(key.dtype), value=str(value.dtype),
                          probabilities=str(result[1].dtype), output=str(result[0].dtype))
            self.precision_observations.setdefault(f'{phase}/layer{layer}', record)
            if any(dtype != 'torch.float32' for dtype in record.values()):
                raise RuntimeError('Non-FP32 native attention encountered; refusing precision fallback')
        return result
