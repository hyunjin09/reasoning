"""Source-only identity extraction, conservative aliases and deterministic ordering."""
import hashlib

def identify(data,item_family,inherited_context=False):
    found=set()
    if isinstance(data,dict):
        tags=[data.get(k) for k in ['dataset','benchmark','source_dataset','protocol_id','image','image_path','original_image','image_source']]
        context=inherited_context or any(isinstance(v,str) and 'mathvision' in v.lower() for v in tags)
        item=str(data.get('item_id',data.get('source_item_id','')))
        family=data.get('family_id',data.get('inherited_family_id'))
        matched=item in item_family and family is not None and family==item_family[item]
        if item in item_family and (context or matched):found.add(item)
        for value in data.values():
            if isinstance(value,(dict,list)):found.update(identify(value,item_family,context))
    elif isinstance(data,list):
        for value in data:
            if isinstance(value,(dict,list)):found.update(identify(value,item_family,inherited_context))
    return found

def components(ids,groups):
    parent={i:i for i in ids}
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for group in groups:
        members=sorted(set(group)&parent.keys())
        for member in members[1:]:parent[root(member)]=root(members[0])
    return {i:root(i) for i in ids}

def order(family,purpose):return hashlib.sha256(f'stage12xs-{purpose}-v1|{family}'.encode()).hexdigest()

def choose(rows,n=96,reserve=32):
    metadata=[{k:r[k] for k in ['item_id','family_id','answer_type','level','subject']} for r in rows]
    assert len({r['family_id'] for r in metadata})==len(metadata)
    ordered=sorted(metadata,key=lambda r:(order(r['family_id'],'source'),r['family_id']))
    assert len(ordered)>=n+reserve
    return ([r['item_id'] for r in ordered[:n]],[r['item_id'] for r in ordered[n:n+reserve]])
