"""Freeze the reviewed prospective cohort and explicit limitations before inference."""
import math
from collections import Counter
from datetime import datetime, timezone
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl, sha


def main():
    bases=read_jsonl(OUT/'cohort/proposed_base_manifest.jsonl')
    rows=read_jsonl(OUT/'cohort/proposed_native_manifest.jsonl')
    historical=read_jsonl(ROOT/'outputs/stage6a/audit/source_identity_catalog.jsonl')
    historical_matches=[]
    for b in bases:
        x=b['identity']
        matches=[r['base_id'] for r in historical if x['decoded_stimulus_sha256']==r['decoded_stimulus_sha256'] or (
            abs(math.log((x['width']/x['height'])/(r['width']/r['height'])))<=.15 and
            (int(x['phash'],16)^int(r['phash'],16)).bit_count()<=4)]
        if matches:historical_matches.append(dict(base_id=b['base_id'],historical=matches))
    assert not historical_matches,historical_matches
    cert=read_json(OUT/'annotations/source_edit_review.json')
    assert len(cert)==55 and len(bases)==67
    for r in cert:
        for name,digest in r['image_sha256'].items():assert sha(OUT/'assets'/r['base_id']/name)==digest
    # All ten processed contact sheets were manually inspected in full.
    write_json(OUT/'annotations/processed_source_review.json',dict(status='PASS',pairs=55,
        review='Full actual-processor-pixel sheets00–09 manually inspected: original, T/X original-value sham and semantic replacement remain readable; field identities and punctuation preserved.',
        sheets={f'review/processed_batch_{i:02d}.png':sha(OUT/'review'/f'processed_batch_{i:02d}.png') for i in range(10)},
        image_preprocessing_sha256=sha(OUT/'config/image_preprocessing.json'),causal_or_native_outputs_used=False),freeze=True)
    by_id={b['base_id']:b for b in bases}
    for b in bases:
        b['source_separation_valid']=not bool(b['source_map_overlaps'].get('T_X'))
        b['source_separation_rule']='Any shared T/X token prevents independent-source dominance/wrong-source/stale-source classification. Retain effects as overlapping-source diagnostics, never delete shared tokens to manufacture independence.'
        groups=b['local_source_groups']
        if 'I' in groups and any(set(groups['I'])&set(groups.get(k,[])) for k in ['T','X']):
            b['invalid_irrelevant_group']=groups.pop('I')
            b['irrelevant_audit']={'unavailable':'Pixel-matched sham overlaps a causal source after visual-token projection; keep pixel sham, do not use it as an independent source-suppression control.'}
    for r in rows:
        b=by_id[r['base_id']]
        for key in ['local_source_groups','source_separation_valid','source_separation_rule','irrelevant_audit']:
            r[key]=b[key]
        r['image_sha256']=sha(r['image_path']) if r.get('image_path') else None
        if r['condition']=='unrelated':
            donor=by_id[r['unrelated_donor']]
            assert donor['split']==r['split']
            r['unrelated_review']='Donor full source image previously reviewed; it is a different image/question source. This does not certify that all generic labels or contextual cues are absent. Global visual suppression disqualifies a strict prior-fill label when other visual information remains causal.'
        if r['condition'] in ['mask','strong','unrelated','no_image']:
            r['answer_scope']='Original task truth for source-consistency only; unavailable evidence can justify abstention. Do not treat original-answer mismatch as an objectively wrong observed visual fact without semantic review.'
    # Discovery images first; the largest discovery input first validates resource scale.
    rows.sort(key=lambda r:(r['split']!='discovery',-math.prod(r.get('image_grid_thw',[1,1,1])),r['base_id'],['intact','strong','mask','sham_mask','unrelated','no_image','aba'].index(r['condition'])))
    split=read_json(OUT/'cohort/proposed_discovery_confirmation_split.json')
    write_json(OUT/'cohort/discovery_confirmation_split.json',split,freeze=True)
    write_jsonl(OUT/'cohort/base_manifest.jsonl',bases,freeze=True)
    manifests={}
    for name, selected in [('native_manifest',rows),('discovery_native_manifest',[r for r in rows if r['split']=='discovery']),('confirmation_native_manifest',[r for r in rows if r['split']=='confirmation'])]:
        path=OUT/'cohort'/(name+'.jsonl');write_jsonl(path,selected,freeze=True);manifests[str(path.relative_to(ROOT))]=sha(path)
    source_exclusions=read_json(OUT/'annotations/source_review_exclusions.json')
    excluded=[dict(base_id=k,stage='source_review',reason=v) for k,v in source_exclusions.items()]
    excluded += [dict(base_id=r['base_id'],stage='object_review',reason=r['review']) for r in read_json(OUT/'annotations/object_source_review.json') if r['status']=='exclude']
    write_jsonl(OUT/'cohort/exclusions.jsonl',excluded,freeze=True)
    write_json(OUT/'cohort/screening_accounting.json',dict(candidate_caps=dict(C1=240,C2=96,C3=96),
        reviewed_source_images=dict(MathVista=36,MathVision=48,MathVerse=24,DocVQA=32,POPE_COCO2014=96),
        accepted_bases=dict(Counter(b['cohort'] for b in bases)),retained_conditions=dict(Counter(r['condition'] for r in rows)),
        stopping='Fixed source-only bank frozen before any fresh model output. C2 accepted-source cap24 reached. C1 initial reviewed pool produced31 paired editable fields; remaining finite reserves are unused/unreviewed, not counted as failed semantic screens. No replenishment after model outcomes.',
        C1_scope='27 MathVista TabMWP tables and4 MathVision diagrams; no fresh MathVerse base passed this paired-field authoring slice. Report this limitation; do not claim broad diagram generalization.',
        objects='96 finite candidates screened;14 provisional,2 ambiguous negative images excluded by full-image review;2 positive masks provide only partial evidence removal.'),freeze=True)
    write_json(OUT/'audit/split_integrity.json',dict(status='PASS',base_counts=dict(Counter(b['split'] for b in bases)),
        near_image_groups=read_json(OUT/'audit/new_source_overlap.json')['pairs'],historical_matches=[],
        historical_catalog_sha256=sha(ROOT/'outputs/stage6a/audit/source_identity_catalog.jsonl'),
        donors_within_split=True,template_generalization='Requires separate grouped feasibility folds; not established by base split.'),freeze=True)
    write_json(OUT/'config/event_sampling_rules.json',dict(primary='First mechanically valid independently reviewed explicit demanded-T claim per native availability trace; preserve abstention, conditional, question-provided and no-explicit-claim exclusions.',
        failure_screen='At most one additional earliest objectively incorrect demanded-T visual claim per trace, if distinct from its primary event; selected without causal/passive scores.',
        aba='First independently reviewed T claim, intervening X claim, and first subsequent T claim with the complete preceding source history checked. If sequence not realized, preserve underidentification.',
        binding='First exact role/entity contrast with value fixed when an explicit native binding span exists; otherwise mark unavailable.',
        w8='Every discovery primary event; confirmation bases whose SHA256(base_id) integer mod3 equals0, T and primary X/P only.',
        supplementary_all_visual='G = all visual tokens, W2 only, same pre-WO nonrenormalized source suppression; global visual support disqualifies strict prior-fill when unannotated sources could otherwise be missed. G is not an independent localized source identity.',
        threshold_blinding='Numeric rule selection uses discovery scores only. Confirmation event annotation may use native text, never causal/hidden-state features. No confirmation scores before threshold freeze.'),freeze=True)
    write_json(OUT/'audit/cohort_freeze.json',dict(status='PASS',frozen_at=datetime.now(timezone.utc).isoformat(),bases=len(bases),native_conditions=len(rows),
        native_manifest_sha256=manifests,source_review_sha256=sha(OUT/'annotations/source_edit_review.json'),
        processed_review_sha256=sha(OUT/'annotations/processed_source_review.json'),
        split_sha256=sha(OUT/'cohort/discovery_confirmation_split.json'),
        base_manifest_sha256=sha(OUT/'cohort/base_manifest.jsonl'),
        overlapping_T_X_bases=sum(not b['source_separation_valid'] for b in bases),
        independent_source_limitations_preserved=True,selection_used_model_outputs=False),freeze=True)
    print('Cohort frozen:',len(bases),'bases;',len(rows),'native conditions;',Counter(b['split'] for b in bases))


if __name__=='__main__':main()
