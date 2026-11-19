"""Source-only SAVA query/address packets, deliberately excluding readouts and solver answers."""
import argparse
from scripts.stage14d1.common import *
def prepare(version):
 records={r['item_id']:r for r in rows(P/'inference/families.jsonl')};dest=P/'analysis/source_packets'/version
 for p in sorted((P/'data'/f'{version}_state').glob('*.json')):
  s=load(p);r=records[s['item_id']];out=dest/(s['item_id']+'.json')
  if out.exists():continue
  save(out,dict(item_id=r['item_id'],family_id=r['family_id'],image=r['image'],image_sha256=r['image_sha256'],question=r['question'],prefix=r['prefix'],prefix_sha256=r['prefix_sha256'],query=s['query'],query_contract_valid=s['query_contract_valid'],address=s['address'],address_contract_valid=s['address_contract_valid'],model_values_visible=False,final_answers_visible=False,oracle_values_visible=False,source_state_path=str(p),source_state_sha256=sha(p)))
 print('Source-only packets',len(list(dest.glob('*.json'))))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('version');prepare(a.parse_args().version)
