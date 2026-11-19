"""CPU independent checks of actual helper inputs, coordinate and arm transport."""
import argparse
import hashlib
from pathlib import Path
from PIL import Image
from scripts.stage14d1_pilot.common import *
from scripts.stage14d1_pilot.interface_v6 import build_catalog,compile_query,validate_query,normalize_address
from scripts.stage14d1_pilot.execution import continuation_plan,read_plan
from scripts.stage14d1.contracts_v3 import parse_record


def main(attempt):
    root=P/'raw'/attempt
    families={r['item_id']:r for r in rows(P/'inference/families.jsonl')}
    checks=[]
    for path in sorted((root/'states').glob('*.json')):
        s=load(path);row=families[s['item_id']];item=row['item_id']
        qg=load(s['query_generation']);q=parse_record(qg['raw_decoded_response'])
        assert q==s['query']
        catalog=build_catalog(row['question'],row['prefix']);ok,reason=validate_query(q,catalog)
        assert ok==s['query_valid'] and reason==s['query_reason']
        assert s['compiled_query']==(compile_query(q,catalog) if ok else None)
        if s['locator_generation']:
            address_raw=parse_record(load(s['locator_generation'])['raw_decoded_response'])
            assert address_raw==s['raw_address']
            try:normalized=normalize_address(address_raw)
            except ValueError:normalized=None
            assert normalized==s['address']
        for view,transform in zip(s['views']['paths'][1:],s['views']['transforms']):
            with Image.open(row['image']) as image,Image.open(view) as crop:
                expected=image.convert('RGB').crop(transform['pixel_box'])
                assert expected.size==crop.size and expected.tobytes()==crop.tobytes()
        intended,aliases=read_plan(row['image'],ok and q['status']=='QUERY',s['address_valid'],s['views']['paths'])
        assert s['read_aliases']==aliases
        for arm,images in intended.items():
            meta=s['readouts'][arm];inp=load(Path(meta['generation_path']).parent/'input.json')
            assert inp['images']==images and inp['kind']=='read' and inp['cap']==2048
        physical,logical=continuation_plan(item,{a:m['value'] for a,m in s['readouts'].items()})
        assert logical==s['logical_continuations']
        for arm,rid in logical.items():
            inp=load(Path(s['continuation_paths'][arm]).parent/'input.json')
            assert inp['prompt']==row['original_chat_prompt']+row['prefix']+physical[rid]
            assert inp['kind']=='solver' and inp['seed']==row['seed'] and inp['cap']==256
            assert inp['pixels']==row['original_image_pixels'] and inp['sizes']==row['original_image_sizes']
        checks.append(dict(item_id=item,expected_transport=True,query_reference_contract=ok,
                           source_relevance_not_certified=True,actual_read_arms=list(intended),read_aliases=aliases,
                           physical_solver_calls=len(physical),logical_slots=len(logical),
                           crop_count=len(s['views']['paths'])-1))
    assert len(checks)==8
    save(P/'audit'/f'{attempt}_transport.json',dict(at=now(),checks=checks,all_transport_pass=True,
        source_semantic_accuracy_is_separate=True,no_oracle_runtime=True))
    print('8family arm, coordinate, image, exactsuffix transports PASS')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('attempt');main(p.parse_args().attempt)
