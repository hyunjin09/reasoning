"""Outcome-independent Stage9A prompt, boundary and task rules."""
import hashlib
import re

ARMS = ("instruct_direct", "instruct_cot", "thinking")
COT = "Think step by step before answering."
TAU = 0.5478025980771918


def prompt(question, arm):
    if arm not in ARMS:
        raise ValueError(arm)
    return question + ("\n\n" + COT if arm == "instruct_cot" else "")


def item_seed(item_id):
    return int.from_bytes(hashlib.sha256(("stage9a:" + str(item_id)).encode()).digest()[:4], "big") & 0x7fffffff


def reasoning_span(token_rows, arm):
    """Return [start, end) generated coordinates, without inspecting measurements."""
    if arm not in ARMS:
        raise ValueError(arm)
    pieces = [r["decoded_token"] for r in token_rows]
    text = "".join(pieces)
    special = {"<|im_end|>", "<|endoftext|>", "<think>", "</think>"}
    valid = [i for i, p in enumerate(pieces) if p not in special]
    if not valid:
        return dict(start=0, end=0, common_end=0, boundary="empty", certain=True)
    start, common_end = valid[0], valid[-1] + 1
    stop, boundary, certain = len(text), "no_marker_full_assistant", False
    if arm == "thinking" and "</think>" in text:
        stop, boundary, certain = text.index("</think>"), "native_think_end", True
    elif arm != "thinking":
        last_paragraph = text.rfind("\n\n") + 2 if "\n\n" in text else 0
        pattern = r"(?im)(?:final\s+answer\b|the\s+answer\s+is\b|\banswer\s*:|\\boxed\s*\{)"
        for match in re.finditer(pattern, text):
            line_start = text.rfind("\n", 0, match.start()) + 1
            standalone = bool(re.fullmatch(r"[\s*#]*", text[line_start:match.start()]))
            if match.start() >= last_paragraph or (standalone and match.group().lower().startswith("final")):
                stop, boundary, certain = match.start(), "explicit_final_marker", True
                break
    cursor, end = 0, common_end
    for i, piece in enumerate(pieces):
        if cursor + len(piece) > stop:
            end = min(i, common_end)
            break
        cursor += len(piece)
    return dict(start=min(start, end), end=end, common_end=common_end, boundary=boundary, certain=certain)


def episode_metrics(scores, start, end, threshold=TAU):
    import numpy as np
    x = np.asarray(scores, dtype=float)[start:end]
    active = np.isfinite(x) & (x > threshold)
    on = np.flatnonzero(active & ~np.r_[False, active[:-1]]) if len(x) else np.array([], dtype=int)
    off = np.flatnonzero(active & ~np.r_[active[1:], False]) if len(x) else np.array([], dtype=int)
    episodes = [dict(start=int(a+start), end=int(b+start+1), onset_normalized=float(a/len(x))) for a,b in zip(on,off)]
    gaps = on[1:] - off[:-1] - 1
    eligible = [i for i,b in enumerate(off) if len(x)-1-b >= 128]
    successes = sum(i+1 < len(on) and on[i+1]-off[i] >= 128 for i in eligible)
    valid = np.isfinite(x)
    return dict(reasoning_tokens=len(x), valid_score_tokens=int(valid.sum()), episodes=episodes,
                episode_count=len(on), episodes_per_1k=1000*len(on)/len(x) if len(x) else None,
                active_fraction=float(active.sum()/valid.sum()) if valid.any() else None,
                late_fractions={str(q):float(np.mean(on/len(x)>q)) if len(on) else None for q in (.25,.5,.75)},
                median_inactive_gap=float(np.median(gaps)) if len(gaps) else None,
                max_inactive_gap=int(max(gaps)) if len(gaps) else None,
                long_gap_at_risk=len(eligible), long_gap_successes=int(successes),
                long_gap_probability=successes/len(eligible) if eligible else None)
