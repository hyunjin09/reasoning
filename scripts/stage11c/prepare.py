"""Fresh source-only family audit and frozen held-out/technical packets."""
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path
import pyarrow as pa
from scripts.stage11c.common import ROOT, SEED, load, save, sha, now
from scripts.stage11c.protocol import order_key, stratified


def main():
    source_path = Path('outputs/stage8c_v2/v1/audit/remaining_family_representatives.json')
    old_path = Path('outputs/stage9a/v1/stage9a_cohort_manifest.json')
    prior_paths = [old_path, Path('outputs/stage11b/v1/stage11b_discovery_manifest.json'),
                   Path('outputs/stage11b/v1/stage11b_discovery_manifest_v2.json')]
    source = load(source_path)['rows']
    prior = [r for p in prior_paths for r in load(p)['rows']]
    excluded = {r['item_id'] for r in prior}
    for row in prior:
        excluded.update(row.get('source_only_alias_item_ids', []))
    repair = load('outputs/stage11b/v1/audit/freshness_repair_v2.json')
    excluded.update(repair['excluded_prior_alias_item_ids'])
    allrows = {r['item_id']: r for r in prior}
    allrows.update({r['item_id']: r for r in source})
    parent = {i: i for i in allrows}

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        parent[root(a)] = root(b)

    identities = {}
    for i, row in allrows.items():
        for key in [('family', row.get('inherited_family_id', row['family_id'])),
                    ('pixels', row['decoded_image_sha256']),
                    ('question', re.sub(r'\s+', ' ', row['question'].lower()).strip())]:
            if key in identities:
                union(i, identities[key])
            else:
                identities[key] = i
    tokens = {i: set(re.findall(r'[a-z0-9]+', r['question'].lower())) for i, r in allrows.items()}
    items = list(allrows)
    edges = []
    for index, a in enumerate(items):
        x = tokens[a]
        if len(x) < 20:
            continue
        for b in items[:index]:
            y = tokens[b]
            if len(y) < 20:
                continue
            overlap = len(x & y) / len(x | y)
            if overlap >= .45:
                union(a, b)
                edges.append(dict(a=a, b=b, token_jaccard=overlap))
    banned = {root(i) for i in excluded if i in parent}
    groups = defaultdict(list)
    for i in items:
        groups[root(i)].append(i)
    allowed_source = {r['item_id'] for r in source}
    fresh = []
    removed = []
    for key, ids in groups.items():
        candidates = [allrows[i] for i in ids if i in allowed_source and allrows[i]['level'] in [2, 3, 4]]
        if not candidates:
            continue
        if key in banned:
            removed.extend(r['item_id'] for r in candidates)
            continue
        row = dict(min(candidates, key=lambda r: order_key(r, SEED, 'representative')))
        row['inherited_family_id'] = row['family_id']
        if len(ids) > 1:
            row['family_id'] = 'stage11c_family_' + hashlib.sha256('|'.join(sorted(ids)).encode()).hexdigest()[:20]
        row['source_only_alias_item_ids'] = sorted(ids)
        row['major_subject'] = 'geometry' if 'geometry' in row['subject'] else 'other'
        fresh.append(row)
    assert len(fresh) >= 200, 'Insufficient fresh source pool; do not silently change rule'
    n = min(300, len(fresh))
    selected = stratified(fresh, n, SEED, 'heldout-source', ['subject', 'level', 'answer_format'])
    assert len({r['family_id'] for r in selected}) == n
    selected_ids = {r['item_id'] for r in selected}
    assert not selected_ids.intersection(excluded)
    inventory = load('outputs/stage8b/audit/input_inventory.json')
    assert sha(inventory['source']) == inventory['source_sha256']
    with pa.memory_map(inventory['source'], 'r') as handle:
        metadata = pa.ipc.open_stream(handle).read_all().select(['solution']).to_pylist()
    packets = []
    for index, row in enumerate(selected):
        assert Path(row['image']).resolve().is_relative_to('/data/dataset')
        assert sha(row['image']) == row['image_sha256']
        row['source_order'] = index
        packets.append(dict(row, source_solution=metadata[row['row_index']]['solution']))
    rule_path = ROOT/'stage11c_development_selection_rule.json'
    save(ROOT/'stage11c_heldout_source_manifest.json', dict(at=now(), frozen=True, rows=selected,
        n=n, seed=SEED, rule_sha256=sha(rule_path), model_outcomes_opened=False,
        source_sha256={str(p): sha(p) for p in [source_path, *prior_paths]},
        distribution={key: dict(Counter(str(r[key]) for r in selected)) for key in ['level', 'subject', 'answer_format']}))
    save(ROOT/'audit/freshness.json', dict(at=now(), passed=True, conservative_fresh_families=len(fresh),
        selected=n, prior_and_repaired_item_ids=sorted(excluded), removed_prior_alias_items=sorted(removed),
        union_edges=edges, rule='Inherited family, exact decoded image, exact normalized question, or question-token Jaccard>=.45 with>=20 tokens each; transitive union across all available levels before selection.',
        limitation='Conservative source-similarity union can overmerge distinct problems. No outcome data used.',
        images_verified=n, prior_overlap=0))
    save(ROOT/'packets/evidence_source.json', dict(at=now(), rows=packets,
        heldout_manifest_sha256=sha(ROOT/'stage11c_heldout_source_manifest.json'), model_outcomes_opened=False))
    # Source-only technical sampling from development; never enters confirmation.
    eligibility = {r['item_id']: r for r in load('outputs/stage11a/v1/stage11a_e_star_eligibility.json')['rows']}
    technical_pool = [dict(r, major_subject='geometry' if 'geometry' in r['subject'] else 'other')
                      for r in load(old_path)['rows'] if r['level'] in [2, 3, 4]
                      and eligibility[r['item_id']]['eligibility'] == 'E_STAR_ELIGIBLE']
    technical = stratified(technical_pool, 12, SEED, 'cap-validation', ['major_subject', 'level'])
    assert not {r['item_id'] for r in technical}.intersection(selected_ids)
    save(ROOT/'audit/cap_cases.json', dict(at=now(), frozen=True, rows=technical, n=12,
        source_only_sampling=True, individual_native_correctness_used=False, confirmatory=False,
        caps=[4096, 8192], arms=['thinking', 'instruct_direct'], exact_new_calls=48))
    save(ROOT/'audit/input_inventory.json', dict(at=now(), dataset_inventory=inventory,
        required_dataset='MathVision', required_models=load('outputs/stage11b/v1/config.json')['models'],
        no_download=True, project_dataset_link_present=Path('datasets').is_symlink(),
        derived_images_verified=n, heldout_outcomes_opened=False))
    print(dict(fresh=len(fresh), source_frozen=n, technical_cases=12,
               levels=dict(Counter(r['level'] for r in selected)), prior_alias_exclusions=len(removed)))


if __name__ == '__main__':
    main()
