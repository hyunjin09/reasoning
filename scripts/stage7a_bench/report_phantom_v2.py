"""Report the completed Phantom pair without implying whole-stage completion."""
from collections import Counter
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.native_yield_v2 import indexed, summarize_condition, paired_comparison

OUT = ROOT / 'outputs/stage7a_bench_v2'
RUN = 'phantom_native_01'


def main():
    native = OUT / 'native_screen/generations' / RUN
    # This report is a completed benchmark result, never a partial extrapolation.
    for path in (native / 'run_summary.json', OUT / 'raw' / RUN / 'run_summary.json'):
        if not path.exists() or not read_json(path)['completed']:
            raise RuntimeError('Phantom generation has not completed successfully')
    freeze = read_json(OUT / 'cohort/sample_freeze.json')['native_screen']
    groups, summaries, sources, verified = {}, {}, {}, []
    for condition in ('silent_no_image', 'explicit_guess'):
        path = OUT / 'cohort/benchmark_manifests' / f'phantom_0_{condition}_native.jsonl'
        manifest = read_jsonl(path)
        assert len(manifest) == 200
        matches = [f for f in freeze.values() if f['sha256'] == sha(path) and f['count'] == 200]
        assert len(matches) == 1
        review_path = OUT / 'native_screen/manual_reviews' / f'{RUN}__{condition}.jsonl'
        reviews = read_jsonl(review_path)
        labels = indexed(reviews)
        if set(labels) != {r['event_id'] for r in manifest}:
            raise RuntimeError('Phantom full-response semantic review is incomplete')
        results = []
        for row in manifest:
            example = native / 'examples' / row['event_id']
            result = read_json(example / 'result.json')
            meta = read_json(example / 'input.json')
            review = labels[row['event_id']]
            assert read_json(example / 'manifest_row.json') == row
            assert row['no_image'] and meta['no_image'] and not meta['visual_token_indices']
            assert meta['image_grid_thw'] is None and meta['prompt'] == row['prompt']
            assert review['manifest_sha256'] == sha(path)
            assert review['generation_sha256'] == result['generation_sha256'] == sha(example / 'generation.json')
            assert result['tokens_sha256'] == sha(example / 'tokens.jsonl')
            assert review['final_correctness'] is None and review['causal_state'] is None
            verified.append(dict(event_id=row['event_id'], input_sha256=sha(example / 'input.json'),
                result_sha256=sha(example / 'result.json'), generation_sha256=result['generation_sha256'],
                tokens_sha256=result['tokens_sha256'], no_image_verified=True))
            results.append(result)
        groups[condition] = reviews
        summaries[condition] = summarize_condition(manifest, results, reviews)
        assert summaries[condition]['screen_complete']
        sources[str(path.relative_to(ROOT))] = sha(path)
        sources[str(review_path.relative_to(ROOT))] = sha(review_path)
    left, right = (indexed(groups[c], 'base_id') for c in ('silent_no_image', 'explicit_guess'))
    assert set(left) == set(right) and len(left) == 200
    transitions = Counter(f"{left[k]['screen_label']} → {right[k]['screen_label']}" for k in left)
    discordant = []
    for key in sorted(left):
        a, b = left[key], right[key]
        if a['unsupported_evidence_claim'] or b['unsupported_evidence_claim']:
            discordant.append(dict(base_id=key, silent_index=a['native_index'],
                silent_unsupported=a['unsupported_evidence_claim'], guess_unsupported=b['unsupported_evidence_claim'],
                silent_quote=a['evidence_quote'], guess_quote=b['evidence_quote'],
                silent_claims=a.get('claims', []), guess_claims=b.get('claims', []),
                silent_note=a['review_note'], guess_note=b['review_note']))
    pair = paired_comparison(groups['silent_no_image'], groups['explicit_guess'])
    scope = ('Completed 200-question paired behavioral screen on one frozen 4B model/seed. '
        'No actual image or factual image answer exists. Unsupported claims are not adjudicated factual errors. '
        'No source-null causality or causal PRIOR_FILL certificate is available. '
        'F5 includes uncertainty/abstention; broader caveats can concern generic factual or clinical limitations. '
        'Question categories are not independent images or proof of template independence. '
        'The overall benchmark sweep and winner selection remain unfinished.')
    report = dict(status='PHANTOM_PAIRED_SCREEN_COMPLETE_ONLY', snapshot_unix=time.time(),
        conditions=summaries, paired_comparison=pair, class_transitions=dict(transitions),
        unsupported_pairs=discordant, family_categories=dict(Counter(x['family_id'] for x in left.values())),
        model_environment=read_json(native / 'environment.json'), scope=scope,
        source_sha256=sources, raw_provenance=verified,
        reporter_sha256=sha(ROOT / 'scripts/stage7a_bench/report_phantom_v2.py'),
        primary_benchmark_selected=False, causal_states_assigned=False)
    dest = OUT / 'mirage_prior_track'
    write_json(dest / 'phantom_behavior.json', report)
    fields = [('Unsupported visual claims', 'unsupported_claim_rate'),
              ('F5 uncertainty / abstention', 'uncertainty_abstention_screen_rate'),
              ('Any caveat', 'abstention_or_caveat_rate'),
              ('Explicit/assumed guesses', 'guessed_answer_rate'),
              ('Truncated responses', 'truncation_rate'),
              ('Eligible source-based causal events', 'eligible_causal_event_rate')]
    def display(condition, field):
        r = summaries[condition][field]
        return f"{r['numerator']}/{r['denominator']} ({r['value']:.1%})" if r['value'] is not None else 'Unknown'
    lines = ['# Phantom-0 paired behavioral screen', '', scope, '',
             '| Measure | Silent no-image | Explicit no-image / guess |', '|---|---:|---:|']
    lines.extend(f'| {title} | {display("silent_no_image", field)} | {display("explicit_guess", field)} |'
                 for title, field in fields)
    lines += ['', 'Final accuracy and local factual-error accuracy are unavailable. '
        'The two conditions use exactly the same200 question IDs. Confidence is expressed text, not calibrated probability.', '',
        'Unsupported-claim pairs (full responses reviewed; quotes are excerpts):', '']
    for item in discordant:
        lines += [f"- `{item['base_id']}`: silent={item['silent_unsupported']}, guess={item['guess_unsupported']}. "
                  f"Silent: “{item['silent_quote']}” Guess: “{item['guess_quote']}”"]
    lines += ['', 'Raw counts, claim identities, transition counts, exact input/output hashes and scope qualifications: '
              '`outputs/stage7a_bench_v2/mirage_prior_track/phantom_behavior.json`.', '']
    summary_path = OUT / 'summaries/phantom_behavior_summary.md'
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text('\n'.join(lines))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    colors = ['#417da3', '#bc7438']
    for ax, (title, field) in zip(axes, fields[:2]):
        values = [summaries[c][field]['numerator'] for c in summaries]
        ax.bar(['Silent no-image', 'Explicit no-image'], values, color=colors, width=.6)
        for i, value in enumerate(values): ax.text(i, value+2, f'{value}/200', ha='center')
        ax.set_ylim(0, max(10, max(values)*1.15))
        ax.set_title(title)
        ax.set_ylabel('Responses')
        ax.spines[['top', 'right']].set_visible(False)
    fig.suptitle('Phantom-0: paired behavior, no causal source label', fontweight='bold')
    fig.text(.04, .015, 'Qwen3-VL-4B-Thinking · same 200 questions · frozen decoding/seed · no factual image answer', fontsize=9)
    fig.tight_layout(rect=(0, .06, 1, .93))
    files = {}
    for ext in ('png', 'pdf', 'svg'):
        path = OUT / 'analysis/figures' / ('phantom_paired_behavior.' + ext)
        fig.savefig(path, dpi=170, bbox_inches='tight')
        files[ext] = dict(path=str(path.relative_to(ROOT)), sha256=sha(path))
    plt.close(fig)
    write_json(dest / 'phantom_behavior_artifacts.json', dict(
        report_sha256=sha(dest / 'phantom_behavior.json'), summary_sha256=sha(summary_path), figures=files))
    print('PHANTOM_PAIRED_SCREEN_COMPLETE', 'reviewed', len(verified), 'pairs', len(left))


if __name__ == '__main__':
    main()
