"""Read-only compact review display; explicit excerpts for capped responses."""
import sys
from scripts.stage14c.common import *

p=load(sys.argv[1])
start=int(sys.argv[2]) if len(sys.argv)>2 else 0
stop=int(sys.argv[3]) if len(sys.argv)>3 else len(p['rows'])
for i in range(start,min(stop,len(p['rows']))):
    r=p['rows'][i]
    print('\nROW',i,'ITEM',r['task']['item_id'],'CAP',r.get('cap_hit'))
    for j,a in enumerate(r['shared_source_unit_map']['atoms']):
        print('SOURCE',j,a['text'],'UNITS',list(enumerate(a['subfact_keys'])))
    if r.get('excerpted'):
        print('EXCERPT_HEAD',r['final_body_head'][:2000],'EXCERPT_TAIL',r['final_body_tail'][-1500:])
    else:print('RESPONSE',r.get('final_body'))
    if 'first_review' in r:
        v=r['first_review']['review']
        print('REVIEW',v['status'],[(a['exact'],a['recovered_units']) for a in v['atoms']],v['reason'])
        print('OTHER',[(c['classification'],c['text'],c['binding']) for c in v['claims'] if c['classification']!='required'])
