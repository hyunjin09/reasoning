import pytest
from scripts.stage14c.final_validation import validate_scope, validate_resources


def task(model, condition, family='f'):
    return dict(task_id=f'{model}_{condition}_{family}', model_key=model,
                condition=condition, family_id=family)


def test_scope_rejects_duplicate_and_unapproved_equal_evidence():
    native={'f', 'g'}; eligible={'f'}
    rows=[task(m,c,f) for f in native for m in 'IT'
          for c in (['native','equal_evidence'] if f in eligible else ['native'])]
    validate_scope(rows,native,eligible)
    with pytest.raises(AssertionError):validate_scope(rows+[rows[0]],native,eligible)
    with pytest.raises(AssertionError):
        validate_scope(rows+[task('I','equal_evidence','g')],native,eligible)
    with pytest.raises(AssertionError):validate_scope(rows[:-1],native,eligible)


def test_resources_require_released_gpus_known_cost_and_bounded_d1():
    record=dict(gpu_hours_observed_or_proxy=20,unknown_duration_jobs=[],
                jobs=[dict(mode='main',gpus=1,active=False,gpu_hours=15),
                      dict(mode='D1',gpus=1,active=False,gpu_hours=5)])
    validate_resources(record)
    for changed in [dict(gpu_hours_observed_or_proxy=121),
                    dict(unknown_duration_jobs=['1']),
                    dict(jobs=[dict(mode='D1',gpus=1,active=False,gpu_hours=13)]),
                    dict(jobs=[dict(mode='main',gpus=1,active=True,gpu_hours=1)])]:
        with pytest.raises(AssertionError):validate_resources(dict(record,**changed))
