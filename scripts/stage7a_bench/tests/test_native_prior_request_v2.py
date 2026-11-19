import pytest
import scripts.stage7a_bench.prior_controls_v2 as module


def test_fixed_prefix_bank_does_not_implicitly_request_long_native_generations(monkeypatch):
    monkeypatch.setattr(module, 'load_prior_controls', lambda entry: pytest.fail('Unrequested bank loaded'))
    assert module.requested_native_banks([dict(id='e', source_annotation={})]) == {}


def test_pre_score_request_selects_exact_bank(monkeypatch):
    bank = ({'fixed_'+c:{} for c in ('mask', 'unrelated', 'no_image')}, {'review_sha256': 'verified'})
    monkeypatch.setattr(module, 'load_prior_controls', lambda entry: bank)
    e = dict(id='e', source_annotation=dict(fresh_native_prior_control_request=dict(
        required=True, causal_or_passive_scores_used=False,
        reason='Reviewed unsatisfied visual demand requires matched native convergence.')))
    assert module.requested_native_banks([e]) == {'e':bank}


@pytest.mark.parametrize('proposal', [dict(required=False), dict(required=True, reason=''),
    dict(required=True, causal_or_passive_scores_used=True, reason='Selected after scores')])
def test_unreviewed_or_post_score_native_request_rejected(proposal):
    with pytest.raises(ValueError):
        module.requested_native_banks([dict(id='e', source_annotation=dict(fresh_native_prior_control_request=proposal))])
