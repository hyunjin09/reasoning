"""Read-only retrospective of existing Thinking math runs; no inference imports."""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/thinking_math_failure_audit/v1'
SEED = 20261122
DRAWS = 4000
VERSIONS = ['Text Dominant', 'Text Lite', 'Text Only', 'Vision Intensive', 'Vision Dominant', 'Vision Only']
TOPICS = {
    'counting': r'\bhow many\b|\bnumber of (?:cubes|blocks|circles|triangles|squares|rectangles|paths|routes|ways|objects|points|edges|vertices|intersections|kangaroos)\b|\bcount(?:ing)?\b',
    'area': r'\barea\b',
    'length_distance_perimeter': r'\blength\b|\bdistance\b|\bperimeter\b|\bradius\b|\bdiameter\b',
    'angle_relations': r'\bangle\b|\bangles\b|\\angle|\bdegrees?\b|°',
    'solid_volume_surface': r'\bvolume\b|\bsurface area\b|\bsolid\b|\bprism\b|\bpyramid\b|\bcubes?\b|\bcylinder\b|\bcone\b',
    'transformation_viewpoint': r'\brotat\w*\b|\breflect\w*\b|\bfold\w*\b|\bmirror\b|\bview from\b|\bviewed from\b|\bunfold\w*\b',
    'graph_chart_table_coordinate': r'\bgraph\b|\bchart\b|\btable\b|\bcoordinate\w*\b|\baxes\b|\bx-axis\b|\by-axis\b|\bplott?\w*\b',
    'pattern_sequence_missing': r'\bpattern\b|\bsequence\b|\bmissing\b|\bquestion mark\b|\bnext (?:figure|shape|number|term)\b',
    'probability_statistics': r'\bprobability\b|\baverage\b|\bmedian\b|\bmean\b|\bpercent\w*\b|\bratio\b',
    'spatial_relation_connectivity': r'\binside\b|\boutside\b|\boverlap\w*\b|\bintersect\w*\b|\bparallel\b|\bperpendicular\b|\badjacent\b|\bconnected\b|\bpath\b|\broute\b',
}
FLAG_PATTERNS = {
    'image_unavailable_statement': [
        r"\b(?:I|we) (?:can(?:not|'t|’t)|am unable to|are unable to) (?:actually )?(?:see|view|access|inspect|read) (?:the |this |an? |any )?(?:provided |actual |original )?(?:image|diagram|picture|figure)\b",
        r"\bI can(?:not|'t|’t) see it\b",
        r'\b(?:image|diagram|picture) (?:is |was )?(?:not (?:visible|available|provided|accessible)|unavailable|missing)\b',
    ],
    'description_or_text_reference': [r'\b(?:based on|from|according to|using) (?:the )?(?:text(?:ual)? description|description|given text|problem statement)\b'],
    'assumption_language': [r"\b(?:let(?:'s| us) assume|assuming|assume that|if we assume|most reasonable assumption)\b"],
    'template_language': [r'\b(?:standard|typical|usual|common|classic) (?:three[- ]circle |geometr(?:ic|y) |Venn )?(?:diagram|configuration|problem|Venn diagram|triangle|pattern|arrangement)\b'],
}


def read_json(path):
    return json.loads(Path(path).read_text())


def read_rows(path):
    with Path(path).open() as f:
        return [json.loads(line) for line in f if line.strip()]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def save_csv(path, rows):
    rows = list(rows)
    if not rows:
        return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in r.items()})


def status_counts(rows):
    cc = collections.Counter(r['status'] for r in rows)
    scored = cc['CORRECT'] + cc['WRONG']
    return dict(n=len(rows), correct=cc['CORRECT'], wrong=cc['WRONG'], unscorable=cc['UNSCORABLE'],
                technical_missing=cc['TECHNICAL_MISSING'], scored=scored,
                wrong_rate=cc['WRONG'] / scored if scored else None,
                unscorable_rate=cc['UNSCORABLE'] / len(rows) if rows else None)


def question_tags(text):
    result = [key for key, pattern in TOPICS.items() if re.search(pattern, text, re.I)]
    return result or ['unspecified_in_question_text']


def literal_flags(text):
    out = {}
    for key, patterns in FLAG_PATTERNS.items():
        hits = sorted({(m.start(), m.end()) for p in patterns for m in re.finditer(p, text, re.I)})
        out[key] = [dict(start=a, end=b, quote=text[a:b],
                         context=text[max(0, a-140):min(len(text), b+180)]) for a, b in hits]
    return out


def evidence_state(code):
    return {'1': 'ALL_REQUIRED_SOURCE_FACTS_EXPLICITLY_CORRECT',
            '2': 'EXPLICIT_REQUIRED_SOURCE_ERROR',
            '3': 'INCOMPLETE_OR_AMBIGUOUS'}[str(code)]


def cluster_arrays(rows):
    groups = collections.defaultdict(list)
    for r in rows:
        groups[r['family_id']].append(r)
    ids = sorted(groups)
    return dict(families=ids,
                wrong=np.array([sum(r['status'] == 'WRONG' for r in groups[f]) for f in ids]),
                scored=np.array([sum(r['status'] in ['CORRECT', 'WRONG'] for r in groups[f]) for f in ids]))


def interval(rows):
    a = cluster_arrays(rows)
    if not a['scored'].sum():
        return dict(clusters=len(a['families']), ci_low=None, ci_high=None, family_equal_wrong_rate=None)
    n = len(a['families'])
    rng = np.random.default_rng(SEED)
    weights = rng.multinomial(n, np.full(n, 1/n), size=DRAWS)
    den = weights @ a['scored']
    num = weights @ a['wrong']
    values = num[den > 0] / den[den > 0]
    mask = a['scored'] > 0
    return dict(clusters=n, ci_low=float(np.quantile(values, .025)), ci_high=float(np.quantile(values, .975)),
                family_equal_wrong_rate=float(np.mean(a['wrong'][mask] / a['scored'][mask])),
                finite_draws=len(values))


def pair_transitions(rows, left, right):
    by = collections.defaultdict(dict)
    for r in rows:
        if r['version'] in [left, right]:
            key = (r['family_id'], r['item_id'], r['replicate'])
            assert r['version'] not in by[key], ('duplicate pair cell', key, r['version'])
            by[key][r['version']] = r
    pairs = []
    for (fam, item, rep), cells in sorted(by.items()):
        if left not in cells or right not in cells:
            continue
        pairs.append(dict(family_id=fam, item_id=item, replicate=rep,
                          left_status=cells[left]['status'], right_status=cells[right]['status']))
    cc = collections.Counter(r['left_status'] + '__' + r['right_status'] for r in pairs)
    return dict(left=left, right=right, n=len(pairs), counts=dict(cc), pairs=pairs)


def raw_screen(row, task):
    rawdir = ROOT / 'outputs/stage14b/raw' / task['collection'] / row['task_id']
    path = rawdir/'attempt_0/generation.json'
    content = path.read_bytes() if path.exists() else b''
    if hashlib.sha256(content).hexdigest() != row['generation_sha256']:
        matches = [p for p in rawdir.glob('attempt_*/generation.json') if sha(p) == row['generation_sha256']]
        assert len(matches) == 1, (row['task_id'], 'canonical hash matches', len(matches))
        path = matches[0]
        content = path.read_bytes()
    assert hashlib.sha256(content).hexdigest() == row['generation_sha256']
    g = json.loads(content)
    raw = g['raw_decoded_response']
    assert g['tokens'] == row['tokens']
    assert g['task_id'] == row['task_id']
    flags = literal_flags(raw)
    split = raw.rfind('</think>')
    words = re.findall(r"\b[\w']+\b", raw.lower())
    blocks = [' '.join(words[i:i+32]) for i in range(0, max(0, len(words)-31), 16)]
    repetition = 1-len(set(blocks))/len(blocks) if blocks else 0.
    rec = dict(task_id=row['task_id'], generation_path=str(path.relative_to(ROOT)),
               generation_sha256=row['generation_sha256'], input_path=str((path.parent/'input.json').relative_to(ROOT)),
               result_path=str((path.parent/'result.json').relative_to(ROOT)),
               seed=g['seed'], raw_characters=len(raw), thinking_boundary=split,
               thinking_characters=split if split >= 0 else None,
               final_response_characters=len(raw)-split-len('</think>') if split >= 0 else None,
               think_delimiters=raw.count('</think>'), wait_count=len(re.findall(r'\bwait\b', raw, re.I)),
               word_count=len(words), repeated_32word_window_fraction=repetition,
               lexical_flags=flags)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, default=OUT)
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    sources = [ROOT/'outputs/stage14b/scoring'/f for f in ['scored_outputs.jsonl', 'confirmatory_scored_outputs.jsonl']]
    main_rows, confirm = [[r for r in read_rows(p) if r['model'] == 'T'] for p in sources]
    assert len(main_rows) == 8768 and len(confirm) == 4800
    all_rows = main_rows + confirm
    assert len({r['task_id'] for r in all_rows}) == len(all_rows)
    tasks = {t['task_id']: t for mode in ['main', 'confirmatory']
             for t in read_rows(ROOT/f'outputs/stage14b/manifests/{mode}_tasks.jsonl') if t['model_key'] == 'T'}
    assert set(tasks) == {r['task_id'] for r in all_rows}
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    for mode in ['main', 'confirmatory']:
        p = ROOT/f'outputs/stage14b/manifests/{mode}_tasks.jsonl'
        source_hashes[str(p.relative_to(ROOT))] = sha(p)
    estar_path = ROOT/'outputs/stage14a/v1/stage14a_mathvision_e_star_annotations.json'
    estar = {r['item_id']: r for r in read_json(estar_path)['rows']}
    source_hashes[str(estar_path.relative_to(ROOT))] = sha(estar_path)
    audit_path = ROOT/'outputs/stage14d0_answer_evidence_supplement_v1/family_evidence_status.csv'
    with audit_path.open() as f:
        audits = {r['item_id']: r for r in csv.DictReader(f) if r['model'] == 'T'}
    source_hashes[str(audit_path.relative_to(ROOT))] = sha(audit_path)
    verse_canonical = {r['item_id']: r['source_metadata']['prompt'] for r in main_rows if r['version'] == 'Text Dominant'}
    rows = []
    for r in all_rows:
        meta = r['source_metadata']; t = tasks[r['task_id']]
        assert r['family_id'] == t['family_id'] and r['identity'] == t['identity']
        p = meta['prompt']
        r = dict(r, dataset='MathVerse' if r['version'] else 'MATH-Vision', question=p,
                 subject=meta['subject'], answer_type=meta['answer_type'],
                 difficulty=meta.get('difficulty'),
                 question_topics=question_tags(verse_canonical[r['item_id']] if r['version'] else p),
                 source_clean=meta.get('clean_paired'),
                 repeat_group=meta.get('source_repeat_problem_indices', [r['item_id']]),
                 e_star_available=r['item_id'] in estar if not r['version'] else False)
        if r['dataset'] == 'MATH-Vision' and r['item_id'] in audits:
            a = audits[r['item_id']]
            r['existing_audit'] = {k:a[k] for k in ['panel', 'weight', 'native_status', 'last_state', 'pre_answer_anchored_first_state', 'boundary_available']}
            r['existing_audit']['evidence_status'] = evidence_state(a['last_state'])
        rows.append(r)
    save_json(out/'analysis_rules.json', dict(seed=SEED, draws=DRAWS, topic_patterns=TOPICS, lexical_patterns=FLAG_PATTERNS,
         interpretation='Lexical flags are navigation cues, not cause labels; source annotations are historical and unchanged.',
         model='Qwen3-VL-4B-Thinking', independent_unit='conservative visual family; repeated versions/seeds remain nested'))

    # Cache only new derived screens. Every newly screened raw must match its frozen score hash.
    cache = out/'trace_screens.jsonl'
    screens = {r['task_id']:r for r in read_rows(cache)} if cache.exists() else {}
    pending = [r for r in rows if r['task_id'] not in screens]
    for r in rows:
        if r['task_id'] in screens:
            assert screens[r['task_id']]['generation_sha256'] == r['generation_sha256']
    with cache.open('a') as f, ThreadPoolExecutor(max_workers=4) as pool:
        for rec in pool.map(lambda r: raw_screen(r, tasks[r['task_id']]), pending):
            screens[rec['task_id']] = rec
            f.write(json.dumps(rec, ensure_ascii=False)+'\n')
            if len(screens) % 250 == 0:
                f.flush();print(f'Screened {len(screens)}/{len(rows)} Thinking records', flush=True)
    assert len(screens) == len(rows)
    for r in rows:
        r['screen'] = screens[r['task_id']]
    primary = [r for r in rows if r['replicate'] == 0 and r['condition'] != 'evidence']
    assert len(primary) == 7768
    assert sum(r['status']=='WRONG' for r in primary) == 2303
    save_csv(out/'all_thinking_records.csv', [
        {k:r.get(k) for k in ['task_id','dataset','item_id','identity','family_id','condition','version','replicate','status','answer','subject','answer_type','difficulty','source_clean','repeat_group','question','question_topics','e_star_available','existing_audit','tokens','cap_hit','finish_reason']}
        | {k:r['screen'][k] for k in ['generation_path','generation_sha256','input_path','result_path','wait_count','word_count','repeated_32word_window_fraction']}
        for r in rows])
    with (out/'failure_inventory.jsonl').open('w') as f:
        for r in rows:
            if r['status'] in ['WRONG','UNSCORABLE']:
                f.write(json.dumps(r,ensure_ascii=False)+'\n')

    groups = []
    def add_group(rr, dimension, level, dataset=None, version=None):
        if not rr:
            return
        groups.append(dict(dataset=dataset or rr[0]['dataset'], version=version, dimension=dimension, level=str(level),
                           **status_counts(rr), **interval(rr)))
    for dataset in ['MATH-Vision', 'MathVerse']:
        rr = [r for r in primary if r['dataset']==dataset]
        versions = [None] if dataset=='MATH-Vision' else [*VERSIONS, 'ALL_VERSIONED_CALLS']
        for version in versions:
            ss = rr if version in [None, 'ALL_VERSIONED_CALLS'] else [r for r in rr if r['version']==version]
            add_group(ss, 'overall','all',dataset,version)
            for axis in ['subject','answer_type'] + (['difficulty'] if dataset=='MATH-Vision' else ['source_clean']):
                for level in sorted({str(r[axis]) for r in ss}):
                    add_group([r for r in ss if str(r[axis])==level],axis,level,dataset,version)
            for tag in [*TOPICS, 'unspecified_in_question_text']:
                add_group([r for r in ss if tag in r['question_topics']], 'question_text_cue',tag,dataset,version)
    save_csv(out/'question_type_failure_rates.csv', groups)
    print('Question-type tables complete', flush=True)

    # Source flags only in the 1,000 source-eligible MATH-Vision items.
    features = []
    source_native = [r for r in primary if r['dataset']=='MATH-Vision' and r['item_id'] in estar]
    for field in ['requires_entity_binding','requires_quantity_reading','requires_spatial_relation','requires_diagram_label_reading','requires_graph_table_reading']:
        for level in [False, True]:
            rr=[r for r in source_native if estar[r['item_id']][field] == level]
            features.append(dict(feature=field,level=str(level),**status_counts(rr),**interval(rr)))
    def structured_size(a):
        return sum(x.get('structured_subfact_count',0) or 0 for x in a.get('atom_metadata',[]) if x['atom_type']=='structured_layout')
    for field in ['structured_layout','primary_atoms','structured_subfacts']:
        def value(r):
            a=estar[r['item_id']]
            if field=='structured_layout': return str(any(x['atom_type']=='structured_layout' for x in a['atom_metadata']))
            if field=='primary_atoms': return str(a['num_e_star_atoms'])
            n=structured_size(a)
            return 'none' if n==0 else '1-4' if n<=4 else '5-9' if n<=9 else '10-19' if n<=19 else '20+'
        for level in sorted({value(r) for r in source_native}):
            rr=[r for r in source_native if value(r)==level]
            features.append(dict(feature=field,level=level,**status_counts(rr),**interval(rr)))
    save_csv(out/'source_feature_failure_rates.csv',features)

    # E* followups keep wrong/uncertain/correct transitions separate for all seeds.
    transitions=[]
    for rep in [0,1,2]:
        by=collections.defaultdict(dict)
        for r in rows:
            if r['dataset']=='MATH-Vision' and r['replicate']==rep:
                by[r['item_id']][r['condition']]=r
        for item,cells in by.items():
            if not {'image','evidence'} <= set(cells): continue
            a,b=cells['image'],cells['evidence']
            transitions.append(dict(item_id=item,family_id=a['family_id'],replicate=rep,subject=a['subject'],
               native_status=a['status'],evidence_status=b['status'],native_answer=a['answer'],evidence_answer=b['answer'],
               native_task=a['task_id'],evidence_task=b['task_id']))
    save_csv(out/'evidence_followups.csv',transitions)
    follow_summary={}
    for rep in [0,1,2]:
        rr=[x for x in transitions if x['replicate']==rep]
        follow_summary[str(rep)]=dict(n=len(rr),transitions=dict(collections.Counter(x['native_status']+'__'+x['evidence_status'] for x in rr)))

    # Six MathVerse versions are nested in family. Main/clean and repeat-cluster views.
    verse=[r for r in primary if r['dataset']=='MathVerse']
    modality=[]
    for clean in [False,True]:
        rr=[r for r in verse if not clean or r['source_clean']]
        for left,right in [('Text Dominant','Vision Only'),('Text Only','Vision Only'),('Text Dominant','Vision Dominant'),('Text Lite','Vision Intensive')]:
            p=pair_transitions(rr,left,right)
            scored=[x for x in p['pairs'] if x['left_status'] in ['CORRECT','WRONG'] and x['right_status'] in ['CORRECT','WRONG']]
            ids=sorted({x['family_id'] for x in scored});rg=np.random.default_rng(SEED)
            # Exactly one paired item per frozen MathVerse family at r0.
            assert len(ids)==len(scored)
            values=np.array([(x['right_status']=='WRONG')-(x['left_status']=='WRONG') for x in scored],dtype=float)
            boot=rg.multinomial(len(values),np.full(len(values),1/len(values)),size=DRAWS)@values/len(values)
            modality.append(dict(clean_only=clean,left=left,right=right,n=p['n'],counts=p['counts'],
                 paired_scored=len(scored),right_minus_left_error_pp=float(100*values.mean()),
                 ci_low_pp=float(100*np.quantile(boot,.025)),ci_high_pp=float(100*np.quantile(boot,.975))))
    save_json(out/'modality_transitions.json',modality)
    base_profile=[]
    by=collections.defaultdict(list)
    for r in verse:by[r['item_id']].append(r)
    for item,rr in by.items():
        cc=status_counts(rr)
        base_profile.append(dict(item_id=item,family_id=rr[0]['family_id'],subject=rr[0]['subject'],source_clean=rr[0]['source_clean'],
            correct_versions=cc['correct'],wrong_versions=cc['wrong'],unscorable_versions=cc['unscorable'],
            category='ALL_SIX_CORRECT' if cc['correct']==6 else 'ALL_SIX_WRONG' if cc['wrong']==6 else 'MIXED_OR_UNSCORABLE',
            statuses={r['version']:r['status'] for r in rr}))
    save_csv(out/'mathverse_family_profiles.csv',base_profile)
    repeat_rows=[dict(r,family_id='verse_repeat:'+','.join(sorted(r['repeat_group'],key=str))) for r in verse]
    repeat_summary={v:dict(**status_counts([r for r in repeat_rows if r['version']==v]),**interval([r for r in repeat_rows if r['version']==v])) for v in VERSIONS}

    # Behavior screening is computed over all raw output, before vs after think separately in quotes.
    behavior=[]
    for dataset in ['MATH-Vision','MathVerse']:
        for status in ['CORRECT','WRONG','UNSCORABLE']:
            rr=[r for r in primary if r['dataset']==dataset and r['status']==status]
            for flag in FLAG_PATTERNS:
                hit=[r for r in rr if r['screen']['lexical_flags'][flag]]
                behavior.append(dict(dataset=dataset,status=status,flag=flag,n=len(rr),flagged=len(hit),rate=len(hit)/len(rr) if rr else None,
                                      interpretation='Exact lexical trigger only; no semantic/causal classification'))
            for flag,fn in [('20_plus_waits',lambda s:s['wait_count']>=20),('repeated_32word_windows_ge_10pct',lambda s:s['repeated_32word_window_fraction']>=.1)]:
                hit=[r for r in rr if fn(r['screen'])]
                behavior.append(dict(dataset=dataset,status=status,flag=flag,n=len(rr),flagged=len(hit),rate=len(hit)/len(rr) if rr else None,
                                      interpretation='Mechanical text behavior, not validated pathology'))
    save_csv(out/'trace_behavior_rates.csv',behavior)
    seeds=[]
    for dataset in ['MATH-Vision','MathVerse']:
        for cond in (['image','evidence'] if dataset=='MATH-Vision' else ['native']):
            ids={r['identity'] for r in rows if r['dataset']==dataset and r['condition']==cond and r['replicate']==1}
            for rep in [0,1,2]:
                rr=[r for r in rows if r['identity'] in ids and r['condition']==cond and r['replicate']==rep]
                seeds.append(dict(dataset=dataset,condition=cond,replicate=rep,**status_counts(rr)))
    save_csv(out/'confirmation_seed_sensitivity.csv',seeds)

    summary=dict(primary_native=dict(n=len(primary),**{dataset:status_counts([r for r in primary if r['dataset']==dataset]) for dataset in ['MATH-Vision','MathVerse']}),
        total_thinking_records=len(rows),total_native_records=sum(r['condition']!='evidence' for r in rows),
        all_native_wrong=sum(r['condition']!='evidence' and r['status']=='WRONG' for r in rows),
        all_native_unscorable=sum(r['condition']!='evidence' and r['status']=='UNSCORABLE' for r in rows),
        source_eligible_native=status_counts(source_native),followups=follow_summary,
        mathverse_family_profiles=dict(collections.Counter(x['category'] for x in base_profile)),
        repeat_cluster_sensitivity=repeat_summary,
        source_review_coverage=dict(existing_audit_families=len(audits),main_wrong_with_audit=sum(r['dataset']=='MATH-Vision' and r['status']=='WRONG' and r['item_id'] in audits for r in primary)),
        raw_screens=len(screens),script_wall_seconds=time.monotonic()-started,gpu_hours=0,
        limitations=['All rows screened computationally; not an exhaustive new human/semantic source-image audit.',
                     'No attention/image-necessity measurements; no ignored-image classification.',
                     'Existing audit and E* references have documented source/QC limitations.',
                     'Retrospective source/trace associations, not confirmatory causal effects.'])
    save_json(out/'summary.json',summary)
    for path,expected in source_hashes.items():assert sha(ROOT/path)==expected,path
    save_json(out/'validation.json',dict(complete=True,raws_hash_verified=len(screens),source_hashes_unchanged=source_hashes,
        main_native_thinking_expected=7768,main_wrong_expected=2303,score_changes=0,new_generations=0,gpu_hours=0))
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)


if __name__ == '__main__':
    main()
