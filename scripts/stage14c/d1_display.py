"""Compact presentation of immutable review packets; no inferred annotations."""
import sys
from scripts.stage14c.common import *

def main():
    packet=load(sys.argv[1]);sheetmap={r['family_id']:r for r in load(ROOT/'source/D1_source_sheets/manifest.json')['rows']}
    print('MODEL',packet['model'],'PASS',packet['review_pass'],'REMAINING',packet['remaining'])
    for i,r in enumerate(packet['rows']):
        t=r['task'];sm=sheetmap[t['family_id']]
        print('\nROW',i,'SOURCE_INDEX',sm['index'],'ITEM',t['item_id'],'SHEET',sm['sheet'],'CAP',r.get('cap_hit'),'CLOSED',r.get('native_think_closed'))
        print('QUESTION',t['prompt'].split('\n\n',1)[1])
        for j,a in enumerate(r['shared_source_unit_map']['atoms']):print('ATOM',j,a['text'],'UNITS',list(enumerate(a['subfact_keys'])))
        if r.get('excerpted'):print('RESPONSE_HEAD',r['final_body_head'],'\nRESPONSE_TAIL',r['final_body_tail'],'OMITTED',r['omitted_characters'])
        else:print('RESPONSE',r.get('final_body'))
        if 'first_review' in r:print('FIRST_REVIEW',json.dumps(r['first_review']['review'],ensure_ascii=False))
if __name__=='__main__':main()
