"""Render the prescribed figures and auditable response-reading copies."""
import os
import textwrap
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', str(Path('runs/stage12vs/v1/matplotlib').resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scripts.stage12vs.common import ROOT, load, now

REPORT = Path('reports/stage12vs/v1')


def savefig(fig, name):
    dest = ROOT / 'figures'
    dest.mkdir(exist_ok=True)
    for ext in ['png', 'pdf']:
        fig.savefig(dest / f'{name}.{ext}', dpi=180, bbox_inches='tight')
    plt.close(fig)


def figures():
    info = load(ROOT / 'stage12vs_primary_inference.json')
    primary = info['primary']
    eligible = [r for r in primary if r['stable'] is True]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    for ax, r in zip(axes.flat, primary):
        pts = sorted((int(k), v) for k, v in r['localization']['points'].items())
        complete = [(k, sum(x is True for x in p['outcomes']) / 3) for k, p in pts if None not in p['outcomes']]
        ax.plot(*zip(*complete), 'o--', color='#286b82', lw=1, ms=4)
        for k, p in pts:
            missing = sum(x is None for x in p['outcomes'])
            if missing:
                lo = sum(x is True for x in p['outcomes']) / 3
                ax.errorbar(k, lo, yerr=[[0], [missing / 3]], fmt='s', color='#777777', capsize=4, mfc='white')
        ax.axhline(2 / 3, color='#bbbbbb', ls=':', lw=1)
        if r['stable'] is True:
            a, b = r['localization']['a'], r['localization']['b']
            ax.axvspan(a, b, color='#d18423', alpha=.5)
            ax.annotate(f'{a} → {b}', xy=(b, 1), xytext=(8, -22), textcoords='offset points', fontsize=9)
        ax.set(xlabel='Semantic-step index', ylabel='Correct / 3 seeds', ylim=(-.08, 1.1),
               title=f"{r['item_id']} · {r['localization']['status'].replace('_', ' ')}")
        ax.set_yticks([0, 1/3, 2/3, 1], ['0/3', '1/3', '2/3', '3/3'])
    fig.suptitle('V1 · Prefix portability: gray ranges retain missing cap outcomes')
    savefig(fig, 'V1_portability_emergence')
    fig, axes = plt.subplots(1, len(eligible), figsize=(11, 4.5), squeeze=False, constrained_layout=True)
    for ax, r in zip(axes.flat, eligible):
        loc = r['localization']
        vals = [loc['points'][str(loc[k])]['outcomes'] for k in ['a', 'b']]
        vals += [r['conditions']['C1_DROP']['outcomes'], r['thinking']['before']['outcomes'], r['thinking']['after']['outcomes']]
        heights = [sum(v is True for v in xs) / 3 for xs in vals]
        ax.bar(range(5), heights, color=['#b1c9d3', '#3b7a91', '#d7a370', '#9ca3c1', '#737ca4'])
        for x, y in enumerate(heights):
            ax.text(x, y + .03, f'{round(y*3)}/3', ha='center', fontsize=10)
        ax.set_xticks(range(5), ['I before\nsearch', 'I after', 'I before\nfresh DROP', 'T before', 'T after'], fontsize=9)
        ax.set(ylim=(0, 1.18), ylabel='Correct / 3 seeds', title=f"{r['item_id']} · {loc['a']} → {loc['b']}")
    fig.suptitle('V2 · Search transitions and their fresh-seed checks')
    savefig(fig, 'V2_before_after_checks')
    names = ['Original', 'DROP', 'Counterfactual', 'Paraphrase', 'Control\ndelete', 'E* only', 'E* + step']
    conds = ['C1_DROP', 'C2_CF', 'C3_PARA', 'C4_CTRL_DROP', 'C5_ESTAR', 'E_PLUS_STEP']
    outcomes = [[r['localization']['points'][str(r['localization']['b'])]['outcomes']] +
                [r['conditions'][c]['outcomes'] for c in conds] for r in eligible]
    matrix = [[sum(v is True for v in xs) / 3 for xs in group] for group in outcomes]
    fig, ax = plt.subplots(figsize=(11, 3.4), constrained_layout=True)
    ax.imshow(matrix, vmin=0, vmax=1, cmap='YlGnBu', aspect='auto')
    for y, values in enumerate(matrix):
        for x, value in enumerate(values):
            missing = sum(v is None for v in outcomes[y][x])
            label = f'{round(value*3)}/3' + (f'\n{missing} missing' if missing else '')
            ax.text(x, y, label, ha='center', va='center', color='white' if value > .5 else '#111111')
    ax.set_xticks(range(len(names)), names, fontsize=10)
    ax.set_yticks(range(len(eligible)), [r['item_id'] for r in eligible])
    ax.set_title('V3 · Instruct content interventions; all seeds, no best-of-three')
    savefig(fig, 'V3_content_interventions')
    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    ax.axis('off')
    cells = []
    for r in primary:
        edit = r['critical_step']
        cells.append([r['item_id'], str(edit['step_index']) if edit else '—',
                      edit['critical_source_category'].replace('_', '\n') if edit else r['localization']['status'].replace('_', '\n'),
                      textwrap.fill(edit['original_step'].strip(), 70) if edit else 'No eligible single-step intervention',
                      'Repeats earlier\ncontent; no causal\nnecessity signature' if edit else 'Missing boundary' if r['stable'] is None else 'Nonmonotonic'])
    table = ax.table(cellText=cells, colLabels=['Family', 'Step', 'Frozen role / status', 'Exact source step', 'Interpretation'],
                     cellLoc='left', loc='center', colWidths=[.06, .05, .18, .53, .18])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (i, j), cell in table.get_celld().items():
        cell.set_height(.14 if i == 0 else .19)
    ax.set_title('V4 · Frozen semantic roles; novelty and a common causal mechanism are not established')
    savefig(fig, 'V4_semantic_roles')


def reading_copies(info):
    REPORT.mkdir(parents=True, exist_ok=True)
    index = ['# Stage12V-S complete responses', '', 'Exact new continuations and frozen prefill links. Missing cap outcomes remain missing.', '',
             '[Scientific summary](../../../outputs/stage12vs/v1/stage12vs_summary.md)', '']
    for r in info['all_seed_rows']:
        g = load(ROOT / 'generations' / r['task_id'] / 'generation.json')
        prefix = f"[Exact prefill]({Path(r['prefix_path']).resolve()})" if r['prefix_path'] else 'No prefill'
        text = f"# {r['task_id']}\n\nTarget: {r['target']}; seed: {r['seed']}; tokens: {r['tokens']}; stop: {g['finish_reason']}; label: {r['label']}.\n\n{prefix}\n\n## Exact user text\n\n{r['question']}\n\n## Complete new continuation\n\n```text\n{g['raw_decoded_response']}\n```\n"
        (REPORT / f"{r['task_id']}.md").write_text(text)
        index.append(f"- [{r['task_id']}]({r['task_id']}.md): {r['label']}, {r['tokens']:,} tokens")
    (REPORT / 'index.md').write_text('\n'.join(index) + '\n')


def summary(info, resource, verification):
    d = info['decision']
    eligible = [r for r in info['primary'] if r['stable'] is True]

    def cell(vals):
        missing = sum(v is None for v in vals)
        return f'{sum(v is True for v in vals)}/3' + (f' ({missing} missing)' if missing else '')

    lines = ['# Stage12V-S — Portable Thinking-state localization', '',
             f"Completed {now()}. **{d['decision']}**. Authorized stage ends here; no next experiment launched.", '',
             '**Full-prefix portability replicated in4/4 families, but neither of the two localized steps passed the complete causal signature.** The frozen search found adjacent majority transitions in2/4; a third family was nonmonotonic and the fourth stopped at a missing boundary. Fresh-seed deletion of the apparent critical step retained majority success in both tested families. A robust necessary single deduction was not established.', '',
             'The decision label follows the sealed pre-generation rule (two stable plus one nonmonotonic family). It does not mean all unresolved families are nonmonotonic: family798 remains missingness-limited. The stronger three-family thresholds were not met. Do not replace this with a positive distributed-state classification.', '',
             '## Frozen study and execution', '',
             'Exactly four Stage12U-S production-support families2975/798/750/2908; family991 remains historical/descriptive with no new calls. Original questions and successful answer-safe Thinking prefixes reused unchanged, segmented into2,036 source steps before outcomes. All continuations are image-free native assistant-prefill replays. Three frozen seeds per condition; majority requires at least2/3 correct. No best-of-three, seed search, source regeneration or cap expansion.', '',
             '162 new calls:72 coarse,42 fine,12 adjacent Thinking,30 mandatory Instruct C1–C5,6 optional evidence-plus-step. Optional calls used all previously frozen rows after mandatory completion and a resource-only gate. Independent mandatory jobs overlapped where Slurm capacity allowed. No scientific parameters changed for concurrency.', '',
             'Pinned Qwen3-VL-4B-Instruct: temperature0.7,top-p0.8,top-k20,repetition1,presence1.5,cap32768. Pinned4B-Thinking:temperature1,top-p0.95,top-k20,repetition1,presence0,cap81920. BF16 vLLM0.11.0; exact revisions, input IDs, recipes and hashes are in config/generation receipts. These checkpoint-specific regimes do not isolate a pure Thinking switch.', '',
             '## Localization and adjacent Thinking checks', '',
             '| Family | Frozen search result | I before | I after | T before | T after |',
             '|---|---|---:|---:|---:|---:|']
    for r in info['primary']:
        loc = r['localization']
        if r['stable'] is True:
            lines.append(f"| {r['item_id']} | Stable {loc['a']}→{loc['b']} | {cell(loc['points'][str(loc['a'])]['outcomes'])} | {cell(loc['points'][str(loc['b'])]['outcomes'])} | {cell(r['thinking']['before']['outcomes'])} | {cell(r['thinking']['after']['outcomes'])} |")
        else:
            lines.append(f"| {r['item_id']} | {loc['status']} | — | — | not eligible | not eligible |")
    lines += ['', 'Family750 shows success at149, failure at448 and success again at598 and747. Family798 midpoint8 has one correct, one incorrect and one capped/missing continuation; its majority is unresolved and no retry was allowed. All four families remain in the primary cohort. All six missing outputs are from family798.', '',
              'Thinking shows majority success on both adjacent prefixes for both localized families (plan PatternB descriptively). However, the fresh Instruct DROP replication uses exactly the before prefix and also succeeds in both families. Thus the original before/after majority contrast is sensitive to the frozen seed group; it is not a replicated necessary-step boundary.', '',
              '## Content interventions', '',
              '| Family | Original Pk | DROP | CF | PARA | CTRL DROP | E* only | E* + step | CF-following | Causal signature |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    conds = ['C1_DROP', 'C2_CF', 'C3_PARA', 'C4_CTRL_DROP', 'C5_ESTAR', 'E_PLUS_STEP']
    for r in eligible:
        loc = r['localization']
        entries = [cell(loc['points'][str(loc['b'])]['outcomes'])] + [cell(r['conditions'][c]['outcomes']) for c in conds]
        lines.append('| ' + r['item_id'] + ' | ' + ' | '.join(entries) + f" | {cell(r['cf_following'])} | {r['causal']} |")
    lines += ['', 'Entries are correct continuations out of all three seeds; CF-following is a separately reviewed semantic count. Unfinished caps remain missing, never incorrect. Original Pk is the search observation; DROP is the identical before-prefix input with fresh prospectively fixed seeds, not another altered text.', '',
              'For2975, deletion retains2/3 success, the secant→tangent counterfactual retains3/3, paraphrase retains2/3 and matched-control deletion falls to1/3. None of its three CF continuations ultimately uses the tangent hypothesis. For2908, deletion retains3/3, the angle-rule counterfactual lowers success to1/3, paraphrase/control deletion retain3/3, and one CF continuation follows240 degrees. This supports content sensitivity in that tested contrast, but fails necessity and therefore the joint causal signature.', '',
              'Replicated E*-only controls remain majority incorrect in both eligible families (0/3 and1/3); historical B4 labels are preserved. This does not rescue the missing critical-step necessity evidence. Optional E*+step is secondary; no optional outcome changes the primary decision.', '',
              '## Semantic content and limits', '']
    for r in eligible:
        e = r['critical_step']
        lines += [f"**{r['item_id']}, step{e['step_index']}, frozen {e['critical_source_category']}:**", '',
                  '> ' + e['original_step'].strip().replace('\n', '\n> '), '', e['semantic_interpretation_limit'], '',
                  f"Matched deletion: step{e['control_step_index']}, {e['control_step_tokens']} tokens versus {e['target_step_tokens']} critical-step tokens. {e['control_audit_basis']}", '']
    lines += ['The frozen automatic/source-cue novelty flags are not revised after outcomes; the source-based intervention audit explicitly identifies repeated propositions. Full primary-role manual review covered the short798 trace; long traces were not exhaustively independently semantically certified. The two localized roles differ, neither passes the full causal gate, and no common new deduction mechanism is claimed.', '',
              '## Family-level descriptive endpoints', '',
              '| Endpoint | Confirmed / frozen cohort | Eligible or resolved denominator | Exact descriptive95% interval |',
              '|---|---:|---:|---|']
    for name, data in info['endpoints'].items():
        value = data if name == 'V_P1_localization' else data['eligible_stable_only']
        count = data['successes'] if name == 'V_P1_localization' else data['confirmed_of_four']
        lo, hi = value['clopper_pearson_95']
        ci = f'[{lo:.3f},{hi:.3f}]' if lo is not None else 'not estimable'
        lines.append(f"| {name} | {count}/4 | {value['successes']}/{value['observed']} | {ci} |")
    lines += ['', 'Localization has2 confirmed stable,1 observed nonmonotonic and1 missing-boundary family; its missingness bounds are2/4–3/4. Causal-intervention intervals condition on the two eligible stable families; the other two were not tested. These exact intervals are descriptive, not prevalence estimates. Windows/steps/seeds are not independent families. All per-seed outcomes and final values are in the inference JSON and raw response index.', '',
              '## Verification and resources', '',
              f"All{verification['calls_verified']} input/generation/provenance receipts pass. {verification['scoreable']} scoreable,{verification['missing']} missing;{verification['qc_agreements']} same-agent separate extraction checks agree. This is not independent inter-rater reliability. CF labels cite exact continuation spans under prospectively frozen readouts; no label is inferred from accuracy alone.", '',
              f"All{verification['prior_files_unchanged']} snapshotted prior-stage files and every frozen source/analysis hash are unchanged. All{len(resource['jobs'])} finite science jobs completed0:0 and released their GPUs. Allocated compute **{resource['allocated_gpu_hours']:.6f} GPU-hours**, including startup, below target5/hard7. No retries, downloads or next-stage experiments. Per-request latencies overlap in batches and are not summed as GPU time.", '',
              'Figures: [V1](figures/V1_portability_emergence.png),[V2](figures/V2_before_after_checks.png),[V3](figures/V3_content_interventions.png),[V4](figures/V4_semantic_roles.png), each with a PDF companion. [Complete answers/reasoning](../../../reports/stage12vs/v1/index.md).', '',
              '## Exactly one recommendation', '', d['recommendation'], '', 'Not launched. STOP.']
    (ROOT / 'stage12vs_summary.md').write_text('\n'.join(lines) + '\n')
