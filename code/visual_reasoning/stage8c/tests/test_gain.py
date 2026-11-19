import torch
from visual_reasoning.stage8c.gain import VisualGain


def test_gain_changes_only_projected_visual_component():
    # Nontrivial output matrix distinguishes post-projection residual gain
    # from modifying attention logits, softmax normalization or a whole head.
    projection = torch.nn.Linear(4, 3, bias=True, dtype=torch.float64)
    with torch.no_grad():
        projection.weight.copy_(torch.tensor([[1,2,3,4],[2,0,1,-1],[0,3,-2,4]],dtype=torch.float64))
        projection.bias.fill_(8.)
    cv = torch.tensor([[[.2,-.4,.5,.3]]],dtype=torch.float64)
    cn = torch.tensor([[[-.3,.1,1.,-.1]]],dtype=torch.float64)
    native = projection(cv+cn)
    ctx = VisualGain(None,visual=[0],prompt_length=2,detector=None,gain=1.5)
    ctx.contribution[19] = cv
    changed = ctx.projection_hook(19)(projection, (), native)
    assert torch.allclose(changed, projection(1.5*cv+cn))
    assert not ctx.contribution
    assert ctx.projection_hook(20)(projection, (), native) is native


def test_only_frozen_doses_and_nonprefill_schedules():
    import pytest
    for kwargs in [dict(gain=3.), dict(gain=1.5,policy='schedule',schedule=[0])]:
        with pytest.raises(ValueError):
            VisualGain(None,visual=[0],prompt_length=2,detector=None,**kwargs)
