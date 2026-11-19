"""Validate native numeric readout and edited alternative boundaries on CPU."""
import json
from pathlib import Path
from transformers import AutoTokenizer
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write
from visual_reasoning.stage5a.annotation import exact_semantic_candidate
from visual_reasoning.stage6a.readouts import readout_matches


def main():
    config=json.loads((OUT/'config/stage6a_config.json').read_text())
    tokenizer=AutoTokenizer.from_pretrained(config['model_checkpoint'],local_files_only=True)
    rows=[json.loads(s) for s in (OUT/'c1_diagram_stress/intact_local_claim_review.jsonl').read_text().splitlines()]
    records=[]
    for row in rows:
        if row['membership_status']!='eligible':continue
        path=Path(row['full_prior_history_artifact']);raw=json.loads(path.read_text())['raw_decoded_response']
        tokens=[json.loads(s) for s in (path.parent/'tokens.jsonl').read_text().splitlines()]
        matches=readout_matches(row['claim_quote'],row['readout'])
        assert matches, row['base_id']
        occurrence=row.get('readout_occurrence',0);match=matches[occurrence]
        start=row['char_start']+match.start();end=row['char_start']+match.end()
        assert raw[start:end]==row['readout']
        exact=exact_semantic_candidate(tokens=tokens,match_start=start,match_end=end,
            counterfactual_value=row['target']['counterfactual'],tokenizer=tokenizer)
        records.append(dict(base_id=row['base_id'],event_id=row['event_id'],source_id='T',
            native_readout=row['readout'],counterfactual_readout=row['target']['counterfactual'],
            readout_char_start=start,readout_char_end=end,
            selection='First exact numeral occurrence within explicitly reviewed source-linked claim unless review specifies otherwise; all alternative occurrences retained for audit.',
            occurrences_in_reviewed_claim=[dict(char_start=row['char_start']+m.start(),char_end=row['char_start']+m.end()) for m in matches],
            local_visual_correctness=row['local_visual_correctness'],numeric_label_correctness=row['numeric_label_correctness'],
            numeric_readout_is_error_token=row['numeric_label_correctness']=='INCORRECT',
            semantic_error_may_lie_outside_numeric_readout=row['local_visual_correctness']=='INCORRECT' and row['numeric_label_correctness']=='CORRECT',
            error_readout_scope='Numeric source contrast only; a wrong geometric role requires separate error-token identification before error-rescue claims.',
            semantic_role_warning=row['local_claim_note'],claim_quote=row['claim_quote'],
            **exact,original_generation_artifact=str(path),scores_computed=False))
    write(OUT/'c1_diagram_stress/native_readout_boundaries.jsonl',records)
    report=dict(status='PASS',eligible_reviewed_bases=len(records),native_utf8_and_token_boundaries_exact=True,
        alternative_text_round_trip_exact=True,native_prefix_preserved=True,models_loaded_on_GPU=False,
        causal_or_candidate_scores_computed=False,
        multiple_same_value_occurrences=sum(len(r['occurrences_in_reviewed_claim'])>1 for r in records),
        interpretation='Boundary validation only. A numeric contrast can coexist with an incorrect geometric source role, which remains separately labeled.')
    (OUT/'audit/c1_native_readout_boundary_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
