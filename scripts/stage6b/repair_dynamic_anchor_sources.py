"""Pre-scoring coverage audit: every latency anchor needs its own demanded source."""
from scripts.stage6b.common import OUT,read_jsonl,sha,write_json,write_jsonl


def main():
    old=OUT/'c1_dynamics/exact_anchor_manifest.jsonl';rows=read_jsonl(old);changed=[]
    for e in rows:
        source=e['roles']['demanded']
        if source not in e['w2_sources']:
            assert e['source_groups'][source]
            changed.append({'id':e['id'],'added_current_demanded_source':source,'reason':'Adjacent latency window extends into another reviewed source demand.'})
            e['w2_sources']=sorted(set(e['w2_sources'])|{source})
    new=OUT/'c1_dynamics/exact_anchor_manifest_v2.jsonl';write_jsonl(new,rows,freeze=True)
    write_json(OUT/'config/dynamic_anchor_sources_v2.json',{'mechanical_readout_coverage_repair_before_scoring':True,
        'original_manifest_sha256':sha(old),'manifest_sha256':sha(new),'changes':changed,
        'selection_or_splits_changed':False,'pairs_changed':False,'historical_v1_never_scored':True},freeze=True)
    print('Preserved78anchors and allpairs; added current-demanded source coverage to',len(changed),'latency anchors.')


if __name__=='__main__':main()
