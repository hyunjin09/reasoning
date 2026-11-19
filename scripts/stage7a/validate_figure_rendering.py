"""CPU-only synthetic rendering check. Never writes scientific result folders."""
import copy
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scripts.stage7a.common import ROOT, OUT, read_jsonl, write_json, sha
import scripts.stage7a.render_results as renderer


def main():
    dest = OUT/'audit/figure_validation_v3'
    dest.mkdir(parents=True, exist_ok=True)
    source = read_jsonl(OUT/'config/discovery_events.jsonl')[0]
    entries, states, metrics, features = [], {}, {}, []
    for split in ('discovery', 'confirmation'):
        for i, name in enumerate(renderer.STATE_NAMES):
            entry = copy.deepcopy(source)
            entry.update(id=split+str(i), event_id=split+str(i), base_id=split+str(i), group_id=split+str(i), split=split,
                         downstream_review=dict(error_quote='SYNTHETIC integration example; no scientific claim'))
            entry['reviewed_claim'].update(quote='SYNTHETIC native value claim; not research data', locally_correct=i in (0, 5), demand='singleton')
            entries.append(entry)
            states[entry['id']] = dict(state=name, tier=None if name == 'UNRESOLVED' else 1, source_identity='T')
            semantic = dict(native_contrast=-1., sham_contrast=-.9, semantic_contrast=.9, net_semantic_beyond_sham=1.8)
            metrics[entry['id']] = dict(local_correctness=entry['reviewed_claim']['locally_correct'],
                source_effects={role+'_W2': dict(VSD=.1*(i+1), EP_margin=.05*(i+1)) for role in ('T', 'X', 'I', 'G')},
                semantic_effects={role: semantic for role in ('T', 'X')},
                distribution_similarity={key: dict(JS_nats=.02*(i+1)) for key in ('mask__unrelated', 'mask__no_image', 'unrelated__no_image')})
            features.append(dict(id=entry['id'], features={layer+'.T_minus_X.mean_'+key: float(i+1)
                for layer in ('28', '29') for key in ('qk_cosine', 'attention_mass', 'alpha_v_norm', 'post_wo_norm')}))
    rate = dict(certified_lower_bound_all_claims=dict(mean=.5, ci95=[.2, .8]))
    payloads = {
        'discovery_thresholds.json': dict(prior_js_max=.05),
        'correctness_faithfulness_matrix.json': dict(rows=[dict(split='confirmation', source_fidelity='unresolved', local_correct=True, final_correct=None)]),
        'faithfulness_metrics.json': dict(confirmation=dict(by_condition={c: dict(rates={name: rate for name in
            ('demand_source_consistency', 'grounded_evidence_rate', 'wrong_source_read_rate', 'prior_fill_rate')}) for c in ('intact', 'strong', 'mask', 'unrelated', 'no_image')})),
        'probe_results.json': {task: dict(primary=dict(source_specific=dict(status='UNAVAILABLE'))) for task in ('Task1', 'Task2', 'Task3', 'Task4')},
        'intervention_readiness.json': dict(states={name: dict(checks={key: None for key in ('sufficient_fresh_events', 'causal_direction_coherent',
            'failure_readout_oriented', 'clear_corrective_prediction', 'matched_faithful_controls')}) for name in renderer.STATE_NAMES[1:-1]}),
        'dataset_robustness.json': dict(datasets={'Synthetic': dict(confirmation=dict(yields={name: dict(events=1) for name in renderer.STATE_NAMES}))}),
        'schema_artifacts.json': dict(artifacts={}),
    }
    original_finish = renderer.finish
    def finish(fig, title, subtitle):
        original_finish(fig, title, 'SYNTHETIC RENDERING CHECK — NOT RESEARCH RESULTS\n'+subtitle)
        fig.text(.5, .5, 'SYNTHETIC', color='#ad4747', fontsize=40, alpha=.18, ha='center', va='center', rotation=25)
    def save(fig, stem):
        path = dest/(stem+'.png')
        fig.savefig(path, dpi=100)
        plt.close(fig)
        return {str(path.relative_to(OUT)): sha(path)}
    renderer.OUT = dest
    renderer.load_completed = lambda: (entries, metrics, states, {})
    renderer.read_json = lambda path: payloads[Path(path).name]
    renderer.read_jsonl = lambda path: features
    renderer.finish, renderer.save = finish, save
    renderer.main()
    write_json(dest/'validation.json', dict(completed=True, synthetic_only=True, scientific_output_modified=False,
               cpu_only=True, figures=19, script_sha256=sha(__file__)))
    print('Synthetic19-category rendering completed in audit/figure_validation_v3 only.')


if __name__ == '__main__':
    main()
