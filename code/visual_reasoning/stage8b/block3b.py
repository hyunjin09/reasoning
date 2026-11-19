"""Frozen-window post-read measurements; semantic labels are never inferred here."""
import numpy as np

from visual_reasoning.stage8b.block0 import EPSILON

WINDOWS = (32, 64, 128, 256, 512)
GEOMETRY_WINDOWS = (128, 256, 512)


def geometry(values):
    z = np.asarray(values, dtype=np.float64)
    valid = np.isfinite(z).all(axis=1)
    pairs = valid[:-1] & valid[1:]
    indices = np.flatnonzero(valid)
    count = int(pairs.sum())
    distances = np.linalg.norm(np.diff(z, axis=0), axis=1)
    path = float(distances[pairs].sum()) if count else None
    displacement = float(np.linalg.norm(z[indices[-1]]-z[indices[0]])) if len(indices)>=2 else None
    return dict(path_length=path, movement=path/count if count else None,
        displacement=displacement,
        tortuosity=path/(displacement+EPSILON) if path is not None and displacement is not None else None,
        valid_transitions=count, valid_vectors=int(valid.sum()))


def post_read(t0, length, episode_starts):
    assert 0 <= t0 < length
    starts = np.asarray(episode_starts, dtype=int)
    assert np.all(np.diff(starts)>0) and np.all((starts>=0)&(starts<length))
    later = starts[starts>t0]
    windows = {}
    for width in WINDOWS:
        exposure = min(width, length-1-t0)
        count = int(np.sum(later<=t0+exposure))
        observed = exposure==width
        windows[str(width)] = dict(exposure=exposure, complete=observed, episodes=count,
            within_window=int(count>0) if observed else None,
            observed_return=bool(count), incidence_censored=not observed and count==0)
    gaps = np.diff(later)
    burst = ((gaps.std()-gaps.mean())/(gaps.std()+gaps.mean())) if len(gaps)>=3 and gaps.std()+gaps.mean()>0 else None
    return dict(windows=windows, time_to_next=int(later[0]-t0) if len(later) else None,
        next_retrieval_censored=not len(later), followup_tokens=length-1-t0,
        remaining_episodes=len(later), burstiness=float(burst) if burst is not None else None)


def pre_post(t0, values, widths=GEOMETRY_WINDOWS):
    z = np.asarray(values, dtype=np.float64); n=len(z)
    assert 0 <= t0 < n
    output = {}
    for width in widths:
        pre_start=max(0,t0-width); post_end=min(n-1,t0+width)
        before=geometry(z[pre_start:t0+1]); after=geometry(z[t0:post_end+1])
        complete=t0>=width and t0+width<n
        output[str(width)]=dict(pre=before,post=after,complete=complete,
            pre_exposure=t0-pre_start,post_exposure=post_end-t0,
            delta_tortuosity=after['tortuosity']-before['tortuosity'] if complete and before['tortuosity'] is not None and after['tortuosity'] is not None else None,
            delta_movement=after['movement']-before['movement'] if complete and before['movement'] is not None and after['movement'] is not None else None)
    return output


def aligned_refresh(observation, episodes):
    """Temporal support for an already semantic same-source engagement, not source identity."""
    lo, hi=observation['start_token'],observation['end_token']-1
    return [e['event_id'] for e in episodes if e['start_token']<=hi+32 and e['end_token']>=lo-32]
