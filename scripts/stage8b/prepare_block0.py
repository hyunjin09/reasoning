"""Freeze construction inputs and automatic extraction before any new grading."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from visual_reasoning.stage8b.v2_scoring import extract_answer
from visual_reasoning.stage8b.scoring import safe_number

ROOT = Path('outputs/stage8b_block0/v1')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)


def main():
    index_path = 'outputs/stage8b1a/cohort/census256_artifact_index_node06_v1.json'
    manifest_path = 'outputs/stage8b1a/cohort/census256_manifest_v1.jsonl'
    proof_path = 'outputs/stage8b1a/audit/native256_completion_verified_v1.json'
    detector_path = 'outputs/stage8a/analysis/discovery_freeze_v1/freeze.json'
    prior_path = 'outputs/stage8b/v2/analysis/census_snapshot_reviewed_v2.json'
    config_path = 'outputs/stage8b1a/config/resume125_node06_v1.json'
    index = json.loads(Path(index_path).read_text())['rows']
    manifest = [json.loads(x) for x in Path(manifest_path).read_text().splitlines()]
    proof = json.loads(Path(proof_path).read_text())
    detector = json.loads(Path(detector_path).read_text())
    prior = json.loads(Path(prior_path).read_text())['rows']
    assert len(index) == len(manifest) == len({r['item_id'] for r in index}) == len({r['family_id'] for r in index}) == 256
    assert [(r['order'], r['item_id'], r['family_id']) for r in index] == [(r['order'], r['item_id'], r['family_id']) for r in manifest]
    assert {r['item_id'] for r in prior} == {r['item_id'] for r in index[:32]}
    automatic, packets, cohort = [], [], []
    for i, (source, row) in enumerate(zip(index, manifest)):
        receipt_path = Path(source['receipt'])
        receipt = json.loads(receipt_path.read_text())
        actual = digest(receipt_path)
        assert actual == proof['receipt_sha256'][str(receipt_path)]
        if source['receipt_sha256'] is not None:
            assert actual == source['receipt_sha256']
        assert json.loads((receipt_path.parent/'manifest_row.json').read_text()) == row
        cohort.append(dict(source, receipt_sha256=actual, image_path=row['image'], image_sha256=row['image_sha256']))
        if i < 32:
            continue
        gen_path = receipt_path.parent/'generation.json'
        assert digest(gen_path) == receipt['provenance_sha256'][str(gen_path)]
        text = json.loads(gen_path.read_text())['raw_decoded_response']
        extraction = extract_answer(text, row['options'])
        automatic.append(dict(item_id=row['item_id'], generation_sha256=digest(gen_path), **extraction))
        value = extraction['extracted']
        letters = [chr(65+j) for j in range(len(row['options']))]
        simple = value is not None and (value.strip().strip('().').upper() in letters if letters else safe_number(value) is not None)
        if not simple:
            offset = text.rfind('</think>')+8 if '</think>' in text else 0
            packet = dict(item_id=row['item_id'], question=row['question'], options=row['options'],
                          generation_sha256=digest(gen_path), automatic=extraction, scope_offset=offset,
                          scope_text=text[offset:], ground_truth_excluded=True)
            save(ROOT/'audit'/'blind_extraction'/f"{row['item_id']}.json", packet)
            packets.append(dict(item_id=row['item_id'], automatic=extraction, scope_characters=len(text)-offset))
    save(ROOT/'audit'/'automatic_extraction_freeze.json', dict(at=datetime.now(timezone.utc).isoformat(),
         ground_truth_used=False, rows=automatic, manual_candidates=packets))
    save(ROOT/'stage8b_block0_cohort_manifest.json', dict(rows=cohort, examples=256, families=256,
         original_audit=32, additional=224, source_manifest=manifest_path, source_manifest_sha256=digest(manifest_path)))
    sources = [index_path, manifest_path, proof_path, detector_path, prior_path, config_path,
               detector['retrieval']['models'], 'plan/stage8b_block0_compute_once_shared_dataset_plan.md',
               'plan/stage8b_block0_execution_protocol.md', 'code/visual_reasoning/stage8b/v2_scoring.py',
               'code/visual_reasoning/stage8b/scoring.py', 'code/visual_reasoning/stage8b/transfer.py']
    save(ROOT/'audit'/'input_freeze.json', dict(at=datetime.now(timezone.utc).isoformat(),
         source_sha256={p:digest(p) for p in sources}, detector=detector['retrieval'],
         canonical_config=config_path, prior_outcomes=prior_path, source_manifest=manifest_path,
         cohort_manifest=str(ROOT/'stage8b_block0_cohort_manifest.json'),
         cohort_manifest_sha256=digest(ROOT/'stage8b_block0_cohort_manifest.json'),
         outcome_stratified_analysis=False))
    print(json.dumps(dict(cohort=256, automatic=len(automatic), manual_candidates=packets), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
