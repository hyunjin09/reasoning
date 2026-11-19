"""Publish source-native region geometry without passive/causal measurements."""
import json
from collections import Counter,defaultdict
from pathlib import Path
from scripts.stage6a.inventory import OUT,allowed
from scripts.stage6a.prepare_candidates import write
from scripts.stage6a.source_annotations import secondary_sources


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    inventory=json.loads((OUT/'cohort/dataset_inventory.json').read_text())
    coco=next(r for r in inventory['datasets'] if r['dataset']=='COCO2014')
    annotation_path=allowed(Path(coco['instance_annotations']));data=json.loads(annotation_path.read_text())
    names={c['id']:c['name'] for c in data['categories']};annotations=defaultdict(list)
    for ann in data['annotations']:annotations[ann['image_id']].append(ann)
    # Source-base schemas differ (Arrow metadata vs authored fields). Event
    # manifests are the normalized interface already validated by acquisition.
    rows=[]
    for name in ['c1_primary_v2','c2_primary','c3_primary_v2']:
        rows.extend(r for r in load(OUT/f'cohort/{name}_manifest.jsonl') if r['condition'] in ['intact','AR'])
    for name in ['c4_primary','c4_extension']:
        path=OUT/f'cohort/{name}_manifest.jsonl'
        if path.exists():rows+=load(path)
    regions=[];groups=[];seen=set();secondary=secondary_sources()
    for row in rows:
        key=row['base_id']
        if key in seen:continue
        seen.add(key);cohort=row['cohort']
        if cohort in ['C1','C2']:
            for source in [row['target']]+row.get('other_sources',[])+secondary.get(key,[]):
                regions.append(dict(base_id=key,cohort=cohort,source_id=source['source_id'],
                    entity=source['entity'],geometry_type='reviewed_semantic_rectangle',
                    xyxy=source['roi'],image_path=row['image_path'],
                    provenance=source.get('annotation_provenance','Pre-generation full-source and enlarged ROI-crop review'),
                    annotation_scope=source.get('annotation_scope','Pre-generation construction'),
                    truth_value=row['answers'][0 if source['source_id']=='T' else 1] if cohort=='C2' else source.get('value'),counterfactual_value=source.get('counterfactual'),
                    availability='Source image; condition-specific degradation/masks recorded in manifests',
                    roi_mapping_artifact='regions/controlled_roi_maps.jsonl'))
            continue
        categories=defaultdict(list)
        target_ids={a['id'] for a in row.get('target_annotations',[])} if cohort=='C3' and row['present'] else set()
        for ann in annotations[row['image_id']]:
            category=names[ann['category_id']]
            source_id='T' if ann['id'] in target_ids else f"COCO_INSTANCE:{ann['id']}"
            categories[category].append(source_id)
            regions.append(dict(base_id=key,cohort=cohort,image_id=row['image_id'],
                source_id=source_id,category=category,annotation_id=ann['id'],
                geometry_type='COCO_polygon' if isinstance(ann['segmentation'],list) else 'COCO_RLE',
                bbox_xywh=ann['bbox'],segmentation=ann['segmentation'],iscrowd=ann['iscrowd'],
                annotated_area=ann['area'],image_path=row['image_path'],
                provenance=str(annotation_path),
                geometry_limit='COCO instance extent; no guarantee that mask removes all contextual category information',
                roi_mapping_artifact='regions/controlled_roi_maps.jsonl' if cohort=='C3' and source_id=='T' else 'Source segmentation saved for future projection; no token footprint fabricated'))
        groups.append(dict(base_id=key,cohort=cohort,image_id=row['image_id'],
            category_source_groups={f'COCO_CATEGORY:{cat}':ids for cat,ids in categories.items()},
            queried_category=row.get('category'),queried_object_present=row.get('present'),
            absent_query_source_id='QUERY_ABSENT:'+row['category'] if cohort=='C3' and not row['present'] else None,
            absent_query_has_target_roi=False if cohort=='C3' and not row['present'] else None,
            annotation_missing_object_rule='Manually supported objects without source instances require separate localization; do not invent coordinates.'))
    write(OUT/'regions/ground_truth_rois.jsonl',regions);write(OUT/'regions/coco_category_source_groups.jsonl',groups)
    # The optional learned partition was not required or used; an explicit empty
    # artifact distinguishes omission from an unfinished export.
    write(OUT/'regions/optional_semantic_regions.jsonl',[])
    report=dict(status='SOURCE_GEOMETRY_EXPORTED',bases=len(seen),regions=len(regions),
        by_cohort=dict(Counter(r['cohort'] for r in regions)),
        geometry_types=dict(Counter(r['geometry_type'] for r in regions)),
        C1=f'One reviewed target T per constructed base, plus {sum(len(values) for values in secondary.values())} reviewed secondary numeric regions across all {len(secondary)} retained C1 bases. Source annotations use mixed granularity: coordinate/expression components and whole expressions or table values. Numeric table keys are cell identity metadata. Region counts are not independent fact counts; surrounding geometry is not exhaustively localized.',
        C2='Two independently reviewed T/X source fields per document family.',
        C3='Actual queried-object polygon for present cases; source object instances for distractors; no absent-target ROI.',
        C4='COCO source instances and category-to-instance groups; multi-instance category claims remain spatially coarse.',
        optional_learned_partition='Not run; ground-truth instance geometry is available. No DINO/PCA/attention processing.',
        preprocessing='All geometry is in native source pixels; processed grids and exact prompt visual indices are stored per generation.',
        condition_caveats=['No-image has no visual tokens.',
            'Original ROI coordinates on unrelated images are placebos, not evidence that the original semantic object survives.',
            'RLE segmentations are preserved natively; this export does not pretend a decoded polygon or token mapping exists.'])
    (OUT/'regions/region_provenance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
