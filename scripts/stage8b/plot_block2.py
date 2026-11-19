"""Five diagnostic figures from frozen labels and completed observational replay."""
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from visual_reasoning.stage8b.block2_data import ROOT, PREFIX

COLORS = {'L+': '#237a57', 'L-': '#b64646'}


def finish(figure, stem):
    figure.savefig(ROOT/'figures'/f'{stem}.png', dpi=170, bbox_inches='tight')
    figure.savefig(ROOT/'figures'/f'{stem}.pdf', bbox_inches='tight')
    plt.close(figure)


def points(axis, frame, metric, title, pairs):
    index = frame.set_index('event_id')
    for pair in pairs:
        a, b = pair['control'], pair['failure']
        if a in index.index and b in index.index:
            y = [index.loc[a, metric], index.loc[b, metric]]
            if np.isfinite(y).all():
                axis.plot([0, 1], y, color='.78', linewidth=.6, zorder=1)
    rng = np.random.default_rng(1234)
    for x, label in enumerate(['L+', 'L-']):
        sub = frame.loc[frame.local == label]
        y = pd.to_numeric(sub[metric], errors='coerce').dropna()
        axis.scatter(x+rng.uniform(-.09, .09, len(y)), y, color=COLORS[label], alpha=.8, s=22, zorder=2)
        if len(y):
            axis.plot([x-.16, x+.16], [y.mean()]*2, color='black', linewidth=2)
        axis.text(x, 1.01, f'n={len(y)}', transform=axis.get_xaxis_transform(), ha='center', fontsize=9)
    axis.set_xticks([0, 1], ['L+', 'L−']); axis.set_title(title, pad=24); axis.grid(axis='y', alpha=.2)


def main():
    (ROOT/'figures').mkdir(exist_ok=True)
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    aligned = pd.read_parquet(ROOT/'audit/onset_aligned.parquet')
    curve_records, support = [], {}
    figure, axes = plt.subplots(1, 3, figsize=(12, 3.9))
    for axis, metric, title in zip(axes, ['R', 'qk_visual_nonvisual', 'visual_mass'], ['Frozen retrieval score', 'Visual QK competitiveness', 'Visual attention mass']):
        for label in ['L+', 'L-']:
            sub = aligned.loc[aligned.local == label]
            family = sub.groupby(['family_id', 'offset'])[metric].mean().unstack('offset').reindex(columns=range(-32, 33))
            values = family.to_numpy(float); valid = np.isfinite(values)
            weights = np.random.default_rng(1234).multinomial(len(values), np.full(len(values), 1/len(values)), size=4000)
            denominator = weights@valid
            samples = np.divide(weights@np.nan_to_num(values), denominator, out=np.full(denominator.shape, np.nan, dtype=float), where=denominator > 0)
            lower, upper = np.nanquantile(samples, [.025, .975], axis=0)
            mean = np.nanmean(values, axis=0)
            support[label] = f'{valid.sum(0).min()}–{valid.sum(0).max()}'
            curve_records.extend(dict(metric=metric, local=label, offset=offset, families=int(valid[:, i].sum()),
                                      mean=float(mean[i]), lower=float(lower[i]), upper=float(upper[i])) for i, offset in enumerate(range(-32, 33)))
            axis.plot(range(-32, 33), mean, label=label, color=COLORS[label])
            axis.fill_between(range(-32, 33), lower, upper, color=COLORS[label], alpha=.15)
        axis.axvline(0, color='.4', ls=':', lw=1); axis.set_title(title); axis.set_xlabel('Tokens relative to selected episode onset')
    axes[0].axhline(.5478025980771918, color='.5', ls='--', lw=.8)
    axes[0].legend(); figure.suptitle('Retrieval activation: descriptive, selected events (120 L+, 17 L−)', y=1.04)
    figure.text(.5, -.04, 'Family/class means; pointwise 95% family-bootstrap bands. Observed family support: L+ '+support['L+']+', L− '+support['L-']+'.\nMissing pre-onset observations are omitted. Concurrent alignment, not a pre-read prediction test.', ha='center', fontsize=9)
    figure.tight_layout(); finish(figure, 'figure1_activation')
    pd.DataFrame(curve_records).to_csv(ROOT/'audit/figure1_curve_data.csv', index=False)
    route = pd.read_parquet(ROOT/'audit/replayed_routing.parquet')
    manifest = json.loads((ROOT/(PREFIX+'replay_manifest.json')).read_text())
    figure, axes = plt.subplots(1, 2, figsize=(8.8, 4))
    points(axes[0], route, 'qk_T_X', 'Target − confuser QK (log-mean-exp)', manifest['pairs'])
    points(axes[1], route, 'share_T_X', 'Target − confuser visual attention share', manifest['pairs'])
    figure.suptitle('Source routing: 12 failures + 9 controls; gray lines mark matched pairs', y=1.06)
    figure.text(.5, -.03, 'All replayed events shown; primary comparison uses 9 matched pairs. Missing confusers are omitted per metric.', ha='center', fontsize=9)
    figure.tight_layout(); finish(figure, 'figure2_routing')
    figure, axes = plt.subplots(1, 3, figsize=(12, 4))
    for axis, metric, title in zip(axes, ['target_rank', 'top2_margin', 'source_entropy'], ['Target rank (lower is better)', 'Top-two candidate margin', 'Candidate-source entropy']):
        points(axis, route, metric, title, manifest['pairs'])
    figure.suptitle('Source competition among 2–3 annotated regions per event', y=1.06)
    figure.text(.5, -.03, 'Candidate inventories and ROI areas vary. This is neither exhaustive image routing nor a causal assay.', ha='center', fontsize=9)
    figure.tight_layout(); finish(figure, 'figure3_ambiguity')
    grids = {}
    for label in ['L+', 'L-']:
        by_family = {}
        for request in manifest['requests']:
            if request['local'] != label:
                continue
            path = ROOT/'replay'/f'worker{request["rank"]}'/'events'/f'{request["event_id"]}.json'
            result = json.loads(path.read_text()); grid = []
            for layer in manifest['layers']:
                record = result['per_head_records'][str(layer)]; roles = record['roles']
                qk = np.array(record['qk'])
                grid.append((qk[:, roles.index('T')] > qk[:, roles.index('X')]).astype(float) if 'X' in roles else np.full(16, np.nan))
            by_family.setdefault(request['family_id'], []).append(np.array(grid))
        family_grids = [np.nanmean(values, axis=0) for values in by_family.values() if np.isfinite(values).any()]
        grids[label] = np.nanmean(family_grids, axis=0)
    figure, axes = plt.subplots(1, 2, figsize=(11, 3.5), constrained_layout=True)
    for axis, label in zip(axes, ['L+', 'L-']):
        rendered = axis.imshow(grids[label], vmin=0, vmax=1, cmap='viridis', aspect='auto')
        axis.set_title(label+' target > confuser QK'); axis.set_yticks(range(4), manifest['layers']); axis.set_xticks(range(16)); axis.set_xlabel('Head'); axis.set_ylabel('Frozen layer')
    figure.colorbar(rendered, ax=axes, label='Family-weighted fraction favoring target', shrink=.8)
    figure.suptitle('All 64 frozen late heads; descriptive source preference')
    finish(figure, 'figure4_head_layer')
    frame = pd.read_parquet(ROOT/(PREFIX+'local_read_table.parquet'))
    table = pd.crosstab(frame.local, frame.benchmark_label).reindex(index=['L+', 'L-'], columns=['correct', 'wrong', 'unresolved'], fill_value=0)
    figure, axis = plt.subplots(figsize=(7, 3.4))
    axis.imshow(table, cmap='Blues', aspect='auto')
    for i in range(2):
        for j in range(3):
            axis.text(j, i, str(table.iloc[i, j]), ha='center', va='center', fontsize=24,
                      color='white' if table.iloc[i, j] > 40 else 'black')
    axis.set_xticks(range(3), ['Final correct', 'Final wrong', 'Final unresolved'])
    axis.set_yticks(range(2), ['Local L+', 'Local L−'])
    axis.set_title('Local visual read × final outcome (event counts)')
    figure.text(.5, .01, '120 L+ / 107 families; 17 L− / 16 families. Eleven L? events are reported separately.', ha='center', fontsize=9)
    figure.tight_layout(rect=(0, .05, 1, 1)); finish(figure, 'figure5_local_final')
    print('Five figures saved as PNG and PDF')


if __name__ == '__main__':
    main()
