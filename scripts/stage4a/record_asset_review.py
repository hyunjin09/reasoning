"""Record explicitly completed image/ROI reviews, checking saved invariants."""
import argparse
import numpy as np
from PIL import Image
from scripts.stage4a.prepare_config import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bases', required=True)
    parser.add_argument('--evidence', action='append', required=True)
    args = parser.parse_args()
    wanted = set(args.bases.split(','))
    for path in args.evidence:
        assert (ROOT / path).is_file()
    annotations = read_jsonl(OUT / 'cohort/manual_annotations.jsonl')
    pending = []
    for item in annotations:
        if item['base_problem_id'] not in wanted:
            continue
        assert not item.get('candidate_excluded')
        folder = OUT / 'counterfactual_assets' / item['base_problem_id']
        if item.get('asset_revision', 1) > 1:
            folder /= f"attempt_{item['asset_revision']:02d}"
        meta = read_json(folder / 'metadata.json')
        assert meta['pixel_validation']['passed'] and meta['native_generation_query_exact']
        assert not meta['A_B_overlap'] and meta['layout_exact']
        native = np.asarray(Image.open(ROOT / meta['paths']['OO']).convert('RGB'))
        _, rows, cols = meta['prompt_metadata']['visual_mapping']['merged_grid_shape']
        height, width = native.shape[:2]
        for fact, info in meta['irrelevant_mapping'].items():
            if info.get('unavailable'):
                continue
            pixels = []
            for index in info['local_positions']:
                row, col = divmod(index, cols)
                pixels.append(native[row*height//rows:(row+1)*height//rows, col*width//cols:(col+1)*width//cols].reshape(-1, 3))
            colors = np.unique(np.concatenate(pixels), axis=0)
            assert colors.min() >= 250, (item['base_problem_id'], fact, 'Control needs separate visual review')
            info.update(manual_review='pass: blank near-white background, no visual fact; source reviewed', background_colors_rgb=colors.tolist())
        meta['irrelevant_controls_validated'] = all(not v.get('unavailable') and v.get('manual_review', '').startswith('pass') for v in meta['irrelevant_mapping'].values())
        meta.update(manual_asset_review='pass', manual_roi_review='pass', edits_reviewed=True, manual_review_evidence=args.evidence)
        item.update(edits_reviewed=True, token_map_validated=True, asset_metadata=str((folder / 'metadata.json').relative_to(ROOT)))
        pending.append((folder / 'metadata.json', meta))
    assert len(pending) == len(wanted)
    for path, meta in pending:
        write_json(path, meta)
    write_jsonl(OUT / 'cohort/manual_annotations.jsonl', annotations)
    print('eligible', sum(a['edits_reviewed'] and not a.get('candidate_excluded') for a in annotations))


if __name__ == '__main__':
    main()
