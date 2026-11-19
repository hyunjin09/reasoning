"""Apply frozen benchmark equivalence only after extraction decisions are sealed."""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from prepare_block0 import ROOT, digest, save
from visual_reasoning.stage8b.v2_scoring import equivalent, score_answer


def grade_extracted(answer, row):
    # Same final comparison as the immutable v2 adapter; only extraction differs.
    if answer is None:
        return None
    if row['options']:
        letters=[chr(65+i) for i in range(len(row['options']))]
        letter=answer.strip().strip('().').upper()
        if letter in letters:
            return letter == row['answer']
        matches=[letters[i] for i,value in enumerate(row['options']) if equivalent(answer,value) is True]
        return matches[0] == row['answer'] if len(matches)==1 else None
    return equivalent(answer,row['answer'])


def main():
    automatic_path=ROOT/'audit'/'automatic_extraction_freeze.json'
    manual_path=ROOT/'audit'/'manual_extraction_freeze.json'
    automatic=json.loads(automatic_path.read_text())
    manual=json.loads(manual_path.read_text())
    assert manual['ground_truth_excluded']
    assert manual['automatic_freeze_sha256']==digest(automatic_path)
    auto_by_id={r['item_id']:r for r in automatic['rows']}
    manual_by_id={r['item_id']:r for r in manual['rows']}
    frozen=json.loads((ROOT/'audit'/'input_freeze.json').read_text())
    for key in ['code/visual_reasoning/stage8b/v2_scoring.py','code/visual_reasoning/stage8b/scoring.py',frozen['prior_outcomes']]:
        assert digest(key)==frozen['source_sha256'][key]
    # New truth is loaded only after both extraction freezes above exist.
    manifest={r['item_id']:r for r in map(json.loads,Path(frozen['source_manifest']).read_text().splitlines())}
    cohort=json.loads((ROOT/'stage8b_block0_cohort_manifest.json').read_text())['rows']
    prior={r['item_id']:r for r in json.loads(Path(frozen['prior_outcomes']).read_text())['rows']}
    prior_auto={r['item_id']:r for r in json.loads(Path('outputs/stage8b/v2/analysis/census_snapshot_v1.json').read_text())['rows']}
    rows=[];adoptions=[]
    for source in cohort:
        item=source['item_id']; native=Path(source['receipt']).parent
        generation=json.loads((native/'generation.json').read_text())
        text=generation['raw_decoded_response']
        if item in prior:
            adopted=prior[item]['answer'].copy();auto=prior_auto[item]['answer']
            correct=adopted['correct'];provenance=frozen['prior_outcomes']
            reason='Preserved reviewed outcome from original32 audit' if correct is None else None
            manual_record=None
        else:
            auto=auto_by_id[item]
            assert digest(native/'generation.json')==auto['generation_sha256']
            rescored=score_answer(text,manifest[item])
            for key in ['extracted','span','scope','method','status']:
                assert rescored[key]==auto[key],(item,key)
            assert rescored['correct']==grade_extracted(auto['extracted'],manifest[item])
            manual_record=manual_by_id.get(item)
            adopted=manual_record.copy() if manual_record else auto.copy()
            if manual_record:
                assert manual_record['generation_sha256']==auto['generation_sha256']
                if manual_record['span'] is not None:
                    a,b=manual_record['span'];assert text[a:b]==manual_record['literal'],item
            correct=grade_extracted(adopted['extracted'],manifest[item])
            reason=(adopted.get('rationale','No unambiguous extracted answer') if adopted['extracted'] is None
                    else 'Unsupported or non-unique equivalence under the frozen local adapter') if correct is None else None
            provenance=str(manual_path if manual_record else automatic_path)
        label='unresolved' if correct is None else 'correct' if correct else 'wrong'
        span=adopted.get('span')
        rows.append(dict(item_id=item,family_id=source['family_id'],order=source['order'],
            benchmark_label=label,correct=correct,extracted_answer=adopted['extracted'],
            extraction_method=adopted.get('method'),extraction_scope=adopted.get('scope'),
            source_span_start=span[0] if span else None,source_span_end=span[1] if span else None,
            source_span_text=text[span[0]:span[1]] if span else None,
            ambiguity_flag=adopted['extracted'] is None,unresolved_reason=reason,
            automatic_extracted_answer=auto['extracted'],automatic_method=auto.get('method'),
            automatic_span=json.dumps(auto.get('span')),manual_reviewed=manual_record is not None or item in prior,
            prior32_preserved=item in prior,extraction_provenance=provenance,
            generation_sha256=digest(native/'generation.json'),receipt_sha256=source['receipt_sha256'],
            grader='frozen qwen_1e-6_bounded_numeric',external_judge_used=False))
        adoptions.append(dict(item_id=item,automatic=auto,adopted=adopted,correct=correct,benchmark_label=label))
    assert len(rows)==256 and sum(r['prior32_preserved'] for r in rows)==32
    assert {k:sum(r['benchmark_label']==k for r in rows[:32]) for k in ['correct','wrong','unresolved']} == dict(correct=12,wrong=16,unresolved=4)
    pd.DataFrame(rows).to_csv(ROOT/'stage8b_block0_outcome_table.csv',index=False)
    save(ROOT/'audit'/'outcome_scoring_provenance.json',dict(at=datetime.now(timezone.utc).isoformat(),
        automatic_extraction_sha256=digest(automatic_path),manual_extraction_sha256=digest(manual_path),
        adapter_sha256=digest('code/visual_reasoning/stage8b/v2_scoring.py'),
        implementation_sha256=digest(__file__),manual_freezer_sha256=digest('scripts/stage8b/freeze_block0_manual_extraction.py'),
        original32_preserved=True,automatic_comparison_parity_items=224,extraction_preceded_new_truth_comparison=True,
        limitation='Local deterministic/manual extraction does not reproduce upstream GPT-4o fallback.',rows=adoptions))
    print('Outcome table frozen: 256 rows, original32 preserved, 224 automatic-comparison parity checks passed.')


if __name__ == '__main__':
    main()
