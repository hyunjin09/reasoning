import numpy as np
from visual_reasoning.stage5a.analysis import holm,matched_reference,grouped_folds,classification_metrics,grouped_logistic


def test_holm_and_binary_metrics():
    assert np.allclose(holm([.03,.001,.2]),[.06,.003,.2])
    r=classification_metrics([0,1,0,1],np.array([[.9,.1],[.2,.8],[.8,.2],[.1,.9]]),2)
    assert r['balanced_accuracy']==r['macro_F1']==r['AUROC']==1.


def test_sparse_matching_never_relaxes_source_class_or_size():
    row={'source_class':'length','token_count':4,'reasoning_progress':.1,'sequence_length':100}
    refs=[{**row,'reasoning_progress':.9,'sequence_length':5000} for _ in range(8)]
    assert len(matched_reference(row,refs)[0])==8
    assert matched_reference(row,[{**r,'source_class':'angle'} for r in refs])==([],None)
    assert matched_reference(row,[{**r,'token_count':16} for r in refs])==([],None)


def test_template_and_base_folds_do_not_leak():
    rows=[{'template_family':str(i//4),'base_problem_id':str(i//2)} for i in range(40)]
    folds=grouped_folds(rows,['a' if i%4<2 else 'b' for i in range(40)])
    assert sorted(i for f in folds for i in f)==list(range(40))
    for f in folds:
        train=set(range(40))-set(f)
        for key in ('base_problem_id','template_family'):
            assert not {rows[i][key] for i in f}&{rows[i][key] for i in train}


def test_grouped_logistic_learns_without_test_imputation_or_template_leakage():
    rows=[{'base_problem_id':str(i),'template_family':str(i//2),'event_id':str(i),
           'signal':-2. if i%2 else 2.,'missing':None} for i in range(40)]
    result=grouped_logistic(rows,['a' if i%2 else 'b' for i in range(40)],['signal','missing'])
    assert result['status']=='scored' and result['metrics']['balanced_accuracy']==1.
    for fold in result['folds']:
        assert not set(fold['train_templates'])&set(fold['test_templates'])
        assert not set(fold['train_bases'])&set(fold['test_bases'])
        assert fold['train_imputation'][1]==0.
