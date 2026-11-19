"""Prospective source/geometry grouping before controlled primary generation."""
import hashlib
import json
from collections import defaultdict,Counter
from scripts.stage6a.inventory import OUT
from scripts.stage6a.review_candidates import table
from scripts.stage6a.prepare_candidates import write
from visual_reasoning.stage6a.splits import connected_groups,assign_split


GEOMETRY_GROUPS = {
 'round_solid_volume':['mathverse_651','mathverse_645','mathverse_644','mathverse_690','mathverse_641','mathverse_654','mathverse_691'],
 'sphere_surface_area':['mathverse_664'],
 'pipe_or_drilled_solid':['mathverse_692','mathverse_639','mathverse_698'],
 'prism_surface_area':['mathverse_707','mathverse_703','mathverse_715','mathverse_714','mathvision_754'],
 'prism_volume':['mathverse_728','mathverse_735','mathverse_733','mathverse_724'],
 'curved_solid_surface_area':['mathverse_673','mathvision_3004'],
 'pyramid_surface_area':['mathverse_709'],
 'pythagorean_triangle':['mathverse_638','mathverse_635','mathverse_431','mathverse_745','mathvista_386','mathvista_160','mathvista_238'],
 'right_triangle_trigonometry':['mathverse_380','mathverse_385','mathvision_2980','mathvista_678','mathvista_897','mathvista_665','mathvista_333'],
 'angle_sums_and_parallel_lines':['mathverse_773','mathverse_779','mathverse_774','mathvision_1041','mathvision_1089','mathvista_242','mathvista_866'],
 'circle_radius_isosceles':['mathverse_786','mathverse_771','mathverse_777'],
 'similarity_area_ratio':['mathverse_756','mathvision_2912','mathvision_2885','mathvista_206'],
 'tangent_chord_cyclic_geometry':['mathvision_3006','mathvision_208','mathvista_757','mathvista_726','mathvista_684','mathvista_951','mathvista_283','mathvista_804','mathvista_114'],
 'orthogonal_polygon_perimeter':['mathvision_1678','mathvision_2718','mathvision_2427','mathvision_2512'],
 'parallel_rectangular_area_partition':['mathvision_2407','mathvision_2530','mathvision_1529','mathvision_2525','mathvision_2504'],
 'coordinate_triangle_quadrilateral_area':['mathvision_2546','mathvision_2950','mathvision_3020','mathvision_2958'],
 'triangle_altitude_projection':['mathvision_2910','mathvision_3023','mathvista_716','mathvista_408'],
 'triangle_or_rectangle_congruence':['mathvision_342','mathvision_1186','mathvision_1735','mathvision_802'],
 'parallelogram_perimeter':['mathvista_737','mathvista_822'],
 'equal_lengths_linear_equations':['mathvision_2986','mathvista_819','mathvista_781','mathvista_236'],
}


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    dest=OUT/'cohort/prospective_source_split.json'
    if dest.exists():raise FileExistsError(dest)
    identities={r['base_id']:r for r in load(OUT/'audit/source_identity_catalog.jsonl')}
    definitions=json.loads((OUT/'config/primary_c1_v2_construction_definitions.json').read_text())
    accepted={r[0] for r in definitions['c1']}
    rows=[{**r,'cohort':'C1','phase':'primary'} for r in load(OUT/'cohort/primary_c1_review_queue.jsonl') if r['base_id'] in accepted]
    rows+=load(OUT/'cohort/c2_primary_base_manifest.jsonl')
    rows+=[r for r in load(OUT/'c3_object_stress/pope_manifest.jsonl') if r['phase']=='primary']
    rows+=load(OUT/'cohort/c4_primary_manifest.jsonl')
    source_rows={r['base_id']:r for r in rows}
    families={key:family for family,keys in GEOMETRY_GROUPS.items() for key in keys}
    links=[];group_buckets=defaultdict(list);metadata=[]
    for key,identity in identities.items():
        group_buckets['pixels:'+identity['decoded_stimulus_sha256']].append(key)
    for row in rows:
        key=row['base_id'];cohort=row['cohort'];extra={}
        if cohort=='C1':
            # All TabMWP-generated table stimuli share one conservative family.
            is_table=row['dataset']=='MathVista' and (row.get('metadata',{}).get('source')=='TabMWP' or int(row['dataset_id']) in [568,718,359,651,831,205,746,144,45,928,978,948,245,801,739,517,471,121,323])
            family='tabmwp_table_generator' if is_table else families.get(key,'unique_geometry:'+key)
        elif cohort=='C2':
            source=table(row['arrow_path']);extra={k:source.column(k)[row['arrow_row']].as_py() for k in ['ucsf_document_id','ucsf_document_page_no']}
            group_buckets['document:'+extra['ucsf_document_id']].append(key)
            if key in ['docvqa_5611','docvqa_4930']:family='power_delivery_contract_form'
            elif key in ['docvqa_6351','docvqa_6775','docvqa_15351','docvqa_7014']:family='fax_cover_sheet_family'
            else:family='document_layout:'+extra['ucsf_document_id']
        else:
            family='coco_image:'+str(row['image_id'])
            group_buckets[family].append(key)
        group_buckets['template:'+family].append(key)
        metadata.append(dict(base_id=key,cohort=cohort,dataset=row['dataset'],template_geometry_family=family,
            question_family='COCO detailed native description' if cohort=='C4' else 'POPE object-presence question' if cohort=='C3' else 'same-image four-cell factorial' if cohort=='C2' else row['question'],**extra))
    for values in group_buckets.values():links.extend((values[0],v) for v in values[1:])
    # Conservative grouping of every flagged near-image pair avoids requiring an
    # assertion that visually similar pixels are semantically identical.
    for pair in load(OUT/'audit/perceptual_duplicate_candidates.jsonl'):links.append((pair['left'],pair['right']))
    groups=connected_groups(identities,links);assignments={};group_records=[]
    for members in groups:
        live=[k for k in members if k in source_rows]
        if not live:continue
        historical=any(identities[k]['phase']=='historical' for k in members)
        validation=any(identities[k]['phase'] in ['mechanics','pilot'] for k in members)
        group_id='source_group_'+hashlib.sha256('|'.join(members).encode()).hexdigest()[:16]
        split='historical_overlap' if historical else 'validation_overlap' if validation else assign_split(group_id)
        for key in live:assignments[key]=dict(group_id=group_id,split=split)
        group_records.append(dict(group_id=group_id,split=split,members=members,primary_members=live))
    assert len(assignments)==len(source_rows)
    assert not [k for k,v in assignments.items() if v['split'].endswith('_overlap')], 'Repair source overlap before primary generation'
    metadata=[{**r,**assignments[r['base_id']],**{k:identities[r['base_id']][k] for k in ['decoded_stimulus_sha256','phash','source_image_id']}} for r in metadata]
    report=dict(seed=60972,assignments=assignments,groups=group_records,
        inputs=['source image identities','reviewed geometry/template families','source documents','fixed split seed'],
        model_outcomes_used=False,attention_or_causal_data_used=False,
        known_limits=['Generic POPE wording, COCO description instruction, and factorial prompt structure are task-wide constants; stimulus families are grouped, but unseen-task-template generalization is not claimed.',
          'Historical exact/perceptual images are excluded; an exhaustive semantic-template taxonomy of all historical experiments is unavailable.',
          'Perceptual grouping is conservative and may group distinct images; no flagged pair crosses splits.'],
        composition=dict(Counter(r['cohort']+':'+r['split'] for r in metadata)))
    dest.write_text(json.dumps(report,indent=2)+'\n');write(OUT/'cohort/source_template_groups.jsonl',metadata)
    print(json.dumps(report['composition'],indent=2))


if __name__=='__main__':main()
