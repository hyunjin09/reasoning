"""Export/verify Git-sized derived results; no model, scheduler or dataset access.

The CSV shards reproduce the original table byte-for-byte. Compact per-call
trace features replace the bulky match cache. Image-denial quotes and contexts
remain in text_reliance_screen_candidates.csv; other raw text stays archived.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/thinking_math_failure_audit/v1'
SHARED=BASE/'shared'
LIMIT=3_500_000


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_same_or_new(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        assert path.read_bytes()==data,('preserve differing export',str(path))
    else:path.write_bytes(data)


def csv_parts(source,destination,limit=LIMIT):
    def encoded(row):
        buffer=io.StringIO(newline='');csv.writer(buffer).writerow(row)
        return buffer.getvalue().encode()
    parts=[]
    with Path(source).open(newline='') as f:
        reader=csv.reader(f);header=encoded(next(reader));data=bytearray(header)
        restored=hashlib.sha256(header)
        for row in reader:
            value=encoded(row);restored.update(value)
            assert len(header)+len(value)<=limit,'single CSV record too large'
            if len(data)+len(value)>limit:
                path=Path(destination)/f'part-{len(parts)+1:03d}.csv'
                write_same_or_new(path,bytes(data));parts.append(path);data=bytearray(header)
            data.extend(value)
        path=Path(destination)/f'part-{len(parts)+1:03d}.csv'
        write_same_or_new(path,bytes(data));parts.append(path)
    assert restored.hexdigest()==digest(source),'CSV roundtrip must preserve original bytes'
    return parts


def trace_features(record):
    # These paths/hashes are already in the outcome table; join by task_id.
    duplicate={'lexical_flags','generation_path','generation_sha256','input_path','result_path'}
    exported={k:v for k,v in record.items() if k not in duplicate}
    for flag,matches in record['lexical_flags'].items():
        exported[flag+'_count']=len(matches)
    exported['strict_named_image_denial_count']=sum(
        m['quote'].lower().startswith(('i ','we ')) and
        any(noun in m['quote'].lower() for noun in ['image','diagram','picture','figure'])
        for m in record['lexical_flags']['image_unavailable_statement'])
    return exported


def json_parts(records,destination):
    parts=[];data=bytearray();n=0
    for record in records:
        value=(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n').encode()
        assert len(value)<=LIMIT,'single JSONL record too large'
        if data and len(data)+len(value)>LIMIT:
            path=destination/f'part-{len(parts)+1:03d}.jsonl'
            write_same_or_new(path,bytes(data));parts.append(path);data=bytearray()
        data.extend(value);n+=1
    if data:
        path=destination/f'part-{len(parts)+1:03d}.jsonl'
        write_same_or_new(path,bytes(data));parts.append(path)
    return parts,n


def verify():
    manifest=json.loads((SHARED/'manifest.json').read_text())
    for entry in manifest['files']:
        path=ROOT/entry['path']
        assert path.is_file() and digest(path)==entry['sha256'],entry['path']
        assert path.stat().st_size==entry['bytes']<5*1024*1024
    records=[];combined=hashlib.sha256()
    for i,path in enumerate(sorted((SHARED/'all_thinking_records').glob('*.csv'))):
        data=path.read_bytes();combined.update(data if i==0 else data.split(b'\r\n',1)[1])
        with path.open(newline='') as f:records.extend(csv.DictReader(f))
    assert combined.hexdigest()==manifest['original_csv_sha256']
    assert len(records)==13568 and len({r['task_id'] for r in records})==13568
    primary=[r for r in records if r['replicate']=='0' and r['condition']!='evidence']
    counts=collections.Counter(r['status'] for r in primary)
    assert len(primary)==7768 and counts['WRONG']==2303 and counts['UNSCORABLE']==26
    with (SHARED/'trace_features.csv').open(newline='') as f:traces=list(csv.DictReader(f))
    assert {r['task_id'] for r in traces}=={r['task_id'] for r in records}
    sources=[json.loads(line) for p in sorted((SHARED/'source_metadata').glob('*.jsonl')) for line in p.open()]
    keys={r['metadata_key'] for r in sources}
    assert len(keys)==8768
    assert all(r['identity']+'::'+r['condition'] in keys for r in records)
    print(f"Published results verified: {len(records):,} outcomes, {len(traces):,} trace feature rows, {len(keys):,} source/condition records; {len(manifest['files'])} files.")


def export():
    parts=csv_parts(BASE/'all_thinking_records.csv',SHARED/'all_thinking_records')
    with (BASE/'trace_screens.jsonl').open() as f:
        traces=[trace_features(json.loads(line)) for line in f]
    assert len(traces)==13568
    buffer=io.StringIO(newline='');writer=csv.DictWriter(buffer,fieldnames=list(traces[0]));writer.writeheader();writer.writerows(traces)
    feature_path=SHARED/'trace_features.csv';write_same_or_new(feature_path,buffer.getvalue().encode());parts.append(feature_path)
    metadata={}
    for name in ['scored_outputs.jsonl','confirmatory_scored_outputs.jsonl']:
        with (ROOT/'outputs/stage14b/scoring'/name).open() as f:
            for line in f:
                r=json.loads(line)
                if r['model']!='T':continue
                key=r['identity']+'::'+r['condition'];value=r['source_metadata']
                if key in metadata:assert metadata[key]==value,key
                metadata[key]=value
    sourceparts,n=json_parts((dict(metadata_key=k,source_metadata=v) for k,v in sorted(metadata.items())),SHARED/'source_metadata')
    assert n==8768;parts+=sourceparts
    omitted={'all_thinking_records.csv','trace_screens.jsonl','failure_inventory.jsonl','report.md','casebook.md',
             'image_denial_input_receipt_check.json'}
    small=[p for p in BASE.iterdir() if p.is_file() and p.name not in omitted and p.suffix in {'.csv','.json'}]
    files=parts+small+sorted((BASE/'case_traces').glob('*.md'))
    manifest=dict(schema_version=1,outcomes=13568,trace_screens=13568,source_condition_records=8768,
        original_csv_sha256=digest(BASE/'all_thinking_records.csv'),
        original_trace_screens_sha256=digest(BASE/'trace_screens.jsonl'),
        trace_projection='All per-call counts and trace metadata retained in trace_features.csv. Broad image-denial matches/offsets/context remain in candidate CSV; bulky full match cache is archived only.',
        omitted_redundant_file='failure_inventory.jsonl duplicates outcomes/source records and screens; full per-match cache and input-receipt list stay archived. All main failures are in main_native_failure_cases.csv.',
        metadata_join='identity + :: + condition; source metadata can differ between image and evidence conditions.',
        files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=digest(p)) for p in files])
    write_same_or_new(SHARED/'manifest.json',(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())
    verify()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true')
    args=parser.parse_args();verify() if args.verify else export()
