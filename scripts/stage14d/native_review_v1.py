"""Persist manual full-trace reviews against saved token IDs; never infer labels."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from tokenizers import Tokenizer
from scripts.stage14d.prepare_technical_v1 import ROOT, lines, save, sha
from scripts.stage14d.design import fingerprint
from scripts.stage14d.token_offsets_v1 import valid_boundaries_for_offsets


def record(reviews, version='v1'):
    assert version in {'v1', 'v2', 'v3'}
    work = {r['task_id']: r for r in lines(ROOT/'anchors/native_trace_annotation_worklist_v1.jsonl')}
    cfg = json.loads((ROOT/'spec/pinned_model_revisions_and_recipes.json').read_text())
    tokenizers = {}
    for review in reviews:
        assert review['entire_native_trace_manually_reviewed'] is True
        w = work[review['task_id']]
        item = w['task_id'].split('_')[1]
        model = w['model']
        source_path = ROOT/'annotation/source_review_v1'/f'{item}.json'
        source_index = ROOT/'audit/source_review_adjudication_index_v1.json'
        if source_index.exists():
            override = json.loads(source_index.read_text())['active_overrides'].get(item)
            if override:
                source_path = Path(override['path'])
                assert sha(source_path) == override['sha256']
        source = json.loads(source_path.read_text())
        assert source['status'] == 'SOURCE_VALID_VALUE_FREE'
        for key in ['generation', 'input', 'result']:
            assert sha(w[key]) == w[key+'_sha256']
        g = json.loads(Path(w['generation']).read_text())
        raw, ids = g['raw_decoded_response'], g['generated_token_ids']
        if model not in tokenizers:
            tokenizers[model] = Tokenizer.from_file(cfg['models'][model]['model']['checkpoint']+'/tokenizer.json')
        tok = tokenizers[model]
        assert tok.decode(ids, skip_special_tokens=True) == raw
        requested = [0]
        for value in [review[k] for k in ['E0', 'E1', 'E2', 'earliest']] + review['additional_spans']:
            if value is not None:
                q = value if isinstance(value, str) else value['quote']
                a = raw.index(q) if isinstance(value, str) else value['char_start']
                requested.extend([a, a + len(q)])
        if not review['fallback']:
            requested.append(raw.index(review['boundary']))
        valid = valid_boundaries_for_offsets(tok, ids, raw, requested)

        def event(value):
            if value is None:
                return None
            q = value if isinstance(value, str) else value['quote']
            a = raw.index(q) if isinstance(value, str) else value['char_start']
            b = a + len(q)
            assert raw[a:b] == q
            lo = max(n for n, c in valid if c <= a)
            hi = next(n for n, c in valid if c >= b)
            return dict(quote=q, char_start=a, char_end=b, token_start=lo, token_end=hi)

        events = {k: event(review[k]) for k in ['E0', 'E1', 'E2', 'earliest']}
        if review['fallback']:
            assert review['fallback_reason']
            n, c = 0, 0
        else:
            b = raw.index(review['boundary'])
            n, c = max((n, c) for n, c in valid if c <= b)
            assert not raw[c:b].strip(), 'Token boundary loses non-whitespace; manual repair required'
            assert events['earliest'] and c <= events['earliest']['char_start']
        prefix = tok.decode(ids[:n], skip_special_tokens=True)
        assert prefix == raw[:c]
        cap = 81920 if model == 'T' else 32768
        assert len(g['prompt_token_ids']) + n + cap < 128000
        out = dict(at=dt.datetime.now(dt.timezone.utc).isoformat(),
            state='FULL_NATIVE_REVIEW_COMPLETE', item_id=item, model=model,
            family_id=w['family_id'], original_receipts=w,
            source_review=str(source_path), source_review_sha256=sha(source_path),
            events=events, observed_repeats_or_contradictions=[event(q) for q in review['additional_spans']],
            anchor_token_index=n, anchor_char_index=c, prefix_text=prefix,
            prefix_generated_token_ids=ids[:n], prefix_ids_sha256=fingerprint(ids[:n]),
            prefix_text_sha256=hashlib.sha256(prefix.encode()).hexdigest(),
            full_native_ids_sha256=fingerprint(ids), full_native_char_count=len(raw),
            offset_implementation='scripts/stage14d/token_offsets_v1.py',
            offset_implementation_sha256=sha('scripts/stage14d/token_offsets_v1.py'),
            source_neutral_prefix_review='PASS',
            reviewer='main agent; no independent inter-rater claim',
            scientific_intervention_outcomes_seen=False, **review)
        save(ROOT/f'annotation/native_review_{version}'/f'{w["task_id"]}.json', out)
        print(w['task_id'], 'anchor', n, 'tokens', review['evidence_state'])
