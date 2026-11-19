"""Whole-family bootstrap with mixed local labels retained within every cluster."""
import numpy as np
import pandas as pd

from visual_reasoning.stage8b.block1_statistics import interval, joint_intervals, pooled_sd

BOOTSTRAPS = 4000
SEED = 1234


class FamilyBootstrap:
    def __init__(self, frame, resamples=BOOTSTRAPS, seed=SEED):
        self.frame = frame.reset_index(drop=True)
        families = sorted(set(frame.family_id))
        self.families = families
        lookup = {family: i for i, family in enumerate(families)}
        self.codes = np.array([lookup[f] for f in frame.family_id], dtype=int)
        self.draws = np.random.default_rng(seed).multinomial(len(families), np.full(len(families), 1/len(families)), size=resamples) if families else np.zeros((resamples, 0))
        self.weights = self.draws[:, self.codes]

    def contrast(self, metric):
        y = pd.to_numeric(self.frame[metric], errors='coerce').to_numpy(float)
        group = (self.frame.local == 'L-').to_numpy(int)
        summaries, samples, variances, sample_sizes = {}, [], [], []
        for value, label in [(0, 'L+'), (1, 'L-')]:
            keep = (group == value) & np.isfinite(y)
            weight = self.weights[:, keep]; denominator = weight.sum(1)
            mean = np.divide(weight@y[keep], denominator, out=np.full(len(weight), np.nan), where=denominator > 0)
            sum_squared = np.maximum(weight@(y[keep]**2)-denominator*mean**2, 0)
            variance = np.divide(sum_squared, denominator-1, out=np.full(len(weight), np.nan), where=denominator > 1)
            summaries[label] = dict(events=int(keep.sum()), families=self.frame.loc[keep, 'family_id'].nunique(),
                                    missing=int(((group == value) & ~np.isfinite(y)).sum()),
                                    mean=float(y[keep].mean()) if keep.any() else None,
                                    median=float(np.median(y[keep])) if keep.any() else None,
                                    mean_interval=interval(mean))
            samples.append(mean)
            variances.append(variance); sample_sizes.append(denominator)
        difference = samples[1]-samples[0]
        point = summaries['L-']['mean']-summaries['L+']['mean'] if all(summaries[g]['mean'] is not None for g in ['L+', 'L-']) else np.nan
        sd = pooled_sd(y, group)
        n0, n1 = sample_sizes
        df = n0+n1-2
        pooled_variance = np.divide((n0-1)*variances[0]+(n1-1)*variances[1], df,
                                    out=np.full(len(df), np.nan), where=df > 0)
        pooled = np.sqrt(pooled_variance)
        standardized = np.divide(difference, pooled, out=np.full(len(pooled), np.nan), where=pooled > 0)
        return dict(groups=summaries, effect_Lminus_minus_Lplus=point, ci=interval(difference),
                    pooled_sd=sd, standardized_effect=point/sd if sd > 0 else np.nan,
                    standardized_ci=interval(standardized)), difference


def compare(frame, metrics):
    frame = frame.loc[frame.local.isin(['L+', 'L-'])].copy()
    if not len(frame):
        return dict(status='unavailable', reason='No reviewed estimable events', metrics={})
    engine = FamilyBootstrap(frame); output, joint = {}, {}
    for metric in metrics:
        if metric not in frame:
            frame[metric] = np.nan; engine.frame[metric] = np.nan
        result, samples = engine.contrast(metric)
        output[metric] = result
        joint[metric] = dict(point=result['effect_Lminus_minus_Lplus'], samples=samples)
    means = frame.groupby(['family_id', 'local'], as_index=False)[metrics].mean()
    sensitivity = FamilyBootstrap(means)
    return dict(status='descriptive', independent_unit='image family; all local-label rows retained together',
                events=len(frame), families=frame.family_id.nunique(), resamples=BOOTSTRAPS, seed=SEED,
                metrics=output, simultaneous_intervals=joint_intervals(joint),
                family_class_mean_sensitivity={key: sensitivity.contrast(key)[0] for key in metrics})


def adjustment_diagnostics(frame, *, routing=False):
    """No unstable full adjustment is claimed below the prespecified yield gate."""
    frame = frame.loc[frame.local.isin(['L+', 'L-'])]
    columns = ['normalized_start', 'log_question_length']
    design = frame[columns].astype(float).copy()
    design['log_reasoning_length'] = np.log(frame.reasoning_tokens.astype(float))
    if routing:
        design['R_onset'] = frame.R_onset
    categories = ['subject_group', 'roi_type', 'completion'] + (['subtype'] if routing else [])
    design = pd.concat([design, pd.get_dummies(frame[categories].fillna('unavailable'), drop_first=True, dtype=float)], axis=1)
    design.insert(0, 'intercept', 1.)
    design['Lminus'] = (frame.local == 'L-').astype(float)
    negative_families = frame.loc[frame.local == 'L-', 'family_id'].nunique()
    return dict(status='unavailable' if negative_families < 24 or np.linalg.matrix_rank(design.to_numpy(float)) < design.shape[1] else 'not_run',
                reason='Too few independent L- families for a defensible full adjusted contrast; no controlled null or equivalence claim.',
                negative_families=negative_families, columns=list(design), rank=int(np.linalg.matrix_rank(design.to_numpy(float))),
                column_count=design.shape[1], sparse_strata={key: pd.crosstab(frame[key], frame.local).to_dict(orient='index') for key in categories},
                duration_sensitivity='unavailable under the same full-adjustment yield limitation')


def paired_comparisons(frame, pairs, metrics):
    """Resample connected family components so pairs sharing a family stay together."""
    indexed = frame.set_index('event_id'); valid = [p for p in pairs if p['failure'] in indexed.index and p['control'] in indexed.index]
    parent = {}
    def find(node):
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]
    for pair in valid:
        a, b = [indexed.loc[pair[key], 'family_id'] for key in ['failure', 'control']]
        parent[find(a)] = find(b)
    components = [find(indexed.loc[p['failure'], 'family_id']) for p in valid]
    unique = sorted(set(components)); lookup = {c: i for i, c in enumerate(unique)}
    draws = np.random.default_rng(SEED).multinomial(len(unique), np.full(len(unique), 1/len(unique)), size=BOOTSTRAPS) if unique else np.zeros((BOOTSTRAPS, 0))
    weights = draws[:, [lookup[c] for c in components]]
    output = {}
    for metric in metrics:
        values = np.array([indexed.loc[p['failure'], metric]-indexed.loc[p['control'], metric] for p in valid], dtype=float)
        keep = np.isfinite(values); denominator = weights[:, keep].sum(1)
        samples = np.divide(weights[:, keep]@values[keep], denominator, out=np.full(BOOTSTRAPS, np.nan), where=denominator > 0)
        output[metric] = dict(pairs=int(keep.sum()), mean_paired_difference=float(values[keep].mean()) if keep.any() else None,
                              **interval(samples))
    return dict(pairs=len(valid), independent_connected_family_components=len(unique), components=components,
                method='whole connected-family-component bootstrap, retaining matched pairs', metrics=output)
