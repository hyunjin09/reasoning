import torch
from visual_reasoning.stage5a.passive import routing_summary
from visual_reasoning.stage3c3.metrics import summarize_routing_state


def test_grouped_kv_and_optional_regions_reconstruct():
    q=torch.tensor([[[[1.,0.]],[[0.,1.]]]])
    k=torch.tensor([[[[1.,0.],[0.,1.],[1.,1.]]]])
    v=torch.tensor([[[[2.,0.],[0.,4.],[2.,2.]]]])
    alpha=torch.tensor([[[[.2,.3,.5]],[[.1,.6,.3]]]])
    wo=torch.eye(4)
    r=routing_summary(q,k,v,alpha,wo,1.,2,{'T':[1],'sink':[0],'visual':[1,2]})
    assert set(r['groups'])=={'T','sink','visual'}
    assert abs(r['groups']['T']['mean_attention_mass']-.45)<1e-6
    assert r['per_head'][0]['groups']['T']['alpha_v_vector']==[0.,float(torch.tensor(1.2))]
    assert abs(r['groups']['T']['mean_alpha_v_norm']-1.8)<1e-6
    assert abs(r['groups']['T']['mean_qk_cosine']-.5)<1e-6
    assert r['all_values_finite']


def test_overlapping_aliases_are_explicit_and_do_not_change_inputs():
    torch.manual_seed(7);q=torch.randn(1,2,1,4);k=torch.randn(1,1,5,4);v=torch.randn_like(k)
    a=torch.softmax(torch.randn(1,2,1,5),-1);wo=torch.randn(8,8)
    originals=[t.clone() for t in (q,k,v,a)]
    r=routing_summary(q,k,v,a,wo,.5,2,{'T':[1,2],'M':[1,2],'sink':[0]})
    assert r['groups']['T']==r['groups']['M']
    assert all(torch.equal(t,b) for t,b in zip((q,k,v,a),originals))


def test_historical_readout_definitions_are_preserved():
    torch.manual_seed(11);q=torch.randn(1,2,1,4);k=torch.randn(1,1,5,4);v=torch.randn_like(k)
    a=torch.softmax(torch.randn(1,2,1,5),-1);wo=torch.randn(8,8);groups={'T':[1],'M':[2],'I':[3],'sink':[0]}
    fresh=routing_summary(q,k,v,a,wo,.5,2,groups)
    old=summarize_routing_state({'post_rope_query':q[:,:,0],'key':k,'value':v,'attention':a[:,:,0],
        'wo_weight':wo,'scaling':.5,'num_key_value_groups':2},groups=groups,selected_heads=[0,1])
    for name,g in fresh['groups'].items():
        for key,x in g.items():assert abs(x-old['groups'][name][key])<1e-6
