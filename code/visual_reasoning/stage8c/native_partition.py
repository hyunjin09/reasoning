"""BF16 source split retaining the complete native head/KV tensor layout."""
import torch


def full_axis_parts(weights, values, visual):
    if weights.dtype != values.dtype or weights.ndim != 2 or values.ndim != 3:
        raise ValueError('Expected matching native dtypes and [head,KV]/[head,KV,dim]')
    if weights.shape != values.shape[:2]:
        raise ValueError('Head/KV coordinates disagree')
    mask=torch.zeros(weights.shape[-1],dtype=torch.bool,device=weights.device)
    mask[list(visual)]=True
    vweights=weights.masked_fill(~mask,0)
    nweights=weights.masked_fill(mask,0)
    return (torch.matmul(vweights.unsqueeze(1),values).squeeze(1),
            torch.matmul(nweights.unsqueeze(1),values).squeeze(1))
