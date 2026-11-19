"""Serialize explicit human/agent semantic decisions; never infer matches.

The caller supplies every recovered source unit, verbatim quotation, exact-atom
judgment and additional assertion classification after source/response review.
"""
from scripts.stage14c.common import *
from scripts.stage14c.d1_scoring_v2 import validate_review
from scripts.stage14c.d1_review_v2 import validate_units


def decision(row, matches, extras, exact_atoms=(), reason='Explicit source-image and committed-response semantic review.', status='SCORED'):
    """matches: (atom_index, unit_index, verbatim_quote); extras: (class, quote, binding)."""
    atoms=[dict(exact=i in exact_atoms,recovered_units=[],evidence_quotes=[]) for i in range(len(row['source_target']['atoms']))]
    claims=[]
    for ai,ui,quote in matches:
        key=row['shared_source_unit_map']['atoms'][ai]['subfact_keys'][ui]
        ri=len(atoms[ai]['recovered_units']);atoms[ai]['recovered_units'].append(key);atoms[ai]['evidence_quotes'].append(quote)
        claims.append(dict(text=quote,binding=f'atom{ai}: {key}',classification='required',target_atom=ai,target_unit=ri))
    for kind,quote,binding in extras:claims.append(dict(text=quote,binding=binding,classification=kind))
    review=dict(status=status,reason=reason,atoms=atoms,claims=claims)
    r=dict(task_id=row['task']['task_id'],target_sha256=fingerprint(row['source_target']),
      generation_sha256=sha(row['raw_generation_path']) if row['raw_generation_path'] else None,
      unit_map_sha256=fingerprint(row['shared_source_unit_map']),source_semantic_reviewed=True,review=review)
    if 'first_review' in row:r.update(first_review_sha256=fingerprint(row['first_review']),reread_response_and_source=True)
    validate_review(row['source_target'],review);validate_units(row['shared_source_unit_map'],r)
    return r


def batch(path, packet, decisions):
    assert len(decisions)==len(packet['rows'])
    assert [r['task_id'] for r in decisions]==[r['task']['task_id'] for r in packet['rows']]
    save(path,dict(at=now(),model=packet['model'],review_pass=packet['review_pass'],rows=decisions,
         explicit_semantic_judgments=True,serialization_code_sha256=sha(__file__)))
