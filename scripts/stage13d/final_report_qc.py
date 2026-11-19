"""Presentation-only QC after inference; preserve every pre-QC report artifact."""
import os
import shutil

import numpy as np
import pandas as pd

from scripts.stage13d.common import ROOT, Path, load, now, save, sha


def main():
    summary = ROOT / 'stage13d_summary.md'
    report = Path('reports/stage13d/v1/index.md')
    figure = ROOT / 'figures/stage13d_3_selected_rescue'
    verification = ROOT / 'audit/final_verification.json'
    targets = [summary, report, figure.with_suffix('.png'), figure.with_suffix('.pdf'), verification]
    archive = ROOT / 'audit/report_before_publication_qc'
    archive.mkdir(exist_ok=False)
    before = {}
    for p in targets:
        dest = archive / p.name
        shutil.copyfile(p, dest)
        before[str(p)] = dict(sha256=sha(p), archive=str(dest))
    inference_hash = sha(ROOT / 'stage13d_primary_inference.json')
    decision_hash = sha(ROOT / 'stage13d_decision.json')
    note = (
        '**Neither mechanism met its confirmation gate.** The prospectively defined '
        '`PARTIAL` label reflects a positive but subthreshold semantic point estimate, '
        'not a confirmed mechanism. Derived content did not outperform the fresh baseline. '
        'Stage13A remains unchanged.\n\n'
    )
    bounds_note = (
        '\nMissingness bounds use all 23 safe families and assign missing calls their '
        'worst/best possible outcomes. They are finite-cohort bounds, not confidence '
        'intervals for the 13-family complete-case estimand. The 22 missing calls cluster '
        'across 10 families. Both selected historical overlaps are unresolved for the '
        'complete-case rescue criterion; zero confirmed rescues is not evidence of two '
        'failed rescues. All 13 complete families have verified-correct derived states, '
        'so the flawed-state comparison is not estimable.\n\n'
    )
    for p in [summary, report]:
        text = p.read_text()
        heading, rest = text.split('\n\n', 1)
        text = heading + '\n\n' + note + rest
        anchor = 'Derived-correctness strata are descriptive, not causal error-propagation claims:'
        assert text.count(anchor) == 1
        text = text.replace(anchor, bounds_note + anchor)
        p.write_text(text)

    # Show known per-arm outcomes instead of marking an entire partial family missing.
    os.environ['MPLCONFIGDIR'] = str(Path('runs/stage13d/v1/cache/matplotlib').resolve())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    selected = load(ROOT / 'audit/selected_case_rescue.json')['rows']
    table = pd.read_parquet(ROOT / 'audit/semantic_family_effects.parquet').set_index('item_id')
    order = ['I_BASE', 'I_DUMMY', 'I_SHUFFLED', 'I_DERIVED']
    arr = np.full((len(selected), 4), np.nan)
    labels = {}
    for y, row in enumerate(selected):
        f = table.loc[row['item_id']]
        for x, arm in enumerate(order):
            correct, resolved = int(f[arm + '_correct']), int(f[arm + '_resolved'])
            labels[y, x] = f'{correct}/{resolved}'
            if resolved == 5:
                arr[y, x] = correct
            else:
                labels[y, x] += f'\n{5 - resolved} missing'
    fig, ax = plt.subplots(figsize=(8, 3.8), constrained_layout=True)
    cmap = plt.colormaps['YlGn'].copy()
    cmap.set_bad('#e8e8e8')
    im = ax.imshow(arr, vmin=0, vmax=5, cmap=cmap, aspect='auto')
    ax.set_xticks(range(4), [c.replace('I_', '') for c in order])
    ax.set_yticks(range(len(selected)), [r['item_id'] for r in selected])
    for (y, x), label in labels.items():
        ax.text(x, y, label, ha='center', va='center', color='white' if arr[y, x] >= 4 else 'black')
    ax.set_title('13D-3  Selected-case outcomes (both rescues unresolved)')
    ax.set_xlabel('Cells: correct / resolved; gray cells have technical missingness')
    fig.colorbar(im, ax=ax, label='Correct out of 5 (complete cells only)')
    for ext in ['png', 'pdf']:
        fig.savefig(figure.with_suffix('.' + ext), dpi=180, bbox_inches='tight')
    plt.close(fig)
    assert sha(ROOT / 'stage13d_primary_inference.json') == inference_hash
    assert sha(ROOT / 'stage13d_decision.json') == decision_hash
    record = dict(at=now(), reason='Clarify subthreshold decision/denominators; display observed selected-case cells without falsely marking all arms missing.',
                  statistical_results_changed=False, scores_changed=False, protocol_changed=False,
                  before=before, after={str(p): sha(p) for p in targets if p != verification},
                  primary_inference_sha256=inference_hash, decision_sha256=decision_hash)
    save(ROOT / 'audit/final_report_qc.json', record)
    final = load(verification)
    final['at'] = now()
    final['required_artifacts'][str(summary)] = sha(summary)
    final['report_qc_receipt'] = str(ROOT / 'audit/final_report_qc.json')
    final['previous_verification_archive'] = before[str(verification)]['archive']
    verification.write_text(__import__('json').dumps(final, indent=2) + '\n')


if __name__ == '__main__':
    main()
