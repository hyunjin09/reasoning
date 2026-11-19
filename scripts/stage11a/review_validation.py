"""Validate manually assigned semantic labels without deriving them."""

def _facts(row,packet,text,label_key,allowed):
    assert row['packet_id']==packet['packet_id']
    ids=[f['fact_id'] for f in row['facts']]
    assert len(ids)==len(set(ids))==len(packet['facts'])
    assert set(ids)=={f['fact_id'] for f in packet['facts']}
    for f in row['facts']:
        assert f[label_key] in allowed and f['reason'].strip()
        for q in f.get('quotes',[])+f.get('correct_quotes',[]):assert q and q in text

def validate_native(row,packet):
    assert row['coverage_complete'] and row['state'] in ['N0','N1','N2','N3','N4','N5'] and row['reason'].strip()
    _facts(row,packet,packet['reasoning_text'],'status',{'CORRECT','WRONG','MISSING','CONFLICTING','UNCERTAIN'})
    for q in row.get('evidence_quotes',[]):assert q and q in packet['reasoning_text']
    for key in ['first_evidence_token','first_sufficient_token']:
        if row.get(key) is not None:assert 0<=row[key]<=packet['reasoning_tokens']

def validate_probe(row,packet):
    _facts(row,packet,packet['text'],'label',{'CORRECT','WRONG','MISSING','AMBIGUOUS'})
