import numpy as np
import pytest
from visual_reasoning.stage6b.geometry import fit_pca,project,path_metrics


def test_confirmation_cannot_enter_fit_and_projection_keeps_frozen_fit():
    rows=[{'split':'discovery','base_id':'a','x':0.,'y':0.},
          {'split':'discovery','base_id':'a','x':0.,'y':0.},
          {'split':'discovery','base_id':'b','x':2.,'y':2.}]
    model=fit_pca(rows,['x','y'])
    assert model['mean']==[1.,1.]
    before=model.copy();z,p=project([{'x':100.,'y':-20.}],model)
    assert model==before and z.shape==p.shape==(1,2)
    with pytest.raises(ValueError):fit_pca(rows+[{'split':'confirmation','base_id':'c','x':8.,'y':8.}],['x','y'])


def test_path_geometry_is_reported_outside_projection_and_never_labels_failure():
    result=path_metrics(np.array([[0.,0.],[1.,0.],[1.,1.]]))
    assert result['path_length']==2.
    assert abs(result['tortuosity']-np.sqrt(2))<1e-10
    assert not any('failure' in key for key in result)
