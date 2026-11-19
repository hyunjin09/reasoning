"""D1 source-semantic review contract; no automatic semantic grading.

Targets retain the frozen source atom boundaries and internal counts. Explicit
review decisions map distinct asserted facts to source units and preserve
contradictions, unsupported claims, derivations, and unresolved probes.
"""
from collections import Counter
from scripts.stage14c.common import *

CLASSES={'required','accurate_irrelevant','unsupported','contradictory','derived','uncertain'}


def target_schema(row):
    source=row['source_target']; atoms=[]
    if 'atoms' in source:
        for a in source['atoms']:
            atoms.append(dict(text=a['text'],atom_type=a['atom_type'],
                 subfact_count=a.get('structured_subfact_count') or 1,unit=a.get('unit','scalar relation')))
    else:
        # The frozen math rendering ends its evidence block at the first blank
        # line. No question text/gold is converted into an evidence target.
        evidence=source['source_evidence_prompt'].split('\n\n',1)[0]
        texts=[x[2:] for x in evidence.splitlines() if x.startswith('- ')]
        assert len(texts)==len(source['atom_metadata'])
        for text,a in zip(texts,source['atom_metadata']):
            atoms.append(dict(text=text,atom_type=a['atom_type'],
                 subfact_count=a.get('structured_subfact_count') or 1,unit=a.get('size_unit','scalar relation')))
    assert atoms and all(a['subfact_count']>=1 for a in atoms)
    return dict(family_id=row['family_id'],benchmark=row['benchmark'],atoms=atoms,
                frozen_target_sha256=fingerprint(row))


def validate_review(target,review):
    assert review['status'] in {'SCORED','UNRESOLVED','TECHNICAL_MISSING'}
    assert review['reason'].strip()
    if review['status']!='SCORED':return
    assert len(review['atoms'])==len(target['atoms'])
    recovered=set()
    for i,(a,r) in enumerate(zip(target['atoms'],review['atoms'])):
        assert isinstance(r['exact'],bool)
        assert len(r['recovered_units'])==len(r['evidence_quotes'])<=a['subfact_count']
        assert len(set(r['recovered_units']))==len(r['recovered_units'])
        assert all(x.strip() for x in r['recovered_units']+r['evidence_quotes'])
        assert not r['exact'] or len(r['recovered_units'])==a['subfact_count']
        recovered.update((i,j) for j in range(len(r['recovered_units'])))
    matched=set();claims=set()
    for c in review['claims']:
        assert c['classification'] in CLASSES and c['text'].strip()
        # Repeated identical text may denote distinct bound source facts (e.g.
        # equal entries in different table cells). Preserve explicit binding.
        # Semantic duplicates still require reviewer deduplication.
        key=(c['text'].strip().casefold(),c.get('binding','').strip().casefold());assert key not in claims;claims.add(key)
        if c['classification']=='required':
            key=(c['target_atom'],c['target_unit'])
            assert key in recovered and key not in matched
            matched.add(key)
    assert matched==recovered,'Every recovered unit needs one distinct asserted fact'


def metrics(target,review):
    validate_review(target,review)
    if review['status']!='SCORED':return dict(status=review['status'])
    total=sum(a['subfact_count'] for a in target['atoms'])
    recovered=sum(len(a['recovered_units']) for a in review['atoms'])
    exact=sum(a['exact'] for a in review['atoms']);counts=Counter(c['classification'] for c in review['claims'])
    # Derived quantities and explicitly uncertain non-assertions are separately
    # reported; neither enters the asserted direct-image fact denominator.
    asserted=sum(v for k,v in counts.items() if k not in {'derived','uncertain'})
    return dict(status='SCORED',atoms=len(target['atoms']),exact_atoms=exact,
                subfacts=total,recovered_subfacts=recovered,
                subfact_recall=recovered/total,exact_atom_recall=exact/len(target['atoms']),
                full_E_star_recovery=exact==len(target['atoms']),
                asserted_visual_facts=asserted,required_visual_facts=counts['required'],
                targeted_precision=counts['required']/asserted if asserted else None,
                claim_classes=dict(counts))


def freeze_schema():
    target_path=ROOT/'source/D1_scoring_targets.jsonl'
    schemas=[target_schema(r) for r in rows(target_path)]
    assert len(schemas)==300
    write_rows(ROOT/'source/D1_review_schema_v1.jsonl',schemas)
    save(ROOT/'audit/D1_review_contract_v1.json',dict(at=now(),targets_sha256=sha(target_path),
        schema_sha256=sha(ROOT/'source/D1_review_schema_v1.jsonl'),
        code_sha256=sha(__file__),model_outputs_used=False,
        rules=[
            'Preserve frozen primary atoms, source content, unit descriptions and internal counts.',
            'Before scoring a family, write one shared source-unit decomposition; apply it identically to I and T.',
            'Use semantic source binding, not string identity. No derived facts count as recovered direct evidence.',
            'Exact atom recovery requires every fact and binding in that frozen atom, not only the numerical count.',
            'Split asserted conjunctions at the same source-unit granularity and count each distinct assertion once.',
            'Targeted precision denominator includes required, accurate-irrelevant, unsupported and contradictory asserted image facts.',
            'Derived quantities and explicit uncertain non-assertions are separate contract violations/coverage, not direct-image assertions.',
            'A completed response with no asserted source facts has zero recall and undefined precision.',
            'Unclosed Thinking, missing valid response or an ambiguous cap commitment stays unresolved, not zero recovery.',
            'All600 probes require two-pass same-agent semantic review; report macro and micro denominators separately.',
            'D1 is a separate elicitation assay; its recovery does not establish what a native solver internally knew.'
        ]))


# v1 source schema/contract remain immutable; this version only repairs
# validation of identical quoted values with different source bindings.
